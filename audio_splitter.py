#!/usr/bin/env python3
"""
Audio Splitter using Demucs
This script splits an audio track into stems using the Demucs AI model
"""

import os
import argparse
import sys
from pathlib import Path
import torch
import torchaudio
from torchaudio.pipelines import HDEMUCS_HIGH_MUSDB_PLUS

def split_audio(input_file, output_dir="output", model_name="htdemucs"):
    """
    Split an audio file into stems using Demucs
    
    Args:
        input_file (str): Path to input audio file
        output_dir (str): Directory to save output stems
        model_name (str): Demucs model to use (default: htdemucs)
    """
    try:
        # Check if input file exists
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        # Create output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        print(f"Loading audio file: {input_file}")
        
        # Use torchaudio's built-in Demucs pipeline for high-quality separation
        bundle = HDEMUCS_HIGH_MUSDB_PLUS
        model = bundle.get_model()
        
        # Load audio
        waveform, sample_rate = torchaudio.load(input_file)
        
        # Resample to model's expected sample rate if needed
        target_sample_rate = bundle.sample_rate
        if sample_rate != target_sample_rate:
            print(f"Resampling from {sample_rate}Hz to {target_sample_rate}Hz")
            resampler = torchaudio.transforms.Resample(sample_rate, target_sample_rate)
            waveform = resampler(waveform)
            sample_rate = target_sample_rate
        
        # Convert to mono if stereo (Demucs expects stereo, so we'll convert back if needed)
        if waveform.shape[0] == 1:
            # Convert mono to stereo by duplicating the channel
            waveform = waveform.repeat(2, 1)
        
        print("Separating audio into stems...")
        
        # Move to GPU if available
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model = model.to(device)
        waveform = waveform.to(device)
        
        # Add batch dimension
        waveform = waveform.unsqueeze(0)
        
        # Separate the audio
        with torch.no_grad():
            sources = model(waveform)
        
        # Move back to CPU for saving
        sources = sources.cpu().squeeze(0)
        
        # Get source names from the model
        source_names = model.sources  # ['drums', 'bass', 'other', 'vocals']
        
        # Save the separated stems
        input_filename = Path(input_file).stem
        
        for i, source_name in enumerate(source_names):
            output_filename = f"{input_filename}_{source_name}.wav"
            output_filepath = output_path / output_filename
            
            # Save the stem
            torchaudio.save(output_filepath, sources[i], sample_rate)
            print(f"Saved: {output_filepath}")
        
        print(f"✅ Audio separation complete! Files saved to: {output_dir}")
        print(f"📊 Separated into: {', '.join(source_names)}")
        
    except Exception as e:
        print(f"❌ Error during audio separation: {str(e)}")
        if "CUDA out of memory" in str(e):
            print("💡 Try using CPU instead of GPU by setting CUDA_VISIBLE_DEVICES=\"\"")
        sys.exit(1)

def split_audio_cli(input_file, output_dir="output"):
    """
    Alternative method using Demucs command line (if you have demucs installed via pip)
    """
    try:
        # Check if input file exists
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        # Create output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        print(f"Using Demucs CLI to separate: {input_file}")
        
        # Run demucs command
        cmd = f'python -m demucs --two-stems=vocals "{input_file}" -o "{output_dir}"'
        result = os.system(cmd)
        
        if result == 0:
            print(f"✅ Audio separation complete! Files saved to: {output_dir}")
        else:
            raise RuntimeError("Demucs CLI command failed")
            
    except Exception as e:
        print(f"❌ Error during CLI separation: {str(e)}")
        print("💡 Falling back to PyTorch method...")
        split_audio(input_file, output_dir)

def main():
    parser = argparse.ArgumentParser(
        description="Split audio tracks into stems using Demucs AI"
    )
    parser.add_argument(
        "input_file",
        help="Path to input audio file (supports WAV, MP3, FLAC, etc.)"
    )
    parser.add_argument(
        "-o", "--output",
        default="output",
        help="Output directory for separated stems (default: output)"
    )
    parser.add_argument(
        "--method",
        choices=["pytorch", "cli"],
        default="pytorch",
        help="Method to use: pytorch (built-in) or cli (requires demucs package)"
    )
    parser.add_argument(
        "--device",
        choices=["auto", "cpu", "cuda"],
        default="auto",
        help="Device to use for processing"
    )
    
    args = parser.parse_args()
    
    print("🎵 Audio Splitter using Demucs AI")
    print("=" * 40)
    print(f"Input file: {args.input_file}")
    print(f"Output directory: {args.output}")
    print(f"Method: {args.method}")
    print(f"Device: {args.device}")
    print("=" * 40)
    
    # Set device
    if args.device == "cpu":
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
    elif args.device == "cuda" and not torch.cuda.is_available():
        print("⚠️  CUDA not available, falling back to CPU")
    
    if args.method == "cli":
        split_audio_cli(args.input_file, args.output)
    else:
        split_audio(args.input_file, args.output)

if __name__ == "__main__":
    main() 
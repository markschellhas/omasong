#!/usr/bin/env python3
"""
Demo Example: Using the Audio Processing Suite
This script demonstrates how to use all the audio processing functions programmatically
"""

import os
import sys
from pathlib import Path

# Import functions from our scripts
try:
    from audio_splitter import split_audio
    from vocal_to_midi import vocal_to_midi
    print("✅ All modules imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all required dependencies are installed:")
    print("pip install -r requirements.txt")
    sys.exit(1)

def demo_audio_processing(input_audio_file):
    """
    Demonstrate the complete audio processing workflow
    
    Args:
        input_audio_file: Path to an audio file to process
    """
    
    print("🎵 Audio Processing Suite Demo")
    print("=" * 40)
    
    # Check if input file exists
    if not os.path.exists(input_audio_file):
        print(f"❌ Input file not found: {input_audio_file}")
        print("Please provide a valid audio file path")
        return
    
    # Create demo output directory
    demo_dir = Path("demo_output")
    demo_dir.mkdir(exist_ok=True)
    
    print(f"📁 Created demo directory: {demo_dir}")
    print(f"🎧 Processing file: {input_audio_file}")
    
    # Step 1: Split audio into stems
    print("\n" + "="*40)
    print("Step 1: Audio Stem Separation")
    print("="*40)
    
    stems_dir = demo_dir / "stems"
    
    try:
        split_audio(input_audio_file, str(stems_dir))
        print("✅ Audio separation completed")
    except Exception as e:
        print(f"❌ Error in audio separation: {e}")
        return
    
    # Step 2: Convert vocals to MIDI
    print("\n" + "="*40)
    print("Step 2: Vocal to MIDI Conversion")
    print("="*40)
    
    # Find the vocal stem
    input_name = Path(input_audio_file).stem
    vocal_file = stems_dir / f"{input_name}_vocals.wav"
    
    if not vocal_file.exists():
        print(f"❌ Vocal stem not found: {vocal_file}")
        print("This might happen if the input doesn't contain clear vocals")
        return
    
    # Convert vocals to MIDI
    midi_file = demo_dir / f"{input_name}_melody.mid"
    
    try:
        vocal_to_midi(str(vocal_file), str(midi_file))
        print("✅ Vocal to MIDI conversion completed")
    except Exception as e:
        print(f"❌ Error in vocal to MIDI conversion: {e}")
        return
    
    # Step 3: Summary
    print("\n" + "="*40)
    print("🎉 Demo Completed Successfully!")
    print("="*40)
    
    print(f"📁 Output directory: {demo_dir}")
    print(f"📋 Generated files:")
    
    # List all generated files
    for file in demo_dir.rglob("*"):
        if file.is_file():
            file_size = file.stat().st_size / (1024 * 1024)  # Size in MB
            print(f"   • {file.name} ({file_size:.1f} MB)")
    
    print(f"\n🎯 What you can do next:")
    print(f"   1. Import {midi_file.name} into your DAW")
    print(f"   2. Use the separated stems for remixing")
    print(f"   3. Create karaoke tracks from the instrumental stems")
    print(f"   4. Analyze the melody structure")

def main():
    """
    Main demo function
    """
    
    print("🚀 Audio Processing Suite Demo")
    print("-" * 30)
    
    # You can either provide a file path as command line argument
    # or hardcode a path here for testing
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        # Example: Replace this with your own audio file path
        input_file = "example_song.mp3"
        
        print(f"No input file provided. Using default: {input_file}")
        print("Usage: python demo_example.py path/to/your/audio/file.mp3")
        
        if not os.path.exists(input_file):
            print(f"\n❌ Example file '{input_file}' not found.")
            print("Please provide a valid audio file:")
            print("python demo_example.py path/to/your/song.mp3")
            return
    
    # Run the demo
    demo_audio_processing(input_file)

if __name__ == "__main__":
    main() 
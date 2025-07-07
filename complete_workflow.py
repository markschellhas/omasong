#!/usr/bin/env python3
"""
Complete Audio Processing Workflow
This script demonstrates using both the audio splitter and vocal-to-MIDI converter together
"""

import os
import sys
import argparse
from pathlib import Path
import subprocess

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Error: {result.stderr}")
            return False
        else:
            print(f"✅ {description} completed successfully")
            return True
    except Exception as e:
        print(f"❌ Error running command: {str(e)}")
        return False

def complete_workflow(input_file, output_dir="workflow_output"):
    """
    Complete workflow: Split audio into stems, then convert vocals to MIDI
    
    Args:
        input_file: Path to input audio file
        output_dir: Directory for all output files
    """
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    stems_dir = output_path / "stems"
    stems_dir.mkdir(exist_ok=True)
    
    print("🎵 Complete Audio Processing Workflow")
    print("=" * 50)
    print(f"Input file: {input_file}")
    print(f"Output directory: {output_dir}")
    print("=" * 50)
    
    # Step 1: Split audio into stems
    print("\n📦 Step 1: Splitting audio into stems...")
    split_cmd = f'python audio_splitter.py "{input_file}" -o "{stems_dir}"'
    
    if not run_command(split_cmd, "Audio splitting"):
        return False
    
    # Step 2: Find the vocal stem
    input_name = Path(input_file).stem
    vocal_file = stems_dir / f"{input_name}_vocals.wav"
    
    if not vocal_file.exists():
        print(f"❌ Vocal stem not found: {vocal_file}")
        return False
    
    print(f"✅ Found vocal stem: {vocal_file}")
    
    # Step 3: Convert vocals to MIDI
    print("\n🎹 Step 2: Converting vocals to MIDI...")
    midi_file = output_path / f"{input_name}_melody.mid"
    
    midi_cmd = f'python vocal_to_midi.py "{vocal_file}" -o "{midi_file}"'
    
    if not run_command(midi_cmd, "Vocal to MIDI conversion"):
        return False
    
    print(f"\n🎉 Workflow completed successfully!")
    print(f"📁 Output files:")
    print(f"   Stems directory: {stems_dir}")
    print(f"   MIDI melody: {midi_file}")
    
    # List all output files
    print(f"\n📋 Generated files:")
    for file in stems_dir.glob("*.wav"):
        print(f"   🎵 {file.name}")
    if midi_file.exists():
        print(f"   🎹 {midi_file.name}")
    
    return True

def main():
    parser = argparse.ArgumentParser(
        description="Complete workflow: Split audio into stems and convert vocals to MIDI"
    )
    parser.add_argument(
        "input_file",
        help="Path to input audio file (WAV, MP3, etc.)"
    )
    parser.add_argument(
        "-o", "--output",
        default="workflow_output",
        help="Output directory for all files (default: workflow_output)"
    )
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.exists(args.input_file):
        print(f"❌ Input file not found: {args.input_file}")
        sys.exit(1)
    
    # Check if required scripts exist
    required_scripts = ["audio_splitter.py", "vocal_to_midi.py"]
    missing_scripts = []
    
    for script in required_scripts:
        if not os.path.exists(script):
            missing_scripts.append(script)
    
    if missing_scripts:
        print(f"❌ Missing required scripts: {', '.join(missing_scripts)}")
        print("Make sure both audio_splitter.py and vocal_to_midi.py are in the same directory")
        sys.exit(1)
    
    # Run the complete workflow
    success = complete_workflow(args.input_file, args.output)
    
    if success:
        print("\n🎊 All done! You now have:")
        print("   • Separated audio stems (vocals, drums, bass, other)")
        print("   • MIDI melody extracted from vocals")
        print("   • Ready for further music production!")
    else:
        print("\n❌ Workflow failed. Check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 
#!/bin/bash

# Audio Processing Suite Setup Script
# This script helps you get started with the audio processing tools

echo "🎵 Audio Processing Suite Setup"
echo "================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check Python version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "🔄 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Test imports
echo "🧪 Testing imports..."
python3 -c "
import torch
import torchaudio
import librosa
import pretty_midi
print('✅ All required packages imported successfully')
"

if [ $? -eq 0 ]; then
    echo "✅ All imports successful"
else
    echo "❌ Import test failed"
    exit 1
fi

# Check for GPU support
echo "🔍 Checking GPU support..."
python3 -c "
import torch
if torch.cuda.is_available():
    print(f'✅ GPU available: {torch.cuda.get_device_name(0)}')
    print(f'   Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB')
else:
    print('ℹ️  No GPU available - will use CPU (slower but works)')
"

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "📋 Available scripts:"
echo "   • audio_splitter.py - Split audio into stems"
echo "   • vocal_to_midi.py - Convert vocals to MIDI"
echo "   • complete_workflow.py - Full processing pipeline"
echo "   • demo_example.py - Programmatic demo"
echo ""
echo "📖 Quick start examples:"
echo "   python audio_splitter.py your_song.mp3"
echo "   python vocal_to_midi.py vocal_track.wav"
echo "   python complete_workflow.py your_song.mp3"
echo ""
echo "💡 For help on any script, run: python script_name.py --help"
echo ""
echo "🚀 Ready to process some audio!" 
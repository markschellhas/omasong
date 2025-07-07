# Audio Splitter using Demucs

A Python script to split audio tracks into separate stems (vocals, drums, bass, other instruments) using Meta's Demucs AI model.

## Features

- **High-quality separation**: Uses the state-of-the-art Demucs AI model
- **4-stem separation**: Separates into vocals, drums, bass, and other instruments
- **Multiple audio formats**: Supports WAV, MP3, FLAC, and more
- **GPU acceleration**: Automatic GPU usage when available
- **Easy to use**: Simple command-line interface

## Installation

1. **Clone or download this repository**

2. **Set up Python environment** (Python 3.8+ required):
   ```bash
   # Create virtual environment (recommended)
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage
```bash
python audio_splitter.py path/to/your/song.mp3
```

### Specify Output Directory
```bash
python audio_splitter.py path/to/your/song.mp3 -o separated_tracks
```

### Force CPU Usage (if you have GPU memory issues)
```bash
python audio_splitter.py path/to/your/song.mp3 --device cpu
```

### Use Demucs CLI Method (requires installing demucs package)
```bash
# First install demucs: pip install demucs
python audio_splitter.py path/to/your/song.mp3 --method cli
```

## Output

The script will create four separate files:
- `song_vocals.wav` - Isolated vocals
- `song_drums.wav` - Drum tracks
- `song_bass.wav` - Bass lines
- `song_other.wav` - Other instruments (guitars, keyboards, etc.)

## System Requirements

- **Memory**: At least 4GB RAM (8GB+ recommended)
- **GPU**: Optional but recommended for faster processing
- **Storage**: Output files will be roughly the same size as input

## Troubleshooting

### CUDA Out of Memory
If you get GPU memory errors:
```bash
python audio_splitter.py your_song.mp3 --device cpu
```

### Audio Format Issues
The script supports most common audio formats. If you encounter issues, try converting your file to WAV first.

### Performance Tips
- GPU processing is much faster than CPU
- Longer songs require more memory
- Close other applications to free up RAM/GPU memory

## Examples

```bash
# Basic separation
python audio_splitter.py "my_song.mp3"

# Custom output directory
python audio_splitter.py "my_song.mp3" -o "stems_output"

# CPU only (slower but uses less memory)
python audio_splitter.py "my_song.mp3" --device cpu
```

## About Demucs

This script uses Meta's Demucs model, which is currently one of the best open-source audio separation systems available. It uses deep learning to intelligently separate audio sources while maintaining high audio quality.

## License

This project is provided as-is for educational and personal use. 
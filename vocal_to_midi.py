#!/usr/bin/env python3
"""
Vocal to MIDI Converter
This script converts vocal tracks to MIDI files by detecting pitch and melody
"""

import os
import argparse
import sys
from pathlib import Path
import numpy as np
import librosa
import pretty_midi
from scipy.signal import medfilt
from scipy.ndimage import uniform_filter1d
import soundfile as sf

def detect_pitch(audio, sr, frame_length=2048, hop_length=512):
    """
    Detect pitch from audio using librosa's piptrack with fallback methods
    
    Args:
        audio: Audio time series
        sr: Sample rate
        frame_length: Length of FFT window
        hop_length: Number of samples between frames
    
    Returns:
        times: Time stamps for each frame
        pitches: Fundamental frequency for each frame
        magnitudes: Magnitude of the pitch
    """
    try:
        # Method 1: Try piptrack with newer librosa versions
        pitches, magnitudes = librosa.piptrack(
            y=audio, 
            sr=sr, 
            threshold=0.1,
            fmin=80.0,  # Minimum frequency (around E2)
            fmax=2000.0,  # Maximum frequency (around B6)
            hop_length=hop_length
        )
    except Exception as e:
        print(f"piptrack failed ({e}), trying alternative method...")
        
        # Method 2: Use yin algorithm as fallback
        try:
            f0 = librosa.yin(audio, 
                            fmin=80.0, 
                            fmax=2000.0, 
                            sr=sr, 
                            hop_length=hop_length)
            
            # Convert to piptrack-like format
            times = librosa.frames_to_time(np.arange(len(f0)), sr=sr, hop_length=hop_length)
            return times, f0, np.ones_like(f0)
            
        except Exception as e2:
            print(f"yin failed ({e2}), using basic spectral method...")
            
            # Method 3: Basic spectral centroid as last resort
            spec_cent = librosa.feature.spectral_centroid(y=audio, sr=sr, hop_length=hop_length)[0]
            times = librosa.frames_to_time(np.arange(len(spec_cent)), sr=sr, hop_length=hop_length)
            
            # Convert spectral centroid to approximate pitch
            pitch_track = spec_cent * 0.5  # Rough approximation
            return times, pitch_track, np.ones_like(pitch_track)
    
    # Select the pitch with highest magnitude at each time frame
    pitch_track = []
    for t in range(pitches.shape[1]):
        index = magnitudes[:, t].argmax()
        pitch = pitches[index, t]
        pitch_track.append(pitch)
    
    # Convert to numpy array
    pitch_track = np.array(pitch_track)
    
    # Create time axis
    times = librosa.times_like(pitch_track, sr=sr, hop_length=hop_length)
    
    return times, pitch_track, magnitudes

def smooth_pitch(pitch_track, window_size=5, aggressive_smoothing=True):
    """
    Smooth pitch track to remove spurious detections
    
    Args:
        pitch_track: Array of pitch values
        window_size: Size of median filter window
        aggressive_smoothing: Apply more aggressive smoothing for musical results
    
    Returns:
        Smoothed pitch track
    """
    # Set zero pitches to NaN for filtering
    pitch_track[pitch_track == 0] = np.nan
    
    # Apply median filter to smooth the pitch track
    smoothed = medfilt(pitch_track, kernel_size=window_size)
    
    if aggressive_smoothing:
        # Apply additional smoothing for more musical results
        # Use a larger window for more stable pitch detection (ensure odd kernel size)
        larger_window = window_size * 2 if (window_size * 2) % 2 == 1 else (window_size * 2) + 1
        smoothed = medfilt(smoothed, kernel_size=larger_window)
        
        # Apply moving average to further smooth
        smoothed = uniform_filter1d(smoothed, size=window_size, mode='nearest')
    
    return smoothed

def hz_to_midi(frequencies):
    """
    Convert frequencies in Hz to MIDI note numbers
    
    Args:
        frequencies: Array of frequencies in Hz
    
    Returns:
        Array of MIDI note numbers
    """
    # A4 = 440 Hz = MIDI note 69
    midi_notes = np.zeros_like(frequencies)
    valid_freqs = frequencies > 0
    
    midi_notes[valid_freqs] = 69 + 12 * np.log2(frequencies[valid_freqs] / 440.0)
    
    return midi_notes

def quantize_timing(time_value, beat_subdivision=4):
    """
    Quantize timing to musical beats
    
    Args:
        time_value: Time in seconds
        beat_subdivision: How many subdivisions per beat (4 = sixteenth notes)
    
    Returns:
        Quantized time value
    """
    # Assume 120 BPM for quantization (can be adjusted)
    beat_duration = 60.0 / 120.0  # 0.5 seconds per beat at 120 BPM
    subdivision_duration = beat_duration / beat_subdivision
    
    # Round to nearest subdivision
    quantized = round(time_value / subdivision_duration) * subdivision_duration
    return quantized

def create_midi_notes(times, midi_notes, min_note_duration=0.3, velocity=80, 
                     pitch_threshold=1.0, quantize_timing=False):
    """
    Create MIDI notes from pitch track with improved musicality
    
    Args:
        times: Time stamps
        midi_notes: MIDI note numbers
        min_note_duration: Minimum note duration in seconds (increased default)
        velocity: MIDI velocity (0-127)
        pitch_threshold: Minimum semitone change to trigger new note
        quantize_timing: Whether to quantize note timing to beats
    
    Returns:
        List of MIDI note events
    """
    notes = []
    
    if len(midi_notes) == 0:
        return notes
    
    # Find note onsets (where pitch changes significantly)
    # Use larger threshold for less sensitivity
    note_changes = np.diff(np.round(midi_notes))
    onset_indices = np.where(np.abs(note_changes) > pitch_threshold)[0] + 1
    
    # Add start and end indices
    onset_indices = np.concatenate([[0], onset_indices, [len(midi_notes) - 1]])
    
    for i in range(len(onset_indices) - 1):
        start_idx = onset_indices[i]
        end_idx = onset_indices[i + 1]
        
        # Get the most common note in this segment
        segment_notes = midi_notes[start_idx:end_idx]
        valid_notes = segment_notes[segment_notes > 0]
        
        if len(valid_notes) > 0:
            # Use the median note in the segment (more stable than mean)
            note_number = int(np.round(np.median(valid_notes)))
            
            # Only add notes in valid MIDI range
            if 0 <= note_number <= 127:
                start_time = times[start_idx]
                end_time = times[end_idx]
                duration = end_time - start_time
                
                # Only add notes that meet minimum duration
                if duration >= min_note_duration:
                    # Optionally quantize timing
                    if quantize_timing:
                        start_time = quantize_timing(start_time)
                        end_time = start_time + max(duration, min_note_duration)
                    
                    notes.append({
                        'pitch': note_number,
                        'start': start_time,
                        'end': end_time,
                        'velocity': velocity
                    })
    
    return notes

def vocal_to_midi(input_file, output_file, min_note_duration=0.3, velocity=80, 
                  pitch_threshold=1.0, quantize_timing=False, aggressive_smoothing=True):
    """
    Convert vocal track to MIDI file with improved musicality
    
    Args:
        input_file: Path to input audio file
        output_file: Path to output MIDI file
        min_note_duration: Minimum note duration in seconds (default: 0.3 for more musical results)
        velocity: MIDI velocity (0-127)
        pitch_threshold: Minimum semitone change to trigger new note (default: 1.0)
        quantize_timing: Whether to quantize note timing to beats
        aggressive_smoothing: Apply more aggressive pitch smoothing
    """
    try:
        print(f"Loading audio file: {input_file}")
        
        # Load audio file
        audio, sr = librosa.load(input_file, sr=22050)
        
        # Normalize audio
        audio = librosa.util.normalize(audio)
        
        print("Detecting pitch...")
        
        # Detect pitch
        times, pitch_track, magnitudes = detect_pitch(audio, sr)
        
        print("Smoothing pitch track...")
        
        # Smooth pitch track with configurable aggressiveness
        smoothed_pitch = smooth_pitch(pitch_track, window_size=7, aggressive_smoothing=aggressive_smoothing)
        
        print("Converting to MIDI notes...")
        
        # Convert to MIDI notes
        midi_notes = hz_to_midi(smoothed_pitch)
        
        # Create MIDI note events with improved musicality
        note_events = create_midi_notes(times, midi_notes, min_note_duration, velocity, 
                                      pitch_threshold, quantize_timing)
        
        print(f"Found {len(note_events)} notes")
        
        if len(note_events) == 0:
            print("⚠️  No notes detected. Try adjusting parameters or check if input contains vocals.")
            return
        
        print("Creating MIDI file...")
        
        # Create MIDI file
        midi_file = pretty_midi.PrettyMIDI()
        
        # Create instrument (General MIDI: 0 = Piano, 53 = Voice)
        instrument = pretty_midi.Instrument(program=53, name="Vocal Melody")
        
        # Add notes to instrument
        for note_event in note_events:
            note = pretty_midi.Note(
                velocity=note_event['velocity'],
                pitch=note_event['pitch'],
                start=note_event['start'],
                end=note_event['end']
            )
            instrument.notes.append(note)
        
        # Add instrument to MIDI file
        midi_file.instruments.append(instrument)
        
        # Save MIDI file
        midi_file.write(output_file)
        
        print(f"✅ MIDI file saved: {output_file}")
        
        # Print some statistics
        total_duration = times[-1] if len(times) > 0 else 0
        note_coverage = sum(note['end'] - note['start'] for note in note_events)
        coverage_percent = (note_coverage / total_duration) * 100 if total_duration > 0 else 0
        
        print(f"📊 Statistics:")
        print(f"   Total duration: {total_duration:.2f} seconds")
        print(f"   Number of notes: {len(note_events)}")
        print(f"   Note coverage: {coverage_percent:.1f}%")
        
        # Show note range
        if note_events:
            pitches = [note['pitch'] for note in note_events]
            min_pitch = min(pitches)
            max_pitch = max(pitches)
            print(f"   Note range: {pretty_midi.note_number_to_name(min_pitch)} to {pretty_midi.note_number_to_name(max_pitch)}")
        
    except Exception as e:
        print(f"❌ Error converting vocal to MIDI: {str(e)}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Convert vocal tracks to MIDI melody files"
    )
    parser.add_argument(
        "input_file",
        help="Path to input vocal audio file (WAV, MP3, etc.)"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output MIDI file path (default: input_name.mid)"
    )
    parser.add_argument(
        "--min-duration",
        type=float,
        default=0.3,
        help="Minimum note duration in seconds (default: 0.3 for more musical results)"
    )
    parser.add_argument(
        "--velocity",
        type=int,
        default=80,
        help="MIDI velocity (0-127, default: 80)"
    )
    parser.add_argument(
        "--pitch-threshold",
        type=float,
        default=1.0,
        help="Minimum semitone change to trigger new note (default: 1.0, higher = less sensitive)"
    )
    parser.add_argument(
        "--quantize",
        action="store_true",
        help="Quantize note timing to musical beats"
    )
    parser.add_argument(
        "--light-smoothing",
        action="store_true",
        help="Use lighter pitch smoothing (more detail but potentially noisier)"
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Show pitch detection preview (requires matplotlib)"
    )
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.exists(args.input_file):
        print(f"❌ Input file not found: {args.input_file}")
        sys.exit(1)
    
    # Generate output filename if not provided
    if not args.output:
        input_path = Path(args.input_file)
        output_path = input_path.with_suffix('.mid')
        args.output = str(output_path)
    
    print("🎵 Vocal to MIDI Converter")
    print("=" * 40)
    print(f"Input file: {args.input_file}")
    print(f"Output file: {args.output}")
    print(f"Min note duration: {args.min_duration}s")
    print(f"Pitch threshold: {args.pitch_threshold} semitones")
    print(f"Velocity: {args.velocity}")
    print(f"Quantize timing: {args.quantize}")
    print(f"Aggressive smoothing: {not args.light_smoothing}")
    print("=" * 40)
    
    # Convert vocal to MIDI with improved settings
    vocal_to_midi(args.input_file, args.output, args.min_duration, args.velocity,
                  args.pitch_threshold, args.quantize, not args.light_smoothing)
    
    # Show preview if requested
    if args.preview:
        try:
            import matplotlib.pyplot as plt
            
            print("Generating pitch preview...")
            
            # Load audio and detect pitch for preview
            audio, sr = librosa.load(args.input_file, sr=22050)
            times, pitch_track, _ = detect_pitch(audio, sr)
            smoothed_pitch = smooth_pitch(pitch_track, window_size=7, 
                                        aggressive_smoothing=not args.light_smoothing)
            
            # Plot
            plt.figure(figsize=(12, 6))
            plt.subplot(2, 1, 1)
            plt.plot(times, pitch_track, alpha=0.7, label='Raw pitch')
            plt.plot(times, smoothed_pitch, label='Smoothed pitch')
            plt.ylabel('Frequency (Hz)')
            plt.legend()
            plt.title('Pitch Detection')
            
            plt.subplot(2, 1, 2)
            midi_notes = hz_to_midi(smoothed_pitch)
            plt.plot(times, midi_notes, 'o-', markersize=2)
            plt.ylabel('MIDI Note Number')
            plt.xlabel('Time (s)')
            plt.title('MIDI Notes')
            
            plt.tight_layout()
            plt.show()
            
        except ImportError:
            print("⚠️  matplotlib not installed. Install with: pip install matplotlib")

if __name__ == "__main__":
    main() 
import * as Tone from 'tone';
import { chords } from '../stores/chords.js';
import { audioState } from '../stores/audio.js';

/**
 * Handles chord progression playback
 * Converts chord progressions to MIDI events and plays them
 */
class ChordPlayer extends EventTarget {
  /**
   * @private
   * @type {Tone.PolySynth}
   */
  #chordSynth = null;
  
  /**
   * @private
   * @type {Tone.Volume}
   */
  #chordVolume = null;
  
  /**
   * @private
   * @type {Tone.ToneEvent[]}
   */
  #scheduledChords = [];
  
  /**
   * @private
   * @type {import('../utils/audioEngine.js').AudioEngine}
   */
  #audioEngine = null;
  
  /**
   * @private
   * @type {Function}
   */
  #unsubscribeChords = null;
  
  /**
   * @private
   * @type {import('../stores/chords.js').ChordProgression}
   */
  #currentProgression = [];

  constructor(audioEngine) {
    super();
    this.#audioEngine = audioEngine;
    this.setupAudio();
    this.setupStoreSubscriptions();
  }

  /**
   * Set up audio chain for chord playback
   * @private
   */
  setupAudio() {
    // Wait for audio engine to be initialized before creating synth
    if (this.#audioEngine && this.#audioEngine.isInitialized()) {
      this.createChordSynth();
    } else {
      // Listen for audio engine initialization
      this.#audioEngine?.addEventListener('initialized', () => {
        this.createChordSynth();
      });
    }
  }
  
  /**
   * Create the chord synthesizer
   * @private
   */
  createChordSynth() {
    try {
      console.log('🎵 ChordPlayer: Creating chord synth...');
      
      // Create chord synthesizer (same as keyboard but different sound)
      this.#chordSynth = new Tone.PolySynth(Tone.Synth, {
        oscillator: { type: 'sawtooth' },
        envelope: { attack: 0.1, decay: 0.1, sustain: 0.7, release: 2 }
      });
      
      // Create volume control for chords
      this.#chordVolume = new Tone.Volume(-18); // Much quieter than before (-8 was too loud)
      
      // Connect synth through volume control to destination
      this.#chordSynth.chain(this.#chordVolume, Tone.Destination);
      
      console.log('🎵 ChordPlayer: Chord synth created with volume control at -18dB');
      
    } catch (error) {
      console.error('🎵 ChordPlayer: Failed to create chord synth:', error);
    }
  }

  /**
   * Set up store subscriptions
   * @private
   */
  setupStoreSubscriptions() {
    // Subscribe to chord changes
    this.#unsubscribeChords = chords.subscribe(progression => {
      console.log('🎵 ChordPlayer: Chord progression updated', progression);
      this.#currentProgression = progression;
    });
    
    // Subscribe to audio state changes
    audioState.subscribe(state => {
      console.log('🎵 ChordPlayer: Audio state change', { 
        isPlaying: state.isPlaying, 
        isScheduled: this.isChordPlaybackScheduled() 
      });
      
      if (state.isPlaying && !this.isChordPlaybackScheduled()) {
        console.log('🎵 ChordPlayer: Starting chord playback');
        this.scheduleChordPlayback();
      } else if (!state.isPlaying) {
        console.log('🎵 ChordPlayer: Stopping chord playback');
        this.stopChordPlayback();
      }
    });
  }

  /**
   * Schedule chord progression for playback
   */
  scheduleChordPlayback() {
    try {
      console.log('🎵 ChordPlayer: Scheduling chord playback', this.#currentProgression);
      
      // Clear any existing scheduled chords
      this.clearScheduledChords();
      
      // Don't schedule if no chords or no audio setup
      if (!this.#currentProgression.length || !this.#chordSynth) {
        console.log('🎵 ChordPlayer: No chords to schedule or audio not ready');
        return;
      }
      
      // Schedule each chord
      for (const chord of this.#currentProgression) {
        this.scheduleChord(chord);
      }
      
      console.log('🎵 ChordPlayer: Scheduled', this.#scheduledChords.length, 'chords');
      
    } catch (error) {
      console.error('🎵 ChordPlayer: Failed to schedule chord playback:', error);
    }
  }

  /**
   * Schedule a single chord for playback
   * @private
   * @param {import('../stores/chords.js').Chord} chord - Chord to schedule
   */
  scheduleChord(chord) {
    if (!chord.notes || chord.notes.length === 0) {
      console.warn('🎵 ChordPlayer: Chord has no notes:', chord);
      return;
    }
    
    if (!this.#chordSynth) {
      console.warn('🎵 ChordPlayer: No chord synth available for scheduling');
      return;
    }
    
    // Calculate when to play the chord - simpler approach using seconds
    const startTimeInSeconds = chord.measure * 4 * (60 / Tone.Transport.bpm.value); // measure * beats per measure * seconds per beat
    
    console.log('🎵 ChordPlayer: Scheduling chord', { 
      symbol: chord.symbol, 
      measure: chord.measure, 
      startTimeInSeconds,
      currentBPM: Tone.Transport.bpm.value,
      notes: chord.notes 
    });
    
    // Schedule the chord directly with transport
    const chordEvent = Tone.Transport.schedule((time) => {
      this.playChord(chord, time);
    }, startTimeInSeconds);
    
    this.#scheduledChords.push(chordEvent);
  }

  /**
   * Play a single chord
   * @private
   * @param {import('../stores/chords.js').Chord} chord - Chord to play
   * @param {number} time - When to play
   */
  playChord(chord, time) {
    if (!this.#chordSynth || !chord.notes || chord.notes.length === 0) {
      console.warn('🎵 ChordPlayer: Cannot play chord - missing synth or notes');
      return;
    }
    
    try {
      // Convert MIDI note numbers to frequencies
      const frequencies = chord.notes.map(note => Tone.Frequency(note, 'midi'));
      
      console.log('🎵 ChordPlayer: Playing chord', { 
        symbol: chord.symbol, 
        frequencies: frequencies.map(f => f.toFrequency()),
        time
      });
      
      // Trigger the chord for 1 measure duration (same approach as preview)
      this.#chordSynth.triggerAttackRelease(frequencies, '1m', time, 0.6);
      
      // Dispatch event for visualization
      this.dispatchEvent(new CustomEvent('chordPlayed', {
        detail: { 
          chord, 
          notes: chord.notes,
          time
        }
      }));
      
    } catch (error) {
      console.error('🎵 ChordPlayer: Failed to play chord:', error);
    }
  }

  /**
   * Stop chord playback and clear scheduled events
   */
  stopChordPlayback() {
    try {
      this.clearScheduledChords();
      
      // Stop any currently playing chords
      if (this.#chordSynth) {
        this.#chordSynth.releaseAll();
      }
      
      console.log('🎵 ChordPlayer: Stopped chord playback');
      
    } catch (error) {
      console.error('🎵 ChordPlayer: Failed to stop chord playback:', error);
    }
  }

  /**
   * Clear all scheduled chord events
   * @private
   */
  clearScheduledChords() {
    for (const eventId of this.#scheduledChords) {
      Tone.Transport.clear(eventId);
    }
    this.#scheduledChords = [];
  }

  /**
   * Check if chord playback is currently scheduled
   * @returns {boolean} Is scheduled
   */
  isChordPlaybackScheduled() {
    return this.#scheduledChords.length > 0;
  }

  /**
   * Preview a single chord (for chord cell clicks)
   * @param {import('../stores/chords.js').Chord} chord - Chord to preview
   */
  previewChord(chord) {
    if (!this.#chordSynth || !chord.notes || chord.notes.length === 0) {
      console.warn('🎵 ChordPlayer: Cannot preview chord - no synth or notes', {
        synth: !!this.#chordSynth,
        notes: chord.notes
      });
      return;
    }
    
    try {
      // Convert MIDI note numbers to frequencies
      const frequencies = chord.notes.map(note => Tone.Frequency(note, 'midi'));
      
      console.log('🎵 ChordPlayer: Previewing chord', {
        symbol: chord.symbol,
        frequencies: frequencies.map(f => f.toFrequency())
      });
      
      // Play the chord immediately for 1 second
      this.#chordSynth.triggerAttackRelease(frequencies, '1n', undefined, 0.5);
      
    } catch (error) {
      console.error('🎵 ChordPlayer: Failed to preview chord:', error);
    }
  }
  
  /**
   * Test chord player with a simple C major chord
   */
  testChordPlayer() {
    console.log('🎵 ChordPlayer: Testing with C major chord...');
    
    const testChord = {
      symbol: 'C',
      measure: 0,
      beat: 0,
      duration: 4,
      notes: [60, 64, 67], // C, E, G
      noteNames: ['C4', 'E4', 'G4']
    };
    
    this.previewChord(testChord);
  }

  /**
   * Set chord volume
   * @param {number} volume - Volume (0-1)
   */
  setVolume(volume) {
    if (this.#chordVolume) {
      // Convert linear volume to dB, with additional -12dB offset to keep chords quieter
      const dbValue = volume === 0 ? -Infinity : (20 * Math.log10(volume)) - 12;
      this.#chordVolume.volume.value = dbValue;
      console.log(`🎵 ChordPlayer: Set volume to ${volume} (${dbValue.toFixed(1)}dB)`);
    }
  }
  
  /**
   * Get current chord volume
   * @returns {number} Current volume (0-1)
   */
  getVolume() {
    if (this.#chordVolume) {
      const dbValue = this.#chordVolume.volume.value;
      if (dbValue === -Infinity) return 0;
      // Convert back from dB to linear, accounting for the -12dB offset
      return Math.pow(10, (dbValue + 12) / 20);
    }
    return 0.5; // Default
  }

  /**
   * Dispose of the chord player
   */
  dispose() {
    try {
      this.stopChordPlayback();
      
      if (this.#unsubscribeChords) {
        this.#unsubscribeChords();
      }
      
      if (this.#chordSynth) {
        this.#chordSynth.dispose();
      }
      
      if (this.#chordVolume) {
        this.#chordVolume.dispose();
      }
      
    } catch (error) {
      console.error('🎵 ChordPlayer: Failed to dispose:', error);
    }
  }
}

// Singleton instance
let chordPlayerInstance = null;

/**
 * Get the singleton chord player instance
 * @param {import('../utils/audioEngine.js').AudioEngine} [audioEngine] - Audio engine instance (required on first call)
 * @returns {ChordPlayer} Chord player instance
 */
export function getChordPlayer(audioEngine = null) {
  if (!chordPlayerInstance && audioEngine) {
    chordPlayerInstance = new ChordPlayer(audioEngine);
    console.log('🎵 ChordPlayer: Created singleton instance');
    
    // Temporarily add to window for debugging
    if (typeof window !== 'undefined') {
      window.chordPlayer = chordPlayerInstance;
      console.log('🎵 ChordPlayer added to window.chordPlayer for testing');
      console.log('🎵 Use window.chordPlayer.setVolume(0.3) to adjust chord volume (0-1)');
    }
  }
  return chordPlayerInstance;
}

/**
 * Create a new chord player instance
 * @param {import('../utils/audioEngine.js').AudioEngine} audioEngine - Audio engine instance
 * @returns {ChordPlayer} New chord player instance
 */
export function createChordPlayer(audioEngine) {
  return new ChordPlayer(audioEngine);
}

export default ChordPlayer; 
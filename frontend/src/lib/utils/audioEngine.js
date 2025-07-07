import * as Tone from 'tone';
import { audioState } from '../stores/audio.js';

/**
 * Core audio engine for handling MIDI recording and playback
 * Implements singleton pattern for global audio management
 */
class AudioEngine extends EventTarget {
  /**
   * @private
   * @type {Tone.Transport}
   */
  #transport;
  
  /**
   * @private
   * @type {Tone.MetalSynth}
   */
  #metronome;
  
  /**
   * @private
   * @type {Tone.Volume}
   */
  #masterVolume;
  
  /**
   * @private
   * @type {boolean}
   */
  #isInitialized = false;
  
  /**
   * @private
   * @type {number}
   */
  #countInTimer = null;
  
  /**
   * @private
   * @type {Function}
   */
  #onCountInComplete = null;
  
  /**
   * @private
   * @type {number}
   */
  #playheadUpdateInterval = null;

  constructor() {
    super();
    this.#transport = Tone.Transport;
    this.#setupTransportCallbacks();
  }

  /**
   * Initialize the audio engine
   * Must be called after user interaction to activate audio context
   * @returns {Promise<boolean>} Success status
   */
  async initialize() {
    try {
      if (this.#isInitialized) return true;
      
      // Start audio context (requires user interaction)
      await Tone.start();
      
      // Set up the audio chain - master chain first so metronome can connect to it
      this.#setupMasterChain();
      this.#setupMetronome();
      
      // Set initial tempo
      this.#transport.bpm.value = 120;
      
      this.#isInitialized = true;
      
      this.dispatchEvent(new CustomEvent('initialized'));
      console.log('Audio engine initialized successfully');
      
      return true;
    } catch (error) {
      console.error('Failed to initialize audio engine:', error);
      this.dispatchEvent(new CustomEvent('initializationError', { detail: error }));
      return false;
    }
  }

  /**
   * Set up the master audio chain
   * @private
   */
  #setupMasterChain() {
    this.#masterVolume = new Tone.Volume(-6); // Slightly lower master volume
    this.#masterVolume.toDestination();
  }

  /**
   * Set up metronome
   * @private
   */
  #setupMetronome() {
    this.#metronome = new Tone.MetalSynth({
      frequency: 800,
      envelope: {
        attack: 0.001,
        decay: 0.1,
        release: 0.01
      },
      harmonicity: 8,
      modulationIndex: 2,
      resonance: 4000,
      octaves: 1
    });
    
    // Connect metronome through master volume
    this.#metronome.connect(this.#masterVolume);
  }

  /**
   * Set up transport callbacks for playhead updates
   * @private
   */
  #setupTransportCallbacks() {
    // Update playhead position during playback
    this.#transport.scheduleRepeat((time) => {
      const position = this.#transport.position;
      const positionInBeats = Tone.Time(position).toBarsBeatsSixteenths();
      
      // Dispatch playhead update event
      this.dispatchEvent(new CustomEvent('playheadUpdate', {
        detail: { 
          position: Tone.Time(position).toSeconds(),
          beats: this.#transportPositionToBeats(position)
        }
      }));
      
      // Update audio state store
      audioState.updatePlayhead(this.#transportPositionToBeats(position));
    }, '16n'); // Update every sixteenth note
  }

  /**
   * Convert transport position to beats
   * @private
   * @param {string} position - Transport position
   * @returns {number} Position in beats
   */
  #transportPositionToBeats(position) {
    const time = Tone.Time(position);
    return time.toSeconds() * (this.#transport.bpm.value / 60);
  }

  /**
   * Start playback
   * @returns {Promise<boolean>} Success status
   */
  async play() {
    try {
      if (!this.#isInitialized) {
        await this.initialize();
      }
      
      this.#transport.start();
      audioState.play();
      
      this.dispatchEvent(new CustomEvent('playbackStarted'));
      
      return true;
    } catch (error) {
      console.error('Failed to start playback:', error);
      return false;
    }
  }

  /**
   * Pause playback
   * @returns {boolean} Success status
   */
  pause() {
    try {
      this.#transport.pause();
      audioState.pause();
      
      this.dispatchEvent(new CustomEvent('playbackPaused'));
      
      return true;
    } catch (error) {
      console.error('Failed to pause playback:', error);
      return false;
    }
  }

  /**
   * Stop playback and reset position
   * @returns {boolean} Success status
   */
  stop() {
    try {
      this.#transport.stop();
      this.#transport.position = 0;
      audioState.stop();
      
      this.dispatchEvent(new CustomEvent('playbackStopped'));
      
      return true;
    } catch (error) {
      console.error('Failed to stop playback:', error);
      return false;
    }
  }

  /**
   * Set tempo
   * @param {number} bpm - Beats per minute (60-200)
   * @returns {boolean} Success status
   */
  setTempo(bpm) {
    try {
      const clampedBpm = Math.max(60, Math.min(200, bpm));
      this.#transport.bpm.value = clampedBpm;
      audioState.setTempo(clampedBpm);
      
      this.dispatchEvent(new CustomEvent('tempoChanged', { detail: clampedBpm }));
      
      return true;
    } catch (error) {
      console.error('Failed to set tempo:', error);
      return false;
    }
  }

  /**
   * Get current tempo
   * @returns {number} Current BPM
   */
  getTempo() {
    return this.#transport.bpm.value;
  }

  /**
   * Enable/disable metronome
   * @param {boolean} enabled - Whether metronome should be enabled
   * @returns {boolean} Success status
   */
  setMetronomeEnabled(enabled) {
    try {
      if (enabled) {
        this.#scheduleMetronome();
      } else {
        this.#clearMetronome();
      }
      
      audioState.toggleMetronome();
      
      this.dispatchEvent(new CustomEvent('metronomeToggled', { detail: enabled }));
      
      return true;
    } catch (error) {
      console.error('Failed to toggle metronome:', error);
      return false;
    }
  }

  /**
   * Schedule metronome beats
   * @private
   */
  #scheduleMetronome() {
    // Schedule metronome on every beat
    this.#transport.scheduleRepeat((time) => {
      // Play metronome click
      this.#metronome.triggerAttackRelease('C5', '32n', time);
    }, '4n'); // Every quarter note (beat)
  }

  /**
   * Clear metronome scheduling
   * @private
   */
  #clearMetronome() {
    this.#transport.cancel();
    // Re-setup other scheduled events if needed
    this.#setupTransportCallbacks();
  }

  /**
   * Set metronome volume
   * @param {number} volume - Volume level (0-1)
   * @returns {boolean} Success status
   */
  setMetronomeVolume(volume) {
    try {
      const clampedVolume = Math.max(0, Math.min(1, volume));
      // Convert to dB scale
      const dbVolume = clampedVolume === 0 ? -Infinity : 20 * Math.log10(clampedVolume);
      this.#metronome.volume.value = dbVolume;
      
      audioState.setMetronomeVolume(clampedVolume);
      
      return true;
    } catch (error) {
      console.error('Failed to set metronome volume:', error);
      return false;
    }
  }

  /**
   * Start count-in sequence
   * @param {Function} onCountInComplete - Callback when count-in finishes
   * @param {number} beats - Number of beats to count in (default: 4)
   * @returns {boolean} Success status
   */
  startCountIn(onCountInComplete, beats = 4) {
    try {
      if (this.#countInTimer) {
        clearInterval(this.#countInTimer);
      }
      
      this.#onCountInComplete = onCountInComplete;
      let beatsRemaining = beats;
      
      audioState.startCountIn(beats);
      
      // Calculate interval based on current tempo
      const beatDuration = (60 / this.#transport.bpm.value) * 1000; // milliseconds
      
      this.#countInTimer = setInterval(() => {
        if (beatsRemaining > 0) {
          // Play metronome click for count-in
          this.#metronome.triggerAttackRelease('C6', '32n'); // Higher pitch for count-in
          
          audioState.updateCountIn(beatsRemaining);
          beatsRemaining--;
          
          this.dispatchEvent(new CustomEvent('countInBeat', { 
            detail: { beatsRemaining } 
          }));
        } else {
          // Count-in complete
          clearInterval(this.#countInTimer);
          this.#countInTimer = null;
          
          audioState.stopCountIn();
          
          this.dispatchEvent(new CustomEvent('countInComplete'));
          
          if (this.#onCountInComplete) {
            this.#onCountInComplete();
            this.#onCountInComplete = null;
          }
        }
      }, beatDuration);
      
      return true;
    } catch (error) {
      console.error('Failed to start count-in:', error);
      return false;
    }
  }

  /**
   * Stop count-in sequence
   * @returns {boolean} Success status
   */
  stopCountIn() {
    try {
      if (this.#countInTimer) {
        clearInterval(this.#countInTimer);
        this.#countInTimer = null;
      }
      
      audioState.stopCountIn();
      this.dispatchEvent(new CustomEvent('countInStopped'));
      
      return true;
    } catch (error) {
      console.error('Failed to stop count-in:', error);
      return false;
    }
  }

  /**
   * Seek to position
   * @param {number} positionInBeats - Position in beats
   * @returns {boolean} Success status
   */
  seek(positionInBeats) {
    try {
      const timeInSeconds = positionInBeats / (this.#transport.bpm.value / 60);
      this.#transport.position = timeInSeconds;
      
      audioState.seek(positionInBeats);
      
      this.dispatchEvent(new CustomEvent('seeked', { detail: positionInBeats }));
      
      return true;
    } catch (error) {
      console.error('Failed to seek:', error);
      return false;
    }
  }

  /**
   * Get current playhead position in beats
   * @returns {number} Current position in beats
   */
  getCurrentPosition() {
    return this.#transportPositionToBeats(this.#transport.position);
  }

  /**
   * Check if audio context is running
   * @returns {boolean} Audio context state
   */
  isAudioContextRunning() {
    return Tone.context.state === 'running';
  }

  /**
   * Get audio context state
   * @returns {string} Audio context state
   */
  getAudioContextState() {
    return Tone.context.state;
  }

  /**
   * Get master volume node for connecting audio chains
   * @returns {Tone.Volume} Master volume node
   */
  getMasterVolume() {
    return this.#masterVolume;
  }

  /**
   * Check if engine is initialized
   * @returns {boolean} Initialization state
   */
  isInitialized() {
    return this.#isInitialized;
  }

  /**
   * Dispose of all audio resources
   */
  dispose() {
    try {
      this.stop();
      this.stopCountIn();
      
      if (this.#metronome) {
        this.#metronome.dispose();
      }
      
      if (this.#masterVolume) {
        this.#masterVolume.dispose();
      }
      
      this.#isInitialized = false;
      
      this.dispatchEvent(new CustomEvent('disposed'));
      
    } catch (error) {
      console.error('Error disposing audio engine:', error);
    }
  }
}

// Create singleton instance
let audioEngineInstance = null;

/**
 * Get the singleton audio engine instance
 * @returns {AudioEngine} Audio engine instance
 */
export function getAudioEngine() {
  if (!audioEngineInstance) {
    audioEngineInstance = new AudioEngine();
  }
  return audioEngineInstance;
}

/**
 * Initialize and get audio engine (convenience function)
 * @returns {Promise<AudioEngine>} Initialized audio engine
 */
export async function initializeAudioEngine() {
  const engine = getAudioEngine();
  await engine.initialize();
  return engine;
}

// Export the AudioEngine class as well for type annotations
export { AudioEngine }; 
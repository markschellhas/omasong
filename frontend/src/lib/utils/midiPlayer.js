import * as Tone from 'tone';
import { tracks } from '../stores/tracks.js';
import { audioState } from '../stores/audio.js';

/**
 * Handles MIDI playback functionality
 * Plays back recorded MIDI events from tracks
 */
class MidiPlayer extends EventTarget {
  /**
   * @private
   * @type {Map<string, Tone.ToneEvent[]>}
   */
  #scheduledEvents = new Map();
  
  /**
   * @private
   * @type {Map<string, TrackAudio>}
   */
  #trackAudio = new Map();
  
  /**
   * @private
   * @type {boolean}
   */
  #isPlaying = false;
  
  /**
   * @private
   * @type {import('../utils/audioEngine.js').AudioEngine}
   */
  #audioEngine = null;
  
  /**
   * @private
   * @type {Function}
   */
  #unsubscribeTracks = null;
  
  /**
   * @private
   * @type {Set<number>}
   */
  #activeNotes = new Set();

  /**
   * @typedef {Object} TrackAudio
   * @property {Tone.PolySynth} synth - The synthesizer for this track
   * @property {Tone.Volume} volume - Volume control
   * @property {Tone.Panner} panner - Pan control
   * @property {Tone.Gain} gain - Additional gain stage
   */

  constructor(audioEngine) {
    super();
    this.#audioEngine = audioEngine;
    this.setupStoreSubscriptions();
  }

  /**
   * Set up subscriptions to track changes
   * @private
   */
  setupStoreSubscriptions() {
    this.#unsubscribeTracks = tracks.subscribe(trackList => {
      this.updateTrackAudio(trackList);
    });
  }

  /**
   * Update track audio chains when tracks change
   * @private
   * @param {import('../stores/tracks.js').Track[]} trackList - Current tracks
   */
  updateTrackAudio(trackList) {
    // Remove audio for deleted tracks
    for (const trackId of this.#trackAudio.keys()) {
      if (!trackList.find(t => t.id === trackId)) {
        this.removeTrackAudio(trackId);
      }
    }
    
    // Add/update audio for existing tracks
    for (const track of trackList) {
      if (!this.#trackAudio.has(track.id)) {
        this.createTrackAudio(track);
      } else {
        this.updateTrackAudioSettings(track);
      }
    }
  }

  /**
   * Create audio chain for a track
   * @private
   * @param {import('../stores/tracks.js').Track} track - Track to create audio for
   */
  createTrackAudio(track) {
    try {
      // Check if audio engine is initialized and has master volume
      const masterVolume = this.#audioEngine?.getMasterVolume();
      if (!masterVolume) {
        console.log(`🎵 MidiPlayer: Deferring audio creation for track ${track.id} - audio engine not ready`);
        return; // Audio engine not ready yet, will retry later
      }
      
      console.log(`🎵 MidiPlayer: Creating audio for track ${track.id} (${track.instrument})`);
      
      // Create synthesizer based on instrument type
      const synth = this.createSynthForInstrument(track.instrument);
      
      // Create audio effects chain
      const volume = new Tone.Volume(this.volumeToDb(track.volume));
      const panner = new Tone.Panner(track.pan);
      const gain = new Tone.Gain(1);
      
      // Connect the audio chain to master volume
      synth.chain(volume, panner, gain, masterVolume);
      
      /** @type {TrackAudio} */
      const trackAudio = { synth, volume, panner, gain };
      this.#trackAudio.set(track.id, trackAudio);
      
      console.log(`🎵 MidiPlayer: Successfully created audio for track ${track.id}`);
      
      this.dispatchEvent(new CustomEvent('trackAudioCreated', {
        detail: { trackId: track.id, instrument: track.instrument }
      }));
      
    } catch (error) {
      console.error(`🎵 MidiPlayer: Failed to create audio for track ${track.id}:`, error);
    }
  }

  /**
   * Create synthesizer based on instrument type
   * @private
   * @param {string} instrument - Instrument name
   * @returns {Tone.PolySynth} Synthesizer instance
   */
  createSynthForInstrument(instrument) {
    switch (instrument) {
      case 'piano':
        return new Tone.PolySynth(Tone.Synth, {
          oscillator: { type: 'sine' },
          envelope: { attack: 0.02, decay: 0.1, sustain: 0.3, release: 1 }
        });
        
      case 'organ':
        return new Tone.PolySynth(Tone.Synth, {
          oscillator: { type: 'sawtooth' },
          envelope: { attack: 0.02, decay: 0.1, sustain: 0.8, release: 0.5 }
        });
        
      case 'guitar':
        return new Tone.PolySynth(Tone.Synth, {
          oscillator: { type: 'triangle' },
          envelope: { attack: 0.01, decay: 0.2, sustain: 0.2, release: 1.5 }
        });
        
      case 'bass':
        return new Tone.PolySynth(Tone.Synth, {
          oscillator: { type: 'sine' },
          envelope: { attack: 0.01, decay: 0.05, sustain: 0.1, release: 0.8 }
        }).set({ volume: 6 }); // Boost bass volume
        
      case 'strings':
        return new Tone.PolySynth(Tone.Synth, {
          oscillator: { type: 'sawtooth' },
          envelope: { attack: 0.5, decay: 0.1, sustain: 0.8, release: 2 }
        });
        
      case 'brass':
        return new Tone.PolySynth(Tone.Synth, {
          oscillator: { type: 'square' },
          envelope: { attack: 0.1, decay: 0.1, sustain: 0.7, release: 1 }
        });
        
      case 'drums':
        // For drums, we'll use a basic synth but could be expanded to use Tone.DrumSynth
        return new Tone.PolySynth(Tone.NoiseSynth, {
          noise: { type: 'white' },
          envelope: { attack: 0.01, decay: 0.1, sustain: 0.1, release: 0.2 }
        });
        
      case 'synth':
      default:
        return new Tone.PolySynth(Tone.Synth, {
          oscillator: { type: 'sawtooth' },
          envelope: { attack: 0.1, decay: 0.1, sustain: 0.5, release: 1 }
        });
    }
  }

  /**
   * Update track audio settings when track properties change
   * @private
   * @param {import('../stores/tracks.js').Track} track - Updated track
   */
  updateTrackAudioSettings(track) {
    const trackAudio = this.#trackAudio.get(track.id);
    if (!trackAudio) return;
    
    try {
      // Update volume
      trackAudio.volume.volume.value = this.volumeToDb(track.volume);
      
      // Update pan
      trackAudio.panner.pan.value = track.pan;
      
      // Handle mute
      trackAudio.gain.gain.value = track.isMuted ? 0 : 1;
      
      // Handle solo (this would need coordination with other tracks)
      // For now, just ensure this track is audible if it's soloed
      if (track.isSolo) {
        trackAudio.gain.gain.value = track.isMuted ? 0 : 1;
      }
      
    } catch (error) {
      console.error(`Failed to update audio settings for track ${track.id}:`, error);
    }
  }

  /**
   * Remove audio chain for a track
   * @private
   * @param {string} trackId - Track ID to remove
   */
  removeTrackAudio(trackId) {
    const trackAudio = this.#trackAudio.get(trackId);
    if (!trackAudio) return;
    
    try {
      // Stop any playing notes
      trackAudio.synth.releaseAll();
      
      // Dispose of all audio nodes
      trackAudio.synth.dispose();
      trackAudio.volume.dispose();
      trackAudio.panner.dispose();
      trackAudio.gain.dispose();
      
      this.#trackAudio.delete(trackId);
      
      this.dispatchEvent(new CustomEvent('trackAudioRemoved', {
        detail: { trackId }
      }));
      
    } catch (error) {
      console.error(`Failed to remove audio for track ${trackId}:`, error);
    }
  }

  /**
   * Convert linear volume (0-1) to decibel scale
   * @private
   * @param {number} volume - Linear volume (0-1)
   * @returns {number} Volume in decibels
   */
  volumeToDb(volume) {
    if (volume === 0) return -Infinity;
    return 20 * Math.log10(volume);
  }

  /**
   * Start playback for all tracks
   * @param {import('../stores/tracks.js').Track[]} trackList - Tracks to play
   * @returns {boolean} Success status
   */
  startPlayback(trackList) {
    try {
      if (this.#isPlaying) {
        console.warn('Already playing');
        return false;
      }
      
      this.#isPlaying = true;
      this.clearScheduledEvents();
      
      // Schedule events for each track
      for (const track of trackList) {
        if (!track.isMuted && track.midiEvents.length > 0) {
          this.scheduleTrack(track);
        }
      }
      
      this.dispatchEvent(new CustomEvent('playbackStarted'));
      
      return true;
      
    } catch (error) {
      console.error('Failed to start playback:', error);
      this.#isPlaying = false;
      return false;
    }
  }

  /**
   * Schedule a track for playback
   * @private
   * @param {import('../stores/tracks.js').Track} track - Track to schedule
   */
  scheduleTrack(track) {
    const trackAudio = this.#trackAudio.get(track.id);
    if (!trackAudio) {
      console.warn(`No audio found for track ${track.id}`);
      return;
    }
    
    const events = track.midiEvents.map(event => {
      return new Tone.ToneEvent((time) => {
        this.playNoteEvent(track.id, event, time);
      }, event.time);
    });
    
    // Schedule all events
    events.forEach(event => {
      event.start(Tone.Transport.seconds);
    });
    
    this.#scheduledEvents.set(track.id, events);
    
    this.dispatchEvent(new CustomEvent('trackScheduled', {
      detail: { trackId: track.id, eventCount: events.length }
    }));
  }

  /**
   * Play a single MIDI note event
   * @private
   * @param {string} trackId - Track ID
   * @param {import('../stores/tracks.js').MidiEvent} event - MIDI event
   * @param {number} time - Scheduled time
   */
  playNoteEvent(trackId, event, time) {
    const trackAudio = this.#trackAudio.get(trackId);
    if (!trackAudio) return;
    
    try {
      // Convert MIDI note number to frequency
      const frequency = Tone.Frequency(event.note, 'midi');
      
      // Convert velocity to volume (0-127 to 0-1)
      const velocity = event.velocity / 127;
      
      // Trigger note
      trackAudio.synth.triggerAttackRelease(
        frequency, 
        event.duration, 
        time, 
        velocity
      );
      
      // Track active notes for visualization
      this.#activeNotes.add(event.note);
      
      // Schedule note release for visualization
      Tone.Transport.scheduleOnce(() => {
        this.#activeNotes.delete(event.note);
        this.dispatchEvent(new CustomEvent('noteReleased', {
          detail: { trackId, note: event.note }
        }));
      }, time + event.duration);
      
      this.dispatchEvent(new CustomEvent('notePlayed', {
        detail: { 
          trackId, 
          note: event.note, 
          velocity: event.velocity,
          time,
          duration: event.duration 
        }
      }));
      
    } catch (error) {
      console.error(`Failed to play note for track ${trackId}:`, error);
    }
  }

  /**
   * Stop playback and clear scheduled events
   * @returns {boolean} Success status
   */
  stopPlayback() {
    try {
      this.#isPlaying = false;
      this.clearScheduledEvents();
      this.stopAllNotes();
      
      this.dispatchEvent(new CustomEvent('playbackStopped'));
      
      return true;
      
    } catch (error) {
      console.error('Failed to stop playback:', error);
      return false;
    }
  }

  /**
   * Clear all scheduled events
   * @private
   */
  clearScheduledEvents() {
    for (const [trackId, events] of this.#scheduledEvents.entries()) {
      events.forEach(event => {
        event.dispose();
      });
    }
    this.#scheduledEvents.clear();
  }

  /**
   * Stop all currently playing notes
   * @private
   */
  stopAllNotes() {
    for (const trackAudio of this.#trackAudio.values()) {
      trackAudio.synth.releaseAll();
    }
    this.#activeNotes.clear();
  }

  /**
   * Handle solo logic across all tracks
   * @param {import('../stores/tracks.js').Track[]} trackList - All tracks
   */
  handleSoloLogic(trackList) {
    const soloTracks = trackList.filter(t => t.isSolo);
    const hasSoloTracks = soloTracks.length > 0;
    
    for (const track of trackList) {
      const trackAudio = this.#trackAudio.get(track.id);
      if (!trackAudio) continue;
      
      if (hasSoloTracks) {
        // If there are solo tracks, only solo tracks should be audible
        const shouldPlay = track.isSolo && !track.isMuted;
        trackAudio.gain.gain.value = shouldPlay ? 1 : 0;
      } else {
        // No solo tracks, respect mute settings
        trackAudio.gain.gain.value = track.isMuted ? 0 : 1;
      }
    }
  }

  /**
   * Get currently active notes (for visualization)
   * @returns {Set<number>} Set of active MIDI note numbers
   */
  getActiveNotes() {
    return new Set(this.#activeNotes);
  }

  /**
   * Check if playback is active
   * @returns {boolean} Is playing
   */
  isPlaying() {
    return this.#isPlaying;
  }

  /**
   * Get playback status
   * @returns {Object} Playback status
   */
  getStatus() {
    return {
      isPlaying: this.#isPlaying,
      scheduledTracks: this.#scheduledEvents.size,
      activeTracks: this.#trackAudio.size,
      activeNotes: this.#activeNotes.size
    };
  }

  /**
   * Dispose of all player resources
   */
  dispose() {
    this.stopPlayback();
    
    // Remove all track audio
    for (const trackId of this.#trackAudio.keys()) {
      this.removeTrackAudio(trackId);
    }
    
    // Unsubscribe from stores
    if (this.#unsubscribeTracks) {
      this.#unsubscribeTracks();
    }
    
    this.dispatchEvent(new CustomEvent('disposed'));
  }

  /**
   * Initialize all track audio after audio engine is ready
   * Should be called after AudioEngine.initialize() completes
   */
  initializeAllTrackAudio() {
    console.log('🎵 MidiPlayer: Initializing all track audio...');
    
    // Get current tracks from store
    tracks.subscribe(trackList => {
      for (const track of trackList) {
        if (!this.#trackAudio.has(track.id)) {
          this.createTrackAudio(track);
        }
      }
    })(); // Immediately unsubscribe after getting current value
  }
}

// Create and export player factory
let midiPlayerInstance = null;

/**
 * Get the singleton MIDI player instance
 * @param {import('../utils/audioEngine.js').AudioEngine} audioEngine - Audio engine instance
 * @returns {MidiPlayer} MIDI player instance
 */
export function getMidiPlayer(audioEngine) {
  if (!midiPlayerInstance) {
    midiPlayerInstance = new MidiPlayer(audioEngine);
  }
  return midiPlayerInstance;
}

/**
 * Create a new MIDI player instance
 * @param {import('../utils/audioEngine.js').AudioEngine} audioEngine - Audio engine instance
 * @returns {MidiPlayer} New MIDI player instance
 */
export function createMidiPlayer(audioEngine) {
  return new MidiPlayer(audioEngine);
}

// Export the MidiPlayer class
export { MidiPlayer }; 
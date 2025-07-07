import * as Tone from 'tone';
import { tracks } from '../stores/tracks.js';
import { audioState } from '../stores/audio.js';

/**
 * Handles MIDI recording functionality
 * Records MIDI events from virtual keyboard to armed tracks
 */
class MidiRecorder extends EventTarget {
  /**
   * @private
   * @type {string|null}
   */
  #recordingTrack = null;
  
  /**
   * @private
   * @type {import('../stores/tracks.js').MidiEvent[]}
   */
  #recordedEvents = [];
  
  /**
   * @private
   * @type {string}
   */
  #startTime = "0:0:0";
  
  /**
   * @private
   * @type {boolean}
   */
  #isRecording = false;
  
  /**
   * @private
   * @type {boolean}
   */
  #quantizeEnabled = false; // Disable quantization to test timing
  
  /**
   * @private
   * @type {number}
   */
  #quantizeSubdivision = 16; // 16th notes
  
  /**
   * @private
   * @type {Map<number, number>}
   */
  #activeNotes = new Map(); // note -> start time
  
  /**
   * @private
   * @type {import('../utils/audioEngine.js').AudioEngine}
   */
  #audioEngine = null;

  constructor(audioEngine) {
    super();
    this.#audioEngine = audioEngine;
    this.setupEventListeners();
  }

  /**
   * Set up event listeners for audio engine events
   * @private
   */
  setupEventListeners() {
    // Listen for playhead updates to record timing accurately
    this.#audioEngine.addEventListener('playheadUpdate', (event) => {
      if (this.#isRecording) {
        this.#updateRecordingPosition(event.detail.beats);
      }
    });
  }

  /**
   * Start recording for a specific track
   * @param {string} trackId - The track to record to
   * @returns {boolean} Success status
   */
  startRecording(trackId) {
    try {
      if (this.#isRecording) {
        console.warn('Already recording to track:', this.#recordingTrack);
        return false;
      }
      
      this.#recordingTrack = trackId;
      this.#isRecording = true;
      
      // Store the current transport position as start time 
      this.#startTime = Tone.Transport.position;
      
      this.#recordedEvents = [];
      this.#activeNotes.clear();
      
      this.dispatchEvent(new CustomEvent('recordingStarted', {
        detail: { trackId }
      }));
      
      console.log(`Started recording to track: ${trackId}`);
      return true;
      
    } catch (error) {
      console.error('Failed to start recording:', error);
      return false;
    }
  }

  /**
   * Stop recording and save events to track
   * @returns {boolean} Success status
   */
  stopRecording() {
    try {
      if (!this.#isRecording) {
        console.warn('Not currently recording');
        return false;
      }
      
      // Complete any active notes
      this.#completeActiveNotes();
      
      // Save recorded events to track
      if (this.#recordedEvents.length > 0) {
        console.log(`🎵 MidiRecorder: Saving ${this.#recordedEvents.length} events to track ${this.#recordingTrack}:`, this.#recordedEvents);
        tracks.addMidiEvents(this.#recordingTrack, this.#recordedEvents);
        console.log(`🎵 MidiRecorder: Events saved to track ${this.#recordingTrack}`);
      } else {
        console.log(`🎵 MidiRecorder: No events to save for track ${this.#recordingTrack}`);
      }
      
      const trackId = this.#recordingTrack;
      const eventCount = this.#recordedEvents.length;
      
      // Reset recording state
      this.#isRecording = false;
      this.#recordingTrack = null;
      this.#recordedEvents = [];
      this.#activeNotes.clear();
      
      this.dispatchEvent(new CustomEvent('recordingStopped', {
        detail: { trackId, eventCount }
      }));
      
      console.log(`Stopped recording to track: ${trackId}, recorded ${eventCount} events`);
      return true;
      
    } catch (error) {
      console.error('Failed to stop recording:', error);
      return false;
    }
  }

  /**
   * Record a note start event
   * @param {number} note - MIDI note number (0-127)
   * @param {number} velocity - Note velocity (0-127)
   * @returns {boolean} Success status
   */
  recordNoteOn(note, velocity) {
    if (!this.#isRecording || !this.#recordingTrack) {
      return false;
    }
    
    try {
      const currentTime = this.#getCurrentRecordingTime();
      
      // Store active note for duration calculation
      this.#activeNotes.set(note, currentTime);
      
      console.log(`🎵 MidiRecorder: Note ON - note: ${note}, time: ${currentTime.toFixed(3)} beats`);
      
      this.dispatchEvent(new CustomEvent('noteRecorded', {
        detail: { note, velocity, time: currentTime, type: 'noteOn' }
      }));
      
      return true;
      
    } catch (error) {
      console.error('Failed to record note on:', error);
      return false;
    }
  }

  /**
   * Record a note end event
   * @param {number} note - MIDI note number (0-127)
   * @returns {boolean} Success status
   */
  recordNoteOff(note) {
    if (!this.#isRecording || !this.#recordingTrack) {
      return false;
    }
    
    try {
      const currentTime = this.#getCurrentRecordingTime();
      const startTime = this.#activeNotes.get(note);
      
      if (startTime === undefined) {
        console.warn(`Note off without note on for note: ${note}`);
        return false;
      }
      
      // Calculate duration
      const duration = currentTime - startTime;
      
      // Create MIDI event
      const originalTime = startTime;
      const quantizedTime = this.#quantizeEnabled ? this.#quantizeTime(startTime) : startTime;
      
      /** @type {import('../stores/tracks.js').MidiEvent} */
      const midiEvent = {
        time: quantizedTime,
        note,
        velocity: 100, // Default velocity, could be tracked separately
        duration: Math.max(0.1, duration) // Minimum duration
      };
      
      console.log(`🎵 MidiRecorder: Note OFF - note: ${note}, startTime: ${originalTime.toFixed(3)}, endTime: ${currentTime.toFixed(3)}, duration: ${duration.toFixed(3)}, quantized: ${quantizedTime.toFixed(3)}`);
      
      // Add to recorded events
      this.#recordedEvents.push(midiEvent);
      
      // Remove from active notes
      this.#activeNotes.delete(note);
      
      this.dispatchEvent(new CustomEvent('noteRecorded', {
        detail: { 
          note, 
          time: midiEvent.time, 
          duration: midiEvent.duration,
          type: 'noteOff' 
        }
      }));
      
      return true;
      
    } catch (error) {
      console.error('Failed to record note off:', error);
      return false;
    }
  }

  /**
   * Record a complete note event (note on + off)
   * @param {number} note - MIDI note number (0-127)
   * @param {number} velocity - Note velocity (0-127)
   * @param {number} duration - Note duration in beats
   * @returns {boolean} Success status
   */
  recordNote(note, velocity, duration) {
    if (!this.#isRecording || !this.#recordingTrack) {
      return false;
    }
    
    try {
      const currentTime = this.#getCurrentRecordingTime();
      
      /** @type {import('../stores/tracks.js').MidiEvent} */
      const midiEvent = {
        time: this.#quantizeEnabled ? this.#quantizeTime(currentTime) : currentTime,
        note,
        velocity,
        duration: Math.max(0.1, duration)
      };
      
      this.#recordedEvents.push(midiEvent);
      
      this.dispatchEvent(new CustomEvent('noteRecorded', {
        detail: { 
          note, 
          velocity,
          time: midiEvent.time, 
          duration: midiEvent.duration,
          type: 'complete' 
        }
      }));
      
      return true;
      
    } catch (error) {
      console.error('Failed to record note:', error);
      return false;
    }
  }

  /**
   * Get current recording time in beats
   * Simple and reliable timing using Transport position
   * @private
   * @returns {number} Current time in beats
   */
  #getCurrentRecordingTime() {
    // Get current transport position and convert to beats
    const currentTime = Tone.Time(Tone.Transport.position);
    const startTime = Tone.Time(this.#startTime);
    
    // Calculate the difference in beats
    const currentBeats = currentTime.toBarsBeatsSixteenths();
    const startBeats = startTime.toBarsBeatsSixteenths();
    
    // Convert to decimal beats for easier calculation
    const currentDecimalBeats = this.#barsBeatsSixteenthsToDecimalBeats(currentBeats);
    const startDecimalBeats = this.#barsBeatsSixteenthsToDecimalBeats(startBeats);
    
    const recordingTimeInBeats = currentDecimalBeats - startDecimalBeats;
    
    console.log(`🎵 MidiRecorder: getCurrentRecordingTime() - current: ${currentBeats}, start: ${startBeats}, recording: ${recordingTimeInBeats.toFixed(3)} beats`);
    
    return Math.max(0, recordingTimeInBeats);
  }
  
  /**
   * Convert bars:beats:sixteenths to decimal beats
   * @private
   * @param {string} barsBeatsSixteenths - Format like "0:2:1"
   * @returns {number} Decimal beats
   */
  #barsBeatsSixteenthsToDecimalBeats(barsBeatsSixteenths) {
    const parts = barsBeatsSixteenths.split(':');
    const bars = parseInt(parts[0]) || 0;
    const beats = parseInt(parts[1]) || 0;
    const sixteenths = parseInt(parts[2]) || 0;
    
    return (bars * 4) + beats + (sixteenths / 4);
  }

  /**
   * Update recording position (called from playhead updates)
   * @private
   * @param {number} position - Current position in beats
   */
  #updateRecordingPosition(position) {
    // Could be used for visual feedback during recording
    this.dispatchEvent(new CustomEvent('recordingPosition', {
      detail: { position }
    }));
  }

  /**
   * Quantize time to subdivision
   * @private
   * @param {number} time - Time in beats
   * @returns {number} Quantized time
   */
  #quantizeTime(time) {
    const subdivision = 4 / this.#quantizeSubdivision; // 16th note = 0.25 beats
    const quantized = Math.round(time / subdivision) * subdivision;
    console.log(`🎵 MidiRecorder: Quantizing ${time.toFixed(3)} beats to ${quantized.toFixed(3)} beats (subdivision: ${subdivision})`);
    return quantized;
  }

  /**
   * Complete any active notes at current time
   * @private
   */
  #completeActiveNotes() {
    const currentTime = this.#getCurrentRecordingTime();
    
    for (const [note, startTime] of this.#activeNotes.entries()) {
      const duration = Math.max(0.1, currentTime - startTime);
      
      /** @type {import('../stores/tracks.js').MidiEvent} */
      const midiEvent = {
        time: this.#quantizeEnabled ? this.#quantizeTime(startTime) : startTime,
        note,
        velocity: 100,
        duration
      };
      
      this.#recordedEvents.push(midiEvent);
    }
    
    this.#activeNotes.clear();
  }

  /**
   * Enable/disable quantization
   * @param {boolean} enabled - Whether to enable quantization
   */
  setQuantizeEnabled(enabled) {
    this.#quantizeEnabled = enabled;
    
    this.dispatchEvent(new CustomEvent('quantizeChanged', {
      detail: { enabled }
    }));
  }

  /**
   * Set quantization subdivision
   * @param {number} subdivision - Subdivision (4, 8, 16, 32)
   */
  setQuantizeSubdivision(subdivision) {
    const validSubdivisions = [4, 8, 16, 32];
    if (validSubdivisions.includes(subdivision)) {
      this.#quantizeSubdivision = subdivision;
      
      this.dispatchEvent(new CustomEvent('quantizeSubdivisionChanged', {
        detail: { subdivision }
      }));
    }
  }

  /**
   * Get recording status
   * @returns {Object} Recording status
   */
  getStatus() {
    return {
      isRecording: this.#isRecording,
      recordingTrack: this.#recordingTrack,
      recordedEventCount: this.#recordedEvents.length,
      activeNotesCount: this.#activeNotes.size,
      quantizeEnabled: this.#quantizeEnabled,
      quantizeSubdivision: this.#quantizeSubdivision
    };
  }

  /**
   * Clear recorded events (for testing/debugging)
   */
  clearRecordedEvents() {
    this.#recordedEvents = [];
    this.#activeNotes.clear();
    
    this.dispatchEvent(new CustomEvent('eventsCleared'));
  }

  /**
   * Get recorded events (for preview/editing)
   * @returns {import('../stores/tracks.js').MidiEvent[]} Recorded events
   */
  getRecordedEvents() {
    return [...this.#recordedEvents];
  }

  /**
   * Enable overdub mode (add to existing track events)
   * @param {boolean} enabled - Whether to enable overdub
   */
  setOverdubEnabled(enabled) {
    // This would modify how events are saved to tracks
    // For now, just dispatch event
    this.dispatchEvent(new CustomEvent('overdubChanged', {
      detail: { enabled }
    }));
  }

  /**
   * Get current recording time for external use
   * @returns {number} Current recording time in beats
   */
  getCurrentRecordingTime() {
    return this.#isRecording ? this.#getCurrentRecordingTime() : 0;
  }

  /**
   * Dispose of recorder resources
   */
  dispose() {
    this.stopRecording();
    this.#activeNotes.clear();
    this.#recordedEvents = [];
    
    this.dispatchEvent(new CustomEvent('disposed'));
  }
}

// Create and export recorder factory
let midiRecorderInstance = null;

/**
 * Get the singleton MIDI recorder instance
 * @param {import('../utils/audioEngine.js').AudioEngine} audioEngine - Audio engine instance
 * @returns {MidiRecorder} MIDI recorder instance
 */
export function getMidiRecorder(audioEngine) {
  if (!midiRecorderInstance) {
    midiRecorderInstance = new MidiRecorder(audioEngine);
  }
  return midiRecorderInstance;
}

/**
 * Create a new MIDI recorder instance
 * @param {import('../utils/audioEngine.js').AudioEngine} audioEngine - Audio engine instance
 * @returns {MidiRecorder} New MIDI recorder instance
 */
export function createMidiRecorder(audioEngine) {
  return new MidiRecorder(audioEngine);
}

// Export the MidiRecorder class
export { MidiRecorder }; 
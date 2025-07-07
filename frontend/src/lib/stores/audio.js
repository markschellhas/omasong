import { writable } from 'svelte/store';

/**
 * @typedef {Object} AudioState
 * @property {boolean} isPlaying - Whether audio is playing
 * @property {boolean} isRecording - Whether recording is active
 * @property {boolean} isCountingIn - Whether count-in is active
 * @property {number} tempo - Current tempo (BPM)
 * @property {boolean} metronomeEnabled - Whether metronome is enabled
 * @property {number} metronomeVolume - Metronome volume (0-1)
 * @property {number} currentPosition - Current playback position
 * @property {number} playheadPosition - Current playhead position in beats
 * @property {number} countInBeatsRemaining - Beats remaining in count-in (0-4)
 * @property {number} currentBeat - Current beat number
 * @property {number} currentBar - Current bar number
 */

/**
 * Initial audio state
 * @type {AudioState}
 */
const initialAudioState = {
  isPlaying: false,
  isRecording: false,
  isCountingIn: false,
  tempo: 120,
  metronomeEnabled: false,
  metronomeVolume: 0.7,
  currentPosition: 0,
  playheadPosition: 0,
  countInBeatsRemaining: 0,
  currentBeat: 0,
  currentBar: 0
};

/**
 * Create audio store with additional methods
 */
function createAudioStore() {
  const { subscribe, set, update } = writable(initialAudioState);

  return {
    subscribe,
    
    /**
     * Start playback
     */
    play: () => update(state => ({ ...state, isPlaying: true })),
    
    /**
     * Pause playback
     */
    pause: () => update(state => ({ ...state, isPlaying: false })),
    
    /**
     * Stop playback and reset position
     */
    stop: () => update(state => ({ 
      ...state, 
      isPlaying: false, 
      playheadPosition: 0,
      currentPosition: 0 
    })),
    
    /**
     * Start recording
     */
    startRecording: () => update(state => ({ ...state, isRecording: true })),
    
    /**
     * Stop recording
     */
    stopRecording: () => update(state => ({ ...state, isRecording: false })),
    
    /**
     * Start count-in sequence
     * @param {number} beats - Number of beats to count in
     */
    startCountIn: (beats = 4) => update(state => ({ 
      ...state, 
      isCountingIn: true, 
      countInBeatsRemaining: beats 
    })),
    
    /**
     * Update count-in progress
     * @param {number} beatsRemaining - Beats remaining in count-in
     */
    updateCountIn: (beatsRemaining) => update(state => ({ 
      ...state, 
      countInBeatsRemaining: beatsRemaining 
    })),
    
    /**
     * Stop count-in
     */
    stopCountIn: () => update(state => ({ 
      ...state, 
      isCountingIn: false, 
      countInBeatsRemaining: 0 
    })),
    
    /**
     * Set tempo
     * @param {number} tempo - New tempo in BPM (60-200)
     */
    setTempo: (tempo) => {
      const clampedTempo = Math.max(60, Math.min(200, tempo));
      update(state => ({ ...state, tempo: clampedTempo }));
    },
    
    /**
     * Toggle metronome
     */
    toggleMetronome: () => update(state => ({ 
      ...state, 
      metronomeEnabled: !state.metronomeEnabled 
    })),
    
    /**
     * Set metronome volume
     * @param {number} volume - Volume level (0-1)
     */
    setMetronomeVolume: (volume) => {
      const clampedVolume = Math.max(0, Math.min(1, volume));
      update(state => ({ ...state, metronomeVolume: clampedVolume }));
    },
    
    /**
     * Update playhead position
     * @param {number} position - New position in beats
     */
    updatePlayhead: (position) => update(state => {
      const currentBeat = Math.floor(position % 4) + 1;
      const currentBar = Math.floor(position / 4) + 1;
      return { 
        ...state, 
        playheadPosition: position,
        currentPosition: position,
        currentBeat,
        currentBar
      };
    }),
    
    /**
     * Seek to position
     * @param {number} position - Position to seek to in beats
     */
    seek: (position) => update(state => {
      const currentBeat = Math.floor(position % 4) + 1;
      const currentBar = Math.floor(position / 4) + 1;
      return { 
        ...state, 
        playheadPosition: position,
        currentPosition: position,
        currentBeat,
        currentBar
      };
    }),
    
    /**
     * Reset to initial state
     */
    reset: () => set(initialAudioState),
    
    /**
     * Update multiple properties at once
     * @param {Partial<AudioState>} updates - Properties to update
     */
    updateState: (updates) => update(state => ({ ...state, ...updates }))
  };
}

/** @type {import('svelte/store').Writable<AudioState>} */
export const audioState = createAudioStore();

/**
 * Save audio state to localStorage
 * @param {AudioState} state - Current audio state
 */
export function saveAudioState(state) {
  try {
    const persistentState = {
      tempo: state.tempo,
      metronomeEnabled: state.metronomeEnabled,
      metronomeVolume: state.metronomeVolume
    };
    localStorage.setItem('midi-studio-audio', JSON.stringify(persistentState));
  } catch (error) {
    console.warn('Failed to save audio state:', error);
  }
}

/**
 * Load audio state from localStorage
 * @returns {Partial<AudioState>} Saved audio state
 */
export function loadAudioState() {
  try {
    const saved = localStorage.getItem('midi-studio-audio');
    return saved ? JSON.parse(saved) : {};
  } catch (error) {
    console.warn('Failed to load audio state:', error);
    return {};
  }
} 
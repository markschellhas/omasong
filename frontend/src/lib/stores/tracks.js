import { writable } from 'svelte/store';

/**
 * @typedef {Object} MidiEvent
 * @property {number} time - Event time in beats
 * @property {number} note - MIDI note number (0-127)
 * @property {number} velocity - Note velocity (0-127)
 * @property {number} duration - Note duration in beats
 */

/**
 * @typedef {Object} Track
 * @property {string} id - Unique identifier for the track
 * @property {string} name - Display name for the track
 * @property {string} color - Color theme for the track
 * @property {boolean} isArmed - Whether track is armed for recording
 * @property {boolean} isSolo - Whether track is soloed
 * @property {boolean} isMuted - Whether track is muted
 * @property {number} volume - Track volume (0-1)
 * @property {number} pan - Track pan (-1 to 1)
 * @property {MidiEvent[]} midiEvents - Array of MIDI events
 * @property {string} instrument - Instrument/sound for the track
 */

/**
 * Available track colors
 */
const TRACK_COLORS = [
  '#ef4444', // red
  '#f97316', // orange  
  '#eab308', // yellow
  '#22c55e', // green
  '#06b6d4', // cyan
  '#3b82f6', // blue
  '#8b5cf6', // violet
  '#ec4899', // pink
];

/**
 * Available instruments
 */
const INSTRUMENTS = [
  'synth',
  'piano',
  'organ',
  'guitar',
  'bass',
  'strings',
  'brass',
  'drums'
];

/**
 * Generate unique ID
 * @returns {string} Unique identifier
 */
function generateId() {
  return 'track_' + Math.random().toString(36).substr(2, 9);
}

/**
 * Create a new track
 * @param {string} name - Track name
 * @param {number} index - Track index for color selection
 * @returns {Track} New track object
 */
function createTrack(name, index = 0) {
  return {
    id: generateId(),
    name: name || `Track ${index + 1}`,
    color: TRACK_COLORS[index % TRACK_COLORS.length],
    isArmed: false,
    isSolo: false,
    isMuted: false,
    volume: 0.8,
    pan: 0,
    midiEvents: [],
    instrument: INSTRUMENTS[0] // default to synth
  };
}

/**
 * Create tracks store with additional methods
 */
function createTracksStore() {
  const { subscribe, set, update } = writable([]);

  return {
    subscribe,
    
    /**
     * Add a new track
     * @param {string} [name] - Optional track name
     */
    add: (name) => update(tracks => {
      const newTrack = createTrack(name, tracks.length);
      return [...tracks, newTrack];
    }),
    
    /**
     * Remove a track by ID
     * @param {string} id - Track ID to remove
     */
    remove: (id) => update(tracks => tracks.filter(t => t.id !== id)),
    
    /**
     * Update a track property
     * @param {string} id - Track ID
     * @param {string} property - Property name
     * @param {any} value - New value
     */
    updateTrackProperty: (id, property, value) => update(tracks =>
      tracks.map(track => 
        track.id === id 
          ? { ...track, [property]: value }
          : track
      )
    ),
    
    /**
     * Update entire track
     * @param {string} id - Track ID
     * @param {Partial<Track>} changes - Changes to apply
     */
    updateTrack: (id, changes) => update(tracks => 
      tracks.map(t => t.id === id ? { ...t, ...changes } : t)
    ),
    
    /**
     * Arm track for recording (disarms others)
     * @param {string} id - Track ID to arm
     */
    armForRecording: (id) => update(tracks =>
      tracks.map(t => ({ ...t, isArmed: t.id === id }))
    ),
    
    /**
     * Toggle track mute
     * @param {string} id - Track ID
     */
    toggleMute: (id) => update(tracks =>
      tracks.map(t => 
        t.id === id ? { ...t, isMuted: !t.isMuted } : t
      )
    ),
    
    /**
     * Toggle track solo (unsolo others if soloing)
     * @param {string} id - Track ID
     */
    toggleSolo: (id) => update(tracks => {
      const track = tracks.find(t => t.id === id);
      if (!track) return tracks;
      
      const newSoloState = !track.isSolo;
      
      return tracks.map(t => ({
        ...t,
        isSolo: t.id === id ? newSoloState : (newSoloState ? false : t.isSolo)
      }));
    }),
    
    /**
     * Set track volume
     * @param {string} id - Track ID
     * @param {number} volume - Volume level (0-1)
     */
    setVolume: (id, volume) => {
      const clampedVolume = Math.max(0, Math.min(1, volume));
      update(tracks =>
        tracks.map(t => 
          t.id === id ? { ...t, volume: clampedVolume } : t
        )
      );
    },
    
    /**
     * Set track pan
     * @param {string} id - Track ID
     * @param {number} pan - Pan position (-1 to 1)
     */
    setPan: (id, pan) => {
      const clampedPan = Math.max(-1, Math.min(1, pan));
      update(tracks =>
        tracks.map(t => 
          t.id === id ? { ...t, pan: clampedPan } : t
        )
      );
    },
    
    /**
     * Set track instrument
     * @param {string} id - Track ID
     * @param {string} instrument - Instrument name
     */
    setInstrument: (id, instrument) => update(tracks =>
      tracks.map(t => 
        t.id === id ? { ...t, instrument } : t
      )
    ),
    
    /**
     * Add MIDI event to track
     * @param {string} trackId - Track ID
     * @param {MidiEvent} event - MIDI event to add
     */
    addMidiEvent: (trackId, event) => update(tracks =>
      tracks.map(t => 
        t.id === trackId 
          ? { ...t, midiEvents: [...t.midiEvents, event] }
          : t
      )
    ),
    
    /**
     * Add multiple MIDI events to track
     * @param {string} trackId - Track ID
     * @param {MidiEvent[]} events - MIDI events to add
     */
    addMidiEvents: (trackId, events) => update(tracks =>
      tracks.map(t => 
        t.id === trackId 
          ? { ...t, midiEvents: [...t.midiEvents, ...events] }
          : t
      )
    ),
    
    /**
     * Clear all MIDI events from track
     * @param {string} trackId - Track ID
     */
    clearMidiEvents: (trackId) => update(tracks =>
      tracks.map(t => 
        t.id === trackId 
          ? { ...t, midiEvents: [] }
          : t
      )
    ),
    
    /**
     * Duplicate a track
     * @param {string} id - Track ID to duplicate
     */
    duplicate: (id) => update(tracks => {
      const track = tracks.find(t => t.id === id);
      if (!track) return tracks;
      
      const duplicatedTrack = {
        ...track,
        id: generateId(),
        name: `${track.name} Copy`,
        isArmed: false,
        isSolo: false
      };
      
      return [...tracks, duplicatedTrack];
    }),
    
    /**
     * Reorder tracks
     * @param {number} fromIndex - Source index
     * @param {number} toIndex - Target index
     */
    reorder: (fromIndex, toIndex) => update(tracks => {
      const result = [...tracks];
      const [removed] = result.splice(fromIndex, 1);
      result.splice(toIndex, 0, removed);
      return result;
    }),
    
    /**
     * Get armed track
     * @param {Track[]} tracks - Current tracks
     * @returns {Track|null} Armed track or null
     */
    getArmedTrack: (tracks) => tracks.find(t => t.isArmed) || null,
    
    /**
     * Get solo tracks
     * @param {Track[]} tracks - Current tracks
     * @returns {Track[]} Solo tracks
     */
    getSoloTracks: (tracks) => tracks.filter(t => t.isSolo),
    
    /**
     * Reset all tracks
     */
    reset: () => set([]),
    
    /**
     * Initialize with default tracks
     */
    initializeDefault: () => set([
      createTrack('Piano', 0),
      createTrack('Bass', 1),
      createTrack('Drums', 2)
    ])
  };
}

/** @type {import('svelte/store').Writable<Track[]>} */
export const tracks = createTracksStore();

/**
 * Export track colors and instruments for use in components
 */
export { TRACK_COLORS, INSTRUMENTS };

/**
 * Save tracks to localStorage
 * @param {Track[]} trackList - Current tracks
 */
export function saveTracks(trackList) {
  try {
    localStorage.setItem('midi-studio-tracks', JSON.stringify(trackList));
  } catch (error) {
    console.warn('Failed to save tracks:', error);
  }
}

/**
 * Load tracks from localStorage
 * @returns {Track[]} Saved tracks
 */
export function loadTracks() {
  try {
    const saved = localStorage.getItem('midi-studio-tracks');
    return saved ? JSON.parse(saved) : [];
  } catch (error) {
    console.warn('Failed to load tracks:', error);
    return [];
  }
} 
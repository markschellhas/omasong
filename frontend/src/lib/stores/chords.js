import { writable } from 'svelte/store';

/**
 * @typedef {Object} Chord
 * @property {string} symbol - Chord symbol (e.g., "Cmaj", "Dm7")
 * @property {number} measure - Measure number (0-based index)
 * @property {number} beat - Beat position within measure
 * @property {number} duration - Duration in beats
 * @property {number[]} notes - MIDI note numbers
 * @property {string[]} noteNames - MIDI note names
 */

/**
 * @typedef {Chord[]} ChordProgression
 */

/**
 * Create empty progression with specified number of measures
 * @param {number} measures - Number of measures to create
 * @returns {ChordProgression} Empty progression
 */
function createEmptyProgression(measures = 16) {
  return [];
}

/**
 * Create chords store with additional methods
 */
function createChordsStore() {
  const { subscribe, set, update } = writable(createEmptyProgression());

  return {
    subscribe,
    
    /**
     * Set chord for a specific measure
     * @param {number} measure - Measure index (0-based)
     * @param {Chord|null} chord - Chord data or null to clear
     */
    setChord: (measure, chord) => update(chords => {
      console.log('🎵 ChordsStore: setChord called', { measure, chord, existingChords: chords.length });
      
      // Remove existing chord at this measure
      const filtered = chords.filter(c => c.measure !== measure);
      console.log('🎵 ChordsStore: After filtering', { filtered: filtered.length });
      
      // Add new chord if provided
      if (chord) {
        const newChord = {
          ...chord,
          measure // Ensure measure is set correctly
        };
        filtered.push(newChord);
        console.log('🎵 ChordsStore: Added new chord', newChord);
      }
      
      // Sort by measure
      const result = filtered.sort((a, b) => a.measure - b.measure);
      console.log('🎵 ChordsStore: Final result', result);
      return result;
    }),
    
    /**
     * Get chord for specific measure
     * @param {number} measure - Measure index (0-based)
     * @returns {Chord|null} Chord or null
     */
    getChordAtMeasure: (measure) => {
      let currentChords = [];
      const unsubscribe = subscribe(chords => {
        currentChords = chords;
      });
      unsubscribe();
      
      return currentChords.find(c => c.measure === measure) || null;
    },
    
    /**
     * Clear all chords
     */
    clear: () => set([]),
    
    /**
     * Initialize default empty progression
     */
    initializeDefault: () => set(createEmptyProgression()),
    
    /**
     * Load progression from data
     * @param {ChordProgression} progression - Progression to load
     */
    loadProgression: (progression) => set(progression || []),
    
    /**
     * Copy chord from one measure to another
     * @param {number} fromMeasure - Source measure (0-based)
     * @param {number} toMeasure - Target measure (0-based)
     */
    copyChord: (fromMeasure, toMeasure) => update(chords => {
      const sourceChord = chords.find(c => c.measure === fromMeasure);
      if (!sourceChord) return chords;
      
      // Remove existing chord at target measure
      const filtered = chords.filter(c => c.measure !== toMeasure);
      
      // Add copied chord
      filtered.push({
        ...sourceChord,
        measure: toMeasure
      });
      
      return filtered.sort((a, b) => a.measure - b.measure);
    }),
    
    /**
     * Get non-empty chords
     * @returns {ChordProgression} Non-empty chords
     */
    getNonEmptyChords: () => {
      let currentChords = [];
      const unsubscribe = subscribe(chords => {
        currentChords = chords;
      });
      unsubscribe();
      
      return currentChords.filter(c => c.symbol && c.symbol.trim());
    },
    
    /**
     * Get chord progression as text
     * @returns {string} Chord progression as string
     */
    getProgressionText: () => {
      let currentChords = [];
      const unsubscribe = subscribe(chords => {
        currentChords = chords;
      });
      unsubscribe();
      
      return currentChords
        .filter(c => c.symbol && c.symbol.trim())
        .sort((a, b) => a.measure - b.measure)
        .map(c => `${c.measure + 1}: ${c.symbol}`)
        .join(' | ');
    },
    
    /**
     * Load progression from text
     * @param {string} progressionText - Space or comma separated chord symbols
     */
    loadFromText: (progressionText) => {
      const chordSymbols = progressionText
        .split(/[,\s|]+/)
        .map(s => s.trim())
        .filter(s => s.length > 0);
      
      const newChords = chordSymbols.map((symbol, index) => ({
        symbol,
        measure: index,
        beat: 0,
        duration: 4,
        notes: [],
        noteNames: []
      }));
      
      set(newChords);
    },
    
    /**
     * Transpose all chords
     * @param {number} semitones - Number of semitones to transpose
     */
    transpose: (semitones) => update(chords => {
      // This would require chord parsing implementation
      // For now, just return chords unchanged
      console.log(`Transpose by ${semitones} semitones - not yet implemented`);
      return chords;
    }),
    
    /**
     * Reset to empty progression
     * @param {number} measures - Number of empty measures
     */
    reset: (measures = 16) => set(createEmptyProgression(measures)),
    

  };
}

/** @type {import('svelte/store').Writable<ChordProgression>} */
export const chords = createChordsStore();



/**
 * Save chords to localStorage
 * @param {ChordProgression} chordList - Current chords
 */
export function saveChords(chordList) {
  try {
    localStorage.setItem('midi-studio-chords', JSON.stringify(chordList));
  } catch (error) {
    console.warn('Failed to save chords:', error);
  }
}

/**
 * Load chords from localStorage
 * @returns {ChordProgression} Saved chords
 */
export function loadChords() {
  try {
    const saved = localStorage.getItem('midi-studio-chords');
    return saved ? JSON.parse(saved) : createEmptyProgression();
  } catch (error) {
    console.warn('Failed to load chords:', error);
    return createEmptyProgression();
  }
} 
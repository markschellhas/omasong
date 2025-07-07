/**
 * @fileoverview Chord Symbol Parser and Note Generator
 * Parses chord symbols and generates corresponding MIDI note arrays
 * Supports major, minor, diminished, augmented, seventh chords, and extensions
 */

/**
 * @typedef {Object} ChordInfo
 * @property {string} symbol - Original chord symbol
 * @property {string} root - Root note (C, D, E, F, G, A, B)
 * @property {string} [accidental] - Accidental (♯, ♭, #, b)
 * @property {string} quality - Chord quality (major, minor, diminished, augmented)
 * @property {string[]} extensions - Array of extensions (7, 9, 11, 13, sus2, sus4, add9, etc.)
 * @property {string} [bass] - Bass note if slash chord
 * @property {number[]} notes - Array of MIDI note numbers
 * @property {string[]} noteNames - Array of note names
 */

/**
 * @typedef {Object} ParsedChord
 * @property {boolean} isValid - Whether the chord was successfully parsed
 * @property {ChordInfo|null} chord - Parsed chord information
 * @property {string} [error] - Error message if parsing failed
 */

// Note name to MIDI number mapping (octave 4)
const NOTE_NUMBERS = {
  'C': 60, 'C#': 61, 'Db': 61, 'D': 62, 'D#': 63, 'Eb': 63,
  'E': 64, 'F': 65, 'F#': 66, 'Gb': 66, 'G': 67, 'G#': 68,
  'Ab': 68, 'A': 69, 'A#': 70, 'Bb': 70, 'B': 71
};

// MIDI number to note name mapping
const MIDI_TO_NOTE = {
  60: 'C', 61: 'C#', 62: 'D', 63: 'D#', 64: 'E', 65: 'F',
  66: 'F#', 67: 'G', 68: 'G#', 69: 'A', 70: 'A#', 71: 'B'
};

// Interval definitions (semitones from root)
const INTERVALS = {
  // Basic triads
  major: [0, 4, 7],
  minor: [0, 3, 7],
  diminished: [0, 3, 6],
  augmented: [0, 4, 8],
  
  // Suspended chords
  sus2: [0, 2, 7],
  sus4: [0, 5, 7],
  
  // Seventh chords
  major7: [0, 4, 7, 11],
  minor7: [0, 3, 7, 10],
  dominant7: [0, 4, 7, 10],
  diminished7: [0, 3, 6, 9],
  halfDiminished7: [0, 3, 6, 10],
  augmented7: [0, 4, 8, 10],
  
  // Extended chords
  major9: [0, 4, 7, 11, 14],
  minor9: [0, 3, 7, 10, 14],
  dominant9: [0, 4, 7, 10, 14],
  major11: [0, 4, 7, 11, 14, 17],
  minor11: [0, 3, 7, 10, 14, 17],
  dominant11: [0, 4, 7, 10, 14, 17],
  major13: [0, 4, 7, 11, 14, 17, 21],
  minor13: [0, 3, 7, 10, 14, 17, 21],
  dominant13: [0, 4, 7, 10, 14, 17, 21]
};

// Chord symbol regex patterns
const CHORD_PATTERNS = {
  // Root note (required)
  root: '([A-G])',
  
  // Accidentals (optional)
  accidental: '([#♯b♭]?)',
  
  // Quality indicators
  minor: '(m|min|minor|-)',
  diminished: '(dim|°|o)',
  augmented: '(aug|\\+)',
  
  // Extensions and modifications
  seventh: '(7|maj7|M7|Δ7)',
  ninth: '(9|add9|maj9|M9|Δ9)',
  eleventh: '(11|add11)',
  thirteenth: '(13|add13)',
  suspended: '(sus2|sus4)',
  
  // Slash chord (bass note)
  slash: '(?:/([A-G][#♯b♭]?))?'
};

// Complete chord regex
const CHORD_REGEX = new RegExp(
  `^${CHORD_PATTERNS.root}${CHORD_PATTERNS.accidental}` +
  `(${CHORD_PATTERNS.minor}|${CHORD_PATTERNS.diminished}|${CHORD_PATTERNS.augmented})?` +
  `(${CHORD_PATTERNS.seventh}|${CHORD_PATTERNS.ninth}|${CHORD_PATTERNS.eleventh}|${CHORD_PATTERNS.thirteenth}|${CHORD_PATTERNS.suspended})*` +
  `${CHORD_PATTERNS.slash}$`,
  'i'
);

/**
 * Chord Parser class for parsing chord symbols and generating notes
 */
export class ChordParser {
  /**
   * Parse a chord symbol into chord information and notes
   * @param {string} symbol - Chord symbol to parse (e.g., "Cmaj7", "Am", "F#dim")
   * @param {number} [octave=4] - Octave for the root note
   * @param {string} [voicing='root'] - Voicing type ('root', 'inversion1', 'inversion2', 'spread')
   * @returns {ParsedChord} Parsed chord information
   */
  static parseChord(symbol, octave = 4, voicing = 'root') {
    try {
      if (!symbol || typeof symbol !== 'string') {
        return {
          isValid: false,
          chord: null,
          error: 'Invalid chord symbol'
        };
      }
      
      // Clean up the symbol
      const cleanSymbol = symbol.trim().replace(/\s+/g, '');
      
      // Handle special cases
      if (cleanSymbol.toLowerCase() === 'n.c.' || cleanSymbol === '-') {
        return {
          isValid: true,
          chord: {
            symbol: cleanSymbol,
            root: '',
            quality: 'silent',
            extensions: [],
            notes: [],
            noteNames: []
          }
        };
      }
      
      // Parse the chord components
      const components = this.parseChordComponents(cleanSymbol);
      if (!components.isValid) {
        return {
          isValid: false,
          chord: null,
          error: components.error
        };
      }
      
      // Generate notes based on chord type
      const notes = this.generateChordNotes(components, octave, voicing);
      
      /** @type {ChordInfo} */
      const chord = {
        symbol: cleanSymbol,
        root: components.root,
        accidental: components.accidental,
        quality: components.quality,
        extensions: components.extensions,
        bass: components.bass,
        notes: notes,
        noteNames: notes.map(note => this.midiToNoteName(note))
      };
      
      return {
        isValid: true,
        chord
      };
      
    } catch (error) {
      return {
        isValid: false,
        chord: null,
        error: error.message
      };
    }
  }
  
  /**
   * Parse chord symbol into components
   * @private
   * @param {string} symbol - Chord symbol
   * @returns {Object} Parsed components
   */
  static parseChordComponents(symbol) {
    // Simple parsing for common chord types
    const root = symbol.charAt(0).toUpperCase();
    if (!'ABCDEFG'.includes(root)) {
      return {
        isValid: false,
        error: 'Invalid root note'
      };
    }
    
    let remaining = symbol.slice(1);
    let accidental = '';
    let quality = 'major';
    let extensions = [];
    let bass = null;
    
    // Parse accidental
    if (remaining.length > 0 && '#♯b♭'.includes(remaining.charAt(0))) {
      accidental = remaining.charAt(0);
      remaining = remaining.slice(1);
    }
    
    // Parse slash chord
    const slashIndex = remaining.indexOf('/');
    if (slashIndex !== -1) {
      const bassNote = remaining.slice(slashIndex + 1);
      bass = bassNote;
      remaining = remaining.slice(0, slashIndex);
    }
    
    // Parse quality and extensions
    remaining = remaining.toLowerCase();
    
    // Check for specific patterns
    if (remaining.includes('dim') || remaining.includes('°') || remaining.includes('o')) {
      quality = 'diminished';
      if (remaining.includes('7')) {
        extensions.push('7');
      }
    } else if (remaining.includes('aug') || remaining.includes('+')) {
      quality = 'augmented';
      if (remaining.includes('7')) {
        extensions.push('7');
      }
    } else if (remaining.includes('m') || remaining.includes('min') || remaining.includes('-')) {
      quality = 'minor';
      if (remaining.includes('7')) {
        extensions.push('7');
      }
      if (remaining.includes('9')) {
        extensions.push('9');
      }
    } else {
      // Major chord
      if (remaining.includes('maj7') || remaining.includes('m7') || remaining.includes('δ7')) {
        extensions.push('maj7');
      } else if (remaining.includes('7')) {
        extensions.push('7');
      }
      
      if (remaining.includes('9')) {
        extensions.push('9');
      }
      if (remaining.includes('11')) {
        extensions.push('11');
      }
      if (remaining.includes('13')) {
        extensions.push('13');
      }
    }
    
    // Parse suspended chords
    if (remaining.includes('sus4')) {
      quality = 'sus4';
    } else if (remaining.includes('sus2')) {
      quality = 'sus2';
    }
    
    return {
      isValid: true,
      root,
      accidental,
      quality,
      extensions,
      bass
    };
  }
  
  /**
   * Generate MIDI notes for a chord
   * @private
   * @param {Object} components - Parsed chord components
   * @param {number} octave - Root octave
   * @param {string} voicing - Voicing type
   * @returns {number[]} Array of MIDI note numbers
   */
  static generateChordNotes(components, octave, voicing) {
    // Get root note MIDI number
    const rootNote = components.root + (components.accidental || '');
    const rootMidi = NOTE_NUMBERS[rootNote] + (octave - 4) * 12;
    
    // Get intervals based on chord quality and extensions
    let intervals = this.getChordIntervals(components.quality, components.extensions);
    
    // Generate notes
    let notes = intervals.map(interval => rootMidi + interval);
    
    // Handle slash chord (bass note)
    if (components.bass) {
      const bassNote = components.bass;
      const bassMidi = NOTE_NUMBERS[bassNote] + (octave - 4) * 12;
      
      // Add bass note in lower octave if it's not already in the chord
      const bassInChord = notes.some(note => (note % 12) === (bassMidi % 12));
      if (!bassInChord) {
        notes.unshift(bassMidi - 12); // Add bass note one octave below
      } else {
        // Move existing bass note to bottom
        notes = notes.filter(note => (note % 12) !== (bassMidi % 12));
        notes.unshift(bassMidi - 12);
      }
    }
    
    // Apply voicing
    notes = this.applyVoicing(notes, voicing);
    
    // Sort notes and remove duplicates
    notes = [...new Set(notes)].sort((a, b) => a - b);
    
    return notes;
  }
  
  /**
   * Get intervals for a chord quality and extensions
   * @private
   * @param {string} quality - Chord quality
   * @param {string[]} extensions - Extensions array
   * @returns {number[]} Interval array
   */
  static getChordIntervals(quality, extensions) {
    let intervals = [];
    
    // Base triad
    switch (quality) {
      case 'minor':
        intervals = [...INTERVALS.minor];
        break;
      case 'diminished':
        intervals = [...INTERVALS.diminished];
        break;
      case 'augmented':
        intervals = [...INTERVALS.augmented];
        break;
      case 'sus2':
        intervals = [...INTERVALS.sus2];
        break;
      case 'sus4':
        intervals = [...INTERVALS.sus4];
        break;
      case 'major':
      default:
        intervals = [...INTERVALS.major];
        break;
    }
    
    // Add extensions
    for (const extension of extensions) {
      switch (extension) {
        case '7':
          if (quality === 'minor' || quality === 'diminished') {
            intervals.push(10); // Minor 7th
          } else {
            intervals.push(10); // Dominant 7th
          }
          break;
        case 'maj7':
          intervals.push(11); // Major 7th
          break;
        case '9':
          intervals.push(14); // 9th
          if (!intervals.includes(10) && !intervals.includes(11)) {
            intervals.push(10); // Add 7th if not present
          }
          break;
        case '11':
          intervals.push(17); // 11th
          if (!intervals.includes(10) && !intervals.includes(11)) {
            intervals.push(10); // Add 7th if not present
          }
          if (!intervals.includes(14)) {
            intervals.push(14); // Add 9th if not present
          }
          break;
        case '13':
          intervals.push(21); // 13th
          if (!intervals.includes(10) && !intervals.includes(11)) {
            intervals.push(10); // Add 7th if not present
          }
          if (!intervals.includes(14)) {
            intervals.push(14); // Add 9th if not present
          }
          if (!intervals.includes(17)) {
            intervals.push(17); // Add 11th if not present
          }
          break;
      }
    }
    
    return intervals;
  }
  
  /**
   * Apply voicing to chord notes
   * @private
   * @param {number[]} notes - Array of MIDI notes
   * @param {string} voicing - Voicing type
   * @returns {number[]} Voiced notes
   */
  static applyVoicing(notes, voicing) {
    switch (voicing) {
      case 'inversion1':
        // First inversion - move root up an octave
        if (notes.length > 1) {
          const root = notes.shift();
          notes.push(root + 12);
        }
        break;
        
      case 'inversion2':
        // Second inversion - move root and third up an octave
        if (notes.length > 2) {
          const root = notes.shift();
          const third = notes.shift();
          notes.push(root + 12);
          notes.push(third + 12);
        }
        break;
        
      case 'spread':
        // Spread voicing - spread notes across octaves
        return notes.map((note, index) => note + Math.floor(index / 3) * 12);
        
      case 'root':
      default:
        // Root position - no change
        break;
    }
    
    return notes;
  }
  
  /**
   * Convert MIDI note number to note name
   * @private
   * @param {number} midiNote - MIDI note number
   * @returns {string} Note name with octave
   */
  static midiToNoteName(midiNote) {
    const noteNumber = midiNote % 12;
    const octave = Math.floor(midiNote / 12) - 1;
    const noteName = MIDI_TO_NOTE[noteNumber + 60] || 'C';
    return `${noteName}${octave}`;
  }
  
  /**
   * Get all supported chord qualities
   * @returns {string[]} Array of chord qualities
   */
  static getSupportedQualities() {
    return [
      'major', 'minor', 'diminished', 'augmented',
      'sus2', 'sus4', 'major7', 'minor7', 'dominant7',
      'diminished7', 'halfDiminished7', 'augmented7'
    ];
  }
  
  /**
   * Get all supported extensions
   * @returns {string[]} Array of extensions
   */
  static getSupportedExtensions() {
    return ['7', 'maj7', '9', '11', '13', 'sus2', 'sus4', 'add9'];
  }
  
  /**
   * Validate a chord symbol
   * @param {string} symbol - Chord symbol to validate
   * @returns {boolean} Is valid
   */
  static isValidChord(symbol) {
    const result = this.parseChord(symbol);
    return result.isValid;
  }
  
  /**
   * Get chord suggestions based on partial input
   * @param {string} partial - Partial chord symbol
   * @returns {string[]} Array of suggested chord symbols
   */
  static getChordSuggestions(partial) {
    const suggestions = [];
    const partialUpper = partial.toUpperCase();
    
    // Common chord progressions and variations
    const commonChords = [
      'C', 'Cm', 'C7', 'Cmaj7', 'Dm', 'Dm7', 'Em', 'Em7',
      'F', 'Fmaj7', 'G', 'G7', 'Am', 'Am7', 'Bdim', 'B7',
      'D', 'D7', 'E', 'E7', 'A', 'A7', 'F#m', 'F#m7',
      'Bm', 'Bm7', 'C#dim', 'C#7', 'F#', 'F#7', 'B', 'Bmaj7'
    ];
    
    for (const chord of commonChords) {
      if (chord.startsWith(partialUpper)) {
        suggestions.push(chord);
      }
    }
    
    return suggestions.slice(0, 10); // Limit to 10 suggestions
  }
  
  /**
   * Transpose a chord by semitones
   * @param {string} symbol - Original chord symbol
   * @param {number} semitones - Number of semitones to transpose
   * @returns {string} Transposed chord symbol
   */
  static transposeChord(symbol, semitones) {
    const parsed = this.parseChord(symbol);
    if (!parsed.isValid) return symbol;
    
    const chord = parsed.chord;
    const rootNote = chord.root + (chord.accidental || '');
    const rootMidi = NOTE_NUMBERS[rootNote];
    const newRootMidi = (rootMidi + semitones + 12) % 12;
    const newRootNote = MIDI_TO_NOTE[newRootMidi + 60];
    
    // Reconstruct chord symbol
    let newSymbol = newRootNote;
    
    // Add quality indicators
    if (chord.quality === 'minor') {
      newSymbol += 'm';
    } else if (chord.quality === 'diminished') {
      newSymbol += 'dim';
    } else if (chord.quality === 'augmented') {
      newSymbol += 'aug';
    } else if (chord.quality === 'sus2') {
      newSymbol += 'sus2';
    } else if (chord.quality === 'sus4') {
      newSymbol += 'sus4';
    }
    
    // Add extensions
    for (const extension of chord.extensions) {
      newSymbol += extension;
    }
    
    // Add bass note if present
    if (chord.bass) {
      const bassNote = chord.bass;
      const bassMidi = NOTE_NUMBERS[bassNote];
      const newBassMidi = (bassMidi + semitones + 12) % 12;
      const newBassNote = MIDI_TO_NOTE[newBassMidi + 60];
      newSymbol += '/' + newBassNote;
    }
    
    return newSymbol;
  }
}

// Export convenience functions
export const parseChord = ChordParser.parseChord.bind(ChordParser);
export const isValidChord = ChordParser.isValidChord.bind(ChordParser);
export const getChordSuggestions = ChordParser.getChordSuggestions.bind(ChordParser);
export const transposeChord = ChordParser.transposeChord.bind(ChordParser); 
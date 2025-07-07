/**
 * @fileoverview Type definitions for MIDI Recording Studio
 * All type definitions using JSDoc for type safety without TypeScript
 */

/**
 * @typedef {Object} NavigationState
 * @property {boolean} isPlaying - Whether audio is currently playing
 * @property {boolean} isRecording - Whether recording is active
 * @property {boolean} isCountingIn - Whether count-in is active
 * @property {number} tempo - Current BPM (60-200)
 * @property {boolean} metronomeEnabled - Whether metronome is active
 * @property {number} metronomeVolume - Metronome volume (0-1)
 * @property {number} currentBeat - Current beat number
 * @property {number} currentBar - Current bar number
 * @property {number} playheadPosition - Current playhead position in beats
 * @property {number} countInBeatsRemaining - Beats remaining in count-in (0-4)
 */

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
 */

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
 * @typedef {Object} ChordCell
 * @property {string} id - Unique identifier for the chord cell
 * @property {number} barNumber - Bar number in the progression
 * @property {string} chordSymbol - Chord symbol (e.g., "Cmaj", "Dm7")
 * @property {string[]} chordNotes - MIDI note names for the chord
 * @property {boolean} isEmpty - Whether the cell is empty
 */

/**
 * @typedef {Object} PlayheadState
 * @property {number} position - Current position in beats
 * @property {number} pixelPosition - Current pixel position on screen
 * @property {boolean} isDragging - Whether user is dragging playhead
 * @property {boolean} isVisible - Whether playhead is visible
 */

/**
 * @typedef {Object} ChatMessage
 * @property {string} id - Unique identifier for the message
 * @property {string} content - Message content
 * @property {Date} timestamp - When the message was sent
 * @property {boolean} isUser - Whether message is from user or AI
 * @property {boolean} [isLoading] - Whether message is being generated
 */

/**
 * @typedef {Object} UIState
 * @property {string|null} activeTrack - Currently selected track ID
 * @property {number} keyboardOctave - Current keyboard octave
 * @property {boolean} sidebarOpen - Whether sidebar is open
 */

/**
 * @typedef {Object} TrackProps
 * @property {Track} track - Track data object
 * @property {Function} onUpdate - Update callback
 * @property {boolean} [isSelected] - Optional selection state
 */ 
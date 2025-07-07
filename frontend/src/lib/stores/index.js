/**
 * @fileoverview Barrel exports for all stores
 * Provides a single import point for all store functionality
 */

// Re-export all stores
export { audioState, saveAudioState, loadAudioState } from './audio.js';
export { tracks, TRACK_COLORS, INSTRUMENTS, saveTracks, loadTracks } from './tracks.js';
export { chords, saveChords, loadChords } from './chords.js';
export { uiState, KEYBOARD_LAYOUTS, VIEWS, saveUIState, loadUIState } from './ui.js';

/**
 * Initialize all stores with saved data from localStorage
 */
export function initializeStores() {
  // Load saved states
  const savedAudio = loadAudioState();
  const savedTracks = loadTracks();
  const savedChords = loadChords();
  const savedUI = loadUIState();
  
  // Apply saved states to stores
  if (Object.keys(savedAudio).length > 0) {
    audioState.updateState(savedAudio);
  }
  
  if (savedTracks.length > 0) {
    tracks.set(savedTracks);
  } else {
    // Initialize with default tracks if none saved
    tracks.initializeDefault();
  }
  
  if (savedChords.length > 0) {
    chords.set(savedChords);
  }
  
  if (Object.keys(savedUI).length > 0) {
    uiState.updateState(savedUI);
  }
}

/**
 * Save all store states to localStorage
 */
export function saveAllStores() {
  // Get current state from stores
  let currentAudioState, currentTracks, currentChords, currentUI;
  
  audioState.subscribe(state => currentAudioState = state)();
  tracks.subscribe(trackList => currentTracks = trackList)();
  chords.subscribe(chordList => currentChords = chordList)();
  uiState.subscribe(state => currentUI = state)();
  
  // Save to localStorage
  saveAudioState(currentAudioState);
  saveTracks(currentTracks);
  saveChords(currentChords);
  saveUIState(currentUI);
}

/**
 * Reset all stores to initial state
 */
export function resetAllStores() {
  audioState.reset();
  tracks.reset();
  chords.reset();
  uiState.reset();
}

/**
 * Debug function to log all store states
 */
export function debugStores() {
  audioState.subscribe(state => console.log('Audio State:', state))();
  tracks.subscribe(trackList => console.log('Tracks:', trackList))();
  chords.subscribe(chordList => console.log('Chords:', chordList))();
  uiState.subscribe(state => console.log('UI State:', state))();
} 
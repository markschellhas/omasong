import { writable } from 'svelte/store';

/**
 * @typedef {Object} UIState
 * @property {string|null} activeTrack - Currently selected track ID
 * @property {number} keyboardOctave - Current keyboard octave
 * @property {boolean} sidebarOpen - Whether sidebar is open
 * @property {string} currentView - Current active view
 * @property {boolean} isFullscreen - Whether app is in fullscreen mode
 * @property {number} gridCols - Number of chord grid columns visible
 * @property {number} trackHeight - Height of individual tracks in pixels
 * @property {boolean} showChordNames - Whether to show chord names on virtual keyboard
 * @property {string} keyboardLayout - Keyboard layout (qwerty/dvorak/colemak)
 * @property {boolean} showVelocity - Whether to show velocity indicators
 * @property {number} zoomLevel - Timeline zoom level (0.5 - 4.0)
 */

/**
 * Initial UI state
 * @type {UIState}
 */
const initialUIState = {
  activeTrack: null,
  keyboardOctave: 4,
  sidebarOpen: true,
  currentView: 'studio', // studio, settings, help
  isFullscreen: false,
  gridCols: 8,
  trackHeight: 60,
  showChordNames: true,
  keyboardLayout: 'qwerty',
  showVelocity: true,
  zoomLevel: 1.0
};

/**
 * Create UI store with additional methods
 */
function createUIStore() {
  const { subscribe, set, update } = writable(initialUIState);

  return {
    subscribe,
    
    /**
     * Set active track
     * @param {string|null} trackId - Track ID or null to deselect
     */
    setActiveTrack: (trackId) => update(state => ({ ...state, activeTrack: trackId })),
    
    /**
     * Clear active track selection
     */
    clearActiveTrack: () => update(state => ({ ...state, activeTrack: null })),
    
    /**
     * Set keyboard octave
     * @param {number} octave - Octave number (1-8)
     */
    setKeyboardOctave: (octave) => {
      const clampedOctave = Math.max(1, Math.min(8, octave));
      update(state => ({ ...state, keyboardOctave: clampedOctave }));
    },
    
    /**
     * Shift keyboard octave up
     */
    octaveUp: () => update(state => ({ 
      ...state, 
      keyboardOctave: Math.min(8, state.keyboardOctave + 1) 
    })),
    
    /**
     * Shift keyboard octave down
     */
    octaveDown: () => update(state => ({ 
      ...state, 
      keyboardOctave: Math.max(1, state.keyboardOctave - 1) 
    })),
    
    /**
     * Toggle sidebar visibility
     */
    toggleSidebar: () => update(state => ({ ...state, sidebarOpen: !state.sidebarOpen })),
    
    /**
     * Set sidebar visibility
     * @param {boolean} open - Whether sidebar should be open
     */
    setSidebarOpen: (open) => update(state => ({ ...state, sidebarOpen: open })),
    
    /**
     * Set current view
     * @param {string} view - View name (studio, settings, help)
     */
    setCurrentView: (view) => update(state => ({ ...state, currentView: view })),
    
    /**
     * Toggle fullscreen mode
     */
    toggleFullscreen: () => update(state => ({ ...state, isFullscreen: !state.isFullscreen })),
    
    /**
     * Set fullscreen mode
     * @param {boolean} fullscreen - Whether to enable fullscreen
     */
    setFullscreen: (fullscreen) => update(state => ({ ...state, isFullscreen: fullscreen })),
    
    /**
     * Set chord grid columns
     * @param {number} cols - Number of columns (4, 8, 16)
     */
    setGridCols: (cols) => {
      const validCols = [4, 8, 16];
      const clampedCols = validCols.includes(cols) ? cols : 8;
      update(state => ({ ...state, gridCols: clampedCols }));
    },
    
    /**
     * Set track height
     * @param {number} height - Height in pixels (40-120)
     */
    setTrackHeight: (height) => {
      const clampedHeight = Math.max(40, Math.min(120, height));
      update(state => ({ ...state, trackHeight: clampedHeight }));
    },
    
    /**
     * Toggle chord names display on keyboard
     */
    toggleChordNames: () => update(state => ({ 
      ...state, 
      showChordNames: !state.showChordNames 
    })),
    
    /**
     * Set keyboard layout
     * @param {string} layout - Layout name (qwerty, dvorak, colemak)
     */
    setKeyboardLayout: (layout) => {
      const validLayouts = ['qwerty', 'dvorak', 'colemak'];
      const validLayout = validLayouts.includes(layout) ? layout : 'qwerty';
      update(state => ({ ...state, keyboardLayout: validLayout }));
    },
    
    /**
     * Toggle velocity indicators
     */
    toggleVelocity: () => update(state => ({ 
      ...state, 
      showVelocity: !state.showVelocity 
    })),
    
    /**
     * Set zoom level
     * @param {number} zoom - Zoom level (0.5 - 4.0)
     */
    setZoomLevel: (zoom) => {
      const clampedZoom = Math.max(0.5, Math.min(4.0, zoom));
      update(state => ({ ...state, zoomLevel: clampedZoom }));
    },
    
    /**
     * Zoom in
     */
    zoomIn: () => update(state => ({ 
      ...state, 
      zoomLevel: Math.min(4.0, state.zoomLevel * 1.2) 
    })),
    
    /**
     * Zoom out
     */
    zoomOut: () => update(state => ({ 
      ...state, 
      zoomLevel: Math.max(0.5, state.zoomLevel / 1.2) 
    })),
    
    /**
     * Reset zoom to default
     */
    resetZoom: () => update(state => ({ ...state, zoomLevel: 1.0 })),
    
    /**
     * Update multiple UI properties at once
     * @param {Partial<UIState>} updates - Properties to update
     */
    updateState: (updates) => update(state => ({ ...state, ...updates })),
    
    /**
     * Reset to initial state
     */
    reset: () => set(initialUIState),
    
    /**
     * Get responsive breakpoint info
     * @param {number} width - Window width
     * @returns {Object} Breakpoint information
     */
    getBreakpoint: (width) => {
      if (width < 768) return { name: 'mobile', cols: 1, sidebarBelow: true };
      if (width < 1024) return { name: 'tablet', cols: 2, sidebarBelow: true };
      return { name: 'desktop', cols: 4, sidebarBelow: false };
    },
    
    /**
     * Apply responsive layout based on window size
     * @param {number} width - Window width
     */
    applyResponsiveLayout: (width) => {
      const breakpoint = update(state => state).getBreakpoint(width);
      
      update(state => ({
        ...state,
        sidebarOpen: breakpoint.name === 'desktop' ? state.sidebarOpen : false,
        gridCols: breakpoint.name === 'mobile' ? 4 : state.gridCols
      }));
    }
  };
}

/** @type {import('svelte/store').Writable<UIState>} */
export const uiState = createUIStore();

/**
 * Keyboard layouts for different keyboard types
 */
export const KEYBOARD_LAYOUTS = {
  qwerty: {
    white: ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', "'"],
    black: ['w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[']
  },
  dvorak: {
    white: ['a', 'o', 'e', 'u', 'i', 'd', 'h', 't', 'n', 's', '-'],
    black: [',', '.', 'p', 'y', 'f', 'g', 'c', 'r', 'l', '/']
  },
  colemak: {
    white: ['a', 'r', 's', 't', 'd', 'h', 'n', 'e', 'i', 'o', "'"],
    black: ['w', 'f', 'p', 'g', 'j', 'l', 'u', 'y', ';', '[']
  }
};

/**
 * Available views in the application
 */
export const VIEWS = {
  STUDIO: 'studio',
  SETTINGS: 'settings', 
  HELP: 'help'
};

/**
 * Save UI state to localStorage
 * @param {UIState} state - Current UI state
 */
export function saveUIState(state) {
  try {
    const persistentState = {
      keyboardOctave: state.keyboardOctave,
      sidebarOpen: state.sidebarOpen,
      gridCols: state.gridCols,
      trackHeight: state.trackHeight,
      showChordNames: state.showChordNames,
      keyboardLayout: state.keyboardLayout,
      showVelocity: state.showVelocity,
      zoomLevel: state.zoomLevel
    };
    localStorage.setItem('midi-studio-ui', JSON.stringify(persistentState));
  } catch (error) {
    console.warn('Failed to save UI state:', error);
  }
}

/**
 * Load UI state from localStorage
 * @returns {Partial<UIState>} Saved UI state
 */
export function loadUIState() {
  try {
    const saved = localStorage.getItem('midi-studio-ui');
    return saved ? JSON.parse(saved) : {};
  } catch (error) {
    console.warn('Failed to load UI state:', error);
    return {};
  }
} 
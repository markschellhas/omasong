<script>
  import { onMount, onDestroy } from 'svelte';
  import { browser } from '$app/environment';
  import { ChevronUp, ChevronDown } from 'lucide-svelte';
  import { uiState, KEYBOARD_LAYOUTS } from '../../stores/ui.js';
  import { audioState } from '../../stores/audio.js';
  import { tracks } from '../../stores/tracks.js';
  import { getAudioEngine, getMidiRecorder } from '../../utils/index.js';
  import { getMidiPlayer } from '../../utils/midiPlayer.js';
  import * as Tone from 'tone';
  
  /** @type {import('../../utils/audioEngine.js').AudioEngine} */
  let audioEngine;
  
  /** @type {import('../../utils/midiRecorder.js').MidiRecorder} */
  let midiRecorder;
  
  /** @type {Tone.PolySynth} */
  let keyboardSynth;
  
  /** @type {boolean} */
  let audioInitialized = false;
  
  /** @type {string} */
  let audioStatus = 'Not initialized';
  
  /** @type {import('../../stores/ui.js').UIState} */
  let currentUIState;
  
  /** @type {import('../../stores/audio.js').AudioState} */
  let currentAudioState;
  
  /** @type {import('../../stores/tracks.js').Track[]} */
  let currentTracks = [];
  
  /** @type {Set<string>} */
  let pressedKeys = new Set();
  
  /** @type {Set<number>} */
  let activeNotes = new Set();
  
  /** @type {boolean} */
  let sustainEnabled = false;
  
  /** @type {Map<string, number>} */
  let keyPressTimestamps = new Map();
  
  /** @type {Map<number, number>} */
  let noteVelocities = new Map();
  
  /** @type {Map<number, number>} */
  let noteStartTimes = new Map();
  
  // Piano layout (2 octaves)
  const OCTAVE_KEYS = [
    { note: 'C', type: 'white', keyIndex: 0 },
    { note: 'C#', type: 'black', keyIndex: 0.5 },
    { note: 'D', type: 'white', keyIndex: 1 },
    { note: 'D#', type: 'black', keyIndex: 1.5 },
    { note: 'E', type: 'white', keyIndex: 2 },
    { note: 'F', type: 'white', keyIndex: 3 },
    { note: 'F#', type: 'black', keyIndex: 3.5 },
    { note: 'G', type: 'white', keyIndex: 4 },
    { note: 'G#', type: 'black', keyIndex: 4.5 },
    { note: 'A', type: 'white', keyIndex: 5 },
    { note: 'A#', type: 'black', keyIndex: 5.5 },
    { note: 'B', type: 'white', keyIndex: 6 }
  ];
  
  // Create 2 octaves of keys
  $: pianoKeys = [
    ...OCTAVE_KEYS.map(key => ({
      ...key,
      octave: currentUIState?.keyboardOctave || 4,
      midiNote: (currentUIState?.keyboardOctave || 4) * 12 + getNoteOffset(key.note)
    })),
    ...OCTAVE_KEYS.map(key => ({
      ...key,
      octave: (currentUIState?.keyboardOctave || 4) + 1,
      midiNote: ((currentUIState?.keyboardOctave || 4) + 1) * 12 + getNoteOffset(key.note)
    }))
  ];
  
  // Key mapping based on keyboard layout
  $: keyLayout = KEYBOARD_LAYOUTS[currentUIState?.keyboardLayout || 'qwerty'];
  $: keyToMidiMap = createKeyToMidiMap();
  
  // Subscribe to stores
  const unsubscribeUI = uiState.subscribe(state => {
    currentUIState = state;
  });
  
  const unsubscribeAudio = audioState.subscribe(state => {
    currentAudioState = state;
  });
  
  const unsubscribeTracks = tracks.subscribe(trackList => {
    currentTracks = trackList;
  });
  
  onMount(async () => {
    if (!browser) return;
    
    console.log('🎹 VirtualKeyboard: Initializing...');
    audioStatus = 'Initializing...';
    
    try {
      audioEngine = getAudioEngine();
      midiRecorder = getMidiRecorder(audioEngine);
      console.log('🎹 VirtualKeyboard: Audio engine and MIDI recorder obtained');
      
      // Add click listener to initialize audio on first user interaction
      document.addEventListener('click', initializeAudioOnInteraction, { once: true });
      document.addEventListener('keydown', initializeAudioOnInteraction, { once: true });
      
      console.log('🎹 VirtualKeyboard: Waiting for user interaction to start audio...');
      audioStatus = 'Waiting for user interaction...';
      
    } catch (error) {
      console.error('🎹 VirtualKeyboard: Failed to get audio engine:', error);
      audioStatus = `Error: ${error.message}`;
    }
    
    // Add keyboard event listeners
    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('keyup', handleKeyUp);
    
    // Add touch event listeners for mobile
    document.addEventListener('touchstart', handleTouchStart, { passive: false });
    document.addEventListener('touchend', handleTouchEnd, { passive: false });
  });
  
  onDestroy(() => {
    unsubscribeUI();
    unsubscribeAudio();
    unsubscribeTracks();
    
    // Clean up synth
    if (keyboardSynth) {
      console.log('🎹 VirtualKeyboard: Disposing synth');
      keyboardSynth.dispose();
    }
    
    // Remove event listeners
    if (browser) {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('keyup', handleKeyUp);
      document.removeEventListener('touchstart', handleTouchStart);
      document.removeEventListener('touchend', handleTouchEnd);
      document.removeEventListener('click', initializeAudioOnInteraction);
      document.removeEventListener('keydown', initializeAudioOnInteraction);
    }
  });
  
  /**
   * Initialize audio on first user interaction
   */
  async function initializeAudioOnInteraction() {
    if (audioInitialized) return;
    
    console.log('🎹 VirtualKeyboard: User interaction detected, initializing audio...');
    audioStatus = 'Initializing audio...';
    
    try {
      // Initialize audio engine
      await audioEngine.initialize();
      console.log('🎹 VirtualKeyboard: Audio engine initialized');
      
      // Set up keyboard synth
      await setupKeyboardSynth();
      console.log('🎹 VirtualKeyboard: Keyboard synth ready');
      
      // Initialize MidiPlayer audio chains now that engine is ready
      const midiPlayer = getMidiPlayer(audioEngine);
      midiPlayer.initializeAllTrackAudio();
      console.log('🎹 VirtualKeyboard: MidiPlayer audio initialized');
      
      audioInitialized = true;
      audioStatus = 'Ready';
      
      console.log('🎹 VirtualKeyboard: Audio system fully initialized');
      
    } catch (error) {
      console.error('🎹 VirtualKeyboard: Failed to initialize audio:', error);
      audioStatus = `Error: ${error.message}`;
    }
  }
  
  /**
   * Set up the keyboard synthesizer
   */
  async function setupKeyboardSynth() {
    try {
      console.log('🎹 VirtualKeyboard: Creating keyboard synth...');
      console.log('🎹 VirtualKeyboard: Tone context state:', Tone.context.state);
      
      // Create a polyphonic synthesizer for the virtual keyboard
      keyboardSynth = new Tone.PolySynth(Tone.Synth, {
        oscillator: { type: 'triangle' },
        envelope: { 
          attack: 0.02, 
          decay: 0.1, 
          sustain: 0.3, 
          release: 1 
        }
      });
      
      console.log('🎹 VirtualKeyboard: Synth created, connecting to destination...');
      
      // Connect directly to destination for now
      keyboardSynth.toDestination();
      
      // Set volume
      keyboardSynth.volume.value = -12; // Reduce volume to avoid distortion
      
      console.log('🎹 VirtualKeyboard: Synth connected to destination');
      console.log('🎹 VirtualKeyboard: Synth volume:', keyboardSynth.volume.value);
      
    } catch (error) {
      console.error('🎹 VirtualKeyboard: Failed to setup keyboard synth:', error);
      throw error;
    }
  }
  
  /**
   * Get MIDI note offset for note name
   * @param {string} noteName - Note name (C, C#, D, etc.)
   * @returns {number} MIDI offset
   */
  function getNoteOffset(noteName) {
    const offsets = {
      'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5,
      'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11
    };
    return offsets[noteName];
  }
  
  /**
   * Create mapping from keyboard keys to MIDI notes
   * @returns {Map<string, number>} Key to MIDI note mapping
   */
  function createKeyToMidiMap() {
    const map = new Map();
    const baseOctave = currentUIState?.keyboardOctave || 4;
    
    // White keys mapping
    keyLayout.white.forEach((key, index) => {
      if (index < 7) {
        // First octave
        const whiteNoteOffsets = [0, 2, 4, 5, 7, 9, 11]; // C, D, E, F, G, A, B
        const midiNote = baseOctave * 12 + whiteNoteOffsets[index];
        map.set(key, midiNote);
      } else {
        // Second octave
        const whiteNoteOffsets = [0, 2, 4, 5]; // C, D, E, F of next octave
        const midiNote = (baseOctave + 1) * 12 + whiteNoteOffsets[index - 7];
        map.set(key, midiNote);
      }
    });
    
    // Black keys mapping
    keyLayout.black.forEach((key, index) => {
      if (index < 5) {
        // First octave
        const blackNoteOffsets = [1, 3, 6, 8, 10]; // C#, D#, F#, G#, A#
        const midiNote = baseOctave * 12 + blackNoteOffsets[index];
        map.set(key, midiNote);
      } else {
        // Second octave
        const blackNoteOffsets = [1, 3, 6, 8, 10]; // C#, D#, F#, G#, A# of next octave
        const midiNote = (baseOctave + 1) * 12 + blackNoteOffsets[index - 5];
        map.set(key, midiNote);
      }
    });
    
    return map;
  }
  
  /**
   * Calculate velocity based on key press timing
   * @param {string} key - Keyboard key
   * @returns {number} Velocity (0-127)
   */
  function calculateVelocity(key) {
    const now = performance.now();
    const lastPress = keyPressTimestamps.get(key);
    
    if (!lastPress) {
      keyPressTimestamps.set(key, now);
      return 100; // Default velocity
    }
    
    const timeDiff = now - lastPress;
    keyPressTimestamps.set(key, now);
    
    // Convert timing to velocity (faster = louder)
    const velocity = Math.max(30, Math.min(127, 127 - (timeDiff * 2)));
    return Math.round(velocity);
  }
  
  /**
   * Handle keyboard key down
   * @param {KeyboardEvent} event
   */
  function handleKeyDown(event) {
    // Initialize audio if not already done
    if (!audioInitialized) {
      initializeAudioOnInteraction();
    }
    
    // Prevent default for mapped keys
    if (keyToMidiMap.has(event.key) || event.key === ' ') {
      event.preventDefault();
    }
    
    // Handle sustain pedal (spacebar)
    if (event.key === ' ') {
      sustainEnabled = true;
      return;
    }
    
    // Ignore if key is already pressed
    if (pressedKeys.has(event.key)) return;
    
    const midiNote = keyToMidiMap.get(event.key);
    if (midiNote !== undefined) {
      pressedKeys.add(event.key);
      const velocity = calculateVelocity(event.key);
      playNote(midiNote, velocity);
    }
  }
  
  /**
   * Handle keyboard key up
   * @param {KeyboardEvent} event
   */
  function handleKeyUp(event) {
    // Handle sustain pedal release
    if (event.key === ' ') {
      sustainEnabled = false;
      // Release all sustained notes
      if (!sustainEnabled) {
        activeNotes.forEach(note => {
          releaseNote(note);
        });
      }
      return;
    }
    
    const midiNote = keyToMidiMap.get(event.key);
    if (midiNote !== undefined && pressedKeys.has(event.key)) {
      pressedKeys.delete(event.key);
      
      // Only release note if sustain is not enabled
      if (!sustainEnabled) {
        releaseNote(midiNote);
      }
    }
  }
  
  /**
   * Handle touch start for mobile
   * @param {TouchEvent} event
   */
  function handleTouchStart(event) {
    if (!browser) return;
    event.preventDefault();
    
    // Initialize audio if not already done
    if (!audioInitialized) {
      initializeAudioOnInteraction();
    }
    
    for (const touch of event.touches) {
      const element = document.elementFromPoint(touch.clientX, touch.clientY);
      if (element && element.dataset.midiNote) {
        const midiNote = parseInt(element.dataset.midiNote);
        playNote(midiNote, 100);
      }
    }
  }
  
  /**
   * Handle touch end for mobile
   * @param {TouchEvent} event
   */
  function handleTouchEnd(event) {
    if (!browser) return;
    event.preventDefault();
    
    for (const touch of event.changedTouches) {
      const element = document.elementFromPoint(touch.clientX, touch.clientY);
      if (element && element.dataset.midiNote) {
        const midiNote = parseInt(element.dataset.midiNote);
        releaseNote(midiNote);
      }
    }
  }
  
  /**
   * Handle mouse/touch press on virtual key
   * @param {number} midiNote - MIDI note number
   */
  function handleKeyPress(midiNote) {
    // Initialize audio if not already done
    if (!audioInitialized) {
      initializeAudioOnInteraction();
    }
    
    playNote(midiNote, 100);
  }
  
  /**
   * Handle mouse/touch release on virtual key
   * @param {number} midiNote - MIDI note number
   */
  function handleKeyRelease(midiNote) {
    if (!sustainEnabled) {
      releaseNote(midiNote);
    }
  }
  
  /**
   * Play a note
   * @param {number} midiNote - MIDI note number
   * @param {number} velocity - Note velocity (0-127)
   */
  function playNote(midiNote, velocity) {
    if (activeNotes.has(midiNote)) return;
    
    console.log(`🎹 Playing note: ${midiNote}, velocity: ${velocity}, synth: ${!!keyboardSynth}, initialized: ${audioInitialized}`);
    
    activeNotes.add(midiNote);
    noteVelocities.set(midiNote, velocity);
    
    // Record note start time for duration calculation
    noteStartTimes.set(midiNote, performance.now());
    
    // Record MIDI event if recording is active and a track is armed
    if (currentAudioState?.isRecording && midiRecorder && audioInitialized) {
      const armedTrack = currentTracks.find(t => t.isArmed);
      if (armedTrack && midiRecorder.getStatus().isRecording) {
        const success = midiRecorder.recordNoteOn(midiNote, velocity);
        console.log(`🎹 Recording note ON: ${midiNote} to track: ${armedTrack.name}, success: ${success}, recorder status:`, midiRecorder.getStatus());
      } else {
        console.log(`🎹 Cannot record note ON: ${midiNote}, armedTrack: ${!!armedTrack}, recorderStatus:`, midiRecorder?.getStatus());
      }
    }
    
    // Trigger audio through keyboard synth
    if (keyboardSynth && audioInitialized) {
      try {
        const frequency = Tone.Frequency(midiNote, 'midi');
        const normalizedVelocity = velocity / 127;
        console.log(`🎹 Triggering synth: freq=${frequency.toFrequency()}Hz, vel=${normalizedVelocity}`);
        keyboardSynth.triggerAttack(frequency, undefined, normalizedVelocity);
      } catch (error) {
        console.error('🎹 Failed to play note:', error);
      }
    } else {
      console.warn('🎹 Cannot play note - synth not ready:', { 
        synth: !!keyboardSynth, 
        initialized: audioInitialized,
        audioStatus 
      });
    }
    
    // Trigger reactive update
    activeNotes = new Set(activeNotes);
  }
  
  /**
   * Release a note
   * @param {number} midiNote - MIDI note number
   */
  function releaseNote(midiNote) {
    console.log(`🎹 Releasing note: ${midiNote}`);
    
    // Record MIDI note off if recording is active and a track is armed
    if (currentAudioState?.isRecording && midiRecorder && audioInitialized) {
      const armedTrack = currentTracks.find(t => t.isArmed);
      if (armedTrack && midiRecorder.getStatus().isRecording) {
        const success = midiRecorder.recordNoteOff(midiNote);
        console.log(`🎹 Recording note OFF: ${midiNote} to track: ${armedTrack.name}, success: ${success}`);
      }
    }
    
    activeNotes.delete(midiNote);
    noteVelocities.delete(midiNote);
    noteStartTimes.delete(midiNote);
    
    // Release note through keyboard synth
    if (keyboardSynth && audioInitialized) {
      try {
        const frequency = Tone.Frequency(midiNote, 'midi');
        keyboardSynth.triggerRelease(frequency);
      } catch (error) {
        console.error('🎹 Failed to release note:', error);
      }
    }
    
    // Trigger reactive update
    activeNotes = new Set(activeNotes);
  }
  
  /**
   * Get key for MIDI note
   * @param {number} midiNote - MIDI note number
   * @returns {string|null} Computer key or null
   */
  function getKeyForNote(midiNote) {
    for (const [key, note] of keyToMidiMap.entries()) {
      if (note === midiNote) return key;
    }
    return null;
  }
  
  /**
   * Check if note is pressed
   * @param {number} midiNote - MIDI note number
   * @returns {boolean} Is pressed
   */
  function isNoteActive(midiNote) {
    return activeNotes.has(midiNote);
  }
  
  /**
   * Get velocity for note
   * @param {number} midiNote - MIDI note number
   * @returns {number} Velocity (0-127)
   */
  function getNoteVelocity(midiNote) {
    return noteVelocities.get(midiNote) || 0;
  }
  
  /**
   * Calculate the left position for black keys
   * @param {number} keyIndex - The key index (0.5, 1.5, 3.5, etc.)
   * @param {number} octaveOffset - The octave offset (0 for first octave, 7 for second)
   * @returns {number} Left position percentage
   */
  function getBlackKeyPosition(keyIndex, octaveOffset = 0) {
    // Map each black key to its position relative to white keys
    const blackKeyPositions = {
      0.5: 7.14,   // C# - after first white key (C)
      1.5: 14.28,  // D# - after second white key (D)  
      3.5: 35.71,  // F# - after fourth white key (F)
      4.5: 42.85,  // G# - after fifth white key (G)
      5.5: 50.0    // A# - after sixth white key (A)
    };
    
    const basePosition = blackKeyPositions[keyIndex % 7] || 0;
    const octavePosition = octaveOffset * (100 / 14); // Each octave takes 7/14 of the space
    
    return basePosition + octavePosition;
  }
  
  /**
   * Test audio by playing a note
   */
  function testAudio() {
    console.log('🎹 Testing audio...');
    playNote(60, 100); // Middle C
    setTimeout(() => releaseNote(60), 1000);
  }
</script>

<!-- Virtual Keyboard Container -->
<section class="col-span-3 bg-gray-800 p-4">
  <div class="flex items-center justify-between mb-4">
    <div class="text-sm font-medium">Virtual Keyboard</div>
    
    <!-- Audio Status & Recording Indicator -->
    <div class="flex items-center space-x-4">
      <div class="text-xs">
        <span class="text-gray-400">Audio:</span>
        <span class="{audioInitialized ? 'text-green-400' : 'text-yellow-400'}">{audioStatus}</span>
      </div>
      
      {#if currentAudioState?.isRecording}
        <div class="text-xs bg-red-600 text-white px-2 py-1 rounded animate-pulse">
          RECORDING
          {#if currentTracks.find(t => t.isArmed)}
            → {currentTracks.find(t => t.isArmed)?.name}
          {/if}
        </div>
      {:else if currentTracks.find(t => t.isArmed)}
        <div class="text-xs bg-yellow-600 text-white px-2 py-1 rounded">
          ARMED: {currentTracks.find(t => t.isArmed)?.name}
        </div>
      {/if}
      
      {#if audioInitialized}
        <button 
          class="bg-blue-600 hover:bg-blue-700 text-white text-xs px-2 py-1 rounded"
          on:click={testAudio}
          title="Test Audio"
        >
          Test
        </button>
      {/if}
    </div>
    
    <!-- Octave Controls -->
    <div class="flex items-center space-x-2">
      <button 
        class="bg-gray-600 hover:bg-gray-700 text-white p-1 rounded transition-colors duration-200"
        on:click={() => uiState.octaveDown()}
        title="Octave Down"
      >
        <ChevronDown class="w-4 h-4" />
      </button>
      
      <span class="text-sm font-mono min-w-[3rem] text-center">
        Oct {currentUIState?.keyboardOctave || 4}
      </span>
      
      <button 
        class="bg-gray-600 hover:bg-gray-700 text-white p-1 rounded transition-colors duration-200"
        on:click={() => uiState.octaveUp()}
        title="Octave Up"
      >
        <ChevronUp class="w-4 h-4" />
      </button>
      
      <!-- Sustain Indicator -->
      <div class="flex items-center space-x-2 ml-4">
        <span class="text-xs text-gray-400">Sustain:</span>
        <div class="w-3 h-3 rounded-full {sustainEnabled ? 'bg-yellow-500' : 'bg-gray-600'}"></div>
        <span class="text-xs text-gray-400">(Space)</span>
      </div>
    </div>
  </div>
  
  <!-- Piano Keys -->
  <div class="relative h-32 bg-gray-900 rounded-lg overflow-hidden">
    <!-- White Keys -->
    <div class="flex h-full">
      {#each pianoKeys.filter(key => key.type === 'white') as key}
        {@const isActive = isNoteActive(key.midiNote)}
        {@const velocity = getNoteVelocity(key.midiNote)}
        {@const computerKey = getKeyForNote(key.midiNote)}
        
        <div 
          class="flex-1 border border-gray-600 cursor-pointer transition-all duration-150 flex flex-col justify-end items-center p-2 relative
            {isActive 
              ? 'bg-blue-100 border-blue-300 shadow-lg shadow-blue-400/50' 
              : 'bg-white hover:bg-gray-100 border-gray-600'}"
          style="opacity: {isActive ? 0.85 + (velocity / 127) * 0.15 : 1}"
          data-midi-note={key.midiNote}
          on:mousedown={() => handleKeyPress(key.midiNote)}
          on:mouseup={() => handleKeyRelease(key.midiNote)}
          on:mouseleave={() => handleKeyRelease(key.midiNote)}
          role="button"
          tabindex="0"
          aria-label="Piano key {key.note}{key.octave}"
        >
          <!-- Note Label -->
          <div class="text-xs font-medium mb-1 {isActive ? 'text-blue-800' : 'text-gray-700'}">
            {key.note}{key.octave}
          </div>
          
          <!-- Computer Key Label -->
          {#if computerKey}
            <div class="text-xs px-1 rounded {isActive ? 'text-blue-700 bg-blue-50' : 'text-gray-500 bg-gray-200'}">
              {computerKey.toUpperCase()}
            </div>
          {/if}
          
          <!-- Velocity Indicator -->
          {#if isActive && currentUIState?.showVelocity}
            <div class="absolute top-1 right-1 w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
          {/if}
          
          <!-- Active Key Glow Effect -->
          {#if isActive}
            <div class="absolute inset-0 bg-blue-400/20 rounded pointer-events-none"></div>
          {/if}
        </div>
      {/each}
    </div>
    
    <!-- Black Keys -->
    <div class="absolute top-0 left-0 h-20 flex pointer-events-none w-full">
      {#each pianoKeys.filter(key => key.type === 'black') as key}
        {@const isActive = isNoteActive(key.midiNote)}
        {@const velocity = getNoteVelocity(key.midiNote)}
        {@const computerKey = getKeyForNote(key.midiNote)}
        {@const octaveOffset = key.octave > (currentUIState?.keyboardOctave || 4) ? 7 : 0}
        {@const leftPosition = getBlackKeyPosition(key.keyIndex, octaveOffset)}
        
        <div 
          class="absolute w-8 h-full cursor-pointer transition-all duration-150 flex flex-col justify-end items-center p-1 pointer-events-auto border rounded-sm
            {isActive 
              ? 'bg-blue-600 border-blue-400 shadow-lg shadow-blue-500/60' 
              : 'bg-gray-900 hover:bg-gray-700 border-gray-700'}"
          style="left: {leftPosition}%; transform: translateX(-50%); opacity: {isActive ? 0.9 + (velocity / 127) * 0.1 : 1}"
          data-midi-note={key.midiNote}
          on:mousedown={() => handleKeyPress(key.midiNote)}
          on:mouseup={() => handleKeyRelease(key.midiNote)}
          on:mouseleave={() => handleKeyRelease(key.midiNote)}
          role="button"
          tabindex="0"
          aria-label="Piano key {key.note}{key.octave}"
        >
          <!-- Computer Key Label -->
          {#if computerKey}
            <div class="text-xs px-1 rounded {isActive ? 'text-blue-100 bg-blue-700/50' : 'text-white bg-gray-800'}">
              {computerKey.toUpperCase()}
            </div>
          {/if}
          
          <!-- Velocity Indicator -->
          {#if isActive && currentUIState?.showVelocity}
            <div class="absolute top-1 right-1 w-1.5 h-1.5 bg-blue-300 rounded-full animate-pulse"></div>
          {/if}
          
          <!-- Active Key Glow Effect -->
          {#if isActive}
            <div class="absolute inset-0 bg-blue-400/30 rounded-sm pointer-events-none"></div>
          {/if}
        </div>
      {/each}
    </div>
  </div>
  
  <!-- Key Mapping Help -->
  <div class="mt-2 text-xs text-gray-400 text-center">
    White keys: {keyLayout.white.slice(0, 11).join(' ')} | 
    Black keys: {keyLayout.black.slice(0, 10).join(' ')} | 
    Sustain: SPACE
  </div>
</section>

<style>
  /* Prevent text selection on piano keys */
  [data-midi-note] {
    user-select: none;
    -webkit-user-select: none;
    -moz-user-select: none;
    -ms-user-select: none;
  }
  
  /* Touch-friendly styles for mobile */
  @media (hover: none) {
    [data-midi-note] {
      min-height: 4rem;
    }
  }
</style> 
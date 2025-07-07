<script>
  import { onMount, onDestroy } from 'svelte';
  import { browser } from '$app/environment';
  import { Volume2, Headphones, Mic, Square, Trash2 } from 'lucide-svelte';
  import { tracks, TRACK_COLORS, INSTRUMENTS } from '../../stores/tracks.js';
  import { audioState } from '../../stores/audio.js';
  import { uiState } from '../../stores/ui.js';
  import { getAudioEngine, getMidiRecorder, getMidiPlayer } from '../../utils/index.js';
  import { getChordPlayer } from '../../utils/chordPlayer.js';
  import Track from './Track.svelte';
  
  /** @type {import('../../utils/audioEngine.js').AudioEngine} */
  let audioEngine;
  
  /** @type {import('../../utils/midiRecorder.js').MidiRecorder} */
  let midiRecorder;
  
  /** @type {import('../../utils/midiPlayer.js').MidiPlayer} */
  let midiPlayer;
  
  /** @type {import('../../utils/chordPlayer.js').ChordPlayer} */
  let chordPlayer;
  
  /** @type {import('../../stores/tracks.js').Track[]} */
  let currentTracks = [];
  
  /** @type {import('../../stores/audio.js').AudioState} */
  let currentAudioState;
  
  /** @type {import('../../stores/ui.js').UIState} */
  let currentUIState;
  
  /** @type {HTMLDivElement} */
  let trackListContainer;
  
  // Subscribe to stores
  const unsubscribeTracks = tracks.subscribe(trackList => {
    currentTracks = trackList;
    
    // Handle solo logic in player
    if (midiPlayer) {
      midiPlayer.handleSoloLogic(trackList);
    }
  });
  
  const unsubscribeAudio = audioState.subscribe(state => {
    currentAudioState = state;
    
    // Handle recording state changes - only stop recording, start is handled by count-in completion
    if (!state.isRecording && midiRecorder?.getStatus().isRecording) {
      console.log('🎵 TrackList: Stopping MIDI recording');
      midiRecorder.stopRecording();
    }
    
    // Handle playback state changes
    if (state.isPlaying && !midiPlayer?.isPlaying()) {
      midiPlayer?.startPlayback(currentTracks);
    } else if (!state.isPlaying && midiPlayer?.isPlaying()) {
      midiPlayer?.stopPlayback();
    }
  });
  
  const unsubscribeUI = uiState.subscribe(state => {
    currentUIState = state;
  });
  
  onMount(() => {
    if (!browser) return;
    
    audioEngine = getAudioEngine();
    midiRecorder = getMidiRecorder(audioEngine);
    midiPlayer = getMidiPlayer(audioEngine);
    chordPlayer = getChordPlayer(audioEngine);
    
    // Initialize with default tracks if none exist
    if (currentTracks.length === 0) {
      tracks.initializeDefault();
    }
    
    // Set up event listeners for recording and playback
    setupEventListeners();
    
    // Listen for MIDI recording start signal from audio engine
    audioEngine.addEventListener('startMidiRecording', handleStartMidiRecording);
    
    // Listen for stop and disarm signal from audio engine
    audioEngine.addEventListener('stopAndDisarm', handleStopAndDisarm);
    
    // Add keyboard event listeners
    document.addEventListener('keydown', handleKeydown);
  });
  
  onDestroy(() => {
    unsubscribeTracks();
    unsubscribeAudio();
    unsubscribeUI();
    
    // Remove audio engine event listeners
    if (audioEngine) {
      audioEngine.removeEventListener('startMidiRecording', handleStartMidiRecording);
      audioEngine.removeEventListener('stopAndDisarm', handleStopAndDisarm);
    }
    
    // Remove keyboard event listeners
    if (browser) {
      document.removeEventListener('keydown', handleKeydown);
    }
  });
  
  /**
   * Set up event listeners for MIDI recorder and player
   */
  function setupEventListeners() {
    if (midiRecorder) {
      midiRecorder.addEventListener('recordingStarted', handleRecordingStarted);
      midiRecorder.addEventListener('recordingStopped', handleRecordingStopped);
      midiRecorder.addEventListener('noteRecorded', handleNoteRecorded);
    }
    
    if (midiPlayer) {
      midiPlayer.addEventListener('notePlayed', handleNotePlayed);
      midiPlayer.addEventListener('noteReleased', handleNoteReleased);
    }
  }
  
  /**
   * Handle recording started event
   * @param {CustomEvent} event
   */
  function handleRecordingStarted(event) {
    console.log('Recording started for track:', event.detail.trackId);
  }
  
  /**
   * Handle recording stopped event
   * @param {CustomEvent} event
   */
  function handleRecordingStopped(event) {
    console.log('Recording stopped for track:', event.detail.trackId, 'Events:', event.detail.eventCount);
  }
  
  /**
   * Handle note recorded event
   * @param {CustomEvent} event
   */
  function handleNoteRecorded(event) {
    // Could be used for real-time visual feedback
    // console.log('Note recorded:', event.detail);
  }
  
  /**
   * Handle note played event
   * @param {CustomEvent} event
   */
  function handleNotePlayed(event) {
    // Could be used for real-time visual feedback
    // console.log('Note played:', event.detail);
  }
  
  /**
   * Handle note released event
   * @param {CustomEvent} event
   */
  function handleNoteReleased(event) {
    // Could be used for real-time visual feedback
    // console.log('Note released:', event.detail);
  }
  
  /**
   * Start recording on the armed track
   */
  function startRecordingOnArmedTrack() {
    const armedTrack = currentTracks.find(t => t.isArmed);
    if (armedTrack) {
      midiRecorder.startRecording(armedTrack.id);
    }
  }
  
  /**
   * Handle MIDI recording start signal from audio engine (after count-in)
   */
  function handleStartMidiRecording() {
    console.log('🎵 TrackList: Starting MIDI recording after count-in');
    startRecordingOnArmedTrack();
  }
  
  /**
   * Handle stop and disarm signal from audio engine
   */
  function handleStopAndDisarm() {
    console.log('🎵 TrackList: Stopping and disarming all tracks');
    
    // Disarm all tracks
    currentTracks.forEach(track => {
      if (track.isArmed) {
        tracks.updateTrackProperty(track.id, 'isArmed', false);
      }
    });
  }
  
  // Track management functions removed - keeping it simple with just 2 tracks
  
  /**
   * Handle track property updates
   * @param {string} trackId - Track ID
   * @param {string} property - Property name
   * @param {any} value - New value
   */
  function updateTrackProperty(trackId, property, value) {
    tracks.updateTrackProperty(trackId, property, value);
  }
  
  /**
   * Arm track for recording
   * @param {string} trackId - Track ID to arm
   */
  function armTrack(trackId) {
    tracks.armForRecording(trackId);
    uiState.setActiveTrack(trackId);
  }
  
  /**
   * Toggle track mute
   * @param {string} trackId - Track ID
   */
  function toggleMute(trackId) {
    tracks.toggleMute(trackId);
  }
  
  /**
   * Toggle track solo
   * @param {string} trackId - Track ID
   */
  function toggleSolo(trackId) {
    tracks.toggleSolo(trackId);
  }
  
  /**
   * Set track volume
   * @param {string} trackId - Track ID
   * @param {number} volume - Volume level (0-1)
   */
  function setTrackVolume(trackId, volume) {
    tracks.setVolume(trackId, volume);
  }
  
  /**
   * Set track instrument
   * @param {string} trackId - Track ID
   * @param {string} instrument - Instrument name
   */
  function setTrackInstrument(trackId, instrument) {
    tracks.setInstrument(trackId, instrument);
  }
  
  /**
   * Clear MIDI events from track
   * @param {string} trackId - Track ID
   */
  function clearTrackEvents(trackId) {
    if (confirm('Are you sure you want to clear all recorded events from this track?')) {
      tracks.clearMidiEvents(trackId);
    }
  }
  
  /**
   * Get track recording level (placeholder for future implementation)
   * @param {string} trackId - Track ID
   * @returns {number} Recording level (0-1)
   */
  function getTrackRecordingLevel(trackId) {
    // This would be implemented with actual audio level detection
    return currentAudioState?.isRecording && 
           currentTracks.find(t => t.id === trackId)?.isArmed ? 
           Math.random() * 0.5 + 0.1 : 0;
  }
  
  /**
   * Check if track has any MIDI events
   * @param {import('../../stores/tracks.js').Track} track - Track to check
   * @returns {boolean} Has events
   */
  function trackHasEvents(track) {
    return track.midiEvents && track.midiEvents.length > 0;
  }
  
  /**
   * Get track event count
   * @param {import('../../stores/tracks.js').Track} track - Track to check
   * @returns {number} Event count
   */
  function getTrackEventCount(track) {
    return track.midiEvents ? track.midiEvents.length : 0;
  }
  
  /**
   * Add a test note to the armed track for testing visualization
   */
  function addTestNote() {
    const armedTrack = currentTracks.find(t => t.isArmed);
    if (!armedTrack) {
      alert('Please arm a track first (press 1 or 2)');
      return;
    }
    
    // Create a test MIDI event
    const testEvent = {
      time: Math.random() * 4, // Random time between 0-4 beats
      note: 60 + Math.floor(Math.random() * 12), // Random note C4-B4
      velocity: 80 + Math.floor(Math.random() * 40), // Random velocity 80-120
      duration: 0.5 + Math.random() * 1.5 // Random duration 0.5-2 beats
    };
    
    console.log('🎵 TrackList: Adding test note:', testEvent);
    tracks.addMidiEvent(armedTrack.id, testEvent);
  }
  
  /**
   * Set chord volume
   * @param {number} volume - Volume level (0-1)
   */
  function setChordVolume(volume) {
    if (chordPlayer) {
      chordPlayer.setVolume(volume);
    }
  }
  
  /**
   * Handle keyboard shortcuts
   * @param {KeyboardEvent} event
   */
  function handleKeydown(event) {
    if (!browser) return;
    
    // Number keys 1-2: Arm corresponding track
    if (event.key === '1' && currentTracks.length >= 1) {
      event.preventDefault();
      armTrack(currentTracks[0].id);
    } else if (event.key === '2' && currentTracks.length >= 2) {
      event.preventDefault();
      armTrack(currentTracks[1].id);
    }
  }
</script>

<!-- Track List Container -->
<div class="flex flex-col h-full">
  <!-- Track List Header -->
  <div class="flex items-center justify-between mb-4">
    <div class="flex items-center space-x-2">
      <h3 class="text-sm font-medium">Tracks ({currentTracks.length})</h3>
      {#if currentTracks.some(t => t.isSolo)}
        <span class="px-2 py-1 bg-yellow-600 text-white text-xs rounded">SOLO</span>
      {/if}
      {#if currentAudioState?.isRecording}
        <span class="px-2 py-1 bg-red-600 text-white text-xs rounded animate-pulse">
          RECORDING
        </span>
      {/if}
    </div>
    
    <!-- Recording Status and Quantization Control -->
    <div class="flex items-center space-x-3">
      <div class="text-xs text-gray-400">
        {#if currentTracks.find(t => t.isArmed)}
          Armed: {currentTracks.find(t => t.isArmed)?.name}
        {:else}
          No track armed
        {/if}
      </div>
      
      <!-- Quantization Toggle -->
      <button 
        class="text-xs px-2 py-1 rounded {midiRecorder?.getStatus().quantizeEnabled ? 'bg-blue-600 text-white' : 'bg-gray-600 text-gray-300'}"
        on:click={() => midiRecorder?.setQuantizeEnabled(!midiRecorder?.getStatus().quantizeEnabled)}
        title="Toggle quantization (snap to beat grid)"
      >
        QUANT: {midiRecorder?.getStatus().quantizeEnabled ? 'ON' : 'OFF'}
      </button>
      
      <!-- Test Note Button -->
      <button 
        class="text-xs px-2 py-1 rounded bg-green-600 text-white hover:bg-green-700"
        on:click={addTestNote}
        title="Add a test note to armed track"
      >
        TEST NOTE
      </button>
      
      <!-- Chord Volume Control -->
      <div class="flex items-center space-x-2">
        <span class="text-xs text-gray-400">Chords:</span>
        <input 
          type="range" 
          min="0" 
          max="1" 
          step="0.1" 
          value={chordPlayer?.getVolume() || 0.5}
          on:input={(e) => setChordVolume(parseFloat(e.target.value))}
          class="w-16 h-2 bg-gray-600 rounded-lg appearance-none cursor-pointer"
          title="Chord volume"
        />
        <span class="text-xs text-gray-400 w-8">{Math.round((chordPlayer?.getVolume() || 0.5) * 100)}%</span>
      </div>
    </div>
  </div>
  
  <!-- Tracks -->
  <div 
    class="flex-1 space-y-2 overflow-y-auto" 
    bind:this={trackListContainer}
    style="height: {currentUIState?.trackHeight || 60}px"
  >
    {#each currentTracks as track (track.id)}
      <Track
        {track}
        isActive={currentUIState?.activeTrack === track.id}
        isRecording={currentAudioState?.isRecording && track.isArmed}
        recordingLevel={getTrackRecordingLevel(track.id)}
        hasEvents={trackHasEvents(track)}
        eventCount={getTrackEventCount(track)}
        on:arm={() => armTrack(track.id)}
        on:mute={() => toggleMute(track.id)}
        on:solo={() => toggleSolo(track.id)}
        on:volumeChange={(e) => setTrackVolume(track.id, e.detail)}
        on:instrumentChange={(e) => setTrackInstrument(track.id, e.detail)}
        on:nameChange={(e) => updateTrackProperty(track.id, 'name', e.detail)}
        on:clear={() => clearTrackEvents(track.id)}
        on:select={() => uiState.setActiveTrack(track.id)}
      />
    {/each}
  </div>
  
  <!-- Track List Footer -->
  <div class="mt-4 pt-2 border-t border-gray-700">
    <div class="flex items-center justify-between text-xs text-gray-400">
      <div>
        Armed: {currentTracks.filter(t => t.isArmed).length} | 
        Solo: {currentTracks.filter(t => t.isSolo).length} | 
        Muted: {currentTracks.filter(t => t.isMuted).length}
      </div>
      <div>
        Notes: {currentTracks.reduce((sum, t) => sum + getTrackEventCount(t), 0)}
      </div>
    </div>
    
    {#if !currentTracks.some(t => t.isArmed)}
      <div class="text-xs text-yellow-400 mt-1 text-center italic">
        Press 1 or 2 to arm a track for recording
      </div>
    {:else if currentAudioState?.isRecording}
      <div class="text-xs text-red-400 mt-1 text-center italic animate-pulse">
        Recording to {currentTracks.find(t => t.isArmed)?.name} - play notes on keyboard
      </div>
    {:else}
      <div class="text-xs text-green-400 mt-1 text-center italic">
        {currentTracks.find(t => t.isArmed)?.name} armed - click Record then Play to start
      </div>
    {/if}
  </div>
</div>



<style>
  /* Custom scrollbar for track list */
  .space-y-2::-webkit-scrollbar {
    width: 6px;
  }
  
  .space-y-2::-webkit-scrollbar-track {
    background: #374151;
    border-radius: 3px;
  }
  
  .space-y-2::-webkit-scrollbar-thumb {
    background: #6b7280;
    border-radius: 3px;
  }
  
  .space-y-2::-webkit-scrollbar-thumb:hover {
    background: #9ca3af;
  }
  
  /* Smooth transitions for track states */
  .track-container {
    transition: all 0.2s ease-in-out;
  }
  
  .track-container:hover {
    transform: translateY(-1px);
  }
  
  /* Focus styles for accessibility */
  button:focus-visible {
    outline: 2px solid #3b82f6;
    outline-offset: 2px;
      }
  </style> 
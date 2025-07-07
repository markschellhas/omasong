<script>
  import { onMount, onDestroy } from 'svelte';
  import { browser } from '$app/environment';
  import { Plus, Volume2, Headphones, Mic, Square, Trash2 } from 'lucide-svelte';
  import { tracks, TRACK_COLORS, INSTRUMENTS } from '../../stores/tracks.js';
  import { audioState } from '../../stores/audio.js';
  import { uiState } from '../../stores/ui.js';
  import { getAudioEngine, getMidiRecorder, getMidiPlayer } from '../../utils/index.js';
  import Track from './Track.svelte';
  
  /** @type {import('../../utils/audioEngine.js').AudioEngine} */
  let audioEngine;
  
  /** @type {import('../../utils/midiRecorder.js').MidiRecorder} */
  let midiRecorder;
  
  /** @type {import('../../utils/midiPlayer.js').MidiPlayer} */
  let midiPlayer;
  
  /** @type {import('../../stores/tracks.js').Track[]} */
  let currentTracks = [];
  
  /** @type {import('../../stores/audio.js').AudioState} */
  let currentAudioState;
  
  /** @type {import('../../stores/ui.js').UIState} */
  let currentUIState;
  
  /** @type {HTMLDivElement} */
  let trackListContainer;
  
  /** @type {boolean} */
  let showAddTrackOptions = false;
  
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
    
    // Handle recording state changes
    if (state.isRecording && !midiRecorder?.getStatus().isRecording) {
      startRecordingOnArmedTrack();
    } else if (!state.isRecording && midiRecorder?.getStatus().isRecording) {
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
    
    // Initialize with default tracks if none exist
    if (currentTracks.length === 0) {
      tracks.initializeDefault();
    }
    
    // Set up event listeners for recording and playback
    setupEventListeners();
    
    // Add keyboard event listeners
    document.addEventListener('keydown', handleKeydown);
  });
  
  onDestroy(() => {
    unsubscribeTracks();
    unsubscribeAudio();
    unsubscribeUI();
    
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
   * Add a new track
   * @param {string} [name] - Optional track name
   * @param {string} [instrument] - Optional instrument type
   */
  function addTrack(name = null, instrument = 'synth') {
    const trackName = name || `Track ${currentTracks.length + 1}`;
    tracks.add(trackName);
    
    // Set instrument for the new track
    const newTracks = [...currentTracks];
    const lastTrack = newTracks[newTracks.length - 1];
    if (lastTrack) {
      tracks.setInstrument(lastTrack.id, instrument);
    }
    
    showAddTrackOptions = false;
  }
  
  /**
   * Remove a track
   * @param {string} trackId - Track ID to remove
   */
  function removeTrack(trackId) {
    if (currentTracks.length <= 1) {
      alert('Cannot remove the last track');
      return;
    }
    
    if (confirm('Are you sure you want to remove this track?')) {
      tracks.remove(trackId);
    }
  }
  
  /**
   * Duplicate a track
   * @param {string} trackId - Track ID to duplicate
   */
  function duplicateTrack(trackId) {
    tracks.duplicate(trackId);
  }
  
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
   * Set track pan
   * @param {string} trackId - Track ID
   * @param {number} pan - Pan position (-1 to 1)
   */
  function setTrackPan(trackId, pan) {
    tracks.setPan(trackId, pan);
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
   * Handle keyboard shortcuts
   * @param {KeyboardEvent} event
   */
  function handleKeydown(event) {
    if (!browser) return;
    
    // Cmd/Ctrl + T: Add new track
    if ((event.metaKey || event.ctrlKey) && event.key === 't') {
      event.preventDefault();
      addTrack();
    }
    
    // Cmd/Ctrl + D: Duplicate active track
    if ((event.metaKey || event.ctrlKey) && event.key === 'd' && currentUIState?.activeTrack) {
      event.preventDefault();
      duplicateTrack(currentUIState.activeTrack);
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
    </div>
    
    <!-- Add Track Button -->
    <div class="relative">
      <button 
        class="bg-primary-600 hover:bg-primary-700 text-white p-2 rounded transition-colors duration-200"
        on:click={() => showAddTrackOptions = !showAddTrackOptions}
        title="Add Track (Cmd+T)"
      >
        <Plus class="w-4 h-4" />
      </button>
      
      <!-- Add Track Options -->
      {#if showAddTrackOptions}
        <div class="absolute right-0 top-full mt-1 bg-gray-800 border border-gray-600 rounded-lg shadow-lg z-30 min-w-48">
          <div class="p-2">
            <div class="text-xs text-gray-400 mb-2">Add Track:</div>
            {#each INSTRUMENTS as instrument}
              <button 
                class="w-full text-left px-3 py-2 text-sm hover:bg-gray-700 rounded capitalize"
                on:click={() => addTrack(null, instrument)}
              >
                {instrument}
              </button>
            {/each}
          </div>
        </div>
      {/if}
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
        on:panChange={(e) => setTrackPan(track.id, e.detail)}
        on:instrumentChange={(e) => setTrackInstrument(track.id, e.detail)}
        on:nameChange={(e) => updateTrackProperty(track.id, 'name', e.detail)}
        on:remove={() => removeTrack(track.id)}
        on:duplicate={() => duplicateTrack(track.id)}
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
        Events: {currentTracks.reduce((sum, t) => sum + getTrackEventCount(t), 0)}
      </div>
    </div>
  </div>
</div>

<!-- Click outside to close add track options -->
{#if showAddTrackOptions}
  <div 
    class="fixed inset-0 z-20" 
    on:click={() => showAddTrackOptions = false}
    role="button"
    tabindex="0"
    aria-label="Close menu"
  ></div>
{/if}

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
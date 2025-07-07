<script>
  import { createEventDispatcher } from 'svelte';
  import { browser } from '$app/environment';
  import { 
    Mic, MicOff, Volume2, VolumeX, Headphones, 
    MoreVertical, Trash2, Copy, RotateCcw 
  } from 'lucide-svelte';
  import { TRACK_COLORS, INSTRUMENTS } from '../../stores/tracks.js';
  
  const dispatch = createEventDispatcher();
  
  /** @type {import('../../stores/tracks.js').Track} */
  export let track;
  
  /** @type {boolean} */
  export let isActive = false;
  
  /** @type {boolean} */
  export let isRecording = false;
  
  /** @type {number} */
  export let recordingLevel = 0;
  
  /** @type {boolean} */
  export let hasEvents = false;
  
  /** @type {number} */
  export let eventCount = 0;
  
  /** @type {boolean} */
  let showOptionsMenu = false;
  
  /** @type {boolean} */
  let isEditingName = false;
  
  /** @type {string} */
  let editingName = track.name;
  
  /** @type {HTMLInputElement} */
  let nameInput;
  
  /**
   * Handle arm button click
   */
  function handleArm() {
    dispatch('arm');
  }
  
  /**
   * Handle mute button click
   */
  function handleMute() {
    dispatch('mute');
  }
  
  /**
   * Handle solo button click
   */
  function handleSolo() {
    dispatch('solo');
  }
  
  /**
   * Handle volume change
   * @param {Event} event
   */
  function handleVolumeChange(event) {
    const volume = parseFloat(event.target.value);
    dispatch('volumeChange', volume);
  }
  
  /**
   * Handle pan change
   * @param {Event} event
   */
  function handlePanChange(event) {
    const pan = parseFloat(event.target.value);
    dispatch('panChange', pan);
  }
  
  /**
   * Handle instrument change
   * @param {Event} event
   */
  function handleInstrumentChange(event) {
    const instrument = event.target.value;
    dispatch('instrumentChange', instrument);
  }
  
  /**
   * Start editing track name
   */
  function startEditingName() {
    isEditingName = true;
    editingName = track.name;
    
    // Focus input after render
    setTimeout(() => {
      if (nameInput) {
        nameInput.focus();
        nameInput.select();
      }
    }, 0);
  }
  
  /**
   * Save edited name
   */
  function saveEditingName() {
    if (editingName.trim() && editingName !== track.name) {
      dispatch('nameChange', editingName.trim());
    }
    isEditingName = false;
  }
  
  /**
   * Cancel editing name
   */
  function cancelEditingName() {
    editingName = track.name;
    isEditingName = false;
  }
  
  /**
   * Handle name input key events
   * @param {KeyboardEvent} event
   */
  function handleNameKeydown(event) {
    if (event.key === 'Enter') {
      event.preventDefault();
      saveEditingName();
    } else if (event.key === 'Escape') {
      event.preventDefault();
      cancelEditingName();
    }
  }
  
  /**
   * Handle track selection
   */
  function handleSelect() {
    dispatch('select');
  }
  
  /**
   * Handle remove track
   */
  function handleRemove() {
    dispatch('remove');
    showOptionsMenu = false;
  }
  
  /**
   * Handle duplicate track
   */
  function handleDuplicate() {
    dispatch('duplicate');
    showOptionsMenu = false;
  }
  
  /**
   * Handle clear track events
   */
  function handleClear() {
    dispatch('clear');
    showOptionsMenu = false;
  }
  
  /**
   * Get track color class based on color
   * @returns {string} CSS class
   */
  function getTrackColorClass() {
    return `bg-${track.color}-500`;
  }
  
  /**
   * Get recording level bar width
   * @returns {number} Width percentage
   */
  function getRecordingLevelWidth() {
    return Math.min(100, recordingLevel * 100);
  }
  
  /**
   * Format pan value for display
   * @param {number} pan Pan value (-1 to 1)
   * @returns {string} Formatted pan
   */
  function formatPan(pan) {
    if (pan === 0) return 'C';
    if (pan < 0) return `L${Math.abs(pan * 100).toFixed(0)}`;
    return `R${(pan * 100).toFixed(0)}`;
  }
  
  /**
   * Get volume percentage for display
   * @param {number} volume Volume value (0-1)
   * @returns {number} Percentage
   */
  function getVolumePercentage(volume) {
    return Math.round(volume * 100);
  }
</script>

<!-- Track Container -->
<div 
  class="bg-gray-900 border border-gray-700 rounded-lg p-3 {isActive ? 'ring-2 ring-primary-500' : ''} {isRecording ? 'ring-2 ring-red-500' : ''}"
  on:click={handleSelect}
  role="button"
  tabindex="0"
  aria-label="Track {track.name}"
>
  <!-- Track Header Row -->
  <div class="flex items-center justify-between mb-2">
    <!-- Track Color and Name -->
    <div class="flex items-center space-x-2 flex-1">
      <!-- Color Indicator -->
      <div 
        class="w-3 h-3 rounded-full {getTrackColorClass()}"
        title="Track color: {track.color}"
      ></div>
      
      <!-- Track Name -->
      {#if isEditingName}
        <input 
          bind:this={nameInput}
          bind:value={editingName}
          on:blur={saveEditingName}
          on:keydown={handleNameKeydown}
          class="bg-gray-800 text-white text-sm px-2 py-1 rounded border border-gray-600 focus:border-primary-500 focus:outline-none flex-1"
          maxlength="30"
        />
      {:else}
        <button 
          class="text-sm font-medium text-white hover:text-primary-400 transition-colors duration-200 text-left flex-1"
          on:click|stopPropagation={startEditingName}
          title="Click to edit name"
        >
          {track.name}
        </button>
      {/if}
      
      <!-- Event Indicator -->
      {#if hasEvents}
        <span 
          class="text-xs px-2 py-1 bg-green-600 text-white rounded"
          title="{eventCount} recorded events"
        >
          {eventCount}
        </span>
      {/if}
    </div>
    
    <!-- Track Options -->
    <div class="relative">
      <button 
        class="p-1 hover:bg-gray-700 rounded transition-colors duration-200"
        on:click|stopPropagation={() => showOptionsMenu = !showOptionsMenu}
        title="Track options"
      >
        <MoreVertical class="w-4 h-4" />
      </button>
      
      <!-- Options Menu -->
      {#if showOptionsMenu}
        <div class="absolute right-0 top-full mt-1 bg-gray-800 border border-gray-600 rounded-lg shadow-lg z-30 min-w-32">
          <div class="p-1">
            <button 
              class="w-full text-left px-3 py-2 text-sm hover:bg-gray-700 rounded flex items-center space-x-2"
              on:click={handleDuplicate}
            >
              <Copy class="w-4 h-4" />
              <span>Duplicate</span>
            </button>
            
            {#if hasEvents}
              <button 
                class="w-full text-left px-3 py-2 text-sm hover:bg-gray-700 rounded flex items-center space-x-2 text-yellow-400"
                on:click={handleClear}
              >
                <RotateCcw class="w-4 h-4" />
                <span>Clear Events</span>
              </button>
            {/if}
            
            <button 
              class="w-full text-left px-3 py-2 text-sm hover:bg-gray-700 rounded flex items-center space-x-2 text-red-400"
              on:click={handleRemove}
            >
              <Trash2 class="w-4 h-4" />
              <span>Remove</span>
            </button>
          </div>
        </div>
      {/if}
    </div>
  </div>
  
  <!-- Control Buttons Row -->
  <div class="flex items-center space-x-2 mb-2">
    <!-- Arm Button -->
    <button 
      class="p-2 rounded {track.isArmed ? 'bg-red-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'} transition-colors duration-200"
      on:click|stopPropagation={handleArm}
      title={track.isArmed ? 'Disarm track' : 'Arm track for recording'}
    >
      {#if track.isArmed}
        <Mic class="w-4 h-4" />
      {:else}
        <MicOff class="w-4 h-4" />
      {/if}
    </button>
    
    <!-- Mute Button -->
    <button 
      class="p-2 rounded {track.isMuted ? 'bg-gray-600 text-yellow-400' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'} transition-colors duration-200"
      on:click|stopPropagation={handleMute}
      title={track.isMuted ? 'Unmute track' : 'Mute track'}
    >
      {#if track.isMuted}
        <VolumeX class="w-4 h-4" />
      {:else}
        <Volume2 class="w-4 h-4" />
      {/if}
    </button>
    
    <!-- Solo Button -->
    <button 
      class="p-2 rounded {track.isSolo ? 'bg-yellow-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'} transition-colors duration-200"
      on:click|stopPropagation={handleSolo}
      title={track.isSolo ? 'Unsolo track' : 'Solo track'}
    >
      <Headphones class="w-4 h-4" />
    </button>
    
    <!-- Instrument Selector -->
    <select 
      value={track.instrument}
      on:change={handleInstrumentChange}
      on:click|stopPropagation
      class="bg-gray-700 text-white text-sm px-2 py-1 rounded border border-gray-600 focus:border-primary-500 focus:outline-none capitalize"
      title="Track instrument"
    >
      {#each INSTRUMENTS as instrument}
        <option value={instrument} class="capitalize">{instrument}</option>
      {/each}
    </select>
  </div>
  
  <!-- Volume and Pan Controls -->
  <div class="grid grid-cols-2 gap-3">
    <!-- Volume Control -->
    <div class="space-y-1">
      <div class="flex items-center justify-between">
        <label class="text-xs text-gray-400">Volume</label>
        <span class="text-xs text-gray-400">{getVolumePercentage(track.volume)}%</span>
      </div>
      <input 
        type="range"
        min="0"
        max="1"
        step="0.01"
        value={track.volume}
        on:input={handleVolumeChange}
        on:click|stopPropagation
        class="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
        title="Track volume: {getVolumePercentage(track.volume)}%"
      />
    </div>
    
    <!-- Pan Control -->
    <div class="space-y-1">
      <div class="flex items-center justify-between">
        <label class="text-xs text-gray-400">Pan</label>
        <span class="text-xs text-gray-400">{formatPan(track.pan)}</span>
      </div>
      <input 
        type="range"
        min="-1"
        max="1"
        step="0.01"
        value={track.pan}
        on:input={handlePanChange}
        on:click|stopPropagation
        class="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
        title="Track pan: {formatPan(track.pan)}"
      />
    </div>
  </div>
  
  <!-- Recording Level Indicator -->
  {#if isRecording}
    <div class="mt-2">
      <div class="w-full bg-gray-700 rounded-full h-1">
        <div 
          class="bg-red-500 h-1 rounded-full transition-all duration-75"
          style="width: {getRecordingLevelWidth()}%"
        ></div>
      </div>
    </div>
  {/if}
</div>

<!-- Click outside to close options menu -->
{#if showOptionsMenu}
  <div 
    class="fixed inset-0 z-20" 
    on:click={() => showOptionsMenu = false}
    role="button"
    tabindex="0"
    aria-label="Close menu"
  ></div>
{/if}

<style>
  /* Custom slider styles */
  .slider::-webkit-slider-thumb {
    appearance: none;
    height: 16px;
    width: 16px;
    border-radius: 50%;
    background: #3b82f6;
    cursor: pointer;
    border: 2px solid #1f2937;
  }
  
  .slider::-webkit-slider-thumb:hover {
    background: #2563eb;
  }
  
  .slider::-moz-range-thumb {
    height: 16px;
    width: 16px;
    border-radius: 50%;
    background: #3b82f6;
    cursor: pointer;
    border: 2px solid #1f2937;
    box-sizing: border-box;
  }
  
  .slider::-moz-range-thumb:hover {
    background: #2563eb;
  }
  
  /* Track selection styles */
  .track-container:hover {
    border-color: #4b5563;
  }
  
  /* Recording animation */
  @keyframes recording-pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }
  
  .recording-indicator {
    animation: recording-pulse 1s ease-in-out infinite;
  }
  
  /* Focus styles for accessibility */
  button:focus-visible,
  input:focus-visible,
  select:focus-visible {
    outline: 2px solid #3b82f6;
    outline-offset: 2px;
  }
</style> 
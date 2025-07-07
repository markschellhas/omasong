<script>
  import { createEventDispatcher } from 'svelte';
  import { X } from 'lucide-svelte';
  
  const dispatch = createEventDispatcher();
  
  /** @type {number} */
  export let measure;
  
  /** @type {import('../../stores/chords.js').Chord|null} */
  export let chord = null;
  
  /** @type {boolean} */
  export let isActive = false;
  
  /** @type {boolean} */
  export let isEditing = false;
  
  // Debug chord prop
  $: {
    if (chord) {
      console.log(`🎵 ChordCell ${measure}: Received chord`, chord);
    }
  } 

  
  /**
   * Handle cell click
   */
  function handleClick() {
    dispatch('click');
  }
  
  /**
   * Handle clear chord
   * @param {Event} event
   */
  function handleClear(event) {
    event.stopPropagation();
    dispatch('clear');
  }
  
  /**
   * Get chord display text
   * @returns {string} Display text
   */
  function getChordDisplay() {
    if (!chord) return '';
    return chord.symbol;
  }
  
  /**
   * Get note names for tooltip
   * @returns {string} Note names
   */
  function getNoteNames() {
    if (!chord || !chord.noteNames) return '';
    return chord.noteNames.join(', ');
  }
  
  /**
   * Get cell background color based on state
   * @returns {string} CSS classes
   */
  function getCellClasses() {
    let classes = 'flex-1 h-8 border-2 rounded-lg cursor-pointer transition-all duration-200 relative group ';
    
    if (isActive) {
      classes += 'border-red-500 bg-red-500 bg-opacity-20 shadow-lg ';
    } else if (isEditing) {
      classes += 'border-primary-500 bg-primary-500 bg-opacity-20 ';
    } else if (chord) {
      classes += 'border-green-500 bg-green-500 bg-opacity-10 hover:bg-opacity-20 ';
    } else {
      classes += 'border-gray-600 bg-gray-700 bg-opacity-50 hover:bg-opacity-70 hover:border-gray-500 ';
    }
    
    return classes;
  }
</script>

<!-- Chord Cell -->
<div 
  class={getCellClasses()}
  on:click={handleClick}
  role="button"
  tabindex="0"
  title={chord ? `${chord.symbol} (${getNoteNames()})` : `Click to add chord to measure ${measure}`}
  aria-label={chord ? `Chord ${chord.symbol} in measure ${measure}` : `Empty measure ${measure}`}
>
  <!-- Measure Number -->
  <div class="absolute top-1 left-1 text-xs text-gray-400 font-mono">
    {measure}
  </div>
  
  <!-- Clear Button -->
  {#if chord}
    <button 
      class="absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200 bg-red-600 hover:bg-red-700 text-white rounded-full p-1"
      on:click={handleClear}
      title="Clear chord"
      aria-label="Clear chord from measure {measure}"
    >
      <X class="w-3 h-3" />
    </button>
  {/if}
  
  <!-- Chord Content -->
  <div class="flex-1 flex items-center justify-center p-2">
    {#if chord}
      <!-- Chord Symbol -->
      <div class="text-center">
        <div class="text-sm font-bold text-white">
          {getChordDisplay()}
        </div>
      </div>
    {:else}
      <!-- Empty Cell -->
      <div class="text-center">
        <div class="text-xs text-gray-500">Add Chord</div>
      </div>
    {/if}
  </div>
  
  <!-- Active Indicator -->
  {#if isActive}
    <div class="absolute inset-0 border-2 border-red-400 rounded-lg animate-pulse pointer-events-none"></div>
  {/if}
  
  <!-- Editing Indicator -->
  {#if isEditing}
    <div class="absolute inset-0 border-2 border-primary-400 rounded-lg pointer-events-none"></div>
  {/if}
</div>

<style>
  /* Smooth hover transitions */
  .chord-cell {
    transition: all 0.2s ease-in-out;
  }
  
  /* Active chord pulse animation */
  @keyframes chord-pulse {
    0%, 100% { 
      box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7);
    }
    50% { 
      box-shadow: 0 0 0 8px rgba(239, 68, 68, 0);
    }
  }
  
  .chord-active {
    animation: chord-pulse 2s infinite;
  }
  
  /* Hover lift effect */
  .chord-cell:hover {
    transform: translateY(-2px);
  }
  
  /* Focus styles for accessibility */
  .chord-cell:focus-visible {
    outline: 2px solid #3b82f6;
    outline-offset: 2px;
  }
  
  /* Group hover effects for clear button */
  .group:hover .group-hover\:opacity-100 {
    opacity: 1;
  }
</style> 
<script>
  import { onMount, onDestroy } from 'svelte';
  import { browser } from '$app/environment';
  import { audioState } from '../../stores/audio.js';
  import { uiState } from '../../stores/ui.js';
  import { getAudioEngine } from '../../utils/audioEngine.js';
  
  /** @type {import('../../utils/audioEngine.js').AudioEngine} */
  let audioEngine;
  
  /** @type {import('../../stores/audio.js').AudioState} */
  let currentAudioState;
  
  /** @type {import('../../stores/ui.js').UIState} */
  let currentUIState;
  
  /** @type {HTMLDivElement} */
  let timelineContainer;
  
  /** @type {HTMLDivElement} */
  let playheadElement;
  
  /** @type {boolean} */
  let isDragging = false;
  
  /** @type {number} */
  let dragStartX = 0;
  
  /** @type {number} */
  let dragStartPosition = 0;
  
  /** @type {number} */
  let timelineWidth = 0;
  
  /** @type {number} */
  let playheadPosition = 0; // in pixels
  
  // Timeline settings
  const BEATS_PER_MEASURE = 4;
  const MEASURES_VISIBLE = 16;
  const TOTAL_BEATS = BEATS_PER_MEASURE * MEASURES_VISIBLE;
  
  // Subscribe to stores
  const unsubscribeAudio = audioState.subscribe(state => {
    currentAudioState = state;
    updatePlayheadPosition();
  });
  
  const unsubscribeUI = uiState.subscribe(state => {
    currentUIState = state;
  });
  
  onMount(() => {
    if (!browser) return;
    
    audioEngine = getAudioEngine();
    
    // Set up resize observer for timeline container
    const resizeObserver = new ResizeObserver(entries => {
      for (const entry of entries) {
        timelineWidth = entry.contentRect.width;
        updatePlayheadPosition();
      }
    });
    
    if (timelineContainer) {
      resizeObserver.observe(timelineContainer);
    }
    
    // Add global mouse event listeners for dragging
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    document.addEventListener('touchmove', handleTouchMove, { passive: false });
    document.addEventListener('touchend', handleTouchEnd);
    
    return () => {
      resizeObserver.disconnect();
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.removeEventListener('touchmove', handleTouchMove);
      document.removeEventListener('touchend', handleTouchEnd);
    };
  });
  
  onDestroy(() => {
    unsubscribeAudio();
    unsubscribeUI();
  });
  
  /**
   * Update playhead position based on audio state
   */
  function updatePlayheadPosition() {
    if (!timelineWidth || !currentAudioState) return;
    
    const positionInBeats = currentAudioState.playheadPosition;
    const percentage = positionInBeats / TOTAL_BEATS;
    playheadPosition = percentage * timelineWidth;
  }
  
  /**
   * Convert pixel position to beats
   * @param {number} pixelX - X position in pixels
   * @returns {number} Position in beats
   */
  function pixelsToBeats(pixelX) {
    if (!timelineWidth) return 0;
    const percentage = Math.max(0, Math.min(1, pixelX / timelineWidth));
    return percentage * TOTAL_BEATS;
  }
  
  /**
   * Convert beats to pixel position
   * @param {number} beats - Position in beats
   * @returns {number} Position in pixels
   */
  function beatsToPixels(beats) {
    if (!timelineWidth) return 0;
    const percentage = beats / TOTAL_BEATS;
    return percentage * timelineWidth;
  }
  
  /**
   * Snap position to grid (beat boundaries)
   * @param {number} beats - Position in beats
   * @returns {number} Snapped position in beats
   */
  function snapToGrid(beats) {
    const subdivision = currentUIState?.zoomLevel >= 2 ? 0.25 : 1; // 16th notes or beats
    return Math.round(beats / subdivision) * subdivision;
  }
  
  /**
   * Handle mouse down on playhead
   * @param {MouseEvent} event
   */
  function handlePlayheadMouseDown(event) {
    if (!browser) return;
    event.preventDefault();
    event.stopPropagation();
    
    isDragging = true;
    dragStartX = event.clientX;
    dragStartPosition = currentAudioState.playheadPosition;
    
    // Add dragging class for visual feedback
    if (playheadElement) {
      playheadElement.classList.add('dragging');
    }
  }
  
  /**
   * Handle touch start on playhead
   * @param {TouchEvent} event
   */
  function handlePlayheadTouchStart(event) {
    if (!browser) return;
    event.preventDefault();
    event.stopPropagation();
    
    const touch = event.touches[0];
    isDragging = true;
    dragStartX = touch.clientX;
    dragStartPosition = currentAudioState.playheadPosition;
    
    if (playheadElement) {
      playheadElement.classList.add('dragging');
    }
  }
  
  /**
   * Handle mouse move during drag
   * @param {MouseEvent} event
   */
  function handleMouseMove(event) {
    if (!isDragging) return;
    event.preventDefault();
    
    const deltaX = event.clientX - dragStartX;
    const deltaBeats = pixelsToBeats(deltaX);
    const newPosition = Math.max(0, dragStartPosition + deltaBeats);
    const snappedPosition = snapToGrid(newPosition);
    
    // Update audio engine position if initialized
    if (audioEngine && audioEngine.isInitialized()) {
      audioEngine.seek(snappedPosition);
    } else {
      // Update store directly if audio engine not ready
      audioState.seek(snappedPosition);
    }
  }
  
  /**
   * Handle touch move during drag
   * @param {TouchEvent} event
   */
  function handleTouchMove(event) {
    if (!isDragging) return;
    event.preventDefault();
    
    const touch = event.touches[0];
    const deltaX = touch.clientX - dragStartX;
    const deltaBeats = pixelsToBeats(deltaX);
    const newPosition = Math.max(0, dragStartPosition + deltaBeats);
    const snappedPosition = snapToGrid(newPosition);
    
    if (audioEngine && audioEngine.isInitialized()) {
      audioEngine.seek(snappedPosition);
    } else {
      audioState.seek(snappedPosition);
    }
  }
  
  /**
   * Handle mouse up (end drag)
   * @param {MouseEvent} event
   */
  function handleMouseUp(event) {
    if (!isDragging) return;
    
    isDragging = false;
    
    if (playheadElement) {
      playheadElement.classList.remove('dragging');
    }
  }
  
  /**
   * Handle touch end (end drag)
   * @param {TouchEvent} event
   */
  function handleTouchEnd(event) {
    if (!isDragging) return;
    
    isDragging = false;
    
    if (playheadElement) {
      playheadElement.classList.remove('dragging');
    }
  }
  
  /**
   * Handle click on timeline (seek to position)
   * @param {MouseEvent} event
   */
  function handleTimelineClick(event) {
    if (!browser || isDragging) return;
    
    const rect = timelineContainer.getBoundingClientRect();
    const clickX = event.clientX - rect.left;
    const clickPosition = pixelsToBeats(clickX);
    const snappedPosition = snapToGrid(clickPosition);
    
    if (audioEngine && audioEngine.isInitialized()) {
      audioEngine.seek(snappedPosition);
    } else {
      audioState.seek(snappedPosition);
    }
  }
  
  /**
   * Handle touch on timeline (seek to position)
   * @param {TouchEvent} event
   */
  function handleTimelineTouch(event) {
    if (!browser || isDragging) return;
    event.preventDefault();
    
    const touch = event.touches[0];
    const rect = timelineContainer.getBoundingClientRect();
    const touchX = touch.clientX - rect.left;
    const touchPosition = pixelsToBeats(touchX);
    const snappedPosition = snapToGrid(touchPosition);
    
    if (audioEngine && audioEngine.isInitialized()) {
      audioEngine.seek(snappedPosition);
    } else {
      audioState.seek(snappedPosition);
    }
  }
  
  /**
   * Get current time display
   * @returns {string} Formatted time
   */
  function getTimeDisplay() {
    const positionInBeats = currentAudioState?.playheadPosition || 0;
    const bars = Math.floor(positionInBeats / BEATS_PER_MEASURE) + 1;
    const beats = Math.floor(positionInBeats % BEATS_PER_MEASURE) + 1;
    const sixteenths = Math.floor((positionInBeats % 1) * 4) + 1;
    
    return `${bars}:${beats}:${sixteenths}`;
  }
  
  /**
   * Generate timeline markers
   * @returns {Array} Array of marker objects
   */
  function getTimelineMarkers() {
    const markers = [];
    
    for (let measure = 0; measure < MEASURES_VISIBLE; measure++) {
      for (let beat = 0; beat < BEATS_PER_MEASURE; beat++) {
        const positionInBeats = measure * BEATS_PER_MEASURE + beat;
        const percentage = (positionInBeats / TOTAL_BEATS) * 100;
        
        markers.push({
          position: percentage,
          isMeasureStart: beat === 0,
          label: beat === 0 ? `${measure + 1}` : null,
          positionInBeats
        });
      }
    }
    
    return markers;
  }
  
  $: timelineMarkers = getTimelineMarkers();
  $: isVisible = currentAudioState?.playheadPosition !== undefined;
</script>

<!-- Time Indicator Container -->
<div class="absolute inset-0 pointer-events-none z-20">
  <!-- Timeline Background (in tracks area) -->
  <div 
    class="absolute left-0 right-0 h-full bg-transparent pointer-events-auto cursor-pointer"
    bind:this={timelineContainer}
    on:click={handleTimelineClick}
    on:touchstart={handleTimelineTouch}
    role="slider"
    tabindex="0"
    aria-label="Timeline scrubber"
    aria-valuemin="0"
    aria-valuemax={TOTAL_BEATS}
    aria-valuenow={currentAudioState?.playheadPosition || 0}
  >
    <!-- Timeline Markers -->
    {#each timelineMarkers as marker}
      <div 
        class="absolute top-0 bottom-0 {marker.isMeasureStart ? 'w-0.5 bg-gray-600' : 'w-px bg-gray-700'}"
        style="left: {marker.position}%"
      >
        {#if marker.label}
          <div class="absolute -top-5 -left-2 text-xs text-gray-400 font-mono">
            {marker.label}
          </div>
        {/if}
      </div>
    {/each}
    
    <!-- Playhead Line -->
    {#if isVisible}
      <div 
        class="absolute top-0 bottom-0 w-0.5 bg-red-500 transition-all duration-75 pointer-events-auto z-30 {isDragging ? 'bg-red-400' : ''}"
        style="left: {playheadPosition}px; transform: translateX(-1px)"
        bind:this={playheadElement}
      >
        <!-- Playhead Handle -->
        <div 
          class="absolute -top-1 -left-2 w-4 h-4 cursor-grab hover:cursor-grabbing select-none {isDragging ? 'cursor-grabbing' : ''}"
          on:mousedown={handlePlayheadMouseDown}
          on:touchstart={handlePlayheadTouchStart}
          role="button"
          tabindex="0"
          aria-label="Playhead handle"
        >
          <!-- Triangle Handle -->
          <div class="w-0 h-0 border-l-2 border-r-2 border-b-4 border-transparent border-b-red-500 {isDragging ? 'border-b-red-400' : ''}"></div>
        </div>
        
        <!-- Position Label -->
        {#if isDragging || currentAudioState?.isPlaying}
          <div 
            class="absolute -top-8 -left-8 bg-gray-900 text-white text-xs px-2 py-1 rounded shadow-lg border border-gray-600 whitespace-nowrap font-mono"
          >
            {getTimeDisplay()}
          </div>
        {/if}
      </div>
    {/if}
  </div>
</div>

<style>
  /* Ensure smooth transitions */
  .playhead-line {
    transition: left 0.075s ease-out;
  }
  
  /* Dragging state styles */
  .dragging {
    transition: none !important;
  }
  
  /* Make the timeline markers more subtle */
  .timeline-marker {
    opacity: 0.6;
  }
  
  .timeline-marker:hover {
    opacity: 1;
  }
  
  /* Ensure proper z-index stacking */
  .playhead-container {
    z-index: 100;
  }
  
  /* Touch-friendly handle for mobile */
  @media (hover: none) {
    .playhead-handle {
      width: 2rem;
      height: 2rem;
      top: -0.5rem;
      left: -1rem;
    }
  }
</style> 
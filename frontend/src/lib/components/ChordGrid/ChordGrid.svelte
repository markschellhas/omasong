<script>
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';
  import { createEventDispatcher } from 'svelte';
  import { Grid3X3 } from 'lucide-svelte';
  import { chords } from '../../stores/chords.js';
  import { audioState } from '../../stores/audio.js';
  import { uiState } from '../../stores/ui.js';
  import { parseChord, getChordSuggestions } from '../../utils/chordParser.js';
  import { getMidiPlayer, getAudioEngine, getChordPlayer } from '../../utils/index.js';
  import ChordCell from './ChordCell.svelte';
  
  const dispatch = createEventDispatcher();
  
  // Remove the manual variable and use the store directly
  
  /** @type {import('../../stores/audio.js').AudioState} */
  let currentAudioState;
  
  /** @type {import('../../stores/ui.js').UIState} */
  let currentUIState;
  
  /** @type {import('../../utils/midiPlayer.js').MidiPlayer} */
  let midiPlayer;
  
  /** @type {import('../../utils/audioEngine.js').AudioEngine} */
  let audioEngine;
  
  /** @type {import('../../utils/chordPlayer.js').default} */
  let chordPlayer;
  
  /** @type {number} */
  let activeChordIndex = -1;
  
  /** @type {boolean} */
  let isPlaying = false;
  
  /** @type {boolean} */
  let showChordSuggestions = false;
  
  /** @type {string[]} */
  let chordSuggestions = [];
  
  /** @type {number} */
  let editingCellIndex = -1;
  
  /** @type {HTMLInputElement} */
  let chordInput;
  
  /** @type {string} */
  let currentChordInput = '';
  
  // Grid layout settings
  const MEASURES_PER_ROW = 4;
  const TOTAL_MEASURES = 16;
  
  // Use reactive statements instead of manual subscriptions
  $: {
    currentAudioState = $audioState;
    isPlaying = $audioState.isPlaying;
    
    // Update active chord based on playhead position
    if ($audioState.isPlaying && $audioState.playheadPosition !== undefined) {
      const measurePosition = $audioState.playheadPosition / 4; // Convert beats to measures
      const currentMeasure = Math.floor(measurePosition);
      activeChordIndex = Math.min(currentMeasure, TOTAL_MEASURES - 1);
    } else if (!$audioState.isPlaying) {
      activeChordIndex = -1;
    }
  }
  
  $: currentUIState = $uiState;
  
  onMount(() => {
    if (!browser) return;
    
    audioEngine = getAudioEngine();
    midiPlayer = getMidiPlayer(audioEngine);
    chordPlayer = getChordPlayer(); // Use singleton instance
    
    // Initialize progression if empty
    if ($chords.length === 0) {
      chords.initializeDefault();
    }
  });
  
  // No need for onDestroy with reactive statements
  
  /**
   * Handle chord cell click
   * @param {number} index - Cell index
   */
  function handleChordClick(index) {
    editingCellIndex = index;
    showChordSuggestions = false;
    
    // Initialize input with existing chord value
    const existingChord = getChordForMeasure(index);
    currentChordInput = existingChord?.symbol || '';
    
    console.log('🎹 ChordGrid: Opening chord editor', { 
      index, 
      existingChord, 
      currentChordInput 
    });
    
    // Focus input after render
    setTimeout(() => {
      if (chordInput) {
        chordInput.focus();
        chordInput.select();
      }
    }, 0);
  }
  
  /**
   * Handle chord input change
   * @param {Event} event
   */
  function handleChordInput(event) {
    // Show suggestions if value is not empty
    if (currentChordInput.trim()) {
      chordSuggestions = getChordSuggestions(currentChordInput);
      showChordSuggestions = chordSuggestions.length > 0;
    } else {
      showChordSuggestions = false;
    }
  }
  
  /**
   * Handle chord input submission
   * @param {Event} event
   */
  function handleChordSubmit(event) {
    event.preventDefault();
    
    // Use the bound value
    const value = currentChordInput.trim();
    
    console.log('🎹 ChordGrid: Submitting chord', { 
      editingCellIndex, 
      value, 
      currentChordInput
    });
    
    if (editingCellIndex >= 0) {
      if (value === '') {
        // Clear chord
        console.log('🎹 ChordGrid: Clearing chord at measure', editingCellIndex);
        chords.setChord(editingCellIndex, null);
      } else {
        // Parse and validate chord
        const parsed = parseChord(value);
        console.log('🎹 ChordGrid: Parsed chord', { value, parsed });
        
        if (parsed.isValid && parsed.chord) {
          const chordData = {
            symbol: value,
            measure: editingCellIndex,
            beat: 0,
            duration: 4,
            notes: parsed.chord.notes || [],
            noteNames: parsed.chord.noteNames || []
          };
          console.log('🎹 ChordGrid: Setting chord data', chordData);
          chords.setChord(editingCellIndex, chordData);
        } else {
          alert(`Invalid chord: ${parsed.error || 'Unknown error'}`);
          return;
        }
      }
    }
    
    cancelEditing();
  }
  
  /**
   * Handle suggestion click
   * @param {string} suggestion
   */
  function handleSuggestionClick(suggestion) {
    if (editingCellIndex >= 0) {
      currentChordInput = suggestion;
      handleChordSubmit({ preventDefault: () => {} });
    }
  }
  
  /**
   * Cancel chord editing
   */
  function cancelEditing() {
    editingCellIndex = -1;
    showChordSuggestions = false;
  }
  

  
  /**
   * Handle key events for chord input
   * @param {KeyboardEvent} event
   */
  function handleChordKeydown(event) {
    if (event.key === 'Escape') {
      event.preventDefault();
      cancelEditing();
    } else if (event.key === 'Tab') {
      event.preventDefault();
      
      // Move to next cell
      const nextIndex = editingCellIndex + (event.shiftKey ? -1 : 1);
      if (nextIndex >= 0 && nextIndex < TOTAL_MEASURES) {
        handleChordClick(nextIndex);
      } else {
        cancelEditing();
      }
    }
  }
  
  /**
   * Play chord progression
   */
  function playProgression() {
    if (!audioEngine || !audioEngine.isInitialized()) {
      alert('Please click anywhere to initialize audio first');
      return;
    }
    
    console.log('🎹 ChordGrid: Starting chord progression playback');
    audioState.play();
  }
  
  /**
   * Stop chord progression
   */
  function stopProgression() {
    audioState.stop();
  }
  

  
  /**
   * Get chord for measure
   * @param {number} measure
   * @returns {import('../../stores/chords.js').Chord|null}
   */
  function getChordForMeasure(measure) {
    const chord = $chords.find(chord => chord.measure === measure) || null;
    console.log('🎹 ChordGrid: getChordForMeasure', { 
      measure, 
      chord, 
      progressionLength: $chords.length,
      allMeasures: $chords.map(c => c.measure)
    });
    return chord;
  }
  
  /**
   * Generate grid rows
   * @returns {number[][]} Array of row arrays with measure indices
   */
  function generateGridRows() {
    const rows = [];
    for (let i = 0; i < TOTAL_MEASURES; i += MEASURES_PER_ROW) {
      const row = [];
      for (let j = 0; j < MEASURES_PER_ROW && i + j < TOTAL_MEASURES; j++) {
        row.push(i + j);
      }
      rows.push(row);
    }
    return rows;
  }
  
  $: gridRows = generateGridRows();
  
  // Debug reactive statement for chord progression
  $: {
    console.log('🎹 ChordGrid: Reactive chords update', {
      length: $chords.length,
      chords: $chords.map(c => ({measure: c.measure, symbol: c.symbol}))
    });
  }
</script>

<!-- Chord Grid Container -->
<div class="flex flex-col h-full">
  <!-- Chord Grid Header -->
  <div class="flex items-center justify-between mb-4">
    <div class="flex items-center space-x-2">
      <Grid3X3 class="w-5 h-5 text-primary-400" />
      <h3 class="text-lg font-semibold">Chord Progression</h3>
    </div>
    
  </div>
  

  
  <!-- Chord Grid -->
  <div class="flex-1 bg-gray-800 rounded-lg p-4">
    {#each gridRows as row, rowIndex}
      <div class="flex mb-3 last:mb-0">
        <!-- Row Label -->
        <div class="w-8 flex items-center justify-center text-sm text-gray-400 mr-3">
          {rowIndex * MEASURES_PER_ROW + 1}-{Math.min((rowIndex + 1) * MEASURES_PER_ROW, TOTAL_MEASURES)}
        </div>
        
                <!-- Chord Cells -->
        <div class="flex space-x-2 flex-1">
          {#each row as measureIndex}
            {@const chordForMeasure = $chords.find(c => c.measure === measureIndex)}
            {@const debugInfo = { measureIndex, chordForMeasure, allChords: $chords.map(c => `${c.measure}:${c.symbol}`) }}
            {#if measureIndex === 0}
              {console.log('🎹 ChordGrid: Cell 0 debug', debugInfo)}
            {/if}
            <ChordCell
              measure={measureIndex + 1}
              chord={chordForMeasure}
              isActive={activeChordIndex === measureIndex}
              isEditing={editingCellIndex === measureIndex}
              on:click={() => handleChordClick(measureIndex)}
              on:clear={() => chords.setChord(measureIndex, null)}
            />
          {/each}
        </div>
      </div>
    {/each}
  </div>
  
  <!-- Chord Input Modal -->
  {#if editingCellIndex >= 0}
    <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-gray-800 border border-gray-600 rounded-lg p-6 w-96">
        <h4 class="text-lg font-medium mb-4">
          Enter Chord for Measure {editingCellIndex + 1}
        </h4>
        
        <form on:submit={handleChordSubmit}>
          <input 
            bind:this={chordInput}
            type="text"
            name="chordSymbol"
            placeholder="e.g., C, Am, F#dim7, G/B"
            bind:value={currentChordInput}
            on:input={handleChordInput}
            on:keydown={handleChordKeydown}
            class="w-full bg-gray-700 text-white px-3 py-2 rounded border border-gray-600 focus:border-primary-500 focus:outline-none mb-3"
            autocomplete="off"
          />
          
          <!-- Chord Suggestions -->
          {#if showChordSuggestions && chordSuggestions.length > 0}
            <div class="mb-3">
              <div class="text-sm text-gray-400 mb-2">Suggestions:</div>
              <div class="flex flex-wrap gap-2">
                {#each chordSuggestions as suggestion}
                  <button 
                    type="button"
                    class="bg-gray-700 hover:bg-gray-600 text-white px-2 py-1 rounded text-sm transition-colors duration-200"
                    on:click={() => handleSuggestionClick(suggestion)}
                  >
                    {suggestion}
                  </button>
                {/each}
              </div>
            </div>
          {/if}
          
          <div class="flex justify-end space-x-2">
            <button 
              type="button"
              class="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded transition-colors duration-200"
              on:click={cancelEditing}
            >
              Cancel
            </button>
            <button 
              type="submit"
              class="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded transition-colors duration-200"
            >
              Save
            </button>
          </div>
        </form>
        
        <!-- Chord Examples -->
        <div class="mt-4 text-xs text-gray-400">
          <div class="mb-1"><strong>Examples:</strong></div>
          <div>Major: C, D, E • Minor: Am, Dm, Em</div>
          <div>7th: C7, Am7, Fmaj7 • Extended: Dm9, G13</div>
          <div>Slash: C/E, Am/G • Sus: Csus4, Fsus2</div>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  /* Grid cell hover effects */
  .chord-cell:hover {
    transform: translateY(-1px);
  }
  
  /* Active chord animation */
  @keyframes chord-pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
  }
  
  .chord-active {
    animation: chord-pulse 1s ease-in-out infinite;
  }
  
  /* Smooth transitions */
  .chord-cell {
    transition: all 0.2s ease-in-out;
  }
  
  /* Focus styles for accessibility */
  button:focus-visible,
  input:focus-visible {
    outline: 2px solid #3b82f6;
    outline-offset: 2px;
  }
</style> 
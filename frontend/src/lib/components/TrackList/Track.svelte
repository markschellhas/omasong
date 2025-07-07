<script>
  import { createEventDispatcher } from 'svelte';
  import { browser } from '$app/environment';
  import { 
    Mic, MicOff, Volume2, VolumeX, Headphones, 
    RotateCcw 
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
   * Handle clear track events
   */
  function handleClear() {
    if (confirm('Clear all recorded notes from this track?')) {
      dispatch('clear');
    }
  }
  
  /**
   * Get track color class based on color
   * @returns {string} CSS class
   */
  function getTrackColorClass() {
    return `border-l-4 border-l-${track.color.replace('#', '')}-500`;
  }
  
  /**
   * Get recording level bar width
   * @returns {number} Width percentage
   */
  function getRecordingLevelWidth() {
    return Math.min(100, recordingLevel * 100);
  }
  
  /**
   * Get volume percentage for display
   * @param {number} volume Volume value (0-1)
   * @returns {number} Percentage
   */
  function getVolumePercentage(volume) {
    return Math.round(volume * 100);
  }
  
  // Piano roll visualization settings
  const PIANO_ROLL_HEIGHT = 200; // pixels (increased from 120)
  const TIMELINE_WIDTH = 600; // pixels (doubled)
  const BEATS_VISIBLE = 48; // beats to show in timeline (3x wider: 16 -> 48)
  const MIN_NOTE = 36; // C2 (lower range to catch more notes)
  const MAX_NOTE = 96; // C7 (higher range to catch more notes)
  const NOTE_RANGE = MAX_NOTE - MIN_NOTE;
  
  /**
   * Get piano roll visualization data
   * @returns {Array} Array of positioned note rectangles
   */
  function getPianoRollNotes() {
    if (!track.midiEvents || track.midiEvents.length === 0) return [];
    
    return track.midiEvents.map((event, index) => {
      // Calculate X position (time to pixels) - ensure it's visible
      const xPercent = Math.max(0, (event.time / BEATS_VISIBLE) * 100);
      const widthPercent = Math.max(2, (event.duration / BEATS_VISIBLE) * 100); // Minimum 2% width
      
      // Calculate Y position (note to pixels from bottom) - clamp to visible range
      const noteInRange = Math.max(MIN_NOTE, Math.min(MAX_NOTE, event.note));
      const yPercent = ((noteInRange - MIN_NOTE) / NOTE_RANGE) * 100;
      
      // Get note info for display
      const noteName = getNoteNameFromMidi(event.note);
      const velocityOpacity = Math.max(0.5, event.velocity / 127); // Minimum 50% opacity
      
      const noteRect = {
        id: `note-${index}`,
        x: Math.min(98, xPercent), // Keep within bounds
        y: Math.max(0, Math.min(95, 100 - yPercent)), // Flip Y axis (higher notes at top)
        width: Math.min(100 - xPercent, widthPercent), // Ensure visible width
        height: 8, // Taller for better visibility in larger piano roll
        note: event.note,
        noteName,
        time: event.time,
        duration: event.duration,
        velocity: event.velocity,
        opacity: velocityOpacity,
        color: getNoteColor(event.note),
        // More permissive visibility - show notes even if slightly outside time range
        isVisible: event.note >= MIN_NOTE && event.note <= MAX_NOTE
      };
      
      console.log(`🎹 Note ${index}: ${noteName} (MIDI ${event.note}) at time ${event.time.toFixed(2)} beats → x:${noteRect.x.toFixed(1)}% y:${noteRect.y.toFixed(1)}% xPercent:${xPercent.toFixed(2)} visible:${noteRect.isVisible}`);
      
      return noteRect;
    }).filter(note => note.isVisible); // Only filter by note range, not time
  }
  
  /**
   * Get note name from MIDI number
   * @param {number} midiNote MIDI note number
   * @returns {string} Note name (e.g., "C4", "F#5")
   */
  function getNoteNameFromMidi(midiNote) {
    const noteNames = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
    const octave = Math.floor(midiNote / 12) - 1;
    const note = noteNames[midiNote % 12];
    return `${note}${octave}`;
  }
  
  /**
   * Get note color based on MIDI note number
   * @param {number} note MIDI note number
   * @returns {string} CSS background color
   */
  function getNoteColor(note) {
    const noteInOctave = note % 12;
    
    // Color coding: C=red, D=orange, E=yellow, F=green, G=blue, A=indigo, B=purple
    const colors = [
      '#ef4444', // C - red
      '#dc2626', // C# - dark red  
      '#f97316', // D - orange
      '#ea580c', // D# - dark orange
      '#eab308', // E - yellow
      '#22c55e', // F - green
      '#16a34a', // F# - dark green
      '#3b82f6', // G - blue
      '#2563eb', // G# - dark blue
      '#8b5cf6', // A - violet
      '#7c3aed', // A# - dark violet
      '#d946ef'  // B - fuchsia
    ];
    
    return colors[noteInOctave];
  }
  
  /**
   * Generate piano roll grid lines for reference
   * @returns {Array} Array of grid line data
   */
  function getPianoRollGrid() {
    const grid = {
      timeLines: [],
      noteLines: []
    };
    
    // Vertical time lines (every 2 beats for readability at wider scale)
    for (let beat = 0; beat <= BEATS_VISIBLE; beat += 2) {
      const xPercent = (beat / BEATS_VISIBLE) * 100;
      grid.timeLines.push({
        x: xPercent,
        label: beat,
        isMajor: beat % 8 === 0 // Every 8 beats (2 measures) is major
      });
    }
    
    // Horizontal note lines (every octave and C notes)
    for (let note = MIN_NOTE; note <= MAX_NOTE; note++) {
      const noteInOctave = note % 12;
      if (noteInOctave === 0) { // C notes
        const yPercent = 100 - ((note - MIN_NOTE) / NOTE_RANGE) * 100;
        grid.noteLines.push({
          y: yPercent,
          label: getNoteNameFromMidi(note),
          isMajor: true
        });
      }
    }
    
    return grid;
  }
  
  // Reactive statements
  $: pianoRollNotes = getPianoRollNotes();
  $: pianoRollGrid = getPianoRollGrid();
  
  // Debug track events and piano roll
  $: {
    console.log(`🎵 Track ${track.name}: ${track.midiEvents?.length || 0} MIDI events:`, track.midiEvents);
    if (track.midiEvents?.length > 0) {
      console.log(`🎹 Piano roll notes:`, pianoRollNotes);
      console.log(`🎹 Note range: ${MIN_NOTE}-${MAX_NOTE}, Events note range: ${Math.min(...track.midiEvents.map(e => e.note))}-${Math.max(...track.midiEvents.map(e => e.note))}`);
      console.log(`🎹 Time range: 0-${BEATS_VISIBLE} beats, Events time range: ${Math.min(...track.midiEvents.map(e => e.time))}-${Math.max(...track.midiEvents.map(e => e.time))}`);
    }
  }
</script>

<!-- Track Container -->
<div 
  class="bg-gray-900 border border-gray-700 rounded-lg p-3 {getTrackColorClass()} {isActive ? 'ring-2 ring-primary-500' : ''} {isRecording ? 'ring-2 ring-red-500 bg-red-900/10' : ''}"
  on:click={handleSelect}
  role="button"
  tabindex="0"
  aria-label="Track {track.name}"
>
  <!-- Track Header Row -->
  <div class="flex items-center justify-between mb-3">
    <!-- Track Name and Status -->
    <div class="flex items-center space-x-3 flex-1">
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
      
      <!-- Event Count and Recording Status -->
      <div class="flex items-center space-x-2">
        {#if isRecording}
          <span class="text-xs px-2 py-1 bg-red-600 text-white rounded animate-pulse">
            REC
          </span>
        {/if}
        
        {#if hasEvents}
          <span 
            class="text-xs px-2 py-1 bg-green-600 text-white rounded"
            title="{eventCount} recorded notes"
          >
            {eventCount}
          </span>
        {/if}
      </div>
    </div>
    
    <!-- Clear Button -->
    {#if hasEvents}
      <button 
        class="p-1 hover:bg-gray-700 rounded transition-colors duration-200 text-yellow-400"
        on:click|stopPropagation={handleClear}
        title="Clear recorded notes"
      >
        <RotateCcw class="w-4 h-4" />
      </button>
    {/if}
  </div>
  
  <!-- Control Buttons Row -->
  <div class="flex items-center space-x-2 mb-3">
    <!-- Arm Button -->
    <button 
      class="p-2 rounded {track.isArmed ? 'bg-red-600 text-white animate-pulse' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'} transition-colors duration-200"
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
      class="bg-gray-700 text-white text-sm px-2 py-1 rounded border border-gray-600 focus:border-primary-500 focus:outline-none capitalize flex-1"
      title="Track instrument"
    >
      {#each INSTRUMENTS as instrument}
        <option value={instrument} class="capitalize">{instrument}</option>
      {/each}
    </select>
  </div>
  
  <!-- Volume Control -->
  <div class="mb-3">
    <div class="flex items-center justify-between mb-1">
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
  
  <!-- Piano Roll Visualization -->
  <div class="bg-gray-800 rounded p-2">
    {#if hasEvents}
      <div class="text-xs text-gray-400 mb-2 flex justify-between">
        <span>Piano Roll ({eventCount} notes)</span>
        <span>0 → {BEATS_VISIBLE} beats</span>
      </div>
      
      <!-- Piano Roll Container -->
      <div class="relative bg-gray-900 rounded border border-gray-700 overflow-hidden" style="height: {PIANO_ROLL_HEIGHT}px; min-width: 100%;">
        <!-- Grid Lines -->
        <svg class="absolute inset-0 w-full h-full pointer-events-none">
          <!-- Vertical time lines -->
          {#each pianoRollGrid.timeLines as line}
            <line 
              x1="{line.x}%" 
              y1="0" 
              x2="{line.x}%" 
              y2="100%" 
              stroke={line.isMajor ? '#4b5563' : '#374151'}
              stroke-width={line.isMajor ? '1' : '0.5'}
              opacity="0.6"
            />
            {#if line.isMajor && line.label > 0}
              <text 
                x="{line.x}%" 
                y="12" 
                fill="#9ca3af" 
                font-size="10" 
                text-anchor="middle"
              >
                {line.label}
              </text>
            {/if}
          {/each}
          
          <!-- Horizontal note lines -->
          {#each pianoRollGrid.noteLines as line}
            <line 
              x1="0" 
              y1="{line.y}%" 
              x2="100%" 
              y2="{line.y}%" 
              stroke="#4b5563"
              stroke-width="0.5"
              opacity="0.4"
            />
            <text 
              x="4" 
              y="{line.y - 1}%" 
              fill="#9ca3af" 
              font-size="9" 
              text-anchor="start"
            >
              {line.label}
            </text>
          {/each}
        </svg>
        
                 <!-- Note Rectangles -->
         {#each pianoRollNotes as noteRect}
           <div 
             class="absolute rounded-sm border border-white/40"
             style="
               left: {noteRect.x}%; 
               top: {noteRect.y}%; 
               width: {Math.max(2, noteRect.width)}%; 
               height: {noteRect.height}px;
               background-color: {noteRect.color};
               opacity: {noteRect.opacity};
               z-index: 10;
             "
             title="{noteRect.noteName} | Time: {noteRect.time.toFixed(2)} beats | Duration: {noteRect.duration.toFixed(2)} beats | Velocity: {noteRect.velocity}"
           ></div>
         {/each}
         
                   <!-- Fallback: Show all notes as simple rectangles if pianoRollNotes is empty -->
          {#if pianoRollNotes.length === 0 && track.midiEvents?.length > 0}
            {#each track.midiEvents.slice(0, 8) as event, index}
              <div 
                class="absolute rounded-sm border border-yellow-400 bg-yellow-500"
                style="
                  left: {(index * 8) + 2}%; 
                  top: {15 + (index * 8)}%; 
                  width: 6%; 
                  height: 12px;
                  opacity: 0.8;
                  z-index: 20;
                "
                title="Fallback: {getNoteNameFromMidi(event.note)} at {event.time.toFixed(2)} beats"
              ></div>
            {/each}
          {/if}
        
        <!-- Recording Indicator -->
        {#if isRecording && track.isArmed}
          <div 
            class="absolute top-2 right-2 w-3 h-3 bg-red-500 rounded-full animate-pulse"
            title="Recording..."
          ></div>
        {/if}
      </div>
      
             <!-- Note Range Indicator -->
       <div class="text-xs text-gray-500 mt-1 text-center">
         Range: {getNoteNameFromMidi(MIN_NOTE)} - {getNoteNameFromMidi(MAX_NOTE)} | Showing {pianoRollNotes.length} of {eventCount} notes
       </div>
       
       <!-- Debug: Simple Note List if piano roll is empty -->
       {#if pianoRollNotes.length === 0 && eventCount > 0}
         <div class="mt-2 p-2 bg-yellow-900/20 border border-yellow-600 rounded">
           <div class="text-xs text-yellow-400 mb-1">Debug: Notes outside visible range (0-{BEATS_VISIBLE} beats)</div>
           <div class="flex flex-wrap gap-1">
             {#each track.midiEvents.slice(0, 10) as event, index}
               <span 
                 class="px-1 py-0.5 bg-yellow-600 text-black text-xs rounded"
                 title="MIDI: {event.note}, Time: {event.time.toFixed(2)} beats, Duration: {event.duration.toFixed(2)}, Velocity: {event.velocity}"
               >
                 {getNoteNameFromMidi(event.note)} @{event.time.toFixed(1)}b
               </span>
             {/each}
             {#if track.midiEvents.length > 10}
               <span class="text-xs text-yellow-400">+{track.midiEvents.length - 10} more</span>
             {/if}
           </div>
           <div class="text-xs text-yellow-300 mt-1">
             Time range in data: {Math.min(...track.midiEvents.map(e => e.time)).toFixed(2)} - {Math.max(...track.midiEvents.map(e => e.time)).toFixed(2)} beats
           </div>
         </div>
       {/if}
      
    {:else if track.isArmed && isRecording}
      <div class="text-xs text-red-400 text-center italic animate-pulse p-4">Recording... play notes on keyboard</div>
    {:else if track.isArmed}
      <div class="text-xs text-green-400 text-center italic p-4">Ready to record - click Record then Play</div>
    {:else}
      <div class="text-xs text-gray-400 text-center italic p-4">No notes recorded</div>
    {/if}
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
  
  /* Focus styles for accessibility */
  button:focus-visible,
  input:focus-visible,
  select:focus-visible {
    outline: 2px solid #3b82f6;
    outline-offset: 2px;
  }
  
  /* Recording animation */
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
  }
  
  .animate-pulse {
    animation: pulse 1s ease-in-out infinite;
  }
</style> 
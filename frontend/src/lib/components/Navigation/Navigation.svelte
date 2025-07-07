<script>
  import { onMount, onDestroy } from 'svelte';
  import { browser } from '$app/environment';
  import { Play, Pause, Square, SkipBack, RotateCw } from 'lucide-svelte';
  import { audioState } from '../../stores/audio.js';
  import { getAudioEngine } from '../../utils/audioEngine.js';
  import { getChordPlayer } from '../../utils/chordPlayer.js';
  
  /** @type {import('../../types/jsdoc-types.js').AudioState} */
  let currentAudioState;
  
  /** @type {import('../../utils/audioEngine.js').AudioEngine} */
  let audioEngine;
  
  /** @type {import('../../utils/chordPlayer.js').default} */
  let chordPlayer;
  
  /** @type {number} */
  let tempoInput = 120;
  
  /** @type {number[]} */
  let tapTimes = [];
  
  /** @type {boolean} */
  let showCountIn = false;
  
  /** @type {number} */
  let beatPulse = 0;
  
  /** @type {number} */
  let beatPulseInterval;
  
  // Subscribe to audio state
  const unsubscribe = audioState.subscribe(state => {
    currentAudioState = state;
    tempoInput = state.tempo;
    
    // Show count-in indicator
    showCountIn = state.isCountingIn;
    
    // Handle beat pulsing during playback
    if (state.isPlaying) {
      startBeatPulse();
    } else {
      stopBeatPulse();
    }
  });
  
  onMount(async () => {
    if (!browser) return;
    
    audioEngine = getAudioEngine();
    
    // Initialize audio engine on first user interaction
    const initializeOnInteraction = async () => {
      await audioEngine.initialize();
      // Initialize chord player after audio engine is ready
      chordPlayer = getChordPlayer(audioEngine);
      console.log('🎵 Navigation: ChordPlayer initialized');
      document.removeEventListener('click', initializeOnInteraction);
    };
    
    document.addEventListener('click', initializeOnInteraction);
  });
  
  onDestroy(() => {
    unsubscribe();
    stopBeatPulse();
  });
  
  /**
   * Start beat pulse animation
   */
  function startBeatPulse() {
    if (beatPulseInterval) return;
    
    const beatDuration = (60 / currentAudioState.tempo) * 1000;
    
    beatPulseInterval = setInterval(() => {
      beatPulse = Date.now();
    }, beatDuration);
  }
  
  /**
   * Stop beat pulse animation
   */
  function stopBeatPulse() {
    if (beatPulseInterval) {
      clearInterval(beatPulseInterval);
      beatPulseInterval = null;
    }
  }
  
  /**
   * Handle play/pause button click
   */
  async function handlePlayPause() {
    if (!audioEngine.isInitialized()) {
      await audioEngine.initialize();
    }
    
    if (currentAudioState.isPlaying) {
      audioEngine.pause();
    } else {
      // Check if we need count-in (at position 0 and recording)
      if (currentAudioState.playheadPosition === 0 && currentAudioState.isRecording) {
        audioEngine.startCountIn(() => {
          audioEngine.play();
        });
      } else {
        audioEngine.play();
      }
    }
  }
  
  /**
   * Handle stop button click
   */
  function handleStop() {
    audioEngine.stop();
  }
  
  /**
   * Handle rewind to beginning
   */
  function handleRewind() {
    audioEngine.seek(0);
  }
  
  /**
   * Handle record button click
   */
  function handleRecord() {
    if (currentAudioState.isRecording) {
      audioState.stopRecording();
    } else {
      audioState.startRecording();
    }
  }
  
  /**
   * Handle loop toggle
   */
  function handleLoopToggle() {
    // Loop functionality would be implemented in audio engine
    console.log('Loop toggle - not yet implemented');
  }
  
  /**
   * Handle tempo input change
   * @param {Event} event
   */
  function handleTempoChange(event) {
    const value = parseInt(event.target.value);
    if (value >= 60 && value <= 200) {
      audioEngine.setTempo(value);
    }
  }
  
  /**
   * Handle tempo slider change
   * @param {Event} event
   */
  function handleTempoSlider(event) {
    const value = parseInt(event.target.value);
    audioEngine.setTempo(value);
  }
  
  /**
   * Handle tap tempo button
   */
  function handleTapTempo() {
    const now = Date.now();
    tapTimes.push(now);
    
    // Keep only the last 4 taps
    if (tapTimes.length > 4) {
      tapTimes.shift();
    }
    
    // Calculate tempo if we have at least 2 taps
    if (tapTimes.length >= 2) {
      const intervals = [];
      for (let i = 1; i < tapTimes.length; i++) {
        intervals.push(tapTimes[i] - tapTimes[i - 1]);
      }
      
      const avgInterval = intervals.reduce((a, b) => a + b) / intervals.length;
      const bpm = Math.round(60000 / avgInterval);
      
      if (bpm >= 60 && bpm <= 200) {
        audioEngine.setTempo(bpm);
      }
    }
    
    // Clear tap times after 3 seconds of inactivity
    setTimeout(() => {
      const timeSinceLastTap = Date.now() - tapTimes[tapTimes.length - 1];
      if (timeSinceLastTap >= 3000) {
        tapTimes = [];
      }
    }, 3000);
  }
  
  /**
   * Handle metronome toggle
   */
  function handleMetronomeToggle() {
    audioEngine.setMetronomeEnabled(!currentAudioState.metronomeEnabled);
  }
  
  /**
   * Handle metronome volume change
   * @param {Event} event
   */
  function handleMetronomeVolume(event) {
    const value = parseFloat(event.target.value);
    audioEngine.setMetronomeVolume(value);
  }
  

</script>

<!-- Count-in Indicator -->
{#if showCountIn}
  <div class="fixed top-4 left-1/2 transform -translate-x-1/2 bg-yellow-600 text-white px-4 py-2 rounded-lg font-bold text-xl z-50">
    Count-in: <span class="text-2xl">{currentAudioState.countInBeatsRemaining}</span>
  </div>
{/if}

<!-- Main Navigation -->
<nav class="col-span-3 bg-gray-800 border-b border-gray-700 p-4 flex items-center justify-between">
  <!-- Left: Transport Controls -->
  <div class="flex items-center space-x-2">
    <!-- Rewind to Beginning -->
    <button 
      class="bg-gray-600 hover:bg-gray-700 text-white p-2 rounded-lg transition-colors duration-200"
      on:click={handleRewind}
      title="Rewind to Beginning"
    >
      <SkipBack class="w-5 h-5" />
    </button>
    
    <!-- Play/Pause -->
    <button 
      class="bg-primary-600 hover:bg-primary-700 text-white p-2 rounded-lg transition-colors duration-200"
      on:click={handlePlayPause}
      title={currentAudioState.isPlaying ? 'Pause' : 'Play'}
    >
      {#if currentAudioState.isPlaying}
        <Pause class="w-5 h-5" />
      {:else}
        <Play class="w-5 h-5" />
      {/if}
    </button>
    
    <!-- Stop -->
    <button 
      class="bg-gray-600 hover:bg-gray-700 text-white p-2 rounded-lg transition-colors duration-200"
      on:click={handleStop}
      title="Stop"
    >
      <Square class="w-5 h-5" />
    </button>
    
    <!-- Record -->
    <button 
      class="bg-red-600 hover:bg-red-700 text-white p-2 rounded-lg transition-colors duration-200 {currentAudioState.isRecording ? 'animate-pulse' : ''}"
      on:click={handleRecord}
      title={currentAudioState.isRecording ? 'Stop Recording' : 'Record'}
    >
      <div class="w-3 h-3 bg-white rounded-full"></div>
    </button>
    
    <!-- Loop Toggle -->
    <button 
      class="bg-gray-600 hover:bg-gray-700 text-white p-2 rounded-lg transition-colors duration-200"
      on:click={handleLoopToggle}
      title="Loop"
    >
      <RotateCw class="w-5 h-5" />
    </button>
  </div>
  
  <!-- Center: Tempo Controls -->
  <div class="flex items-center space-x-4">
    <!-- BPM Display and Input -->
    <div class="flex items-center space-x-2">
      <label class="text-sm font-medium text-gray-300">BPM:</label>
      <input 
        type="number" 
        min="60" 
        max="200" 
        bind:value={tempoInput}
        on:change={handleTempoChange}
        class="w-16 bg-gray-700 border border-gray-600 rounded px-2 py-1 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
      />
    </div>
    
    <!-- Tempo Slider -->
    <input 
      type="range" 
      min="60" 
      max="200" 
      bind:value={tempoInput}
      on:input={handleTempoSlider}
      class="w-24 accent-primary-500"
    />
    
    <!-- Tap Tempo -->
    <button 
      class="bg-secondary-600 hover:bg-secondary-700 text-white px-3 py-1 rounded text-sm transition-colors duration-200"
      on:click={handleTapTempo}
      title="Tap Tempo"
    >
      TAP
    </button>
  </div>
  
  <!-- Right: Metronome and Beat Indicator -->
  <div class="flex items-center space-x-4">
    <!-- Beat Indicator -->
    <div class="flex items-center space-x-2">
      <span class="text-sm text-gray-300">Beat:</span>
      <div 
        class="w-8 h-8 rounded-full border-2 border-primary-500 flex items-center justify-center transition-all duration-100 {currentAudioState.isPlaying ? 'animate-pulse' : ''}"
        style="animation-duration: {60/currentAudioState.tempo}s"
      >
        <div class="w-2 h-2 bg-primary-500 rounded-full"></div>
      </div>
      <span class="text-sm font-mono text-white min-w-[3rem]">
        {currentAudioState.currentBar}:{currentAudioState.currentBeat}
      </span>
    </div>
    
    <!-- Metronome Controls -->
    <div class="flex items-center space-x-2">
      <!-- Metronome Toggle -->
      <button 
        class="bg-{currentAudioState.metronomeEnabled ? 'green' : 'gray'}-600 hover:bg-{currentAudioState.metronomeEnabled ? 'green' : 'gray'}-700 text-white px-3 py-1 rounded text-sm transition-colors duration-200"
        on:click={handleMetronomeToggle}
        title="Toggle Metronome"
      >
        METRO
      </button>
      
      <!-- Metronome Volume -->
      <div class="flex items-center space-x-1">
        <span class="text-xs text-gray-400">Vol:</span>
        <input 
          type="range" 
          min="0" 
          max="1" 
          step="0.1" 
          value={currentAudioState.metronomeVolume}
          on:input={handleMetronomeVolume}
          class="w-16 accent-green-500"
          title="Metronome Volume"
        />
      </div>
    </div>

  </div>
</nav>

<style>
  /* Custom animation for beat pulse */
  @keyframes beat-pulse {
    0%, 100% { 
      transform: scale(1);
      opacity: 1;
    }
    50% { 
      transform: scale(1.2);
      opacity: 0.7;
    }
  }
  
  .beat-pulse {
    animation: beat-pulse var(--beat-duration) infinite;
  }
</style> 
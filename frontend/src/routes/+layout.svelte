<script>
	// Import global styles and types
	import '../lib/types/jsdoc-types.js';
	import Navigation from '../lib/components/Navigation/Navigation.svelte';
	import VirtualKeyboard from '../lib/components/VirtualKeyboard/VirtualKeyboard.svelte';
	import TimeIndicator from '../lib/components/TimeIndicator/TimeIndicator.svelte';
	import TrackList from '../lib/components/TrackList/TrackList.svelte';
	import ChordGrid from '../lib/components/ChordGrid/ChordGrid.svelte';
</script>

<!-- Main App Container with CSS Grid -->
<div class="app-container grid grid-cols-4 grid-rows-4 h-screen bg-gray-900 text-white">
	<!-- Navigation -->
	<Navigation />
	
	<!-- Chord Grid -->
	<section class="col-span-3 bg-gray-800 border-b border-gray-700 p-4">
		<!-- Chord Grid Component -->
		<ChordGrid />
	</section>
	
	<!-- Tracks -->
	<section class="col-span-3 bg-gray-800 border-b border-gray-700 p-4 overflow-y-auto relative">
		<!-- Track List Component -->
		<TrackList />
		
		<!-- Time Indicator overlays the tracks -->
		<TimeIndicator />
	</section>
	
	<!-- Virtual Keyboard -->
	<VirtualKeyboard />
	
	<!-- Sidebar -->
	<aside class="row-span-4 bg-gray-900 border-l border-gray-700 p-4 flex flex-col">
		<div class="text-sm font-medium mb-4">AI Assistant</div>
		<!-- Chat interface will go here -->
		<div class="flex-1 bg-gray-800 rounded-lg p-4">
			<div class="text-sm text-gray-400">Chat interface coming soon...</div>
		</div>
	</aside>
</div>

<slot />

<style>
	.app-container {
		grid-template-areas: 
			"nav nav nav sidebar"
			"chords chords chords sidebar"
			"tracks tracks tracks sidebar"
			"keyboard keyboard keyboard sidebar";
		grid-template-rows: auto auto 1fr auto;
		grid-template-columns: 1fr 1fr 1fr 300px;
	}
</style> 
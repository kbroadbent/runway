<script lang="ts">
	import '../app.css';
	import Sidebar from '$lib/components/Sidebar.svelte';
	import favicon from '$lib/assets/favicon.svg';

	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<title>Runway</title>
</svelte:head>

<div class="app-layout">
	<Sidebar />
	<main class="main-content">
		{@render children()}
	</main>
</div>

<style>
	.app-layout {
		display: flex;
		min-height: 100vh;
	}

	.main-content {
		margin-left: 200px;
		flex: 1;
		padding: 1.5rem 2rem;
	}
</style>

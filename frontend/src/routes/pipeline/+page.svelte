<script lang="ts">
	import type { PipelineEntry } from '$lib/types';
	import { pipeline } from '$lib/api';
	import KanbanBoard from '$lib/components/KanbanBoard.svelte';
	import PipelineDetailPanel from '$lib/components/PipelineDetailPanel.svelte';
	import { onMount } from 'svelte';

	let board = $state<Record<string, PipelineEntry[]>>({});
	let selectedEntry = $state<PipelineEntry | null>(null);

	onMount(loadBoard);

	async function loadBoard() {
		board = await pipeline.list();
	}

	function handleCardClick(entry: PipelineEntry) {
		selectedEntry = entry;
	}

	async function handleMoved() {
		await loadBoard();
	}

	async function handleUpdated() {
		await loadBoard();
		// Refresh selected entry from new board data
		if (selectedEntry) {
			for (const entries of Object.values(board)) {
				const updated = entries.find((e) => e.id === selectedEntry!.id);
				if (updated) { selectedEntry = updated; break; }
			}
		}
	}
</script>

<div class="page-header">
	<h1>Pipeline</h1>
</div>

<KanbanBoard {board} onCardClick={handleCardClick} onMoved={handleMoved} />

{#if selectedEntry}
	<PipelineDetailPanel
		entry={selectedEntry}
		onClose={() => (selectedEntry = null)}
		onUpdated={handleUpdated}
	/>
{/if}

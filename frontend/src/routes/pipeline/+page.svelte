<script lang="ts">
	import type { PipelineEntry } from '$lib/types';
	import { pipeline } from '$lib/api';
	import KanbanBoard from '$lib/components/KanbanBoard.svelte';
	import PipelineDetailPanel from '$lib/components/PipelineDetailPanel.svelte';
	import { tierFilter, searchFilter } from '$lib/stores/pipelineFilters';

	let board = $state<Record<string, PipelineEntry[]>>({});
	let selectedEntry = $state<PipelineEntry | null>(null);

	let debounceTimer: ReturnType<typeof setTimeout>;

	$effect(() => {
		const _search = $searchFilter;
		const _tier = $tierFilter;
		clearTimeout(debounceTimer);
		debounceTimer = setTimeout(() => loadBoard(), 200);
		return () => clearTimeout(debounceTimer);
	});

	async function loadBoard() {
		board = await pipeline.list({
			title: $searchFilter || undefined,
			tier: $tierFilter ?? undefined,
		});
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

<KanbanBoard {board} onCardClick={handleCardClick} onMoved={handleMoved} />

{#if selectedEntry}
	<PipelineDetailPanel
		entry={selectedEntry}
		onClose={() => (selectedEntry = null)}
		onUpdated={handleUpdated}
	/>
{/if}

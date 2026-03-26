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
			search: $searchFilter || undefined,
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
		if (selectedEntry) {
			for (const entries of Object.values(board)) {
				const updated = entries.find((e) => e.id === selectedEntry!.id);
				if (updated) { selectedEntry = updated; break; }
			}
		}
	}
</script>

<div class="pipeline-header">
	<h1>Pipeline</h1>
	<div class="filters">
		<input
			class="filter-search"
			type="text"
			placeholder="Search company or description…"
			bind:value={$searchFilter}
		/>
		<div class="tier-filter">
			<button class="btn btn-sm" class:btn-primary={$tierFilter === null} class:btn-secondary={$tierFilter !== null} onclick={() => ($tierFilter = null)}>All</button>
			<button class="btn btn-sm tier-btn-1" class:active={$tierFilter === 1} onclick={() => ($tierFilter = $tierFilter === 1 ? null : 1)}>T1</button>
			<button class="btn btn-sm tier-btn-2" class:active={$tierFilter === 2} onclick={() => ($tierFilter = $tierFilter === 2 ? null : 2)}>T2</button>
			<button class="btn btn-sm tier-btn-3" class:active={$tierFilter === 3} onclick={() => ($tierFilter = $tierFilter === 3 ? null : 3)}>T3</button>
		</div>
	</div>
</div>

<KanbanBoard {board} onCardClick={handleCardClick} onMoved={handleMoved} />

<style>
	.pipeline-header {
		display: flex;
		flex-direction: column;
		align-items: flex-start;
		gap: 0.5rem;
		margin-bottom: 1rem;
	}

	.filters {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.filter-search {
		width: 220px;
		padding: 0.35rem 0.5rem;
		font-size: 0.85rem;
		background: var(--bg-secondary);
		border: 1px solid var(--border-color);
		border-radius: var(--radius);
		color: var(--text-primary);
		outline: none;
	}

	.filter-search:focus {
		border-color: var(--accent-blue);
	}

	.tier-filter {
		display: flex;
		gap: 0.4rem;
		align-items: center;
	}

	.tier-btn-1.active {
		background: color-mix(in srgb, #f59e0b 30%, transparent);
		color: #b45309;
		border-color: #f59e0b;
	}

	.tier-btn-2.active {
		background: color-mix(in srgb, #cd7c3a 30%, transparent);
		color: #92400e;
		border-color: #cd7c3a;
	}

	.tier-btn-3.active {
		background: color-mix(in srgb, #6b7280 30%, transparent);
		color: #374151;
		border-color: #9ca3af;
	}
</style>

{#if selectedEntry}
	<PipelineDetailPanel
		entry={selectedEntry}
		onClose={() => (selectedEntry = null)}
		onUpdated={handleUpdated}
	/>
{/if}

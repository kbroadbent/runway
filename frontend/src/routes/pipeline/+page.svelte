<script lang="ts">
	import type { PipelineEntry } from '$lib/types';
	import { pipeline } from '$lib/api';
	import KanbanBoard from '$lib/components/KanbanBoard.svelte';
	import PipelineDetailPanel from '$lib/components/PipelineDetailPanel.svelte';

	let board = $state<Record<string, PipelineEntry[]>>({});
	let selectedEntry = $state<PipelineEntry | null>(null);
	let tierFilter = $state<number | null>(null);
	let searchQuery = $state('');

	let debounceTimer: ReturnType<typeof setTimeout>;

	$effect(() => {
		const _search = searchQuery;
		const _tier = tierFilter;
		clearTimeout(debounceTimer);
		debounceTimer = setTimeout(() => loadBoard(), 200);
		return () => clearTimeout(debounceTimer);
	});

	async function loadBoard() {
		board = await pipeline.list({
			title: searchQuery || undefined,
			tier: tierFilter ?? undefined,
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

<div class="page-header">
	<h1>Pipeline</h1>
	<div class="filters">
		<input
			type="text"
			class="search-input"
			placeholder="Filter by title..."
			bind:value={searchQuery}
		/>
		<div class="tier-filter">
			<button class="btn btn-sm" class:btn-primary={tierFilter === null} class:btn-secondary={tierFilter !== null} onclick={() => (tierFilter = null)}>All</button>
			<button class="btn btn-sm tier-btn-1" class:active={tierFilter === 1} onclick={() => (tierFilter = tierFilter === 1 ? null : 1)}>T1</button>
			<button class="btn btn-sm tier-btn-2" class:active={tierFilter === 2} onclick={() => (tierFilter = tierFilter === 2 ? null : 2)}>T2</button>
			<button class="btn btn-sm tier-btn-3" class:active={tierFilter === 3} onclick={() => (tierFilter = tierFilter === 3 ? null : 3)}>T3</button>
		</div>
	</div>
</div>

<KanbanBoard {board} onCardClick={handleCardClick} onMoved={handleMoved} />

<style>
	.filters {
		display: flex;
		gap: 0.75rem;
		align-items: center;
	}

	.search-input {
		width: 200px;
		padding: 0.35rem 0.6rem;
		font-size: 0.85rem;
		border: 1px solid var(--border-color);
		border-radius: var(--radius);
		background: var(--bg-primary);
		color: var(--text-primary);
	}

	.search-input::placeholder {
		color: var(--text-muted);
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
		background: color-mix(in srgb, #6b7280 30%, transparent);
		color: #374151;
		border-color: #9ca3af;
	}

	.tier-btn-3.active {
		background: color-mix(in srgb, #cd7c3a 30%, transparent);
		color: #92400e;
		border-color: #cd7c3a;
	}
</style>

{#if selectedEntry}
	<PipelineDetailPanel
		entry={selectedEntry}
		onClose={() => (selectedEntry = null)}
		onUpdated={handleUpdated}
	/>
{/if}

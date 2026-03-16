<script lang="ts">
	import type { PipelineEntry } from '$lib/types';
	import { pipeline } from '$lib/api';
	import KanbanCard from './KanbanCard.svelte';

	const STAGES = [
		'Interested',
		'Applying',
		'Applied',
		'Recruiter Screen',
		'Tech Screen',
		'Onsite',
		'Offer',
		'Rejected',
		'Archived',
	];

	interface Props {
		board: Record<string, PipelineEntry[]>;
		onCardClick: (entry: PipelineEntry) => void;
		onMoved: () => void;
	}

	let { board, onCardClick, onMoved }: Props = $props();

	let draggingEntryId = $state<number | null>(null);
	let dragOverStage = $state<string | null>(null);

	function handleDragStart(e: DragEvent, entryId: number) {
		draggingEntryId = entryId;
		e.dataTransfer?.setData('text/plain', String(entryId));
	}

	function handleDragOver(e: DragEvent, stage: string) {
		e.preventDefault();
		dragOverStage = stage;
	}

	function handleDragLeave() {
		dragOverStage = null;
	}

	async function handleDrop(e: DragEvent, toStage: string) {
		e.preventDefault();
		dragOverStage = null;
		if (draggingEntryId === null) return;
		const id = draggingEntryId;
		draggingEntryId = null;

		// Find the entry to check its current stage
		for (const entries of Object.values(board)) {
			const entry = entries.find((en) => en.id === id);
			if (entry && entry.stage === toStage) return; // no-op
		}

		await pipeline.move(id, { to_stage: toStage });
		onMoved();
	}
</script>

<div class="kanban-board">
	{#each STAGES as stage}
		{@const entries = board[stage] ?? []}
		<div
			class="kanban-column"
			class:drag-over={dragOverStage === stage}
			ondragover={(e) => handleDragOver(e, stage)}
			ondragleave={handleDragLeave}
			ondrop={(e) => handleDrop(e, stage)}
		>
			<div class="column-header">
				<span class="column-name">{stage}</span>
				<span class="column-count">{entries.length}</span>
			</div>
			<div class="column-cards">
				{#each entries as entry}
					<KanbanCard
						{entry}
						onclick={() => onCardClick(entry)}
						ondragstart={(e) => handleDragStart(e, entry.id)}
					/>
				{/each}
			</div>
		</div>
	{/each}
</div>

<style>
	.kanban-board {
		display: flex;
		gap: 0.75rem;
		overflow-x: auto;
		padding-bottom: 1rem;
		min-height: calc(100vh - 10rem);
	}

	.kanban-column {
		width: 200px;
		flex-shrink: 0;
		background: var(--bg-secondary);
		border: 1px solid var(--border-color);
		border-radius: var(--radius);
		display: flex;
		flex-direction: column;
		transition: border-color 0.15s;
	}

	.kanban-column.drag-over {
		border-color: var(--accent-blue);
		background: color-mix(in srgb, var(--accent-blue) 5%, var(--bg-secondary));
	}

	.column-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0.6rem 0.75rem;
		border-bottom: 1px solid var(--border-color);
	}

	.column-name {
		font-size: 0.8rem;
		font-weight: 600;
		color: var(--text-secondary);
		text-transform: uppercase;
		letter-spacing: 0.04em;
	}

	.column-count {
		background: var(--bg-tertiary);
		color: var(--text-muted);
		border-radius: 9999px;
		font-size: 0.75rem;
		padding: 0.1rem 0.4rem;
	}

	.column-cards {
		padding: 0.5rem;
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
		flex: 1;
	}
</style>

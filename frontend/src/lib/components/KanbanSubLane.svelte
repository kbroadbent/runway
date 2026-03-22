<script lang="ts">
	import type { PipelineEntry } from '$lib/types';
	import KanbanCard from './KanbanCard.svelte';

	interface Props {
		label: string;
		stageKey: string;
		entries: PipelineEntry[];
		dragOverStage: string | null;
		onCardClick: (entry: PipelineEntry) => void;
		onDragStart: (e: DragEvent, entryId: number) => void;
		onDragOver: (e: DragEvent, stageKey: string) => void;
		onDragLeave: () => void;
		onDrop: (e: DragEvent, stageKey: string) => void;
	}

	let { label, stageKey, entries, dragOverStage, onCardClick, onDragStart, onDragOver, onDragLeave, onDrop }: Props = $props();
</script>

<div
	class="sub-lane"
	class:drag-over={dragOverStage === stageKey}
	ondragover={(e) => onDragOver(e, stageKey)}
	ondragleave={onDragLeave}
	ondrop={(e) => onDrop(e, stageKey)}
>
	<div class="sub-lane-header">
		<span class="sub-lane-label">{label}</span>
		<span class="sub-lane-count">{entries.length}</span>
	</div>
	<div class="sub-lane-cards">
		{#each entries as entry}
			<KanbanCard
				{entry}
				onclick={() => onCardClick(entry)}
				ondragstart={(e) => onDragStart(e, entry.id)}
			/>
		{/each}
	</div>
</div>

<style>
	.sub-lane {
		padding: 0.35rem;
		border-radius: var(--radius);
		transition: background 0.15s;
		min-height: 2rem;
	}

	.sub-lane.drag-over {
		background: color-mix(in srgb, var(--accent-blue) 8%, transparent);
	}

	.sub-lane-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0.15rem 0.25rem 0.3rem;
	}

	.sub-lane-label {
		font-size: 0.7rem;
		font-weight: 500;
		color: var(--text-muted);
		text-transform: uppercase;
		letter-spacing: 0.03em;
	}

	.sub-lane-count {
		font-size: 0.65rem;
		color: var(--text-muted);
		background: var(--bg-tertiary);
		border-radius: 9999px;
		padding: 0rem 0.3rem;
	}

	.sub-lane-cards {
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
	}
</style>

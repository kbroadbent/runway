<script lang="ts">
	import type { PipelineEntry } from '$lib/types';
	import { pipeline } from '$lib/api';
	import KanbanCard from './KanbanCard.svelte';
	import KanbanSubLane from './KanbanSubLane.svelte';
	import StageDateModal from './StageDateModal.svelte';
	import { STAGES } from '$lib/pipeline';
	import type { StageConfig } from '$lib/pipeline';

	interface Props {
		board: Record<string, PipelineEntry[]>;
		onCardClick: (entry: PipelineEntry) => void;
		onMoved: () => void;
	}

	let { board, onCardClick, onMoved }: Props = $props();

	let draggingEntryId = $state<number | null>(null);
	let dragOverStage = $state<string | null>(null);

	let pendingMove = $state<{ entryId: number; toStage: string; entryTitle: string } | null>(null);

	function getEntries(key: string): PipelineEntry[] {
		return board[key] ?? [];
	}

	function getColumnCount(stage: StageConfig): number {
		if (stage.subLanes) {
			return stage.subLanes.reduce((sum, sl) => sum + getEntries(sl.key).length, 0);
		}
		return getEntries(stage.key).length;
	}

	let totalEntries = $derived(
		Object.values(board).reduce((sum, entries) => sum + entries.length, 0)
	);

	function handleDragStart(e: DragEvent, entryId: number) {
		draggingEntryId = entryId;
		e.dataTransfer?.setData('text/plain', String(entryId));
	}

	function handleDragOver(e: DragEvent, stageKey: string) {
		e.preventDefault();
		dragOverStage = stageKey;
	}

	function handleDragLeave() {
		dragOverStage = null;
	}

	async function handleDrop(e: DragEvent, toStageKey: string) {
		e.preventDefault();
		dragOverStage = null;
		if (draggingEntryId === null) return;
		const id = draggingEntryId;
		draggingEntryId = null;

		// Find the entry to check its current stage
		let entryTitle = '';
		for (const entries of Object.values(board)) {
			const entry = entries.find((en) => en.id === id);
			if (entry) {
				if (entry.stage === toStageKey) return; // no-op same stage
				entryTitle = entry.job_posting?.title ?? '';
				break;
			}
		}

		pendingMove = { entryId: id, toStage: toStageKey, entryTitle };
	}

	async function handleModalConfirm(dates: Record<string, string>) {
		if (!pendingMove) return;
		const { entryId, toStage } = pendingMove;
		pendingMove = null;
		await pipeline.move(entryId, { to_stage: toStage, stage_dates: dates });
		onMoved();
	}

	async function handleModalSkip() {
		if (!pendingMove) return;
		const { entryId, toStage } = pendingMove;
		pendingMove = null;
		await pipeline.move(entryId, { to_stage: toStage });
		onMoved();
	}

	function handleModalCancel() {
		pendingMove = null;
	}
</script>

<div class="kanban-board">
	{#each STAGES as stage}
		<div class="kanban-column" class:has-sub-lanes={!!stage.subLanes}>
			<div class="column-header">
				<span class="column-name">{stage.label}</span>
				<span class="column-count">{getColumnCount(stage)}</span>
			</div>

			{#if stage.subLanes}
				<div class="column-sub-lanes">
					{#each stage.subLanes as subLane}
						<KanbanSubLane
							label={subLane.label}
							stageKey={subLane.key}
							entries={getEntries(subLane.key)}
							{dragOverStage}
							{onCardClick}
							onDragStart={handleDragStart}
							onDragOver={handleDragOver}
							onDragLeave={handleDragLeave}
							onDrop={handleDrop}
						/>
					{/each}
				</div>
			{:else}
				{@const entries = getEntries(stage.key)}
				<div
					class="column-cards"
					class:drag-over={dragOverStage === stage.key}
					ondragover={(e) => handleDragOver(e, stage.key)}
					ondragleave={handleDragLeave}
					ondrop={(e) => handleDrop(e, stage.key)}
				>
					{#each entries as entry}
						<KanbanCard
							{entry}
							onclick={() => onCardClick(entry)}
							ondragstart={(e) => handleDragStart(e, entry.id)}
						/>
					{/each}
				</div>
			{/if}
		</div>
	{/each}
</div>

{#if pendingMove}
	<StageDateModal
		stage={pendingMove.toStage}
		entryTitle={pendingMove.entryTitle}
		onConfirm={handleModalConfirm}
		onSkip={handleModalSkip}
		onCancel={handleModalCancel}
	/>
{/if}

{#if totalEntries === 0}
	<div class="empty-state">
		<p>No pipeline entries match your filters.</p>
	</div>
{/if}

<style>
	.empty-state {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		color: var(--text-muted);
		font-size: 0.95rem;
	}

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

	.kanban-column.has-sub-lanes {
		min-width: 220px;
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

	.column-sub-lanes {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		padding: 0.25rem;
		flex: 1;
	}

	.column-cards {
		padding: 0.5rem;
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
		flex: 1;
		transition: background 0.15s;
	}

	.column-cards.drag-over {
		background: color-mix(in srgb, var(--accent-blue) 5%, var(--bg-secondary));
	}
</style>

<script lang="ts">
	import { ACTIVE_STAGES, TERMINAL_STAGES } from '$lib/pipeline';

	interface Props {
		laneCounts: Record<string, number>;
	}

	let { laneCounts }: Props = $props();

	function stageCount(stage: { key: string; subLanes?: { key: string }[] }): number {
		if (stage.subLanes) {
			return stage.subLanes.reduce((sum, sub) => sum + (laneCounts[sub.key] ?? 0), 0);
		}
		return laneCounts[stage.key] ?? 0;
	}

	let totalActive = $derived(
		ACTIVE_STAGES.reduce((sum, s) => sum + stageCount(s), 0)
	);
</script>

<div class="lane-counts">
	<div class="section-header">
		<h2>Pipeline</h2>
		<span class="total-badge">{totalActive} active</span>
	</div>

	<div class="lanes-grid">
		{#each ACTIVE_STAGES as stage}
			<a href="/pipeline" class="lane-card">
				<span class="lane-count">{stageCount(stage)}</span>
				<span class="lane-label">{stage.label}</span>
			</a>
		{/each}
	</div>

	<div class="terminal-section">
		{#each TERMINAL_STAGES as stage}
			<div class="terminal-lane">
				<span class="terminal-label">{stage.label}</span>
				<span class="terminal-count">{stageCount(stage)}</span>
			</div>
		{/each}
	</div>
</div>

<style>
	.lane-counts {
		background: var(--bg-secondary);
		border: 1px solid var(--border-color);
		border-radius: var(--radius);
		padding: 1.25rem;
	}

	.section-header {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-bottom: 1rem;
	}

	.section-header h2 {
		font-size: 1rem;
		font-weight: 600;
		color: var(--text-primary);
	}

	.total-badge {
		font-size: 0.75rem;
		color: var(--text-muted);
		background: var(--bg-tertiary);
		padding: 0.125rem 0.5rem;
		border-radius: 999px;
	}

	.lanes-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
		gap: 0.5rem;
		margin-bottom: 1rem;
	}

	.lane-card {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.25rem;
		padding: 0.75rem 0.5rem;
		background: var(--bg-tertiary);
		border-radius: var(--radius);
		text-decoration: none;
		transition: background 0.15s;
	}

	.lane-card:hover {
		background: var(--bg-primary);
		text-decoration: none;
	}

	.lane-count {
		font-size: 1.5rem;
		font-weight: 700;
		color: var(--accent-blue);
	}

	.lane-label {
		font-size: 0.75rem;
		color: var(--text-secondary);
		text-align: center;
	}

	.terminal-section {
		display: flex;
		gap: 1.5rem;
		padding-top: 0.75rem;
		border-top: 1px solid var(--border-color);
	}

	.terminal-lane {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.terminal-label {
		font-size: 0.75rem;
		color: var(--text-muted);
	}

	.terminal-count {
		font-size: 0.875rem;
		font-weight: 600;
		color: var(--text-muted);
	}
</style>

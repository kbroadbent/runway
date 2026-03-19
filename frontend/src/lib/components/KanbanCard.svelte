<script lang="ts">
	import type { PipelineEntry } from '$lib/types';

	interface Props {
		entry: PipelineEntry;
		onclick: () => void;
		ondragstart: (e: DragEvent) => void;
	}

	let { entry, onclick, ondragstart }: Props = $props();

	let isUrgent = $derived.by(() => {
		if (!entry.next_action_date) return false;
		const due = new Date(entry.next_action_date);
		const now = new Date();
		const diffDays = (due.getTime() - now.getTime()) / (1000 * 60 * 60 * 24);
		return diffDays <= 2;
	});

	function formatSalary(min: number | null, max: number | null): string {
		if (!min && !max) return '';
		const fmt = (n: number) => '$' + Math.round(n / 1000) + 'k';
		if (min && max) return `${fmt(min)}–${fmt(max)}`;
		if (min) return `${fmt(min)}+`;
		return `≤${fmt(max!)}`;
	}
</script>

<div
	class="kanban-card"
	class:urgent={isUrgent}
	draggable="true"
	{ondragstart}
	onclick={onclick}
	role="button"
	tabindex="0"
	onkeydown={(e) => e.key === 'Enter' && onclick()}
>
	<div class="card-header">
		<div class="card-title">{entry.job_posting.title}</div>
		{#if entry.job_posting.tier}
			<span class="tier-badge tier-{entry.job_posting.tier}">T{entry.job_posting.tier}</span>
		{/if}
	</div>
	{#if entry.job_posting.company || entry.job_posting.company_name}
		<div class="card-company">{entry.job_posting.company?.name ?? entry.job_posting.company_name}</div>
	{/if}
	{#if entry.job_posting.salary_min || entry.job_posting.salary_max}
		<div class="card-salary">
			{formatSalary(entry.job_posting.salary_min, entry.job_posting.salary_max)}
		</div>
	{/if}
	{#if entry.next_action_date}
		<div class="card-action" class:urgent-text={isUrgent}>
			⏰ {new Date(entry.next_action_date).toLocaleDateString()}
			{#if entry.next_action}— {entry.next_action}{/if}
		</div>
	{/if}
</div>

<style>
	.kanban-card {
		background: var(--bg-primary);
		border: 1px solid var(--border-color);
		border-radius: var(--radius);
		padding: 0.6rem 0.75rem;
		cursor: grab;
		transition: border-color 0.15s, box-shadow 0.15s;
		user-select: none;
	}

	.kanban-card:hover {
		border-color: var(--accent-blue);
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
	}

	.kanban-card.urgent {
		border-color: var(--accent-yellow);
	}

	.card-header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 0.4rem;
		margin-bottom: 0.2rem;
	}

	.card-title {
		font-size: 0.9rem;
		font-weight: 600;
		line-height: 1.3;
		flex: 1;
	}

	.tier-badge {
		font-size: 0.65rem;
		font-weight: 700;
		padding: 0.1rem 0.35rem;
		border-radius: 3px;
		flex-shrink: 0;
		line-height: 1.4;
	}

	.tier-1 {
		background: color-mix(in srgb, #f59e0b 25%, transparent);
		color: #b45309;
		border: 1px solid #f59e0b;
	}

	.tier-2 {
		background: color-mix(in srgb, #6b7280 25%, transparent);
		color: #4b5563;
		border: 1px solid #9ca3af;
	}

	.tier-3 {
		background: color-mix(in srgb, #cd7c3a 25%, transparent);
		color: #92400e;
		border: 1px solid #cd7c3a;
	}

	.card-company {
		font-size: 0.8rem;
		color: var(--text-secondary);
		margin-bottom: 0.2rem;
	}

	.card-salary {
		font-size: 0.8rem;
		color: var(--accent-green);
	}

	.card-action {
		font-size: 0.75rem;
		color: var(--text-muted);
		margin-top: 0.3rem;
	}

	.urgent-text {
		color: var(--accent-yellow);
	}
</style>

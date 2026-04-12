<script lang="ts">
	import type { StaleEntry } from '$lib/types';
	import { STAGES } from '$lib/pipeline';

	interface Props {
		items: StaleEntry[];
	}

	let { items }: Props = $props();

	let showAll = $state(false);
	const VISIBLE_LIMIT = 10;

	let visibleItems = $derived(showAll ? items : items.slice(0, VISIBLE_LIMIT));
	let hasMore = $derived(items.length > VISIBLE_LIMIT);

	const stageLabelMap = new Map<string, string>();
	for (const stage of STAGES) {
		stageLabelMap.set(stage.key, stage.label);
		if (stage.subLanes) {
			for (const sub of stage.subLanes) {
				stageLabelMap.set(sub.key, `${stage.label} (${sub.label})`);
			}
		}
	}

	function formatStage(key: string): string {
		return stageLabelMap.get(key) ?? key;
	}
</script>

<div class="stale-entries">
	<h2>Stale Applications</h2>

	{#if items.length === 0}
		<p class="empty-state">No stale applications. Everything is moving.</p>
	{:else}
		<div class="items-list">
			{#each visibleItems as item}
				<a class="stale-item" href="/pipeline?entry={item.pipeline_entry_id}">
					<div class="item-left">
						<span class="item-stage-badge">{formatStage(item.stage)}</span>
						<div class="item-details">
							<span class="item-title">{item.job_title}</span>
							{#if item.company_name}
								<span class="item-company">{item.company_name}</span>
							{/if}
						</div>
					</div>
					<div class="item-days">{item.days_in_stage}d</div>
				</a>
			{/each}
		</div>

		{#if hasMore && !showAll}
			<button class="show-more" onclick={() => (showAll = true)}>
				Show all ({items.length} items)
			</button>
		{/if}
	{/if}
</div>

<style>
	.stale-entries {
		background: var(--bg-secondary);
		border: 1px solid var(--border-color);
		border-radius: var(--radius);
		padding: 1.25rem;
	}

	h2 {
		font-size: 1rem;
		font-weight: 600;
		color: var(--text-primary);
		margin-bottom: 1rem;
	}

	.empty-state {
		color: var(--text-muted);
		font-size: 0.875rem;
		padding: 1rem 0;
	}

	.items-list {
		display: flex;
		flex-direction: column;
		gap: 0.375rem;
	}

	.stale-item {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0.625rem 0.75rem;
		background: var(--bg-tertiary);
		border-radius: var(--radius);
		border-left: 3px solid var(--text-muted);
		text-decoration: none;
		color: inherit;
		cursor: pointer;
	}

	.stale-item:hover {
		filter: brightness(1.08);
	}

	.item-left {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		min-width: 0;
	}

	.item-stage-badge {
		font-size: 0.625rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		padding: 0.125rem 0.375rem;
		border-radius: 3px;
		background: var(--bg-primary);
		color: var(--text-muted);
		white-space: nowrap;
	}

	.item-details {
		display: flex;
		flex-direction: column;
		min-width: 0;
	}

	.item-title {
		font-size: 0.875rem;
		color: var(--text-primary);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.item-company {
		font-size: 0.75rem;
		color: var(--text-muted);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.item-days {
		font-size: 0.75rem;
		color: var(--text-muted);
		white-space: nowrap;
		margin-left: 1rem;
		font-weight: 600;
	}

	.show-more {
		display: block;
		width: 100%;
		margin-top: 0.5rem;
		padding: 0.5rem;
		background: none;
		border: 1px solid var(--border-color);
		border-radius: var(--radius);
		color: var(--text-secondary);
		font-size: 0.75rem;
		text-align: center;
		transition: background 0.15s, color 0.15s;
	}

	.show-more:hover {
		background: var(--bg-tertiary);
		color: var(--text-primary);
	}
</style>

<script lang="ts">
	import type { CompletedInterview } from '$lib/types';

	interface Props {
		items: CompletedInterview[];
	}

	let { items }: Props = $props();

	let showAll = $state(false);
	const VISIBLE_LIMIT = 10;
	const STALE_DAYS = 7;

	let visibleItems = $derived(showAll ? items : items.slice(0, VISIBLE_LIMIT));
	let hasMore = $derived(items.length > VISIBLE_LIMIT);

	function parseDate(dateStr: string): Date {
		if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
			return new Date(dateStr + 'T00:00:00');
		}
		return new Date(dateStr);
	}

	function formatDate(dateStr: string | null): string {
		if (!dateStr) return '';
		return parseDate(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
	}
</script>

<div class="completed-interviews">
	<h2>Completed Interviews</h2>

	{#if items.length === 0}
		<p class="empty-state">No completed interviews awaiting next step.</p>
	{:else}
		<div class="items-list">
			{#each visibleItems as item}
				<a
					class="event-item"
					class:stale={item.days_since >= STALE_DAYS}
					href="/pipeline?entry={item.pipeline_entry_id}"
				>
					<div class="item-left">
						<span class="item-type-badge">Interview</span>
						<div class="item-details">
							<span class="item-description">
								{item.stage_label}{item.interview_date ? ` · ${formatDate(item.interview_date)}` : ''}
							</span>
							<span class="item-job">
								{item.job_title}{item.company_name ? ` · ${item.company_name}` : ''}
							</span>
						</div>
					</div>
					<div class="item-days" class:stale={item.days_since >= STALE_DAYS}>
						{item.days_since}d waiting
					</div>
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
	.completed-interviews {
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

	.event-item {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0.625rem 0.75rem;
		background: var(--bg-tertiary);
		border-radius: var(--radius);
		border-left: 3px solid var(--accent-blue);
		text-decoration: none;
		color: inherit;
		cursor: pointer;
	}

	.event-item:hover {
		filter: brightness(1.08);
	}

	.event-item.stale {
		border-left-color: var(--accent-red);
	}

	.item-left {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		min-width: 0;
	}

	.item-type-badge {
		font-size: 0.625rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		padding: 0.125rem 0.375rem;
		border-radius: 3px;
		background: var(--bg-primary);
		color: var(--accent-blue);
		white-space: nowrap;
	}

	.item-details {
		display: flex;
		flex-direction: column;
		min-width: 0;
	}

	.item-description {
		font-size: 0.875rem;
		color: var(--text-primary);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.item-job {
		font-size: 0.75rem;
		color: var(--text-muted);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.item-days {
		font-size: 0.75rem;
		color: var(--text-secondary);
		white-space: nowrap;
		margin-left: 1rem;
		font-weight: 600;
	}

	.item-days.stale {
		color: var(--accent-red);
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

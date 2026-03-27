<script lang="ts">
	import type { DashboardActionItem } from '$lib/types';

	interface Props {
		items: DashboardActionItem[];
	}

	let { items }: Props = $props();

	let showAll = $state(false);
	const VISIBLE_LIMIT = 10;

	let visibleItems = $derived(showAll ? items : items.slice(0, VISIBLE_LIMIT));
	let hasMore = $derived(items.length > VISIBLE_LIMIT);

	function formatDate(dateStr: string | null): string {
		if (!dateStr) return 'No date';
		const date = new Date(dateStr);
		const now = new Date();
		const diffMs = date.getTime() - now.getTime();
		const diffDays = Math.round(diffMs / (1000 * 60 * 60 * 24));

		const formatted = date.toLocaleDateString('en-US', {
			month: 'short',
			day: 'numeric',
		});

		if (diffDays === 0) return 'Today';
		if (diffDays === 1) return 'Tomorrow';
		if (diffDays === -1) return 'Yesterday';
		if (diffDays < 0) return `${formatted} (${Math.abs(diffDays)}d ago)`;
		return `${formatted} (in ${diffDays}d)`;
	}
</script>

<div class="upcoming-events">
	<h2>Upcoming Events</h2>

	{#if items.length === 0}
		<p class="empty-state">No upcoming events scheduled.</p>
	{:else}
		<div class="items-list">
			{#each visibleItems as item}
				<div class="event-item" class:overdue={item.is_overdue}>
					<div class="item-left">
						<span class="item-type-badge">Interview</span>
						<div class="item-details">
							<span class="item-description">{item.description}</span>
							<span class="item-job">
								{item.job_title}{item.company_name ? ` · ${item.company_name}` : ''}
							</span>
						</div>
					</div>
					<div class="item-date" class:overdue={item.is_overdue}>
						{formatDate(item.date)}
					</div>
				</div>
			{/each}
		</div>

		{#if hasMore && !showAll}
			<button class="show-more" onclick={() => (showAll = true)}>
				Show all ({items.length} events)
			</button>
		{/if}
	{/if}
</div>

<style>
	.upcoming-events {
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
	}

	.event-item.overdue {
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

	.item-date {
		font-size: 0.75rem;
		color: var(--text-secondary);
		white-space: nowrap;
		margin-left: 1rem;
	}

	.item-date.overdue {
		color: var(--accent-red);
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

<script lang="ts">
	import type { DashboardActionItem } from '$lib/types';

	type Filter = 'today' | 'tomorrow' | 'this_week' | 'next_week' | 'all';

	interface Props {
		items: DashboardActionItem[];
	}

	let { items }: Props = $props();

	let filter = $state<Filter>('this_week');

	function startOfDay(d: Date): Date {
		return new Date(d.getFullYear(), d.getMonth(), d.getDate());
	}

	/** Parse date string as local time, not UTC */
	function parseDate(dateStr: string): Date {
		// Date-only strings ("2026-04-13") are parsed as UTC by default.
		// Append T00:00:00 to force local timezone interpretation.
		if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
			return new Date(dateStr + 'T00:00:00');
		}
		return new Date(dateStr);
	}

	function getEndOfWeek(): Date {
		const now = new Date();
		const day = now.getDay();
		// Days until Sunday (end of Mon-Sun week): Sunday=0 means 0, Mon=1 means 6, etc.
		const daysUntilSunday = day === 0 ? 0 : 7 - day;
		const end = startOfDay(now);
		end.setDate(end.getDate() + daysUntilSunday);
		return end;
	}

	let filteredItems = $derived.by(() => {
		if (filter === 'all') return items;

		const today = startOfDay(new Date());
		const tomorrow = new Date(today);
		tomorrow.setDate(tomorrow.getDate() + 1);

		return items.filter((item) => {
			if (!item.date) return false;
			const d = startOfDay(parseDate(item.date));

			if (filter === 'today') return d.getTime() === today.getTime();
			if (filter === 'tomorrow') return d.getTime() === tomorrow.getTime();
			const endOfWeek = getEndOfWeek();
			if (filter === 'this_week') return d >= today && d <= endOfWeek;
			// next_week: Monday after this week's Sunday through the following Sunday
			const nextMonday = new Date(endOfWeek);
			nextMonday.setDate(nextMonday.getDate() + 1);
			const nextSunday = new Date(nextMonday);
			nextSunday.setDate(nextSunday.getDate() + 6);
			return d >= nextMonday && d <= nextSunday;
		});
	});

	let showAll = $state(false);
	const VISIBLE_LIMIT = 10;

	let visibleItems = $derived(showAll ? filteredItems : filteredItems.slice(0, VISIBLE_LIMIT));
	let hasMore = $derived(filteredItems.length > VISIBLE_LIMIT);

	function formatDate(dateStr: string | null): string {
		if (!dateStr) return 'No date';
		const date = parseDate(dateStr);
		const now = new Date();
		const diffMs = startOfDay(date).getTime() - startOfDay(now).getTime();
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

	const filters: { key: Filter; label: string }[] = [
		{ key: 'today', label: 'Today' },
		{ key: 'tomorrow', label: 'Tomorrow' },
		{ key: 'this_week', label: 'This Week' },
		{ key: 'next_week', label: 'Next Week' },
		{ key: 'all', label: 'All' },
	];
</script>

<div class="upcoming-events">
	<div class="header">
		<h2>Upcoming Events</h2>
		<div class="filters">
			{#each filters as f}
				<button
					class="filter-btn"
					class:active={filter === f.key}
					onclick={() => { filter = f.key; showAll = false; }}
				>
					{f.label}
				</button>
			{/each}
		</div>
	</div>

	{#if filteredItems.length === 0}
		<p class="empty-state">No upcoming events{filter !== 'all' ? ` ${filters.find(f => f.key === filter)?.label.toLowerCase()}` : ''}.</p>
	{:else}
		<div class="items-list">
			{#each visibleItems as item}
				<a class="event-item" class:overdue={item.is_overdue} href="/pipeline?entry={item.pipeline_entry_id}">
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
				</a>
			{/each}
		</div>

		{#if hasMore && !showAll}
			<button class="show-more" onclick={() => (showAll = true)}>
				Show all ({filteredItems.length} events)
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

	.header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 1rem;
	}

	h2 {
		font-size: 1rem;
		font-weight: 600;
		color: var(--text-primary);
		margin-bottom: 0;
	}

	.filters {
		display: flex;
		gap: 0.25rem;
	}

	.filter-btn {
		font-size: 0.6875rem;
		padding: 0.25rem 0.5rem;
		border-radius: 4px;
		border: 1px solid var(--border-color);
		background: none;
		color: var(--text-secondary);
		cursor: pointer;
		transition: background 0.15s, color 0.15s, border-color 0.15s;
	}

	.filter-btn:hover {
		background: var(--bg-tertiary);
		color: var(--text-primary);
	}

	.filter-btn.active {
		background: var(--accent-blue);
		color: #fff;
		border-color: var(--accent-blue);
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

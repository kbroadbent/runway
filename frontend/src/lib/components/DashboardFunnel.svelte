<script lang="ts">
	import { onMount } from 'svelte';
	import { dashboard as dashboardApi } from '$lib/api';
	import type { FunnelResponse } from '$lib/types';
	import SankeyChart from './SankeyChart.svelte';

	type DateRange = '30d' | '90d' | 'all';

	let dateRange = $state<DateRange>('all');
	let data = $state<FunnelResponse | null>(null);
	let loading = $state(true);
	let error = $state<string | null>(null);

	function getDateParams(range: DateRange): { start?: string; end?: string } {
		if (range === 'all') return {};
		const now = new Date();
		const days = range === '30d' ? 30 : 90;
		const start = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);
		return { start: start.toISOString() };
	}

	async function fetchFunnel(range: DateRange) {
		loading = true;
		error = null;
		try {
			data = await dashboardApi.funnel(getDateParams(range));
		} catch {
			error = 'Failed to load funnel data';
		} finally {
			loading = false;
		}
	}

	onMount(() => {
		fetchFunnel(dateRange);
	});

	function handleFilterChange(range: DateRange) {
		dateRange = range;
		fetchFunnel(range);
	}

	const ranges: { value: DateRange; label: string }[] = [
		{ value: '30d', label: '30d' },
		{ value: '90d', label: '90d' },
		{ value: 'all', label: 'All time' },
	];
</script>

<section class="funnel-section">
	<div class="funnel-header">
		<div class="funnel-title">
			<h2>Job Search Funnel</h2>
			<span class="funnel-subtitle">Gray links show stage progression, colored links show outcomes</span>
		</div>
		<div class="date-filter">
			{#each ranges as range}
				<button
					class="filter-btn"
					class:active={dateRange === range.value}
					onclick={() => handleFilterChange(range.value)}
				>
					{range.label}
				</button>
			{/each}
		</div>
	</div>

	<div class="funnel-body">
		{#if loading}
			<div class="funnel-placeholder">Loading...</div>
		{:else if error}
			<div class="funnel-placeholder">{error}</div>
		{:else if data && data.transitions.length === 0}
			<div class="funnel-placeholder">No pipeline data yet — add postings and move them through stages to see your funnel.</div>
		{:else if data}
			<div class="chart-container">
				<SankeyChart {data} />
			</div>
		{/if}
	</div>
</section>

<style>
	.funnel-section {
		background: var(--bg-secondary);
		border: 1px solid var(--border-color);
		border-radius: var(--radius);
		padding: 1.25rem;
	}

	.funnel-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		margin-bottom: 1rem;
	}

	.funnel-title h2 {
		font-size: 1rem;
		font-weight: 600;
		color: var(--text-primary);
		margin: 0;
	}

	.funnel-subtitle {
		font-size: 0.75rem;
		color: var(--text-muted);
	}

	.date-filter {
		display: flex;
		gap: 0;
		border: 1px solid var(--border-color);
		border-radius: var(--radius);
		overflow: hidden;
	}

	.filter-btn {
		padding: 0.25rem 0.75rem;
		font-size: 0.75rem;
		background: transparent;
		color: var(--text-secondary);
		border: none;
		border-right: 1px solid var(--border-color);
		cursor: pointer;
		transition: background 0.15s, color 0.15s;
	}

	.filter-btn:last-child {
		border-right: none;
	}

	.filter-btn:hover {
		background: var(--bg-tertiary);
	}

	.filter-btn.active {
		background: var(--accent-blue);
		color: white;
	}

	.funnel-body {
		min-height: 200px;
	}

	.funnel-placeholder {
		display: flex;
		align-items: center;
		justify-content: center;
		min-height: 200px;
		color: var(--text-muted);
		font-size: 0.875rem;
	}

	.chart-container {
		width: 100%;
		min-height: 300px;
	}
</style>

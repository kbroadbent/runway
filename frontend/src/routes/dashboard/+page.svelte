<script lang="ts">
	import { onMount } from 'svelte';
	import type { DashboardResponse } from '$lib/types';
	import { dashboard as dashboardApi } from '$lib/api';
	import DashboardLaneCounts from '$lib/components/DashboardLaneCounts.svelte';
	import DashboardUpcomingEvents from '$lib/components/DashboardUpcomingEvents.svelte';
	import DashboardCompletedInterviews from '$lib/components/DashboardCompletedInterviews.svelte';
	import DashboardActionItems from '$lib/components/DashboardActionItems.svelte';
	import DashboardClosedPostings from '$lib/components/DashboardClosedPostings.svelte';
	import DashboardStaleEntries from '$lib/components/DashboardStaleEntries.svelte';
	import DashboardFunnel from '$lib/components/DashboardFunnel.svelte';

	let data = $state<DashboardResponse | null>(null);
	let error = $state<string | null>(null);
	let loading = $state(true);

	onMount(async () => {
		try {
			data = await dashboardApi.get();
		} catch (e) {
			error = 'Failed to load dashboard';
		} finally {
			loading = false;
		}
	});
</script>

{#if loading}
	<p>Loading...</p>
{:else if error}
	<p>{error}</p>
{:else if data}
	<h1>Dashboard</h1>

	{#if Object.keys(data.lane_counts).length === 0}
		<p class="empty-state">No jobs yet. <a href="/search">Find or import jobs</a> to get started.</p>
	{:else}
		<div class="dashboard-grid">
			<DashboardLaneCounts laneCounts={data.lane_counts} />
			<DashboardFunnel />
			<DashboardActionItems items={data.action_items} />
			<DashboardUpcomingEvents items={data.upcoming_events} />
			<DashboardCompletedInterviews items={data.completed_interviews} />
			<DashboardStaleEntries items={data.stale_entries} />
			<DashboardClosedPostings items={data.closed_postings} />
		</div>
	{/if}
{/if}

<style>
	h1 {
		font-size: 1.5rem;
		font-weight: 700;
		margin-bottom: 1.25rem;
	}

	.empty-state {
		color: var(--text-secondary);
	}

	.dashboard-grid {
		display: flex;
		flex-direction: column;
		gap: 1.25rem;
	}
</style>

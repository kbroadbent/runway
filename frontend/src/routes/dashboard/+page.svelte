<script lang="ts">
	import { onMount } from 'svelte';
	import type { DashboardResponse } from '$lib/types';
	import { dashboard as dashboardApi } from '$lib/api';
	import DashboardLaneCounts from '$lib/components/DashboardLaneCounts.svelte';
	import DashboardActionItems from '$lib/components/DashboardActionItems.svelte';

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

	<div class="dashboard-grid">
		<DashboardLaneCounts laneCounts={data.lane_counts} />
		<DashboardActionItems items={data.action_items} />
	</div>
{/if}

<style>
	h1 {
		font-size: 1.5rem;
		font-weight: 700;
		margin-bottom: 1.25rem;
	}

	.dashboard-grid {
		display: flex;
		flex-direction: column;
		gap: 1.25rem;
	}
</style>

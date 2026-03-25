<script lang="ts">
	import { onMount } from 'svelte';
	import type { DashboardResponse, DashboardActionItem } from '$lib/types';

	let data = $state<DashboardResponse | null>(null);
	let error = $state<string | null>(null);
	let loading = $state(true);

	onMount(async () => {
		try {
			const resp = await fetch('http://localhost:8000/api/dashboard', {
				headers: { 'Content-Type': 'application/json' },
			});
			if (!resp.ok) {
				error = 'Failed to load dashboard';
				return;
			}
			data = await resp.json();
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

	<div class="lane-counts">
		{#each Object.entries(data.lane_counts) as [name, count]}
			<div class="lane">
				<span class="lane-name">{name}</span>
				<span class="lane-count">{count}</span>
			</div>
		{/each}
	</div>

	{#if data.action_items.length > 0}
		<div class="action-items">
			<h2>Action Items</h2>
			{#each data.action_items as item}
				<div class="action-item">
					<span class="job-title">{item.job_title}</span>
					{#if item.company_name}
						<span class="company">{item.company_name}</span>
					{/if}
					<span class="description">{item.description}</span>
				</div>
			{/each}
		</div>
	{/if}
{/if}

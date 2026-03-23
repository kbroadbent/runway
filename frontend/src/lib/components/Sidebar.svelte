<script lang="ts">
	import { page } from '$app/state';
	import { tierFilter, searchFilter } from '$lib/stores/pipelineFilters';

	const navItems = [
		{ href: '/search', label: 'Search' },
		{ href: '/pipeline', label: 'Pipeline' },
		{ href: '/postings', label: 'Saved Postings' },
		{ href: '/companies', label: 'Companies' },
	];

	$: onPipeline = page.url.pathname.startsWith('/pipeline');
</script>

<aside class="sidebar">
	<div class="sidebar-brand">Runway</div>
	<nav>
		{#each navItems as item}
			<a
				href={item.href}
				class="nav-link"
				class:active={page.url.pathname.startsWith(item.href)}
			>
				{item.label}
			</a>
			{#if item.href === '/pipeline' && onPipeline}
				<div class="pipeline-filters">
					<input
						class="filter-search"
						type="text"
						placeholder="Search…"
						bind:value={$searchFilter}
					/>
					<div class="tier-btns">
						<button
							class="tier-btn"
							class:tier-btn-all-active={$tierFilter === null}
							onclick={() => ($tierFilter = null)}
						>All</button>
						<button
							class="tier-btn tier-btn-1"
							class:active={$tierFilter === 1}
							onclick={() => ($tierFilter = $tierFilter === 1 ? null : 1)}
						>T1</button>
						<button
							class="tier-btn tier-btn-2"
							class:active={$tierFilter === 2}
							onclick={() => ($tierFilter = $tierFilter === 2 ? null : 2)}
						>T2</button>
						<button
							class="tier-btn tier-btn-3"
							class:active={$tierFilter === 3}
							onclick={() => ($tierFilter = $tierFilter === 3 ? null : 3)}
						>T3</button>
					</div>
				</div>
			{/if}
		{/each}
	</nav>
</aside>

<style>
	.sidebar {
		width: 200px;
		height: 100vh;
		position: fixed;
		top: 0;
		left: 0;
		background: var(--bg-secondary);
		border-right: 1px solid var(--border-color);
		display: flex;
		flex-direction: column;
		padding: 1rem 0;
	}

	.sidebar-brand {
		font-size: 1.25rem;
		font-weight: 800;
		color: var(--accent-blue);
		padding: 0 1rem 1rem;
		border-bottom: 1px solid var(--border-color);
		margin-bottom: 0.5rem;
	}

	nav {
		display: flex;
		flex-direction: column;
		gap: 0.125rem;
		padding: 0 0.5rem;
	}

	.nav-link {
		display: block;
		padding: 0.5rem 0.75rem;
		border-radius: var(--radius);
		color: var(--text-secondary);
		text-decoration: none;
		font-weight: 500;
		transition: background 0.15s, color 0.15s;
	}

	.nav-link:hover {
		background: var(--bg-tertiary);
		color: var(--text-primary);
		text-decoration: none;
	}

	.nav-link.active {
		background: var(--bg-tertiary);
		color: var(--accent-blue);
	}

	.pipeline-filters {
		padding: 0.5rem 0.5rem 0.25rem;
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
	}

	.filter-search {
		width: 100%;
		box-sizing: border-box;
		padding: 0.35rem 0.5rem;
		font-size: 0.8rem;
		background: var(--bg-tertiary);
		border: 1px solid var(--border-color);
		border-radius: var(--radius);
		color: var(--text-primary);
		outline: none;
	}

	.filter-search:focus {
		border-color: var(--accent-blue);
	}

	.tier-btns {
		display: flex;
		gap: 0.3rem;
	}

	.tier-btn {
		flex: 1;
		padding: 0.25rem 0;
		font-size: 0.75rem;
		font-weight: 600;
		border-radius: var(--radius);
		border: 1px solid var(--border-color);
		background: var(--bg-tertiary);
		color: var(--text-secondary);
		cursor: pointer;
		transition: background 0.15s, color 0.15s, border-color 0.15s;
	}

	.tier-btn:hover {
		background: var(--bg-secondary);
		color: var(--text-primary);
	}

	.tier-btn-all-active {
		background: var(--accent-blue);
		color: #fff;
		border-color: var(--accent-blue);
	}

	.tier-btn-1.active {
		background: color-mix(in srgb, #f59e0b 30%, transparent);
		color: #b45309;
		border-color: #f59e0b;
	}

	.tier-btn-2.active {
		background: color-mix(in srgb, #6b7280 30%, transparent);
		color: #374151;
		border-color: #9ca3af;
	}

	.tier-btn-3.active {
		background: color-mix(in srgb, #cd7c3a 30%, transparent);
		color: #92400e;
		border-color: #cd7c3a;
	}
</style>

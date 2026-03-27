<script lang="ts">
	import { page } from '$app/state';

	const navItems = [
		{ href: '/dashboard', label: 'Dashboard', exact: true },
		{ href: '/pipeline', label: 'Pipeline' },
		{ href: '/postings', label: 'Saved Postings' },
		{ href: '/search', label: 'Search' },
		{ href: '/companies', label: 'Companies' },
	];
</script>

<aside class="sidebar">
	<div class="sidebar-brand">Runway</div>
	<nav>
		{#each navItems as item}
			<a
				href={item.href}
				class="nav-link"
				class:active={item.exact ? page.url.pathname === item.href : page.url.pathname.startsWith(item.href)}
			>
				{item.label}
			</a>
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
</style>

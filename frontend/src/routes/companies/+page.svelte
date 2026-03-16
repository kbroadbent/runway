<script lang="ts">
	import type { Company } from '$lib/types';
	import { companies as companiesApi } from '$lib/api';
	import CompanyForm from '$lib/components/CompanyForm.svelte';
	import CompanyDetail from '$lib/components/CompanyDetail.svelte';
	import { onMount } from 'svelte';

	let allCompanies = $state<Company[]>([]);
	let selectedCompany = $state<Company | null>(null);
	let showForm = $state(false);
	let searchText = $state('');

	// Sort
	let sortKey = $state('name');
	let sortAsc = $state(true);

	onMount(loadCompanies);

	async function loadCompanies() {
		allCompanies = await companiesApi.list();
	}

	let filtered = $derived.by(() => {
		let list = allCompanies.filter((c) => {
			if (!searchText) return true;
			const q = searchText.toLowerCase();
			return (
				c.name.toLowerCase().includes(q) ||
				(c.industry ?? '').toLowerCase().includes(q)
			);
		});

		list.sort((a, b) => {
			let av: unknown, bv: unknown;
			switch (sortKey) {
				case 'name': av = a.name; bv = b.name; break;
				case 'industry': av = a.industry ?? ''; bv = b.industry ?? ''; break;
				case 'glassdoor_rating': av = a.glassdoor_rating ?? 0; bv = b.glassdoor_rating ?? 0; break;
				case 'employee_count': av = a.employee_count ?? 0; bv = b.employee_count ?? 0; break;
				default: av = a.name; bv = b.name;
			}
			if (av! < bv!) return sortAsc ? -1 : 1;
			if (av! > bv!) return sortAsc ? 1 : -1;
			return 0;
		});
		return list;
	});

	function handleSort(key: string) {
		if (sortKey === key) sortAsc = !sortAsc;
		else { sortKey = key; sortAsc = true; }
	}

	async function handleSave(data: Partial<Company>) {
		await companiesApi.create(data);
		showForm = false;
		await loadCompanies();
	}

	async function handleUpdated() {
		await loadCompanies();
		if (selectedCompany) {
			selectedCompany = allCompanies.find((c) => c.id === selectedCompany!.id) ?? selectedCompany;
		}
	}

	const columns = [
		{ key: 'name', label: 'Name' },
		{ key: 'industry', label: 'Industry' },
		{ key: 'glassdoor_rating', label: 'Glassdoor' },
		{ key: 'employee_count', label: 'Employees' },
	];
</script>

<div class="page-header">
	<h1>Companies</h1>
	<button class="btn btn-primary" onclick={() => (showForm = !showForm)}>
		{showForm ? 'Cancel' : 'Add Company'}
	</button>
</div>

{#if showForm}
	<CompanyForm onSave={handleSave} onCancel={() => (showForm = false)} />
{/if}

<div class="filters card" style="margin-bottom:1rem;padding:0.75rem">
	<input
		type="text"
		bind:value={searchText}
		placeholder="Search by name or industry..."
		style="width:100%;max-width:360px"
	/>
</div>

{#if filtered.length === 0}
	<p class="empty-state">No companies yet. They're created automatically when postings are imported.</p>
{:else}
	<div class="table-wrap">
		<table>
			<thead>
				<tr>
					{#each columns as col}
						<th class="sortable" onclick={() => handleSort(col.key)}>
							{col.label}
							{#if sortKey === col.key}<span class="sort-arrow">{sortAsc ? '↑' : '↓'}</span>{/if}
						</th>
					{/each}
				</tr>
			</thead>
			<tbody>
				{#each filtered as company}
					<tr class="company-row" onclick={() => (selectedCompany = company)}>
						<td class="company-name-cell">
							{company.name}
							{#if company.website}
								<a href={company.website} target="_blank" rel="noopener" onclick={(e) => e.stopPropagation()} class="website-link">↗</a>
							{/if}
						</td>
						<td>{company.industry ?? '-'}</td>
						<td>
							{#if company.glassdoor_rating}
								<span class="rating">{company.glassdoor_rating}★</span>
							{:else}
								-
							{/if}
						</td>
						<td>{company.employee_count ? company.employee_count.toLocaleString() : '-'}</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
{/if}

{#if selectedCompany}
	<CompanyDetail
		company={selectedCompany}
		onClose={() => (selectedCompany = null)}
		onUpdated={handleUpdated}
	/>
{/if}

<style>
	.table-wrap {
		overflow-x: auto;
	}

	.sortable {
		cursor: pointer;
		user-select: none;
	}

	.sortable:hover {
		color: var(--accent-blue);
	}

	.sort-arrow {
		margin-left: 0.25rem;
		font-size: 0.75rem;
	}

	.company-row {
		cursor: pointer;
		transition: background 0.1s;
	}

	.company-row:hover {
		background: var(--bg-tertiary);
	}

	.company-name-cell {
		font-weight: 500;
	}

	.website-link {
		margin-left: 0.35rem;
		font-size: 0.8rem;
		color: var(--text-muted);
	}

	.rating {
		color: var(--accent-yellow);
		font-weight: 600;
	}

	.empty-state {
		color: var(--text-muted);
		text-align: center;
		padding: 3rem;
	}
</style>

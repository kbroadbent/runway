<script lang="ts">
	import type { JobPosting, Company, PostingsFilter } from '$lib/types';
	import { postings as postingsApi, pipeline } from '$lib/api';
	import ImportModal from '$lib/components/ImportModal.svelte';
	import PostingDetailPanel from '$lib/components/PostingDetailPanel.svelte';
	import CompanyDetail from '$lib/components/CompanyDetail.svelte';
	import { onMount } from 'svelte';

	let allPostings = $state<JobPosting[]>([]);
	let selectedPosting = $state<JobPosting | null>(null);
	let selectedCompany = $state<Company | null>(null);
	let showImport = $state(false);
	let showDismissed = $state(false);
	let selected = $state<Set<number>>(new Set());

	// Filters
	let searchText = $state('');
	let sourceFilter = $state('');
	let remoteFilter = $state('');
	let tierFilter = $state<string>('');
	let salaryMinFilter = $state<number | undefined>(undefined);
	let salaryMaxFilter = $state<number | undefined>(undefined);

	// Sort
	let sortKey = $state('date_saved');
	let sortAsc = $state(false);

	let hideArchived = $state(true);

	onMount(loadPostings);

	async function loadPostings() {
		allPostings = await postingsApi.list(showDismissed ? 'dismissed' : 'saved');
	}

	let sources = $derived([...new Set(allPostings.map((p) => p.source))]);

	let filtered = $derived.by(() => {
		let list = allPostings.filter((p) => {
			if (searchText) {
				const q = searchText.toLowerCase();
				if (
					!p.title.toLowerCase().includes(q) &&
					!(p.company?.name ?? p.company_name ?? '').toLowerCase().includes(q) &&
					!(p.location ?? '').toLowerCase().includes(q)
				)
					return false;
			}
			if (sourceFilter && p.source !== sourceFilter) return false;
			if (remoteFilter && p.remote_type !== remoteFilter) return false;
			if (tierFilter === 'none' && p.tier !== null) return false;
			if (tierFilter && tierFilter !== 'none' && p.tier !== Number(tierFilter)) return false;
			if (salaryMinFilter && (p.salary_max ?? 0) < salaryMinFilter) return false;
			if (salaryMaxFilter && (p.salary_min ?? Infinity) > salaryMaxFilter) return false;
			if (hideArchived && p.pipeline_stage === 'archived') return false;
			return true;
		});

		list.sort((a, b) => {
			let av: unknown, bv: unknown;
			switch (sortKey) {
				case 'title': av = a.title; bv = b.title; break;
				case 'company': av = a.company?.name ?? a.company_name ?? ''; bv = b.company?.name ?? b.company_name ?? ''; break;
				case 'location': av = a.location ?? ''; bv = b.location ?? ''; break;
				case 'salary': av = a.salary_min ?? 0; bv = b.salary_min ?? 0; break;
				case 'tier': av = a.tier ?? 99; bv = b.tier ?? 99; break;
				case 'source': av = a.source; bv = b.source; break;
				case 'pipeline_stage': av = a.pipeline_stage ?? ''; bv = b.pipeline_stage ?? ''; break;
				default: av = a.date_saved; bv = b.date_saved;
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

	function toggleSelect(id: number) {
		const next = new Set(selected);
		if (next.has(id)) next.delete(id);
		else next.add(id);
		selected = next;
	}

	function toggleSelectAll() {
		if (selected.size === filtered.length) selected = new Set();
		else selected = new Set(filtered.map((p) => p.id));
	}

	async function addToPipeline(posting: JobPosting, e: MouseEvent) {
		e.stopPropagation();
		await pipeline.add({ job_posting_id: posting.id });
		await loadPostings();
	}

	async function setTier(posting: JobPosting, e: Event) {
		e.stopPropagation();
		const val = (e.target as HTMLSelectElement).value;
		const tier = val === '' ? null : Number(val);
		await postingsApi.update(posting.id, { tier });
		posting.tier = tier;
		allPostings = allPostings; // trigger reactivity
	}

	async function deleteSelected() {
		if (!confirm(`Delete ${selected.size} posting(s)?`)) return;
		await Promise.all([...selected].map((id) => postingsApi.delete(id)));
		selected = new Set();
		await loadPostings();
	}

	async function undismissSelected() {
		await Promise.all([...selected].map((id) => postingsApi.save(id)));
		selected = new Set();
		await loadPostings();
	}

	function formatSalary(min: number | null, max: number | null): string {
		if (!min && !max) return '-';
		const fmt = (n: number) => '$' + Math.round(n / 1000) + 'k';
		if (min && max) return `${fmt(min)}–${fmt(max)}`;
		if (min) return `${fmt(min)}+`;
		return `≤${fmt(max!)}`;
	}

	const columns = [
		{ key: 'title', label: 'Title' },
		{ key: 'company', label: 'Company' },
		{ key: 'location', label: 'Location' },
		{ key: 'salary', label: 'Salary' },
		{ key: 'tier', label: 'Tier' },
		{ key: 'source', label: 'Source' },
		{ key: 'pipeline_stage', label: 'Pipeline' },
		{ key: 'date_saved', label: 'Saved' },
	];
</script>

<div class="page-header">
	<h1>{showDismissed ? 'Dismissed Postings' : 'Saved Postings'}</h1>
	<div style="display: flex; gap: 0.5rem;">
		<button class="btn btn-secondary" onclick={async () => { showDismissed = !showDismissed; selected = new Set(); await loadPostings(); }}>
			{showDismissed ? 'View Saved' : 'View Dismissed'}
		</button>
		{#if !showDismissed}
			<button class="btn btn-primary" onclick={() => (showImport = true)}>Import Posting</button>
		{/if}
	</div>
</div>

<!-- Filters -->
<div class="filters card">
	<input type="text" bind:value={searchText} placeholder="Search title, company, location..." />
	<select bind:value={sourceFilter}>
		<option value="">All sources</option>
		{#each sources as src}
			<option value={src}>{src}</option>
		{/each}
	</select>
	<select bind:value={remoteFilter}>
		<option value="">Any remote</option>
		<option value="remote">Remote</option>
		<option value="hybrid">Hybrid</option>
		<option value="onsite">Onsite</option>
	</select>
	<select bind:value={tierFilter}>
		<option value="">Any tier</option>
		<option value="1">Tier 1</option>
		<option value="2">Tier 2</option>
		<option value="3">Tier 3</option>
		<option value="none">Untiered</option>
	</select>
	<input type="number" bind:value={salaryMinFilter} placeholder="Min salary" style="width: 120px" />
	<input type="number" bind:value={salaryMaxFilter} placeholder="Max salary" style="width: 120px" />
	<label class="filter-checkbox">
		<input type="checkbox" bind:checked={hideArchived} />
		Hide archived
	</label>
</div>

{#if selected.size > 0}
	<div class="bulk-actions">
		<span>{selected.size} selected</span>
		{#if showDismissed}
			<button class="btn btn-sm btn-primary" onclick={undismissSelected}>Undismiss Selected</button>
		{/if}
		<button class="btn btn-sm btn-danger" onclick={deleteSelected}>Delete Selected</button>
		<button class="btn btn-sm btn-secondary" onclick={() => (selected = new Set())}>Clear</button>
	</div>
{/if}

<div class="table-wrap">
	{#if filtered.length === 0}
		<p class="empty-state">No postings found. Import one or run a search.</p>
	{:else}
		<table>
			<thead>
				<tr>
					<th>
						<input
							type="checkbox"
							checked={selected.size === filtered.length && filtered.length > 0}
							onchange={toggleSelectAll}
						/>
					</th>
					{#each columns as col}
						<th class="sortable" onclick={() => handleSort(col.key)}>
							{col.label}
							{#if sortKey === col.key}<span class="sort-arrow">{sortAsc ? '↑' : '↓'}</span>{/if}
						</th>
					{/each}
				</tr>
			</thead>
			<tbody>
				{#each filtered as posting}
					<tr
						class="posting-row"
						class:row-selected={selected.has(posting.id)}
						onclick={() => (selectedPosting = posting)}
					>
						<td onclick={(e) => { e.stopPropagation(); toggleSelect(posting.id); }}>
							<input type="checkbox" checked={selected.has(posting.id)} onchange={() => toggleSelect(posting.id)} />
						</td>
						<td>{posting.title}</td>
						<td>
							{#if posting.company}
								<button class="company-link" onclick={(e) => { e.stopPropagation(); selectedCompany = posting.company; }}>
									{posting.company.name}
								</button>
							{:else}
								{posting.company_name ?? '-'}
							{/if}
						</td>
						<td>{posting.location ?? '-'}</td>
						<td>{formatSalary(posting.salary_min, posting.salary_max)}</td>
						<td onclick={(e) => e.stopPropagation()}>
							<select class="tier-select tier-val-{posting.tier ?? 0}" value={posting.tier ?? ''} onchange={(e) => setTier(posting, e)}>
								<option value="">—</option>
								<option value={1}>T1</option>
								<option value={2}>T2</option>
								<option value={3}>T3</option>
							</select>
						</td>
						<td><span class="badge badge-stage">{posting.source}</span></td>
						<td>
							{#if posting.pipeline_stage}
								<span class="badge badge-stage">{posting.pipeline_stage}</span>
							{:else}
								<button class="btn btn-xs btn-secondary" onclick={(e) => addToPipeline(posting, e)}>
									+ Pipeline
								</button>
							{/if}
						</td>
						<td>{new Date(posting.date_saved).toLocaleDateString()}</td>
					</tr>
				{/each}
			</tbody>
		</table>
	{/if}
</div>

{#if showImport}
	<ImportModal
		onClose={() => (showImport = false)}
		onSaved={async () => { await loadPostings(); }}
	/>
{/if}

{#if selectedCompany}
	<CompanyDetail
		company={selectedCompany}
		onClose={() => (selectedCompany = null)}
		onUpdated={loadPostings}
	/>
{/if}

{#if selectedPosting}
	<PostingDetailPanel
		posting={selectedPosting}
		onClose={() => (selectedPosting = null)}
		onDeleted={async () => { await loadPostings(); selectedPosting = null; }}
		onUpdated={async () => { await loadPostings(); }}
	/>
{/if}

<style>
	.filters {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
		align-items: center;
		margin-bottom: 1rem;
		padding: 0.75rem;
	}

	.filters input[type='text'],
	.filters select {
		flex: 1;
		min-width: 140px;
	}

	.bulk-actions {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-bottom: 0.75rem;
		font-size: 0.9rem;
		color: var(--text-secondary);
	}

	.table-wrap {
		overflow-x: auto;
	}

	.company-link {
		background: none;
		border: none;
		padding: 0;
		color: inherit;
		cursor: pointer;
		font-size: inherit;
		font-family: inherit;
		text-decoration: none;
	}

	.company-link:hover {
		text-decoration: underline;
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

	.posting-row {
		cursor: pointer;
		transition: background 0.1s;
	}

	.posting-row:hover {
		background: var(--bg-tertiary);
	}

	.row-selected {
		background: color-mix(in srgb, var(--accent-blue) 10%, transparent);
	}

	.text-muted {
		color: var(--text-muted);
	}

	.empty-state {
		color: var(--text-muted);
		text-align: center;
		padding: 3rem;
	}

	.btn-xs {
		padding: 0.15rem 0.5rem;
		font-size: 0.75rem;
	}

	.filter-checkbox {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		font-size: 0.9rem;
		color: var(--text-secondary);
		cursor: pointer;
		white-space: nowrap;
	}

	.tier-select {
		font-size: 0.8rem;
		padding: 0.1rem 0.25rem;
		border-radius: var(--radius);
		border: 1px solid var(--border-color);
		background: var(--bg-tertiary);
		color: var(--text-primary);
		width: 52px;
	}

	.tier-val-1 { background: color-mix(in srgb, #f59e0b 20%, transparent); color: #b45309; border-color: #f59e0b; }
	.tier-val-2 { background: color-mix(in srgb, #6b7280 20%, transparent); color: #4b5563; border-color: #9ca3af; }
	.tier-val-3 { background: color-mix(in srgb, #cd7c3a 20%, transparent); color: #92400e; border-color: #cd7c3a; }

	.tier-badge {
		font-weight: 700;
		font-size: 0.75rem;
	}

	.tier-1 {
		background: color-mix(in srgb, #f59e0b 20%, transparent);
		color: #b45309;
		border: 1px solid #f59e0b;
	}

	.tier-2 {
		background: color-mix(in srgb, #6b7280 20%, transparent);
		color: #4b5563;
		border: 1px solid #9ca3af;
	}

	.tier-3 {
		background: color-mix(in srgb, #cd7c3a 20%, transparent);
		color: #92400e;
		border: 1px solid #cd7c3a;
	}
</style>

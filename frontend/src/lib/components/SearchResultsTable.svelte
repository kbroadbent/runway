<script lang="ts">
	import type { JobPosting } from '$lib/types';

	interface Props {
		results: JobPosting[];
		onSavePosting?: (posting: JobPosting) => void;
		onAddToPipeline?: (posting: JobPosting) => void;
	}

	let { results, onSavePosting, onAddToPipeline }: Props = $props();

	let expandedId = $state<number | null>(null);
	let sortKey = $state<string>('date_posted');
	let sortAsc = $state(false);

	function toggleExpand(id: number) {
		expandedId = expandedId === id ? null : id;
	}

	function handleSort(key: string) {
		if (sortKey === key) {
			sortAsc = !sortAsc;
		} else {
			sortKey = key;
			sortAsc = true;
		}
	}

	function formatSalary(min: number | null, max: number | null): string {
		if (!min && !max) return '-';
		const fmt = (n: number) => '$' + n.toLocaleString();
		if (min && max) return `${fmt(min)} - ${fmt(max)}`;
		if (min) return `${fmt(min)}+`;
		return `up to ${fmt(max!)}`;
	}

	let sortedResults = $derived.by(() => {
		const copy = [...results];
		copy.sort((a, b) => {
			let aVal: unknown, bVal: unknown;
			switch (sortKey) {
				case 'title':
					aVal = a.title;
					bVal = b.title;
					break;
				case 'company':
					aVal = a.company?.name ?? '';
					bVal = b.company?.name ?? '';
					break;
				case 'location':
					aVal = a.location ?? '';
					bVal = b.location ?? '';
					break;
				case 'salary':
					aVal = a.salary_min ?? 0;
					bVal = b.salary_min ?? 0;
					break;
				case 'source':
					aVal = a.source;
					bVal = b.source;
					break;
				case 'date_posted':
					aVal = a.date_posted ?? '';
					bVal = b.date_posted ?? '';
					break;
				default:
					return 0;
			}
			if (aVal! < bVal!) return sortAsc ? -1 : 1;
			if (aVal! > bVal!) return sortAsc ? 1 : -1;
			return 0;
		});
		return copy;
	});

	const columns = [
		{ key: 'title', label: 'Title' },
		{ key: 'company', label: 'Company' },
		{ key: 'location', label: 'Location' },
		{ key: 'salary', label: 'Salary' },
		{ key: 'source', label: 'Source' },
		{ key: 'date_posted', label: 'Date' },
	];
</script>

{#if results.length === 0}
	<p class="empty-state">No results yet. Run a search to see postings.</p>
{:else}
	<div class="table-wrap">
		<table>
			<thead>
				<tr>
					{#each columns as col}
						<th class="sortable" onclick={() => handleSort(col.key)}>
							{col.label}
							{#if sortKey === col.key}
								<span class="sort-arrow">{sortAsc ? '↑' : '↓'}</span>
							{/if}
						</th>
					{/each}
					<th>Actions</th>
				</tr>
			</thead>
			<tbody>
				{#each sortedResults as posting}
					<tr class="result-row" onclick={() => toggleExpand(posting.id)}>
						<td>{posting.title}</td>
						<td>{posting.company?.name ?? '-'}</td>
						<td>{posting.location ?? '-'}</td>
						<td>{formatSalary(posting.salary_min, posting.salary_max)}</td>
						<td><span class="badge badge-stage">{posting.source}</span></td>
						<td>{posting.date_posted ? new Date(posting.date_posted).toLocaleDateString() : '-'}</td>
						<td class="actions" onclick={(e) => e.stopPropagation()}>
							{#if onAddToPipeline}
								<button class="btn btn-sm btn-primary" onclick={() => onAddToPipeline(posting)}>
									+ Pipeline
								</button>
							{/if}
						</td>
					</tr>
					{#if expandedId === posting.id}
						<tr class="expanded-row">
							<td colspan="7">
								<div class="description-panel">
									{#if posting.url}
										<p><a href={posting.url} target="_blank" rel="noopener">View original posting</a></p>
									{/if}
									<div class="description-text">
										{posting.description ?? 'No description available.'}
									</div>
								</div>
							</td>
						</tr>
					{/if}
				{/each}
			</tbody>
		</table>
	</div>
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

	.result-row {
		cursor: pointer;
		transition: background 0.1s;
	}

	.result-row:hover {
		background: var(--bg-tertiary);
	}

	.expanded-row td {
		background: var(--bg-secondary);
		padding: 1rem;
	}

	.description-panel {
		max-height: 300px;
		overflow-y: auto;
	}

	.description-text {
		margin-top: 0.5rem;
		white-space: pre-wrap;
		font-size: 0.9rem;
		color: var(--text-secondary);
		line-height: 1.6;
	}

	.actions {
		white-space: nowrap;
	}

	.empty-state {
		color: var(--text-muted);
		text-align: center;
		padding: 2rem;
	}
</style>

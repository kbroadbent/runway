<script lang="ts">
	import type { JobPosting } from '$lib/types';
	import JobDetailModal from '$lib/components/JobDetailModal.svelte';

	interface Props {
		results: JobPosting[];
		onSave?: (posting: JobPosting) => void;
		onDismiss?: (posting: JobPosting) => void;
		onAddToPipeline?: (posting: JobPosting) => void;
	}

	let { results, onSave, onDismiss, onAddToPipeline }: Props = $props();

	let selectedPosting = $state<JobPosting | null>(null);
	let sortKey = $state<string>('date_posted');
	let sortAsc = $state(false);

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
					<tr class="result-row" onclick={() => selectedPosting = posting}>
						<td>{posting.title}</td>
						<td>{posting.company?.name ?? '-'}</td>
						<td>{posting.location ?? '-'}</td>
						<td>{formatSalary(posting.salary_min, posting.salary_max)}</td>
						<td><span class="badge badge-stage">{posting.source}</span></td>
						<td>{posting.date_posted ? new Date(posting.date_posted).toLocaleDateString() : '-'}</td>
						<td class="actions" onclick={(e) => e.stopPropagation()}>
							{#if onSave}
								<button class="btn btn-sm btn-primary" onclick={() => onSave(posting)}>Save</button>
							{/if}
							{#if onAddToPipeline}
								<button class="btn btn-sm btn-secondary" onclick={() => onAddToPipeline(posting)}>+ Pipeline</button>
							{/if}
							{#if onDismiss}
								<button class="btn btn-sm btn-danger" onclick={() => onDismiss(posting)}>Dismiss</button>
							{/if}
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
{/if}

<JobDetailModal
	posting={selectedPosting}
	onClose={() => selectedPosting = null}
	onAddToPipeline={onAddToPipeline}
/>

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

	.actions {
		white-space: nowrap;
	}

	.empty-state {
		color: var(--text-muted);
		text-align: center;
		padding: 2rem;
	}
</style>

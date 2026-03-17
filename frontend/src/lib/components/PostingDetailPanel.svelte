<script lang="ts">
	import type { JobPosting } from '$lib/types';
	import { postings, pipeline } from '$lib/api';
	import { marked } from 'marked';
	import DOMPurify from 'dompurify';

	function renderMarkdown(text: string): string {
		const html = marked.parse(text, { async: false }) as string;
		return DOMPurify.sanitize(html);
	}

	interface Props {
		posting: JobPosting;
		onClose: () => void;
		onDeleted: () => void;
		onUpdated: () => void;
	}

	let { posting, onClose, onDeleted, onUpdated }: Props = $props();

	let deleting = $state(false);
	let addingToPipeline = $state(false);
	let savingCompany = $state(false);
	let status = $state('');

	function formatSalary(min: number | null, max: number | null): string {
		if (!min && !max) return 'Not specified';
		const fmt = (n: number) => '$' + n.toLocaleString();
		if (min && max) return `${fmt(min)} – ${fmt(max)}`;
		if (min) return `${fmt(min)}+`;
		return `up to ${fmt(max!)}`;
	}

	async function handleDelete() {
		if (!confirm(`Delete "${posting.title}"?`)) return;
		deleting = true;
		try {
			await postings.delete(posting.id);
			onDeleted();
			onClose();
		} catch (e) {
			status = e instanceof Error ? e.message : 'Delete failed';
			deleting = false;
		}
	}

	async function handleSaveCompany() {
		savingCompany = true;
		try {
			await postings.linkCompany(posting.id);
			onUpdated();
		} catch (e) {
			status = e instanceof Error ? e.message : 'Failed to save company';
		} finally {
			savingCompany = false;
		}
	}

	async function handleAddToPipeline() {
		addingToPipeline = true;
		try {
			await pipeline.add({ job_posting_id: posting.id });
			status = 'Added to pipeline!';
			onUpdated();
		} catch (e) {
			status = e instanceof Error ? e.message : 'Failed to add to pipeline';
		} finally {
			addingToPipeline = false;
		}
	}
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div class="panel-backdrop" onclick={onClose} onkeydown={(e) => e.key === 'Escape' && onClose()}>
	<div class="panel" onclick={(e) => e.stopPropagation()}>
		<div class="panel-header">
			<div class="panel-title-block">
				<h2>{posting.title}</h2>
				{#if posting.company || posting.company_name}
					<span class="company-name">{posting.company?.name ?? posting.company_name}</span>
				{/if}
			</div>
			<button class="close-btn" onclick={onClose}>✕</button>
		</div>

		<div class="panel-meta">
			{#if posting.location}
				<span class="meta-item">📍 {posting.location}</span>
			{/if}
			{#if posting.remote_type}
				<span class="badge badge-stage">{posting.remote_type}</span>
			{/if}
			<span class="meta-item">💰 {formatSalary(posting.salary_min, posting.salary_max)}</span>
			<span class="meta-item">🔗 {posting.source}</span>
			{#if posting.pipeline_stage}
				<span class="badge badge-stage">{posting.pipeline_stage}</span>
			{/if}
		</div>

		{#if posting.url}
			<a href={posting.url} target="_blank" rel="noopener" class="view-link">View Original Posting ↗</a>
		{/if}

		{#if posting.company}
			<div class="section">
				<h3>Company</h3>
				<div class="company-links">
					{#if posting.company.website}
						<a href={posting.company.website} target="_blank" rel="noopener" class="btn btn-sm btn-secondary">Website ↗</a>
					{/if}
					{#if posting.company.glassdoor_url}
						<a href={posting.company.glassdoor_url} target="_blank" rel="noopener" class="btn btn-sm btn-secondary">
							Glassdoor {posting.company.glassdoor_rating ? `(${posting.company.glassdoor_rating}★)` : '↗'}
						</a>
					{/if}
					{#if posting.company.levels_url}
						<a href={posting.company.levels_url} target="_blank" rel="noopener" class="btn btn-sm btn-secondary">Levels.fyi ↗</a>
					{/if}
					{#if posting.company.blind_url}
						<a href={posting.company.blind_url} target="_blank" rel="noopener" class="btn btn-sm btn-secondary">Blind ↗</a>
					{/if}
				</div>
				{#if posting.company.industry || posting.company.employee_count}
					<p class="company-detail">
						{#if posting.company.industry}{posting.company.industry}{/if}
						{#if posting.company.employee_count} · {posting.company.employee_count.toLocaleString()} employees{/if}
					</p>
				{/if}
			</div>
		{/if}
		{#if !posting.company && posting.company_name}
			<div class="section">
				<h3>Company</h3>
				<div class="company-unlinked">
					<span>{posting.company_name}</span>
					<button class="btn btn-sm btn-secondary" onclick={handleSaveCompany} disabled={savingCompany}>
						{savingCompany ? 'Saving...' : 'Save Company'}
					</button>
				</div>
			</div>
		{/if}

		{#if posting.description}
			<div class="section">
				<h3>Description</h3>
				<div class="description-text">{@html renderMarkdown(posting.description)}</div>
			</div>
		{/if}

		{#if status}
			<p class="status-msg">{status}</p>
		{/if}

		<div class="panel-actions">
			{#if !posting.pipeline_stage}
				<button class="btn btn-primary" onclick={handleAddToPipeline} disabled={addingToPipeline}>
					{addingToPipeline ? 'Adding...' : '+ Add to Pipeline'}
				</button>
			{/if}
			<button class="btn btn-danger" onclick={handleDelete} disabled={deleting}>
				{deleting ? 'Deleting...' : 'Delete'}
			</button>
		</div>
	</div>
</div>

<style>
	.panel-backdrop {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.5);
		z-index: 100;
		display: flex;
		justify-content: flex-end;
	}

	.panel {
		width: 520px;
		max-width: 95vw;
		height: 100vh;
		overflow-y: auto;
		background: var(--bg-secondary);
		border-left: 1px solid var(--border-color);
		padding: 1.5rem;
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.panel-header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 1rem;
	}

	.panel-title-block h2 {
		font-size: 1.2rem;
		font-weight: 700;
		line-height: 1.3;
	}

	.company-name {
		color: var(--text-secondary);
		font-size: 0.95rem;
	}

	.close-btn {
		background: none;
		border: none;
		color: var(--text-secondary);
		font-size: 1rem;
		flex-shrink: 0;
	}

	.close-btn:hover {
		color: var(--text-primary);
	}

	.panel-meta {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
		align-items: center;
	}

	.meta-item {
		font-size: 0.9rem;
		color: var(--text-secondary);
	}

	.view-link {
		font-size: 0.9rem;
	}

	.section h3 {
		font-size: 0.85rem;
		font-weight: 600;
		color: var(--text-secondary);
		text-transform: uppercase;
		letter-spacing: 0.05em;
		margin-bottom: 0.5rem;
	}

	.company-links {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
		margin-bottom: 0.5rem;
	}

	.company-detail {
		font-size: 0.9rem;
		color: var(--text-secondary);
	}

	.company-unlinked {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		font-size: 0.9rem;
		color: var(--text-secondary);
	}

	.description-text {
		font-size: 0.9rem;
		color: var(--text-secondary);
		line-height: 1.7;
		max-height: 400px;
		overflow-y: auto;
	}

	.description-text :global(h1),
	.description-text :global(h2),
	.description-text :global(h3),
	.description-text :global(h4) {
		color: var(--text-primary);
		font-weight: 600;
		margin: 1rem 0 0.5rem;
	}

	.description-text :global(h1) { font-size: 1.1rem; }
	.description-text :global(h2) { font-size: 1rem; }
	.description-text :global(h3) { font-size: 0.95rem; }

	.description-text :global(p) {
		margin: 0.5rem 0;
	}

	.description-text :global(ul),
	.description-text :global(ol) {
		padding-left: 1.5rem;
		margin: 0.5rem 0;
	}

	.description-text :global(li) {
		margin: 0.25rem 0;
	}

	.description-text :global(strong) {
		color: var(--text-primary);
		font-weight: 600;
	}

	.description-text :global(a) {
		color: var(--accent-blue);
	}

	.description-text :global(code) {
		background: var(--bg-tertiary);
		padding: 0.1em 0.3em;
		border-radius: 3px;
		font-size: 0.85em;
	}

	.status-msg {
		color: var(--accent-green);
		font-size: 0.9rem;
	}

	.panel-actions {
		display: flex;
		gap: 0.5rem;
		margin-top: auto;
		padding-top: 1rem;
	}
</style>

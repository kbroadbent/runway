<script lang="ts">
	import type { JobPosting } from '$lib/types';
	import { marked } from 'marked';
	import DOMPurify from 'dompurify';

	interface Props {
		posting: JobPosting | null;
		onClose: () => void;
		onSave?: (posting: JobPosting) => void;
	}

	let { posting, onClose, onSave }: Props = $props();

	function formatSalary(min: number | null, max: number | null): string {
		if (!min && !max) return 'Not specified';
		const fmt = (n: number) => '$' + n.toLocaleString();
		if (min && max) return `${fmt(min)} – ${fmt(max)}`;
		if (min) return `${fmt(min)}+`;
		return `up to ${fmt(max!)}`;
	}

	function renderMarkdown(text: string): string {
		const html = marked.parse(text, { async: false }) as string;
		return DOMPurify.sanitize(html);
	}
</script>

{#if posting}
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div class="modal-backdrop" onclick={onClose} onkeydown={(e) => e.key === 'Escape' && onClose()}>
		<div class="modal" onclick={(e) => e.stopPropagation()}>
			<div class="modal-header">
				<div class="title-block">
					<h2>{posting.title}</h2>
					{#if posting.company || posting.company_name}
						<span class="company-name">{posting.company?.name ?? posting.company_name}</span>
					{/if}
				</div>
				<button class="close-btn" onclick={onClose}>✕</button>
			</div>

			<div class="modal-meta">
				{#if posting.location}
					<span class="meta-item">📍 {posting.location}</span>
				{/if}
				{#if posting.remote_type}
					<span class="badge badge-stage">{posting.remote_type}</span>
				{/if}
				<span class="meta-item">💰 {formatSalary(posting.salary_min, posting.salary_max)}</span>
				<span class="meta-item">🔗 {posting.source}</span>
				{#if posting.date_posted}
					<span class="meta-item">📅 {new Date(posting.date_posted).toLocaleDateString()}</span>
				{/if}
			</div>

			{#if posting.url}
				<a href={posting.url} target="_blank" rel="noopener" class="view-link">View Original Posting ↗</a>
			{/if}

			{#if posting.description}
				<div class="description">
					{@html renderMarkdown(posting.description)}
				</div>
			{:else}
				<p class="no-description">No description available.</p>
			{/if}

			{#if onSave}
				<div class="modal-actions">
					<button class="btn btn-primary" onclick={() => { onSave!(posting!); onClose(); }}>
						Save
					</button>
				</div>
			{/if}
		</div>
	</div>
{/if}

<style>
	.modal-backdrop {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.6);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 100;
	}

	.modal {
		background: var(--bg-secondary);
		border: 1px solid var(--border-color);
		border-radius: var(--radius);
		width: 720px;
		max-width: 95vw;
		max-height: 85vh;
		overflow-y: auto;
		padding: 1.5rem;
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.modal-header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 1rem;
	}

	.title-block h2 {
		font-size: 1.2rem;
		font-weight: 700;
		line-height: 1.3;
	}

	.company-name {
		display: block;
		color: var(--text-secondary);
		font-size: 0.95rem;
		margin-top: 0.2rem;
	}

	.close-btn {
		background: none;
		border: none;
		color: var(--text-secondary);
		font-size: 1rem;
		flex-shrink: 0;
		cursor: pointer;
		padding: 0.25rem;
	}

	.close-btn:hover {
		color: var(--text-primary);
	}

	.modal-meta {
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

	.description {
		font-size: 0.9rem;
		color: var(--text-secondary);
		line-height: 1.7;
		border-top: 1px solid var(--border-color);
		padding-top: 1rem;
	}

	.description :global(h1),
	.description :global(h2),
	.description :global(h3),
	.description :global(h4) {
		color: var(--text-primary);
		font-weight: 600;
		margin: 1rem 0 0.5rem;
	}

	.description :global(h1) { font-size: 1.1rem; }
	.description :global(h2) { font-size: 1rem; }
	.description :global(h3) { font-size: 0.95rem; }

	.description :global(p) {
		margin: 0.5rem 0;
	}

	.description :global(ul),
	.description :global(ol) {
		padding-left: 1.5rem;
		margin: 0.5rem 0;
	}

	.description :global(li) {
		margin: 0.25rem 0;
	}

	.description :global(strong) {
		color: var(--text-primary);
		font-weight: 600;
	}

	.description :global(a) {
		color: var(--accent-blue);
	}

	.description :global(code) {
		background: var(--bg-tertiary);
		padding: 0.1em 0.3em;
		border-radius: 3px;
		font-size: 0.85em;
	}

	.no-description {
		color: var(--text-muted);
		font-size: 0.9rem;
	}

	.modal-actions {
		display: flex;
		gap: 0.5rem;
		padding-top: 0.5rem;
		border-top: 1px solid var(--border-color);
	}
</style>

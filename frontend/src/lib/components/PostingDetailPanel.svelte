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
	let summarizing = $state(false);
	let status = $state('');

	let localPosting = $state({ ...posting });
	$effect(() => { localPosting = { ...posting }; });

	let editing = $state(false);
	let saving = $state(false);
	let editTitle = $state('');
	let editCompany = $state('');
	let editLocation = $state('');
	let editRemoteType = $state('');
	let editSalaryMin = $state<number | undefined>(undefined);
	let editSalaryMax = $state<number | undefined>(undefined);
	let editUrl = $state('');
	let editDescription = $state('');
	let editTier = $state<number | null>(null);

	function handleEditStart() {
		editTitle = localPosting.title;
		editCompany = localPosting.company?.name ?? '';
		editLocation = localPosting.location ?? '';
		editRemoteType = localPosting.remote_type ?? '';
		editSalaryMin = localPosting.salary_min ?? undefined;
		editSalaryMax = localPosting.salary_max ?? undefined;
		editUrl = localPosting.url ?? '';
		editDescription = localPosting.description ?? '';
		editTier = localPosting.tier ?? null;
		editing = true;
	}

	function handleCancel() {
		editing = false;
		status = '';
	}

	async function handleSave() {
		saving = true;
		status = '';
		try {
			const updated = await postings.update(localPosting.id, {
				title: editTitle,
				company_name: editCompany || undefined,
				location: editLocation || null,
				remote_type: editRemoteType || null,
				salary_min: editSalaryMin ?? null,
				salary_max: editSalaryMax ?? null,
				url: editUrl || null,
				description: editDescription || null,
			});
			localPosting = updated;
			editing = false;
			onUpdated();
		} catch (e) {
			status = e instanceof Error ? e.message : 'Save failed';
		} finally {
			saving = false;
		}
	}

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

	async function handleGenerateSummary() {
		summarizing = true;
		status = '';
		try {
			localPosting = await postings.summarize(localPosting.id);
			onUpdated();
		} catch (e) {
			status = e instanceof Error ? e.message : 'Failed to generate summary';
		} finally {
			summarizing = false;
		}
	}

	async function handleAddToPipeline() {
		addingToPipeline = true;
		try {
			const entry = await pipeline.add({ job_posting_id: posting.id });
			localPosting = { ...localPosting, pipeline_stage: entry.stage };
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
				<h2>{localPosting.title}</h2>
				{#if localPosting.company || localPosting.company_name}
					<span class="company-name">{localPosting.company?.name ?? localPosting.company_name}</span>
				{/if}
			</div>
			<div class="panel-header-actions">
				{#if !editing}
					<button class="btn btn-sm btn-secondary" onclick={handleEditStart}>Edit</button>
				{/if}
				<button class="close-btn" onclick={onClose}>✕</button>
			</div>
		</div>

		{#if editing}
			<div class="edit-form">
				<div class="form-group">
					<label>Title</label>
					<input type="text" bind:value={editTitle} style="width: 100%" />
				</div>
				<div class="form-row">
					<div class="form-group">
						<label>Company</label>
						<input type="text" bind:value={editCompany} style="width: 100%" />
					</div>
					<div class="form-group">
						<label>Location</label>
						<input type="text" bind:value={editLocation} style="width: 100%" />
					</div>
				</div>
				<div class="form-row">
					<div class="form-group">
						<label>Remote</label>
						<select bind:value={editRemoteType} style="width: 100%">
							<option value="">Unknown</option>
							<option value="remote">Remote</option>
							<option value="hybrid">Hybrid</option>
							<option value="onsite">Onsite</option>
						</select>
					</div>
					<div class="form-group">
						<label>Min Salary</label>
						<input type="number" bind:value={editSalaryMin} style="width: 100%" />
					</div>
					<div class="form-group">
						<label>Max Salary</label>
						<input type="number" bind:value={editSalaryMax} style="width: 100%" />
					</div>
				</div>
				<div class="form-group">
					<label>URL</label>
					<input type="url" bind:value={editUrl} style="width: 100%" />
				</div>
				<div class="form-group">
					<label>Description</label>
					<textarea bind:value={editDescription} rows={8} style="width: 100%"></textarea>
				</div>
				{#if status}
					<p class="status-msg error">{status}</p>
				{/if}
				<div class="panel-actions">
					<button class="btn btn-primary" onclick={handleSave} disabled={saving || !editTitle}>
						{saving ? 'Saving...' : 'Save'}
					</button>
					<button class="btn btn-secondary" onclick={handleCancel}>Cancel</button>
				</div>
			</div>
		{:else}
			<div class="panel-meta">
				<select
					class="tier-select"
					value={localPosting.tier ?? ''}
					onchange={async (e) => {
						const val = (e.target as HTMLSelectElement).value;
						const newTier = val === '' ? null : Number(val) as 1 | 2 | 3;
						const updated = await postings.update(localPosting.id, { tier: newTier });
						localPosting = updated;
						onUpdated();
					}}
				>
					<option value="">No tier</option>
					<option value={1}>Tier 1</option>
					<option value={2}>Tier 2</option>
					<option value={3}>Tier 3</option>
				</select>
				{#if localPosting.location}
					<span class="meta-item">📍 {localPosting.location}</span>
				{/if}
				{#if localPosting.remote_type}
					<span class="badge badge-stage">{localPosting.remote_type}</span>
				{/if}
				<span class="meta-item">💰 {formatSalary(localPosting.salary_min, localPosting.salary_max)}</span>
				<span class="meta-item">🔗 {localPosting.source}</span>
				{#if localPosting.pipeline_stage}
					<span class="badge badge-stage">{localPosting.pipeline_stage}</span>
				{/if}
			</div>

			{#if localPosting.url}
				<a href={localPosting.url} target="_blank" rel="noopener" class="view-link">View Original Posting ↗</a>
			{/if}

			{#if localPosting.company}
				<div class="section">
					<h3>Company</h3>
					<div class="company-links">
						{#if localPosting.company.website}
							<a href={localPosting.company.website} target="_blank" rel="noopener" class="btn btn-sm btn-secondary">Website ↗</a>
						{/if}
						{#if localPosting.company.glassdoor_url}
							<a href={localPosting.company.glassdoor_url} target="_blank" rel="noopener" class="btn btn-sm btn-secondary">
								Glassdoor {localPosting.company.glassdoor_rating ? `(${localPosting.company.glassdoor_rating}★)` : '↗'}
							</a>
						{/if}
						{#if localPosting.company.levels_url}
							<a href={localPosting.company.levels_url} target="_blank" rel="noopener" class="btn btn-sm btn-secondary">Levels.fyi ↗</a>
						{/if}
						{#if localPosting.company.blind_url}
							<a href={localPosting.company.blind_url} target="_blank" rel="noopener" class="btn btn-sm btn-secondary">Blind ↗</a>
						{/if}
					</div>
					{#if localPosting.company.industry || localPosting.company.employee_count}
						<p class="company-detail">
							{#if localPosting.company.industry}{localPosting.company.industry}{/if}
							{#if localPosting.company.employee_count} · {localPosting.company.employee_count.toLocaleString()} employees{/if}
						</p>
					{/if}
				</div>
			{/if}

			{#if !localPosting.company && localPosting.company_name}
				<div class="section">
					<h3>Company</h3>
					<div class="company-unlinked">
						<span>{localPosting.company_name}</span>
						<button class="btn btn-sm btn-secondary" onclick={handleSaveCompany} disabled={savingCompany}>
							{savingCompany ? 'Saving...' : 'Save Company'}
						</button>
					</div>
				</div>
			{/if}

			{#if localPosting.has_raw_content || localPosting.description}
				<div class="section">
					<h3>Description</h3>
					{#if localPosting.description}
						<div class="description-text">{@html renderMarkdown(localPosting.description)}</div>
					{/if}
					{#if localPosting.has_raw_content}
						<button class="btn btn-sm btn-secondary" onclick={handleGenerateSummary} disabled={summarizing}>
							{summarizing ? 'Generating…' : 'Generate Summary'}
						</button>
					{/if}
				</div>
			{/if}

			{#if status}
				<p class="status-msg">{status}</p>
			{/if}

			<div class="panel-actions">
				{#if !localPosting.pipeline_stage}
					<button class="btn btn-primary" onclick={handleAddToPipeline} disabled={addingToPipeline}>
						{addingToPipeline ? 'Adding...' : '+ Add to Pipeline'}
					</button>
				{/if}
				<button class="btn btn-danger" onclick={handleDelete} disabled={deleting}>
					{deleting ? 'Deleting...' : 'Delete'}
				</button>
			</div>
		{/if}
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

	.panel-header-actions {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		flex-shrink: 0;
	}

	.edit-form {
		display: flex;
		flex-direction: column;
		gap: 0;
	}

	.form-group {
		margin-bottom: 0.75rem;
	}

	.form-group label {
		display: block;
		font-size: 0.85rem;
		color: var(--text-secondary);
		margin-bottom: 0.25rem;
	}

	.form-row {
		display: flex;
		gap: 0.75rem;
	}

	.form-row .form-group {
		flex: 1;
	}

	.status-msg.error {
		color: var(--accent-red);
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

	.tier-select {
		font-size: 0.85rem;
		padding: 0.15rem 0.35rem;
		border-radius: var(--radius);
		border: 1px solid var(--border-color);
		background: var(--bg-tertiary);
		color: var(--text-primary);
		width: auto;
	}

	.tier-badge {
		font-weight: 700;
		font-size: 0.8rem;
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

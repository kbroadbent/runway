<script lang="ts">
	import type { ImportPreview } from '$lib/types';
	import { postings, pipeline, ApiError } from '$lib/api';

	interface Props {
		onClose: () => void;
		onSaved: () => void;
	}

	let { onClose, onSaved }: Props = $props();

	let tab = $state<'text' | 'url'>('url');
	let rawText = $state('');
	let rawUrl = $state('');
	let preview = $state<ImportPreview | null>(null);
	let parsing = $state(false);
	let saving = $state(false);
	let addToPipeline = $state(false);
	let error = $state('');
	let duplicateId = $state<number | null>(null);

	// Editable preview fields
	let title = $state('');
	let company_name = $state('');
	let location = $state('');
	let remote_type = $state('');
	let salary_min = $state<number | undefined>(undefined);
	let salary_max = $state<number | undefined>(undefined);
	let description = $state('');
	let url = $state('');

	function applyPreview(p: ImportPreview) {
		title = p.title ?? '';
		company_name = p.company_name ?? '';
		location = p.location ?? '';
		remote_type = p.remote_type ?? '';
		salary_min = p.salary_min ?? undefined;
		salary_max = p.salary_max ?? undefined;
		description = p.description ?? '';
		url = p.url ?? '';
	}

	async function handleParse() {
		parsing = true;
		error = '';
		try {
			const data = tab === 'text' ? { text: rawText } : { url: rawUrl };
			preview = await postings.importPreview(data);
			applyPreview(preview);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Parse failed';
		} finally {
			parsing = false;
		}
	}

	async function handleSave() {
		saving = true;
		error = '';
		duplicateId = null;
		try {
			const data: ImportPreview = {
				title,
				company_name,
				location,
				remote_type,
				salary_min: salary_min ?? null,
				salary_max: salary_max ?? null,
				description,
				url,
				raw_content: preview?.raw_content ?? null,
			};
			const saved = await postings.importConfirm(data);
			if (addToPipeline) {
				await pipeline.add({ job_posting_id: saved.id });
			}
			onSaved();
			onClose();
		} catch (e) {
			if (e instanceof ApiError && e.status === 409) {
				const data = e.data as { message?: string; existing_id?: number } | null;
				duplicateId = data?.existing_id ?? null;
				error = data?.message ?? 'Already imported';
			} else {
				error = e instanceof Error ? e.message : 'Save failed';
			}
		} finally {
			saving = false;
		}
	}
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div class="modal-backdrop" onclick={onClose} onkeydown={(e) => e.key === 'Escape' && onClose()}>
	<div class="modal" onclick={(e) => e.stopPropagation()}>
		<div class="modal-header">
			<h2>Import Job Posting</h2>
			<button class="close-btn" onclick={onClose}>✕</button>
		</div>

		<div class="tabs">
			<button class="tab" class:active={tab === 'url'} onclick={() => { tab = 'url'; preview = null; }}>
				Paste URL
			</button>
			<button class="tab" class:active={tab === 'text'} onclick={() => { tab = 'text'; preview = null; }}>
				Paste Text
			</button>
		</div>

		{#if !preview}
			<div class="tab-content">
				{#if tab === 'text'}
					<textarea
						bind:value={rawText}
						placeholder="Paste the full job posting text here..."
						rows={10}
					></textarea>
				{:else}
					<input
						type="url"
						bind:value={rawUrl}
						placeholder="https://..."
						style="width: 100%"
					/>
				{/if}
				{#if error}
					<p class="error">{error}</p>
				{/if}
				<div class="modal-actions">
					<button class="btn btn-primary" onclick={handleParse} disabled={parsing || (!rawText && !rawUrl)}>
						{parsing ? 'Parsing...' : 'Parse'}
					</button>
					<button class="btn btn-secondary" onclick={onClose}>Cancel</button>
				</div>
			</div>
		{:else}
			<div class="preview-form">
				<p class="preview-label">
				Review and edit the parsed fields:
				{#if preview.ai_used}
					<span class="parse-badge ai">AI parsed</span>
				{:else}
					<span class="parse-badge heuristic">Heuristic parsed</span>
				{/if}
			</p>

				<div class="form-group">
					<label>Title</label>
					<input type="text" bind:value={title} style="width: 100%" />
				</div>
				<div class="form-row">
					<div class="form-group">
						<label>Company</label>
						<input type="text" bind:value={company_name} style="width: 100%" />
					</div>
					<div class="form-group">
						<label>Location</label>
						<input type="text" bind:value={location} style="width: 100%" />
					</div>
				</div>
				<div class="form-row">
					<div class="form-group">
						<label>Remote</label>
						<select bind:value={remote_type} style="width: 100%">
							<option value="">Unknown</option>
							<option value="remote">Remote</option>
							<option value="hybrid">Hybrid</option>
							<option value="onsite">Onsite</option>
						</select>
					</div>
					<div class="form-group">
						<label>Min Salary</label>
						<input type="number" bind:value={salary_min} style="width: 100%" />
					</div>
					<div class="form-group">
						<label>Max Salary</label>
						<input type="number" bind:value={salary_max} style="width: 100%" />
					</div>
				</div>
				<div class="form-group">
					<label>URL</label>
					<input type="url" bind:value={url} style="width: 100%" />
				</div>
				<div class="form-group">
					<label>Description</label>
					<textarea bind:value={description} rows={6} style="width: 100%"></textarea>
				</div>

				<label class="checkbox-label">
					<input type="checkbox" bind:checked={addToPipeline} />
					Add to Pipeline immediately
				</label>

				{#if error}
					<p class="error">
						{error}
						{#if duplicateId}
							— <a href="/postings?id={duplicateId}" onclick={() => onClose()}>View posting</a>
						{/if}
					</p>
				{/if}
				<div class="modal-actions">
					<button class="btn btn-primary" onclick={handleSave} disabled={saving || !title}>
						{saving ? 'Saving...' : 'Save Posting'}
					</button>
					<button class="btn btn-secondary" onclick={() => { preview = null; }}>← Back</button>
					<button class="btn btn-secondary" onclick={onClose}>Cancel</button>
				</div>
			</div>
		{/if}
	</div>
</div>

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
		width: 680px;
		max-width: 95vw;
		max-height: 90vh;
		overflow-y: auto;
		padding: 1.5rem;
	}

	.modal-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 1rem;
	}

	.modal-header h2 {
		font-size: 1.2rem;
		font-weight: 700;
	}

	.close-btn {
		background: none;
		border: none;
		color: var(--text-secondary);
		font-size: 1rem;
		padding: 0.25rem;
	}

	.close-btn:hover {
		color: var(--text-primary);
	}

	.tabs {
		display: flex;
		gap: 0;
		border-bottom: 1px solid var(--border-color);
		margin-bottom: 1rem;
	}

	.tab {
		background: none;
		border: none;
		color: var(--text-secondary);
		padding: 0.5rem 1rem;
		font-weight: 500;
		border-bottom: 2px solid transparent;
		margin-bottom: -1px;
	}

	.tab.active {
		color: var(--accent-blue);
		border-bottom-color: var(--accent-blue);
	}

	.tab-content textarea,
	.preview-form textarea {
		width: 100%;
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

	.preview-label {
		color: var(--text-secondary);
		font-size: 0.9rem;
		margin-bottom: 0.75rem;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.parse-badge {
		font-size: 0.75rem;
		padding: 0.1rem 0.4rem;
		border-radius: 4px;
		font-weight: 500;
	}

	.parse-badge.ai {
		background: color-mix(in srgb, var(--accent-blue) 15%, transparent);
		color: var(--accent-blue);
	}

	.parse-badge.heuristic {
		background: color-mix(in srgb, var(--accent-orange, #f59e0b) 15%, transparent);
		color: var(--accent-orange, #f59e0b);
	}

	.checkbox-label {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		cursor: pointer;
		margin-bottom: 0.75rem;
	}

	.modal-actions {
		display: flex;
		gap: 0.5rem;
		margin-top: 1rem;
	}

	.error {
		color: var(--accent-red);
		font-size: 0.9rem;
		margin-top: 0.5rem;
	}
</style>

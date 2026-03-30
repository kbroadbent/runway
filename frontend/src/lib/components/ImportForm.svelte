<script lang="ts">
	import { postings, ApiError } from '$lib/api';
	import type { ImportPreview, LeadSource } from '$lib/types';
	import { LEAD_SOURCE_LABELS } from '$lib/types';
	import LeadSourceTooltip from './LeadSourceTooltip.svelte';

	interface Props {
		mode: 'url' | 'text';
	}

	let { mode }: Props = $props();

	type Phase = 'input' | 'preview' | 'success';

	let phase = $state<Phase>('input');
	let urlValue = $state('');
	let textValue = $state('');
	let parseError = $state<string | null>(null);
	let saveError = $state<string | null>(null);
	let parsing = $state(false);
	let saving = $state(false);

	let preview = $state<ImportPreview | null>(null);
	let savedId = $state<number | null>(null);
	let duplicateId = $state<number | null>(null);

	// Preview form fields
	let title = $state('');
	let companyName = $state('');
	let location = $state('');
	let remoteType = $state('');
	let salaryMin = $state<number | null>(null);
	let salaryMax = $state<number | null>(null);
	let description = $state('');
	let url = $state('');
	let leadSource = $state<LeadSource>('cold_apply');

	async function handleParse() {
		parseError = null;
		parsing = true;
		try {
			const payload = mode === 'url' ? { url: urlValue } : { text: textValue };
			const result = await postings.importPreview(payload);
			preview = result;
			title = result.title ?? '';
			companyName = result.company_name ?? '';
			location = result.location ?? '';
			remoteType = result.remote_type ?? '';
			salaryMin = result.salary_min ?? null;
			salaryMax = result.salary_max ?? null;
			description = result.description ?? '';
			url = result.url ?? '';
			leadSource = result.lead_source ?? 'cold_apply';
			phase = 'preview';
		} catch (err) {
			parseError = err instanceof Error ? err.message : 'Unknown error';
		} finally {
			parsing = false;
		}
	}

	async function handleSave() {
		saveError = null;
		duplicateId = null;
		saving = true;
		try {
			const data: ImportPreview = {
				title,
				company_name: companyName,
				location,
				remote_type: remoteType,
				salary_min: salaryMin,
				salary_max: salaryMax,
				description,
				url: url || null,
				raw_content: preview?.raw_content ?? null,
				ai_used: preview?.ai_used,
				notes: preview?.notes ?? null,
				lead_source: leadSource,
			};
			const result = await postings.importConfirm(data);
			savedId = result.id;
			phase = 'success';
		} catch (err) {
			if (err instanceof ApiError && err.status === 409) {
				const data = err.data as { existing_id?: number };
				if (data?.existing_id) {
					duplicateId = data.existing_id;
				}
				saveError = err.message;
			} else {
				saveError = err instanceof Error ? err.message : 'Unknown error';
			}
		} finally {
			saving = false;
		}
	}

	function handleBack() {
		phase = 'input';
		parseError = null;
		saveError = null;
		duplicateId = null;
	}
</script>

<div class="import-form">
	{#if phase === 'input'}
		<div class="input-phase">
			{#if mode === 'url'}
				<input
					type="url"
					placeholder="https://..."
					bind:value={urlValue}
					oninput={(e) => (urlValue = (e.target as HTMLInputElement).value)}
				/>
			{:else}
				<textarea
					placeholder="Paste the full job posting text here"
					bind:value={textValue}
					oninput={(e) => (textValue = (e.target as HTMLTextAreaElement).value)}
					rows="8"
				></textarea>
			{/if}

			{#if parseError}
				<p class="error">{parseError}</p>
			{/if}

			<button onclick={handleParse} disabled={parsing}>
				{parsing ? 'Parsing…' : 'Parse'}
			</button>
		</div>
	{:else if phase === 'preview'}
		<div class="preview-phase">
			<h3>Review and Edit</h3>

			<div class="field">
				<label for="title">Title</label>
				<input id="title" type="text" bind:value={title} />
			</div>

			<div class="field">
				<label for="company">Company</label>
				<input id="company" type="text" bind:value={companyName} />
			</div>

			<div class="field">
				<label for="location">Location</label>
				<input id="location" type="text" bind:value={location} />
			</div>

			<div class="field">
				<label for="remote-type">Remote Type</label>
				<input id="remote-type" type="text" bind:value={remoteType} />
			</div>

			<div class="field">
				<label for="salary-min">Salary Min</label>
				<input
					id="salary-min"
					type="number"
					value={salaryMin ?? ''}
					oninput={(e) => {
						const v = (e.target as HTMLInputElement).value;
						salaryMin = v ? Number(v) : null;
					}}
				/>
			</div>

			<div class="field">
				<label for="salary-max">Salary Max</label>
				<input
					id="salary-max"
					type="number"
					value={salaryMax ?? ''}
					oninput={(e) => {
						const v = (e.target as HTMLInputElement).value;
						salaryMax = v ? Number(v) : null;
					}}
				/>
			</div>

			<div class="field">
				<label for="description">Description</label>
				<textarea id="description" bind:value={description} rows="6"></textarea>
			</div>

			<div class="field">
				<label for="url">URL</label>
				<input id="url" type="url" bind:value={url} />
			</div>

			<div class="field lead-source-field">
				<label for="lead-source">Lead Source</label>
				<LeadSourceTooltip />
				<select
					id="lead-source"
					bind:value={leadSource}
					onchange={(e) => (leadSource = (e.target as HTMLSelectElement).value as LeadSource)}
				>
					{#each Object.entries(LEAD_SOURCE_LABELS) as [value, label]}
						<option {value}>{label}</option>
					{/each}
				</select>
			</div>

			{#if saveError}
				<p class="error">{saveError}</p>
				{#if duplicateId}
					<a href="/postings?highlight={duplicateId}">View Posting</a>
				{/if}
			{/if}

			<div class="actions">
				<button onclick={handleBack}>Back</button>
				<button onclick={handleSave} disabled={saving}>
					{saving ? 'Saving…' : 'Save Posting'}
				</button>
			</div>
		</div>
	{:else if phase === 'success'}
		<div class="success-phase">
			<p>Posting saved!</p>
			<a href="/postings?highlight={savedId}">View in Postings</a>
		</div>
	{/if}
</div>

<style>
	.import-form {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.input-phase,
	.preview-phase,
	.success-phase {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.field {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.lead-source-field {
		flex-direction: row;
		align-items: center;
		gap: 0.5rem;
		flex-wrap: wrap;
	}

	.lead-source-field label {
		flex: 0 0 auto;
	}

	.lead-source-field select {
		flex: 1;
	}

	input,
	textarea,
	select {
		background: var(--bg-secondary);
		border: 1px solid var(--border-color);
		border-radius: var(--radius);
		color: var(--text-primary);
		padding: 0.4rem 0.6rem;
		font-size: 0.9rem;
		width: 100%;
	}

	label {
		font-size: 0.8rem;
		color: var(--text-secondary);
	}

	button {
		padding: 0.4rem 1rem;
		border-radius: var(--radius);
		border: 1px solid var(--border-color);
		background: var(--bg-secondary);
		color: var(--text-primary);
		cursor: pointer;
		font-size: 0.9rem;
		width: fit-content;
	}

	button:hover:not(:disabled) {
		background: var(--bg-tertiary);
	}

	button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.actions {
		display: flex;
		gap: 0.5rem;
	}

	.error {
		color: var(--accent-red);
		font-size: 0.85rem;
	}
</style>

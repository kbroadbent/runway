<script lang="ts">
	import type { PipelineEntry, CustomDate } from '$lib/types';
	import { pipeline } from '$lib/api';
	import { STAGE_DATE_FIELDS } from '$lib/pipeline';

	interface Props {
		entry: PipelineEntry;
		onUpdated: () => void;
	}

	let { entry, onUpdated }: Props = $props();

	// All stage date fields shown regardless of current stage
	const allStageDateFields = [
		{ label: 'Applied Date', field: 'applied_date' },
		{ label: 'Recruiter Screen Date', field: 'recruiter_screen_date' },
		{ label: 'Tech Screen Date', field: 'tech_screen_date' },
		{ label: 'Onsite Date', field: 'onsite_date' },
		{ label: 'Offer Date', field: 'offer_date' },
		{ label: 'Offer Expiration Date', field: 'offer_expiration_date' },
	];

	// Stage date edit state
	let stageDates = $state<Record<string, string>>({});
	let savingStage = $state(false);
	let stageStatus = $state('');

	// Custom dates
	let customDates = $state<CustomDate[]>([]);
	let loadingCustom = $state(true);

	// Add custom date form
	let showAddForm = $state(false);
	let newLabel = $state('');
	let newDate = $state('');
	let addingCustom = $state(false);

	// Edit custom date state
	let editingId = $state<number | null>(null);
	let editLabel = $state('');
	let editDate = $state('');
	let savingEdit = $state(false);

	function syncStageDates() {
		const dates: Record<string, string> = {};
		for (const { field } of allStageDateFields) {
			const val = (entry as unknown as Record<string, unknown>)[field] as string | null;
			dates[field] = val ? val.substring(0, 10) : '';
		}
		stageDates = dates;
	}

	$effect(() => {
		// Re-sync when entry changes
		entry.id;
		syncStageDates();
	});

	$effect(() => {
		// Reload custom dates when entry changes
		const id = entry.id;
		loadingCustom = true;
		pipeline.customDates(id).then((dates) => {
			customDates = dates;
			loadingCustom = false;
		});
	});

	async function saveStageDates() {
		savingStage = true;
		stageStatus = '';
		try {
			const payload: Record<string, string | null> = {};
			for (const { field } of allStageDateFields) {
				payload[field] = stageDates[field] || null;
			}
			await pipeline.update(entry.id, payload as Partial<PipelineEntry>);
			stageStatus = 'Saved!';
			onUpdated();
		} catch (e) {
			stageStatus = e instanceof Error ? e.message : 'Save failed';
		} finally {
			savingStage = false;
		}
	}

	async function addCustomDate() {
		if (!newLabel || !newDate) return;
		addingCustom = true;
		try {
			const created = await pipeline.createCustomDate(entry.id, { label: newLabel, date: newDate });
			customDates = [...customDates, created];
			newLabel = '';
			newDate = '';
			showAddForm = false;
			onUpdated();
		} finally {
			addingCustom = false;
		}
	}

	function startEdit(cd: CustomDate) {
		editingId = cd.id;
		editLabel = cd.label;
		editDate = cd.date.substring(0, 10);
	}

	function cancelEdit() {
		editingId = null;
	}

	async function saveEdit(cd: CustomDate) {
		if (!editLabel || !editDate) return;
		savingEdit = true;
		try {
			const updated = await pipeline.updateCustomDate(entry.id, cd.id, {
				label: editLabel,
				date: editDate,
			});
			customDates = customDates.map((d) => (d.id === cd.id ? updated : d));
			editingId = null;
			onUpdated();
		} finally {
			savingEdit = false;
		}
	}

	async function deleteCustomDate(cd: CustomDate) {
		if (!confirm(`Delete "${cd.label}"?`)) return;
		await pipeline.deleteCustomDate(entry.id, cd.id);
		customDates = customDates.filter((d) => d.id !== cd.id);
		onUpdated();
	}
</script>

<div class="section">
	<h3>Key Dates</h3>

	<div class="stage-dates">
		{#each allStageDateFields as { label, field }}
			<div class="date-row">
				<label for="stage-{field}">{label}</label>
				<input
					id="stage-{field}"
					type="date"
					value={stageDates[field] ?? ''}
					onchange={(e) => (stageDates[field] = (e.target as HTMLInputElement).value)}
				/>
			</div>
		{/each}
	</div>

	{#if stageStatus}
		<p class="status-msg">{stageStatus}</p>
	{/if}
	<button class="btn btn-primary btn-sm" onclick={saveStageDates} disabled={savingStage}>
		{savingStage ? 'Saving...' : 'Save Dates'}
	</button>
</div>

<div class="section">
	<h3>Custom Dates</h3>

	{#if loadingCustom}
		<p class="empty-hint">Loading...</p>
	{:else if customDates.length === 0 && !showAddForm}
		<p class="empty-hint">No custom dates.</p>
	{/if}

	{#each customDates as cd}
		<div class="custom-date-row">
			{#if editingId === cd.id}
				<div class="custom-date-edit">
					<input type="text" bind:value={editLabel} placeholder="Label" class="edit-input" />
					<input type="date" bind:value={editDate} class="edit-input" />
					<div class="edit-actions">
						<button class="btn btn-primary btn-sm" onclick={() => saveEdit(cd)} disabled={savingEdit || !editLabel || !editDate}>
							Save
						</button>
						<button class="btn btn-secondary btn-sm" onclick={cancelEdit}>Cancel</button>
					</div>
				</div>
			{:else}
				<div class="custom-date-display">
					<div class="custom-date-info">
						<span class="custom-date-label">{cd.label}</span>
						<span class="custom-date-value">{new Date(cd.date).toLocaleDateString()}</span>
					</div>
					<div class="custom-date-actions">
						<button class="btn btn-sm btn-secondary" onclick={() => startEdit(cd)}>Edit</button>
						<button class="btn btn-sm btn-danger" onclick={() => deleteCustomDate(cd)}>Delete</button>
					</div>
				</div>
			{/if}
		</div>
	{/each}

	{#if showAddForm}
		<div class="add-form">
			<div class="form-group">
				<label>Label *</label>
				<input type="text" bind:value={newLabel} placeholder="e.g. Follow-up call" style="width:100%" />
			</div>
			<div class="form-group">
				<label>Date *</label>
				<input type="date" bind:value={newDate} style="width:100%" />
			</div>
			<div style="display:flex;gap:0.5rem;margin-top:0.5rem">
				<button class="btn btn-primary btn-sm" onclick={addCustomDate} disabled={addingCustom || !newLabel || !newDate}>
					{addingCustom ? 'Adding...' : 'Add'}
				</button>
				<button class="btn btn-secondary btn-sm" onclick={() => (showAddForm = false)}>Cancel</button>
			</div>
		</div>
	{:else}
		<button class="btn btn-secondary btn-sm" onclick={() => (showAddForm = true)} style="margin-top:0.25rem">
			+ Add Custom Date
		</button>
	{/if}
</div>

<style>
	.section h3 {
		font-size: 0.8rem;
		font-weight: 600;
		color: var(--text-muted);
		text-transform: uppercase;
		letter-spacing: 0.05em;
		margin-bottom: 0.4rem;
	}

	.stage-dates {
		display: flex;
		flex-direction: column;
		gap: 0.35rem;
		margin-bottom: 0.5rem;
	}

	.date-row {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.date-row label {
		font-size: 0.8rem;
		color: var(--text-secondary);
		min-width: 140px;
		flex-shrink: 0;
	}

	.date-row input[type='date'] {
		flex: 1;
	}

	.status-msg {
		color: var(--accent-green);
		font-size: 0.85rem;
		margin-bottom: 0.25rem;
	}

	.custom-date-row {
		margin-bottom: 0.35rem;
	}

	.custom-date-display {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 0.5rem;
		padding: 0.35rem 0;
		border-bottom: 1px solid var(--border-color);
	}

	.custom-date-info {
		display: flex;
		flex-direction: column;
	}

	.custom-date-label {
		font-size: 0.85rem;
		font-weight: 500;
	}

	.custom-date-value {
		font-size: 0.8rem;
		color: var(--text-secondary);
	}

	.custom-date-actions {
		display: flex;
		gap: 0.25rem;
		flex-shrink: 0;
	}

	.custom-date-edit {
		display: flex;
		flex-direction: column;
		gap: 0.35rem;
		padding: 0.5rem;
		background: var(--bg-primary);
		border-radius: var(--radius);
		border: 1px solid var(--border-color);
	}

	.edit-input {
		width: 100%;
	}

	.edit-actions {
		display: flex;
		gap: 0.5rem;
	}

	.add-form {
		padding: 0.5rem;
		background: var(--bg-primary);
		border-radius: var(--radius);
		border: 1px solid var(--border-color);
		margin-top: 0.25rem;
	}

	.form-group {
		margin-bottom: 0.5rem;
	}

	.form-group label {
		display: block;
		font-size: 0.8rem;
		color: var(--text-secondary);
		margin-bottom: 0.2rem;
	}

	.empty-hint {
		color: var(--text-muted);
		font-size: 0.9rem;
	}
</style>

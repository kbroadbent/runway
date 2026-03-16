<script lang="ts">
	import type { Company } from '$lib/types';

	interface Props {
		company?: Partial<Company>;
		onSave: (data: Partial<Company>) => void;
		onCancel: () => void;
	}

	let { company = {}, onSave, onCancel }: Props = $props();

	let name = $state(company.name ?? '');
	let website = $state(company.website ?? '');
	let industry = $state(company.industry ?? '');
	let employee_count = $state<number | undefined>(company.employee_count ?? undefined);
	let notes = $state(company.notes ?? '');

	function handleSubmit() {
		onSave({
			name,
			website: website || null,
			industry: industry || null,
			employee_count: employee_count ?? null,
			notes: notes || null,
		});
	}
</script>

<form class="card company-form" onsubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
	<div class="form-group">
		<label for="name">Company Name *</label>
		<input id="name" type="text" bind:value={name} required placeholder="e.g. Acme Corp" style="width:100%" />
	</div>
	<div class="form-group">
		<label for="website">Website</label>
		<input id="website" type="url" bind:value={website} placeholder="https://..." style="width:100%" />
	</div>
	<div class="form-row">
		<div class="form-group">
			<label for="industry">Industry</label>
			<input id="industry" type="text" bind:value={industry} placeholder="e.g. Software" style="width:100%" />
		</div>
		<div class="form-group">
			<label for="employee_count">Employees</label>
			<input id="employee_count" type="number" bind:value={employee_count} placeholder="e.g. 500" style="width:100%" />
		</div>
	</div>
	<div class="form-group">
		<label for="notes">Notes</label>
		<textarea id="notes" bind:value={notes} rows={3} style="width:100%" placeholder="Any notes..."></textarea>
	</div>
	<div class="form-actions">
		<button type="submit" class="btn btn-primary">Save</button>
		<button type="button" class="btn btn-secondary" onclick={onCancel}>Cancel</button>
	</div>
</form>

<style>
	.company-form {
		max-width: 480px;
		margin-bottom: 1.5rem;
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

	.form-actions {
		display: flex;
		gap: 0.5rem;
		margin-top: 1rem;
	}
</style>

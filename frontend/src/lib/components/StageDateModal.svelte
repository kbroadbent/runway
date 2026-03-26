<script lang="ts">
	import { onMount } from 'svelte';
	import { STAGE_DATE_FIELDS } from '$lib/pipeline';

	interface Props {
		stage: string;
		entryTitle: string;
		onConfirm: (dates: Record<string, string>) => void;
		onSkip: () => void;
		onCancel: () => void;
	}

	let { stage, entryTitle, onConfirm, onSkip, onCancel }: Props = $props();

	let dialogEl: HTMLDialogElement | undefined = $state();

	const fields = $derived(STAGE_DATE_FIELDS[stage] ?? []);
	const today = new Date().toISOString().substring(0, 10);
	let dateValues = $state<Record<string, string>>({});

	$effect(() => {
		const vals: Record<string, string> = {};
		for (const f of STAGE_DATE_FIELDS[stage] ?? []) {
			vals[f.field] = today;
		}
		dateValues = vals;
	});

	onMount(() => {
		dialogEl?.showModal();
	});

	function handleConfirm() {
		const result: Record<string, string> = {};
		for (const [key, val] of Object.entries(dateValues)) {
			if (val) result[key] = val;
		}
		onConfirm(result);
	}

	function handleKeyDown(e: KeyboardEvent) {
		if (e.key === 'Escape') {
			e.preventDefault();
			onCancel();
		}
	}

	const stageDisplay = $derived(stage.replace(/_/g, ' '));
</script>

<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
<dialog bind:this={dialogEl} onkeydown={handleKeyDown}>
	<div class="modal-content">
		<h2>Set dates for {stageDisplay}</h2>
		<p class="subtitle">{entryTitle}</p>

		{#each fields as f (f.field)}
			<div class="form-group">
				<label for={f.field}>{f.label}</label>
				<input
					type="date"
					id={f.field}
					bind:value={dateValues[f.field]}
				/>
			</div>
		{/each}

		<div class="modal-actions">
			<button class="btn btn-primary" onclick={handleConfirm}>Save</button>
			<button class="btn btn-secondary" onclick={onSkip}>Skip</button>
			<button class="btn btn-secondary" onclick={onCancel}>Cancel</button>
		</div>
	</div>
</dialog>

<style>
	dialog {
		background: var(--bg-secondary);
		border: 1px solid var(--border-color);
		border-radius: var(--radius);
		padding: 1.5rem;
		min-width: 360px;
		max-width: 95vw;
	}

	dialog::backdrop {
		background: rgba(0, 0, 0, 0.6);
	}

	h2 {
		font-size: 1.1rem;
		font-weight: 700;
		margin: 0 0 0.25rem;
	}

	.subtitle {
		color: var(--text-secondary);
		font-size: 0.9rem;
		margin: 0 0 1rem;
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

	.form-group input[type='date'] {
		width: 100%;
	}

	.modal-actions {
		display: flex;
		gap: 0.5rem;
		margin-top: 1rem;
	}
</style>

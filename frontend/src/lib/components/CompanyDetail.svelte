<script lang="ts">
	import type { Company, JobPosting } from '$lib/types';
	import { companies, postings as postingsApi } from '$lib/api';
	import { onMount } from 'svelte';

	interface Props {
		company: Company;
		onClose: () => void;
		onUpdated: () => void;
	}

	let { company, onClose, onUpdated }: Props = $props();

	let companyPostings = $state<JobPosting[]>([]);
	let researching = $state(false);
	let savingNotes = $state(false);
	let notes = $state(company.notes ?? '');
	let status = $state('');
	let currentCompany = $state(company);

	onMount(async () => {
		const all = await postingsApi.list();
		companyPostings = all.filter((p) => p.company?.id === company.id);
	});

	async function handleResearch() {
		researching = true;
		status = 'Researching...';
		try {
			currentCompany = await companies.research(company.id);
			status = 'Research complete!';
			onUpdated();
		} catch (e) {
			status = e instanceof Error ? e.message : 'Research failed';
		} finally {
			researching = false;
		}
	}

	async function saveNotes() {
		savingNotes = true;
		try {
			await companies.update(company.id, { notes });
			status = 'Notes saved!';
			onUpdated();
		} catch (e) {
			status = e instanceof Error ? e.message : 'Save failed';
		} finally {
			savingNotes = false;
		}
	}
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div class="panel-backdrop" onclick={onClose} onkeydown={(e) => e.key === 'Escape' && onClose()}>
	<div class="panel" onclick={(e) => e.stopPropagation()}>
		<div class="panel-header">
			<div>
				<h2>{currentCompany.name}</h2>
				{#if currentCompany.industry}
					<span class="company-meta">{currentCompany.industry}</span>
				{/if}
				{#if currentCompany.employee_count}
					<span class="company-meta"> · {currentCompany.employee_count.toLocaleString()} employees</span>
				{/if}
			</div>
			<button class="close-btn" onclick={onClose}>✕</button>
		</div>

		<!-- External links -->
		<div class="links-row">
			{#if currentCompany.website}
				<a href={currentCompany.website} target="_blank" rel="noopener" class="btn btn-sm btn-secondary">Website ↗</a>
			{/if}
			{#if currentCompany.glassdoor_url}
				<a href={currentCompany.glassdoor_url} target="_blank" rel="noopener" class="btn btn-sm btn-secondary">
					Glassdoor {currentCompany.glassdoor_rating ? `(${currentCompany.glassdoor_rating}★)` : '↗'}
				</a>
			{/if}
			{#if currentCompany.levels_url}
				<a href={currentCompany.levels_url} target="_blank" rel="noopener" class="btn btn-sm btn-secondary">Levels.fyi ↗</a>
			{/if}
			{#if currentCompany.blind_url}
				<a href={currentCompany.blind_url} target="_blank" rel="noopener" class="btn btn-sm btn-secondary">Blind ↗</a>
			{/if}
			<button class="btn btn-sm btn-primary" onclick={handleResearch} disabled={researching}>
				{researching ? 'Researching...' : '🔍 Research'}
			</button>
		</div>

		{#if currentCompany.levels_salary_data}
			<div class="section">
				<h3>Salary Data (Levels.fyi)</h3>
				<p class="salary-data">{currentCompany.levels_salary_data}</p>
			</div>
		{/if}

		<div class="section">
			<h3>Notes</h3>
			<textarea bind:value={notes} rows={4} style="width:100%" placeholder="Notes about this company..."></textarea>
			<button class="btn btn-sm btn-secondary" onclick={saveNotes} disabled={savingNotes} style="margin-top:0.4rem">
				{savingNotes ? 'Saving...' : 'Save Notes'}
			</button>
		</div>

		{#if status}
			<p class="status-msg">{status}</p>
		{/if}

		{#if companyPostings.length > 0}
			<div class="section">
				<h3>Job Postings ({companyPostings.length})</h3>
				{#each companyPostings as posting}
					<div class="posting-item">
						<span class="posting-title">{posting.title}</span>
						{#if posting.pipeline_stage}
							<span class="badge badge-stage">{posting.pipeline_stage}</span>
						{/if}
					</div>
				{/each}
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
		width: 480px;
		max-width: 95vw;
		height: 100vh;
		overflow-y: auto;
		background: var(--bg-secondary);
		border-left: 1px solid var(--border-color);
		padding: 1.25rem;
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

	.panel-header h2 {
		font-size: 1.2rem;
		font-weight: 700;
	}

	.company-meta {
		font-size: 0.85rem;
		color: var(--text-secondary);
	}

	.close-btn {
		background: none;
		border: none;
		color: var(--text-secondary);
		font-size: 1rem;
		cursor: pointer;
		flex-shrink: 0;
	}

	.close-btn:hover {
		color: var(--text-primary);
	}

	.links-row {
		display: flex;
		flex-wrap: wrap;
		gap: 0.4rem;
	}

	.section h3 {
		font-size: 0.8rem;
		font-weight: 600;
		color: var(--text-muted);
		text-transform: uppercase;
		letter-spacing: 0.05em;
		margin-bottom: 0.4rem;
	}

	.salary-data {
		font-size: 0.9rem;
		color: var(--text-secondary);
		white-space: pre-wrap;
	}

	.status-msg {
		color: var(--accent-green);
		font-size: 0.85rem;
	}

	.posting-item {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0.4rem 0;
		border-bottom: 1px solid var(--border-color);
		font-size: 0.9rem;
	}

	.posting-title {
		color: var(--text-primary);
	}
</style>

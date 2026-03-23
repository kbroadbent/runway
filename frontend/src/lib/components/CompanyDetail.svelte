<script lang="ts">
	import type { Company, JobPosting, CompanyInterview } from '$lib/types';
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

	let tab = $state<'overview' | 'interviews' | 'questions' | 'salary'>('overview');
	let companyInterviews = $state<CompanyInterview[]>([]);
	let loadingInterviews = $state(false);
	let commonQuestions = $derived.by<string[]>(() => {
		if (!currentCompany.common_questions) return [];
		try {
			return JSON.parse(currentCompany.common_questions);
		} catch {
			return [];
		}
	});
	let newQuestion = $state('');
	let savingQuestions = $state(false);

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

	async function loadInterviews() {
		if (companyInterviews.length > 0) return;
		loadingInterviews = true;
		try {
			companyInterviews = await companies.interviews(company.id);
		} finally {
			loadingInterviews = false;
		}
	}

	$effect(() => {
		if (tab === 'interviews') loadInterviews();
	});

	let groupedInterviews = $derived.by(() => {
		const map = new Map<string, { posting_title: string; notes: CompanyInterview[] }>();
		for (const n of companyInterviews) {
			if (!map.has(n.posting_title)) {
				map.set(n.posting_title, { posting_title: n.posting_title, notes: [] });
			}
			map.get(n.posting_title)!.notes.push(n);
		}
		return [...map.values()];
	});

	async function addQuestion() {
		if (!newQuestion.trim()) return;
		commonQuestions = [...commonQuestions, newQuestion.trim()];
		newQuestion = '';
		await saveQuestions();
	}

	async function removeQuestion(index: number) {
		commonQuestions = commonQuestions.filter((_, i) => i !== index);
		await saveQuestions();
	}

	async function saveQuestions() {
		savingQuestions = true;
		try {
			await companies.update(company.id, { common_questions: JSON.stringify(commonQuestions) });
			onUpdated();
		} finally {
			savingQuestions = false;
		}
	}

	function parseSalaryData(raw: string | null) {
		if (!raw) return null;
		try {
			const parsed = JSON.parse(raw);
			return Array.isArray(parsed) ? parsed : null;
		} catch {
			return null;
		}
	}

	let parsedSalary = $derived(parseSalaryData(currentCompany.levels_salary_data));
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

		<!-- Tab bar -->
		<div class="tabs">
			<button class="tab" class:active={tab === 'overview'} onclick={() => tab = 'overview'}>Overview</button>
			<button class="tab" class:active={tab === 'interviews'} onclick={() => tab = 'interviews'}>Interviews</button>
			<button class="tab" class:active={tab === 'questions'} onclick={() => tab = 'questions'}>Questions</button>
			<button class="tab" class:active={tab === 'salary'} onclick={() => tab = 'salary'}>Salary</button>
		</div>

		{#if tab === 'overview'}
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

			{#if status}
				<p class="status-msg">{status}</p>
			{/if}

			<div class="section">
				<h3>Notes</h3>
				<textarea bind:value={notes} rows={4} style="width:100%" placeholder="Notes about this company..." onkeydown={(e) => { if (e.ctrlKey && e.key === 'Enter') saveNotes(); }}></textarea>
				<button class="btn btn-sm btn-secondary" onclick={saveNotes} disabled={savingNotes} style="margin-top:0.4rem">
					{savingNotes ? 'Saving...' : 'Save Notes'}
				</button>
			</div>

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
		{:else if tab === 'interviews'}
			{#if loadingInterviews}
				<p class="empty-state">Loading...</p>
			{:else if groupedInterviews.length === 0}
				<p class="empty-state">No interview notes for this company yet.</p>
			{:else}
				{#each groupedInterviews as group}
					<div class="interview-group">
						<h4 class="group-title">{group.posting_title}</h4>
						{#each group.notes as note}
							<div class="interview-note">
								<div class="note-header">
									<strong>{note.round}</strong>
									{#if note.scheduled_at}
										<span class="note-meta">{new Date(note.scheduled_at).toLocaleDateString()}</span>
									{/if}
									{#if note.outcome}
										<span class="badge badge-{note.outcome}">{note.outcome}</span>
									{/if}
								</div>
								{#if note.interviewers}
									<p class="note-meta">Interviewers: {note.interviewers}</p>
								{/if}
								{#if note.notes}
									<p class="note-body">{note.notes}</p>
								{/if}
							</div>
						{/each}
					</div>
				{/each}
			{/if}
		{:else if tab === 'questions'}
			{#if commonQuestions.length === 0 && !newQuestion}
				<p class="empty-state">No questions saved yet.</p>
			{/if}
			{#each commonQuestions as q, i}
				<div class="question-item">
					<span class="question-text">{q}</span>
					<button class="btn-icon" onclick={() => removeQuestion(i)} title="Remove">✕</button>
				</div>
			{/each}
			<div class="add-question">
				<input
					type="text"
					bind:value={newQuestion}
					placeholder="Add a common question..."
					onkeydown={(e) => e.key === 'Enter' && addQuestion()}
				/>
				<button class="btn btn-sm btn-secondary" onclick={addQuestion} disabled={!newQuestion.trim() || savingQuestions}>
					Add
				</button>
			</div>
			{#if savingQuestions}<p class="status-msg">Saving...</p>{/if}
		{:else if tab === 'salary'}
			{#if parsedSalary}
				<table class="salary-table">
					<thead>
						<tr><th>Role / Level</th><th>Salary</th></tr>
					</thead>
					<tbody>
						{#each parsedSalary as row}
							<tr>
								<td>{row.title ?? row.level ?? row.role ?? JSON.stringify(row)}</td>
								<td>{row.salary ?? row.total ?? row.compensation ?? '-'}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			{:else if currentCompany.levels_salary_data}
				<p class="salary-data">{currentCompany.levels_salary_data}</p>
			{:else}
				<p class="empty-state">No salary data. Use the Research button (Overview tab) to fetch from Levels.fyi.</p>
			{/if}
			{#if currentCompany.levels_url}
				<a href={currentCompany.levels_url} target="_blank" rel="noopener" class="btn btn-sm btn-secondary" style="margin-top: 0.75rem">View on Levels.fyi ↗</a>
			{/if}
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

	.tabs {
		display: flex;
		gap: 0;
		border-bottom: 1px solid var(--border-color);
		margin-bottom: 0.5rem;
	}

	.tab {
		background: none;
		border: none;
		border-bottom: 2px solid transparent;
		padding: 0.5rem 0.75rem;
		font-size: 0.85rem;
		color: var(--text-secondary);
		cursor: pointer;
		margin-bottom: -1px;
	}

	.tab:hover {
		color: var(--text-primary);
	}

	.tab.active {
		color: var(--text-primary);
		border-bottom-color: var(--accent-blue, #3b82f6);
		font-weight: 600;
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

	.interview-group {
		margin-bottom: 1rem;
	}

	.group-title {
		font-size: 0.85rem;
		font-weight: 600;
		color: var(--text-secondary);
		margin-bottom: 0.5rem;
		padding-bottom: 0.25rem;
		border-bottom: 1px solid var(--border-color);
	}

	.interview-note {
		padding: 0.5rem 0;
		border-bottom: 1px solid var(--border-color);
		font-size: 0.9rem;
	}

	.note-header {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-bottom: 0.25rem;
	}

	.note-meta {
		font-size: 0.8rem;
		color: var(--text-muted);
		margin: 0.1rem 0;
	}

	.note-body {
		color: var(--text-secondary);
		font-size: 0.85rem;
		white-space: pre-wrap;
		margin: 0.25rem 0 0;
	}

	.question-item {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 0.5rem;
		padding: 0.4rem 0;
		border-bottom: 1px solid var(--border-color);
		font-size: 0.9rem;
	}

	.question-text {
		flex: 1;
		color: var(--text-primary);
	}

	.btn-icon {
		background: none;
		border: none;
		color: var(--text-muted);
		cursor: pointer;
		font-size: 0.75rem;
		padding: 0.1rem 0.25rem;
		flex-shrink: 0;
	}

	.btn-icon:hover {
		color: var(--text-primary);
	}

	.add-question {
		display: flex;
		gap: 0.4rem;
		margin-top: 0.75rem;
	}

	.add-question input {
		flex: 1;
		padding: 0.35rem 0.5rem;
		font-size: 0.85rem;
		border: 1px solid var(--border-color);
		border-radius: 4px;
		background: var(--bg-primary);
		color: var(--text-primary);
	}

	.salary-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.85rem;
	}

	.salary-table th,
	.salary-table td {
		text-align: left;
		padding: 0.4rem 0.5rem;
		border-bottom: 1px solid var(--border-color);
	}

	.salary-table th {
		font-size: 0.75rem;
		font-weight: 600;
		color: var(--text-muted);
		text-transform: uppercase;
		letter-spacing: 0.04em;
	}

	.salary-data {
		font-size: 0.9rem;
		color: var(--text-secondary);
		white-space: pre-wrap;
	}

	.empty-state {
		color: var(--text-muted);
		font-size: 0.85rem;
		padding: 1rem 0;
		text-align: center;
	}
</style>

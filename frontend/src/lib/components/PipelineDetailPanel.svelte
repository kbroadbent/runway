<script lang="ts">
	import type { PipelineEntry, PipelineHistory, InterviewNote } from '$lib/types';
	import { pipeline, interviews, postings } from '$lib/api';
	import { onMount } from 'svelte';
	import PipelineComments from './PipelineComments.svelte';

	interface Props {
		entry: PipelineEntry;
		onClose: () => void;
		onUpdated: () => void;
	}

	let { entry, onClose, onUpdated }: Props = $props();

	let tab = $state<'details' | 'interviews' | 'history' | 'comments'>('details');
	let history = $state<PipelineHistory[]>([]);
	let interviewNotes = $state<InterviewNote[]>([]);
	let saving = $state(false);
	let status = $state('');

	// Detail edit state
	let notes = $state(entry.job_posting.notes ?? '');
	let next_action = $state(entry.next_action ?? '');
	let next_action_date = $state(
		entry.next_action_date ? entry.next_action_date.substring(0, 10) : ''
	);
	let tier = $state<1 | 2 | 3 | null>(entry.job_posting.tier ?? null);

	// Manual event form
	let showEventForm = $state(false);
	let eventDescription = $state('');
	let eventDate = $state('');

	// New interview form
	let showInterviewForm = $state(false);
	let iRound = $state('');
	let iScheduled = $state('');
	let iInterviewers = $state('');
	let iNotes = $state('');
	let iOutcome = $state('');

	onMount(async () => {
		[history, interviewNotes] = await Promise.all([
			pipeline.history(entry.id),
			pipeline.interviews(entry.id),
		]);
	});

	async function saveDetails() {
		saving = true;
		try {
			await Promise.all([
				postings.update(entry.job_posting.id, { notes: notes || null }),
				pipeline.update(entry.id, {
					next_action: next_action || null,
					next_action_date: next_action_date || null,
				}),
			]);
			status = 'Saved!';
			onUpdated();
		} catch (e) {
			status = e instanceof Error ? e.message : 'Save failed';
		} finally {
			saving = false;
		}
	}

	async function addInterview() {
		await pipeline.addInterview(entry.id, {
			round: iRound,
			scheduled_at: iScheduled || null,
			interviewers: iInterviewers || null,
			notes: iNotes || null,
			outcome: iOutcome || null,
		});
		interviewNotes = await pipeline.interviews(entry.id);
		iRound = iScheduled = iInterviewers = iNotes = iOutcome = '';
		showInterviewForm = false;
	}

	async function addEvent() {
		await pipeline.addEvent(entry.id, {
			description: eventDescription,
			event_date: eventDate || undefined,
		});
		history = await pipeline.history(entry.id);
		eventDescription = '';
		eventDate = '';
		showEventForm = false;
	}

	async function deleteInterview(id: number) {
		if (!confirm('Delete this interview note?')) return;
		await interviews.delete(id);
		interviewNotes = interviewNotes.filter((n) => n.id !== id);
	}

	function formatSalary(min: number | null, max: number | null): string {
		if (!min && !max) return 'Not specified';
		const fmt = (n: number) => '$' + n.toLocaleString();
		if (min && max) return `${fmt(min)} – ${fmt(max)}`;
		if (min) return `${fmt(min)}+`;
		return `up to ${fmt(max!)}`;
	}
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div class="panel-backdrop" onclick={onClose} onkeydown={(e) => e.key === 'Escape' && onClose()}>
	<div class="panel" onclick={(e) => e.stopPropagation()}>
		<div class="panel-header">
			<div>
				<h2>{entry.job_posting.title}</h2>
				{#if entry.job_posting.company}
					<span class="company-name">{entry.job_posting.company.name}</span>
				{/if}
				<span class="stage-badge badge badge-stage">{entry.stage}</span>
			</div>
			<button class="close-btn" onclick={onClose}>✕</button>
		</div>

		<div class="tabs">
			{#each [['details', 'Details'], ['interviews', 'Interviews'], ['history', 'History'], ['comments', 'Comments']] as [key, label]}
				<button class="tab" class:active={tab === key} onclick={() => (tab = key as typeof tab)}>
					{label}
					{#if key === 'interviews' && interviewNotes.length > 0}
						<span class="tab-count">{interviewNotes.length}</span>
					{/if}
				</button>
			{/each}
		</div>

		{#if tab === 'details'}
			<div class="tab-content">
				<div class="posting-meta">
					{#if entry.job_posting.location}<p>📍 {entry.job_posting.location}</p>{/if}
					{#if entry.job_posting.remote_type}<p>🏠 {entry.job_posting.remote_type}</p>{/if}
					<p>💰 {formatSalary(entry.job_posting.salary_min, entry.job_posting.salary_max)}</p>
					{#if entry.job_posting.url}
						<a href={entry.job_posting.url} target="_blank" rel="noopener">View posting ↗</a>
					{/if}
				</div>

				{#if entry.job_posting.company}
					{@const co = entry.job_posting.company}
					<div class="section">
						<h3>Company</h3>
						<div class="company-links">
							{#if co.website}<a href={co.website} target="_blank" rel="noopener" class="btn btn-sm btn-secondary">Website ↗</a>{/if}
							{#if co.glassdoor_url}<a href={co.glassdoor_url} target="_blank" rel="noopener" class="btn btn-sm btn-secondary">Glassdoor {co.glassdoor_rating ? `(${co.glassdoor_rating}★)` : '↗'}</a>{/if}
							{#if co.levels_url}<a href={co.levels_url} target="_blank" rel="noopener" class="btn btn-sm btn-secondary">Levels.fyi ↗</a>{/if}
							{#if co.blind_url}<a href={co.blind_url} target="_blank" rel="noopener" class="btn btn-sm btn-secondary">Blind ↗</a>{/if}
						</div>
					</div>
				{/if}

				<div class="section">
					<h3>Tier</h3>
					<select bind:value={tier} style="width: 120px" onchange={() => postings.update(entry.job_posting.id, { tier })}>
						<option value={null}>None</option>
						<option value={1}>Tier 1</option>
						<option value={2}>Tier 2</option>
						<option value={3}>Tier 3</option>
					</select>
				</div>

				<div class="section">
					<h3>Notes</h3>
					<textarea bind:value={notes} rows={4} style="width: 100%" placeholder="Application notes..." onkeydown={(e) => { if (e.ctrlKey && e.key === 'Enter') saveDetails(); }}></textarea>
				</div>

				<div class="section">
					<h3>Next Action</h3>
					<input type="text" bind:value={next_action} style="width: 100%" placeholder="e.g. Follow up with recruiter" />
					<input type="date" bind:value={next_action_date} style="width: 100%; margin-top: 0.5rem" />
				</div>

				{#if status}<p class="status-msg">{status}</p>{/if}
				<button class="btn btn-primary" onclick={saveDetails} disabled={saving}>
					{saving ? 'Saving...' : 'Save Details'}
				</button>
			</div>

		{:else if tab === 'interviews'}
			<div class="tab-content">
				{#if interviewNotes.length === 0}
					<p class="empty-hint">No interview notes yet.</p>
				{/if}
				{#each interviewNotes as note}
					<div class="interview-card card">
						<div class="interview-header">
							<strong>{note.round}</strong>
							{#if note.outcome}<span class="badge badge-stage">{note.outcome}</span>{/if}
							<button class="btn btn-sm btn-danger" onclick={() => deleteInterview(note.id)}>Delete</button>
						</div>
						{#if note.scheduled_at}<p class="interview-meta">📅 {new Date(note.scheduled_at).toLocaleString()}</p>{/if}
						{#if note.interviewers}<p class="interview-meta">👥 {note.interviewers}</p>{/if}
						{#if note.notes}<p class="interview-notes">{note.notes}</p>{/if}
					</div>
				{/each}

				{#if showInterviewForm}
					<div class="card">
						<div class="form-group">
							<label>Round *</label>
							<input type="text" bind:value={iRound} placeholder="e.g. Phone Screen" style="width:100%" />
						</div>
						<div class="form-group">
							<label>Date/Time</label>
							<input type="datetime-local" bind:value={iScheduled} style="width:100%" />
						</div>
						<div class="form-group">
							<label>Interviewers</label>
							<input type="text" bind:value={iInterviewers} placeholder="Names or roles" style="width:100%" />
						</div>
						<div class="form-group">
							<label>Notes</label>
							<textarea bind:value={iNotes} rows={3} style="width:100%" onkeydown={(e) => { if (e.ctrlKey && e.key === 'Enter' && iRound) addInterview(); }}></textarea>
						</div>
						<div class="form-group">
							<label>Outcome</label>
							<select bind:value={iOutcome} style="width:100%">
								<option value="">Pending</option>
								<option value="passed">Passed</option>
								<option value="failed">Failed</option>
								<option value="cancelled">Cancelled</option>
							</select>
						</div>
						<div style="display:flex;gap:0.5rem;margin-top:0.5rem">
							<button class="btn btn-primary btn-sm" onclick={addInterview} disabled={!iRound}>Save</button>
							<button class="btn btn-secondary btn-sm" onclick={() => (showInterviewForm = false)}>Cancel</button>
						</div>
					</div>
				{:else}
					<button class="btn btn-secondary" onclick={() => (showInterviewForm = true)} style="margin-top:0.5rem">
						+ Add Interview Note
					</button>
				{/if}
			</div>

		{:else if tab === 'history'}
			<div class="tab-content">
				{#if history.length === 0}
					<p class="empty-hint">No history yet.</p>
				{/if}
				{#each history as h}
					<div class="history-item">
						<div class="history-dot" class:manual-event={h.event_type === 'manual'}></div>
						<div>
							{#if h.event_type === 'manual'}
								<span class="history-description">{h.description}</span>
								<p class="history-date">
									{#if h.event_date}
										{new Date(h.event_date).toLocaleDateString()} &middot;
									{/if}
									Added {new Date(h.changed_at).toLocaleString()}
								</p>
							{:else}
								<span class="history-stages">
									{#if h.from_stage}<span class="text-muted">{h.from_stage} →</span>{/if}
									<strong>{h.to_stage}</strong>
								</span>
								<p class="history-date">{new Date(h.changed_at).toLocaleString()}</p>
								{#if h.note}<p class="history-note">{h.note}</p>{/if}
							{/if}
						</div>
					</div>
				{/each}

				{#if showEventForm}
					<div class="card">
						<div class="form-group">
							<label>Description *</label>
							<input type="text" bind:value={eventDescription} placeholder="e.g. Coffee chat with hiring manager" style="width:100%" />
						</div>
						<div class="form-group">
							<label>Date (optional)</label>
							<input type="date" bind:value={eventDate} style="width:100%" />
						</div>
						<div style="display:flex;gap:0.5rem;margin-top:0.5rem">
							<button class="btn btn-primary btn-sm" onclick={addEvent} disabled={!eventDescription}>Add</button>
							<button class="btn btn-secondary btn-sm" onclick={() => (showEventForm = false)}>Cancel</button>
						</div>
					</div>
				{:else}
					<button class="btn btn-secondary" onclick={() => (showEventForm = true)} style="margin-top:0.5rem">
						+ Add Event
					</button>
				{/if}
			</div>
		{:else if tab === 'comments'}
			<div class="tab-content">
				<PipelineComments entryId={entry.id} />
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
		gap: 0.75rem;
	}

	.panel-header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 1rem;
	}

	.panel-header h2 {
		font-size: 1.1rem;
		font-weight: 700;
	}

	.company-name {
		display: block;
		color: var(--text-secondary);
		font-size: 0.9rem;
		margin-top: 0.15rem;
	}

	.stage-badge {
		margin-top: 0.25rem;
	}

	.close-btn {
		background: none;
		border: none;
		color: var(--text-secondary);
		font-size: 1rem;
		flex-shrink: 0;
		cursor: pointer;
	}

	.tabs {
		display: flex;
		border-bottom: 1px solid var(--border-color);
	}

	.tab {
		background: none;
		border: none;
		color: var(--text-secondary);
		padding: 0.4rem 0.75rem;
		font-weight: 500;
		border-bottom: 2px solid transparent;
		margin-bottom: -1px;
		cursor: pointer;
		display: flex;
		align-items: center;
		gap: 0.35rem;
	}

	.tab.active {
		color: var(--accent-blue);
		border-bottom-color: var(--accent-blue);
	}

	.tab-count {
		background: var(--bg-tertiary);
		border-radius: 9999px;
		font-size: 0.7rem;
		padding: 0.1rem 0.35rem;
	}

	.tab-content {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
		flex: 1;
	}

	.posting-meta p, .posting-meta a {
		font-size: 0.9rem;
		color: var(--text-secondary);
	}

	.section h3 {
		font-size: 0.8rem;
		font-weight: 600;
		color: var(--text-muted);
		text-transform: uppercase;
		letter-spacing: 0.05em;
		margin-bottom: 0.4rem;
	}

	.company-links {
		display: flex;
		flex-wrap: wrap;
		gap: 0.4rem;
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

	.status-msg {
		color: var(--accent-green);
		font-size: 0.85rem;
	}

	.interview-card {
		margin-bottom: 0.5rem;
	}

	.interview-header {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-bottom: 0.25rem;
	}

	.interview-meta {
		font-size: 0.85rem;
		color: var(--text-secondary);
	}

	.interview-notes {
		font-size: 0.85rem;
		color: var(--text-secondary);
		white-space: pre-wrap;
		margin-top: 0.25rem;
	}

	.history-item {
		display: flex;
		gap: 0.75rem;
		align-items: flex-start;
	}

	.history-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background: var(--accent-blue);
		margin-top: 0.35rem;
		flex-shrink: 0;
	}

	.history-dot.manual-event {
		background: var(--accent-green);
	}

	.history-description {
		font-size: 0.9rem;
		font-weight: 500;
	}

	.history-stages {
		font-size: 0.9rem;
	}

	.history-date {
		font-size: 0.8rem;
		color: var(--text-muted);
	}

	.history-note {
		font-size: 0.85rem;
		color: var(--text-secondary);
	}

	.text-muted {
		color: var(--text-muted);
	}

	.empty-hint {
		color: var(--text-muted);
		font-size: 0.9rem;
	}
</style>

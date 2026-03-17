<script lang="ts">
	import type { SearchProfile, JobPosting } from '$lib/types';
	import { searchProfiles, postings, pipeline, searchResults } from '$lib/api';
	import SearchProfileForm from '$lib/components/SearchProfileForm.svelte';
	import SearchResultsTable from '$lib/components/SearchResultsTable.svelte';
	import { onMount } from 'svelte';

	let profiles = $state<SearchProfile[]>([]);
	let selectedProfile = $state<SearchProfile | null>(null);
	let results = $state<JobPosting[]>([]);
	let showForm = $state(false);
	let editingProfile = $state<SearchProfile | null>(null);
	let loading = $state(false);
	let runStatus = $state('');

	onMount(async () => {
		await loadProfiles();
	});

	async function loadProfiles() {
		profiles = await searchProfiles.list();
	}

	async function selectProfile(profile: SearchProfile) {
		selectedProfile = profile;
		results = [];
		runStatus = '';
	}

	async function handleRunSearch() {
		if (!selectedProfile) return;
		loading = true;
		runStatus = 'Searching...';
		try {
			const result = await searchProfiles.run(selectedProfile.id);
			runStatus = `Found ${result.new_count} new of ${result.total_count} total results`;
			// Reload postings scoped to this profile
			results = await searchProfiles.postings(selectedProfile.id);
			// Refresh profiles to update new_result_count
			await loadProfiles();
			selectedProfile = profiles.find((p) => p.id === selectedProfile!.id) ?? selectedProfile;
		} catch (e) {
			runStatus = `Error: ${e instanceof Error ? e.message : 'Search failed'}`;
		} finally {
			loading = false;
		}
	}

	async function handleSaveProfile(data: Partial<SearchProfile>) {
		if (editingProfile) {
			await searchProfiles.update(editingProfile.id, data);
		} else {
			await searchProfiles.create(data);
			selectedProfile = null;
			results = [];
		}
		showForm = false;
		editingProfile = null;
		await loadProfiles();
	}

	function handleCreateProfile() {
		editingProfile = null;
		showForm = true;
	}

	function handleEditProfile(profile: SearchProfile) {
		editingProfile = profile;
		showForm = true;
	}

	function handleCancelForm() {
		showForm = false;
		editingProfile = null;
	}

	async function handleDeleteProfile(profile: SearchProfile) {
		if (!confirm(`Delete profile "${profile.name}"?`)) return;
		await searchProfiles.delete(profile.id);
		if (selectedProfile?.id === profile.id) {
			selectedProfile = null;
			results = [];
		}
		await loadProfiles();
	}

	async function handleMarkReviewed() {
		if (!selectedProfile) return;
		await searchResults.markReviewed(selectedProfile.id);
		await loadProfiles();
		selectedProfile = profiles.find((p) => p.id === selectedProfile!.id) ?? selectedProfile;
	}

	async function handleSave(posting: JobPosting) {
		await postings.save(posting.id);
		results = results.filter((r) => r.id !== posting.id);
	}

	async function handleDismiss(posting: JobPosting) {
		await postings.dismiss(posting.id);
		results = results.filter((r) => r.id !== posting.id);
	}

	async function handleAddToPipeline(posting: JobPosting) {
		await pipeline.add({ job_posting_id: posting.id });
		results = results.filter((r) => r.id !== posting.id);
		runStatus = `Added "${posting.title}" to pipeline`;
	}
</script>

<div class="page-header">
	<h1>Search</h1>
	<button class="btn btn-primary" onclick={handleCreateProfile}>New Profile</button>
</div>

{#if showForm}
	<SearchProfileForm
		profile={editingProfile ?? {}}
		onSave={handleSaveProfile}
		onCancel={handleCancelForm}
	/>
{:else}
	<div class="search-layout">
		<div class="profiles-panel">
			<h2 class="panel-title">Search Profiles</h2>
			{#if profiles.length === 0}
				<p class="empty-hint">No profiles yet. Create one to start searching.</p>
			{/if}
			{#each profiles as profile}
				<div
					class="profile-card"
					class:active={selectedProfile?.id === profile.id}
					onclick={() => selectProfile(profile)}
					role="button"
					tabindex="0"
					onkeydown={(e) => { if (e.key === 'Enter') selectProfile(profile); }}
				>
					<div class="profile-name">
						{profile.name}
						{#if profile.new_result_count > 0}
							<span class="badge badge-new">{profile.new_result_count} new</span>
						{/if}
					</div>
					<div class="profile-meta">
						{profile.search_term ?? 'No search term'}
						{#if profile.location} &middot; {profile.location}{/if}
					</div>
					<div class="profile-actions" onclick={(e) => e.stopPropagation()}>
						<button class="btn btn-sm btn-secondary" onclick={() => handleEditProfile(profile)}>Edit</button>
						<button class="btn btn-sm btn-danger" onclick={() => handleDeleteProfile(profile)}>Delete</button>
					</div>
				</div>
			{/each}
		</div>

		<div class="results-panel">
			{#if selectedProfile}
				<div class="results-header">
					<h2 class="panel-title">{selectedProfile.name}</h2>
					<div class="results-actions">
						{#if selectedProfile.new_result_count > 0}
							<button class="btn btn-sm btn-secondary" onclick={handleMarkReviewed}>
								Mark All Reviewed
							</button>
						{/if}
						<button
							class="btn btn-primary"
							onclick={handleRunSearch}
							disabled={loading}
						>
							{loading ? 'Searching...' : 'Run Search'}
						</button>
					</div>
				</div>

				{#if runStatus}
					<p class="run-status">{runStatus}</p>
				{/if}

				{#if selectedProfile.last_run_at}
					<p class="last-run">Last run: {new Date(selectedProfile.last_run_at).toLocaleString()}</p>
				{/if}

				<SearchResultsTable {results} onSave={handleSave} onDismiss={handleDismiss} onAddToPipeline={handleAddToPipeline} />
			{:else}
				<p class="empty-hint">Select a search profile to view results.</p>
			{/if}
		</div>
	</div>
{/if}

<style>
	.search-layout {
		display: flex;
		gap: 1.5rem;
		min-height: calc(100vh - 8rem);
	}

	.profiles-panel {
		width: 280px;
		flex-shrink: 0;
	}

	.results-panel {
		flex: 1;
		min-width: 0;
	}

	.panel-title {
		font-size: 1rem;
		font-weight: 600;
		color: var(--text-secondary);
		text-transform: uppercase;
		letter-spacing: 0.05em;
		margin-bottom: 0.75rem;
	}

	.profile-card {
		display: block;
		width: 100%;
		text-align: left;
		background: var(--bg-secondary);
		border: 1px solid var(--border-color);
		border-radius: var(--radius);
		padding: 0.75rem;
		margin-bottom: 0.5rem;
		cursor: pointer;
		transition: border-color 0.15s;
		color: var(--text-primary);
	}

	.profile-card:hover {
		border-color: var(--text-muted);
	}

	.profile-card.active {
		border-color: var(--accent-blue);
	}

	.profile-name {
		font-weight: 600;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.profile-meta {
		font-size: 0.85rem;
		color: var(--text-secondary);
		margin-top: 0.25rem;
	}

	.profile-actions {
		display: flex;
		gap: 0.25rem;
		margin-top: 0.5rem;
	}

	.results-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 0.5rem;
	}

	.results-actions {
		display: flex;
		gap: 0.5rem;
	}

	.run-status {
		color: var(--accent-green);
		font-size: 0.9rem;
		margin-bottom: 0.5rem;
	}

	.last-run {
		color: var(--text-muted);
		font-size: 0.8rem;
		margin-bottom: 1rem;
	}

	.empty-hint {
		color: var(--text-muted);
		font-size: 0.9rem;
	}
</style>

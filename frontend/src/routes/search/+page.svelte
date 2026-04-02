<script lang="ts">
	import type { SearchProfile, JobPosting } from '$lib/types';
	import { searchProfiles, postings, searchResults } from '$lib/api';
	import SearchProfileForm from '$lib/components/SearchProfileForm.svelte';
	import SearchResultsTable from '$lib/components/SearchResultsTable.svelte';
	import ImportForm from '$lib/components/ImportForm.svelte';
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';

	let profiles = $state<SearchProfile[]>([]);
	let selectedProfile = $state<SearchProfile | null>(null);
	let results = $state<JobPosting[]>([]);
	let showForm = $state(false);
	let editingProfile = $state<SearchProfile | null>(null);
	let loading = $state(false);
	let loadingPostings = $state(false);
	let runStatus = $state('');
	let addedIds = $state<Set<number>>(new Set());
	let removedPostings = $state<JobPosting[]>([]);

	let activeTab = $state(page.url.searchParams.get('tab') ?? 'search');

	function switchTab(tab: string) {
		activeTab = tab;
		goto(`?tab=${tab}`);
	}

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
		addedIds = new Set();
		removedPostings = [];
		loadingPostings = true;
		try {
			results = await searchProfiles.postings(profile.id);
		} catch {
			// silently fail — results stays empty
		} finally {
			loadingPostings = false;
		}
	}

	async function handleRunSearch() {
		if (!selectedProfile) return;
		loading = true;
		runStatus = 'Searching...';
		try {
			const previousResults = results;
			const previousIds = new Set(previousResults.map((r) => r.id));
			const result = await searchProfiles.run(selectedProfile.id);
			runStatus = `${result.new_count} new · ${result.total_count} total`;
			// Reload postings scoped to this profile
			const newResults = await searchProfiles.postings(selectedProfile.id);
			const newIds = new Set(newResults.map((r) => r.id));

			// Only compute deltas if there were previous results
			if (previousResults.length > 0) {
				addedIds = new Set([...newIds].filter((id) => !previousIds.has(id)));
				removedPostings = previousResults.filter((r) => !newIds.has(r.id));
			} else {
				addedIds = new Set();
				removedPostings = [];
			}

			results = newResults;
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
		addedIds = new Set();
		removedPostings = [];
		await loadProfiles();
		selectedProfile = profiles.find((p) => p.id === selectedProfile!.id) ?? selectedProfile;
	}

	async function handleSave(posting: JobPosting) {
		await postings.save(posting.id);
		results = results.filter((r) => r.id !== posting.id);
		if (addedIds.has(posting.id)) {
			addedIds = new Set([...addedIds].filter((id) => id !== posting.id));
		}
	}

	async function handleDismiss(posting: JobPosting) {
		await postings.dismiss(posting.id);
		results = results.filter((r) => r.id !== posting.id);
		if (addedIds.has(posting.id)) {
			addedIds = new Set([...addedIds].filter((id) => id !== posting.id));
		}
	}

</script>

<div class="page-header">
	<h1>Add Jobs</h1>
</div>

<div class="tab-bar" role="tablist">
	<button role="tab" class="tab-btn" class:active={activeTab === 'search'} onclick={() => switchTab('search')}>Search</button>
	<button role="tab" class="tab-btn" class:active={activeTab === 'import-url'} onclick={() => switchTab('import-url')}>From URL</button>
	<button role="tab" class="tab-btn" class:active={activeTab === 'paste'} onclick={() => switchTab('paste')}>From Text</button>
</div>

{#if activeTab === 'import-url'}
	<ImportForm mode="url" />
{:else if activeTab === 'paste'}
	<ImportForm mode="text" />
{:else if showForm}
	<SearchProfileForm
		profile={editingProfile ?? {}}
		onSave={handleSaveProfile}
		onCancel={handleCancelForm}
	/>
{:else}
	<div class="import-cards">
		<button class="import-card" onclick={() => switchTab('import-url')}>
			<span class="import-card-title">Import from URL</span>
			<span class="import-card-subtitle">Paste a job posting link</span>
		</button>
		<button class="import-card" onclick={() => switchTab('paste')}>
			<span class="import-card-title">Import from Text</span>
			<span class="import-card-subtitle">Paste job description text</span>
		</button>
	</div>
	<div class="search-layout-header">
		<button class="btn btn-primary" onclick={handleCreateProfile}>New Profile</button>
	</div>
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
						{#if selectedProfile.new_result_count > 0 || addedIds.size > 0}
							<button class="btn btn-sm btn-secondary" onclick={handleMarkReviewed}>
								Mark All Reviewed
							</button>
						{/if}
						<button
							class="btn btn-primary"
							onclick={handleRunSearch}
							disabled={loading}
						>
							{loading ? 'Searching...' : 'Refresh'}
						</button>
					</div>
				</div>

				{#if !loadingPostings}
					<p class="results-count">{results.length} results</p>
				{/if}

				{#if runStatus}
					<p class="run-status">{runStatus}</p>
				{/if}

				{#if selectedProfile.last_run_at}
					<p class="last-run">Last run: {new Date(selectedProfile.last_run_at).toLocaleString()}</p>
				{/if}

				{#if loadingPostings}
					<p class="empty-hint">Loading results...</p>
				{:else}
					<SearchResultsTable {results} {addedIds} {removedPostings} onSave={handleSave} onDismiss={handleDismiss} />
				{/if}
			{:else}
				<p class="empty-hint">Select a search profile to view results.</p>
			{/if}
		</div>
	</div>
{/if}

<style>
	.import-cards {
		display: flex;
		gap: 1rem;
		margin-bottom: 1.5rem;
	}

	.import-card {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		padding: 1rem 1.25rem;
		background: var(--bg-secondary);
		border: 1px solid var(--border-color);
		border-radius: var(--radius);
		cursor: pointer;
		text-align: left;
		color: var(--text-primary);
		transition: border-color 0.15s, background 0.15s;
	}

	.import-card:hover {
		border-color: var(--accent-blue);
		background: var(--bg-tertiary);
	}

	.import-card-title {
		font-weight: 600;
		font-size: 0.95rem;
	}

	.import-card-subtitle {
		font-size: 0.85rem;
		color: var(--text-muted);
	}

	.tab-bar {
		display: flex;
		gap: 0.25rem;
		border-bottom: 1px solid var(--border-color);
		margin-bottom: 1.5rem;
	}

	.tab-btn {
		padding: 0.5rem 1rem;
		background: none;
		border: none;
		border-bottom: 2px solid transparent;
		color: var(--text-secondary);
		cursor: pointer;
		font-size: 0.9rem;
		font-weight: 500;
		margin-bottom: -1px;
		transition: color 0.15s, border-color 0.15s;
	}

	.tab-btn:hover {
		color: var(--text-primary);
	}

	.tab-btn.active {
		color: var(--accent-blue);
		border-bottom-color: var(--accent-blue);
	}

	.search-layout-header {
		display: flex;
		justify-content: flex-end;
		margin-bottom: 1rem;
	}

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

	.results-count {
		color: var(--text-secondary);
		font-size: 0.9rem;
		margin-bottom: 0.25rem;
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

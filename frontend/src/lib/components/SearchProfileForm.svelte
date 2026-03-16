<script lang="ts">
	import type { SearchProfile } from '$lib/types';

	interface Props {
		profile?: Partial<SearchProfile>;
		onSave: (data: Partial<SearchProfile>) => void;
		onCancel: () => void;
	}

	let { profile = {}, onSave, onCancel }: Props = $props();

	let name = $state(profile.name ?? '');
	let search_term = $state(profile.search_term ?? '');
	let location = $state(profile.location ?? '');
	let remote_filter = $state(profile.remote_filter ?? '');
	let salary_min = $state(profile.salary_min ?? undefined);
	let salary_max = $state(profile.salary_max ?? undefined);
	let job_type = $state(profile.job_type ?? '');
	let run_interval = $state(profile.run_interval ?? undefined);
	let is_auto_enabled = $state(profile.is_auto_enabled ?? false);

	const allSources = ['indeed', 'linkedin', 'glassdoor', 'zip_recruiter'];
	let selectedSources = $state<string[]>(profile.sources ?? ['indeed']);

	function toggleSource(source: string) {
		if (selectedSources.includes(source)) {
			selectedSources = selectedSources.filter((s) => s !== source);
		} else {
			selectedSources = [...selectedSources, source];
		}
	}

	function handleSubmit() {
		onSave({
			name,
			search_term: search_term || null,
			location: location || null,
			remote_filter: remote_filter || null,
			salary_min: salary_min ?? null,
			salary_max: salary_max ?? null,
			job_type: job_type || null,
			sources: selectedSources.length > 0 ? selectedSources : null,
			run_interval: run_interval ?? null,
			is_auto_enabled,
		});
	}
</script>

<form class="card profile-form" onsubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
	<div class="form-group">
		<label for="name">Profile Name</label>
		<input id="name" type="text" bind:value={name} required placeholder="e.g. Remote React Jobs" />
	</div>

	<div class="form-group">
		<label for="search_term">Search Term</label>
		<input id="search_term" type="text" bind:value={search_term} placeholder="e.g. software engineer" />
	</div>

	<div class="form-group">
		<label for="location">Location</label>
		<input id="location" type="text" bind:value={location} placeholder="e.g. San Francisco, CA" />
	</div>

	<div class="form-row">
		<div class="form-group">
			<label for="remote_filter">Remote</label>
			<select id="remote_filter" bind:value={remote_filter}>
				<option value="">Any</option>
				<option value="onsite">Onsite</option>
				<option value="remote">Remote</option>
				<option value="hybrid">Hybrid</option>
			</select>
		</div>

		<div class="form-group">
			<label for="job_type">Job Type</label>
			<select id="job_type" bind:value={job_type}>
				<option value="">Any</option>
				<option value="fulltime">Full-time</option>
				<option value="parttime">Part-time</option>
				<option value="contract">Contract</option>
				<option value="internship">Internship</option>
			</select>
		</div>
	</div>

	<div class="form-row">
		<div class="form-group">
			<label for="salary_min">Min Salary</label>
			<input id="salary_min" type="number" bind:value={salary_min} placeholder="e.g. 100000" />
		</div>
		<div class="form-group">
			<label for="salary_max">Max Salary</label>
			<input id="salary_max" type="number" bind:value={salary_max} placeholder="e.g. 200000" />
		</div>
	</div>

	<div class="form-group">
		<label>Sources</label>
		<div class="checkbox-group">
			{#each allSources as source}
				<label class="checkbox-label">
					<input
						type="checkbox"
						checked={selectedSources.includes(source)}
						onchange={() => toggleSource(source)}
					/>
					{source.replace('_', ' ')}
				</label>
			{/each}
		</div>
	</div>

	<div class="form-row">
		<div class="form-group">
			<label for="run_interval">Auto-run Interval (hours)</label>
			<input id="run_interval" type="number" bind:value={run_interval} placeholder="e.g. 24" />
		</div>
		<div class="form-group">
			<label class="checkbox-label" style="margin-top: 1.5rem;">
				<input type="checkbox" bind:checked={is_auto_enabled} />
				Enable auto-run
			</label>
		</div>
	</div>

	<div class="form-actions">
		<button type="submit" class="btn btn-primary">Save</button>
		<button type="button" class="btn btn-secondary" onclick={onCancel}>Cancel</button>
	</div>
</form>

<style>
	.profile-form {
		max-width: 500px;
	}

	.form-group {
		margin-bottom: 1rem;
	}

	.form-group label {
		display: block;
		margin-bottom: 0.25rem;
		color: var(--text-secondary);
		font-size: 0.85rem;
		font-weight: 500;
	}

	.form-group input[type='text'],
	.form-group input[type='number'],
	.form-group select {
		width: 100%;
	}

	.form-row {
		display: flex;
		gap: 1rem;
	}

	.form-row .form-group {
		flex: 1;
	}

	.checkbox-group {
		display: flex;
		flex-wrap: wrap;
		gap: 0.75rem;
	}

	.checkbox-label {
		display: flex;
		align-items: center;
		gap: 0.35rem;
		cursor: pointer;
		color: var(--text-primary);
		font-size: 0.9rem;
		text-transform: capitalize;
	}

	.checkbox-label input[type='checkbox'] {
		width: auto;
		padding: 0;
	}

	.form-actions {
		display: flex;
		gap: 0.5rem;
		margin-top: 1.5rem;
	}
</style>

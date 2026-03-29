import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/svelte';
import type { SearchProfile, JobPosting } from '$lib/types';

// Mock fetch globally
const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

const MOCK_PROFILE: SearchProfile = {
	id: 1,
	name: 'Frontend Jobs',
	search_term: 'frontend developer',
	location: 'Remote',
	remote_filter: null,
	salary_min: null,
	salary_max: null,
	job_type: null,
	sources: ['indeed'],
	exclude_terms: null,
	run_interval: null,
	is_auto_enabled: false,
	created_at: '2026-03-20T00:00:00',
	last_run_at: '2026-03-24T12:00:00',
	new_result_count: 2,
};

const MOCK_PROFILE_NO_RESULTS: SearchProfile = {
	id: 2,
	name: 'Backend Jobs',
	search_term: 'backend developer',
	location: null,
	remote_filter: null,
	salary_min: null,
	salary_max: null,
	job_type: null,
	sources: null,
	exclude_terms: null,
	run_interval: null,
	is_auto_enabled: false,
	created_at: '2026-03-21T00:00:00',
	last_run_at: null,
	new_result_count: 0,
};

const MOCK_POSTINGS: JobPosting[] = [
	{
		id: 10,
		title: 'Senior Frontend Developer',
		company: { id: 1, name: 'Acme Corp', website: null, glassdoor_rating: null, glassdoor_url: null, levels_salary_data: null, levels_url: null, blind_url: null, employee_count: null, industry: null, notes: null, common_questions: null, last_researched_at: null, created_at: '2026-03-20T00:00:00' },
		company_name: 'Acme Corp',
		description: 'Build UIs',
		location: 'Remote',
		remote_type: 'remote',
		salary_min: 120000,
		salary_max: 180000,
		url: 'https://example.com/job/10',
		source: 'indeed',
		date_posted: '2026-03-23T00:00:00',
		date_saved: '2026-03-24T00:00:00',
		status: 'new',
		tier: null,
		pipeline_stage: null,
		has_raw_content: false,
		notes: null,
		lead_source: 'cold_apply',
	},
	{
		id: 11,
		title: 'React Engineer',
		company: { id: 2, name: 'BigCo', website: null, glassdoor_rating: null, glassdoor_url: null, levels_salary_data: null, levels_url: null, blind_url: null, employee_count: null, industry: null, notes: null, common_questions: null, last_researched_at: null, created_at: '2026-03-20T00:00:00' },
		company_name: 'BigCo',
		description: 'React stuff',
		location: 'NYC',
		remote_type: null,
		salary_min: 100000,
		salary_max: 150000,
		url: 'https://example.com/job/11',
		source: 'indeed',
		date_posted: '2026-03-22T00:00:00',
		date_saved: '2026-03-24T00:00:00',
		status: 'new',
		tier: null,
		pipeline_stage: null,
		has_raw_content: false,
		notes: null,
		lead_source: 'cold_apply',
	},
];

/**
 * Mock a successful JSON response for a given URL pattern.
 * Calls are matched in order, so queue them in the order the component will call them.
 */
function mockJsonResponse(data: unknown) {
	mockFetch.mockResolvedValueOnce({
		ok: true,
		status: 200,
		json: () => Promise.resolve(data),
	});
}

describe('Search Page — selectProfile loads persisted results', () => {
	let SearchPage: typeof import('./+page.svelte').default;

	beforeEach(async () => {
		mockFetch.mockReset();
		const mod = await import('./+page.svelte');
		SearchPage = mod.default;
	});

	// --- selectProfile calls postings endpoint ---

	it('fetches postings when a profile is selected', async () => {
		// 1. Mount fetches profile list
		mockJsonResponse([MOCK_PROFILE, MOCK_PROFILE_NO_RESULTS]);
		render(SearchPage);

		await waitFor(() => {
			expect(screen.getByText('Frontend Jobs')).toBeInTheDocument();
		});

		// 2. Click the profile — should trigger postings fetch
		mockJsonResponse(MOCK_POSTINGS);
		await fireEvent.click(screen.getByText('Frontend Jobs'));

		await waitFor(() => {
			expect(mockFetch).toHaveBeenCalledWith(
				expect.stringContaining('/search-profiles/1/postings'),
				expect.any(Object),
			);
		});
	});

	it('displays persisted postings after selecting a profile', async () => {
		mockJsonResponse([MOCK_PROFILE]);
		render(SearchPage);

		await waitFor(() => {
			expect(screen.getByText('Frontend Jobs')).toBeInTheDocument();
		});

		mockJsonResponse(MOCK_POSTINGS);
		await fireEvent.click(screen.getByText('Frontend Jobs'));

		await waitFor(() => {
			expect(screen.getByText('Senior Frontend Developer')).toBeInTheDocument();
			expect(screen.getByText('React Engineer')).toBeInTheDocument();
		});
	});

	// --- Loading state ---

	it('shows loading state while fetching postings for selected profile', async () => {
		mockJsonResponse([MOCK_PROFILE]);
		render(SearchPage);

		await waitFor(() => {
			expect(screen.getByText('Frontend Jobs')).toBeInTheDocument();
		});

		// Return a promise that never resolves to keep loading state visible
		mockFetch.mockReturnValueOnce(new Promise(() => {}));
		await fireEvent.click(screen.getByText('Frontend Jobs'));

		await waitFor(() => {
			expect(screen.getByText(/loading/i)).toBeInTheDocument();
		});
	});

	// --- Empty results message ---

	it('shows empty message when profile has no persisted results', async () => {
		mockJsonResponse([MOCK_PROFILE_NO_RESULTS]);
		render(SearchPage);

		await waitFor(() => {
			expect(screen.getByText('Backend Jobs')).toBeInTheDocument();
		});

		// Profile with no results returns empty array
		mockJsonResponse([]);
		await fireEvent.click(screen.getByText('Backend Jobs'));

		await waitFor(() => {
			expect(screen.getByText(/no results/i)).toBeInTheDocument();
		});
	});

	it('updates empty message to reflect that a search can be run rather than prompting to select a profile', async () => {
		mockJsonResponse([MOCK_PROFILE_NO_RESULTS]);
		render(SearchPage);

		await waitFor(() => {
			expect(screen.getByText('Backend Jobs')).toBeInTheDocument();
		});

		mockJsonResponse([]);
		await fireEvent.click(screen.getByText('Backend Jobs'));

		await waitFor(() => {
			// After selecting a profile with no results, the message should NOT say "select a profile"
			expect(screen.queryByText(/select a search profile/i)).not.toBeInTheDocument();
			// Instead it should indicate running a search or that there are no results yet
			expect(screen.getByText(/no results|run a search/i)).toBeInTheDocument();
		});
	});
});

describe('Search Page — results header with count and timestamp', () => {
	let SearchPage: typeof import('./+page.svelte').default;

	beforeEach(async () => {
		mockFetch.mockReset();
		const mod = await import('./+page.svelte');
		SearchPage = mod.default;
	});

	it('shows result count after selecting a profile with postings', async () => {
		mockJsonResponse([MOCK_PROFILE]);
		render(SearchPage);

		await waitFor(() => {
			expect(screen.getByText('Frontend Jobs')).toBeInTheDocument();
		});

		mockJsonResponse(MOCK_POSTINGS);
		await fireEvent.click(screen.getByText('Frontend Jobs'));

		await waitFor(() => {
			expect(screen.getByText(/2 results/i)).toBeInTheDocument();
		});
	});

	it('shows last run timestamp when profile has last_run_at', async () => {
		mockJsonResponse([MOCK_PROFILE]);
		render(SearchPage);

		await waitFor(() => {
			expect(screen.getByText('Frontend Jobs')).toBeInTheDocument();
		});

		mockJsonResponse(MOCK_POSTINGS);
		await fireEvent.click(screen.getByText('Frontend Jobs'));

		await waitFor(() => {
			// last_run_at is '2026-03-24T12:00:00' — should be displayed as a readable timestamp
			expect(screen.getByText(/last run/i)).toBeInTheDocument();
		});
	});

	it('does not show last run timestamp when profile has no last_run_at', async () => {
		mockJsonResponse([MOCK_PROFILE_NO_RESULTS]);
		render(SearchPage);

		await waitFor(() => {
			expect(screen.getByText('Backend Jobs')).toBeInTheDocument();
		});

		mockJsonResponse([]);
		await fireEvent.click(screen.getByText('Backend Jobs'));

		await waitFor(() => {
			expect(screen.queryByText(/last run/i)).not.toBeInTheDocument();
		});
	});

	it('shows delta summary after running a search', async () => {
		mockJsonResponse([MOCK_PROFILE]);
		render(SearchPage);

		await waitFor(() => {
			expect(screen.getByText('Frontend Jobs')).toBeInTheDocument();
		});

		// Select the profile first
		mockJsonResponse(MOCK_POSTINGS);
		await fireEvent.click(screen.getByText('Frontend Jobs'));

		await waitFor(() => {
			expect(screen.getByText('Senior Frontend Developer')).toBeInTheDocument();
		});

		// Run search — returns new_count and total_count
		mockJsonResponse({ new_count: 3, total_count: 15 });
		// After run, it reloads postings
		mockJsonResponse(MOCK_POSTINGS);
		// Then reloads profiles
		mockJsonResponse([MOCK_PROFILE]);

		await fireEvent.click(screen.getByText('Refresh'));

		await waitFor(() => {
			expect(screen.getByText(/3 new/)).toBeInTheDocument();
			expect(screen.getByText(/15 total/)).toBeInTheDocument();
		});
	});

	it('labels the search button as Refresh instead of Run Search', async () => {
		mockJsonResponse([MOCK_PROFILE]);
		render(SearchPage);

		await waitFor(() => {
			expect(screen.getByText('Frontend Jobs')).toBeInTheDocument();
		});

		mockJsonResponse(MOCK_POSTINGS);
		await fireEvent.click(screen.getByText('Frontend Jobs'));

		await waitFor(() => {
			expect(screen.getByText('Senior Frontend Developer')).toBeInTheDocument();
		});

		// The button should say "Refresh", not "Run Search"
		expect(screen.queryByText('Run Search')).not.toBeInTheDocument();
		expect(screen.getByText('Refresh')).toBeInTheDocument();
	});

	it('shows zero results count when profile has no postings', async () => {
		mockJsonResponse([MOCK_PROFILE_NO_RESULTS]);
		render(SearchPage);

		await waitFor(() => {
			expect(screen.getByText('Backend Jobs')).toBeInTheDocument();
		});

		mockJsonResponse([]);
		await fireEvent.click(screen.getByText('Backend Jobs'));

		await waitFor(() => {
			expect(screen.getByText(/0 results/i)).toBeInTheDocument();
		});
	});
});

// --- Additional mock postings for delta tests ---

const MOCK_POSTING_NEW: JobPosting = {
	id: 12,
	title: 'Vue.js Developer',
	company: { id: 3, name: 'StartupXYZ', website: null, glassdoor_rating: null, glassdoor_url: null, levels_salary_data: null, levels_url: null, blind_url: null, employee_count: null, industry: null, notes: null, common_questions: null, last_researched_at: null, created_at: '2026-03-20T00:00:00' },
	company_name: 'StartupXYZ',
	description: 'Vue work',
	location: 'Remote',
	remote_type: 'remote',
	salary_min: 110000,
	salary_max: 160000,
	url: 'https://example.com/job/12',
	source: 'indeed',
	date_posted: '2026-03-24T00:00:00',
	date_saved: '2026-03-25T00:00:00',
	status: 'new',
	tier: null,
	pipeline_stage: null,
	has_raw_content: false,
	notes: null,
	lead_source: 'cold_apply',
};

const MOCK_POSTING_NEW_2: JobPosting = {
	id: 13,
	title: 'Angular Developer',
	company: { id: 4, name: 'MegaCorp', website: null, glassdoor_rating: null, glassdoor_url: null, levels_salary_data: null, levels_url: null, blind_url: null, employee_count: null, industry: null, notes: null, common_questions: null, last_researched_at: null, created_at: '2026-03-20T00:00:00' },
	company_name: 'MegaCorp',
	description: 'Angular work',
	location: 'SF',
	remote_type: null,
	salary_min: 130000,
	salary_max: 190000,
	url: 'https://example.com/job/13',
	source: 'indeed',
	date_posted: '2026-03-24T00:00:00',
	date_saved: '2026-03-25T00:00:00',
	status: 'new',
	tier: null,
	pipeline_stage: null,
	has_raw_content: false,
	notes: null,
	lead_source: 'cold_apply',
};

/**
 * Helper to set up a profile with initial postings selected.
 * Returns after the profile is selected and postings are loaded.
 */
async function selectProfileWithPostings(
	SearchPage: typeof import('./+page.svelte').default,
	profile: SearchProfile,
	initialPostings: JobPosting[],
) {
	mockJsonResponse([profile]);
	render(SearchPage);

	await waitFor(() => {
		expect(screen.getByText(profile.name)).toBeInTheDocument();
	});

	mockJsonResponse(initialPostings);
	await fireEvent.click(screen.getByText(profile.name));

	if (initialPostings.length > 0) {
		await waitFor(() => {
			expect(screen.getByText(initialPostings[0].title)).toBeInTheDocument();
		});
	} else {
		await waitFor(() => {
			expect(screen.getByText(/no results/i)).toBeInTheDocument();
		});
	}
}

describe('Search Page — delta tracking on refresh', () => {
	let SearchPage: typeof import('./+page.svelte').default;

	beforeEach(async () => {
		mockFetch.mockReset();
		const mod = await import('./+page.svelte');
		SearchPage = mod.default;
	});

	it('identifies added postings after refresh by passing addedIds to results table', async () => {
		// Initial state: postings [10, 11]
		await selectProfileWithPostings(SearchPage, MOCK_PROFILE, MOCK_POSTINGS);

		// Refresh: run returns, then postings now [11, 12] — posting 10 removed, 12 added
		mockJsonResponse({ new_count: 1, total_count: 2 });
		mockJsonResponse([MOCK_POSTINGS[1], MOCK_POSTING_NEW]); // postings after refresh
		mockJsonResponse([MOCK_PROFILE]); // profile list reload

		await fireEvent.click(screen.getByText('Refresh'));

		await waitFor(() => {
			expect(screen.getByText('Vue.js Developer')).toBeInTheDocument();
		});

		// The new posting (id 12) should be marked as added via a data attribute or CSS class
		const newRow = screen.getByText('Vue.js Developer').closest('tr');
		expect(newRow).toHaveAttribute('data-delta', 'added');
	});

	it('does not mark any postings as added on first refresh with no prior results', async () => {
		// Initial state: no postings
		await selectProfileWithPostings(SearchPage, MOCK_PROFILE_NO_RESULTS, []);

		// Refresh: returns postings for the first time
		mockJsonResponse({ new_count: 2, total_count: 2 });
		mockJsonResponse(MOCK_POSTINGS); // postings after refresh
		mockJsonResponse([MOCK_PROFILE_NO_RESULTS]); // profile list reload

		await fireEvent.click(screen.getByText('Refresh'));

		await waitFor(() => {
			expect(screen.getByText('Senior Frontend Developer')).toBeInTheDocument();
		});

		// No postings should be marked as added since this is the first load
		const rows = screen.getAllByRole('row').filter((row) => row.closest('tbody'));
		rows.forEach((row) => {
			expect(row).not.toHaveAttribute('data-delta', 'added');
		});
	});

	it('tracks removed postings that disappear after refresh', async () => {
		// Initial state: postings [10, 11]
		await selectProfileWithPostings(SearchPage, MOCK_PROFILE, MOCK_POSTINGS);

		// Refresh: posting 10 disappears, posting 12 added → results now [11, 12]
		mockJsonResponse({ new_count: 1, total_count: 2 });
		mockJsonResponse([MOCK_POSTINGS[1], MOCK_POSTING_NEW]);
		mockJsonResponse([MOCK_PROFILE]);

		await fireEvent.click(screen.getByText('Refresh'));

		await waitFor(() => {
			expect(screen.getByText('Vue.js Developer')).toBeInTheDocument();
		});

		// The removed posting (id 10, "Senior Frontend Developer") should still be visible
		// in a removed/collapsed section, not just vanished
		expect(screen.getByText('Senior Frontend Developer')).toBeInTheDocument();
	});

	it('clears delta state when switching to a different profile', async () => {
		// Set up with two profiles
		mockJsonResponse([MOCK_PROFILE, MOCK_PROFILE_NO_RESULTS]);
		render(SearchPage);

		await waitFor(() => {
			expect(screen.getByText('Frontend Jobs')).toBeInTheDocument();
		});

		// Select first profile with postings
		mockJsonResponse(MOCK_POSTINGS);
		await fireEvent.click(screen.getByText('Frontend Jobs'));

		await waitFor(() => {
			expect(screen.getByText('Senior Frontend Developer')).toBeInTheDocument();
		});

		// Refresh to produce deltas: posting 10 removed, 12 added
		mockJsonResponse({ new_count: 1, total_count: 2 });
		mockJsonResponse([MOCK_POSTINGS[1], MOCK_POSTING_NEW]);
		mockJsonResponse([MOCK_PROFILE, MOCK_PROFILE_NO_RESULTS]);

		await fireEvent.click(screen.getByText('Refresh'));

		await waitFor(() => {
			expect(screen.getByText('Vue.js Developer')).toBeInTheDocument();
		});

		// Switch to second profile — deltas should be cleared
		mockJsonResponse([]);
		await fireEvent.click(screen.getByText('Backend Jobs'));

		await waitFor(() => {
			expect(screen.getByText(/no results/i)).toBeInTheDocument();
		});

		// Switch back to first profile — no delta markers should persist
		mockJsonResponse([MOCK_POSTINGS[1], MOCK_POSTING_NEW]);
		await fireEvent.click(screen.getByText('Frontend Jobs'));

		await waitFor(() => {
			expect(screen.getByText('Vue.js Developer')).toBeInTheDocument();
		});

		// No added markers should be present since deltas were cleared
		const newRow = screen.getByText('Vue.js Developer').closest('tr');
		expect(newRow).not.toHaveAttribute('data-delta', 'added');
	});
});

describe('Search Page — acknowledge deltas', () => {
	let SearchPage: typeof import('./+page.svelte').default;

	beforeEach(async () => {
		mockFetch.mockReset();
		const mod = await import('./+page.svelte');
		SearchPage = mod.default;
	});

	it('clears delta highlights and calls markReviewed when acknowledging', async () => {
		// Select profile and get initial postings
		await selectProfileWithPostings(SearchPage, MOCK_PROFILE, MOCK_POSTINGS);

		// Refresh to produce deltas: new posting 12 added
		mockJsonResponse({ new_count: 1, total_count: 3 });
		mockJsonResponse([...MOCK_POSTINGS, MOCK_POSTING_NEW]);
		mockJsonResponse([MOCK_PROFILE]);

		await fireEvent.click(screen.getByText('Refresh'));

		await waitFor(() => {
			expect(screen.getByText('Vue.js Developer')).toBeInTheDocument();
		});

		// Verify the added posting is marked
		const addedRow = screen.getByText('Vue.js Developer').closest('tr');
		expect(addedRow).toHaveAttribute('data-delta', 'added');

		// Click acknowledge to clear deltas
		mockJsonResponse({}); // markReviewed response
		mockJsonResponse([{ ...MOCK_PROFILE, new_result_count: 0 }]); // profiles reload

		await fireEvent.click(screen.getByText('Mark All Reviewed'));

		// Verify markReviewed API was called
		await waitFor(() => {
			expect(mockFetch).toHaveBeenCalledWith(
				expect.stringContaining('/search-results/1/mark-reviewed'),
				expect.objectContaining({ method: 'POST' }),
			);
		});

		// After acknowledging, delta highlights should be cleared
		await waitFor(() => {
			const row = screen.getByText('Vue.js Developer').closest('tr');
			expect(row).not.toHaveAttribute('data-delta', 'added');
		});
	});
});

describe('Search Page — individual actions clear delta state', () => {
	let SearchPage: typeof import('./+page.svelte').default;

	beforeEach(async () => {
		mockFetch.mockReset();
		const mod = await import('./+page.svelte');
		SearchPage = mod.default;
	});

	it('saving a posting that was marked as added removes it from results and addedIds', async () => {
		// Select profile with initial postings [10, 11]
		await selectProfileWithPostings(SearchPage, MOCK_PROFILE, MOCK_POSTINGS);

		// Refresh: adds posting 12 → results now [10, 11, 12]
		mockJsonResponse({ new_count: 1, total_count: 3 });
		mockJsonResponse([...MOCK_POSTINGS, MOCK_POSTING_NEW]);
		mockJsonResponse([MOCK_PROFILE]);

		await fireEvent.click(screen.getByText('Refresh'));

		await waitFor(() => {
			expect(screen.getByText('Vue.js Developer')).toBeInTheDocument();
		});

		// Save the newly added posting (id 12)
		mockJsonResponse({}); // save response

		// Find the Save button in the row for Vue.js Developer
		const row = screen.getByText('Vue.js Developer').closest('tr')!;
		const saveBtn = row.querySelector('button.btn-primary')!;
		await fireEvent.click(saveBtn);

		// The posting should be removed from results entirely
		await waitFor(() => {
			expect(screen.queryByText('Vue.js Developer')).not.toBeInTheDocument();
		});
	});

	it('dismissing a posting that was marked as added removes it from results and addedIds', async () => {
		// Select profile with initial postings [10, 11]
		await selectProfileWithPostings(SearchPage, MOCK_PROFILE, MOCK_POSTINGS);

		// Refresh: adds posting 12 → results now [10, 11, 12]
		mockJsonResponse({ new_count: 1, total_count: 3 });
		mockJsonResponse([...MOCK_POSTINGS, MOCK_POSTING_NEW]);
		mockJsonResponse([MOCK_PROFILE]);

		await fireEvent.click(screen.getByText('Refresh'));

		await waitFor(() => {
			expect(screen.getByText('Vue.js Developer')).toBeInTheDocument();
		});

		// Dismiss the newly added posting (id 12)
		mockJsonResponse({}); // dismiss response

		const row = screen.getByText('Vue.js Developer').closest('tr')!;
		const dismissBtn = row.querySelector('button.btn-danger')!;
		await fireEvent.click(dismissBtn);

		// The posting should be removed from results entirely
		await waitFor(() => {
			expect(screen.queryByText('Vue.js Developer')).not.toBeInTheDocument();
		});
	});
});

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

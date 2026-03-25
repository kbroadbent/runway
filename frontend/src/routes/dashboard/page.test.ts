import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/svelte';
import type { DashboardResponse } from '$lib/types';

// Mock fetch globally
const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

const EMPTY_DASHBOARD: DashboardResponse = {
	lane_counts: {
		Interested: 0,
		Applying: 0,
		Applied: 0,
		'Recruiter Screen': 0,
		'Tech Screen': 0,
		Onsite: 0,
		Offer: 0,
		Rejected: 0,
		Archived: 0,
	},
	action_items: [],
};

const POPULATED_DASHBOARD: DashboardResponse = {
	lane_counts: {
		Interested: 3,
		Applying: 1,
		Applied: 2,
		'Recruiter Screen': 1,
		'Tech Screen': 0,
		Onsite: 0,
		Offer: 0,
		Rejected: 1,
		Archived: 0,
	},
	action_items: [
		{
			pipeline_entry_id: 1,
			job_title: 'Frontend Dev',
			company_name: 'Acme Corp',
			type: 'action',
			description: 'Submit application',
			date: '2026-03-25T00:00:00',
			is_overdue: false,
		},
		{
			pipeline_entry_id: 2,
			job_title: 'Backend Dev',
			company_name: 'BigCo',
			type: 'interview',
			description: 'Technical round',
			date: '2026-03-20T00:00:00',
			is_overdue: true,
		},
	],
};

function mockDashboardResponse(data: DashboardResponse) {
	mockFetch.mockResolvedValueOnce({
		ok: true,
		status: 200,
		json: () => Promise.resolve(data),
	});
}

describe('Dashboard Page', () => {
	let DashboardPage: typeof import('./+page.svelte').default;

	beforeEach(async () => {
		mockFetch.mockReset();
		const mod = await import('./+page.svelte');
		DashboardPage = mod.default;
	});

	// --- Fetches data on mount ---

	it('calls GET /api/dashboard on mount', async () => {
		mockDashboardResponse(EMPTY_DASHBOARD);
		render(DashboardPage);

		await waitFor(() => {
			expect(mockFetch).toHaveBeenCalledWith(
				expect.stringContaining('/dashboard'),
				expect.any(Object),
			);
		});
	});

	// --- Lane counts rendering ---

	it('displays lane counts from the API response', async () => {
		mockDashboardResponse(POPULATED_DASHBOARD);
		render(DashboardPage);

		await waitFor(() => {
			expect(screen.getByText('Interested')).toBeInTheDocument();
			expect(screen.getByText('3')).toBeInTheDocument();
		});
	});

	it('displays multiple lane counts', async () => {
		mockDashboardResponse(POPULATED_DASHBOARD);
		render(DashboardPage);

		await waitFor(() => {
			expect(screen.getByText('Applied')).toBeInTheDocument();
			expect(screen.getByText('Applying')).toBeInTheDocument();
		});
	});

	it('shows zero counts for empty lanes', async () => {
		mockDashboardResponse(EMPTY_DASHBOARD);
		render(DashboardPage);

		await waitFor(() => {
			expect(screen.getByText('Interested')).toBeInTheDocument();
		});
	});

	// --- Action items rendering ---

	it('displays action item job titles', async () => {
		mockDashboardResponse(POPULATED_DASHBOARD);
		render(DashboardPage);

		await waitFor(() => {
			expect(screen.getByText('Frontend Dev')).toBeInTheDocument();
			expect(screen.getByText('Backend Dev')).toBeInTheDocument();
		});
	});

	it('displays action item descriptions', async () => {
		mockDashboardResponse(POPULATED_DASHBOARD);
		render(DashboardPage);

		await waitFor(() => {
			expect(screen.getByText('Submit application')).toBeInTheDocument();
			expect(screen.getByText('Technical round')).toBeInTheDocument();
		});
	});

	it('displays company names for action items', async () => {
		mockDashboardResponse(POPULATED_DASHBOARD);
		render(DashboardPage);

		await waitFor(() => {
			expect(screen.getByText('Acme Corp')).toBeInTheDocument();
		});
	});

	it('shows empty state when no action items exist', async () => {
		mockDashboardResponse(EMPTY_DASHBOARD);
		render(DashboardPage);

		await waitFor(() => {
			// Should not show action item content when list is empty
			expect(screen.queryByText('Submit application')).not.toBeInTheDocument();
		});
	});

	// --- Loading / error states ---

	it('shows a loading indicator before data arrives', () => {
		// Never resolve the fetch
		mockFetch.mockReturnValueOnce(new Promise(() => {}));
		render(DashboardPage);

		// Should show some loading state (text or spinner)
		expect(screen.getByText(/loading/i)).toBeInTheDocument();
	});

	it('shows an error message when the API call fails', async () => {
		mockFetch.mockResolvedValueOnce({
			ok: false,
			status: 500,
			statusText: 'Internal Server Error',
			json: () => Promise.resolve({ detail: 'something broke' }),
		});
		render(DashboardPage);

		await waitFor(() => {
			expect(screen.getByText(/error|failed/i)).toBeInTheDocument();
		});
	});
});

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import PipelineDetailPanel from './PipelineDetailPanel.svelte';
import type { PipelineEntry, PipelineHistory } from '$lib/types';

const { mockDeleteHistory, mockHistory, mockInterviews } = vi.hoisted(() => ({
	mockDeleteHistory: vi.fn(() => Promise.resolve()),
	mockHistory: vi.fn(() => Promise.resolve([])),
	mockInterviews: vi.fn(() => Promise.resolve([])),
}));

vi.mock('$lib/api', () => ({
	pipeline: {
		history: mockHistory,
		interviews: mockInterviews,
		update: vi.fn(() => Promise.resolve({})),
		addEvent: vi.fn(() => Promise.resolve({})),
		addInterview: vi.fn(() => Promise.resolve({})),
		customDates: vi.fn(() => Promise.resolve([])),
		createCustomDate: vi.fn(() => Promise.resolve({})),
		updateCustomDate: vi.fn(() => Promise.resolve({})),
		deleteCustomDate: vi.fn(() => Promise.resolve()),
		comments: vi.fn(() => Promise.resolve([])),
	},
	postings: {
		update: vi.fn(() => Promise.resolve({})),
	},
	pipelineHistory: {
		delete: mockDeleteHistory,
	},
	interviews: {
		delete: vi.fn(() => Promise.resolve()),
		update: vi.fn(() => Promise.resolve({})),
	},
	pipelineComments: {
		delete: vi.fn(() => Promise.resolve()),
		update: vi.fn(() => Promise.resolve({})),
	},
}));

function makeEntry(overrides: Partial<PipelineEntry> = {}): PipelineEntry {
	return {
		id: 1,
		stage: 'applied',
		position: 0,
		next_action: null,
		next_action_date: null,
		applied_date: null,
		recruiter_screen_date: null,
		manager_screen_date: null,
		tech_screen_date: null,
		onsite_date: null,
		offer_date: null,
		offer_expiration_date: null,
		custom_dates: [],
		created_at: '2026-01-01T00:00:00',
		updated_at: '2026-01-01T00:00:00',
		job_posting: {
			id: 1,
			title: 'Software Engineer',
			company: null,
			company_name: 'Acme Corp',
			description: null,
			location: null,
			remote_type: null,
			salary_min: null,
			salary_max: null,
			url: null,
			source: 'manual',
			date_posted: null,
			date_saved: '2026-01-01T00:00:00',
			status: 'saved',
			tier: null,
			pipeline_stage: 'applied',
			has_raw_content: false,
			notes: null,
			lead_source: 'cold_apply',
			is_closed_detected: false,
			closed_check_dismissed: false,
		},
		...overrides,
	};
}

function makeHistoryItem(overrides: Partial<PipelineHistory> = {}): PipelineHistory {
	return {
		id: 1,
		event_type: 'stage_change',
		from_stage: null,
		to_stage: 'applied',
		note: null,
		description: null,
		event_date: null,
		changed_at: '2026-01-01T00:00:00',
		...overrides,
	};
}

function renderPanel(entry: PipelineEntry = makeEntry()) {
	return render(PipelineDetailPanel, {
		props: {
			entry,
			onClose: vi.fn(),
			onUpdated: vi.fn(),
		},
	});
}

async function navigateToHistoryTab() {
	await fireEvent.click(screen.getByRole('button', { name: 'History' }));
}

beforeEach(() => {
	vi.clearAllMocks();
	mockHistory.mockResolvedValue([]);
	mockInterviews.mockResolvedValue([]);
});

describe('PipelineDetailPanel — history tab delete button', () => {
	it('shows a delete button for each history item', async () => {
		mockHistory.mockResolvedValue([
			makeHistoryItem({ id: 1 }),
			makeHistoryItem({ id: 2 }),
		]);
		renderPanel();
		await navigateToHistoryTab();

		await waitFor(() => {
			expect(screen.getAllByRole('button', { name: /delete/i })).toHaveLength(2);
		});
	});

	it('does not call window.confirm when delete is clicked on a history item', async () => {
		const confirmSpy = vi.spyOn(window, 'confirm');
		mockHistory.mockResolvedValue([makeHistoryItem({ id: 1 })]);
		renderPanel();
		await navigateToHistoryTab();

		await waitFor(() => screen.getByRole('button', { name: /delete/i }));
		await fireEvent.click(screen.getByRole('button', { name: /delete/i }));

		expect(confirmSpy).not.toHaveBeenCalled();
		confirmSpy.mockRestore();
	});

	it('shows Confirm and Cancel buttons inline after clicking delete', async () => {
		mockHistory.mockResolvedValue([makeHistoryItem({ id: 1 })]);
		renderPanel();
		await navigateToHistoryTab();

		await waitFor(() => screen.getByRole('button', { name: /delete/i }));
		await fireEvent.click(screen.getByRole('button', { name: /delete/i }));

		expect(screen.getByRole('button', { name: /confirm/i })).toBeInTheDocument();
		expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
	});

	it('hides the inline confirmation and does not call the API when Cancel is clicked', async () => {
		mockHistory.mockResolvedValue([makeHistoryItem({ id: 1 })]);
		renderPanel();
		await navigateToHistoryTab();

		await waitFor(() => screen.getByRole('button', { name: /delete/i }));
		await fireEvent.click(screen.getByRole('button', { name: /delete/i }));
		await fireEvent.click(screen.getByRole('button', { name: /cancel/i }));

		expect(mockDeleteHistory).not.toHaveBeenCalled();
		expect(screen.queryByRole('button', { name: /confirm/i })).not.toBeInTheDocument();
	});

	it('calls pipelineHistory.delete with the correct id when Confirm is clicked', async () => {
		mockHistory.mockResolvedValue([makeHistoryItem({ id: 42 })]);
		renderPanel();
		await navigateToHistoryTab();

		await waitFor(() => screen.getByRole('button', { name: /delete/i }));
		await fireEvent.click(screen.getByRole('button', { name: /delete/i }));
		await fireEvent.click(screen.getByRole('button', { name: /confirm/i }));

		expect(mockDeleteHistory).toHaveBeenCalledWith(42);
	});

	it('removes the confirmed-delete item from the list without a page reload', async () => {
		mockHistory.mockResolvedValue([
			makeHistoryItem({ id: 1, event_type: 'manual', description: 'Coffee chat with manager', to_stage: null }),
		]);
		renderPanel();
		await navigateToHistoryTab();

		await waitFor(() => screen.getByText('Coffee chat with manager'));

		await fireEvent.click(screen.getByRole('button', { name: /delete/i }));
		await fireEvent.click(screen.getByRole('button', { name: /confirm/i }));

		await waitFor(() => {
			expect(screen.queryByText('Coffee chat with manager')).not.toBeInTheDocument();
		});
	});
});

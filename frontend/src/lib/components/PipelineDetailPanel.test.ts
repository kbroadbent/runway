import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import PipelineDetailPanel from './PipelineDetailPanel.svelte';
import type { PipelineEntry, PipelineHistory, InterviewNote } from '$lib/types';

const { mockDeleteHistory, mockHistory, mockInterviews, mockUpdateInterview } = vi.hoisted(() => ({
	mockDeleteHistory: vi.fn(),
	mockHistory: vi.fn(),
	mockInterviews: vi.fn(),
	mockUpdateInterview: vi.fn(),
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
		update: mockUpdateInterview,
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

async function navigateToInterviewsTab() {
	await fireEvent.click(screen.getByRole('button', { name: 'Interviews' }));
}

beforeEach(() => {
	vi.clearAllMocks();
	mockHistory.mockResolvedValue([]);
	mockInterviews.mockResolvedValue([]);
	mockUpdateInterview.mockResolvedValue({});
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

describe('PipelineDetailPanel — interview add form', () => {
	it('uses a date input instead of datetime-local for the scheduled date', async () => {
		renderPanel();
		await navigateToInterviewsTab();
		await fireEvent.click(screen.getByRole('button', { name: /add interview note/i }));

		expect(document.body.querySelector('input[type="datetime-local"]')).toBeNull();
		expect(document.body.querySelector('input[type="date"]')).not.toBeNull();
	});

	it('does not include an outcome field', async () => {
		renderPanel();
		await navigateToInterviewsTab();
		await fireEvent.click(screen.getByRole('button', { name: /add interview note/i }));

		expect(screen.queryByText(/^outcome$/i)).not.toBeInTheDocument();
	});
});

describe('PipelineDetailPanel — interview card display', () => {
	it('does not show an outcome badge even when the server returns an outcome value', async () => {
		mockInterviews.mockResolvedValue([
			{ id: 1, round: 'Phone Screen', scheduled_at: null, interviewers: null, notes: null, created_at: '2026-01-01T00:00:00' },
		]);
		renderPanel();
		await navigateToInterviewsTab();
		await waitFor(() => screen.getByText('Phone Screen'));

		expect(screen.queryByText('passed')).not.toBeInTheDocument();
	});
});

describe('PipelineDetailPanel — interview edit form', () => {
	it('shows an edit button for each interview note', async () => {
		mockInterviews.mockResolvedValue([
			{ id: 1, round: 'Phone Screen', scheduled_at: null, interviewers: null, notes: null, created_at: '2026-01-01T00:00:00' },
			{ id: 2, round: 'Technical', scheduled_at: null, interviewers: null, notes: null, created_at: '2026-01-01T00:00:00' },
		]);
		renderPanel();
		await navigateToInterviewsTab();

		await waitFor(() => {
			expect(screen.getAllByRole('button', { name: /^edit$/i })).toHaveLength(2);
		});
	});

	it('clicking Edit shows a pre-filled form with the note\'s current round', async () => {
		mockInterviews.mockResolvedValue([
			{ id: 1, round: 'Phone Screen', scheduled_at: null, interviewers: null, notes: 'Great call', created_at: '2026-01-01T00:00:00' },
		]);
		renderPanel();
		await navigateToInterviewsTab();

		await waitFor(() => screen.getByRole('button', { name: /^edit$/i }));
		await fireEvent.click(screen.getByRole('button', { name: /^edit$/i }));

		expect(screen.getByDisplayValue('Phone Screen')).toBeInTheDocument();
	});

	it('saving the edit form calls interviews.update with the note id and current data', async () => {
		mockInterviews.mockResolvedValue([
			{ id: 42, round: 'Phone Screen', scheduled_at: null, interviewers: null, notes: null, created_at: '2026-01-01T00:00:00' },
		]);
		renderPanel();
		await navigateToInterviewsTab();

		await waitFor(() => screen.getByRole('button', { name: /^edit$/i }));
		await fireEvent.click(screen.getByRole('button', { name: /^edit$/i }));
		await fireEvent.click(screen.getByRole('button', { name: /^save$/i }));

		expect(mockUpdateInterview).toHaveBeenCalledWith(42, expect.objectContaining({ round: 'Phone Screen' }));
	});

	it('pressing Ctrl+Enter in the edit form notes field saves the interview', async () => {
		mockInterviews.mockResolvedValue([
			{ id: 42, round: 'Phone Screen', scheduled_at: null, interviewers: null, notes: null, created_at: '2026-01-01T00:00:00' },
		]);
		renderPanel();
		await navigateToInterviewsTab();

		await waitFor(() => screen.getByRole('button', { name: /^edit$/i }));
		await fireEvent.click(screen.getByRole('button', { name: /^edit$/i }));

		const notesTextarea = screen.getByRole('textbox', { name: /notes/i });
		await fireEvent.keyDown(notesTextarea, { key: 'Enter', ctrlKey: true });

		expect(mockUpdateInterview).toHaveBeenCalledWith(42, expect.anything());
	});
});

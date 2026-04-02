import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/svelte';
import PostingDetailPanel from './PostingDetailPanel.svelte';
import type { JobPosting } from '$lib/types';

// Mock the API (use vi.hoisted so mockUpdate is available inside the hoisted factory)
const { mockUpdate } = vi.hoisted(() => ({ mockUpdate: vi.fn() }));
vi.mock('$lib/api', () => ({
	postings: {
		update: mockUpdate,
		delete: vi.fn(() => Promise.resolve()),
		linkCompany: vi.fn(() => Promise.resolve()),
		summarize: vi.fn(() => Promise.resolve({})),
	},
}));

// Mock marked and dompurify to avoid jsdom rendering issues
vi.mock('marked', () => ({
	marked: { parse: (text: string) => text },
}));
vi.mock('dompurify', () => ({
	default: { sanitize: (html: string) => html },
}));

function makePosting(overrides: Partial<JobPosting> = {}): JobPosting {
	return {
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
		date_saved: '2026-03-26T00:00:00',
		status: 'saved',
		tier: null,
		pipeline_stage: null,
		has_raw_content: false,
		notes: null,
		lead_source: 'cold_apply',
		is_closed_detected: false,
		closed_check_dismissed: false,
		...overrides,
	};
}

function renderPanel(posting: JobPosting = makePosting()) {
	return render(PostingDetailPanel, {
		props: {
			posting,
			onClose: vi.fn(),
			onDeleted: vi.fn(),
			onUpdated: vi.fn(),
		},
	});
}

beforeEach(() => {
	vi.clearAllMocks();
	// Suppress confirm dialog in delete tests
	vi.stubGlobal('confirm', () => true);
});

describe('PostingDetailPanel — view mode lead_source badge', () => {
	it('shows the human-readable lead_source label in view mode', () => {
		renderPanel(makePosting({ lead_source: 'cold_apply' }));
		expect(screen.getByText('Cold Apply')).toBeInTheDocument();
	});

	it('shows Referral label for referral lead_source', () => {
		renderPanel(makePosting({ lead_source: 'referral' }));
		expect(screen.getByText('Referral')).toBeInTheDocument();
	});

	it('shows Recruiter (Inbound) label for recruiter_inbound lead_source', () => {
		renderPanel(makePosting({ lead_source: 'recruiter_inbound' }));
		expect(screen.getByText('Recruiter (Inbound)')).toBeInTheDocument();
	});

	it('shows Recruiter (Outbound) label for recruiter_outbound lead_source', () => {
		renderPanel(makePosting({ lead_source: 'recruiter_outbound' }));
		expect(screen.getByText('Recruiter (Outbound)')).toBeInTheDocument();
	});

	it('does not show lead source select in view mode', () => {
		renderPanel(makePosting({ lead_source: 'cold_apply' }));
		// In view mode there should be no "Lead Source" label
		expect(screen.queryByLabelText(/lead source/i)).not.toBeInTheDocument();
	});
});

describe('PostingDetailPanel — edit mode lead_source select', () => {
	async function enterEditMode(posting: JobPosting = makePosting()) {
		renderPanel(posting);
		await fireEvent.click(screen.getByRole('button', { name: /edit/i }));
	}

	it('shows a lead source select in edit mode', async () => {
		await enterEditMode();
		// The select options should include all four lead source labels
		expect(screen.getByText('Cold Apply')).toBeInTheDocument();
		expect(screen.getByText('Referral')).toBeInTheDocument();
		expect(screen.getByText('Recruiter (Inbound)')).toBeInTheDocument();
		expect(screen.getByText('Recruiter (Outbound)')).toBeInTheDocument();
	});

	it('initializes the lead source select with the current posting value', async () => {
		await enterEditMode(makePosting({ lead_source: 'referral' }));
		// Find select that contains lead source options
		const options = screen.getAllByRole('option', { name: 'Referral' });
		const selected = options.find((o) => (o as HTMLOptionElement).selected);
		expect(selected).toBeDefined();
	});

	it('shows a Lead Source label in the edit form', async () => {
		await enterEditMode();
		expect(screen.getByText(/lead source/i)).toBeInTheDocument();
	});

	it('shows the lead source help icon (LeadSourceTooltip) in edit mode', async () => {
		await enterEditMode();
		expect(screen.getByRole('button', { name: /lead source help/i })).toBeInTheDocument();
	});
});

describe('PostingDetailPanel — save includes lead_source', () => {
	it('calls postings.update with lead_source when saving', async () => {
		const updated = makePosting({ lead_source: 'cold_apply' });
		mockUpdate.mockResolvedValue(updated);

		renderPanel(makePosting({ lead_source: 'cold_apply' }));
		await fireEvent.click(screen.getByRole('button', { name: /edit/i }));
		await fireEvent.click(screen.getByRole('button', { name: /save/i }));

		expect(mockUpdate).toHaveBeenCalledOnce();
		const [, payload] = mockUpdate.mock.calls[0];
		expect(payload).toHaveProperty('lead_source');
	});

	it('calls postings.update with the changed lead_source value', async () => {
		const updated = makePosting({ lead_source: 'referral' });
		mockUpdate.mockResolvedValue(updated);

		renderPanel(makePosting({ lead_source: 'cold_apply' }));
		await fireEvent.click(screen.getByRole('button', { name: /edit/i }));

		// Change the lead source select to 'referral'
		const selects = screen.getAllByRole('combobox');
		const leadSourceSelect = selects.find((s) =>
			Array.from((s as HTMLSelectElement).options).some((o) => o.value === 'referral')
		) as HTMLSelectElement;
		expect(leadSourceSelect).toBeDefined();
		await fireEvent.change(leadSourceSelect, { target: { value: 'referral' } });

		await fireEvent.click(screen.getByRole('button', { name: /save/i }));

		const [, payload] = mockUpdate.mock.calls[0];
		expect(payload.lead_source).toBe('referral');
	});
});

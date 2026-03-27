import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/svelte';
import ImportModal from './ImportModal.svelte';

vi.mock('$lib/api', () => ({
	postings: {
		importPreview: vi.fn(),
		importConfirm: vi.fn(),
	},
	ApiError: class ApiError extends Error {
		status: number;
		data: unknown;
		constructor(message: string, status: number, data: unknown) {
			super(message);
			this.status = status;
			this.data = data;
		}
	},
}));

import { postings } from '$lib/api';

const defaultProps = {
	onClose: vi.fn(),
	onSaved: vi.fn(),
};

const mockPreview = {
	title: 'Software Engineer',
	company_name: 'Acme',
	location: 'Remote',
	remote_type: 'remote',
	salary_min: null,
	salary_max: null,
	description: 'A job',
	notes: null,
	url: 'https://example.com/job',
	raw_content: 'raw text',
	ai_used: false,
};

async function renderWithPreview(overrides = {}) {
	vi.mocked(postings.importPreview).mockResolvedValue(mockPreview);
	vi.mocked(postings.importConfirm).mockResolvedValue({ id: 1, ...mockPreview });

	const result = render(ImportModal, { props: { ...defaultProps, ...overrides } });

	// Type a URL and click Parse to trigger preview
	const urlInput = screen.getByPlaceholderText(/https:\/\//);
	await fireEvent.input(urlInput, { target: { value: 'https://example.com/job' } });
	const parseBtn = screen.getByRole('button', { name: /parse/i });
	await fireEvent.click(parseBtn);

	// Wait for the preview form to appear
	await screen.findByText(/review and edit/i);

	return result;
}

beforeEach(() => {
	vi.clearAllMocks();
});

describe('ImportModal lead_source', () => {
	it('shows a lead source select in the preview form', async () => {
		await renderWithPreview();
		// The lead source label should be visible in the preview form
		expect(screen.getByText('Lead Source')).toBeDefined();
	});

	it('lead source select defaults to cold_apply option', async () => {
		await renderWithPreview();
		// Find the select that has the cold apply option selected
		const selects = screen.getAllByRole('combobox') as HTMLSelectElement[];
		const leadSourceSelect = selects.find((s) =>
			Array.from(s.options).some((o) => o.value === 'cold_apply')
		);
		expect(leadSourceSelect).toBeDefined();
		expect(leadSourceSelect!.value).toBe('cold_apply');
	});

	it('lead source select has all four options', async () => {
		await renderWithPreview();
		const selects = screen.getAllByRole('combobox') as HTMLSelectElement[];
		const leadSourceSelect = selects.find((s) =>
			Array.from(s.options).some((o) => o.value === 'cold_apply')
		)!;
		const values = Array.from(leadSourceSelect.options).map((o) => o.value);
		expect(values).toContain('referral');
		expect(values).toContain('recruiter_inbound');
		expect(values).toContain('recruiter_outbound');
		expect(values).toContain('cold_apply');
	});

	it('renders a LeadSourceTooltip help button near the lead source select', async () => {
		await renderWithPreview();
		// The tooltip renders a button with aria-label "Lead source help"
		const helpBtn = screen.getByRole('button', { name: /lead source help/i });
		expect(helpBtn).toBeDefined();
	});

	it('includes lead_source in the save payload with default value', async () => {
		await renderWithPreview();
		await fireEvent.click(screen.getByRole('button', { name: /save posting/i }));
		expect(postings.importConfirm).toHaveBeenCalledOnce();
		const payload = vi.mocked(postings.importConfirm).mock.calls[0][0] as Record<string, unknown>;
		expect(payload.lead_source).toBe('cold_apply');
	});

	it('includes the selected lead_source in the save payload when changed', async () => {
		await renderWithPreview();
		const selects = screen.getAllByRole('combobox') as HTMLSelectElement[];
		const leadSourceSelect = selects.find((s) =>
			Array.from(s.options).some((o) => o.value === 'cold_apply')
		)!;
		await fireEvent.change(leadSourceSelect, { target: { value: 'referral' } });

		await fireEvent.click(screen.getByRole('button', { name: /save posting/i }));
		const payload = vi.mocked(postings.importConfirm).mock.calls[0][0] as Record<string, unknown>;
		expect(payload.lead_source).toBe('referral');
	});

	it('includes recruiter_outbound lead_source in save payload when selected', async () => {
		await renderWithPreview();
		const selects = screen.getAllByRole('combobox') as HTMLSelectElement[];
		const leadSourceSelect = selects.find((s) =>
			Array.from(s.options).some((o) => o.value === 'cold_apply')
		)!;
		await fireEvent.change(leadSourceSelect, { target: { value: 'recruiter_outbound' } });

		await fireEvent.click(screen.getByRole('button', { name: /save posting/i }));
		const payload = vi.mocked(postings.importConfirm).mock.calls[0][0] as Record<string, unknown>;
		expect(payload.lead_source).toBe('recruiter_outbound');
	});
});

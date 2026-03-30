import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/svelte';
import ImportForm from './ImportForm.svelte';

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

async function renderWithPreview(mode: 'url' | 'text' = 'url') {
	vi.mocked(postings.importPreview).mockResolvedValue(mockPreview);
	// eslint-disable-next-line @typescript-eslint/no-explicit-any
	vi.mocked(postings.importConfirm).mockResolvedValue({ id: 42, ...mockPreview } as any);

	render(ImportForm, { props: { mode } });

	if (mode === 'url') {
		const urlInput = screen.getByPlaceholderText(/https:\/\//);
		await fireEvent.input(urlInput, { target: { value: 'https://example.com/job' } });
	} else {
		const textarea = screen.getByPlaceholderText(/paste the full job posting text/i);
		await fireEvent.input(textarea, { target: { value: 'Some job text here' } });
	}

	const parseBtn = screen.getByRole('button', { name: /import/i });
	await fireEvent.click(parseBtn);

	await screen.findByText(/review and edit/i);
}

beforeEach(() => {
	vi.clearAllMocks();
});

describe('ImportForm — mode prop', () => {
	it('renders a URL input when mode is url', () => {
		render(ImportForm, { props: { mode: 'url' } });
		expect(screen.getByPlaceholderText(/https:\/\//)).toBeDefined();
	});

	it('renders a textarea when mode is text', () => {
		render(ImportForm, { props: { mode: 'text' } });
		expect(screen.getByPlaceholderText(/paste the full job posting text/i)).toBeDefined();
	});

	it('does not render a URL input when mode is text', () => {
		render(ImportForm, { props: { mode: 'text' } });
		expect(screen.queryByPlaceholderText(/https:\/\//)).toBeNull();
	});

	it('does not render a textarea when mode is url', () => {
		render(ImportForm, { props: { mode: 'url' } });
		expect(screen.queryByPlaceholderText(/paste the full job posting text/i)).toBeNull();
	});
});

describe('ImportForm — no modal wrapper', () => {
	it('does not render a close button', () => {
		render(ImportForm, { props: { mode: 'url' } });
		expect(screen.queryByRole('button', { name: /close|✕|×/i })).toBeNull();
	});

	it('does not render a modal backdrop', () => {
		const { container } = render(ImportForm, { props: { mode: 'url' } });
		expect(container.querySelector('.modal-backdrop')).toBeNull();
	});
});

describe('ImportForm — parse phase', () => {
	it('calls importPreview with url when mode is url', async () => {
		vi.mocked(postings.importPreview).mockResolvedValue(mockPreview);
		render(ImportForm, { props: { mode: 'url' } });

		const urlInput = screen.getByPlaceholderText(/https:\/\//);
		await fireEvent.input(urlInput, { target: { value: 'https://example.com/job' } });
		await fireEvent.click(screen.getByRole('button', { name: /import/i }));

		expect(postings.importPreview).toHaveBeenCalledWith({ url: 'https://example.com/job' });
	});

	it('calls importPreview with text when mode is text', async () => {
		vi.mocked(postings.importPreview).mockResolvedValue(mockPreview);
		render(ImportForm, { props: { mode: 'text' } });

		const textarea = screen.getByPlaceholderText(/paste the full job posting text/i);
		await fireEvent.input(textarea, { target: { value: 'Some job text here' } });
		await fireEvent.click(screen.getByRole('button', { name: /import/i }));

		expect(postings.importPreview).toHaveBeenCalledWith({ text: 'Some job text here' });
	});

	it('shows review form after successful parse', async () => {
		await renderWithPreview('url');
		expect(screen.getByText(/review and edit/i)).toBeDefined();
	});

	it('shows an error message when parse fails', async () => {
		vi.mocked(postings.importPreview).mockRejectedValue(new Error('Fetch failed'));
		render(ImportForm, { props: { mode: 'url' } });

		const urlInput = screen.getByPlaceholderText(/https:\/\//);
		await fireEvent.input(urlInput, { target: { value: 'https://example.com/job' } });
		await fireEvent.click(screen.getByRole('button', { name: /import/i }));

		expect(await screen.findByText(/fetch failed/i)).toBeDefined();
	});
});

describe('ImportForm — preview form', () => {
	it('populates title field from preview', async () => {
		await renderWithPreview();
		const titleInput = screen.getByDisplayValue('Software Engineer');
		expect(titleInput).toBeDefined();
	});

	it('populates company field from preview', async () => {
		await renderWithPreview();
		expect(screen.getByDisplayValue('Acme')).toBeDefined();
	});

	it('shows a back button to return to input phase', async () => {
		await renderWithPreview();
		expect(screen.getByRole('button', { name: /back/i })).toBeDefined();
	});

	it('returns to input phase when back button is clicked', async () => {
		await renderWithPreview();
		await fireEvent.click(screen.getByRole('button', { name: /back/i }));
		expect(screen.getByPlaceholderText(/https:\/\//)).toBeDefined();
	});
});

describe('ImportForm — lead source in preview form', () => {
	it('shows a lead source select in the preview form', async () => {
		await renderWithPreview();
		expect(screen.getByText('Lead Source')).toBeDefined();
	});

	it('lead source select defaults to cold_apply', async () => {
		await renderWithPreview();
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
		const helpBtn = screen.getByRole('button', { name: /lead source help/i });
		expect(helpBtn).toBeDefined();
	});
});

describe('ImportForm — save phase', () => {
	it('calls importConfirm with lead_source defaulting to cold_apply', async () => {
		await renderWithPreview();
		await fireEvent.click(screen.getByRole('button', { name: /save posting/i }));
		expect(postings.importConfirm).toHaveBeenCalledOnce();
		const payload = vi.mocked(postings.importConfirm).mock.calls[0][0] as unknown as Record<string, unknown>;
		expect(payload.lead_source).toBe('cold_apply');
	});

	it('calls importConfirm with the selected lead_source when changed', async () => {
		await renderWithPreview();
		const selects = screen.getAllByRole('combobox') as HTMLSelectElement[];
		const leadSourceSelect = selects.find((s) =>
			Array.from(s.options).some((o) => o.value === 'cold_apply')
		)!;
		await fireEvent.change(leadSourceSelect, { target: { value: 'referral' } });

		await fireEvent.click(screen.getByRole('button', { name: /save posting/i }));
		const payload = vi.mocked(postings.importConfirm).mock.calls[0][0] as unknown as Record<string, unknown>;
		expect(payload.lead_source).toBe('referral');
	});

	it('shows an error message when save fails', async () => {
		await renderWithPreview();
		vi.mocked(postings.importConfirm).mockRejectedValue(new Error('Save failed'));
		await fireEvent.click(screen.getByRole('button', { name: /save posting/i }));
		expect(await screen.findByText(/save failed/i)).toBeDefined();
	});
});

describe('ImportForm — success state', () => {
	it('shows a View in Postings link after successful save', async () => {
		await renderWithPreview();
		await fireEvent.click(screen.getByRole('button', { name: /save posting/i }));
		const link = await screen.findByRole('link', { name: /view in postings/i });
		expect(link).toBeDefined();
	});

	it('View in Postings link points to the postings page for the saved id', async () => {
		await renderWithPreview();
		await fireEvent.click(screen.getByRole('button', { name: /save posting/i }));
		const link = await screen.findByRole('link', { name: /view in postings/i }) as HTMLAnchorElement;
		expect(link.href).toContain('/postings');
		expect(link.href).toContain('42');
	});

	it('does not show the save button after successful save', async () => {
		await renderWithPreview();
		await fireEvent.click(screen.getByRole('button', { name: /save posting/i }));
		await screen.findByRole('link', { name: /view in postings/i });
		expect(screen.queryByRole('button', { name: /save posting/i })).toBeNull();
	});

	it('shows duplicate error with link to existing posting on 409', async () => {
		const { ApiError } = await import('$lib/api');
		await renderWithPreview();
		vi.mocked(postings.importConfirm).mockRejectedValue(
			new ApiError('Already imported', 409, { message: 'Already imported', existing_id: 7 })
		);
		await fireEvent.click(screen.getByRole('button', { name: /save posting/i }));
		const viewLink = await screen.findByRole('link', { name: /view posting/i });
		expect(viewLink).toBeDefined();
	});
});

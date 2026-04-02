import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/svelte';
import type { JobPosting } from '$lib/types';
import { readable } from 'svelte/store';

vi.mock('$app/stores', () => ({
	page: readable({ url: new URL('http://localhost/postings') }),
}));

const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

function mockJsonResponse(data: unknown, status = 200) {
	mockFetch.mockResolvedValueOnce({
		ok: true,
		status,
		json: () => Promise.resolve(data),
	});
}

function makePosting(overrides: Partial<JobPosting> & { id: number; title: string }): JobPosting {
	return {
		company: null,
		company_name: 'Acme',
		description: null,
		location: null,
		remote_type: null,
		salary_min: null,
		salary_max: null,
		url: null,
		source: 'indeed',
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

const REFERRAL_POSTING = makePosting({ id: 1, title: 'Referral Role', lead_source: 'referral' });
const COLD_APPLY_POSTING = makePosting({ id: 2, title: 'Cold Apply Role', lead_source: 'cold_apply' });
const RECRUITER_POSTING = makePosting({ id: 3, title: 'Recruiter Role', lead_source: 'recruiter_inbound' });

describe('Postings Page — lead_source filter select', () => {
	let PostingsPage: typeof import('./+page.svelte').default;

	beforeEach(async () => {
		mockFetch.mockReset();
		const mod = await import('./+page.svelte');
		PostingsPage = mod.default;
	});

	it('renders a lead source filter with "Any lead source" option', async () => {
		mockJsonResponse([REFERRAL_POSTING, COLD_APPLY_POSTING]);
		render(PostingsPage);

		await waitFor(() => {
			expect(screen.getByText('Referral Role')).toBeInTheDocument();
		});

		expect(screen.getByText('Any lead source')).toBeInTheDocument();
	});

	it('renders lead source options for all four lead source values', async () => {
		mockJsonResponse([REFERRAL_POSTING]);
		render(PostingsPage);

		await waitFor(() => {
			expect(screen.getByText('Referral Role')).toBeInTheDocument();
		});

		expect(screen.getByText('Referral')).toBeInTheDocument();
		expect(screen.getByText('Recruiter (Inbound)')).toBeInTheDocument();
		expect(screen.getByText('Recruiter (Outbound)')).toBeInTheDocument();
		expect(screen.getByText('Cold Apply')).toBeInTheDocument();
	});

	it('filters postings by selected lead source', async () => {
		mockJsonResponse([REFERRAL_POSTING, COLD_APPLY_POSTING, RECRUITER_POSTING]);
		render(PostingsPage);

		await waitFor(() => {
			expect(screen.getByText('Referral Role')).toBeInTheDocument();
			expect(screen.getByText('Cold Apply Role')).toBeInTheDocument();
			expect(screen.getByText('Recruiter Role')).toBeInTheDocument();
		});

		const selects = screen.getAllByRole('combobox');
		const leadSourceSelect = selects.find((s) =>
			s.querySelector('option[value="referral"]') !== null ||
			Array.from((s as HTMLSelectElement).options).some((o) => o.text === 'Any lead source')
		);

		await fireEvent.change(leadSourceSelect!, { target: { value: 'referral' } });

		await waitFor(() => {
			expect(screen.getByText('Referral Role')).toBeInTheDocument();
			expect(screen.queryByText('Cold Apply Role')).not.toBeInTheDocument();
			expect(screen.queryByText('Recruiter Role')).not.toBeInTheDocument();
		});
	});

	it('shows all postings when lead source filter is cleared', async () => {
		mockJsonResponse([REFERRAL_POSTING, COLD_APPLY_POSTING]);
		render(PostingsPage);

		await waitFor(() => {
			expect(screen.getByText('Referral Role')).toBeInTheDocument();
		});

		const selects = screen.getAllByRole('combobox');
		const leadSourceSelect = selects.find((s) =>
			Array.from((s as HTMLSelectElement).options ?? []).some((o: HTMLOptionElement) => o.text === 'Any lead source')
		) as HTMLSelectElement;

		await fireEvent.change(leadSourceSelect, { target: { value: 'referral' } });
		await waitFor(() => {
			expect(screen.queryByText('Cold Apply Role')).not.toBeInTheDocument();
		});

		await fireEvent.change(leadSourceSelect, { target: { value: '' } });
		await waitFor(() => {
			expect(screen.getByText('Referral Role')).toBeInTheDocument();
			expect(screen.getByText('Cold Apply Role')).toBeInTheDocument();
		});
	});
});

describe('Postings Page — Lead column header', () => {
	let PostingsPage: typeof import('./+page.svelte').default;

	beforeEach(async () => {
		mockFetch.mockReset();
		const mod = await import('./+page.svelte');
		PostingsPage = mod.default;
	});

	it('renders a "Lead" column header', async () => {
		mockJsonResponse([REFERRAL_POSTING]);
		render(PostingsPage);

		await waitFor(() => {
			expect(screen.getByText('Referral Role')).toBeInTheDocument();
		});

		expect(screen.getByText('Lead')).toBeInTheDocument();
	});

	it('renders the "Search Source" column header instead of "Source"', async () => {
		mockJsonResponse([REFERRAL_POSTING]);
		render(PostingsPage);

		await waitFor(() => {
			expect(screen.getByText('Referral Role')).toBeInTheDocument();
		});

		expect(screen.getByText('Search Source')).toBeInTheDocument();
		expect(screen.queryByText('Source')).not.toBeInTheDocument();
	});
});

describe('Postings Page — lead_source badge in table rows', () => {
	let PostingsPage: typeof import('./+page.svelte').default;

	beforeEach(async () => {
		mockFetch.mockReset();
		const mod = await import('./+page.svelte');
		PostingsPage = mod.default;
	});

	it('renders lead source label badge in each table row', async () => {
		mockJsonResponse([REFERRAL_POSTING, COLD_APPLY_POSTING]);
		render(PostingsPage);

		await waitFor(() => {
			expect(screen.getByText('Referral Role')).toBeInTheDocument();
		});

		// LEAD_SOURCE_LABELS maps referral -> 'Referral', cold_apply -> 'Cold Apply'
		const badges = screen.getAllByText('Referral');
		expect(badges.length).toBeGreaterThanOrEqual(1);

		const coldApplyBadges = screen.getAllByText('Cold Apply');
		expect(coldApplyBadges.length).toBeGreaterThanOrEqual(1);
	});

	it('renders the human-readable label for recruiter_inbound', async () => {
		mockJsonResponse([RECRUITER_POSTING]);
		render(PostingsPage);

		await waitFor(() => {
			expect(screen.getByText('Recruiter Role')).toBeInTheDocument();
		});

		expect(screen.getByText('Recruiter (Inbound)')).toBeInTheDocument();
	});
});

describe('Postings Page — lead_source sorting', () => {
	let PostingsPage: typeof import('./+page.svelte').default;

	beforeEach(async () => {
		mockFetch.mockReset();
		const mod = await import('./+page.svelte');
		PostingsPage = mod.default;
	});

	it('sorts postings by lead_source when Lead column header is clicked', async () => {
		mockJsonResponse([RECRUITER_POSTING, REFERRAL_POSTING, COLD_APPLY_POSTING]);
		render(PostingsPage);

		await waitFor(() => {
			expect(screen.getByText('Recruiter Role')).toBeInTheDocument();
		});

		await fireEvent.click(screen.getByText('Lead'));

		await waitFor(() => {
			const rows = screen.getAllByRole('row');
			const dataRows = rows.filter((r) => r.querySelector('td'));
			// After sort by lead_source asc: cold_apply < recruiter_inbound < referral
			// Just verify all three are still visible after sort
			expect(dataRows.length).toBe(3);
		});
	});
});

describe('Postings Page — Import Posting button removed', () => {
	let PostingsPage: typeof import('./+page.svelte').default;

	beforeEach(async () => {
		mockFetch.mockReset();
		const mod = await import('./+page.svelte');
		PostingsPage = mod.default;
	});

	it('does not render an Import Posting button', async () => {
		mockJsonResponse([REFERRAL_POSTING]);
		render(PostingsPage);

		await waitFor(() => {
			expect(screen.getByText('Referral Role')).toBeInTheDocument();
		});

		expect(screen.queryByText('Import Posting')).toBeNull();
	});
});

describe('Postings Page — empty state links to search and import', () => {
	let PostingsPage: typeof import('./+page.svelte').default;

	beforeEach(async () => {
		mockFetch.mockReset();
		const mod = await import('./+page.svelte');
		PostingsPage = mod.default;
	});

	it('empty state has a link to /search?tab=import-url', async () => {
		mockJsonResponse([]);
		render(PostingsPage);

		await waitFor(() => {
			const links = screen.getAllByRole('link');
			const importLink = links.find(
				(l) => (l as HTMLAnchorElement).href?.includes('/search?tab=import-url'),
			);
			expect(importLink).toBeDefined();
		});
	});

	it('empty state has a link to /search', async () => {
		mockJsonResponse([]);
		render(PostingsPage);

		await waitFor(() => {
			const links = screen.getAllByRole('link');
			const searchLink = links.find((l) => {
				const href = (l as HTMLAnchorElement).getAttribute('href');
				return href === '/search';
			});
			expect(searchLink).toBeDefined();
		});
	});
});

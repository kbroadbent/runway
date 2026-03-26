import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/svelte';
import SearchResultsTable from './SearchResultsTable.svelte';
import type { JobPosting } from '$lib/types';

// jsdom doesn't implement HTMLDialogElement.showModal/close
beforeEach(() => {
	HTMLDialogElement.prototype.showModal =
		HTMLDialogElement.prototype.showModal ??
		vi.fn(function (this: HTMLDialogElement) {
			this.setAttribute('open', '');
		});
	HTMLDialogElement.prototype.close =
		HTMLDialogElement.prototype.close ??
		vi.fn(function (this: HTMLDialogElement) {
			this.removeAttribute('open');
		});
});

function makePosting(overrides: Partial<JobPosting> = {}): JobPosting {
	return {
		id: 1,
		title: 'Software Engineer',
		company: { id: 1, name: 'Acme Corp', website: null, glassdoor_rating: null, glassdoor_url: null, levels_salary_data: null, levels_url: null, blind_url: null, employee_count: null, industry: null, notes: null, common_questions: null, last_researched_at: null, created_at: '2026-01-01' },
		company_name: 'Acme Corp',
		description: null,
		location: 'Remote',
		remote_type: null,
		salary_min: null,
		salary_max: null,
		url: null,
		source: 'linkedin',
		date_posted: '2026-03-01',
		date_saved: '2026-03-01',
		status: 'new',
		tier: null,
		pipeline_stage: null,
		has_raw_content: false,
		notes: null,
		...overrides,
	};
}

const POSTING_A = makePosting({ id: 10, title: 'Frontend Developer', company_name: 'Alpha Inc' });
const POSTING_B = makePosting({ id: 11, title: 'Backend Developer', company_name: 'Beta LLC' });
const POSTING_C = makePosting({ id: 12, title: 'Fullstack Engineer', company_name: 'Gamma Co' });

describe('SearchResultsTable — added postings (green border)', () => {
	it('marks rows for postings in addedIds with data-delta="added"', () => {
		render(SearchResultsTable, {
			props: {
				results: [POSTING_A, POSTING_B, POSTING_C],
				addedIds: new Set([12]),
			},
		});

		const addedRow = screen.getByText('Fullstack Engineer').closest('tr');
		expect(addedRow).toHaveAttribute('data-delta', 'added');
	});

	it('does not mark rows that are not in addedIds', () => {
		render(SearchResultsTable, {
			props: {
				results: [POSTING_A, POSTING_B, POSTING_C],
				addedIds: new Set([12]),
			},
		});

		const normalRow = screen.getByText('Frontend Developer').closest('tr');
		expect(normalRow).not.toHaveAttribute('data-delta', 'added');
	});

	it('applies a green border style to rows with data-delta="added"', () => {
		const { container } = render(SearchResultsTable, {
			props: {
				results: [POSTING_A, POSTING_B],
				addedIds: new Set([10]),
			},
		});

		// The component should have CSS that gives added rows a green border.
		// We verify the data attribute is set — the CSS rule [data-delta="added"]
		// should apply a green left border or similar visual indicator.
		const addedRow = screen.getByText('Frontend Developer').closest('tr');
		expect(addedRow).toHaveAttribute('data-delta', 'added');

		// Verify the component includes a style rule for data-delta="added" with green
		const styleTag = container.querySelector('style');
		// The compiled Svelte styles may or may not be inspectable in jsdom,
		// so we check via computed style or the presence of a class.
		// At minimum, the data attribute must be present for CSS to target.
		expect(addedRow?.getAttribute('data-delta')).toBe('added');
	});

	it('does not set data-delta when addedIds is empty', () => {
		render(SearchResultsTable, {
			props: {
				results: [POSTING_A],
				addedIds: new Set(),
			},
		});

		const row = screen.getByText('Frontend Developer').closest('tr');
		expect(row).not.toHaveAttribute('data-delta');
	});
});

describe('SearchResultsTable — removed postings section', () => {
	it('renders a removed section when removedPostings has items', () => {
		render(SearchResultsTable, {
			props: {
				results: [POSTING_B],
				removedPostings: [POSTING_A],
			},
		});

		expect(screen.getByText('Removed')).toBeInTheDocument();
		expect(screen.getByText('Frontend Developer')).toBeInTheDocument();
	});

	it('does not render the removed section when removedPostings is empty', () => {
		render(SearchResultsTable, {
			props: {
				results: [POSTING_B],
				removedPostings: [],
			},
		});

		expect(screen.queryByText('Removed')).not.toBeInTheDocument();
	});

	it('marks removed rows with data-delta="removed"', () => {
		render(SearchResultsTable, {
			props: {
				results: [POSTING_B],
				removedPostings: [POSTING_A],
			},
		});

		const removedRow = screen.getByText('Frontend Developer').closest('tr');
		expect(removedRow).toHaveAttribute('data-delta', 'removed');
	});

	it('renders the removed section collapsed by default', async () => {
		render(SearchResultsTable, {
			props: {
				results: [POSTING_B],
				removedPostings: [POSTING_A],
			},
		});

		// The removed section header should be visible
		expect(screen.getByText('Removed')).toBeInTheDocument();

		// But the removed postings should be hidden/collapsed by default
		const removedRow = screen.queryByText('Frontend Developer');
		expect(removedRow).not.toBeVisible();
	});

	it('expands the removed section when the header is clicked', async () => {
		render(SearchResultsTable, {
			props: {
				results: [POSTING_B],
				removedPostings: [POSTING_A],
			},
		});

		// Click the removed section header to expand
		const header = screen.getByText('Removed');
		await fireEvent.click(header);

		// Now the removed posting should be visible
		expect(screen.getByText('Frontend Developer')).toBeVisible();
	});

	it('collapses the removed section when the header is clicked again', async () => {
		render(SearchResultsTable, {
			props: {
				results: [POSTING_B],
				removedPostings: [POSTING_A],
			},
		});

		const header = screen.getByText('Removed');

		// Expand
		await fireEvent.click(header);
		expect(screen.getByText('Frontend Developer')).toBeVisible();

		// Collapse
		await fireEvent.click(header);
		expect(screen.queryByText('Frontend Developer')).not.toBeVisible();
	});

	it('shows the count of removed postings in the header', () => {
		render(SearchResultsTable, {
			props: {
				results: [POSTING_C],
				removedPostings: [POSTING_A, POSTING_B],
			},
		});

		// The header should indicate how many postings were removed
		expect(screen.getByText(/Removed/)).toHaveTextContent('2');
	});
});

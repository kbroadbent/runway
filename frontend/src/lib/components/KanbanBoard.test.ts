import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/svelte';
import KanbanBoard from './KanbanBoard.svelte';
import type { PipelineEntry } from '$lib/types';

// Mock the pipeline API
vi.mock('$lib/api', () => ({
	pipeline: {
		move: vi.fn(() => Promise.resolve({})),
	},
}));

import { pipeline } from '$lib/api';

// jsdom doesn't implement DataTransfer, HTMLDialogElement.showModal/close
class MockDataTransfer {
	private data: Record<string, string> = {};
	setData(format: string, value: string) {
		this.data[format] = value;
	}
	getData(format: string) {
		return this.data[format] ?? '';
	}
}

beforeEach(() => {
	vi.clearAllMocks();
	// @ts-ignore
	globalThis.DataTransfer = MockDataTransfer;

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

function makePipelineEntry(overrides: Partial<PipelineEntry> = {}): PipelineEntry {
	return {
		id: 1,
		job_posting: {
			id: 10,
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
			date_saved: '2026-01-01',
			status: 'new',
			tier: null,
			pipeline_stage: 'interested',
			has_raw_content: false,
			notes: null,
			lead_source: 'cold_apply',
		},
		stage: 'interested',
		position: 0,
		next_action: null,
		next_action_date: null,
		applied_date: null,
		recruiter_screen_date: null,
		tech_screen_date: null,
		onsite_date: null,
		offer_date: null,
		offer_expiration_date: null,
		custom_dates: [],
		created_at: '2026-01-01T00:00:00',
		updated_at: '2026-01-01T00:00:00',
		...overrides,
	};
}

function renderBoard(
	boardData?: Record<string, PipelineEntry[]>,
	overrides: Record<string, unknown> = {}
) {
	const defaultBoard: Record<string, PipelineEntry[]> = {
		interested: [makePipelineEntry()],
		applying: [],
		applied: [],
		recruiter_screen_scheduled: [],
		recruiter_screen_completed: [],
		tech_screen_scheduled: [],
		tech_screen_completed: [],
		onsite_scheduled: [],
		onsite_completed: [],
		offer: [],
		rejected: [],
		archived: [],
	};

	return render(KanbanBoard, {
		props: {
			board: boardData ?? defaultBoard,
			onCardClick: vi.fn(),
			onMoved: vi.fn(),
			...overrides,
		},
	});
}

/**
 * Simulate dragging a card and dropping it on a target column.
 * Stages without sub-lanes get a .column-cards drop zone.
 * The STAGES order is: interested, applying, applied, recruiter_screen (sub-lanes),
 * tech_screen (sub-lanes), onsite (sub-lanes), offer, rejected, archived.
 * Non-sub-lane columns with .column-cards: interested(0), applying(1), applied(2), offer(3), rejected(4), archived(5)
 */
async function dragAndDrop(dropZoneIndex: number) {
	const card = document.querySelector('[draggable="true"]');
	expect(card).toBeTruthy();

	const dataTransfer = new DataTransfer();
	dataTransfer.setData('text/plain', '1');
	await fireEvent.dragStart(card!, { dataTransfer });

	const dropZones = document.querySelectorAll('.column-cards');
	expect(dropZones.length).toBeGreaterThan(dropZoneIndex);
	await fireEvent.drop(dropZones[dropZoneIndex], { dataTransfer });
}

describe('KanbanBoard two-phase drop handler', () => {
	describe('pending move state', () => {
		it('does not call pipeline.move immediately on drop', async () => {
			renderBoard();
			// Drop on "applied" column (index 2: interested=0, applying=1, applied=2)
			await dragAndDrop(2);

			// pipeline.move should NOT be called yet — modal should show first
			expect(pipeline.move).not.toHaveBeenCalled();
		});

		it('shows StageDateModal after dropping a card onto a new stage', async () => {
			renderBoard();
			await dragAndDrop(2);

			const dialog = document.querySelector('dialog');
			expect(dialog).toBeInTheDocument();
		});

		it('passes the target stage to StageDateModal', async () => {
			renderBoard();
			await dragAndDrop(2); // drop on "applied"

			// Modal dialog should contain the stage name in its heading
			const dialog = document.querySelector('dialog');
			expect(dialog).toBeInTheDocument();
			expect(dialog!.textContent).toContain('applied');
		});

		it('passes the entry title to StageDateModal', async () => {
			renderBoard();
			await dragAndDrop(2);

			// Modal dialog should contain the entry title
			const dialog = document.querySelector('dialog');
			expect(dialog).toBeInTheDocument();
			expect(dialog!.textContent).toContain('Software Engineer');
		});
	});

	describe('modal confirm', () => {
		it('calls pipeline.move with stage_dates when modal is confirmed', async () => {
			renderBoard();
			await dragAndDrop(2);

			const saveButton = screen.getByRole('button', { name: /save/i });
			await fireEvent.click(saveButton);

			expect(pipeline.move).toHaveBeenCalledOnce();
			const callArgs = (pipeline.move as ReturnType<typeof vi.fn>).mock.calls[0];
			expect(callArgs[0]).toBe(1); // entry id
			expect(callArgs[1].to_stage).toBe('applied');
			expect(callArgs[1].stage_dates).toBeDefined();
		});

		it('calls onMoved after confirming the modal', async () => {
			const onMoved = vi.fn();
			renderBoard(undefined, { onMoved });
			await dragAndDrop(2);

			const saveButton = screen.getByRole('button', { name: /save/i });
			await fireEvent.click(saveButton);

			expect(onMoved).toHaveBeenCalledOnce();
		});

		it('dismisses the modal after confirm', async () => {
			renderBoard();
			await dragAndDrop(2);

			const saveButton = screen.getByRole('button', { name: /save/i });
			await fireEvent.click(saveButton);

			const dialog = document.querySelector('dialog');
			expect(dialog).not.toBeInTheDocument();
		});
	});

	describe('modal skip', () => {
		it('calls pipeline.move without stage_dates when modal is skipped', async () => {
			renderBoard();
			await dragAndDrop(2);

			const skipButton = screen.getByRole('button', { name: /skip/i });
			await fireEvent.click(skipButton);

			expect(pipeline.move).toHaveBeenCalledOnce();
			const callArgs = (pipeline.move as ReturnType<typeof vi.fn>).mock.calls[0];
			expect(callArgs[0]).toBe(1);
			expect(callArgs[1].to_stage).toBe('applied');
			expect(callArgs[1].stage_dates).toBeUndefined();
		});

		it('calls onMoved after skipping', async () => {
			const onMoved = vi.fn();
			renderBoard(undefined, { onMoved });
			await dragAndDrop(2);

			const skipButton = screen.getByRole('button', { name: /skip/i });
			await fireEvent.click(skipButton);

			expect(onMoved).toHaveBeenCalledOnce();
		});
	});

	describe('modal cancel', () => {
		it('does not call pipeline.move when modal is cancelled', async () => {
			renderBoard();
			await dragAndDrop(2);

			const cancelButton = screen.getByRole('button', { name: /cancel/i });
			await fireEvent.click(cancelButton);

			expect(pipeline.move).not.toHaveBeenCalled();
		});

		it('does not call onMoved when modal is cancelled', async () => {
			const onMoved = vi.fn();
			renderBoard(undefined, { onMoved });
			await dragAndDrop(2);

			const cancelButton = screen.getByRole('button', { name: /cancel/i });
			await fireEvent.click(cancelButton);

			expect(onMoved).not.toHaveBeenCalled();
		});

		it('dismisses the modal after cancel', async () => {
			renderBoard();
			await dragAndDrop(2);

			const cancelButton = screen.getByRole('button', { name: /cancel/i });
			await fireEvent.click(cancelButton);

			const dialog = document.querySelector('dialog');
			expect(dialog).not.toBeInTheDocument();
		});
	});

	describe('same-stage drop', () => {
		it('does not show modal when dropping onto the same stage', async () => {
			renderBoard();
			// Drop on "interested" column (index 0) — same stage as entry
			await dragAndDrop(0);

			const dialog = document.querySelector('dialog');
			expect(dialog).not.toBeInTheDocument();
			expect(pipeline.move).not.toHaveBeenCalled();
		});
	});
});

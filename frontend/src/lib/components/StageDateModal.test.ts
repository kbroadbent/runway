import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/svelte';
import StageDateModal from './StageDateModal.svelte';
import { STAGE_DATE_FIELDS } from '$lib/pipeline';

// jsdom doesn't implement HTMLDialogElement.showModal/close
beforeEach(() => {
	if (!HTMLDialogElement.prototype.showModal) {
		HTMLDialogElement.prototype.showModal = vi.fn(function (this: HTMLDialogElement) {
			this.setAttribute('open', '');
		});
	}
	if (!HTMLDialogElement.prototype.close) {
		HTMLDialogElement.prototype.close = vi.fn(function (this: HTMLDialogElement) {
			this.removeAttribute('open');
		});
	}
});

function getToday(): string {
	return new Date().toISOString().substring(0, 10);
}

describe('StageDateModal', () => {
	const defaultProps = {
		stage: 'applied',
		entryTitle: 'Software Engineer at Acme',
		onConfirm: vi.fn(),
		onSkip: vi.fn(),
		onCancel: vi.fn(),
	};

	function renderModal(overrides: Partial<typeof defaultProps> = {}) {
		return render(StageDateModal, { props: { ...defaultProps, ...overrides } });
	}

	describe('rendering', () => {
		it('renders a dialog element', () => {
			renderModal();
			const dialog = document.querySelector('dialog');
			expect(dialog).toBeInTheDocument();
		});

		it('calls showModal on mount', () => {
			renderModal();
			expect(HTMLDialogElement.prototype.showModal).toHaveBeenCalled();
		});

		it('displays the entry title in the subtitle', () => {
			renderModal({ entryTitle: 'Backend Dev at Initech' });
			expect(screen.getByText(/Backend Dev at Initech/)).toBeInTheDocument();
		});

		it('displays the stage name with underscores replaced by spaces', () => {
			renderModal({ stage: 'recruiter_screen_scheduled' });
			expect(screen.getByText(/recruiter screen scheduled/)).toBeInTheDocument();
		});

		it('renders Save, Skip, and Cancel buttons', () => {
			renderModal();
			expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument();
			expect(screen.getByRole('button', { name: /skip/i })).toBeInTheDocument();
			expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
		});
	});

	describe('date fields for single-date stages', () => {
		it('renders one date input for the applied stage', () => {
			renderModal({ stage: 'applied' });
			const inputs = screen.getAllByLabelText(/date/i);
			expect(inputs).toHaveLength(1);
		});

		it('labels the applied stage field correctly', () => {
			renderModal({ stage: 'applied' });
			expect(screen.getByLabelText('Applied Date')).toBeInTheDocument();
		});

		it('pre-fills the date input with today', () => {
			renderModal({ stage: 'applied' });
			const input = screen.getByLabelText('Applied Date') as HTMLInputElement;
			expect(input.value).toBe(getToday());
		});
	});

	describe('date fields for multi-date stages', () => {
		it('renders two date inputs for the offer stage', () => {
			renderModal({ stage: 'offer' });
			expect(screen.getByLabelText('Offer Date')).toBeInTheDocument();
			expect(screen.getByLabelText('Offer Expiration Date')).toBeInTheDocument();
		});

		it('pre-fills both offer date inputs with today', () => {
			renderModal({ stage: 'offer' });
			const offerDate = screen.getByLabelText('Offer Date') as HTMLInputElement;
			const expirationDate = screen.getByLabelText('Offer Expiration Date') as HTMLInputElement;
			expect(offerDate.value).toBe(getToday());
			expect(expirationDate.value).toBe(getToday());
		});
	});

	describe('stages without date fields', () => {
		it('renders no date inputs for the interested stage', () => {
			renderModal({ stage: 'interested' });
			const inputs = document.querySelectorAll('input[type="date"]');
			expect(inputs).toHaveLength(0);
		});

		it('still renders action buttons for stages without date fields', () => {
			renderModal({ stage: 'interested' });
			expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument();
			expect(screen.getByRole('button', { name: /skip/i })).toBeInTheDocument();
		});
	});

	describe('confirm action', () => {
		it('calls onConfirm with filled date values when Save is clicked', async () => {
			const onConfirm = vi.fn();
			renderModal({ stage: 'applied', onConfirm });

			await fireEvent.click(screen.getByRole('button', { name: /save/i }));

			expect(onConfirm).toHaveBeenCalledOnce();
			const dates = onConfirm.mock.calls[0][0];
			expect(dates).toHaveProperty('applied_date');
			expect(dates.applied_date).toBe(getToday());
		});

		it('calls onConfirm with multiple dates for offer stage', async () => {
			const onConfirm = vi.fn();
			renderModal({ stage: 'offer', onConfirm });

			await fireEvent.click(screen.getByRole('button', { name: /save/i }));

			const dates = onConfirm.mock.calls[0][0];
			expect(dates).toHaveProperty('offer_date');
			expect(dates).toHaveProperty('offer_expiration_date');
		});

		it('omits empty date values from the confirm payload', async () => {
			const onConfirm = vi.fn();
			renderModal({ stage: 'offer', onConfirm });

			// Clear the offer expiration date
			const expirationInput = screen.getByLabelText('Offer Expiration Date') as HTMLInputElement;
			await fireEvent.input(expirationInput, { target: { value: '' } });

			await fireEvent.click(screen.getByRole('button', { name: /save/i }));

			const dates = onConfirm.mock.calls[0][0];
			expect(dates).toHaveProperty('offer_date');
			expect(dates).not.toHaveProperty('offer_expiration_date');
		});
	});

	describe('skip action', () => {
		it('calls onSkip when Skip is clicked', async () => {
			const onSkip = vi.fn();
			renderModal({ onSkip });

			await fireEvent.click(screen.getByRole('button', { name: /skip/i }));

			expect(onSkip).toHaveBeenCalledOnce();
		});

		it('does not call onConfirm when Skip is clicked', async () => {
			const onConfirm = vi.fn();
			const onSkip = vi.fn();
			renderModal({ onConfirm, onSkip });

			await fireEvent.click(screen.getByRole('button', { name: /skip/i }));

			expect(onConfirm).not.toHaveBeenCalled();
		});
	});

	describe('cancel action', () => {
		it('calls onCancel when Cancel is clicked', async () => {
			const onCancel = vi.fn();
			renderModal({ onCancel });

			await fireEvent.click(screen.getByRole('button', { name: /cancel/i }));

			expect(onCancel).toHaveBeenCalledOnce();
		});

		it('does not call onConfirm or onSkip when Cancel is clicked', async () => {
			const onConfirm = vi.fn();
			const onSkip = vi.fn();
			const onCancel = vi.fn();
			renderModal({ onConfirm, onSkip, onCancel });

			await fireEvent.click(screen.getByRole('button', { name: /cancel/i }));

			expect(onConfirm).not.toHaveBeenCalled();
			expect(onSkip).not.toHaveBeenCalled();
		});
	});

	describe('keyboard interaction', () => {
		it('calls onCancel when Escape is pressed on the dialog', async () => {
			const onCancel = vi.fn();
			renderModal({ onCancel });

			const dialog = document.querySelector('dialog')!;
			await fireEvent.keyDown(dialog, { key: 'Escape' });

			expect(onCancel).toHaveBeenCalledOnce();
		});
	});
});

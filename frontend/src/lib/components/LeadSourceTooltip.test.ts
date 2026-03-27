import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/svelte';
import LeadSourceTooltip from './LeadSourceTooltip.svelte';

describe('LeadSourceTooltip', () => {
	it('renders a help button', () => {
		render(LeadSourceTooltip);
		const button = screen.getByRole('button', { name: /lead source help/i });
		expect(button).toBeDefined();
	});

	it('does not show tooltip content initially', () => {
		render(LeadSourceTooltip);
		expect(screen.queryByText('Referral')).toBeNull();
	});

	it('shows tooltip with all four lead source labels on mouse enter', async () => {
		render(LeadSourceTooltip);
		const button = screen.getByRole('button', { name: /lead source help/i });
		await fireEvent.mouseEnter(button);
		expect(screen.getByText('Referral')).toBeDefined();
		expect(screen.getByText('Recruiter (Inbound)')).toBeDefined();
		expect(screen.getByText('Recruiter (Outbound)')).toBeDefined();
		expect(screen.getByText('Cold Apply')).toBeDefined();
	});

	it('hides tooltip on mouse leave', async () => {
		render(LeadSourceTooltip);
		const button = screen.getByRole('button', { name: /lead source help/i });
		await fireEvent.mouseEnter(button);
		await fireEvent.mouseLeave(button);
		expect(screen.queryByText('Referral')).toBeNull();
	});

	it('toggles tooltip on click', async () => {
		render(LeadSourceTooltip);
		const button = screen.getByRole('button', { name: /lead source help/i });
		await fireEvent.click(button);
		expect(screen.getByText('Referral')).toBeDefined();
		await fireEvent.click(button);
		expect(screen.queryByText('Referral')).toBeNull();
	});

	it('shows descriptions for each lead source', async () => {
		render(LeadSourceTooltip);
		const button = screen.getByRole('button', { name: /lead source help/i });
		await fireEvent.mouseEnter(button);
		// Each lead source should have a description text visible
		expect(screen.getByText(/someone referred you/i)).toBeDefined();
		expect(screen.getByText(/recruiter reached out/i)).toBeDefined();
		expect(screen.getByText(/you reached out to a recruiter/i)).toBeDefined();
		expect(screen.getByText(/found and applied independently/i)).toBeDefined();
	});
});

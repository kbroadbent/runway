import { describe, it, expect, beforeEach } from 'vitest';
import { render } from '@testing-library/svelte';
import { goto } from '$app/navigation';
import RootPage from './+page.svelte';

describe('Root page redirect', () => {
	beforeEach(() => {
		(goto as ReturnType<typeof import('vitest').vi.fn>).mockReset();
	});

	it('redirects to /dashboard instead of /search', async () => {
		render(RootPage);

		// onMount fires asynchronously — wait a tick
		await new Promise((r) => setTimeout(r, 0));

		expect(goto).toHaveBeenCalledWith('/dashboard', { replaceState: true });
	});

	it('does not redirect to /search', async () => {
		render(RootPage);

		await new Promise((r) => setTimeout(r, 0));

		expect(goto).not.toHaveBeenCalledWith('/search', expect.anything());
	});
});

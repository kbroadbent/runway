import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

function mockOkResponse(data: unknown = []) {
	return mockFetch.mockResolvedValueOnce({
		ok: true,
		status: 200,
		json: () => Promise.resolve(data),
	});
}

describe('API base URL configuration', () => {
	let originalViteApiBase: string | undefined;

	beforeEach(() => {
		mockFetch.mockReset();
		vi.resetModules();
		originalViteApiBase = import.meta.env.VITE_API_BASE;
		delete import.meta.env.VITE_API_BASE;
	});

	afterEach(() => {
		if (originalViteApiBase !== undefined) {
			import.meta.env.VITE_API_BASE = originalViteApiBase;
		} else {
			delete import.meta.env.VITE_API_BASE;
		}
	});

	it('defaults to http://localhost:8000/api when VITE_API_BASE is not set', async () => {
		mockOkResponse([]);

		const { searchProfiles } = await import('./api');
		await searchProfiles.list();

		const [url] = mockFetch.mock.calls[0];
		expect(url).toBe('http://localhost:8000/api/search-profiles');
	});

	it('uses VITE_API_BASE env var when set', async () => {
		import.meta.env.VITE_API_BASE = 'https://myapp.example.com/api';
		mockOkResponse([]);

		const { searchProfiles } = await import('./api');
		await searchProfiles.list();

		const [url] = mockFetch.mock.calls[0];
		expect(url).toBe('https://myapp.example.com/api/search-profiles');
	});

	it('strips trailing slash from VITE_API_BASE to avoid double slashes', async () => {
		import.meta.env.VITE_API_BASE = 'https://myapp.example.com/api/';
		mockOkResponse({});

		const { dashboard } = await import('./api');
		await dashboard.get();

		const [url] = mockFetch.mock.calls[0];
		expect(url).toBe('https://myapp.example.com/api/dashboard');
	});

	it('works with a relative base URL like /api', async () => {
		import.meta.env.VITE_API_BASE = '/api';
		mockOkResponse([]);

		const { companies } = await import('./api');
		await companies.list();

		const [url] = mockFetch.mock.calls[0];
		expect(url).toBe('/api/companies');
	});
});

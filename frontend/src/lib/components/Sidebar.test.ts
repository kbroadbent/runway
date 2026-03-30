import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import Sidebar from './Sidebar.svelte';
import { setPathname } from '../../tests/mocks/app-state';

describe('Sidebar', () => {
	beforeEach(() => {
		setPathname('/search');
	});

	it('renders Dashboard as the first nav item', () => {
		render(Sidebar);
		const links = screen.getAllByRole('link');
		expect(links[0]).toHaveTextContent('Dashboard');
	});

	it('renders Dashboard link pointing to /dashboard', () => {
		render(Sidebar);
		const dashboardLink = screen.getByRole('link', { name: 'Dashboard' });
		expect(dashboardLink).toHaveAttribute('href', '/dashboard');
	});

	it('marks Dashboard active only on exact /dashboard path', () => {
		setPathname('/dashboard');
		render(Sidebar);
		const dashboardLink = screen.getByRole('link', { name: 'Dashboard' });
		expect(dashboardLink).toHaveClass('active');
	});

	it('does not mark Dashboard active on /dashboard/subpath', () => {
		setPathname('/dashboard/something');
		render(Sidebar);
		const dashboardLink = screen.getByRole('link', { name: 'Dashboard' });
		expect(dashboardLink).not.toHaveClass('active');
	});

	it('does not mark Dashboard active when on another page', () => {
		setPathname('/search');
		render(Sidebar);
		const dashboardLink = screen.getByRole('link', { name: 'Dashboard' });
		expect(dashboardLink).not.toHaveClass('active');
	});

	it('renders all expected nav items in order', () => {
		render(Sidebar);
		const links = screen.getAllByRole('link');
		const labels = links.map((link) => link.textContent?.trim());
		expect(labels).toEqual([
			'Dashboard',
			'Find Jobs',
			'Pipeline',
			'Saved Postings',
			'Companies',
		]);
	});

	it('renders Find Jobs nav link pointing to /search', () => {
		render(Sidebar);
		const link = screen.getByRole('link', { name: 'Find Jobs' });
		expect(link).toHaveAttribute('href', '/search');
	});

	it('does not render a nav link labeled Search', () => {
		render(Sidebar);
		expect(screen.queryByRole('link', { name: 'Search' })).toBeNull();
	});

	it('marks Find Jobs link active when on /search path', () => {
		setPathname('/search');
		render(Sidebar);
		const link = screen.getByRole('link', { name: 'Find Jobs' });
		expect(link).toHaveClass('active');
	});
});

import { describe, it, expect } from 'vitest';
import { readFileSync, existsSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const projectRoot = resolve(dirname(fileURLToPath(import.meta.url)), '../..');

describe('adapter-static configuration', () => {
	it('svelte.config.js imports adapter-static instead of adapter-auto', () => {
		const configSource = readFileSync(resolve(projectRoot, 'svelte.config.js'), 'utf-8');

		expect(configSource).toContain('adapter-static');
		expect(configSource).not.toContain('adapter-auto');
	});

	it('svelte.config.js configures SPA fallback', () => {
		const configSource = readFileSync(resolve(projectRoot, 'svelte.config.js'), 'utf-8');

		expect(configSource).toMatch(/fallback\s*:/);
	});

	it('root +layout.ts exists with prerender = true for static generation', () => {
		const layoutPath = resolve(projectRoot, 'src/routes/+layout.ts');
		expect(existsSync(layoutPath)).toBe(true);

		const layoutSource = readFileSync(layoutPath, 'utf-8');
		expect(layoutSource).toMatch(/export\s+const\s+prerender\s*=\s*true/);
	});

	it('root +layout.ts exports ssr = false for SPA mode', () => {
		const layoutPath = resolve(projectRoot, 'src/routes/+layout.ts');
		expect(existsSync(layoutPath)).toBe(true);

		const layoutSource = readFileSync(layoutPath, 'utf-8');
		expect(layoutSource).toMatch(/export\s+const\s+ssr\s*=\s*false/);
	});
});

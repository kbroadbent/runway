import { svelte } from '@sveltejs/vite-plugin-svelte';
import { defineConfig } from 'vitest/config';

export default defineConfig({
	plugins: [svelte({ hot: false })],
	test: {
		include: ['src/**/*.test.ts'],
		environment: 'jsdom',
		setupFiles: ['src/tests/setup.ts'],
		alias: {
			'$app/state': new URL('./src/tests/mocks/app-state.ts', import.meta.url).pathname,
			'$lib': new URL('./src/lib', import.meta.url).pathname,
		},
	},
	resolve: {
		conditions: ['browser'],
	},
});

import { describe, it, expect } from 'vitest';
import { get } from 'svelte/store';
import { leadSourceFilter } from './pipelineFilters';

describe('leadSourceFilter store', () => {
	it('exports leadSourceFilter as a writable store', () => {
		expect(leadSourceFilter).toBeDefined();
		expect(typeof leadSourceFilter.subscribe).toBe('function');
		expect(typeof leadSourceFilter.set).toBe('function');
	});

	it('initializes to null', () => {
		expect(get(leadSourceFilter)).toBeNull();
	});

	it('can be set to a lead source value', () => {
		leadSourceFilter.set('referral');
		expect(get(leadSourceFilter)).toBe('referral');
		leadSourceFilter.set(null);
	});

	it('can be reset to null', () => {
		leadSourceFilter.set('cold_apply');
		leadSourceFilter.set(null);
		expect(get(leadSourceFilter)).toBeNull();
	});
});

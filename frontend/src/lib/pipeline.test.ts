import { describe, it, expect } from 'vitest';
import { STAGES, ACTIVE_STAGES, TERMINAL_STAGES } from './pipeline';
import type { StageConfig } from './pipeline';

describe('STAGES', () => {
	it('exports an array of stage configs', () => {
		expect(Array.isArray(STAGES)).toBe(true);
		expect(STAGES.length).toBeGreaterThan(0);
	});

	it('contains all expected top-level stages in order', () => {
		const keys = STAGES.map((s) => s.key);
		expect(keys).toEqual([
			'interested',
			'applying',
			'applied',
			'recruiter_screen',
			'manager_screen',
			'tech_screen',
			'onsite',
			'offer',
			'rejected',
			'withdrawn',
			'ghosted',
			'archived',
		]);
	});

	it('includes ghosted stage with correct label', () => {
		const stage = STAGES.find((s) => s.key === 'ghosted');
		expect(stage).toBeDefined();
		expect(stage?.label).toBe('Ghosted');
	});

	it('has label for every stage', () => {
		for (const stage of STAGES) {
			expect(stage.label).toBeTruthy();
		}
	});

	it('includes sub-lanes for recruiter_screen', () => {
		const stage = STAGES.find((s) => s.key === 'recruiter_screen');
		expect(stage?.subLanes).toEqual([
			{ key: 'recruiter_screen_scheduled', label: 'Scheduled' },
			{ key: 'recruiter_screen_completed', label: 'Completed' },
		]);
	});

	it('includes sub-lanes for tech_screen', () => {
		const stage = STAGES.find((s) => s.key === 'tech_screen');
		expect(stage?.subLanes).toEqual([
			{ key: 'tech_screen_scheduled', label: 'Scheduled' },
			{ key: 'tech_screen_completed', label: 'Completed' },
		]);
	});

	it('includes sub-lanes for onsite', () => {
		const stage = STAGES.find((s) => s.key === 'onsite');
		expect(stage?.subLanes).toEqual([
			{ key: 'onsite_scheduled', label: 'Scheduled' },
			{ key: 'onsite_completed', label: 'Completed' },
		]);
	});

	it('does not have sub-lanes for simple stages', () => {
		const simpleKeys = [
			'interested',
			'applying',
			'applied',
			'offer',
			'rejected',
			'withdrawn',
			'ghosted',
			'archived',
		];
		for (const key of simpleKeys) {
			const stage = STAGES.find((s) => s.key === key);
			expect(stage?.subLanes).toBeUndefined();
		}
	});

	it('satisfies StageConfig type contract', () => {
		// Type-level check: assigning to typed variable compiles
		const stages: StageConfig[] = STAGES;
		expect(stages).toBe(STAGES);
	});
});

describe('ACTIVE_STAGES', () => {
	it('does not include ghosted', () => {
		const keys = ACTIVE_STAGES.map((s) => s.key);
		expect(keys).not.toContain('ghosted');
	});

	it('includes active non-terminal stages', () => {
		const keys = ACTIVE_STAGES.map((s) => s.key);
		expect(keys).toContain('interested');
		expect(keys).toContain('applying');
		expect(keys).toContain('offer');
	});

	it('does not include any terminal stages', () => {
		const keys = ACTIVE_STAGES.map((s) => s.key);
		expect(keys).not.toContain('rejected');
		expect(keys).not.toContain('withdrawn');
		expect(keys).not.toContain('ghosted');
		expect(keys).not.toContain('archived');
	});
});

describe('TERMINAL_STAGES', () => {
	it('includes ghosted', () => {
		const keys = TERMINAL_STAGES.map((s) => s.key);
		expect(keys).toContain('ghosted');
	});

	it('includes all terminal stages', () => {
		const keys = TERMINAL_STAGES.map((s) => s.key);
		expect(keys).toContain('rejected');
		expect(keys).toContain('withdrawn');
		expect(keys).toContain('ghosted');
		expect(keys).toContain('archived');
	});

	it('does not include active stages', () => {
		const keys = TERMINAL_STAGES.map((s) => s.key);
		expect(keys).not.toContain('interested');
		expect(keys).not.toContain('applying');
		expect(keys).not.toContain('offer');
	});
});

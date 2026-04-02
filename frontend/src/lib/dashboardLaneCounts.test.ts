import { describe, it, expect } from 'vitest';
import { computeLaneCounts } from './dashboardLaneCounts';
import type { LaneCountResult } from './dashboardLaneCounts';
import { STAGES } from './pipeline';
import type { PipelineEntry } from './types';

function makeEntry(stage: string, id = 1): PipelineEntry {
	return {
		id,
		job_posting: {
			id,
			title: `Job ${id}`,
			company: null,
			company_name: null,
			description: null,
			location: null,
			remote_type: null,
			salary_min: null,
			salary_max: null,
			url: null,
			source: 'test',
			date_posted: null,
			date_saved: '2026-01-01',
			status: 'saved',
			tier: null,
			pipeline_stage: stage,
			has_raw_content: false,
			notes: null,
			lead_source: 'cold_apply',
		},
		stage,
		position: 0,
		next_action: null,
		next_action_date: null,
		applied_date: null,
		recruiter_screen_date: null,
		manager_screen_date: null,
		tech_screen_date: null,
		onsite_date: null,
		offer_date: null,
		offer_expiration_date: null,
		custom_dates: [],
		created_at: '2026-01-01',
		updated_at: '2026-01-01',
	};
}

describe('computeLaneCounts', () => {
	it('returns zero counts for all stages when entries is empty', () => {
		const result = computeLaneCounts([]);
		expect(result.active.every((lane) => lane.count === 0)).toBe(true);
		expect(result.terminal.every((lane) => lane.count === 0)).toBe(true);
	});

	it('separates active stages from terminal stages', () => {
		const result = computeLaneCounts([]);
		const activeKeys = result.active.map((l) => l.key);
		const terminalKeys = result.terminal.map((l) => l.key);

		expect(activeKeys).toContain('interested');
		expect(activeKeys).toContain('applying');
		expect(activeKeys).toContain('applied');
		expect(activeKeys).toContain('offer');
		expect(activeKeys).not.toContain('rejected');
		expect(activeKeys).not.toContain('archived');

		expect(terminalKeys).toContain('rejected');
		expect(terminalKeys).toContain('archived');
		expect(terminalKeys).not.toContain('interested');
	});

	it('counts entries in a simple stage', () => {
		const entries = [makeEntry('interested', 1), makeEntry('interested', 2), makeEntry('applied', 3)];
		const result = computeLaneCounts(entries);

		const interested = result.active.find((l) => l.key === 'interested');
		const applied = result.active.find((l) => l.key === 'applied');
		expect(interested?.count).toBe(2);
		expect(applied?.count).toBe(1);
	});

	it('aggregates sub-lane entries into parent stage count', () => {
		const entries = [
			makeEntry('recruiter_screen_scheduled', 1),
			makeEntry('recruiter_screen_completed', 2),
			makeEntry('recruiter_screen_scheduled', 3),
		];
		const result = computeLaneCounts(entries);

		const recruiterScreen = result.active.find((l) => l.key === 'recruiter_screen');
		expect(recruiterScreen?.count).toBe(3);
	});

	it('counts terminal stage entries correctly', () => {
		const entries = [makeEntry('rejected', 1), makeEntry('rejected', 2), makeEntry('archived', 3)];
		const result = computeLaneCounts(entries);

		const rejected = result.terminal.find((l) => l.key === 'rejected');
		const archived = result.terminal.find((l) => l.key === 'archived');
		expect(rejected?.count).toBe(2);
		expect(archived?.count).toBe(1);
	});

	it('includes label from STAGES config for each lane', () => {
		const result = computeLaneCounts([]);

		const interested = result.active.find((l) => l.key === 'interested');
		expect(interested?.label).toBe('Interested');

		const rejected = result.terminal.find((l) => l.key === 'rejected');
		expect(rejected?.label).toBe('Rejected');
	});

	it('preserves stage order from STAGES config', () => {
		const result = computeLaneCounts([]);
		const activeKeys = result.active.map((l) => l.key);

		// Active stages should maintain STAGES order
		const stageKeys = STAGES.map((s) => s.key);
		const activeFromConfig = stageKeys.filter(
			(k) => k !== 'rejected' && k !== 'archived'
		);
		expect(activeKeys).toEqual(activeFromConfig);
	});

	it('computes total across active and terminal', () => {
		const entries = [
			makeEntry('interested', 1),
			makeEntry('applied', 2),
			makeEntry('rejected', 3),
		];
		const result = computeLaneCounts(entries);

		expect(result.activeTotal).toBe(2);
		expect(result.terminalTotal).toBe(1);
	});
});

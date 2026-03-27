import { describe, it, expect } from 'vitest';

// These imports will fail until types.ts exports them
import { LEAD_SOURCE_LABELS, LEAD_SOURCE_DESCRIPTIONS } from './types';
import type { LeadSource, JobPosting, ImportPreview, PostingsFilter } from './types';

describe('LeadSource constants', () => {
	it('LEAD_SOURCE_LABELS has all four values', () => {
		expect(Object.keys(LEAD_SOURCE_LABELS)).toEqual(
			expect.arrayContaining(['referral', 'recruiter_inbound', 'recruiter_outbound', 'cold_apply'])
		);
		expect(Object.keys(LEAD_SOURCE_LABELS)).toHaveLength(4);
	});

	it('LEAD_SOURCE_LABELS has human-readable strings', () => {
		expect(LEAD_SOURCE_LABELS['referral']).toBe('Referral');
		expect(LEAD_SOURCE_LABELS['recruiter_inbound']).toBe('Recruiter (Inbound)');
		expect(LEAD_SOURCE_LABELS['recruiter_outbound']).toBe('Recruiter (Outbound)');
		expect(LEAD_SOURCE_LABELS['cold_apply']).toBe('Cold Apply');
	});

	it('LEAD_SOURCE_DESCRIPTIONS has all four values', () => {
		expect(Object.keys(LEAD_SOURCE_DESCRIPTIONS)).toHaveLength(4);
	});

	it('LEAD_SOURCE_DESCRIPTIONS contains non-empty strings', () => {
		const keys: LeadSource[] = ['referral', 'recruiter_inbound', 'recruiter_outbound', 'cold_apply'];
		for (const key of keys) {
			expect(typeof LEAD_SOURCE_DESCRIPTIONS[key]).toBe('string');
			expect(LEAD_SOURCE_DESCRIPTIONS[key].length).toBeGreaterThan(0);
		}
	});
});

describe('JobPosting interface includes lead_source', () => {
	it('accepts lead_source field with a valid LeadSource value', () => {
		const posting: JobPosting = {
			id: 1,
			title: 'Engineer',
			company: null,
			company_name: 'Acme',
			description: null,
			location: null,
			remote_type: null,
			salary_min: null,
			salary_max: null,
			url: null,
			source: 'manual',
			date_posted: null,
			date_saved: '2026-03-26T00:00:00',
			status: 'saved',
			tier: null,
			pipeline_stage: null,
			has_raw_content: false,
			notes: null,
			lead_source: 'cold_apply',
		};
		expect(posting.lead_source).toBe('cold_apply');
	});

	it('accepts all valid LeadSource values on JobPosting', () => {
		const values: LeadSource[] = ['referral', 'recruiter_inbound', 'recruiter_outbound', 'cold_apply'];
		for (const val of values) {
			const posting: JobPosting = {
				id: 1,
				title: 'Test',
				company: null,
				company_name: null,
				description: null,
				location: null,
				remote_type: null,
				salary_min: null,
				salary_max: null,
				url: null,
				source: 'manual',
				date_posted: null,
				date_saved: '2026-03-26T00:00:00',
				status: 'saved',
				tier: null,
				pipeline_stage: null,
				has_raw_content: false,
				notes: null,
				lead_source: val,
			};
			expect(posting.lead_source).toBe(val);
		}
	});
});

describe('ImportPreview interface includes lead_source', () => {
	it('accepts optional lead_source on ImportPreview', () => {
		const preview: ImportPreview = {
			title: 'Role',
			company_name: 'Co',
			location: null,
			remote_type: null,
			salary_min: null,
			salary_max: null,
			description: null,
			url: null,
			raw_content: null,
			lead_source: 'referral',
		};
		expect(preview.lead_source).toBe('referral');
	});

	it('allows ImportPreview without lead_source (optional field)', () => {
		const preview: ImportPreview = {
			title: 'Role',
			company_name: 'Co',
			location: null,
			remote_type: null,
			salary_min: null,
			salary_max: null,
			description: null,
			url: null,
			raw_content: null,
		};
		expect(preview.lead_source).toBeUndefined();
	});
});

describe('PostingsFilter interface includes lead_source', () => {
	it('accepts optional lead_source on PostingsFilter', () => {
		const filter: PostingsFilter = {
			lead_source: 'recruiter_outbound',
		};
		expect(filter.lead_source).toBe('recruiter_outbound');
	});

	it('allows PostingsFilter without lead_source (optional field)', () => {
		const filter: PostingsFilter = {};
		expect(filter.lead_source).toBeUndefined();
	});
});

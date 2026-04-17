import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import type { DashboardResponse, DashboardActionItem } from './types';

// Mock fetch globally before importing api module
const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

describe('DashboardActionItem type', () => {
  it('accepts a valid action item with all fields', () => {
    const item: DashboardActionItem = {
      pipeline_entry_id: 1,
      job_title: 'Frontend Dev',
      company_name: 'Acme Corp',
      type: 'action',
      description: 'Submit application',
      date: '2026-03-25T00:00:00',
      is_overdue: false,
    };
    expect(item.pipeline_entry_id).toBe(1);
    expect(item.type).toBe('action');
    expect(item.is_overdue).toBe(false);
  });

  it('accepts interview type', () => {
    const item: DashboardActionItem = {
      pipeline_entry_id: 2,
      job_title: 'Backend Dev',
      company_name: null,
      type: 'interview',
      description: 'Technical round',
      date: null,
      is_overdue: true,
    };
    expect(item.type).toBe('interview');
    expect(item.company_name).toBeNull();
    expect(item.date).toBeNull();
  });
});

describe('DashboardResponse type', () => {
  it('accepts a valid dashboard response', () => {
    const response: DashboardResponse = {
      lane_counts: {
        Interested: 2,
        Applying: 1,
        Applied: 0,
        'Recruiter Screen': 0,
        'Tech Screen': 0,
        Onsite: 0,
        Offer: 0,
        Rejected: 1,
        Archived: 0,
      },
      upcoming_events: [],
      action_items: [
        {
          pipeline_entry_id: 1,
          job_title: 'Frontend Dev',
          company_name: 'Acme Corp',
          type: 'action',
          description: 'Submit application',
          date: '2026-03-25T00:00:00',
          is_overdue: false,
        },
      ],
      stale_entries: [],
      closed_postings: [],
      completed_interviews: [],
    };
    expect(response.lane_counts['Interested']).toBe(2);
    expect(response.action_items).toHaveLength(1);
  });

  it('accepts empty action_items array', () => {
    const response: DashboardResponse = {
      lane_counts: {},
      upcoming_events: [],
      action_items: [],
      stale_entries: [],
      closed_postings: [],
      completed_interviews: [],
    };
    expect(response.action_items).toHaveLength(0);
  });
});

describe('dashboard.get()', () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it('calls GET /api/dashboard and returns typed response', async () => {
    const mockResponse: DashboardResponse = {
      lane_counts: { Interested: 3, Applying: 1 },
      upcoming_events: [],
      action_items: [
        {
          pipeline_entry_id: 5,
          job_title: 'SRE',
          company_name: 'BigCo',
          type: 'action',
          description: 'Prep for screen',
          date: '2026-03-20T00:00:00',
          is_overdue: true,
        },
      ],
      stale_entries: [],
      closed_postings: [],
      completed_interviews: [],
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve(mockResponse),
    });

    // Dynamic import so the mock is in place before the module loads
    const { dashboard } = await import('./api');
    const result = await dashboard.get();

    expect(mockFetch).toHaveBeenCalledOnce();
    const [url, options] = mockFetch.mock.calls[0];
    expect(url).toBe('http://localhost:8000/api/dashboard');
    // GET request — no method override needed (defaults to GET)
    expect(options?.method).toBeUndefined();

    expect(result.lane_counts['Interested']).toBe(3);
    expect(result.action_items).toHaveLength(1);
    expect(result.action_items[0].is_overdue).toBe(true);
  });

  it('throws ApiError on non-ok response', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      json: () => Promise.resolve({ detail: 'something broke' }),
    });

    const { dashboard, ApiError } = await import('./api');

    await expect(dashboard.get()).rejects.toThrow(ApiError);
  });
});

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import type { DashboardActionItem } from '../types';

// Helper to create action items with sensible defaults
function makeItem(overrides: Partial<DashboardActionItem> = {}): DashboardActionItem {
  return {
    pipeline_entry_id: 1,
    job_title: 'Software Engineer',
    company_name: 'Acme Corp',
    type: 'action',
    description: 'Submit application',
    date: '2026-03-25T00:00:00',
    is_overdue: false,
    ...overrides,
  };
}

describe('DashboardActionItems helpers', () => {
  // We import dynamically so the module can be created by the implementer
  let helpers: typeof import('./dashboardActionItems');

  beforeEach(async () => {
    helpers = await import('./dashboardActionItems');
  });

  describe('getTypeBadge', () => {
    it('returns a label for action type', () => {
      const badge = helpers.getTypeBadge('action');
      expect(badge).toBeTruthy();
      expect(typeof badge).toBe('string');
    });

    it('returns a label for interview type', () => {
      const badge = helpers.getTypeBadge('interview');
      expect(badge).toBeTruthy();
      expect(typeof badge).toBe('string');
    });

    it('returns different labels for different types', () => {
      const actionBadge = helpers.getTypeBadge('action');
      const interviewBadge = helpers.getTypeBadge('interview');
      expect(actionBadge).not.toBe(interviewBadge);
    });

    it('returns a fallback label for unknown types', () => {
      const badge = helpers.getTypeBadge('unknown_type');
      expect(badge).toBeTruthy();
      expect(typeof badge).toBe('string');
    });
  });

  describe('getTypeBadgeClass', () => {
    it('returns a CSS class string for action type', () => {
      const cls = helpers.getTypeBadgeClass('action');
      expect(typeof cls).toBe('string');
      expect(cls.length).toBeGreaterThan(0);
    });

    it('returns a CSS class string for interview type', () => {
      const cls = helpers.getTypeBadgeClass('interview');
      expect(typeof cls).toBe('string');
      expect(cls.length).toBeGreaterThan(0);
    });

    it('returns different classes for different types', () => {
      expect(helpers.getTypeBadgeClass('action')).not.toBe(helpers.getTypeBadgeClass('interview'));
    });
  });

  describe('isOverdue', () => {
    it('returns true when is_overdue flag is true', () => {
      const item = makeItem({ is_overdue: true });
      expect(helpers.isOverdue(item)).toBe(true);
    });

    it('returns false when is_overdue flag is false', () => {
      const item = makeItem({ is_overdue: false });
      expect(helpers.isOverdue(item)).toBe(false);
    });

    it('returns true for overdue item with a past date', () => {
      const item = makeItem({ is_overdue: true, date: '2026-03-01T00:00:00' });
      expect(helpers.isOverdue(item)).toBe(true);
    });
  });

  describe('sliceItems (show-more logic)', () => {
    const items = Array.from({ length: 10 }, (_, i) =>
      makeItem({ pipeline_entry_id: i + 1, job_title: `Job ${i + 1}` }),
    );

    it('returns all items when count is less than or equal to default limit', () => {
      const threeItems = items.slice(0, 3);
      const result = helpers.sliceItems(threeItems, false);
      expect(result).toHaveLength(3);
    });

    it('returns limited items when not expanded and count exceeds default limit', () => {
      const result = helpers.sliceItems(items, false);
      expect(result.length).toBeLessThan(items.length);
    });

    it('returns all items when expanded', () => {
      const result = helpers.sliceItems(items, true);
      expect(result).toHaveLength(items.length);
    });

    it('returns empty array for empty input', () => {
      const result = helpers.sliceItems([], false);
      expect(result).toHaveLength(0);
    });
  });

  describe('DEFAULT_VISIBLE_COUNT', () => {
    it('is exported as a positive number', () => {
      expect(helpers.DEFAULT_VISIBLE_COUNT).toBeGreaterThan(0);
    });

    it('is a reasonable default (between 3 and 10)', () => {
      expect(helpers.DEFAULT_VISIBLE_COUNT).toBeGreaterThanOrEqual(3);
      expect(helpers.DEFAULT_VISIBLE_COUNT).toBeLessThanOrEqual(10);
    });
  });

  describe('sortActionItems', () => {
    it('sorts overdue items before non-overdue items', () => {
      const items = [
        makeItem({ pipeline_entry_id: 1, is_overdue: false }),
        makeItem({ pipeline_entry_id: 2, is_overdue: true }),
        makeItem({ pipeline_entry_id: 3, is_overdue: false }),
      ];
      const sorted = helpers.sortActionItems(items);
      expect(sorted[0].pipeline_entry_id).toBe(2);
    });

    it('preserves order among items with same overdue status', () => {
      const items = [
        makeItem({ pipeline_entry_id: 1, is_overdue: true, date: '2026-03-01T00:00:00' }),
        makeItem({ pipeline_entry_id: 2, is_overdue: true, date: '2026-03-02T00:00:00' }),
      ];
      const sorted = helpers.sortActionItems(items);
      // Earlier date should come first among overdue items
      expect(sorted[0].pipeline_entry_id).toBe(1);
      expect(sorted[1].pipeline_entry_id).toBe(2);
    });

    it('returns empty array for empty input', () => {
      expect(helpers.sortActionItems([])).toHaveLength(0);
    });

    it('does not mutate the original array', () => {
      const items = [
        makeItem({ pipeline_entry_id: 1, is_overdue: false }),
        makeItem({ pipeline_entry_id: 2, is_overdue: true }),
      ];
      const original = [...items];
      helpers.sortActionItems(items);
      expect(items[0].pipeline_entry_id).toBe(original[0].pipeline_entry_id);
    });
  });

  describe('formatActionDate', () => {
    it('returns a formatted string for a valid date', () => {
      const result = helpers.formatActionDate('2026-03-25T00:00:00');
      expect(typeof result).toBe('string');
      expect(result.length).toBeGreaterThan(0);
    });

    it('returns a fallback for null date', () => {
      const result = helpers.formatActionDate(null);
      expect(typeof result).toBe('string');
    });

    it('returns different output for different dates', () => {
      const a = helpers.formatActionDate('2026-03-25T00:00:00');
      const b = helpers.formatActionDate('2026-04-01T00:00:00');
      expect(a).not.toBe(b);
    });
  });
});

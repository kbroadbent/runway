import type { DashboardActionItem } from '../types';

export const DEFAULT_VISIBLE_COUNT = 5;

const TYPE_BADGES: Record<string, string> = {
	action: 'Action',
	interview: 'Interview',
	follow_up: 'Follow Up',
	deadline: 'Deadline'
};

const TYPE_BADGE_CLASSES: Record<string, string> = {
	action: 'badge-action',
	interview: 'badge-interview',
	follow_up: 'badge-follow-up',
	deadline: 'badge-deadline'
};

export function getTypeBadge(type: string): string {
	return TYPE_BADGES[type] ?? 'Other';
}

export function getTypeBadgeClass(type: string): string {
	return TYPE_BADGE_CLASSES[type] ?? 'badge-default';
}

export function isOverdue(item: DashboardActionItem): boolean {
	return item.is_overdue;
}

export function sliceItems(items: DashboardActionItem[], expanded: boolean): DashboardActionItem[] {
	if (expanded || items.length <= DEFAULT_VISIBLE_COUNT) {
		return items;
	}
	return items.slice(0, DEFAULT_VISIBLE_COUNT);
}

export function sortActionItems(items: DashboardActionItem[]): DashboardActionItem[] {
	return [...items].sort((a, b) => {
		if (a.is_overdue !== b.is_overdue) {
			return a.is_overdue ? -1 : 1;
		}
		const dateA = a.date ?? '';
		const dateB = b.date ?? '';
		return dateA.localeCompare(dateB);
	});
}

export function formatActionDate(date: string | null): string {
	if (!date) return '—';
	const d = new Date(date);
	return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

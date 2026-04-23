import { STAGES } from './pipeline';
import type { PipelineEntry } from './types';

export interface LaneCount {
	key: string;
	label: string;
	count: number;
}

export interface LaneCountResult {
	active: LaneCount[];
	terminal: LaneCount[];
	activeTotal: number;
	terminalTotal: number;
}

const TERMINAL_STAGES = new Set(['rejected', 'archived', 'ghosted']);

export function computeLaneCounts(entries: PipelineEntry[]): LaneCountResult {
	// Build a map from sub-lane key -> parent key
	const subLaneToParent = new Map<string, string>();
	for (const stage of STAGES) {
		if (stage.subLanes) {
			for (const sub of stage.subLanes) {
				subLaneToParent.set(sub.key, stage.key);
			}
		}
	}

	// Count entries per top-level stage
	const counts = new Map<string, number>();
	for (const entry of entries) {
		const parentKey = subLaneToParent.get(entry.stage) ?? entry.stage;
		counts.set(parentKey, (counts.get(parentKey) ?? 0) + 1);
	}

	const active: LaneCount[] = [];
	const terminal: LaneCount[] = [];

	for (const stage of STAGES) {
		const lane: LaneCount = {
			key: stage.key,
			label: stage.label,
			count: counts.get(stage.key) ?? 0,
		};
		if (TERMINAL_STAGES.has(stage.key)) {
			terminal.push(lane);
		} else {
			active.push(lane);
		}
	}

	const activeTotal = active.reduce((sum, l) => sum + l.count, 0);
	const terminalTotal = terminal.reduce((sum, l) => sum + l.count, 0);

	return { active, terminal, activeTotal, terminalTotal };
}

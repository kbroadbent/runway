export type StageConfig = {
	key: string;
	label: string;
	subLanes?: { key: string; label: string }[];
};

export const STAGES: StageConfig[] = [
	{ key: 'interested', label: 'Interested' },
	{ key: 'applying', label: 'Applying' },
	{ key: 'applied', label: 'Applied' },
	{
		key: 'recruiter_screen',
		label: 'Recruiter Screen',
		subLanes: [
			{ key: 'recruiter_screen_scheduled', label: 'Scheduled' },
			{ key: 'recruiter_screen_completed', label: 'Completed' },
		],
	},
	{
		key: 'manager_screen',
		label: 'Manager Screen',
		subLanes: [
			{ key: 'manager_screen_scheduled', label: 'Scheduled' },
			{ key: 'manager_screen_completed', label: 'Completed' },
		],
	},
	{
		key: 'tech_screen',
		label: 'Tech Screen',
		subLanes: [
			{ key: 'tech_screen_scheduled', label: 'Scheduled' },
			{ key: 'tech_screen_completed', label: 'Completed' },
		],
	},
	{
		key: 'onsite',
		label: 'Onsite',
		subLanes: [
			{ key: 'onsite_scheduled', label: 'Scheduled' },
			{ key: 'onsite_completed', label: 'Completed' },
		],
	},
	{ key: 'offer', label: 'Offer' },
	{ key: 'rejected', label: 'Rejected' },
	{ key: 'archived', label: 'Archived' },
];

export const STAGE_DATE_FIELDS: Record<string, { label: string; field: string }[]> = {
	applied: [{ label: 'Applied Date', field: 'applied_date' }],
	recruiter_screen_scheduled: [{ label: 'Recruiter Screen Date', field: 'recruiter_screen_date' }],
	manager_screen_scheduled: [{ label: 'Manager Screen Date', field: 'manager_screen_date' }],
	tech_screen_scheduled: [{ label: 'Tech Screen Date', field: 'tech_screen_date' }],
	onsite_scheduled: [{ label: 'Onsite Date', field: 'onsite_date' }],
	offer: [
		{ label: 'Offer Date', field: 'offer_date' },
		{ label: 'Offer Expiration Date', field: 'offer_expiration_date' },
	],
};

export const AUTO_DATE_STAGES: Record<string, string> = {};

export const ACTIVE_STAGES = STAGES.filter(
	(s) => s.key !== 'rejected' && s.key !== 'archived'
);
export const TERMINAL_STAGES = STAGES.filter(
	(s) => s.key === 'rejected' || s.key === 'archived'
);

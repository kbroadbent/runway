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

export type LeadSource = 'referral' | 'recruiter_inbound' | 'recruiter_outbound' | 'cold_apply';

export const LEAD_SOURCE_LABELS: Record<LeadSource, string> = {
  referral: 'Referral',
  recruiter_inbound: 'Recruiter (Inbound)',
  recruiter_outbound: 'Recruiter (Outbound)',
  cold_apply: 'Cold Apply',
};

export const LEAD_SOURCE_DESCRIPTIONS: Record<LeadSource, string> = {
  referral: 'Someone referred you to this role',
  recruiter_inbound: 'A recruiter reached out to you',
  recruiter_outbound: 'You reached out to a recruiter',
  cold_apply: 'You found and applied independently',
};

export interface Company {
  id: number;
  name: string;
  website: string | null;
  glassdoor_rating: number | null;
  glassdoor_url: string | null;
  levels_salary_data: string | null;
  levels_url: string | null;
  blind_url: string | null;
  employee_count: number | null;
  industry: string | null;
  notes: string | null;
  common_questions: string | null;
  last_researched_at: string | null;
  created_at: string;
}

export interface JobPosting {
  id: number;
  title: string;
  company: Company | null;
  company_name: string | null;
  description: string | null;
  location: string | null;
  remote_type: string | null;
  salary_min: number | null;
  salary_max: number | null;
  url: string | null;
  source: string;
  date_posted: string | null;
  date_saved: string;
  status: string;
  tier: 1 | 2 | 3 | null;
  pipeline_stage: string | null;
  has_raw_content: boolean;
  notes: string | null;
  lead_source: LeadSource;
  is_closed_detected: boolean;
  closed_check_dismissed: boolean;
}

export interface PipelineEntry {
  id: number;
  job_posting: JobPosting;
  stage: string;
  position: number;
  next_action: string | null;
  next_action_date: string | null;
  applied_date: string | null;
  recruiter_screen_date: string | null;
  manager_screen_date: string | null;
  tech_screen_date: string | null;
  onsite_date: string | null;
  offer_date: string | null;
  offer_expiration_date: string | null;
  custom_dates: CustomDate[];
  created_at: string;
  updated_at: string;
}

export interface PipelineHistory {
  id: number;
  event_type: string;
  from_stage: string | null;
  to_stage: string | null;
  note: string | null;
  description: string | null;
  event_date: string | null;
  changed_at: string;
}

export interface CustomDate {
  id: number;
  label: string;
  date: string;
  created_at: string;
}

export interface PipelineComment {
  id: number;
  content: string;
  created_at: string;
  updated_at: string;
}

export interface InterviewNote {
  id: number;
  round: string;
  scheduled_at: string | null;
  interviewers: string | null;
  notes: string | null;
  outcome: string | null;
  created_at: string;
}

export interface CompanyInterview {
  id: number;
  round: string;
  scheduled_at: string | null;
  interviewers: string | null;
  notes: string | null;
  outcome: string | null;
  created_at: string;
  posting_id: number;
  posting_title: string;
}

export interface SearchProfile {
  id: number;
  name: string;
  search_term: string | null;
  location: string | null;
  remote_filter: string | null;
  salary_min: number | null;
  salary_max: number | null;
  job_type: string | null;
  sources: string[] | null;
  exclude_terms: string[] | null;
  run_interval: number | null;
  is_auto_enabled: boolean;
  created_at: string;
  last_run_at: string | null;
  new_result_count: number;
}

export interface ImportPreview {
  title: string | null;
  company_name: string | null;
  location: string | null;
  remote_type: string | null;
  salary_min: number | null;
  salary_max: number | null;
  description: string | null;
  url: string | null;
  raw_content: string | null;
  ai_used?: boolean;
  notes?: string | null;
  lead_source?: LeadSource;
}

export interface DashboardActionItem {
  pipeline_entry_id: number;
  job_title: string;
  company_name: string | null;
  type: string;
  description: string;
  date: string | null;
  is_overdue: boolean;
}

export interface ClosedPostingAlert {
  id: number;
  title: string;
  company_name: string | null;
  url: string | null;
}

export interface DashboardResponse {
  lane_counts: Record<string, number>;
  upcoming_events: DashboardActionItem[];
  action_items: DashboardActionItem[];
  closed_postings: ClosedPostingAlert[];
}

export interface PostingsFilter {
  search?: string;
  source?: string;
  salary_min?: number;
  salary_max?: number;
  remote_type?: string;
  lead_source?: LeadSource;
}

export interface FunnelTransition {
	from_stage: string;
	to_stage: string;
	count: number;
}

export interface FunnelResponse {
	transitions: FunnelTransition[];
	stage_counts: Record<string, number>;
}

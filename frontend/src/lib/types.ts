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
}

export interface PipelineEntry {
  id: number;
  job_posting: JobPosting;
  stage: string;
  position: number;
  notes: string | null;
  next_action: string | null;
  next_action_date: string | null;
  created_at: string;
  updated_at: string;
}

export interface PipelineHistory {
  id: number;
  from_stage: string | null;
  to_stage: string;
  note: string | null;
  changed_at: string;
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
  ai_used: boolean;
}

export interface PostingsFilter {
  search?: string;
  source?: string;
  salary_min?: number;
  salary_max?: number;
  remote_type?: string;
}

import type {
  Company,
  JobPosting,
  PipelineEntry,
  PipelineHistory,
  InterviewNote,
  CompanyInterview,
  SearchProfile,
  ImportPreview,
  PostingsFilter,
} from './types';

const BASE = 'http://localhost:8000/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const resp = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!resp.ok) {
    throw new Error(`API error: ${resp.status} ${resp.statusText}`);
  }
  if (resp.status === 204) return undefined as T;
  return resp.json();
}

function toQuery(params: Record<string, unknown>): string {
  const entries = Object.entries(params).filter(([, v]) => v != null);
  return entries.length
    ? '?' + new URLSearchParams(entries.map(([k, v]) => [k, String(v)])).toString()
    : '';
}

export const searchProfiles = {
  list: () => request<SearchProfile[]>('/search-profiles'),
  create: (data: Partial<SearchProfile>) =>
    request<SearchProfile>('/search-profiles', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: number, data: Partial<SearchProfile>) =>
    request<SearchProfile>(`/search-profiles/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (id: number) =>
    request<void>(`/search-profiles/${id}`, { method: 'DELETE' }),
  run: (id: number) =>
    request<{ new_count: number; total_count: number }>(`/search-profiles/${id}/run`, {
      method: 'POST',
    }),
  postings: (id: number) => request<JobPosting[]>(`/search-profiles/${id}/postings`),
};

export const postings = {
  list: (status: string = 'saved', filters?: PostingsFilter) =>
    request<JobPosting[]>(`/postings${toQuery({ status, ...(filters as Record<string, unknown> ?? {}) })}`),
  get: (id: number) => request<JobPosting>(`/postings/${id}`),
  save: (id: number) => request<JobPosting>(`/postings/${id}/save`, { method: 'POST' }),
  dismiss: (id: number) => request<JobPosting>(`/postings/${id}/dismiss`, { method: 'POST' }),
  create: (data: Partial<JobPosting> & { company_name?: string }) =>
    request<JobPosting>('/postings', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: number, data: Partial<JobPosting> & { company_name?: string }) =>
    request<JobPosting>(`/postings/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (id: number) => request<void>(`/postings/${id}`, { method: 'DELETE' }),
  importPreview: (data: { text?: string; url?: string }) =>
    request<ImportPreview>('/postings/import', { method: 'POST', body: JSON.stringify(data) }),
  importConfirm: (data: ImportPreview) =>
    request<JobPosting>('/postings/import/confirm', { method: 'POST', body: JSON.stringify(data) }),
  linkCompany: (id: number) =>
    request<JobPosting>(`/postings/${id}/link-company`, { method: 'POST' }),
  summarize: (id: number) =>
    request<JobPosting>(`/postings/${id}/summarize`, { method: 'POST' }),
};

export const pipeline = {
  list: () => request<Record<string, PipelineEntry[]>>('/pipeline'),
  add: (data: { job_posting_id: number; stage?: string }) =>
    request<PipelineEntry>('/pipeline', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: number, data: Partial<PipelineEntry>) =>
    request<PipelineEntry>(`/pipeline/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  move: (id: number, data: { to_stage: string; note?: string }) =>
    request<PipelineEntry>(`/pipeline/${id}/move`, { method: 'PUT', body: JSON.stringify(data) }),
  history: (id: number) => request<PipelineHistory[]>(`/pipeline/${id}/history`),
  interviews: (id: number) => request<InterviewNote[]>(`/pipeline/${id}/interviews`),
  addInterview: (id: number, data: Partial<InterviewNote>) =>
    request<InterviewNote>(`/pipeline/${id}/interviews`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
};

export const interviews = {
  update: (id: number, data: Partial<InterviewNote>) =>
    request<InterviewNote>(`/interviews/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (id: number) => request<void>(`/interviews/${id}`, { method: 'DELETE' }),
};

export const companies = {
  list: () => request<Company[]>('/companies'),
  get: (id: number) => request<Company>(`/companies/${id}`),
  create: (data: Partial<Company>) =>
    request<Company>('/companies', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: number, data: Partial<Company>) =>
    request<Company>(`/companies/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  research: (id: number) =>
    request<Company>(`/companies/${id}/research`, { method: 'POST' }),
  interviews: (id: number) =>
    request<CompanyInterview[]>(`/companies/${id}/interviews`),
};

export const searchResults = {
  markReviewed: (id: number) =>
    request<void>(`/search-results/${id}/mark-reviewed`, { method: 'POST' }),
};

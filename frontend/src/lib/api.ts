import type {
  Company,
  JobPosting,
  PipelineEntry,
  PipelineHistory,
  PipelineComment,
  InterviewNote,
  CompanyInterview,
  SearchProfile,
  ImportPreview,
  PostingsFilter,
  DashboardResponse,
  FunnelResponse,
  CustomDate,
} from './types';

function getBase() {
  return (import.meta.env.VITE_API_BASE || 'http://localhost:8000/api').replace(/\/$/, '');
}

export class ApiError extends Error {
  status: number;
  data: unknown;
  constructor(status: number, statusText: string, data: unknown) {
    super(`API error: ${status} ${statusText}`);
    this.status = status;
    this.data = data;
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const resp = await fetch(`${getBase()}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!resp.ok) {
    let data: unknown = null;
    try { data = await resp.json(); } catch { /* ignore */ }
    throw new ApiError(resp.status, resp.statusText, data);
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
  dismissClosed: (id: number) =>
    request<JobPosting>(`/postings/${id}/dismiss-closed`, { method: 'POST' }),
};

export const pipeline = {
  list: (filters?: { search?: string; tier?: number; lead_source?: string }) =>
    request<Record<string, PipelineEntry[]>>(`/pipeline${toQuery(filters ?? {})}`),
  add: (data: { job_posting_id: number; stage?: string }) =>
    request<PipelineEntry>('/pipeline', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: number, data: Partial<PipelineEntry>) =>
    request<PipelineEntry>(`/pipeline/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  move: (id: number, data: { to_stage: string; note?: string; stage_dates?: Record<string, string | null> }) =>
    request<PipelineEntry>(`/pipeline/${id}/move`, { method: 'PUT', body: JSON.stringify(data) }),
  history: (id: number) => request<PipelineHistory[]>(`/pipeline/${id}/history`),
  addEvent: (id: number, data: { description: string; event_date?: string }) =>
    request<PipelineHistory>(`/pipeline/${id}/history`, { method: 'POST', body: JSON.stringify(data) }),
  interviews: (id: number) => request<InterviewNote[]>(`/pipeline/${id}/interviews`),
  addInterview: (id: number, data: Partial<InterviewNote>) =>
    request<InterviewNote>(`/pipeline/${id}/interviews`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  comments: (id: number) => request<PipelineComment[]>(`/pipeline/${id}/comments`),
  addComment: (id: number, data: { content: string }) =>
    request<PipelineComment>(`/pipeline/${id}/comments`, { method: 'POST', body: JSON.stringify(data) }),
  customDates: (id: number) => request<CustomDate[]>(`/pipeline/${id}/dates`),
  createCustomDate: (id: number, data: { label: string; date: string }) =>
    request<CustomDate>(`/pipeline/${id}/dates`, { method: 'POST', body: JSON.stringify(data) }),
  updateCustomDate: (id: number, dateId: number, data: { label?: string; date?: string }) =>
    request<CustomDate>(`/pipeline/${id}/dates/${dateId}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteCustomDate: (id: number, dateId: number) =>
    request<void>(`/pipeline/${id}/dates/${dateId}`, { method: 'DELETE' }),
};

export const interviews = {
  update: (id: number, data: Partial<InterviewNote>) =>
    request<InterviewNote>(`/interviews/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (id: number) => request<void>(`/interviews/${id}`, { method: 'DELETE' }),
};

export const pipelineHistory = {
  delete: (id: number) => request<void>(`/pipeline-history/${id}`, { method: 'DELETE' }),
};

export const pipelineComments = {
  update: (id: number, data: { content: string }) =>
    request<PipelineComment>(`/pipeline-comments/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (id: number) => request<void>(`/pipeline-comments/${id}`, { method: 'DELETE' }),
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

export const dashboard = {
  get: () => request<DashboardResponse>('/dashboard'),
  funnel: (params?: { start?: string; end?: string }) =>
    request<FunnelResponse>(`/dashboard/funnel${toQuery(params ?? {})}`),
};

export const searchResults = {
  markReviewed: (id: number) =>
    request<void>(`/search-results/${id}/mark-reviewed`, { method: 'POST' }),
};

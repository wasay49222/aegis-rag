// src/lib/api.ts
const API_BASE_URL = 'http://localhost:8000';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface UploadResponse {
  message: string;
  document_id: string;
  chunk_count: number;
}

export interface QueryRequest {
  question: string;
  document_id?: string;
}

export interface QueryResponse {
  answer: string;
  sources: string[];
  pii_redacted_count: number;
  blocked: boolean;
  agent_retries: number;
}

export interface AuditLog {
  id: string;
  event_type: string;
  user_id: string;
  details: Record<string, unknown>;
  created_at: string;
}

export interface AuditStats {
  pii_redactions: number;
  injections_blocked: number;
  hallucinations: number;
  documents: number;
}

export interface DashboardStats {
  security: {
    pii_redactions: number;
    injections_blocked: number;
    hallucinations: number;
  };
  documents: number;
  queries: number;
  mlops: {
    faithfulness: number;
    answer_relevance: number;
    context_precision: number;
  };
  period: string;
}

export interface RecentActivity {
  id: string;
  event_type: string;
  created_at: string;
  details: Record<string, unknown>;
}

class ApiClient {
  constructor() {}

  setToken(token: string) {
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', token);
    }
  }

  getToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('access_token');
    }
    return null;
  }

  logout() {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
    }
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = this.getToken();
    
    if (!token && !endpoint.includes('/auth/login')) {
      throw new Error('Not authenticated. Please log in again.');
    }

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    };

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      if (response.status === 401) {
        this.logout();
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
      }
      const errorText = await response.text();
      throw new Error(`API Error: ${response.status} - ${errorText}`);
    }

    return response.json();
  }

  async login(data: LoginRequest) {
    const response = await this.request<{ access_token: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    this.setToken(response.access_token);
    return response;
  }

  async uploadDocument(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const token = this.getToken();
    if (!token) {
      throw new Error('Not authenticated. Please log in again.');
    }

    const response = await fetch(`${API_BASE_URL}/documents/upload`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Upload failed: ${errorText}`);
    }
    return response.json();
  }

  async query(data: QueryRequest): Promise<QueryResponse> {
  return this.request<QueryResponse>('/rag/query', {
    method: 'POST',
    body: JSON.stringify({
      question: data.question,
      document_id: data.document_id
    }),
  });
}

  async getAuditLogs(limit: number = 50, eventType?: string): Promise<AuditLog[]> {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (eventType) {
      params.append('event_type', eventType);
    }
    return this.request<AuditLog[]>(`/audit/logs?${params}`);
  }

  async getAuditStats(): Promise<AuditStats> {
    return this.request<AuditStats>('/audit/stats');
  }

  async getDashboardStats(): Promise<DashboardStats> {
    return this.request<DashboardStats>('/dashboard/stats');
  }

  async getRecentActivity(limit: number = 10): Promise<RecentActivity[]> {
    return this.request<RecentActivity[]>(`/dashboard/recent-activity?limit=${limit}`);
  }
}

export const api = new ApiClient();
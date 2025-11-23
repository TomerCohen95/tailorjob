import { supabase } from '@/integrations/supabase/client';

const API_BASE_URL = 'http://localhost:8000/api';

/**
 * Get the current user's JWT token from Supabase
 */
async function getAuthToken(): Promise<string | null> {
  const { data: { session } } = await supabase.auth.getSession();
  return session?.access_token || null;
}

/**
 * Make an authenticated API request to the backend
 */
async function fetchAPI(endpoint: string, options: RequestInit = {}) {
  const token = await getAuthToken();
  
  if (!token) {
    throw new Error('Not authenticated');
  }

  const headers = {
    'Authorization': `Bearer ${token}`,
    ...options.headers,
  };

  // Don't set Content-Type for FormData (browser will set it with boundary)
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || `Request failed with status ${response.status}`);
  }

  return response.json();
}

// ============================================================================
// CV API
// ============================================================================

export interface CV {
  id: string;
  user_id: string;
  filename: string;
  file_path: string;
  file_size: number;
  file_type: string;
  status: 'uploaded' | 'parsing' | 'parsed' | 'error';
  created_at: string;
  updated_at: string;
}

export interface CVSections {
  id: string;
  cv_id: string;
  summary: string;
  skills: string;
  experience: string;
  education: string;
  certifications: string;
  created_at: string;
  updated_at: string;
}

export interface CVWithSections {
  cv: CV;
  sections: CVSections | null;
}

export const cvAPI = {
  /**
   * Upload a CV file
   */
  async upload(file: File): Promise<CV> {
    const formData = new FormData();
    formData.append('file', file);
    
    return fetchAPI('/cv/upload', {
      method: 'POST',
      body: formData,
    });
  },

  /**
   * List all CVs for the current user
   */
  async list(): Promise<CV[]> {
    return fetchAPI('/cv/list');
  },

  /**
   * Get a specific CV by ID with its parsed sections
   */
  async get(cvId: string): Promise<CVWithSections> {
    return fetchAPI(`/cv/${cvId}`);
  },

  /**
   * Delete a CV
   */
  async delete(cvId: string): Promise<{ message: string }> {
    return fetchAPI(`/cv/${cvId}`, {
      method: 'DELETE',
    });
  },
};

// ============================================================================
// Jobs API
// ============================================================================

export interface Job {
  id: string;
  user_id: string;
  title: string;
  company: string;
  description: string;
  status: 'active' | 'archived';
  created_at: string;
  updated_at: string;
}

export interface CreateJobInput {
  title: string;
  company: string;
  description: string;
}

export interface UpdateJobInput {
  title?: string;
  company?: string;
  description?: string;
  status?: 'active' | 'archived';
}

export const jobsAPI = {
  /**
   * Create a new job posting
   */
  async create(data: CreateJobInput): Promise<Job> {
    return fetchAPI('/jobs/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * List all jobs for the current user
   */
  async list(): Promise<Job[]> {
    return fetchAPI('/jobs/');
  },

  /**
   * Get a specific job by ID
   */
  async get(jobId: string): Promise<Job> {
    return fetchAPI(`/jobs/${jobId}`);
  },

  /**
   * Update a job
   */
  async update(jobId: string, data: UpdateJobInput): Promise<Job> {
    return fetchAPI(`/jobs/${jobId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  /**
   * Delete a job
   */
  async delete(jobId: string): Promise<{ message: string }> {
    return fetchAPI(`/jobs/${jobId}`, {
      method: 'DELETE',
    });
  },
};

// ============================================================================
// Tailor API
// ============================================================================

export interface TailoredCV {
  id: string;
  cv_id: string;
  job_id: string;
  user_id: string;
  status: 'queued' | 'processing' | 'completed' | 'error';
  tailored_content?: string;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: string;
  tailored_cv_id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

export const tailorAPI = {
  /**
   * Tailor a CV for a specific job
   */
  async tailor(cvId: string, jobId: string): Promise<{
    message: string;
    tailored_cv_id: string;
    job_id: string;
  }> {
    return fetchAPI(`/tailor/${cvId}/${jobId}`, {
      method: 'POST',
    });
  },

  /**
   * Get a tailored CV
   */
  async get(cvId: string, jobId: string): Promise<TailoredCV> {
    return fetchAPI(`/tailor/${cvId}/${jobId}`);
  },

  /**
   * Get tailoring status
   */
  async getStatus(cvId: string, jobId: string): Promise<{
    tailored_cv_id: string;
    status: string;
    queue_status: string;
    created_at: string;
    updated_at: string;
  }> {
    return fetchAPI(`/tailor/${cvId}/${jobId}/status`);
  },

  /**
   * Send a chat message
   */
  async sendMessage(cvId: string, jobId: string, content: string): Promise<{
    user_message: ChatMessage;
    ai_response: ChatMessage;
  }> {
    return fetchAPI(`/chat/${cvId}/${jobId}`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    });
  },

  /**
   * Get chat history
   */
  async getChatHistory(cvId: string, jobId: string): Promise<{
    tailored_cv_id: string;
    messages: ChatMessage[];
  }> {
    return fetchAPI(`/chat/${cvId}/${jobId}/history`);
  },
};

// ============================================================================
// Health Check
// ============================================================================

export const healthAPI = {
  /**
   * Check if the backend is running
   */
  async check(): Promise<{ status: string; timestamp: string }> {
    const response = await fetch(`${API_BASE_URL.replace('/api', '')}/health`);
    return response.json();
  },
};

// ============================================================================
// Unified API Client Export
// ============================================================================

export const apiClient = {
  // CV operations
  getCVs: cvAPI.list,
  getCV: cvAPI.get,
  uploadCV: cvAPI.upload,
  deleteCV: cvAPI.delete,
  
  // Job operations
  getJobs: jobsAPI.list,
  getJob: jobsAPI.get,
  createJob: jobsAPI.create,
  updateJob: jobsAPI.update,
  deleteJob: jobsAPI.delete,
  
  // Tailor operations
  tailorCV: tailorAPI.tailor,
  getTailoredCV: tailorAPI.get,
  getTailoringStatus: tailorAPI.getStatus,
  sendChatMessage: tailorAPI.sendMessage,
  getChatHistory: tailorAPI.getChatHistory,
  
  // Health check
  healthCheck: healthAPI.check,
};
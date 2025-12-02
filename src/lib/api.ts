import { supabase } from '@/integrations/supabase/client';

// Use environment variable if set, otherwise use localhost for dev
const API_BASE_URL = import.meta.env.VITE_API_URL ||
  (import.meta.env.PROD
    ? 'https://tailorjob.onrender.com/api'  // Production backend on Render
    : 'http://localhost:8000/api'           // Local development
  );

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
    
    // If detail is an object (structured error with upgrade info), throw it as-is
    if (typeof error.detail === 'object' && error.detail !== null) {
      const err: any = new Error(error.detail.error || error.detail.message || 'Request failed');
      err.upgrade_info = error.detail;
      throw err;
    }
    
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
  original_filename: string;
  file_path: string;
  file_size: number;
  mime_type: string;
  status: 'uploaded' | 'parsing' | 'parsed' | 'error';
  is_primary?: boolean;
  file_hash?: string;
  error_message?: string;
  parsed_at?: string;
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

export interface CVNotification {
  id: string;
  user_id: string;
  cv_id: string;
  type: 'cv_parsed' | 'cv_error';
  message: string;
  read: boolean;
  created_at: string;
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
   * Manually trigger re-parsing of an existing CV
   */
  async reparse(cvId: string): Promise<{ cv_id: string; job_id: string; status: string; message: string }> {
    return fetchAPI(`/cv/${cvId}/reparse`, {
      method: 'POST',
    });
  },

  /**
   * Set a CV as primary
   */
  async setPrimary(cvId: string): Promise<{ message: string; cv_id: string }> {
    return fetchAPI(`/cv/${cvId}/set-primary`, {
      method: 'POST',
    });
  },

  /**
   * Delete a CV
   */
  async delete(cvId: string): Promise<{ message: string }> {
    return fetchAPI(`/cv/${cvId}`, {
      method: 'DELETE',
    });
  },

  /**
   * Get all unread notifications
   */
  async getNotifications(): Promise<CVNotification[]> {
    return fetchAPI('/cv/notifications');
  },

  /**
   * Mark a notification as read
   */
  async markNotificationRead(notificationId: string): Promise<{ message: string }> {
    return fetchAPI(`/cv/notifications/${notificationId}/read`, {
      method: 'POST',
    });
  },

  /**
   * Delete a notification
   */
  async deleteNotification(notificationId: string): Promise<{ message: string }> {
    return fetchAPI(`/cv/notifications/${notificationId}`, {
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
  url?: string;
  requirements_matrix?: {
    must_have: Array<{
      category: string;
      requirement: string;
      keywords: string[];
    }>;
    nice_to_have: Array<{
      category: string;
      requirement: string;
      keywords: string[];
    }>;
  };
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

  /**
   * Scrape job details from a URL and save to database
   */
  async scrapeFromUrl(url: string): Promise<{ title: string; company: string; description: string; id: string; saved: boolean }> {
    return fetchAPI('/jobs/scrape', {
      method: 'POST',
      body: JSON.stringify({ url }),
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
// Matching API (AI CV-to-Job Scoring)
// ============================================================================

export interface MatchScore {
  overall_score: number;
  matcher_version?: string;  // Which matcher version was used (v2.x, v3.0, v5.0)
  
  // v2.x fields (legacy)
  deterministic_score?: number;
  fit_score?: number;
  must_have_score?: number;
  nice_to_have_score?: number;
  
  // v3.0 fields (AI-first)
  ai_holistic_score?: number;
  component_average?: number;
  scoring_method?: string;
  
  // Component scores (both versions)
  skills_score?: number;
  experience_score?: number;
  qualifications_score?: number;
  
  // v3.0 domain analysis
  domain_fit?: 'SAME' | 'ADJACENT' | 'ORTHOGONAL' | 'UNKNOWN';
  domain_mismatch?: boolean;
  domain_mismatch_severity?: 'none' | 'moderate' | 'severe';
  domain_explanation?: string;
  transferability_assessment?: string;
  reasoning?: string;
  
  // Match details (flattened for backward compatibility)
  strengths?: string[];
  gaps?: string[];
  recommendations?: string[];
  matched_skills?: string[];
  missing_skills?: string[];
  matched_qualifications?: string[];
  missing_qualifications?: string[];
  
  // Legacy nested format (kept for backward compatibility)
  analysis?: {
    matcher_version?: string;
    strengths: string[];
    gaps: string[];
    recommendations: string[];
    matched_skills: string[];
    missing_skills: string[];
    matched_qualifications: string[];
    missing_qualifications: string[];
  };
  
  cached: boolean;
  created_at: string;
}

export const matchingAPI = {
  /**
   * Analyze CV-to-job match score with AI
   * Returns cached result if available (< 7 days old)
   */
  async analyze(cvId: string, jobId: string): Promise<MatchScore> {
    return fetchAPI('/matching/analyze', {
      method: 'POST',
      body: JSON.stringify({ cv_id: cvId, job_id: jobId }),
    });
  },

  /**
   * Get cached match score if available (quick lookup for badges)
   * Returns null if not analyzed yet or expired
   */
  async getScore(cvId: string, jobId: string): Promise<MatchScore | null> {
    return fetchAPI(`/matching/score/${cvId}/${jobId}`);
  },

  /**
   * Delete cached match score (forces re-analysis on next request)
   */
  async deleteScore(cvId: string, jobId: string): Promise<{ message: string; deleted: boolean }> {
    return fetchAPI(`/matching/score/${cvId}/${jobId}`, {
      method: 'DELETE',
    });
  },
};

// ============================================================================
// Health Check
// ============================================================================

// ============================================================================
// Payments API
// ============================================================================

export interface Subscription {
  id: string;
  user_id: string;
  paypal_subscription_id: string;
  plan_id: string;
  tier: 'free' | 'basic' | 'pro';
  status: 'active' | 'cancelled' | 'suspended' | 'expired';
  start_date: string;
  end_date?: string;
  next_billing_date?: string;
  auto_renew: boolean;
  created_at: string;
  updated_at: string;
}

export interface UsageData {
  user_id: string;
  tier: 'free' | 'basic' | 'pro';
  period_start: string;
  period_end: string;
  cv_uploads: number;
  cv_limit: number;
  job_matches: number;
  match_limit: number;
  tailored_cvs: number;
  tailor_limit: number;
}

export interface CreateSubscriptionResponse {
  subscription_id: string;
  approval_url: string;
  plan_id: string;
}

export const paymentsAPI = {
  /**
   * Create a new PayPal subscription
   */
  async createSubscription(tier: 'basic' | 'pro'): Promise<CreateSubscriptionResponse> {
    const currentUrl = window.location.origin;
    return fetchAPI('/payments/subscriptions/create', {
      method: 'POST',
      body: JSON.stringify({
        plan_id: tier === 'basic' ? 'basic_monthly' : 'pro_monthly',
        return_url: `${currentUrl}/account?success=true`,
        cancel_url: `${currentUrl}/pricing?cancelled=true`,
      }),
    });
  },

  /**
   * Activate subscription after PayPal approval
   */
  async activateSubscription(subscriptionId: string): Promise<Subscription> {
    return fetchAPI('/payments/subscriptions/activate', {
      method: 'POST',
      body: JSON.stringify({ subscription_id: subscriptionId }),
    });
  },

  /**
   * Get current user's subscription
   */
  async getSubscription(): Promise<Subscription | null> {
    try {
      return await fetchAPI('/payments/subscriptions/me');
    } catch (error) {
      // Return null if no subscription found (free tier)
      return null;
    }
  },

  /**
   * Cancel current subscription
   */
  async cancelSubscription(): Promise<{ message: string }> {
    return fetchAPI('/payments/subscriptions/cancel', {
      method: 'POST',
    });
  },

  /**
   * Upgrade subscription to a higher tier
   */
  async upgradeSubscription(newTier: 'basic' | 'pro'): Promise<CreateSubscriptionResponse> {
    return fetchAPI('/payments/subscriptions/upgrade', {
      method: 'POST',
      body: JSON.stringify({ new_tier: newTier }),
    });
  },

  /**
   * Get current usage statistics
   */
  async getUsage(): Promise<UsageData> {
    return fetchAPI('/payments/usage');
  },
};

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
  
  // Matching operations
  analyzeMatch: matchingAPI.analyze,
  getMatchScore: matchingAPI.getScore,
  deleteMatchScore: matchingAPI.deleteScore,
  
  // Payment operations
  createSubscription: paymentsAPI.createSubscription,
  activateSubscription: paymentsAPI.activateSubscription,
  getSubscription: paymentsAPI.getSubscription,
  cancelSubscription: paymentsAPI.cancelSubscription,
  upgradeSubscription: paymentsAPI.upgradeSubscription,
  getUsage: paymentsAPI.getUsage,
  
  // Health check
  healthCheck: healthAPI.check,
};
import { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react';
import { apiClient } from '@/lib/api';
import { toast } from 'sonner';

export interface ParsingState {
  cvId: string;
  filename: string;
  status: 'uploading' | 'parsing' | 'parsed' | 'error';
  progress: number; // 0-100
  stage: string;
  startTime: Date;
  estimatedCompletion?: Date;
  error?: string;
}

interface CVParsingContextType {
  parsingCVs: Map<string, ParsingState>;
  startParsing: (cvId: string, filename: string) => void;
  updateProgress: (cvId: string, progress: number, stage: string) => void;
  completeParsing: (cvId: string, metadata?: any) => void;
  failParsing: (cvId: string, error: string) => void;
  removeParsing: (cvId: string) => void;
  isAnyParsing: boolean;
}

const CVParsingContext = createContext<CVParsingContextType | undefined>(undefined);

const STORAGE_KEY = 'cv_parsing_state';
const POLL_INTERVAL = 2000; // 2 seconds
const MAX_POLL_DURATION = 5 * 60 * 1000; // 5 minutes timeout

// Helper to calculate estimated completion based on file size and historical data
function calculateEstimatedCompletion(startTime: Date, progress: number): Date | undefined {
  if (progress === 0) return undefined;
  
  const elapsed = Date.now() - startTime.getTime();
  const estimatedTotal = (elapsed / progress) * 100;
  const remaining = estimatedTotal - elapsed;
  
  return new Date(Date.now() + remaining);
}

export function CVParsingProvider({ children }: { children: ReactNode }) {
  const [parsingCVs, setParsingCVs] = useState<Map<string, ParsingState>>(new Map());
  const [pollInterval, setPollInterval] = useState<NodeJS.Timeout | null>(null);

  // Load state from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const data = JSON.parse(stored);
        const restoredMap = new Map<string, ParsingState>();
        
        Object.entries(data).forEach(([cvId, state]: [string, any]) => {
          // Only restore parsing/uploading states
          if (state.status === 'parsing' || state.status === 'uploading') {
            restoredMap.set(cvId, {
              ...state,
              startTime: new Date(state.startTime),
              estimatedCompletion: state.estimatedCompletion ? new Date(state.estimatedCompletion) : undefined,
            });
          }
        });
        
        if (restoredMap.size > 0) {
          setParsingCVs(restoredMap);
        }
      }
    } catch (error) {
      console.error('Failed to restore parsing state:', error);
    }
  }, []);

  // Save state to localStorage whenever it changes
  useEffect(() => {
    if (parsingCVs.size > 0) {
      const data = Object.fromEntries(parsingCVs);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  }, [parsingCVs]);

  // Poll for CV status updates
  const pollCVStatus = useCallback(async () => {
    const now = Date.now();
    const updates = new Map<string, ParsingState>();
    
    for (const [cvId, state] of parsingCVs) {
      // Skip if already completed or errored
      if (state.status === 'parsed' || state.status === 'error') continue;
      
      // Timeout check
      if (now - state.startTime.getTime() > MAX_POLL_DURATION) {
        updates.set(cvId, {
          ...state,
          status: 'error',
          error: 'Parsing timeout - please try re-parsing',
          progress: 0,
        });
        continue;
      }
      
      try {
        // Get CV status from API
        const data = await apiClient.getCV(cvId);
        const cv = data.cv;
        
        if (!cv) continue;
        
        if (cv.status === 'parsed') {
          updates.set(cvId, {
            ...state,
            status: 'parsed',
            progress: 100,
            stage: 'Complete!',
          });
          
          // Show celebration toast
          toast.success(`🎉 ${state.filename} is ready!`, {
            description: 'Your CV has been successfully parsed',
            duration: 5000,
          });
        } else if (cv.status === 'error') {
          updates.set(cvId, {
            ...state,
            status: 'error',
            error: cv.error_message || 'Parsing failed',
            progress: 0,
          });
          
          toast.error(`Failed to parse ${state.filename}`, {
            description: cv.error_message || 'Please try again',
          });
        } else if (cv.status === 'parsing') {
          // Update progress estimate based on time elapsed
          const elapsed = now - state.startTime.getTime();
          const estimatedProgress = Math.min(90, Math.floor((elapsed / 30000) * 100)); // Assume 30s total
          
          updates.set(cvId, {
            ...state,
            progress: Math.max(state.progress, estimatedProgress),
            estimatedCompletion: calculateEstimatedCompletion(state.startTime, estimatedProgress),
          });
        }
      } catch (error) {
        console.error(`Error polling CV ${cvId}:`, error);
      }
    }
    
    // Apply updates if any
    if (updates.size > 0) {
      setParsingCVs(prev => {
        const newMap = new Map(prev);
        updates.forEach((state, cvId) => {
          newMap.set(cvId, state);
        });
        return newMap;
      });
    }
  }, [parsingCVs]);

  // Start polling when we have parsing CVs
  useEffect(() => {
    const hasParsingCVs = Array.from(parsingCVs.values()).some(
      state => state.status === 'parsing' || state.status === 'uploading'
    );
    
    if (hasParsingCVs && !pollInterval) {
      const interval = setInterval(pollCVStatus, POLL_INTERVAL);
      setPollInterval(interval);
    } else if (!hasParsingCVs && pollInterval) {
      clearInterval(pollInterval);
      setPollInterval(null);
    }
    
    return () => {
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    };
  }, [parsingCVs, pollInterval, pollCVStatus]);

  // Pause polling when page is hidden (battery optimization)
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden && pollInterval) {
        clearInterval(pollInterval);
        setPollInterval(null);
      } else if (!document.hidden) {
        // Resume polling
        const hasParsingCVs = Array.from(parsingCVs.values()).some(
          state => state.status === 'parsing' || state.status === 'uploading'
        );
        if (hasParsingCVs) {
          const interval = setInterval(pollCVStatus, POLL_INTERVAL);
          setPollInterval(interval);
        }
      }
    };
    
    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [pollInterval, parsingCVs, pollCVStatus]);

  const startParsing = useCallback((cvId: string, filename: string) => {
    const newState: ParsingState = {
      cvId,
      filename,
      status: 'parsing',
      progress: 0,
      stage: 'Starting to parse your CV...',
      startTime: new Date(),
    };
    
    setParsingCVs(prev => {
      const newMap = new Map(prev);
      newMap.set(cvId, newState);
      return newMap;
    });
    
    toast.info(`📄 Parsing ${filename}`, {
      description: 'This usually takes 15-30 seconds',
    });
  }, []);

  const updateProgress = useCallback((cvId: string, progress: number, stage: string) => {
    setParsingCVs(prev => {
      const current = prev.get(cvId);
      if (!current) return prev;
      
      const newMap = new Map(prev);
      newMap.set(cvId, {
        ...current,
        progress,
        stage,
        estimatedCompletion: calculateEstimatedCompletion(current.startTime, progress),
      });
      return newMap;
    });
  }, []);

  const completeParsing = useCallback((cvId: string, metadata?: any) => {
    setParsingCVs(prev => {
      const current = prev.get(cvId);
      if (!current) return prev;
      
      const newMap = new Map(prev);
      newMap.set(cvId, {
        ...current,
        status: 'parsed',
        progress: 100,
        stage: 'Complete!',
      });
      
      // Auto-remove after 3 seconds
      setTimeout(() => {
        setParsingCVs(prev => {
          const newMap = new Map(prev);
          newMap.delete(cvId);
          return newMap;
        });
      }, 3000);
      
      return newMap;
    });
  }, []);

  const failParsing = useCallback((cvId: string, error: string) => {
    setParsingCVs(prev => {
      const current = prev.get(cvId);
      if (!current) return prev;
      
      const newMap = new Map(prev);
      newMap.set(cvId, {
        ...current,
        status: 'error',
        error,
        progress: 0,
      });
      return newMap;
    });
    
    toast.error('Parsing failed', {
      description: error,
    });
  }, []);

  const removeParsing = useCallback((cvId: string) => {
    setParsingCVs(prev => {
      const newMap = new Map(prev);
      newMap.delete(cvId);
      return newMap;
    });
  }, []);

  const isAnyParsing = Array.from(parsingCVs.values()).some(
    state => state.status === 'parsing' || state.status === 'uploading'
  );

  const value: CVParsingContextType = {
    parsingCVs,
    startParsing,
    updateProgress,
    completeParsing,
    failParsing,
    removeParsing,
    isAnyParsing,
  };

  return <CVParsingContext.Provider value={value}>{children}</CVParsingContext.Provider>;
}

export function useCVParsing() {
  const context = useContext(CVParsingContext);
  if (!context) {
    throw new Error('useCVParsing must be used within CVParsingProvider');
  }
  return context;
}
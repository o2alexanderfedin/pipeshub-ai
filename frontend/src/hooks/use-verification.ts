import { useMemo, useState, useEffect, useCallback } from 'react';

import type { VerificationState, VerificationResult } from '../types/verification.types';

// ----------------------------------------------------------------------

export type UseVerificationReturn = {
  state: VerificationState;
  toggleVerification: (enabled: boolean) => void;
  startVerification: (totalChunks: number) => void;
  updateProgress: (result: VerificationResult) => void;
  setError: (error: string) => void;
  reset: () => void;
};

const STORAGE_KEY = 'hupyy_verification_enabled';

export function useVerification(): UseVerificationReturn {
  const [state, setState] = useState<VerificationState>({
    enabled: false,
    inProgress: false,
    progress: null,
    error: null,
  });

  // Toggle verification on/off
  const toggleVerification = useCallback((enabled: boolean) => {
    setState((prev) => ({ ...prev, enabled }));
    // Persist to localStorage
    localStorage.setItem(STORAGE_KEY, enabled.toString());
  }, []);

  // Start verification with progress tracking
  const startVerification = useCallback((totalChunks: number) => {
    setState((prev) => ({
      ...prev,
      inProgress: true,
      progress: {
        total: totalChunks,
        completed: 0,
        failed: 0,
        percentage: 0,
        results: [],
      },
      error: null,
    }));
  }, []);

  // Update progress (called from WebSocket/polling)
  const updateProgress = useCallback((result: VerificationResult) => {
    setState((prev) => {
      if (!prev.progress) return prev;

      const newResults = [...prev.progress.results, result];
      const completed = prev.progress.completed + 1;
      const failed = result.verdict === 'error' ? prev.progress.failed + 1 : prev.progress.failed;
      const percentage = Math.round((completed / prev.progress.total) * 100);

      return {
        ...prev,
        progress: {
          ...prev.progress,
          completed,
          failed,
          percentage,
          results: newResults,
        },
        inProgress: completed < prev.progress.total,
      };
    });
  }, []);

  // Set error
  const setError = useCallback((error: string) => {
    setState((prev) => ({ ...prev, error, inProgress: false }));
  }, []);

  // Reset state
  const reset = useCallback(() => {
    setState((prev) => ({
      ...prev,
      inProgress: false,
      progress: null,
      error: null,
    }));
  }, []);

  // Load enabled state from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      setState((prev) => ({ ...prev, enabled: saved === 'true' }));
    }
  }, []);

  const memoizedValue = useMemo(
    () => ({
      state,
      toggleVerification,
      startVerification,
      updateProgress,
      setError,
      reset,
    }),
    [state, toggleVerification, startVerification, updateProgress, setError, reset]
  );

  return memoizedValue;
}

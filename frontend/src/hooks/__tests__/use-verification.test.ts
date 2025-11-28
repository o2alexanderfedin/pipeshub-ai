/**
 * Tests for useVerification hook
 *
 * NOTE: These tests require a test runner (Jest/Vitest) and React Testing Library to be configured.
 */

import type { VerificationResult } from 'src/types/verification.types';

import { act, renderHook } from '@testing-library/react';
import { it, expect, describe, afterEach, beforeEach } from 'vitest';

import { VerificationVerdict } from 'src/types/verification.types';

import { useVerification } from '../use-verification';

describe('useVerification', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('should initialize with default state', () => {
    const { result } = renderHook(() => useVerification());

    expect(result.current.state).toEqual({
      enabled: false,
      inProgress: false,
      progress: null,
      error: null,
    });
  });

  it('should load enabled state from localStorage on mount', () => {
    localStorage.setItem('hupyy_verification_enabled', 'true');

    const { result } = renderHook(() => useVerification());

    expect(result.current.state.enabled).toBe(true);
  });

  it('should toggle verification and persist to localStorage', () => {
    const { result } = renderHook(() => useVerification());

    act(() => {
      result.current.toggleVerification(true);
    });

    expect(result.current.state.enabled).toBe(true);
    expect(localStorage.getItem('hupyy_verification_enabled')).toBe('true');

    act(() => {
      result.current.toggleVerification(false);
    });

    expect(result.current.state.enabled).toBe(false);
    expect(localStorage.getItem('hupyy_verification_enabled')).toBe('false');
  });

  it('should start verification with correct initial progress', () => {
    const { result } = renderHook(() => useVerification());

    act(() => {
      result.current.startVerification(100);
    });

    expect(result.current.state.inProgress).toBe(true);
    expect(result.current.state.progress).toEqual({
      total: 100,
      completed: 0,
      failed: 0,
      percentage: 0,
      results: [],
    });
    expect(result.current.state.error).toBeNull();
  });

  it('should update progress when receiving results', () => {
    const { result } = renderHook(() => useVerification());

    act(() => {
      result.current.startVerification(10);
    });

    const verificationResult: VerificationResult = {
      chunk_id: 'chunk-1',
      verdict: VerificationVerdict.SAT,
      confidence: 0.95,
      formalization_similarity: 0.92,
      extraction_degradation: 0.05,
    };

    act(() => {
      result.current.updateProgress(verificationResult);
    });

    expect(result.current.state.progress?.completed).toBe(1);
    expect(result.current.state.progress?.failed).toBe(0);
    expect(result.current.state.progress?.percentage).toBe(10);
    expect(result.current.state.progress?.results).toHaveLength(1);
    expect(result.current.state.inProgress).toBe(true);
  });

  it('should increment failed count for error verdicts', () => {
    const { result } = renderHook(() => useVerification());

    act(() => {
      result.current.startVerification(10);
    });

    const errorResult: VerificationResult = {
      chunk_id: 'chunk-1',
      verdict: VerificationVerdict.ERROR,
      confidence: 0,
      formalization_similarity: 0,
      extraction_degradation: 1,
    };

    act(() => {
      result.current.updateProgress(errorResult);
    });

    expect(result.current.state.progress?.failed).toBe(1);
  });

  it('should not increment failed count for non-error verdicts', () => {
    const { result } = renderHook(() => useVerification());

    act(() => {
      result.current.startVerification(10);
    });

    const satResult: VerificationResult = {
      chunk_id: 'chunk-1',
      verdict: VerificationVerdict.SAT,
      confidence: 0.95,
      formalization_similarity: 0.92,
      extraction_degradation: 0.05,
    };

    act(() => {
      result.current.updateProgress(satResult);
    });

    expect(result.current.state.progress?.failed).toBe(0);
  });

  it('should set inProgress to false when all chunks are completed', () => {
    const { result } = renderHook(() => useVerification());

    act(() => {
      result.current.startVerification(2);
    });

    const result1: VerificationResult = {
      chunk_id: 'chunk-1',
      verdict: VerificationVerdict.SAT,
      confidence: 0.95,
      formalization_similarity: 0.92,
      extraction_degradation: 0.05,
    };

    const result2: VerificationResult = {
      chunk_id: 'chunk-2',
      verdict: VerificationVerdict.SAT,
      confidence: 0.93,
      formalization_similarity: 0.9,
      extraction_degradation: 0.07,
    };

    act(() => {
      result.current.updateProgress(result1);
    });

    expect(result.current.state.inProgress).toBe(true);

    act(() => {
      result.current.updateProgress(result2);
    });

    expect(result.current.state.inProgress).toBe(false);
    expect(result.current.state.progress?.completed).toBe(2);
    expect(result.current.state.progress?.percentage).toBe(100);
  });

  it('should calculate percentage correctly', () => {
    const { result } = renderHook(() => useVerification());

    act(() => {
      result.current.startVerification(100);
    });

    const verificationResult: VerificationResult = {
      chunk_id: 'chunk-1',
      verdict: VerificationVerdict.SAT,
      confidence: 0.95,
      formalization_similarity: 0.92,
      extraction_degradation: 0.05,
    };

    for (let i = 0; i < 50; i += 1) {
      act(() => {
        result.current.updateProgress({
          ...verificationResult,
          chunk_id: `chunk-${i}`,
        });
      });
    }

    expect(result.current.state.progress?.percentage).toBe(50);
  });

  it('should set error and stop progress', () => {
    const { result } = renderHook(() => useVerification());

    act(() => {
      result.current.startVerification(10);
    });

    act(() => {
      result.current.setError('Network error occurred');
    });

    expect(result.current.state.error).toBe('Network error occurred');
    expect(result.current.state.inProgress).toBe(false);
  });

  it('should reset state correctly', () => {
    const { result } = renderHook(() => useVerification());

    act(() => {
      result.current.toggleVerification(true);
      result.current.startVerification(10);
      result.current.setError('Some error');
    });

    act(() => {
      result.current.reset();
    });

    expect(result.current.state.inProgress).toBe(false);
    expect(result.current.state.progress).toBeNull();
    expect(result.current.state.error).toBeNull();
    // enabled state should not be reset
    expect(result.current.state.enabled).toBe(true);
  });

  it('should not update progress if progress is null', () => {
    const { result } = renderHook(() => useVerification());

    const verificationResult: VerificationResult = {
      chunk_id: 'chunk-1',
      verdict: VerificationVerdict.SAT,
      confidence: 0.95,
      formalization_similarity: 0.92,
      extraction_degradation: 0.05,
    };

    act(() => {
      result.current.updateProgress(verificationResult);
    });

    expect(result.current.state.progress).toBeNull();
  });

  it('should accumulate results in correct order', () => {
    const { result } = renderHook(() => useVerification());

    act(() => {
      result.current.startVerification(3);
    });

    const results: VerificationResult[] = [
      {
        chunk_id: 'chunk-1',
        verdict: VerificationVerdict.SAT,
        confidence: 0.95,
        formalization_similarity: 0.92,
        extraction_degradation: 0.05,
      },
      {
        chunk_id: 'chunk-2',
        verdict: VerificationVerdict.UNSAT,
        confidence: 0.88,
        formalization_similarity: 0.85,
        extraction_degradation: 0.12,
      },
      {
        chunk_id: 'chunk-3',
        verdict: VerificationVerdict.UNKNOWN,
        confidence: 0.7,
        formalization_similarity: 0.75,
        extraction_degradation: 0.2,
      },
    ];

    results.forEach((res) => {
      act(() => {
        result.current.updateProgress(res);
      });
    });

    expect(result.current.state.progress?.results).toEqual(results);
    expect(result.current.state.progress?.results[0].chunk_id).toBe('chunk-1');
    expect(result.current.state.progress?.results[2].chunk_id).toBe('chunk-3');
  });
});

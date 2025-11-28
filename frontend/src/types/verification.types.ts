// ----------------------------------------------------------------------

// Verification verdict enum
export enum VerificationVerdict {
  SAT = 'sat',
  UNSAT = 'unsat',
  UNKNOWN = 'unknown',
  ERROR = 'error',
}

// Failure mode enum
export enum FailureMode {
  TIMEOUT = 'timeout',
  RESOURCE_LIMIT = 'resource_limit',
  PARSE_ERROR = 'parse_error',
  SOLVER_ERROR = 'solver_error',
  NETWORK_ERROR = 'network_error',
  UNKNOWN_ERROR = 'unknown',
}

// Verification result interface
export interface VerificationResult {
  chunk_id: string;
  verdict: VerificationVerdict;
  confidence: number;
  formalization_similarity: number;
  extraction_degradation: number;
  failure_mode?: FailureMode;
  formal_text?: string;
  smt_lib_code?: string;
  model?: Record<string, unknown>;
  metrics?: {
    formalization_attempts: number;
    extraction_attempts: number;
    total_execution_time: number;
  };
}

// Verification progress interface
export interface VerificationProgress {
  total: number;
  completed: number;
  failed: number;
  percentage: number;
  results: VerificationResult[];
}

// Verification state interface
export interface VerificationState {
  enabled: boolean;
  inProgress: boolean;
  progress: VerificationProgress | null;
  error: string | null;
}

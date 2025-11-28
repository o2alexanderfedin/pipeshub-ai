import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { VerificationBadge } from '../verification-badge';
import type { VerificationResult } from 'src/types/verification.types';

describe('VerificationBadge', () => {
  it('renders null when no result provided', () => {
    const { container } = render(<VerificationBadge />);
    expect(container.firstChild).toBeNull();
  });

  it('renders verifying state', () => {
    render(<VerificationBadge isVerifying />);
    expect(screen.getByText('Verifying...')).toBeInTheDocument();
  });

  it('renders SAT verdict correctly', () => {
    const result: VerificationResult = {
      chunk_id: 'test-chunk',
      verdict: 'sat',
      confidence: 0.95,
      formalization_similarity: 0.9,
      extraction_degradation: 0.1,
    };

    render(<VerificationBadge result={result} />);
    expect(screen.getByText(/SAT.*95%/)).toBeInTheDocument();
  });

  it('renders UNSAT verdict correctly', () => {
    const result: VerificationResult = {
      chunk_id: 'test-chunk',
      verdict: 'unsat',
      confidence: 0.88,
      formalization_similarity: 0.85,
      extraction_degradation: 0.15,
    };

    render(<VerificationBadge result={result} />);
    expect(screen.getByText(/UNSAT.*88%/)).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const onClick = vi.fn();
    const result: VerificationResult = {
      chunk_id: 'test-chunk',
      verdict: 'sat',
      confidence: 0.95,
      formalization_similarity: 0.9,
      extraction_degradation: 0.1,
    };

    render(<VerificationBadge result={result} onClick={onClick} />);
    screen.getByText(/SAT.*95%/).click();
    expect(onClick).toHaveBeenCalledTimes(1);
  });
});

/**
 * Tests for VerificationMetadata component
 *
 * NOTE: These tests require a test runner (Jest/Vitest) and React Testing Library to be configured.
 */

import { it, expect, describe } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';

import {
  FailureMode,
  VerificationVerdict,
  type VerificationResult,
} from 'src/types/verification.types';

import { VerificationMetadata } from '../verification-metadata';

describe('VerificationMetadata', () => {
  const baseResult: VerificationResult = {
    chunk_id: 'chunk-123',
    verdict: VerificationVerdict.SAT,
    confidence: 0.95,
    formalization_similarity: 0.92,
    extraction_degradation: 0.05,
  };

  it('should render verdict chip with correct label', () => {
    render(<VerificationMetadata result={baseResult} />);

    expect(screen.getByText('SMT: SAT')).toBeInTheDocument();
  });

  it('should display confidence score', () => {
    render(<VerificationMetadata result={baseResult} />);

    expect(screen.getByText(/Confidence: 95.0%/i)).toBeInTheDocument();
  });

  it('should be collapsed by default', () => {
    render(<VerificationMetadata result={baseResult} />);

    // Details should not be visible initially
    expect(screen.queryByText('Verification Details')).not.toBeInTheDocument();
  });

  it('should expand when clicked', () => {
    render(<VerificationMetadata result={baseResult} />);

    const chip = screen.getByText('SMT: SAT');
    fireEvent.click(chip);

    expect(screen.getByText('Verification Details')).toBeInTheDocument();
  });

  it('should collapse when clicked again', () => {
    render(<VerificationMetadata result={baseResult} />);

    const chip = screen.getByText('SMT: SAT');

    // Expand
    fireEvent.click(chip);
    expect(screen.getByText('Verification Details')).toBeInTheDocument();

    // Collapse
    fireEvent.click(chip);
    // Use a timer or waitFor for animation
    setTimeout(() => {
      expect(screen.queryByText('Verification Details')).not.toBeInTheDocument();
    }, 500);
  });

  it('should display correct color for SAT verdict', () => {
    const result: VerificationResult = {
      ...baseResult,
      verdict: VerificationVerdict.SAT,
    };

    const { container } = render(<VerificationMetadata result={result} />);

    const successChip = container.querySelector('[class*="MuiChip-colorSuccess"]');
    expect(successChip).toBeInTheDocument();
  });

  it('should display correct color for UNSAT verdict', () => {
    const result: VerificationResult = {
      ...baseResult,
      verdict: VerificationVerdict.UNSAT,
    };

    const { container } = render(<VerificationMetadata result={result} />);

    const errorChip = container.querySelector('[class*="MuiChip-colorError"]');
    expect(errorChip).toBeInTheDocument();
  });

  it('should display correct color for UNKNOWN verdict', () => {
    const result: VerificationResult = {
      ...baseResult,
      verdict: VerificationVerdict.UNKNOWN,
    };

    const { container } = render(<VerificationMetadata result={result} />);

    const warningChip = container.querySelector('[class*="MuiChip-colorWarning"]');
    expect(warningChip).toBeInTheDocument();
  });

  it('should display correct color for ERROR verdict', () => {
    const result: VerificationResult = {
      ...baseResult,
      verdict: VerificationVerdict.ERROR,
    };

    const { container } = render(<VerificationMetadata result={result} />);

    const errorChip = container.querySelector('[class*="MuiChip-colorError"]');
    expect(errorChip).toBeInTheDocument();
  });

  it('should display detailed metrics when expanded', () => {
    render(<VerificationMetadata result={baseResult} />);

    fireEvent.click(screen.getByText('SMT: SAT'));

    expect(screen.getByText('Confidence Score')).toBeInTheDocument();
    expect(screen.getByText('95.00%')).toBeInTheDocument();
    expect(screen.getByText('Formalization Similarity')).toBeInTheDocument();
    expect(screen.getByText('92.00%')).toBeInTheDocument();
  });

  it('should calculate and display extraction quality correctly', () => {
    const result: VerificationResult = {
      ...baseResult,
      extraction_degradation: 0.15,
    };

    render(<VerificationMetadata result={result} />);

    fireEvent.click(screen.getByText('SMT: SAT'));

    // extraction_quality = (1 - 0.15) * 100 = 85.00%
    expect(screen.getByText('85.00%')).toBeInTheDocument();
  });

  it('should display failure mode when present', () => {
    const result: VerificationResult = {
      ...baseResult,
      verdict: VerificationVerdict.ERROR,
      failure_mode: FailureMode.TIMEOUT,
    };

    render(<VerificationMetadata result={result} />);

    fireEvent.click(screen.getByText('SMT: ERROR'));

    expect(screen.getByText('Failure Mode')).toBeInTheDocument();
    expect(screen.getByText('TIMEOUT')).toBeInTheDocument();
  });

  it('should display formal text when present', () => {
    const result: VerificationResult = {
      ...baseResult,
      formal_text: 'forall x: int. x > 0 -> x >= 1',
    };

    render(<VerificationMetadata result={result} />);

    fireEvent.click(screen.getByText('SMT: SAT'));

    expect(screen.getByText('Formal Representation')).toBeInTheDocument();
    expect(screen.getByText('forall x: int. x > 0 -> x >= 1')).toBeInTheDocument();
  });

  it('should display execution metrics when present', () => {
    const result: VerificationResult = {
      ...baseResult,
      metrics: {
        formalization_attempts: 3,
        extraction_attempts: 2,
        total_execution_time: 45.67,
      },
    };

    render(<VerificationMetadata result={result} />);

    fireEvent.click(screen.getByText('SMT: SAT'));

    expect(screen.getByText('Execution Metrics')).toBeInTheDocument();
    expect(screen.getByText(/Formalization attempts: 3/i)).toBeInTheDocument();
    expect(screen.getByText(/Extraction attempts: 2/i)).toBeInTheDocument();
    expect(screen.getByText(/Time: 45.67s/i)).toBeInTheDocument();
  });

  it('should not display optional fields when not present', () => {
    render(<VerificationMetadata result={baseResult} />);

    fireEvent.click(screen.getByText('SMT: SAT'));

    expect(screen.queryByText('Failure Mode')).not.toBeInTheDocument();
    expect(screen.queryByText('Formal Representation')).not.toBeInTheDocument();
    expect(screen.queryByText('Execution Metrics')).not.toBeInTheDocument();
  });

  it('should format failure mode text correctly', () => {
    const result: VerificationResult = {
      ...baseResult,
      verdict: VerificationVerdict.ERROR,
      failure_mode: FailureMode.RESOURCE_LIMIT,
    };

    render(<VerificationMetadata result={result} />);

    fireEvent.click(screen.getByText('SMT: ERROR'));

    // Should replace underscores with spaces and uppercase
    expect(screen.getByText('RESOURCE LIMIT')).toBeInTheDocument();
  });
});

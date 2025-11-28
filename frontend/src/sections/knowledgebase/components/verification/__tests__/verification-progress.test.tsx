/**
 * Tests for VerificationProgress component
 *
 * NOTE: These tests require a test runner (Jest/Vitest) and React Testing Library to be configured.
 */

import type { VerificationProgress as VerificationProgressType } from 'src/types/verification.types';

import { it, expect, describe } from 'vitest';
import { render, screen } from '@testing-library/react';

import { VerificationProgress } from '../verification-progress';

describe('VerificationProgress', () => {
  it('should render progress bar with correct percentage', () => {
    const progress: VerificationProgressType = {
      total: 100,
      completed: 50,
      failed: 5,
      percentage: 50,
      results: [],
    };

    render(<VerificationProgress progress={progress} />);

    expect(screen.getByText('50%')).toBeInTheDocument();
  });

  it('should display total chunks being verified', () => {
    const progress: VerificationProgressType = {
      total: 25,
      completed: 10,
      failed: 2,
      percentage: 40,
      results: [],
    };

    render(<VerificationProgress progress={progress} />);

    expect(screen.getByText(/Verifying 25 chunks/i)).toBeInTheDocument();
  });

  it('should show correct number of verified chunks', () => {
    const progress: VerificationProgressType = {
      total: 100,
      completed: 60,
      failed: 10,
      percentage: 60,
      results: [],
    };

    render(<VerificationProgress progress={progress} />);

    // succeeded = completed - failed = 60 - 10 = 50
    expect(screen.getByText('50 verified')).toBeInTheDocument();
  });

  it('should show correct number of failed chunks', () => {
    const progress: VerificationProgressType = {
      total: 100,
      completed: 60,
      failed: 15,
      percentage: 60,
      results: [],
    };

    render(<VerificationProgress progress={progress} />);

    expect(screen.getByText('15 failed')).toBeInTheDocument();
  });

  it('should show correct number of pending chunks', () => {
    const progress: VerificationProgressType = {
      total: 100,
      completed: 75,
      failed: 10,
      percentage: 75,
      results: [],
    };

    render(<VerificationProgress progress={progress} />);

    // pending = total - completed = 100 - 75 = 25
    expect(screen.getByText('25 pending')).toBeInTheDocument();
  });

  it('should display in-progress message when pending chunks exist', () => {
    const progress: VerificationProgressType = {
      total: 100,
      completed: 50,
      failed: 5,
      percentage: 50,
      results: [],
    };

    render(<VerificationProgress progress={progress} />);

    expect(
      screen.getByText(/Verification in progress... This may take 1-2 minutes/i)
    ).toBeInTheDocument();
  });

  it('should not display in-progress message when all chunks are completed', () => {
    const progress: VerificationProgressType = {
      total: 100,
      completed: 100,
      failed: 10,
      percentage: 100,
      results: [],
    };

    render(<VerificationProgress progress={progress} />);

    expect(screen.queryByText(/Verification in progress/i)).not.toBeInTheDocument();
  });

  it('should render chips with correct colors', () => {
    const progress: VerificationProgressType = {
      total: 100,
      completed: 50,
      failed: 5,
      percentage: 50,
      results: [],
    };

    const { container } = render(<VerificationProgress progress={progress} />);

    // Check for success chip (verified)
    const successChip = container.querySelector('[class*="MuiChip-colorSuccess"]');
    expect(successChip).toBeInTheDocument();

    // Check for error chip (failed)
    const errorChip = container.querySelector('[class*="MuiChip-colorError"]');
    expect(errorChip).toBeInTheDocument();
  });

  it('should calculate percentage correctly', () => {
    const progress: VerificationProgressType = {
      total: 200,
      completed: 100,
      failed: 20,
      percentage: 50,
      results: [],
    };

    render(<VerificationProgress progress={progress} />);

    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveAttribute('aria-valuenow', '50');
  });

  it('should handle zero completed chunks', () => {
    const progress: VerificationProgressType = {
      total: 100,
      completed: 0,
      failed: 0,
      percentage: 0,
      results: [],
    };

    render(<VerificationProgress progress={progress} />);

    expect(screen.getByText('0%')).toBeInTheDocument();
    expect(screen.getByText('0 verified')).toBeInTheDocument();
    expect(screen.getByText('100 pending')).toBeInTheDocument();
  });
});

/**
 * Tests for HupyyControls component
 *
 * NOTE: These tests require a test runner (Jest/Vitest) and React Testing Library to be configured.
 * Run: yarn add -D @testing-library/react @testing-library/jest-dom @testing-library/user-event vitest
 *
 * To run tests: yarn test
 */

import { it, vi, expect, describe } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';

import { HupyyControls } from '../hupyy-controls';

describe('HupyyControls', () => {
  it('should render checkbox with label', () => {
    const mockToggle = vi.fn();
    render(<HupyyControls enabled={false} onToggle={mockToggle} />);

    expect(screen.getByLabelText('Enable SMT Verification')).toBeInTheDocument();
  });

  it('should display checkbox as checked when enabled is true', () => {
    const mockToggle = vi.fn();
    render(<HupyyControls enabled onToggle={mockToggle} />);

    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).toBeChecked();
  });

  it('should display checkbox as unchecked when enabled is false', () => {
    const mockToggle = vi.fn();
    render(<HupyyControls enabled={false} onToggle={mockToggle} />);

    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).not.toBeChecked();
  });

  it('should call onToggle with true when checkbox is clicked while unchecked', () => {
    const mockToggle = vi.fn();
    render(<HupyyControls enabled={false} onToggle={mockToggle} />);

    const checkbox = screen.getByRole('checkbox');
    fireEvent.click(checkbox);

    expect(mockToggle).toHaveBeenCalledWith(true);
  });

  it('should call onToggle with false when checkbox is clicked while checked', () => {
    const mockToggle = vi.fn();
    render(<HupyyControls enabled onToggle={mockToggle} />);

    const checkbox = screen.getByRole('checkbox');
    fireEvent.click(checkbox);

    expect(mockToggle).toHaveBeenCalledWith(false);
  });

  it('should disable checkbox when disabled prop is true', () => {
    const mockToggle = vi.fn();
    render(<HupyyControls enabled={false} onToggle={mockToggle} disabled />);

    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).toBeDisabled();
  });

  it('should render info icon with tooltip', () => {
    const mockToggle = vi.fn();
    render(<HupyyControls enabled={false} onToggle={mockToggle} />);

    // Tooltip should be accessible via title attribute
    expect(
      screen.getByTitle(/SMT verification uses formal logic to verify search results/i)
    ).toBeInTheDocument();
  });

  it('should have proper accessibility attributes', () => {
    const mockToggle = vi.fn();
    render(<HupyyControls enabled={false} onToggle={mockToggle} />);

    const checkbox = screen.getByRole('checkbox', {
      name: /Enable SMT Verification/i,
    });
    expect(checkbox).toBeInTheDocument();
  });
});

import type { FC } from 'react';
import type { VerificationResult, VerificationVerdict } from 'src/types/verification.types';

import { Chip, alpha, Tooltip, CircularProgress } from '@mui/material';
import { Help, Cancel, CheckCircle, Error as ErrorIcon } from '@mui/icons-material';

// ----------------------------------------------------------------------

interface VerificationBadgeProps {
  result?: VerificationResult;
  isVerifying?: boolean;
  onClick?: () => void;
}

const VERDICT_CONFIG = {
  sat: {
    label: 'SAT',
    icon: CheckCircle,
    color: 'success' as const,
    bgColor: '#4caf50',
    tooltip: 'Satisfiable - specification can be fulfilled',
  },
  unsat: {
    label: 'UNSAT',
    icon: Cancel,
    color: 'error' as const,
    bgColor: '#f44336',
    tooltip: 'Unsatisfiable - specification cannot be fulfilled',
  },
  unknown: {
    label: 'UNKNOWN',
    icon: Help,
    color: 'warning' as const,
    bgColor: '#ff9800',
    tooltip: 'Unknown - could not determine satisfiability',
  },
  error: {
    label: 'ERROR',
    icon: ErrorIcon,
    color: 'error' as const,
    bgColor: '#d32f2f',
    tooltip: 'Verification failed with error',
  },
};

export const VerificationBadge: FC<VerificationBadgeProps> = ({
  result,
  isVerifying = false,
  onClick,
}) => {
  if (isVerifying) {
    return (
      <Tooltip title="Verification in progress...">
        <Chip
          size="small"
          icon={<CircularProgress size={12} />}
          label="Verifying..."
          sx={{
            cursor: 'default',
            backgroundColor: (theme) => alpha(theme.palette.info.main, 0.1),
            color: 'info.main',
            fontWeight: 600,
            fontSize: '0.75rem',
            height: 24,
          }}
        />
      </Tooltip>
    );
  }

  if (!result) {
    return null;
  }

  const config = VERDICT_CONFIG[result.verdict as VerificationVerdict];
  if (!config) {
    return null;
  }

  const Icon = config.icon;

  return (
    <Tooltip title={config.tooltip}>
      <Chip
        size="small"
        icon={<Icon sx={{ fontSize: 14 }} />}
        label={`${config.label} (${Math.round(result.confidence * 100)}%)`}
        onClick={onClick}
        sx={{
          cursor: onClick ? 'pointer' : 'default',
          backgroundColor: (theme) => alpha(config.bgColor, 0.1),
          color: config.bgColor,
          fontWeight: 600,
          fontSize: '0.75rem',
          height: 24,
          '&:hover': onClick
            ? {
                backgroundColor: (theme) => alpha(config.bgColor, 0.2),
              }
            : {},
          '& .MuiChip-icon': {
            color: config.bgColor,
          },
        }}
      />
    </Tooltip>
  );
};

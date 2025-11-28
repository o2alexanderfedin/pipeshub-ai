import type { FC } from 'react';
import type { VerificationProgress as VerificationProgressType } from 'src/types/verification.types';

import { Box, Chip, Paper, Typography, LinearProgress, CircularProgress } from '@mui/material';

import { Iconify } from 'src/components/iconify';

// ----------------------------------------------------------------------

interface VerificationProgressProps {
  progress: VerificationProgressType;
}

export const VerificationProgress: FC<VerificationProgressProps> = ({ progress }) => {
  const { total, completed, failed, percentage } = progress;
  const pending = total - completed;
  const succeeded = completed - failed;

  return (
    <Paper sx={{ p: 2, my: 2, bgcolor: 'background.default' }}>
      <Box sx={{ mb: 2 }}>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Verifying {total} chunks with SMT solvers...
        </Typography>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          <Box sx={{ flexGrow: 1 }}>
            <LinearProgress
              variant="determinate"
              value={percentage}
              sx={{ height: 8, borderRadius: 1 }}
            />
          </Box>
          <Typography variant="body2" fontWeight="bold">
            {percentage}%
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Chip
            icon={<Iconify icon="eva:checkmark-circle-2-fill" />}
            label={`${succeeded} verified`}
            size="small"
            color="success"
            variant="outlined"
          />
          <Chip
            icon={<Iconify icon="eva:close-circle-fill" />}
            label={`${failed} failed`}
            size="small"
            color="error"
            variant="outlined"
          />
          <Chip
            icon={
              pending > 0 ? <CircularProgress size={14} /> : <Iconify icon="eva:clock-outline" />
            }
            label={`${pending} pending`}
            size="small"
            variant="outlined"
          />
        </Box>
      </Box>

      {pending > 0 && (
        <Typography variant="caption" color="text.secondary">
          Verification in progress... This may take 1-2 minutes.
        </Typography>
      )}
    </Paper>
  );
};

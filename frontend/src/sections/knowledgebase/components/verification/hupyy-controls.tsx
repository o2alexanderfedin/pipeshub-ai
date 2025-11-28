import type { FC } from 'react';

import { Box, Tooltip, Checkbox, FormControlLabel } from '@mui/material';

import { Iconify } from 'src/components/iconify';

// ----------------------------------------------------------------------

interface HupyyControlsProps {
  enabled: boolean;
  onToggle: (enabled: boolean) => void;
  disabled?: boolean;
}

export const HupyyControls: FC<HupyyControlsProps> = ({ enabled, onToggle, disabled = false }) => (
  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
    <FormControlLabel
      control={
        <Checkbox
          checked={enabled}
          onChange={(e) => onToggle(e.target.checked)}
          disabled={disabled}
          color="primary"
        />
      }
      label="Enable SMT Verification"
    />
    <Tooltip title="SMT verification uses formal logic to verify search results. This process takes 1-2 minutes per query but significantly improves accuracy.">
      <Box sx={{ display: 'flex', alignItems: 'center', cursor: 'help' }}>
        <Iconify icon="eva:info-outline" width={20} />
      </Box>
    </Tooltip>
  </Box>
);

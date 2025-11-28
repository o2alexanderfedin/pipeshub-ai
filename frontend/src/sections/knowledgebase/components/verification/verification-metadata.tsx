import type { FC } from 'react';

import { useState } from 'react';

import { Box, Chip, Grid, Paper, Divider, Collapse, IconButton, Typography } from '@mui/material';

import { Iconify } from 'src/components/iconify';

import { VerificationVerdict, type VerificationResult } from 'src/types/verification.types';

// ----------------------------------------------------------------------

interface VerificationMetadataProps {
  result: VerificationResult;
}

export const VerificationMetadata: FC<VerificationMetadataProps> = ({ result }) => {
  const [expanded, setExpanded] = useState(false);

  const getVerdictIcon = (verdict: VerificationVerdict) => {
    switch (verdict) {
      case VerificationVerdict.SAT:
        return <Iconify icon="eva:checkmark-circle-2-fill" />;
      case VerificationVerdict.UNSAT:
        return <Iconify icon="eva:close-circle-fill" />;
      case VerificationVerdict.UNKNOWN:
        return <Iconify icon="eva:question-mark-circle-fill" />;
      case VerificationVerdict.ERROR:
        return <Iconify icon="eva:alert-circle-fill" />;
      default:
        return undefined;
    }
  };

  const getVerdictColor = (
    verdict: VerificationVerdict
  ): 'success' | 'error' | 'warning' | 'default' => {
    switch (verdict) {
      case VerificationVerdict.SAT:
        return 'success';
      case VerificationVerdict.UNSAT:
        return 'error';
      case VerificationVerdict.UNKNOWN:
        return 'warning';
      case VerificationVerdict.ERROR:
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Box>
      <Box
        sx={{ display: 'flex', alignItems: 'center', gap: 1, cursor: 'pointer' }}
        onClick={() => setExpanded(!expanded)}
      >
        <Chip
          icon={getVerdictIcon(result.verdict)}
          label={`SMT: ${result.verdict.toUpperCase()}`}
          size="small"
          color={getVerdictColor(result.verdict)}
          variant="outlined"
        />
        <Typography variant="caption" color="text.secondary">
          Confidence: {(result.confidence * 100).toFixed(1)}%
        </Typography>
        <IconButton
          size="small"
          sx={{
            transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
            transition: 'transform 0.3s',
          }}
        >
          <Iconify icon="eva:arrow-ios-downward-fill" width={16} />
        </IconButton>
      </Box>

      <Collapse in={expanded}>
        <Paper sx={{ p: 2, mt: 1, bgcolor: 'background.default' }}>
          <Typography variant="subtitle2" gutterBottom>
            Verification Details
          </Typography>
          <Divider sx={{ my: 1 }} />

          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Typography variant="caption" color="text.secondary">
                Verdict
              </Typography>
              <Typography variant="body2" fontWeight="bold">
                {result.verdict.toUpperCase()}
              </Typography>
            </Grid>

            <Grid item xs={6}>
              <Typography variant="caption" color="text.secondary">
                Confidence Score
              </Typography>
              <Typography variant="body2" fontWeight="bold">
                {(result.confidence * 100).toFixed(2)}%
              </Typography>
            </Grid>

            <Grid item xs={6}>
              <Typography variant="caption" color="text.secondary">
                Formalization Similarity
              </Typography>
              <Typography variant="body2" fontWeight="bold">
                {(result.formalization_similarity * 100).toFixed(2)}%
              </Typography>
            </Grid>

            <Grid item xs={6}>
              <Typography variant="caption" color="text.secondary">
                Extraction Quality
              </Typography>
              <Typography variant="body2" fontWeight="bold">
                {((1 - result.extraction_degradation) * 100).toFixed(2)}%
              </Typography>
            </Grid>

            {result.failure_mode && (
              <Grid item xs={12}>
                <Typography variant="caption" color="text.secondary">
                  Failure Mode
                </Typography>
                <Typography variant="body2" color="error">
                  {result.failure_mode.replace(/_/g, ' ').toUpperCase()}
                </Typography>
              </Grid>
            )}

            {result.formal_text && (
              <Grid item xs={12}>
                <Typography variant="caption" color="text.secondary">
                  Formal Representation
                </Typography>
                <Paper
                  sx={{
                    p: 1,
                    bgcolor: 'background.paper',
                    fontFamily: 'monospace',
                    fontSize: '0.75rem',
                  }}
                >
                  {result.formal_text}
                </Paper>
              </Grid>
            )}

            {result.metrics && (
              <Grid item xs={12}>
                <Typography variant="caption" color="text.secondary">
                  Execution Metrics
                </Typography>
                <Typography variant="body2" fontSize="0.75rem">
                  Formalization attempts: {result.metrics.formalization_attempts} | Extraction
                  attempts: {result.metrics.extraction_attempts} | Time:{' '}
                  {result.metrics.total_execution_time.toFixed(2)}s
                </Typography>
              </Grid>
            )}
          </Grid>
        </Paper>
      </Collapse>
    </Box>
  );
};

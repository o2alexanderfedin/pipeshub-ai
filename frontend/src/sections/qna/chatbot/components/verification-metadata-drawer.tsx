import type { FC } from 'react';
import type { VerificationResult, VerificationVerdict } from 'src/types/verification.types';

import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

import { Help, Close, Speed, Memory, Cancel, CheckCircle } from '@mui/icons-material';
import {
  Box,
  Chip,
  Stack,
  Paper,
  Alert,
  Drawer,
  Typography,
  IconButton,
} from '@mui/material';

// ----------------------------------------------------------------------

interface VerificationMetadataDrawerProps {
  open: boolean;
  onClose: () => void;
  result: VerificationResult | null;
}

const VERDICT_INFO = {
  sat: {
    label: 'Satisfiable (SAT)',
    icon: CheckCircle,
    color: '#4caf50',
    description: 'The specification can be fulfilled. A model has been found.',
  },
  unsat: {
    label: 'Unsatisfiable (UNSAT)',
    icon: Cancel,
    color: '#f44336',
    description: 'The specification cannot be fulfilled. A proof of contradiction exists.',
  },
  unknown: {
    label: 'Unknown',
    icon: Help,
    color: '#ff9800',
    description: 'Could not determine satisfiability within resource limits.',
  },
  error: {
    label: 'Error',
    icon: Cancel,
    color: '#d32f2f',
    description: 'Verification failed with an error.',
  },
};

export const VerificationMetadataDrawer: FC<VerificationMetadataDrawerProps> = ({
  open,
  onClose,
  result,
}) => {
  if (!result) {
    return null;
  }

  const verdictInfo = VERDICT_INFO[result.verdict as VerificationVerdict];
  const VerdictIcon = verdictInfo?.icon || Help;

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      PaperProps={{
        sx: {
          width: { xs: '100%', sm: 600 },
          maxWidth: '100%',
        },
      }}
    >
      <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        {/* Header */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            p: 2,
            borderBottom: 1,
            borderColor: 'divider',
          }}
        >
          <Typography variant="h6">Verification Details</Typography>
          <IconButton onClick={onClose} size="small">
            <Close />
          </IconButton>
        </Box>

        {/* Content */}
        <Box sx={{ flex: 1, overflow: 'auto', p: 3 }}>
          <Stack spacing={3}>
            {/* Verdict */}
            <Paper elevation={0} sx={{ p: 2, bgcolor: 'background.neutral' }}>
              <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1 }}>
                <VerdictIcon sx={{ color: verdictInfo?.color, fontSize: 24 }} />
                <Typography variant="h6" sx={{ color: verdictInfo?.color }}>
                  {verdictInfo?.label}
                </Typography>
              </Stack>
              <Typography variant="body2" color="text.secondary">
                {verdictInfo?.description}
              </Typography>
            </Paper>

            {/* Metrics */}
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Metrics
              </Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap">
                <Chip
                  icon={<Speed />}
                  label={`Confidence: ${Math.round(result.confidence * 100)}%`}
                  size="small"
                />
                <Chip
                  icon={<Memory />}
                  label={`Similarity: ${Math.round(result.formalization_similarity * 100)}%`}
                  size="small"
                />
                <Chip
                  label={`Degradation: ${Math.round(result.extraction_degradation * 100)}%`}
                  size="small"
                />
              </Stack>
              {result.metrics && (
                <Box sx={{ mt: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    Total time: {(result.metrics.total_execution_time / 1000).toFixed(2)}s •
                    Attempts: {result.metrics.formalization_attempts}/
                    {result.metrics.extraction_attempts}
                  </Typography>
                </Box>
              )}
            </Box>

            {/* Formal Text */}
            {result.formal_text && (
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Formal Specification
                </Typography>
                <Paper
                  elevation={0}
                  sx={{ p: 2, bgcolor: 'background.neutral', fontFamily: 'monospace' }}
                >
                  <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                    {result.formal_text}
                  </Typography>
                </Paper>
              </Box>
            )}

            {/* SMT-LIB Code */}
            {result.smt_lib_code && (
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  SMT-LIB2 Code
                </Typography>
                <Paper elevation={0} sx={{ overflow: 'hidden' }}>
                  <SyntaxHighlighter
                    language="lisp"
                    style={vscDarkPlus}
                    customStyle={{
                      margin: 0,
                      padding: '16px',
                      fontSize: '0.875rem',
                      maxHeight: '300px',
                      overflow: 'auto',
                    }}
                  >
                    {result.smt_lib_code}
                  </SyntaxHighlighter>
                </Paper>
              </Box>
            )}

            {/* Model (for SAT) */}
            {result.verdict === 'sat' && result.model && (
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Model (Variable Assignments)
                </Typography>
                <Paper
                  elevation={0}
                  sx={{ p: 2, bgcolor: 'background.neutral', fontFamily: 'monospace' }}
                >
                  <pre style={{ margin: 0, overflow: 'auto' }}>
                    {JSON.stringify(result.model, null, 2)}
                  </pre>
                </Paper>
              </Box>
            )}

            {/* Failure Mode */}
            {result.failure_mode && (
              <Alert severity="warning">
                <Typography variant="subtitle2" gutterBottom>
                  Failure Mode
                </Typography>
                <Typography variant="body2">{result.failure_mode}</Typography>
              </Alert>
            )}

            {/* Chunk ID */}
            <Box>
              <Typography variant="caption" color="text.secondary">
                Chunk ID: {result.chunk_id}
              </Typography>
            </Box>
          </Stack>
        </Box>
      </Box>
    </Drawer>
  );
};

import React from 'react';
import { Helmet } from 'react-helmet-async';
import { useParams } from 'react-router-dom';

import { Box } from '@mui/material';

import Sidebar from 'src/sections/accountdetails/Sidebar';
import ConnectorManager from 'src/sections/accountdetails/connectors/components/connector-manager';

// ----------------------------------------------------------------------

const metadata = { title: `Connector Management` };

// Generic connector management page
export default function Page() {
  const { connectorName } = useParams<{ connectorName: string }>();
    
  return (
    <>
      <Helmet>
        <title> {metadata.title} - {connectorName}</title>
      </Helmet>
      <Box sx={{ display: 'flex', flexGrow: 1, overflow: 'hidden', zIndex: 0 }}>
        <Sidebar />
        <ConnectorManager showStats={Boolean(true)} />
      </Box>
    </>
  );
}

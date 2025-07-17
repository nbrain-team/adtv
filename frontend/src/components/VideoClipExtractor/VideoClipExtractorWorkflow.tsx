import React from 'react';
import { Box } from '@radix-ui/themes';
import { VideoClipExtractor } from './VideoClipExtractor';

export const VideoClipExtractorWorkflow: React.FC = () => {
  return (
    <Box style={{ height: '100%', padding: '1rem' }}>
      <VideoClipExtractor />
    </Box>
  );
}; 
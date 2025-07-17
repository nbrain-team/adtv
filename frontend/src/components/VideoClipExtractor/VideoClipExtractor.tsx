import React, { useState, useRef } from 'react';
import {
  Box, Flex, Text, Heading, Button, Card, Progress,
  Select, Badge, Grid, IconButton, ScrollArea
} from '@radix-ui/themes';
import {
  UploadIcon, VideoIcon, ScissorsIcon, CheckCircledIcon,
  CrossCircledIcon, ReloadIcon, DownloadIcon, PlayIcon
} from '@radix-ui/react-icons';
import api from '../../api';

interface VideoClip {
  id: string;
  title: string;
  description: string;
  duration: number;
  startTime: number;
  endTime: number;
  platform: 'instagram' | 'youtube' | 'facebook';
  thumbnail?: string;
  status: 'processing' | 'ready' | 'failed';
  url?: string;
}

interface ProcessingJob {
  id: string;
  filename: string;
  status: 'uploading' | 'analyzing' | 'extracting' | 'complete' | 'failed';
  progress: number;
  clips: VideoClip[];
  error?: string;
}

export const VideoClipExtractor: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [processingJobs, setProcessingJobs] = useState<ProcessingJob[]>([]);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.type.startsWith('video/')) {
      setSelectedFile(file);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    const jobId = Date.now().toString();
    const newJob: ProcessingJob = {
      id: jobId,
      filename: selectedFile.name,
      status: 'uploading',
      progress: 0,
      clips: []
    };

    setProcessingJobs(prev => [...prev, newJob]);
    setActiveJobId(jobId);

    const formData = new FormData();
    formData.append('video', selectedFile);
    formData.append('platforms', JSON.stringify(['instagram', 'youtube', 'facebook']));

    try {
      // Upload video
      const uploadResponse = await api.post('/video-processor/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent: any) => {
          const progress = Math.round((progressEvent.loaded * 100) / (progressEvent.total || 1));
          updateJobProgress(jobId, progress, 'uploading');
        }
      });

      // Start processing
      updateJobStatus(jobId, 'analyzing');
      pollJobStatus(jobId, uploadResponse.data.jobId);

    } catch (error) {
      console.error('Upload failed:', error);
      updateJobStatus(jobId, 'failed', 'Upload failed');
    }
  };

  const updateJobProgress = (jobId: string, progress: number, status?: ProcessingJob['status']) => {
    setProcessingJobs(prev => prev.map(job => 
      job.id === jobId ? { ...job, progress, ...(status && { status }) } : job
    ));
  };

  const updateJobStatus = (jobId: string, status: ProcessingJob['status'], error?: string) => {
    setProcessingJobs(prev => prev.map(job => 
      job.id === jobId ? { ...job, status, ...(error && { error }) } : job
    ));
  };

  const pollJobStatus = async (localJobId: string, serverJobId: string) => {
    const checkStatus = async () => {
      try {
        const response = await api.get(`/video-processor/status/${serverJobId}`);
        const { status, progress, clips } = response.data;

        if (status === 'complete') {
          setProcessingJobs(prev => prev.map(job => 
            job.id === localJobId ? { ...job, status: 'complete', progress: 100, clips } : job
          ));
        } else if (status === 'failed') {
          updateJobStatus(localJobId, 'failed', response.data.error);
        } else {
          updateJobProgress(localJobId, progress, status);
          setTimeout(checkStatus, 2000); // Poll every 2 seconds
        }
      } catch (error) {
        console.error('Status check failed:', error);
        updateJobStatus(localJobId, 'failed', 'Failed to check status');
      }
    };

    checkStatus();
  };

  const downloadClip = async (clip: VideoClip) => {
    try {
      const response = await api.get(`/video-processor/download/${clip.id}`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${clip.title}_${clip.platform}.mp4`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  const activeJob = processingJobs.find(job => job.id === activeJobId);

  return (
    <Box style={{ height: '100%' }}>
      <Grid columns="1fr 2fr" gap="4" style={{ height: '100%' }}>
        
        {/* Left Panel - Upload & Jobs */}
        <Box style={{ borderRight: '1px solid var(--gray-4)', paddingRight: '1rem' }}>
          <Card mb="4">
            <Heading size="4" mb="3">Upload Video</Heading>
            
            <input
              ref={fileInputRef}
              type="file"
              accept="video/*"
              onChange={handleFileSelect}
              style={{ display: 'none' }}
            />
            
            {!selectedFile ? (
              <Box
                onClick={() => fileInputRef.current?.click()}
                style={{
                  border: '2px dashed var(--gray-6)',
                  borderRadius: '8px',
                  padding: '2rem',
                  textAlign: 'center',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => e.currentTarget.style.borderColor = 'var(--gray-8)'}
                onMouseLeave={(e) => e.currentTarget.style.borderColor = 'var(--gray-6)'}
              >
                <UploadIcon width="48" height="48" style={{ margin: '0 auto', color: 'var(--gray-9)' }} />
                <Text size="3" mt="3" style={{ display: 'block' }}>
                  Click to upload a video
                </Text>
                <Text size="2" color="gray" mt="1" style={{ display: 'block' }}>
                  MP4, MOV, AVI (max 500MB)
                </Text>
              </Box>
            ) : (
              <Box>
                <Flex align="center" gap="2" mb="3">
                  <VideoIcon />
                  <Text size="2" weight="medium">{selectedFile.name}</Text>
                </Flex>
                <Flex gap="2">
                  <Button onClick={handleUpload} disabled={!selectedFile}>
                    <ScissorsIcon />
                    Extract Clips
                  </Button>
                  <Button variant="soft" onClick={() => setSelectedFile(null)}>
                    Change Video
                  </Button>
                </Flex>
              </Box>
            )}
          </Card>

          {/* Processing Jobs List */}
          <Box>
            <Heading size="3" mb="3">Processing History</Heading>
            <ScrollArea style={{ height: '400px' }}>
              <Flex direction="column" gap="2">
                {processingJobs.map(job => (
                  <Card
                    key={job.id}
                    style={{
                      cursor: 'pointer',
                      border: activeJobId === job.id ? '2px solid var(--blue-9)' : '1px solid var(--gray-4)'
                    }}
                    onClick={() => setActiveJobId(job.id)}
                  >
                    <Flex justify="between" align="center">
                      <Box>
                        <Text size="2" weight="medium">{job.filename}</Text>
                        <Badge size="1" color={
                          job.status === 'complete' ? 'green' :
                          job.status === 'failed' ? 'red' :
                          'blue'
                        }>
                          {job.status}
                        </Badge>
                      </Box>
                      {job.status === 'complete' && (
                        <CheckCircledIcon color="green" />
                      )}
                      {job.status === 'failed' && (
                        <CrossCircledIcon color="red" />
                      )}
                      {['uploading', 'analyzing', 'extracting'].includes(job.status) && (
                        <ReloadIcon className="spinning" />
                      )}
                    </Flex>
                    {job.progress > 0 && job.progress < 100 && (
                      <Progress value={job.progress} mt="2" />
                    )}
                  </Card>
                ))}
              </Flex>
            </ScrollArea>
          </Box>
        </Box>

        {/* Right Panel - Results */}
        <Box>
          {activeJob ? (
            <Box>
              <Flex justify="between" align="center" mb="4">
                <Heading size="4">Extracted Clips</Heading>
                {activeJob.status === 'complete' && (
                  <Badge size="2" color="green">
                    {activeJob.clips.length} clips extracted
                  </Badge>
                )}
              </Flex>

              {activeJob.status === 'complete' ? (
                <Grid columns="repeat(auto-fill, minmax(300px, 1fr))" gap="4">
                  {activeJob.clips.map(clip => (
                    <Card key={clip.id}>
                      <Box
                        style={{
                          aspectRatio: '16/9',
                          backgroundColor: 'var(--gray-3)',
                          borderRadius: '4px',
                          marginBottom: '12px',
                          position: 'relative',
                          overflow: 'hidden'
                        }}
                      >
                        {clip.thumbnail && (
                          <img 
                            src={clip.thumbnail} 
                            alt={clip.title}
                            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                          />
                        )}
                        <Flex
                          style={{
                            position: 'absolute',
                            inset: 0,
                            alignItems: 'center',
                            justifyContent: 'center',
                            backgroundColor: 'rgba(0,0,0,0.3)',
                            opacity: 0,
                            transition: 'opacity 0.2s',
                            cursor: 'pointer'
                          }}
                          className="play-overlay"
                        >
                          <PlayIcon width="48" height="48" color="white" />
                        </Flex>
                      </Box>
                      
                      <Heading size="3" mb="1">{clip.title}</Heading>
                      <Text size="2" color="gray" mb="2">{clip.description}</Text>
                      
                      <Flex justify="between" align="center" mb="2">
                        <Badge variant="soft">
                          {clip.duration}s • {clip.platform}
                        </Badge>
                        <Text size="1" color="gray">
                          {clip.startTime}s - {clip.endTime}s
                        </Text>
                      </Flex>

                      <Button size="2" variant="soft" onClick={() => downloadClip(clip)}>
                        <DownloadIcon />
                        Download
                      </Button>
                    </Card>
                  ))}
                </Grid>
              ) : activeJob.status === 'failed' ? (
                <Card>
                  <Flex direction="column" align="center" gap="3" py="5">
                    <CrossCircledIcon width="48" height="48" color="var(--red-9)" />
                    <Text size="3" color="red">Processing failed</Text>
                    <Text size="2" color="gray">{activeJob.error}</Text>
                  </Flex>
                </Card>
              ) : (
                <Card>
                  <Flex direction="column" align="center" gap="3" py="5">
                    <ReloadIcon width="48" height="48" className="spinning" />
                    <Text size="3">Processing video...</Text>
                    <Text size="2" color="gray">
                      {activeJob.status === 'uploading' && 'Uploading video...'}
                      {activeJob.status === 'analyzing' && 'Analyzing content with AI...'}
                      {activeJob.status === 'extracting' && 'Extracting clips...'}
                    </Text>
                    <Progress value={activeJob.progress} style={{ width: '200px' }} />
                  </Flex>
                </Card>
              )}
            </Box>
          ) : (
            <Flex direction="column" align="center" justify="center" style={{ height: '100%' }}>
              <VideoIcon width="64" height="64" color="var(--gray-6)" />
              <Text size="3" color="gray" mt="3">
                Upload a video to start extracting clips
              </Text>
            </Flex>
          )}
        </Box>
      </Grid>

      <style>
        {`
          .spinning {
            animation: spin 1s linear infinite;
          }
          
          @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
          
          .play-overlay:hover {
            opacity: 1 !important;
          }
        `}
      </style>
    </Box>
  );
}; 
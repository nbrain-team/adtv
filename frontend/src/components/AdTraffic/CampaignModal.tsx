import React, { useState } from 'react';
import { Box, Flex, Text, TextField, Button, Heading, Checkbox, Slider, Progress, Spinner } from '@radix-ui/themes';
import { VideoIcon, UploadIcon, CheckIcon } from '@radix-ui/react-icons';
import { Client, CampaignFormData, Platform, Campaign, CampaignStatus } from './types';
import { api } from '../../services/api';

interface CampaignModalProps {
  client: Client;
  onComplete: (campaign: Campaign) => void;
  onCancel: () => void;
}

export const CampaignModal: React.FC<CampaignModalProps> = ({
  client,
  onComplete,
  onCancel
}) => {
  const [formData, setFormData] = useState<CampaignFormData>({
    name: '',
    duration_weeks: 2,
    platforms: [Platform.FACEBOOK, Platform.INSTAGRAM]
  });
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile && selectedFile.type.startsWith('video/')) {
      setFile(selectedFile);
      setError('');
    } else {
      setError('Please select a valid video file');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!file) {
      setError('Please select a video file');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const formDataToSend = new FormData();
      formDataToSend.append('video', file);
      formDataToSend.append('name', formData.name);
      formDataToSend.append('duration_weeks', formData.duration_weeks.toString());
      formData.platforms.forEach(platform => {
        formDataToSend.append('platforms', platform);
      });

      const response = await api.post(
        `/api/ad-traffic/clients/${client.id}/campaigns`,
        formDataToSend,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (progressEvent: any) => {
            const progress = progressEvent.total
              ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
              : 0;
            setUploadProgress(progress);
          }
        }
      );

      setCampaign(response.data);
      
      // Close modal immediately and let parent handle the campaign
      onComplete(response.data);
      
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create campaign');
      setLoading(false);
    }
  };

  const togglePlatform = (platform: Platform) => {
    const platforms = formData.platforms.includes(platform)
      ? formData.platforms.filter(p => p !== platform)
      : [...formData.platforms, platform];
    
    setFormData({ ...formData, platforms });
  };

  const platformConfig = [
    { value: Platform.FACEBOOK, label: 'Facebook', color: '#1877f2' },
    { value: Platform.INSTAGRAM, label: 'Instagram', color: '#E4405F' },
    { value: Platform.TIKTOK, label: 'TikTok', color: '#000000' }
  ];

  return (
    <Box style={{ padding: '2rem' }}>
      <Heading size="5" mb="4">
        <VideoIcon style={{ display: 'inline', marginRight: '0.5rem' }} />
        Create Video Campaign
      </Heading>

      {!campaign ? (
        <form onSubmit={handleSubmit}>
          <Flex direction="column" gap="4">
            <Box>
              <Text as="label" size="2" weight="medium" htmlFor="name">Campaign Name *</Text>
              <TextField.Root
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Summer Product Launch"
                required
                style={{ marginTop: '0.5rem' }}
              />
            </Box>

            <Box>
              <Text as="label" size="2" weight="medium">Upload Video *</Text>
              <Box style={{ marginTop: '0.5rem' }}>
                <input
                  type="file"
                  accept="video/*"
                  onChange={handleFileChange}
                  style={{ display: 'none' }}
                  id="video-upload"
                />
                <label htmlFor="video-upload">
                  <Box
                    as="span"
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      padding: '0.5rem 1rem',
                      backgroundColor: 'var(--accent-3)',
                      color: 'var(--accent-11)',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      fontSize: '14px',
                      fontWeight: 500,
                      transition: 'background-color 0.2s',
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--accent-4)'}
                    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'var(--accent-3)'}
                  >
                    <UploadIcon /> Choose Video File
                  </Box>
                </label>
                {file && (
                  <Text size="2" color="gray" style={{ marginLeft: '1rem' }}>
                    {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
                  </Text>
                )}
              </Box>
            </Box>

            <Box>
              <Text as="label" size="2" weight="medium">Campaign Duration</Text>
              <Box style={{ marginTop: '0.5rem' }}>
                <Slider
                  value={[formData.duration_weeks]}
                  onValueChange={([value]) => setFormData({ ...formData, duration_weeks: value })}
                  min={1}
                  max={8}
                  step={1}
                />
                <Text size="2" weight="medium" style={{ marginTop: '0.5rem' }}>
                  {formData.duration_weeks} week{formData.duration_weeks > 1 ? 's' : ''}
                </Text>
              </Box>
            </Box>

            <Box>
              <Text as="label" size="2" weight="medium">Platforms *</Text>
              <Flex gap="3" mt="2">
                {platformConfig.map(platform => (
                  <label key={platform.value} style={{ cursor: 'pointer' }}>
                    <Flex align="center" gap="2">
                      <Checkbox
                        checked={formData.platforms.includes(platform.value)}
                        onCheckedChange={() => togglePlatform(platform.value)}
                      />
                      <Text size="2" style={{ color: platform.color }}>
                        {platform.label}
                      </Text>
                    </Flex>
                  </label>
                ))}
              </Flex>
            </Box>

            {error && (
              <Text size="2" color="red">{error}</Text>
            )}

            <Flex gap="3" justify="end">
              <Button 
                type="button" 
                variant="soft" 
                onClick={onCancel}
                disabled={loading}
              >
                Cancel
              </Button>
              <Button 
                type="submit" 
                disabled={loading || !formData.name || !file || formData.platforms.length === 0}
              >
                {loading ? (
                  <Flex align="center" gap="2">
                    <Spinner size="1" />
                    <Text>Uploading...</Text>
                  </Flex>
                ) : (
                  'Create Campaign'
                )}
              </Button>
            </Flex>
          </Flex>
        </form>
      ) : (
        <Flex direction="column" gap="4" align="center" style={{ padding: '2rem' }}>
          {campaign.status === CampaignStatus.PROCESSING ? (
            <>
              <VideoIcon width="48" height="48" />
              <Heading size="4">Processing Video...</Heading>
              <Text size="2" color="gray">
                Extracting clips and generating social content
              </Text>
              <Progress value={campaign.progress} style={{ width: '100%' }} />
              <Text size="1" color="gray">{campaign.progress}%</Text>
            </>
          ) : campaign.status === CampaignStatus.READY ? (
            <>
              <CheckIcon width="48" height="48" color="green" />
              <Heading size="4" color="green">Campaign Ready!</Heading>
              <Text size="2" color="gray">
                Your video has been processed and posts have been scheduled
              </Text>
            </>
          ) : (
            <>
              <Text size="4" color="red">Processing Failed</Text>
              <Text size="2" color="gray">{campaign.error_message}</Text>
              <Button onClick={onCancel}>Close</Button>
            </>
          )}
        </Flex>
      )}
    </Box>
  );
}; 
import React, { useState, useEffect } from 'react';
import {
  Box, Card, Flex, Text, Heading, Button, Badge, Tabs,
  ScrollArea, IconButton, Dialog, TextArea, Separator
} from '@radix-ui/themes';
import {
  CalendarIcon, Pencil1Icon, CheckIcon, Cross2Icon,
  ReloadIcon, RocketIcon, PauseIcon, PlayIcon
} from '@radix-ui/react-icons';
import { useParams } from 'react-router-dom';
import api from '../services/campaignApi';

interface Campaign {
  id: string;
  name: string;
  description?: string;
  client: {
    id: string;
    name: string;
    company: string;
  };
  status: string;
  start_date: string;
  end_date: string;
  topics: string[];
  content_items: ContentItem[];
}

interface ContentItem {
  id: string;
  platform: string;
  content: string;
  title?: string;
  hashtags?: string[];
  scheduled_date: string;
  status: string;
  media_urls?: string[];
}

const platformIcons: Record<string, string> = {
  facebook: '📘',
  linkedin: '💼',
  twitter: '🐦',
  instagram: '📷',
  email: '📧'
};

export const CampaignDetail: React.FC = () => {
  const { campaignId } = useParams<{ campaignId: string }>();
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [selectedContent, setSelectedContent] = useState<ContentItem | null>(null);
  const [editingContent, setEditingContent] = useState<string>('');
  const [feedbackDialog, setFeedbackDialog] = useState(false);
  const [feedback, setFeedback] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCampaign();
  }, [campaignId]);

  const fetchCampaign = async () => {
    try {
      const response = await api.get(`/campaigns/${campaignId}`);
      setCampaign(response.data);
    } catch (error) {
      console.error('Error fetching campaign:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusUpdate = async (status: string) => {
    try {
      await api.put(`/campaigns/${campaignId}/status`, { status });
      fetchCampaign();
    } catch (error) {
      console.error('Error updating status:', error);
    }
  };

  const handleRegenerateContent = async () => {
    if (!selectedContent) return;

    try {
      await api.post(
        `/campaigns/${campaignId}/regenerate/${selectedContent.id}`,
        { feedback }
      );
      setFeedbackDialog(false);
      setFeedback('');
      fetchCampaign();
    } catch (error) {
      console.error('Error regenerating content:', error);
    }
  };

  const groupContentByPlatform = () => {
    if (!campaign) return {};
    
    return campaign.content_items.reduce((acc, item) => {
      if (!acc[item.platform]) {
        acc[item.platform] = [];
      }
      acc[item.platform].push(item);
      return acc;
    }, {} as Record<string, ContentItem[]>);
  };

  if (loading) {
    return (
      <Flex align="center" justify="center" style={{ height: '400px' }}>
        <Text>Loading campaign...</Text>
      </Flex>
    );
  }

  if (!campaign) {
    return (
      <Box>
        <Text>Campaign not found</Text>
      </Box>
    );
  }

  const contentByPlatform = groupContentByPlatform();

  return (
    <Box style={{ maxWidth: '1200px', margin: '0 auto' }}>
      {/* Header */}
      <Flex justify="between" align="start" mb="6">
        <Box>
          <Heading size="6" mb="2">{campaign.name}</Heading>
          <Text color="gray">{campaign.client.company}</Text>
        </Box>
        <Flex gap="2">
          <Badge size="2" color={
            campaign.status === 'draft' ? 'gray' :
            campaign.status === 'pending_approval' ? 'orange' :
            campaign.status === 'approved' ? 'green' :
            campaign.status === 'active' ? 'blue' :
            'gray'
          }>
            {campaign.status.replace('_', ' ').toUpperCase()}
          </Badge>
        </Flex>
      </Flex>

      {/* Campaign Info */}
      <Card mb="4">
        <Flex gap="6">
          <Box>
            <Text size="2" color="gray">Duration</Text>
            <Flex align="center" gap="2" mt="1">
              <CalendarIcon />
              <Text weight="medium">
                {new Date(campaign.start_date).toLocaleDateString()} - 
                {new Date(campaign.end_date).toLocaleDateString()}
              </Text>
            </Flex>
          </Box>
          <Box>
            <Text size="2" color="gray">Topics</Text>
            <Flex gap="2" mt="1" wrap="wrap">
              {campaign.topics.map((topic, idx) => (
                <Badge key={idx} variant="soft">{topic}</Badge>
              ))}
            </Flex>
          </Box>
        </Flex>
      </Card>

      {/* Action Buttons */}
      <Flex gap="2" mb="4">
        {campaign.status === 'pending_approval' && (
          <>
            <Button color="green" onClick={() => handleStatusUpdate('approved')}>
              <CheckIcon />
              Approve Campaign
            </Button>
            <Button variant="soft" color="red" onClick={() => handleStatusUpdate('draft')}>
              <Cross2Icon />
              Request Changes
            </Button>
          </>
        )}
        {campaign.status === 'approved' && (
          <Button onClick={() => handleStatusUpdate('active')}>
            <RocketIcon />
            Launch Campaign
          </Button>
        )}
        {campaign.status === 'active' && (
          <Button variant="soft" onClick={() => handleStatusUpdate('paused')}>
            <PauseIcon />
            Pause Campaign
          </Button>
        )}
        {campaign.status === 'paused' && (
          <Button onClick={() => handleStatusUpdate('active')}>
            <PlayIcon />
            Resume Campaign
          </Button>
        )}
      </Flex>

      {/* Content Tabs */}
      <Tabs.Root defaultValue={Object.keys(contentByPlatform)[0]}>
        <Tabs.List>
          {Object.keys(contentByPlatform).map(platform => (
            <Tabs.Trigger key={platform} value={platform}>
              <Flex align="center" gap="2">
                <Text size="4">{platformIcons[platform]}</Text>
                <Text>{platform.charAt(0).toUpperCase() + platform.slice(1)}</Text>
                <Badge variant="soft" size="1">
                  {contentByPlatform[platform].length}
                </Badge>
              </Flex>
            </Tabs.Trigger>
          ))}
        </Tabs.List>

        {Object.entries(contentByPlatform).map(([platform, items]) => (
          <Tabs.Content key={platform} value={platform}>
            <ScrollArea style={{ height: '600px' }}>
              <Flex direction="column" gap="3" p="4">
                {items.map(item => (
                  <Card key={item.id}>
                    <Flex justify="between" align="start" mb="3">
                      <Badge variant="soft">
                        {new Date(item.scheduled_date).toLocaleDateString()}
                      </Badge>
                      <Flex gap="2">
                        <IconButton
                          size="1"
                          variant="ghost"
                          onClick={() => {
                            setSelectedContent(item);
                            setFeedbackDialog(true);
                          }}
                        >
                          <ReloadIcon />
                        </IconButton>
                      </Flex>
                    </Flex>

                    {item.title && (
                      <Heading size="3" mb="2">{item.title}</Heading>
                    )}
                    
                    <Text style={{ whiteSpace: 'pre-wrap' }}>
                      {item.content}
                    </Text>

                    {item.hashtags && item.hashtags.length > 0 && (
                      <Flex gap="2" mt="3" wrap="wrap">
                        {item.hashtags.map((tag, idx) => (
                          <Badge key={idx} variant="outline" size="1">
                            #{tag}
                          </Badge>
                        ))}
                      </Flex>
                    )}
                  </Card>
                ))}
              </Flex>
            </ScrollArea>
          </Tabs.Content>
        ))}
      </Tabs.Root>

      {/* Regenerate Dialog */}
      <Dialog.Root open={feedbackDialog} onOpenChange={setFeedbackDialog}>
        <Dialog.Content style={{ maxWidth: 450 }}>
          <Dialog.Title>Regenerate Content</Dialog.Title>
          <Dialog.Description size="2" mb="4">
            Provide feedback to improve this content
          </Dialog.Description>

          <TextArea
            placeholder="What would you like to change about this content?"
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            rows={4}
          />

          <Flex gap="3" mt="4" justify="end">
            <Dialog.Close>
              <Button variant="soft" color="gray">
                Cancel
              </Button>
            </Dialog.Close>
            <Button onClick={handleRegenerateContent}>
              Regenerate
            </Button>
          </Flex>
        </Dialog.Content>
      </Dialog.Root>
    </Box>
  );
}; 
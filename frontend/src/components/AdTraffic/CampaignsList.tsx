import React, { useState, useEffect } from 'react';
import { Box, Flex, Text, Card, Badge, Button, Select, IconButton } from '@radix-ui/themes';
import { PlayIcon, CheckIcon, Cross2Icon, ReloadIcon, EyeOpenIcon, TrashIcon } from '@radix-ui/react-icons';
import { AlertDialog } from '@radix-ui/themes';
import { Campaign, CampaignStatus } from './types';
import { api } from '../../services/api';

interface CampaignsListProps {
  clientId: string;
  onViewCampaign: (campaign: Campaign) => void;
  onRefresh?: () => void;
}

export const CampaignsList: React.FC<CampaignsListProps> = ({ 
  clientId, 
  onViewCampaign,
  onRefresh 
}) => {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'processing' | 'ready' | 'failed'>('all');
  const [campaignToDelete, setCampaignToDelete] = useState<Campaign | null>(null);

  useEffect(() => {
    fetchCampaigns();
  }, [clientId]);

  useEffect(() => {
    // Poll for updates every 5 seconds if there are processing campaigns
    const interval = setInterval(() => {
      if (campaigns.some(c => c.status === CampaignStatus.PROCESSING)) {
        fetchCampaigns();
      }
    }, 5000);
    
    return () => clearInterval(interval);
  }, [campaigns, clientId]);

  const fetchCampaigns = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/api/ad-traffic/clients/${clientId}/campaigns`);
      setCampaigns(response.data);
    } catch (error) {
      console.error('Error fetching campaigns:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredCampaigns = campaigns.filter(campaign => {
    if (filter === 'all') return true;
    return campaign.status === filter;
  });

  const handleDelete = async (campaignId: string) => {
    try {
      await api.delete(`/api/ad-traffic/campaigns/${campaignId}`);
      setCampaignToDelete(null);
      fetchCampaigns();
      onRefresh?.();
    } catch (error) {
      console.error('Error deleting campaign:', error);
      // You can add toast notification here for error
    }
  };

  const getStatusIcon = (status: CampaignStatus) => {
    switch (status) {
      case CampaignStatus.PROCESSING:
        return <ReloadIcon className="animate-spin" />;
      case CampaignStatus.READY:
        return <CheckIcon color="green" />;
      case CampaignStatus.FAILED:
        return <Cross2Icon color="red" />;
      default:
        return null;
    }
  };

  const getStatusColor = (status: CampaignStatus) => {
    switch (status) {
      case CampaignStatus.PROCESSING:
        return 'blue';
      case CampaignStatus.READY:
        return 'green';
      case CampaignStatus.FAILED:
        return 'red';
      default:
        return 'gray';
    }
  };

  if (loading) {
    return (
      <Box p="4">
        <Text>Loading campaigns...</Text>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Flex justify="between" align="center" mb="4">
        <Flex align="center" gap="3">
          <Text size="4" weight="bold">Campaigns</Text>
          <Badge size="2" variant="soft">{campaigns.length} total</Badge>
        </Flex>
        
        <Flex gap="2" align="center">
          <Select.Root value={filter} onValueChange={(value: any) => setFilter(value)}>
            <Select.Trigger />
            <Select.Content>
              <Select.Item value="all">All Campaigns</Select.Item>
              <Select.Item value="processing">In Progress</Select.Item>
              <Select.Item value="ready">Completed</Select.Item>
              <Select.Item value="failed">Failed</Select.Item>
            </Select.Content>
          </Select.Root>
          
          <IconButton 
            size="2" 
            variant="soft" 
            onClick={() => {
              fetchCampaigns();
              onRefresh?.();
            }}
          >
            <ReloadIcon />
          </IconButton>
        </Flex>
      </Flex>

      {/* Campaigns List */}
      <Flex direction="column" gap="3">
        {filteredCampaigns.length === 0 ? (
          <Card>
            <Flex align="center" justify="center" p="6">
              <Text color="gray">No campaigns found</Text>
            </Flex>
          </Card>
        ) : (
          filteredCampaigns.map(campaign => (
            <Card 
              key={campaign.id} 
              style={{ cursor: 'pointer' }}
              onClick={() => onViewCampaign(campaign)}
            >
              <Flex justify="between" align="center">
                <Flex direction="column" gap="1">
                  <Flex align="center" gap="2">
                    <Text weight="medium" size="3">{campaign.name}</Text>
                    {getStatusIcon(campaign.status)}
                  </Flex>
                  
                  <Flex gap="3" align="center">
                    <Badge color={getStatusColor(campaign.status)} variant="soft">
                      {campaign.status === CampaignStatus.PROCESSING ? 'Uploading & Processing' : campaign.status}
                    </Badge>
                    
                    {campaign.duration_weeks && (
                      <Text size="1" color="gray">
                        {campaign.duration_weeks} weeks
                      </Text>
                    )}
                    
                    {campaign.status === CampaignStatus.PROCESSING && (
                      <Text size="1" style={{ fontStyle: 'italic' }} color="gray">
                        Creating clips and scheduling posts...
                      </Text>
                    )}
                    
                    <Text size="1" color="gray">
                      Created {new Date(campaign.created_at).toLocaleDateString()}
                    </Text>
                  </Flex>
                </Flex>
                
                <Flex align="center" gap="2">
                  {campaign.progress !== undefined && campaign.status === CampaignStatus.PROCESSING && (
                    <Box style={{ width: '100px' }}>
                      <Flex align="center" gap="2">
                        <Box style={{ 
                          flex: 1, 
                          height: '4px', 
                          backgroundColor: 'var(--gray-4)',
                          borderRadius: '2px',
                          overflow: 'hidden'
                        }}>
                          <Box style={{
                            width: `${campaign.progress}%`,
                            height: '100%',
                            backgroundColor: 'var(--blue-9)',
                            transition: 'width 0.3s ease'
                          }} />
                        </Box>
                        <Text size="1" color="gray">{campaign.progress}%</Text>
                      </Flex>
                    </Box>
                  )}
                  
                  <Button 
                    size="2" 
                    variant="ghost"
                    disabled={campaign.status === CampaignStatus.PROCESSING}
                  >
                    <EyeOpenIcon /> 
                    {campaign.status === CampaignStatus.PROCESSING ? 'Processing...' : 'View'}
                  </Button>
                  <IconButton 
                    size="2" 
                    variant="ghost" 
                    color="red"
                    disabled={campaign.status === CampaignStatus.PROCESSING}
                    onClick={(e) => {
                      e.stopPropagation();
                      setCampaignToDelete(campaign);
                    }}
                  >
                    <TrashIcon />
                  </IconButton>
                </Flex>
              </Flex>
            </Card>
          ))
        )}
      </Flex>

      <AlertDialog.Root open={!!campaignToDelete}>
        <AlertDialog.Content maxWidth="450px">
          <AlertDialog.Title>Delete Campaign</AlertDialog.Title>
          <AlertDialog.Description size="2">
            Are you sure you want to delete "{campaignToDelete?.name}"? This action cannot be undone.
          </AlertDialog.Description>

          <Flex gap="3" mt="4" justify="end">
            <AlertDialog.Cancel>
              <Button variant="soft" color="gray" onClick={() => setCampaignToDelete(null)}>
                Cancel
              </Button>
            </AlertDialog.Cancel>
            <AlertDialog.Action>
              <Button variant="solid" color="red" onClick={() => handleDelete(campaignToDelete!.id)}>
                Delete
              </Button>
            </AlertDialog.Action>
          </Flex>
        </AlertDialog.Content>
      </AlertDialog.Root>

    </Box>
  );
}; 
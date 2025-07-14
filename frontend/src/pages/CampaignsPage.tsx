import React, { useState, useEffect } from 'react';
import { Box, Flex, Heading, Button, Card, Text, Badge, Grid } from '@radix-ui/themes';
import { PlusIcon, MagicWandIcon } from '@radix-ui/react-icons';
import { MainLayout } from '../components/MainLayout';
import { useNavigate } from 'react-router-dom';
import { CampaignCreator } from '../components/CampaignCreator';

interface Campaign {
  id: string;
  name: string;
  client: {
    company: string;
  };
  status: string;
  start_date: string;
  end_date: string;
}

const CampaignsPage = () => {
  const navigate = useNavigate();
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [showCreator, setShowCreator] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCampaigns();
  }, []);

  const fetchCampaigns = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000/api'}/campaigns`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setCampaigns(data);
      }
    } catch (error) {
      console.error('Error fetching campaigns:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'draft': return 'gray';
      case 'pending_approval': return 'orange';
      case 'approved': return 'green';
      case 'active': return 'blue';
      case 'completed': return 'gray';
      default: return 'gray';
    }
  };

  if (showCreator) {
    return (
      <MainLayout onNewChat={() => {}}>
        <Box p="6">
          <Button 
            variant="ghost" 
            onClick={() => setShowCreator(false)}
            mb="4"
          >
            ← Back to Campaigns
          </Button>
          <CampaignCreator />
        </Box>
      </MainLayout>
    );
  }

  return (
    <MainLayout onNewChat={() => {}}>
      <Box p="6">
        <Flex justify="between" align="center" mb="6">
          <Flex align="center" gap="3">
            <MagicWandIcon width="32" height="32" />
            <Heading size="7">Marketing Campaigns</Heading>
          </Flex>
          <Button size="3" onClick={() => setShowCreator(true)}>
            <PlusIcon />
            Create Campaign
          </Button>
        </Flex>

        {loading ? (
          <Text>Loading campaigns...</Text>
        ) : campaigns.length === 0 ? (
          <Card>
            <Flex direction="column" align="center" gap="4" p="6">
              <MagicWandIcon width="48" height="48" color="gray" />
              <Text size="3" color="gray">No campaigns yet</Text>
              <Button onClick={() => setShowCreator(true)}>
                Create Your First Campaign
              </Button>
            </Flex>
          </Card>
        ) : (
          <Grid columns="3" gap="4">
            {campaigns.map(campaign => (
              <Card 
                key={campaign.id}
                style={{ cursor: 'pointer' }}
                onClick={() => navigate(`/campaigns/${campaign.id}`)}
              >
                <Flex direction="column" gap="3">
                  <Flex justify="between" align="start">
                    <Box>
                      <Heading size="4">{campaign.name}</Heading>
                      <Text size="2" color="gray">{campaign.client.company}</Text>
                    </Box>
                    <Badge color={getStatusColor(campaign.status)}>
                      {campaign.status.replace('_', ' ')}
                    </Badge>
                  </Flex>
                  <Text size="2">
                    {new Date(campaign.start_date).toLocaleDateString()} - 
                    {new Date(campaign.end_date).toLocaleDateString()}
                  </Text>
                </Flex>
              </Card>
            ))}
          </Grid>
        )}
      </Box>
    </MainLayout>
  );
};

export default CampaignsPage; 
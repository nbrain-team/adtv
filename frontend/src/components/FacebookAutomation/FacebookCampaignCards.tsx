import { useState, useEffect } from 'react';
import { Box, Flex, Text, Card, Badge, Button, IconButton, Progress, Heading } from '@radix-ui/themes';
import { PlayIcon, PauseIcon, TrashIcon, DotsHorizontalIcon } from '@radix-ui/react-icons';
import api from '../../api';

interface Campaign {
  id: string;
  name: string;
  status: string;
  objective: string;
  daily_budget: number;
  impressions: number;
  reach: number;
  clicks: number;
  ctr: number;
  cpc: number;
  spend: number;
  conversions: number;
  roas: number;
  created_at: string;
  post_thumbnail?: string;
}

interface FacebookCampaignCardsProps {
  clientId: string;
}

const FacebookCampaignCards: React.FC<FacebookCampaignCardsProps> = ({ clientId }) => {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'active' | 'paused' | 'completed'>('all');

  useEffect(() => {
    if (clientId) {
      fetchCampaigns();
    }
  }, [clientId]);

  const fetchCampaigns = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/facebook-automation/campaigns', {
        params: { client_id: clientId }
      });
      setCampaigns(response.data);
    } catch (error) {
      console.error('Failed to fetch campaigns:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCampaignAction = async (campaignId: string, action: string) => {
    try {
      if (action === 'delete') {
        await api.post('/api/facebook-automation/bulk/campaigns', {
          item_ids: [campaignId],
          operation: 'delete'
        });
      } else {
        const status = action === 'pause' ? 'PAUSED' : 'ACTIVE';
        await api.put(`/api/facebook-automation/campaigns/${campaignId}`, { status });
      }
      fetchCampaigns();
    } catch (error) {
      console.error('Failed to update campaign:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'green';
      case 'paused': return 'orange';
      case 'draft': return 'blue';
      case 'completed': return 'gray';
      case 'failed': return 'red';
      default: return 'gray';
    }
  };

  const formatCurrency = (amount: number) => `$${amount.toFixed(2)}`;
  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  const filteredCampaigns = campaigns.filter(campaign => {
    if (filter === 'all') return true;
    return campaign.status === filter;
  });

  const getBudgetSpentPercentage = (campaign: Campaign) => {
    const totalBudget = campaign.daily_budget * 7; // Assuming 7 day campaigns
    const percentage = (campaign.spend / totalBudget) * 100;
    return Math.min(percentage, 100);
  };

  const CampaignCard = ({ campaign }: { campaign: Campaign }) => (
    <Card style={{ 
      overflow: 'hidden',
      transition: 'all 0.2s',
      border: '1px solid var(--gray-4)'
    }}>
      {/* Campaign Header with Image */}
      <Box style={{ position: 'relative' }}>
        {campaign.post_thumbnail && (
          <Box style={{ 
            height: 160,
            background: `url(${campaign.post_thumbnail}) center/cover`,
            filter: campaign.status === 'paused' ? 'grayscale(1)' : 'none'
          }} />
        )}
        {!campaign.post_thumbnail && (
          <Box style={{ 
            height: 160,
            background: 'linear-gradient(135deg, var(--accent-4), var(--accent-6))'
          }} />
        )}
        
        {/* Status Badge */}
        <Badge 
          color={getStatusColor(campaign.status)}
          style={{ 
            position: 'absolute', 
            top: 12, 
            left: 12 
          }}
        >
          {campaign.status}
        </Badge>

        {/* Action Menu */}
        <IconButton 
          size="1" 
          variant="solid"
          style={{ 
            position: 'absolute', 
            top: 12, 
            right: 12,
            background: 'rgba(255,255,255,0.9)'
          }}
        >
          <DotsHorizontalIcon />
        </IconButton>
      </Box>

      {/* Campaign Details */}
      <Box p="4">
        <Heading size="4" mb="2">{campaign.name}</Heading>
        <Text size="2" color="gray" style={{ display: 'block', marginBottom: 16 }}>
          {campaign.objective.replace(/_/g, ' ').toLowerCase()}
        </Text>

        {/* Key Metrics Grid */}
        <Box style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(2, 1fr)', 
          gap: 16,
          marginBottom: 16
        }}>
          <Box>
            <Text size="1" color="gray" style={{ display: 'block' }}>Impressions</Text>
            <Text size="3" weight="bold">{formatNumber(campaign.impressions)}</Text>
          </Box>
          <Box>
            <Text size="1" color="gray" style={{ display: 'block' }}>Clicks</Text>
            <Text size="3" weight="bold">{formatNumber(campaign.clicks)}</Text>
          </Box>
          <Box>
            <Text size="1" color="gray" style={{ display: 'block' }}>CTR</Text>
            <Text size="3" weight="bold">{campaign.ctr.toFixed(2)}%</Text>
          </Box>
          <Box>
            <Text size="1" color="gray" style={{ display: 'block' }}>CPC</Text>
            <Text size="3" weight="bold">{formatCurrency(campaign.cpc)}</Text>
          </Box>
        </Box>

        {/* Budget Progress */}
        <Box mb="3">
          <Flex justify="between" mb="1">
            <Text size="2">Budget Used</Text>
            <Text size="2" weight="bold">{formatCurrency(campaign.spend)} / {formatCurrency(campaign.daily_budget * 7)}</Text>
          </Flex>
          <Progress value={getBudgetSpentPercentage(campaign)} size="2" />
        </Box>

        {/* ROAS Highlight */}
        <Card style={{ background: 'var(--accent-2)' }}>
          <Flex justify="between" align="center" p="3">
            <Text size="2">ROAS</Text>
            <Text size="5" weight="bold" color={campaign.roas > 2 ? 'green' : 'orange'}>
              {campaign.roas.toFixed(1)}x
            </Text>
          </Flex>
        </Card>

        {/* Action Buttons */}
        <Flex gap="2" mt="3">
          {campaign.status === 'active' ? (
            <Button size="2" variant="soft" style={{ flex: 1 }} onClick={() => handleCampaignAction(campaign.id, 'pause')}>
              <PauseIcon />
              Pause
            </Button>
          ) : campaign.status === 'paused' ? (
            <Button size="2" variant="soft" color="green" style={{ flex: 1 }} onClick={() => handleCampaignAction(campaign.id, 'resume')}>
              <PlayIcon />
              Resume
            </Button>
          ) : null}
          <Button size="2" variant="soft" color="red" onClick={() => handleCampaignAction(campaign.id, 'delete')}>
            <TrashIcon />
          </Button>
        </Flex>
      </Box>
    </Card>
  );

  if (loading) {
    return (
      <Flex align="center" justify="center" style={{ minHeight: 400 }}>
        <Text size="3">Loading campaigns...</Text>
      </Flex>
    );
  }

  return (
    <Box>
      {/* Filter Tabs */}
      <Card mb="4">
        <Flex gap="2" p="3">
          <Button 
            size="2" 
            variant={filter === 'all' ? 'solid' : 'soft'}
            onClick={() => setFilter('all')}
          >
            All ({campaigns.length})
          </Button>
          <Button 
            size="2" 
            variant={filter === 'active' ? 'solid' : 'soft'}
            onClick={() => setFilter('active')}
          >
            Active ({campaigns.filter(c => c.status === 'active').length})
          </Button>
          <Button 
            size="2" 
            variant={filter === 'paused' ? 'solid' : 'soft'}
            onClick={() => setFilter('paused')}
          >
            Paused ({campaigns.filter(c => c.status === 'paused').length})
          </Button>
          <Button 
            size="2" 
            variant={filter === 'completed' ? 'solid' : 'soft'}
            onClick={() => setFilter('completed')}
          >
            Completed ({campaigns.filter(c => c.status === 'completed').length})
          </Button>
        </Flex>
      </Card>

      {/* Campaign Cards Grid */}
      {filteredCampaigns.length > 0 ? (
        <Box style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', 
          gap: 20 
        }}>
          {filteredCampaigns.map(campaign => (
            <CampaignCard key={campaign.id} campaign={campaign} />
          ))}
        </Box>
      ) : (
        <Card>
          <Flex direction="column" align="center" p="8">
            <Text size="3" color="gray" mb="4">No {filter} campaigns</Text>
            <Text size="2" color="gray">Create campaigns by converting posts to ads</Text>
          </Flex>
        </Card>
      )}
    </Box>
  );
};

export default FacebookCampaignCards; 
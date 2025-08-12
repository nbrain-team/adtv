import { useState, useEffect } from 'react';
import { Box, Flex, Text, Card, Table, Button, Badge, IconButton } from '@radix-ui/themes';
import { PauseIcon, PlayIcon, TrashIcon } from '@radix-ui/react-icons';
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
}

interface FacebookCampaignsGridProps {
  clientId: string | null;
}

const FacebookCampaignsGrid: React.FC<FacebookCampaignsGridProps> = ({ clientId }) => {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCampaigns, setSelectedCampaigns] = useState<string[]>([]);

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

  const handleBulkOperation = async (operation: string) => {
    try {
      await api.post('/api/facebook-automation/bulk/campaigns', {
        item_ids: selectedCampaigns,
        operation
      });
      fetchCampaigns();
      setSelectedCampaigns([]);
    } catch (error) {
      console.error('Failed to perform bulk operation:', error);
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
  const formatPercent = (value: number) => `${value.toFixed(2)}%`;

  if (loading) {
    return (
      <Card>
        <Box p="6">
          <Text>Loading campaigns...</Text>
        </Box>
      </Card>
    );
  }

  if (campaigns.length === 0) {
    return (
      <Card>
        <Flex direction="column" align="center" p="8">
          <Text size="3" color="gray" mb="4">No campaigns yet</Text>
          <Text size="2" color="gray">Convert posts to ads to see campaigns here</Text>
        </Flex>
      </Card>
    );
  }

  return (
    <Box>
      {/* Bulk Actions */}
      {selectedCampaigns.length > 0 && (
        <Card mb="4">
          <Flex align="center" justify="between" p="3">
            <Text size="2">{selectedCampaigns.length} campaigns selected</Text>
            <Flex gap="2">
              <Button size="2" variant="outline" onClick={() => handleBulkOperation('pause')}>
                Pause Selected
              </Button>
              <Button size="2" variant="outline" onClick={() => handleBulkOperation('resume')}>
                Resume Selected
              </Button>
              <Button size="2" variant="outline" color="red" onClick={() => handleBulkOperation('delete')}>
                Delete Selected
              </Button>
            </Flex>
          </Flex>
        </Card>
      )}

      {/* Campaigns Table */}
      <Card>
        <Table.Root>
          <Table.Header>
            <Table.Row>
              <Table.ColumnHeaderCell width="30px">
                <input
                  type="checkbox"
                  checked={selectedCampaigns.length === campaigns.length}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedCampaigns(campaigns.map(c => c.id));
                    } else {
                      setSelectedCampaigns([]);
                    }
                  }}
                />
              </Table.ColumnHeaderCell>
              <Table.ColumnHeaderCell>Campaign</Table.ColumnHeaderCell>
              <Table.ColumnHeaderCell>Status</Table.ColumnHeaderCell>
              <Table.ColumnHeaderCell>Budget</Table.ColumnHeaderCell>
              <Table.ColumnHeaderCell>Impressions</Table.ColumnHeaderCell>
              <Table.ColumnHeaderCell>Clicks</Table.ColumnHeaderCell>
              <Table.ColumnHeaderCell>CTR</Table.ColumnHeaderCell>
              <Table.ColumnHeaderCell>CPC</Table.ColumnHeaderCell>
              <Table.ColumnHeaderCell>Spend</Table.ColumnHeaderCell>
              <Table.ColumnHeaderCell>ROAS</Table.ColumnHeaderCell>
              <Table.ColumnHeaderCell>Actions</Table.ColumnHeaderCell>
            </Table.Row>
          </Table.Header>

          <Table.Body>
            {campaigns.map(campaign => (
              <Table.Row key={campaign.id}>
                <Table.Cell>
                  <input
                    type="checkbox"
                    checked={selectedCampaigns.includes(campaign.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedCampaigns([...selectedCampaigns, campaign.id]);
                      } else {
                        setSelectedCampaigns(selectedCampaigns.filter(id => id !== campaign.id));
                      }
                    }}
                  />
                </Table.Cell>
                <Table.Cell>
                  <Box>
                    <Text weight="bold" size="2">{campaign.name}</Text>
                    <Text size="1" color="gray">{campaign.objective}</Text>
                  </Box>
                </Table.Cell>
                <Table.Cell>
                  <Badge color={getStatusColor(campaign.status)}>
                    {campaign.status}
                  </Badge>
                </Table.Cell>
                <Table.Cell>{formatCurrency(campaign.daily_budget)}/day</Table.Cell>
                <Table.Cell>{campaign.impressions.toLocaleString()}</Table.Cell>
                <Table.Cell>{campaign.clicks.toLocaleString()}</Table.Cell>
                <Table.Cell>{formatPercent(campaign.ctr)}</Table.Cell>
                <Table.Cell>{formatCurrency(campaign.cpc)}</Table.Cell>
                <Table.Cell>{formatCurrency(campaign.spend)}</Table.Cell>
                <Table.Cell>
                  {campaign.roas > 0 ? `${campaign.roas.toFixed(2)}x` : '-'}
                </Table.Cell>
                <Table.Cell>
                  <Flex gap="1">
                    {campaign.status === 'active' ? (
                      <IconButton
                        size="1"
                        variant="ghost"
                        onClick={() => handleCampaignAction(campaign.id, 'pause')}
                      >
                        <PauseIcon />
                      </IconButton>
                    ) : campaign.status === 'paused' ? (
                      <IconButton
                        size="1"
                        variant="ghost"
                        onClick={() => handleCampaignAction(campaign.id, 'resume')}
                      >
                        <PlayIcon />
                      </IconButton>
                    ) : null}
                    <IconButton
                      size="1"
                      variant="ghost"
                      color="red"
                      onClick={() => handleCampaignAction(campaign.id, 'delete')}
                    >
                      <TrashIcon />
                    </IconButton>
                  </Flex>
                </Table.Cell>
              </Table.Row>
            ))}
          </Table.Body>
        </Table.Root>
      </Card>
    </Box>
  );
};

export default FacebookCampaignsGrid; 
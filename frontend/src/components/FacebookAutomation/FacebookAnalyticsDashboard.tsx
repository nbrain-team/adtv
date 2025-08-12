import { useState, useEffect } from 'react';
import { Box, Flex, Text, Card, Grid, Select } from '@radix-ui/themes';
import api from '../../api';

interface Analytics {
  total_spend: number;
  total_impressions: number;
  total_reach: number;
  total_clicks: number;
  avg_ctr: number;
  avg_cpc: number;
  avg_cpm: number;
  total_conversions: number;
  avg_conversion_rate: number;
  avg_roas: number;
  top_performing_campaigns: Array<{
    id: string;
    name: string;
    roas: number;
    spend: number;
    conversions: number;
  }>;
}

interface FacebookAnalyticsDashboardProps {
  clientId: string | null;
}

const FacebookAnalyticsDashboard: React.FC<FacebookAnalyticsDashboardProps> = ({ clientId }) => {
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeframe, setTimeframe] = useState('last_7_days');

  useEffect(() => {
    if (clientId) {
      fetchAnalytics();
    }
  }, [clientId, timeframe]);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const response = await api.post('/facebook-automation/analytics', {
        client_ids: [clientId],
        timeframe
      });
      setAnalytics(response.data);
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => `$${amount.toFixed(2)}`;
  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  if (loading) {
    return (
      <Card>
        <Box p="6">
          <Text>Loading analytics...</Text>
        </Box>
      </Card>
    );
  }

  if (!analytics) {
    return (
      <Card>
        <Box p="6">
          <Text>No analytics data available</Text>
        </Box>
      </Card>
    );
  }

  return (
    <Box>
      {/* Time Period Selector */}
      <Flex justify="between" align="center" mb="4">
        <Text size="5" weight="bold">Performance Overview</Text>
        <Select.Root value={timeframe} onValueChange={setTimeframe}>
          <Select.Trigger />
          <Select.Content>
            <Select.Item value="today">Today</Select.Item>
            <Select.Item value="yesterday">Yesterday</Select.Item>
            <Select.Item value="last_7_days">Last 7 Days</Select.Item>
            <Select.Item value="last_30_days">Last 30 Days</Select.Item>
            <Select.Item value="this_month">This Month</Select.Item>
            <Select.Item value="last_month">Last Month</Select.Item>
          </Select.Content>
        </Select.Root>
      </Flex>

      {/* Key Metrics Grid */}
      <Grid columns={{ initial: '2', md: '4' }} gap="4" mb="6">
        <Card>
          <Box p="4">
            <Text size="2" color="gray" mb="1">Total Spend</Text>
            <Text size="6" weight="bold">{formatCurrency(analytics.total_spend)}</Text>
          </Box>
        </Card>

        <Card>
          <Box p="4">
            <Text size="2" color="gray" mb="1">Impressions</Text>
            <Text size="6" weight="bold">{formatNumber(analytics.total_impressions)}</Text>
          </Box>
        </Card>

        <Card>
          <Box p="4">
            <Text size="2" color="gray" mb="1">Clicks</Text>
            <Text size="6" weight="bold">{formatNumber(analytics.total_clicks)}</Text>
          </Box>
        </Card>

        <Card>
          <Box p="4">
            <Text size="2" color="gray" mb="1">Conversions</Text>
            <Text size="6" weight="bold">{analytics.total_conversions}</Text>
          </Box>
        </Card>
      </Grid>

      {/* Performance Metrics */}
      <Grid columns={{ initial: '1', md: '2' }} gap="4" mb="6">
        <Card>
          <Box p="4">
            <Text size="3" weight="bold" mb="3">Engagement Metrics</Text>
            <Flex direction="column" gap="3">
              <Flex justify="between" align="center">
                <Text size="2" color="gray">Average CTR</Text>
                <Text size="3" weight="bold">{analytics.avg_ctr.toFixed(2)}%</Text>
              </Flex>
              <Flex justify="between" align="center">
                <Text size="2" color="gray">Average CPC</Text>
                <Text size="3" weight="bold">{formatCurrency(analytics.avg_cpc)}</Text>
              </Flex>
              <Flex justify="between" align="center">
                <Text size="2" color="gray">Average CPM</Text>
                <Text size="3" weight="bold">{formatCurrency(analytics.avg_cpm)}</Text>
              </Flex>
            </Flex>
          </Box>
        </Card>

        <Card>
          <Box p="4">
            <Text size="3" weight="bold" mb="3">Conversion Metrics</Text>
            <Flex direction="column" gap="3">
              <Flex justify="between" align="center">
                <Text size="2" color="gray">Conversion Rate</Text>
                <Text size="3" weight="bold">{analytics.avg_conversion_rate.toFixed(2)}%</Text>
              </Flex>
              <Flex justify="between" align="center">
                <Text size="2" color="gray">Average ROAS</Text>
                <Text size="3" weight="bold">{analytics.avg_roas.toFixed(2)}x</Text>
              </Flex>
              <Flex justify="between" align="center">
                <Text size="2" color="gray">Total Reach</Text>
                <Text size="3" weight="bold">{formatNumber(analytics.total_reach)}</Text>
              </Flex>
            </Flex>
          </Box>
        </Card>
      </Grid>

      {/* Top Performing Campaigns */}
      {analytics.top_performing_campaigns.length > 0 && (
        <Card>
          <Box p="4">
            <Text size="3" weight="bold" mb="3">Top Performing Campaigns</Text>
            <Flex direction="column" gap="2">
              {analytics.top_performing_campaigns.map((campaign, index) => (
                <Flex key={campaign.id} justify="between" align="center" p="2" style={{
                  backgroundColor: index % 2 === 0 ? 'var(--gray-2)' : 'transparent',
                  borderRadius: 4
                }}>
                  <Box>
                    <Text size="2" weight="bold">{campaign.name}</Text>
                    <Text size="1" color="gray">{campaign.conversions} conversions</Text>
                  </Box>
                  <Box style={{ textAlign: 'right' }}>
                    <Text size="2" weight="bold" color="green">{campaign.roas.toFixed(2)}x ROAS</Text>
                    <Text size="1" color="gray">{formatCurrency(campaign.spend)} spent</Text>
                  </Box>
                </Flex>
              ))}
            </Flex>
          </Box>
        </Card>
      )}
    </Box>
  );
};

export default FacebookAnalyticsDashboard; 
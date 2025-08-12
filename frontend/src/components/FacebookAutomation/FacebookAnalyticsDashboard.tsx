import { useState, useEffect } from 'react';
import { Box, Flex, Text, Card, Grid, Select, Heading } from '@radix-ui/themes';
import { 
  LineChart, Line, AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';
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
  demographics_breakdown?: {
    age: Record<string, number>;
    gender: Record<string, number>;
  };
  device_breakdown?: Record<string, number>;
  time_series?: Array<{
    date: string;
    impressions: number;
    clicks: number;
    spend: number;
    conversions: number;
  }>;
}

interface FacebookAnalyticsDashboardProps {
  clientId: string | null;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

const FacebookAnalyticsDashboard: React.FC<FacebookAnalyticsDashboardProps> = ({ clientId }) => {
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(false);
  const [timeframe, setTimeframe] = useState('last_7_days');

  useEffect(() => {
    if (clientId) {
      fetchAnalytics();
    }
  }, [clientId, timeframe]);

  const fetchAnalytics = async () => {
    if (!clientId) return;
    
    try {
      setLoading(true);
      const response = await api.post('/api/facebook-automation/analytics', {
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

  // Generate mock time series data if not provided
  const generateTimeSeriesData = () => {
    const days = timeframe === 'last_7_days' ? 7 : 30;
    const data = [];
    for (let i = days - 1; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      data.push({
        date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        impressions: Math.floor(Math.random() * 50000) + 10000,
        clicks: Math.floor(Math.random() * 1000) + 200,
        spend: Math.floor(Math.random() * 200) + 50,
        conversions: Math.floor(Math.random() * 20) + 5
      });
    }
    return data;
  };

  // Prepare data for charts
  const timeSeriesData = analytics?.time_series || generateTimeSeriesData();
  
  const demographicsData = analytics?.demographics_breakdown?.age ? 
    Object.entries(analytics.demographics_breakdown.age).map(([age, percentage]) => ({
      name: age,
      value: percentage
    })) : [
      { name: '25-34', value: 35 },
      { name: '35-44', value: 40 },
      { name: '45-54', value: 20 },
      { name: '55+', value: 5 }
    ];

  const deviceData = analytics?.device_breakdown ?
    Object.entries(analytics.device_breakdown).map(([device, percentage]) => ({
      name: device.charAt(0).toUpperCase() + device.slice(1),
      value: percentage
    })) : [
      { name: 'Mobile', value: 65 },
      { name: 'Desktop', value: 30 },
      { name: 'Tablet', value: 5 }
    ];

  if (!clientId) {
    return (
      <Card>
        <Box p="6" style={{ textAlign: 'center' }}>
          <Text size="3" color="gray">Select a client to view analytics</Text>
        </Box>
      </Card>
    );
  }

  if (loading) {
    return (
      <Card>
        <Box p="6" style={{ textAlign: 'center' }}>
          <Text size="3">Loading analytics...</Text>
        </Box>
      </Card>
    );
  }

  return (
    <Box>
      {/* Time Period Selector */}
      <Flex justify="between" align="center" mb="4">
        <Heading size="5">Performance Overview</Heading>
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

      {/* Key Metrics Cards */}
      <Grid columns="4" gap="4" mb="6">
        <Card>
          <Box p="4">
            <Text size="2" color="gray">Total Spend</Text>
            <Heading size="6">{formatCurrency(analytics?.total_spend || 0)}</Heading>
          </Box>
        </Card>
        <Card>
          <Box p="4">
            <Text size="2" color="gray">Total Impressions</Text>
            <Heading size="6">{formatNumber(analytics?.total_impressions || 0)}</Heading>
          </Box>
        </Card>
        <Card>
          <Box p="4">
            <Text size="2" color="gray">Total Clicks</Text>
            <Heading size="6">{formatNumber(analytics?.total_clicks || 0)}</Heading>
          </Box>
        </Card>
        <Card>
          <Box p="4">
            <Text size="2" color="gray">Total Conversions</Text>
            <Heading size="6">{analytics?.total_conversions || 0}</Heading>
          </Box>
        </Card>
      </Grid>

      {/* Average Metrics */}
      <Grid columns="4" gap="4" mb="6">
        <Card>
          <Box p="4">
            <Text size="2" color="gray">Avg CTR</Text>
            <Heading size="6">{(analytics?.avg_ctr || 0).toFixed(2)}%</Heading>
          </Box>
        </Card>
        <Card>
          <Box p="4">
            <Text size="2" color="gray">Avg CPC</Text>
            <Heading size="6">{formatCurrency(analytics?.avg_cpc || 0)}</Heading>
          </Box>
        </Card>
        <Card>
          <Box p="4">
            <Text size="2" color="gray">Avg CPM</Text>
            <Heading size="6">{formatCurrency(analytics?.avg_cpm || 0)}</Heading>
          </Box>
        </Card>
        <Card>
          <Box p="4">
            <Text size="2" color="gray">Avg ROAS</Text>
            <Heading size="6">{(analytics?.avg_roas || 0).toFixed(1)}x</Heading>
          </Box>
        </Card>
      </Grid>

      {/* Performance Trend Chart */}
      <Card mb="6">
        <Box p="4">
          <Heading size="4" mb="4">Performance Trends</Heading>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={timeSeriesData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Legend />
              <Line yAxisId="left" type="monotone" dataKey="impressions" stroke="#8884d8" name="Impressions" />
              <Line yAxisId="left" type="monotone" dataKey="clicks" stroke="#82ca9d" name="Clicks" />
              <Line yAxisId="right" type="monotone" dataKey="spend" stroke="#ffc658" name="Spend ($)" />
            </LineChart>
          </ResponsiveContainer>
        </Box>
      </Card>

      <Grid columns="2" gap="4" mb="6">
        {/* Demographics Chart */}
        <Card>
          <Box p="4">
            <Heading size="4" mb="4">Age Demographics</Heading>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={demographicsData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({name, value}) => `${name}: ${value}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {demographicsData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Box>
        </Card>

        {/* Device Breakdown */}
        <Card>
          <Box p="4">
            <Heading size="4" mb="4">Device Usage</Heading>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={deviceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip formatter={(value) => `${value}%`} />
                <Bar dataKey="value" fill="#82ca9d" />
              </BarChart>
            </ResponsiveContainer>
          </Box>
        </Card>
      </Grid>

      {/* Top Performing Campaigns */}
      {analytics?.top_performing_campaigns && analytics.top_performing_campaigns.length > 0 && (
        <Card>
          <Box p="4">
            <Heading size="4" mb="4">Top Performing Campaigns</Heading>
            <Flex direction="column" gap="3">
              {analytics.top_performing_campaigns.map((campaign) => (
                <Flex key={campaign.id} justify="between" align="center" p="3" style={{ backgroundColor: 'var(--gray-2)', borderRadius: 4 }}>
                  <Box>
                    <Text size="3" weight="bold">{campaign.name}</Text>
                    <Text size="2" color="gray">
                      {campaign.conversions} conversions • {formatCurrency(campaign.spend)} spent
                    </Text>
                  </Box>
                  <Box style={{ textAlign: 'right' }}>
                    <Text size="4" weight="bold" color="green">
                      {campaign.roas.toFixed(1)}x ROAS
                    </Text>
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
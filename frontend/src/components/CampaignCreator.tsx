import React, { useState, useEffect } from 'react';
import {
  Box, Card, Flex, Text, Heading, Button, TextField,
  Select, TextArea, Badge, Tabs, Callout, Checkbox
} from '@radix-ui/themes';
import {
  CalendarIcon, MagicWandIcon, RocketIcon,
  FileTextIcon, PersonIcon, CheckIcon
} from '@radix-ui/react-icons';
import { DatePicker } from './DatePicker';
import api from '../services/campaignApi';

interface Client {
  id: string;
  name: string;
  company: string;
  industry?: string;
  brand_voice?: string;
}

interface Platform {
  id: string;
  name: string;
  icon: React.ReactNode;
  selected: boolean;
}

const AVAILABLE_PLATFORMS: Platform[] = [
  { id: 'facebook', name: 'Facebook', icon: '📘', selected: true },
  { id: 'linkedin', name: 'LinkedIn', icon: '💼', selected: true },
  { id: 'twitter', name: 'Twitter', icon: '🐦', selected: false },
  { id: 'instagram', name: 'Instagram', icon: '📷', selected: false },
  { id: 'email', name: 'Email', icon: '📧', selected: true }
];

export const CampaignCreator: React.FC = () => {
  const [step, setStep] = useState(1);
  const [clients, setClients] = useState<Client[]>([]);
  const [selectedClient, setSelectedClient] = useState<string>('');
  const [campaignName, setCampaignName] = useState('');
  const [campaignDescription, setCampaignDescription] = useState('');
  const [topics, setTopics] = useState<string[]>(['', '', '', '', '']);
  const [platforms, setPlatforms] = useState(AVAILABLE_PLATFORMS);
  const [startDate, setStartDate] = useState<Date>(new Date());
  const [endDate, setEndDate] = useState<Date>(
    new Date(Date.now() + 30 * 24 * 60 * 60 * 1000) // 30 days from now
  );
  const [isGenerating, setIsGenerating] = useState(false);

  useEffect(() => {
    fetchClients();
  }, []);

  const fetchClients = async () => {
    try {
      const response = await api.get('/clients');
      setClients(response.data);
    } catch (error) {
      console.error('Error fetching clients:', error);
    }
  };

  const handleTopicChange = (index: number, value: string) => {
    const newTopics = [...topics];
    newTopics[index] = value;
    setTopics(newTopics);
  };

  const togglePlatform = (platformId: string) => {
    setPlatforms(platforms.map(p =>
      p.id === platformId ? { ...p, selected: !p.selected } : p
    ));
  };

  const validateStep = (stepNumber: number): boolean => {
    switch (stepNumber) {
      case 1:
        return selectedClient !== '' && campaignName !== '';
      case 2:
        return topics.filter(t => t.trim() !== '').length > 0;
      case 3:
        return platforms.filter(p => p.selected).length > 0;
      default:
        return true;
    }
  };

  const handleCreateCampaign = async () => {
    setIsGenerating(true);

    try {
      const campaignData = {
        client_id: selectedClient,
        name: campaignName,
        description: campaignDescription,
        topics: topics.filter(t => t.trim() !== ''),
        platforms: platforms.filter(p => p.selected).map(p => p.id),
        start_date: startDate.toISOString(),
        end_date: endDate.toISOString()
      };

      const response = await api.post('/campaigns', campaignData);
      
      // Redirect to campaign detail page
      window.location.href = `/campaigns/${response.data.id}`;
    } catch (error) {
      console.error('Error creating campaign:', error);
      setIsGenerating(false);
    }
  };

  const renderStepContent = () => {
    switch (step) {
      case 1:
        return (
          <Box>
            <Heading size="4" mb="4">Client Selection & Campaign Details</Heading>
            
            <Flex direction="column" gap="4">
              <Box>
                <Text size="2" weight="medium" mb="2">Select Client</Text>
                <Select.Root value={selectedClient} onValueChange={setSelectedClient}>
                  <Select.Trigger placeholder="Choose a client..." />
                  <Select.Content>
                    {clients.map(client => (
                      <Select.Item key={client.id} value={client.id}>
                        <Flex align="center" gap="2">
                          <PersonIcon />
                          <Text>{client.name} - {client.company}</Text>
                        </Flex>
                      </Select.Item>
                    ))}
                  </Select.Content>
                </Select.Root>
              </Box>

              <Box>
                <Text size="2" weight="medium" mb="2">Campaign Name</Text>
                <TextField.Root
                  placeholder="e.g., Summer 2024 Product Launch"
                  value={campaignName}
                  onChange={(e) => setCampaignName(e.target.value)}
                />
              </Box>

              <Box>
                <Text size="2" weight="medium" mb="2">Description (Optional)</Text>
                <TextArea
                  placeholder="Brief description of the campaign goals..."
                  value={campaignDescription}
                  onChange={(e) => setCampaignDescription(e.target.value)}
                  rows={3}
                />
              </Box>

              <Flex gap="4">
                <Box style={{ flex: 1 }}>
                  <Text size="2" weight="medium" mb="2">Start Date</Text>
                  <DatePicker
                    selected={startDate}
                    onChange={setStartDate}
                    minDate={new Date()}
                  />
                </Box>
                <Box style={{ flex: 1 }}>
                  <Text size="2" weight="medium" mb="2">End Date</Text>
                  <DatePicker
                    selected={endDate}
                    onChange={setEndDate}
                    minDate={startDate}
                  />
                </Box>
              </Flex>
            </Flex>
          </Box>
        );

      case 2:
        return (
          <Box>
            <Heading size="4" mb="4">Campaign Topics</Heading>
            <Text size="2" color="gray" mb="4">
              Enter up to 5 topics for your campaign. The AI will generate content around these themes.
            </Text>
            
            <Flex direction="column" gap="3">
              {topics.map((topic, index) => (
                <Box key={index}>
                  <Text size="2" weight="medium" mb="2">Topic {index + 1}</Text>
                  <TextField.Root
                    placeholder={`e.g., ${
                      index === 0 ? 'Product features' :
                      index === 1 ? 'Customer testimonials' :
                      index === 2 ? 'Industry insights' :
                      index === 3 ? 'Company culture' :
                      'Special offers'
                    }`}
                    value={topic}
                    onChange={(e) => handleTopicChange(index, e.target.value)}
                  />
                </Box>
              ))}
            </Flex>
          </Box>
        );

      case 3:
        return (
          <Box>
            <Heading size="4" mb="4">Select Platforms</Heading>
            <Text size="2" color="gray" mb="4">
              Choose which platforms to generate content for.
            </Text>
            
            <Flex direction="column" gap="3">
              {platforms.map(platform => (
                <Card
                  key={platform.id}
                  style={{
                    cursor: 'pointer',
                    border: platform.selected ? '2px solid var(--accent-9)' : undefined
                  }}
                  onClick={() => togglePlatform(platform.id)}
                >
                  <Flex align="center" justify="between">
                    <Flex align="center" gap="3">
                      <Text size="5">{platform.icon}</Text>
                      <Text weight="medium">{platform.name}</Text>
                    </Flex>
                    <Checkbox checked={platform.selected} />
                  </Flex>
                </Card>
              ))}
            </Flex>
          </Box>
        );

      case 4:
        return (
          <Box>
            <Heading size="4" mb="4">Review & Generate</Heading>
            
            <Card mb="4">
              <Flex direction="column" gap="3">
                <Flex justify="between">
                  <Text weight="medium">Client:</Text>
                  <Text>{clients.find(c => c.id === selectedClient)?.company}</Text>
                </Flex>
                <Flex justify="between">
                  <Text weight="medium">Campaign:</Text>
                  <Text>{campaignName}</Text>
                </Flex>
                <Flex justify="between">
                  <Text weight="medium">Duration:</Text>
                  <Text>
                    {startDate.toLocaleDateString()} - {endDate.toLocaleDateString()}
                  </Text>
                </Flex>
                <Flex justify="between">
                  <Text weight="medium">Topics:</Text>
                  <Text>{topics.filter(t => t).length} topics</Text>
                </Flex>
                <Flex justify="between">
                  <Text weight="medium">Platforms:</Text>
                  <Flex gap="2">
                    {platforms.filter(p => p.selected).map(p => (
                      <Badge key={p.id}>{p.name}</Badge>
                    ))}
                  </Flex>
                </Flex>
              </Flex>
            </Card>

            <Callout.Root color="blue" mb="4">
              <Callout.Icon>
                <MagicWandIcon />
              </Callout.Icon>
              <Callout.Text>
                The AI will generate a complete month-long campaign with posts scheduled
                throughout the duration. Content will be created as drafts for your review.
              </Callout.Text>
            </Callout.Root>

            <Button
              size="3"
              onClick={handleCreateCampaign}
              disabled={isGenerating}
              style={{ width: '100%' }}
            >
              {isGenerating ? (
                <>Generating Campaign...</>
              ) : (
                <>
                  <RocketIcon />
                  Generate Campaign
                </>
              )}
            </Button>
          </Box>
        );
    }
  };

  return (
    <Box style={{ maxWidth: '800px', margin: '0 auto' }}>
      <Flex align="center" gap="4" mb="6">
        <MagicWandIcon width="32" height="32" />
        <Heading size="6">Create Marketing Campaign</Heading>
      </Flex>

      {/* Progress Steps */}
      <Flex gap="2" mb="6">
        {[1, 2, 3, 4].map(num => (
          <Flex
            key={num}
            align="center"
            gap="2"
            style={{
              flex: 1,
              opacity: step >= num ? 1 : 0.5
            }}
          >
            <Badge
              size="2"
              variant={step === num ? 'solid' : 'soft'}
              radius="full"
            >
              {step > num ? <CheckIcon /> : num}
            </Badge>
            <Text size="2" weight={step === num ? 'bold' : 'regular'}>
              {num === 1 ? 'Client' :
               num === 2 ? 'Topics' :
               num === 3 ? 'Platforms' :
               'Review'}
            </Text>
          </Flex>
        ))}
      </Flex>

      <Card size="3">
        {renderStepContent()}

        <Flex justify="between" mt="6">
          <Button
            variant="soft"
            onClick={() => setStep(step - 1)}
            disabled={step === 1}
          >
            Previous
          </Button>
          
          {step < 4 ? (
            <Button
              onClick={() => setStep(step + 1)}
              disabled={!validateStep(step)}
            >
              Next
            </Button>
          ) : null}
        </Flex>
      </Card>
    </Box>
  );
}; 
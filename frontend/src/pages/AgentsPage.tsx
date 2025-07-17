import { useState } from 'react';
import { Box, Flex, Text, Heading, Card, Grid } from '@radix-ui/themes';
import { ArrowLeftIcon } from '@radix-ui/react-icons';
import { GeneratorWorkflow } from '../components/GeneratorWorkflow';
import { RealtorImporterWorkflow } from '../components/RealtorImporter/RealtorImporterWorkflow';
import { TemplateAgentCreator } from '../components/TemplateAgentCreator';
import { VideoClipExtractorWorkflow } from '../components/VideoClipExtractor/VideoClipExtractorWorkflow';
import { MainLayout } from '../components/MainLayout';
import { useNavigate } from 'react-router-dom';

// Define the structure for an agent
interface Agent {
  id: string;
  name: string;
  description: string;
  component: JSX.Element;
}

// Array of available agents
const agents: Agent[] = [
  {
    id: 'email-personalizer',
    name: '1-2-1 Email Personalizer',
    description: 'Upload a CSV to generate personalized emails at scale.',
    component: <GeneratorWorkflow />,
  },
  {
    id: 'realtor-importer',
    name: 'Realtor Contact Importer',
    description: 'Scrape realtor contact data from a homes.com search result page.',
    component: <RealtorImporterWorkflow />,
  },
  {
    id: 'template-creator',
    name: 'Template Agent Creator',
    description: 'Create custom template agents from example inputs and outputs.',
    component: <TemplateAgentCreator onBack={() => {}} onCreated={() => {}} />, // Will be properly connected below
  },
  {
    id: 'video-clip-extractor',
    name: 'AI Video Clip Extractor',
    description: 'Extract smart clips from promotional videos using AI vision analysis.',
    component: <VideoClipExtractorWorkflow />,
  },
  {
    id: 'pr-outreach',
    name: 'PR Outreach Agent',
    description: 'Create and distribute personalized press releases. (Coming Soon)',
    component: <Box p="4"><Text>This agent is under construction.</Text></Box>,
  },
];

const AgentsPage = () => {
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const navigate = useNavigate();

  const handleSelectAgent = (agentId: string) => {
    const agent = agents.find(a => a.id === agentId);
    if (agent && agent.id !== 'pr-outreach') {
      setSelectedAgent(agent);
    } else if (agent?.id === 'pr-outreach') {
      // Optionally, show an alert or do nothing for disabled agents
      alert('This agent is coming soon!');
    }
  };

  const handleGoBack = () => {
    setSelectedAgent(null);
  };

  const handleTemplateCreated = () => {
    // Show success message or redirect
    alert('Template agent created successfully! It will now appear in your chat interface.');
    setSelectedAgent(null);
  };

  // Clone the component with proper props for template creator
  const getAgentComponent = (agent: Agent) => {
    if (agent.id === 'template-creator') {
      return <TemplateAgentCreator onBack={handleGoBack} onCreated={handleTemplateCreated} />;
    }
    return agent.component;
  };

  return (
    <MainLayout onNewChat={() => navigate('/home')}>
      <Flex direction="column" style={{ height: '100%', backgroundColor: 'var(--gray-1)' }}>
        <Box style={{ padding: '1.5rem 2rem', borderBottom: '1px solid var(--gray-4)', backgroundColor: 'white' }}>
          {selectedAgent ? (
            <Flex align="center" gap="3">
              <button onClick={handleGoBack} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '0.5rem' }}>
                <ArrowLeftIcon width="24" height="24" />
              </button>
              <Box>
                <Heading size="7" style={{ color: 'var(--gray-12)' }}>{selectedAgent.name}</Heading>
                <Text as="p" size="3" style={{ color: 'var(--gray-10)', marginTop: '0.25rem' }}>
                  {selectedAgent.description}
                </Text>
              </Box>
            </Flex>
          ) : (
            <>
              <Heading size="7" style={{ color: 'var(--gray-12)' }}>Automation Agents</Heading>
              <Text as="p" size="3" style={{ color: 'var(--gray-10)', marginTop: '0.25rem' }}>
                Select an agent to begin an automated workflow.
              </Text>
            </>
          )}
        </Box>

        <Box style={{ padding: '2rem', flex: 1, overflowY: 'auto' }}>
          {selectedAgent ? (
            getAgentComponent(selectedAgent)
          ) : (
            <Grid columns={{ initial: '1', sm: '2', md: '3' }} gap="4">
              {agents.map(agent => (
                <Card 
                  key={agent.id} 
                  onClick={() => handleSelectAgent(agent.id)}
                  style={{ 
                    cursor: agent.id === 'pr-outreach' ? 'not-allowed' : 'pointer', 
                    transition: 'all 0.2s',
                    opacity: agent.id === 'pr-outreach' ? 0.6 : 1
                  }}
                  className="agent-card"
                >
                  <Flex direction="column" gap="2">
                    <Heading size="4">{agent.name}</Heading>
                    <Text size="2" color="gray">{agent.description}</Text>
                  </Flex>
                </Card>
              ))}
            </Grid>
          )}
        </Box>
      </Flex>
    </MainLayout>
  );
};

export default AgentsPage; 
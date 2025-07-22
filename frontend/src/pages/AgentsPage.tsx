import { useState } from 'react';
import { Box, Flex, Text, Heading, Card, Grid } from '@radix-ui/themes';
import { ArrowLeftIcon } from '@radix-ui/react-icons';
import { Mail, Home, Bot, Database, Search, Rocket } from 'lucide-react';
import { GeneratorWorkflow } from '../components/GeneratorWorkflow';
import { RealtorImporterWorkflow } from '../components/RealtorImporter/RealtorImporterWorkflow';
import { TemplateAgentCreator } from '../components/TemplateAgentCreator';
import { MainLayout } from '../components/MainLayout';
import { useNavigate } from 'react-router-dom';

// Define the structure for an agent
interface Agent {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  component: JSX.Element;
}

const iconProps = {
  style: { color: 'var(--gray-11)', width: '3rem', height: '3rem' },
};

// Array of available agents
const agents: Agent[] = [
  {
    id: 'email-personalize',
    name: 'Email Personalizer',
    description: 'Upload a CSV with contact data and generate personalized emails at scale using AI templates.',
    icon: <Mail {...iconProps} />,
    component: <GeneratorWorkflow />,
  },
  {
    id: 'realtor-importer',
    name: 'Realtor Data Importer',
    description: 'Scrape realtor profiles from Homes.com, enrich data, and prepare for email campaigns.',
    icon: <Home {...iconProps} />,
    component: <RealtorImporterWorkflow />,
  },
  {
    id: 'email-templates',
    name: 'Template Agent Manager',
    description: 'Create AI agents that learn from examples to generate custom templates.',
    icon: <Bot {...iconProps} />,
    component: <TemplateAgentCreator onBack={() => {}} onCreated={() => {}} />, // Will be properly connected below
  },
  {
    id: 'data-lake',
    name: 'Data Lake Manager',
    description: 'Manage your centralized database of contacts, import/export data, and maintain your CRM.',
    icon: <Database {...iconProps} />,
    component: <Box p="4"><Text>Redirecting to Data Lake...</Text></Box>, // Placeholder component
  },
  {
    id: 'contact-enricher',
    name: 'Contact Enricher',
    description: 'Enrich your contact lists with emails, phone numbers, and social media data from multiple sources.',
    icon: <Search {...iconProps} />,
    component: <Box p="4"><Text>Redirecting to Contact Enricher...</Text></Box>, // Placeholder component
  },
  {
    id: 'more-coming',
    name: 'More Agents Coming Soon',
    description: 'We\'re constantly building new AI agents to help automate your marketing workflows.',
    icon: <Rocket {...iconProps} />,
    component: <Box p="4"><Text>This agent is under construction.</Text></Box>,
  }
];

const AgentsPage = () => {
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const navigate = useNavigate();

  const handleSelectAgent = (agentId: string) => {
    const agent = agents.find(a => a.id === agentId);
    if (agent && agent.id === 'data-lake') {
      // Navigate to data lake page
      navigate('/data-lake');
    } else if (agent && agent.id === 'contact-enricher') {
      // Navigate to contact enricher page
      navigate('/contact-enricher');
    } else if (agent && agent.id !== 'more-coming') {
      setSelectedAgent(agent);
    } else if (agent?.id === 'more-coming') {
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
    if (agent.id === 'email-templates') {
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
                    cursor: agent.id === 'more-coming' ? 'not-allowed' : 'pointer', 
                    transition: 'all 0.2s',
                    opacity: agent.id === 'more-coming' ? 0.6 : 1
                  }}
                  className="agent-card"
                >
                  <Flex direction="column" gap="3">
                    <Box style={{ height: '3rem' }}>
                      {agent.icon}
                    </Box>
                    <Heading size="5">{agent.name}</Heading>
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
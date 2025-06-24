import { useState } from 'react';
import { Box, Flex, Text, Heading, Card, Grid } from '@radix-ui/themes';
import { ArrowLeftIcon } from '@radix-ui/react-icons';
import { GeneratorWorkflow } from '../components/GeneratorWorkflow';

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
    id: 'pr-outreach',
    name: 'PR Outreach Agent',
    description: 'Create and distribute personalized press releases. (Coming Soon)',
    component: <Box p="4"><Text>This agent is under construction.</Text></Box>,
  },
];

const AgentsPage = () => {
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);

  const handleSelectAgent = (agentId: string) => {
    const agent = agents.find(a => a.id === agentId);
    if (agent && agent.id !== 'pr-outreach') { // Disable PR agent for now
      setSelectedAgent(agent);
    } else {
      // Optionally, show an alert or do nothing for disabled agents
      alert('This agent is coming soon!');
    }
  };

  const handleGoBack = () => {
    setSelectedAgent(null);
  };

  return (
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
          selectedAgent.component
        ) : (
          <Grid columns={{ initial: '1', sm: '2', md: '3' }} gap="4">
            {agents.map(agent => (
              <Card 
                key={agent.id} 
                onClick={() => handleSelectAgent(agent.id)}
                style={{ cursor: 'pointer', transition: 'all 0.2s' }}
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
  );
};

export default AgentsPage; 
import React, { useState } from 'react';
import { Box, Flex, Text, Heading, TextArea, TextField, Button, Card } from '@radix-ui/themes';
import { ArrowLeftIcon } from '@radix-ui/react-icons';
import api from '../api';

interface TemplateAgentCreatorProps {
  onBack: () => void;
  onCreated: () => void;
}

export const TemplateAgentCreator = ({ onBack, onCreated }: TemplateAgentCreatorProps) => {
  const [name, setName] = useState('');
  const [exampleInput, setExampleInput] = useState('');
  const [exampleOutput, setExampleOutput] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState('');

  const handleCreate = async () => {
    if (!name.trim() || !exampleInput.trim() || !exampleOutput.trim()) {
      setError('Please fill in all fields');
      return;
    }

    setIsCreating(true);
    setError('');

    try {
      await api.post('/template-agents', {
        name,
        example_input: exampleInput,
        example_output: exampleOutput
      });

      // Success - notify parent and reset form
      onCreated();
      setName('');
      setExampleInput('');
      setExampleOutput('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create template agent');
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <Box style={{ height: '100%', backgroundColor: 'var(--gray-1)' }}>
      <Box style={{ padding: '1.5rem 2rem', borderBottom: '1px solid var(--gray-4)', backgroundColor: 'white' }}>
        <Flex align="center" gap="3">
          <button onClick={onBack} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '0.5rem' }}>
            <ArrowLeftIcon width="24" height="24" />
          </button>
          <Box>
            <Heading size="7" style={{ color: 'var(--gray-12)' }}>Create Template Agent</Heading>
            <Text as="p" size="3" style={{ color: 'var(--gray-10)', marginTop: '0.25rem' }}>
              Create a reusable template by providing an example
            </Text>
          </Box>
        </Flex>
      </Box>

      <Box style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
        <Flex direction="column" gap="5">
          <Card>
            <Flex direction="column" gap="3">
              <Box>
                <Text as="label" size="2" weight="bold" style={{ display: 'block', marginBottom: '0.5rem' }}>
                  Template Name
                </Text>
                <TextField.Root
                  placeholder="e.g., Welcome Email, Sales Pitch, Support Response"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </Box>

              <Box>
                <Text as="label" size="2" weight="bold" style={{ display: 'block', marginBottom: '0.5rem' }}>
                  Example Input
                </Text>
                <Text size="1" color="gray" style={{ display: 'block', marginBottom: '0.5rem' }}>
                  Paste an example of the input/questions a user would provide
                </Text>
                <TextArea
                  placeholder="What is your primary geographic market?
> The 7 county metro area and northern MN

Why would you like to host?
> Minnesota is a special place..."
                  value={exampleInput}
                  onChange={(e) => setExampleInput(e.target.value)}
                  rows={8}
                  style={{ fontFamily: 'monospace', fontSize: '13px' }}
                />
              </Box>

              <Box>
                <Text as="label" size="2" weight="bold" style={{ display: 'block', marginBottom: '0.5rem' }}>
                  Example Output
                </Text>
                <Text size="1" color="gray" style={{ display: 'block', marginBottom: '0.5rem' }}>
                  Paste an example of the desired output
                </Text>
                <TextArea
                  placeholder="Hi Chris,

Thank you for your enthusiastic response..."
                  value={exampleOutput}
                  onChange={(e) => setExampleOutput(e.target.value)}
                  rows={8}
                  style={{ fontFamily: 'monospace', fontSize: '13px' }}
                />
              </Box>

              {error && (
                <Text color="red" size="2">{error}</Text>
              )}

              <Flex gap="3" justify="end">
                <Button variant="soft" onClick={onBack} disabled={isCreating}>
                  Cancel
                </Button>
                <Button onClick={handleCreate} disabled={isCreating}>
                  {isCreating ? 'Creating...' : 'Create Template'}
                </Button>
              </Flex>
            </Flex>
          </Card>

          <Card>
            <Heading size="3" style={{ marginBottom: '1rem' }}>How it works</Heading>
            <Flex direction="column" gap="2">
              <Text size="2">
                1. <strong>Provide an example:</strong> Show the system what kind of input and output you want
              </Text>
              <Text size="2">
                2. <strong>AI learns the pattern:</strong> The system analyzes your example to understand the structure and style
              </Text>
              <Text size="2">
                3. <strong>Template is created:</strong> A reusable template is generated that others can use
              </Text>
              <Text size="2">
                4. <strong>Use in chat:</strong> The template appears in the chat interface for easy access
              </Text>
            </Flex>
          </Card>
        </Flex>
      </Box>
    </Box>
  );
}; 
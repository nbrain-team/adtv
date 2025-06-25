import { useState, useEffect, useMemo } from 'react';
import { Box, Flex, Button, TextField, Text, Heading, Card, Table, Callout, Badge } from '@radix-ui/themes';
import { InfoCircledIcon } from '@radix-ui/react-icons';
import api from '../../api';

// Define types based on backend schemas
interface RealtorContact {
  id: string;
  first_name: string | null;
  last_name: string | null;
  company: string | null;
  city: string | null;
  state: string | null;
  cell_phone: string | null;
  email: string | null;
}

interface ScrapingJob {
  id: string;
  start_url: string;
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED';
  created_at: string;
  contact_count: number;
  realtor_contacts?: RealtorContact[];
}

const statusColors: { [key in ScrapingJob['status']]: 'gray' | 'blue' | 'green' | 'red' } = {
    PENDING: 'gray',
    IN_PROGRESS: 'blue',
    COMPLETED: 'green',
    FAILED: 'red',
};

export const RealtorImporterWorkflow = () => {
  const [jobs, setJobs] = useState<ScrapingJob[]>([]);
  const [selectedJob, setSelectedJob] = useState<ScrapingJob | null>(null);
  const [newUrl, setNewUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchJobs = async () => {
    try {
      const response = await api.get('/realtor-importer/');
      setJobs(response.data);
    } catch (err) {
      setError('Failed to fetch scraping jobs.');
    }
  };

  const fetchJobDetails = async (jobId: string) => {
    try {
      const response = await api.get(`/realtor-importer/${jobId}`);
      setSelectedJob(response.data);
      // Also update the job list with the new details
      setJobs(prevJobs => prevJobs.map(j => j.id === jobId ? { ...j, status: response.data.status, contact_count: response.data.realtor_contacts.length } : j));
    } catch (err) {
      setError('Failed to fetch job details.');
    }
  };
  
  // Polling mechanism
  useEffect(() => {
    fetchJobs(); // Initial fetch
    const interval = setInterval(() => {
        fetchJobs(); // Refresh job list
        if (selectedJob) {
            // If a job is selected, refresh its details too
            fetchJobDetails(selectedJob.id);
        }
    }, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, [selectedJob?.id]); // Rerun if selected job changes

  const handleCreateJob = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    try {
      await api.post('/realtor-importer/', { url: newUrl });
      setNewUrl('');
      fetchJobs(); // Refresh list immediately
    } catch (err) {
      setError('Failed to start new job. Please check the URL and try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const activeJob = useMemo(() => jobs.find(j => j.status === 'IN_PROGRESS'), [jobs]);

  return (
    <Flex gap="5">
      <Box width="35%">
        <Heading size="5" mb="3">Scraping Jobs</Heading>
        <Card>
            <form onSubmit={handleCreateJob}>
            <Flex direction="column" gap="3">
                <TextField.Root 
                    placeholder="Enter homes.com search URL..." 
                    value={newUrl}
                    onChange={(e) => setNewUrl(e.target.value)}
                    disabled={!!activeJob}
                />
                <Button disabled={isLoading || !!activeJob}>
                    {isLoading ? 'Starting...' : 'Start New Scrape'}
                </Button>
            </Flex>
            </form>
            {activeJob && (
                <Callout.Root color="blue" mt="3">
                    <Callout.Icon><InfoCircledIcon /></Callout.Icon>
                    <Callout.Text>A job is currently in progress. Please wait for it to complete before starting a new one.</Callout.Text>
                </Callout.Root>
            )}
        </Card>
        
        <Flex direction="column" gap="3" mt="4">
            {jobs.map(job => (
                <Card key={job.id} onClick={() => fetchJobDetails(job.id)} style={{cursor: 'pointer'}}>
                    <Flex justify="between">
                        <Text size="2" weight="bold" truncate>{job.start_url}</Text>
                        <Badge color={statusColors[job.status]}>{job.status}</Badge>
                    </Flex>
                    <Flex justify="between" mt="2">
                        <Text size="1" color="gray">Contacts: {job.contact_count}</Text>
                        <Text size="1" color="gray">{new Date(job.created_at).toLocaleString()}</Text>
                    </Flex>
                </Card>
            ))}
        </Flex>
      </Box>

      <Box width="65%">
        <Heading size="5" mb="3">Job Details</Heading>
        {selectedJob ? (
            <Card>
                <Table.Root variant="surface">
                    <Table.Header>
                        <Table.Row>
                            <Table.ColumnHeaderCell>Name</Table.ColumnHeaderCell>
                            <Table.ColumnHeaderCell>Company</Table.ColumnHeaderCell>
                            <Table.ColumnHeaderCell>Location</Table.ColumnHeaderCell>
                            <Table.ColumnHeaderCell>Contact</Table.ColumnHeaderCell>
                        </Table.Row>
                    </Table.Header>
                    <Table.Body>
                        {selectedJob.realtor_contacts?.map(contact => (
                            <Table.Row key={contact.id}>
                                <Table.Cell>{contact.first_name} {contact.last_name}</Table.Cell>
                                <Table.Cell>{contact.company}</Table.Cell>
                                <Table.Cell>{contact.city}, {contact.state}</Table.Cell>
                                <Table.Cell>{contact.cell_phone || contact.email || 'N/A'}</Table.Cell>
                            </Table.Row>
                        ))}
                    </Table.Body>
                </Table.Root>
            </Card>
        ) : (
            <Card>
                <Text>Select a job on the left to see its details.</Text>
            </Card>
        )}
      </Box>
    </Flex>
  );
}; 
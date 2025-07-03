import { useState, useEffect, useMemo } from 'react';
import { Box, Flex, Button, TextField, Text, Heading, Card, Table, Callout, Badge } from '@radix-ui/themes';
import { InfoCircledIcon, ExclamationTriangleIcon } from '@radix-ui/react-icons';
import api from '../../api';
import SalesFilter from './SalesFilter';

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
  agent_website: string | null;
  profile_url: string | null;
  dma: string | null;
  source: string | null;
  years_exp: number | null;
  fb_or_website: string | null;
  seller_deals_total_deals: number | null;
  seller_deals_total_value: number | null;
  seller_deals_avg_price: number | null;
  buyer_deals_total_deals: number | null;
  buyer_deals_total_value: number | null;
  buyer_deals_avg_price: number | null;
}

interface ScrapingJob {
  id: string;
  start_url: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
  contact_count: number;
  error_message?: string | null;
  realtor_contacts?: RealtorContact[];
}

const statusColors: { [key in ScrapingJob['status']]: 'gray' | 'blue' | 'green' | 'red' } = {
    pending: 'gray',
    processing: 'blue',
    completed: 'green',
    failed: 'red',
};

const statusLabels: { [key in ScrapingJob['status']]: string } = {
    pending: 'Pending',
    processing: 'Processing',
    completed: 'Completed',
    failed: 'Failed',
};

export const RealtorImporterWorkflow = () => {
  const [jobs, setJobs] = useState<ScrapingJob[]>([]);
  const [selectedJob, setSelectedJob] = useState<ScrapingJob | null>(null);
  const [newUrl, setNewUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Helper function to format currency
  const formatCurrency = (value: number | null | undefined): string => {
    if (!value) return 'N/A';
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(1)}M`;
    } else if (value >= 1000) {
      return `$${(value / 1000).toFixed(0)}K`;
    }
    return `$${value}`;
  };

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
      setJobs(prevJobs => prevJobs.map(j => 
        j.id === jobId 
          ? { ...j, status: response.data.status, contact_count: response.data.realtor_contacts?.length || 0 } 
          : j
      ));
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
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to start new job. Please check the URL and try again.';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteJob = async (jobId: string, e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent selecting the job
    if (window.confirm('Are you sure you want to delete this job?')) {
      try {
        await api.delete(`/realtor-importer/${jobId}`);
        fetchJobs();
        if (selectedJob?.id === jobId) {
          setSelectedJob(null);
        }
      } catch (err) {
        setError('Failed to delete job.');
      }
    }
  };

  const activeJob = useMemo(() => jobs.find(j => j.status === 'processing' || j.status === 'pending'), [jobs]);

  return (
    <div>
      <Box mb="4">
        <SalesFilter />
      </Box>
      
      {/* Scraper Section */}
      <Box mb="4">
        <Heading size="5" mb="3">Realtor Scraping Jobs</Heading>
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
                <Callout.Root color="blue">
                    <Callout.Icon><InfoCircledIcon /></Callout.Icon>
                    <Callout.Text size="1">Each scraping job is limited to 25 profiles maximum to ensure reliable performance.</Callout.Text>
                </Callout.Root>
            </Flex>
            </form>
            {activeJob && (
                <Callout.Root color="blue" mt="3">
                    <Callout.Icon><InfoCircledIcon /></Callout.Icon>
                    <Callout.Text>A job is currently in progress. Please wait for it to complete before starting a new one.</Callout.Text>
                </Callout.Root>
            )}
            {error && (
                <Callout.Root color="red" mt="3">
                    <Callout.Icon><ExclamationTriangleIcon /></Callout.Icon>
                    <Callout.Text>{error}</Callout.Text>
                </Callout.Root>
            )}
        </Card>
      </Box>

      {/* Jobs List Section */}
      <Flex gap="5" mb="4">
        <Box width="100%">
          <Heading size="4" mb="3">Scraping History</Heading>
          <Flex direction="row" gap="3" wrap="wrap">
              {jobs.map(job => (
                  <Card 
                    key={job.id} 
                    onClick={() => fetchJobDetails(job.id)} 
                    style={{cursor: 'pointer', position: 'relative', minWidth: '300px', flex: '0 0 calc(33.333% - 16px)'}}
                  >
                      <Flex justify="between">
                          <Text size="2" weight="bold" truncate style={{maxWidth: '70%'}}>
                            {job.start_url}
                          </Text>
                          <Badge color={statusColors[job.status]}>
                            {statusLabels[job.status]}
                          </Badge>
                      </Flex>
                      <Flex justify="between" mt="2">
                          <Text size="1" color="gray">Contacts: {job.contact_count}</Text>
                          <Text size="1" color="gray">{new Date(job.created_at).toLocaleString()}</Text>
                      </Flex>
                      {job.status === 'processing' && (
                          <Text size="1" color="blue" mt="1">
                              Scraping up to 25 profiles...
                          </Text>
                      )}
                      <Button 
                        size="1" 
                        color="red" 
                        variant="ghost"
                        onClick={(e) => handleDeleteJob(job.id, e)}
                        style={{position: 'absolute', top: '8px', right: '8px'}}
                      >
                        Delete
                      </Button>
                  </Card>
              ))}
          </Flex>
        </Box>
      </Flex>

      {/* Job Details Section */}
      <Box width="100%">
        <Heading size="5" mb="3">Job Details</Heading>
        {selectedJob ? (
            <Card>
                {selectedJob.error_message && (
                    <Callout.Root color="red" mb="3">
                        <Callout.Icon><ExclamationTriangleIcon /></Callout.Icon>
                        <Callout.Text>Error: {selectedJob.error_message}</Callout.Text>
                    </Callout.Root>
                )}
                {selectedJob.status === 'completed' && selectedJob.realtor_contacts && selectedJob.realtor_contacts.length > 0 && (
                    <Flex justify="between" align="center" mb="3">
                        <Text size="2" weight="bold">
                            Found {selectedJob.realtor_contacts.length} contacts
                            {selectedJob.realtor_contacts.length === 25 && ' (limit reached)'}
                        </Text>
                    </Flex>
                )}
                <Box style={{ overflowX: 'auto' }}>
                  <Table.Root variant="surface" size="1">
                      <Table.Header>
                          <Table.Row>
                              <Table.ColumnHeaderCell>Name</Table.ColumnHeaderCell>
                              <Table.ColumnHeaderCell>Company</Table.ColumnHeaderCell>
                              <Table.ColumnHeaderCell>Location</Table.ColumnHeaderCell>
                              <Table.ColumnHeaderCell>Phone</Table.ColumnHeaderCell>
                              <Table.ColumnHeaderCell>Email</Table.ColumnHeaderCell>
                              <Table.ColumnHeaderCell>Agent Website</Table.ColumnHeaderCell>
                              <Table.ColumnHeaderCell>Seller Value</Table.ColumnHeaderCell>
                              <Table.ColumnHeaderCell>HC Profile</Table.ColumnHeaderCell>
                          </Table.Row>
                      </Table.Header>
                      <Table.Body>
                          {selectedJob.realtor_contacts?.map(contact => (
                              <Table.Row key={contact.id}>
                                  <Table.Cell>{contact.first_name} {contact.last_name}</Table.Cell>
                                  <Table.Cell>{contact.company || 'N/A'}</Table.Cell>
                                  <Table.Cell>{contact.city}, {contact.state}</Table.Cell>
                                  <Table.Cell>{contact.cell_phone || 'N/A'}</Table.Cell>
                                  <Table.Cell>{contact.email || 'N/A'}</Table.Cell>
                                  <Table.Cell>
                                      {contact.agent_website ? (
                                          <a href={contact.agent_website} target="_blank" rel="noopener noreferrer">
                                              View Website
                                          </a>
                                      ) : 'N/A'}
                                  </Table.Cell>
                                  <Table.Cell>{formatCurrency(contact.seller_deals_total_value)}</Table.Cell>
                                  <Table.Cell>
                                      {contact.profile_url && (
                                          <a href={contact.profile_url} target="_blank" rel="noopener noreferrer">
                                              View Profile
                                          </a>
                                      )}
                                  </Table.Cell>
                              </Table.Row>
                          ))}
                      </Table.Body>
                  </Table.Root>
                </Box>
                {selectedJob.realtor_contacts?.length === 0 && (
                    <Text size="2" color="gray" style={{display: 'block', textAlign: 'center', padding: '2rem'}}>
                        {selectedJob.status === 'completed' 
                            ? 'No contacts found for this search.'
                            : 'Contacts will appear here once scraping is complete.'}
                    </Text>
                )}
            </Card>
        ) : (
            <Card>
                <Text>Select a job above to see its details.</Text>
            </Card>
        )}
      </Box>
    </div>
  );
}; 
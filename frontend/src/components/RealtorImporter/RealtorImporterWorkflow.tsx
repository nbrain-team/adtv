import { useState, useEffect, useMemo } from 'react';
import { Box, Flex, Button, TextField, Text, Heading, Card, Table, Callout, Badge, Checkbox, Dialog } from '@radix-ui/themes';
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
  phone2: string | null;
  personal_email: string | null;
  facebook_profile: string | null;
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
  name?: string | null;
  start_url: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  created_at: string;
  contact_count: number;
  error_message?: string | null;
  realtor_contacts?: RealtorContact[];
}

const statusColors: { [key in ScrapingJob['status']]: 'gray' | 'blue' | 'green' | 'red' | 'orange' } = {
    pending: 'gray',
    processing: 'blue',
    completed: 'green',
    failed: 'red',
    cancelled: 'orange',
};

const statusLabels: { [key in ScrapingJob['status']]: string } = {
    pending: 'Pending',
    processing: 'Processing',
    completed: 'Completed',
    failed: 'Failed',
    cancelled: 'Cancelled',
};

export const RealtorImporterWorkflow = () => {
  const [jobs, setJobs] = useState<ScrapingJob[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [newUrl, setNewUrl] = useState('');
  const [newJobName, setNewJobName] = useState('');  // Add state for job name
  const [selectedJob, setSelectedJob] = useState<ScrapingJob | null>(null);
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedJobs, setSelectedJobs] = useState<string[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processedJobId, setProcessedJobId] = useState<string | null>(null);
  const [showProcessedModal, setShowProcessedModal] = useState(false);
  const [processedJobDetails, setProcessedJobDetails] = useState<any>(null);

  // Get completed jobs for selection
  const completedJobs = useMemo(() => 
    jobs.filter(job => job.status === 'completed').map(job => job.id),
    [jobs]
  );

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
    if (!newUrl) return;

    setIsLoading(true);
    try {
      const response = await api.post('/realtor-importer/', { 
        url: newUrl,
        name: newJobName || null  // Include the name in the request
      });
      setNewUrl('');
      setNewJobName('');  // Clear the name field
      fetchJobs();
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to start new job. Please check the URL and try again.';
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

  const handleStopJob = async (jobId: string, e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent selecting the job
    if (window.confirm('Are you sure you want to stop this job? Already scraped data will be kept.')) {
      try {
        await api.post(`/realtor-importer/${jobId}/stop`);
        fetchJobs();
        fetchJobDetails(jobId); // Refresh the details to show cancelled status
      } catch (err) {
        setError('Failed to stop job.');
      }
    }
  };

  const handleSelectAll = (checked: boolean | 'indeterminate') => {
    if (checked === true) {
      setSelectedJobs(completedJobs);
    } else {
      setSelectedJobs([]);
    }
  };

  const handleJobSelection = (jobId: string, checked: boolean) => {
    setSelectedJobs(prev => {
      if (checked) {
        return [...prev, jobId];
      } else {
        return prev.filter(id => id !== jobId);
      }
    });
  };

  const handleProcessJobs = async () => {
    if (selectedJobs.length === 0) return;
    setIsProcessing(true);
    try {
      const response = await api.post('/realtor-importer/process-selected', { job_ids: selectedJobs });
      setProcessedJobId(response.data.id);
      setSelectedJobs([]); // Clear selected jobs after processing
      fetchJobs(); // Refresh job list
      
      // Start polling for processed job status
      pollProcessedJob(response.data.id);
    } catch (err) {
      setError('Failed to process selected jobs.');
    } finally {
      setIsProcessing(false);
    }
  };
  
  const pollProcessedJob = async (jobId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await api.get(`/realtor-importer/processed/${jobId}`);
        setProcessedJobDetails(response.data);
        
        if (response.data.status === 'COMPLETED' || response.data.status === 'FAILED') {
          clearInterval(pollInterval);
          setShowProcessedModal(true);
        }
      } catch (err) {
        clearInterval(pollInterval);
        setError('Failed to fetch processed job details.');
      }
    }, 2000); // Poll every 2 seconds
  };
  
  const handlePersonalizeEmails = async () => {
    if (!processedJobId) return;
    
    try {
      const response = await api.post(`/realtor-importer/processed/${processedJobId}/personalize-emails`);
      
      // Create a Blob from the CSV data
      const blob = new Blob([response.data.csv_data], { type: 'text/csv' });
      const file = new File([blob], 'processed_contacts.csv', { type: 'text/csv' });
      
      // Store the file data in sessionStorage to pass to the email personalizer
      const reader = new FileReader();
      reader.onload = (e) => {
        sessionStorage.setItem('emailPersonalizerData', JSON.stringify({
          fileName: 'processed_contacts.csv',
          fileContent: e.target?.result,
          fromRealtorImporter: true
        }));
        
        // Navigate to the email personalizer
        window.location.href = '/agents?agent=email-personalizer';
      };
      reader.readAsText(file);
      
    } catch (err) {
      setError('Failed to prepare emails for personalization.');
    }
  };

  const activeJob = useMemo(() => jobs.find(j => j.status === 'processing' || j.status === 'pending'), [jobs]);

  return (
    <div>
      <Box mb="4">
        <SalesFilter />
      </Box>
      
      {/* Scraper Section */}
      <Box mb="4" style={{ maxWidth: '700px' }}>
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
                <TextField.Root 
                    placeholder="Optional: Name your job" 
                    value={newJobName}
                    onChange={(e) => setNewJobName(e.target.value)}
                    disabled={!!activeJob}
                />
                <Button disabled={isLoading || !!activeJob}>
                    {isLoading ? 'Starting...' : 'Start New Scrape'}
                </Button>
                <Callout.Root color="blue">
                    <Callout.Icon><InfoCircledIcon /></Callout.Icon>
                    <Callout.Text size="1">Each scraping job can process up to 700 profiles. Results are displayed in batches of 50 as they're scraped.</Callout.Text>
                </Callout.Root>
            </Flex>
            </form>
            {activeJob && (
                <Callout.Root color="blue" mt="3">
                    <Callout.Icon><InfoCircledIcon /></Callout.Icon>
                    <Callout.Text>
                        A job is currently in progress. 
                        {activeJob.contact_count > 0 && ` ${activeJob.contact_count} profiles scraped so far...`}
                        Please wait for it to complete before starting a new one.
                    </Callout.Text>
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
      <Box width="100%">
        <Flex justify="between" align="center" mb="3">
          <Heading size="4">Scraping History</Heading>
          {selectedJobs.length > 0 && (
            <Flex gap="2">
              <Text size="2" color="gray">{selectedJobs.length} selected</Text>
              <Button 
                size="2" 
                onClick={handleProcessJobs}
                disabled={selectedJobs.length < 2 || isProcessing}
              >
                {isProcessing ? 'Processing...' : 'Process Selected'}
              </Button>
            </Flex>
          )}
        </Flex>
        
        {jobs.length === 0 ? (
          <Card>
            <Text size="2" color="gray" style={{display: 'block', textAlign: 'center', padding: '2rem'}}>
              No scraping jobs yet. Start a new scrape above.
            </Text>
          </Card>
        ) : (
          <Card>
            <Table.Root variant="surface" size="2">
              <Table.Header>
                <Table.Row>
                  <Table.ColumnHeaderCell style={{width: '40px'}}>
                    <Checkbox 
                      checked={selectedJobs.length === completedJobs.length && completedJobs.length > 0}
                      onCheckedChange={handleSelectAll}
                    />
                  </Table.ColumnHeaderCell>
                  <Table.ColumnHeaderCell>Job Name</Table.ColumnHeaderCell>
                  <Table.ColumnHeaderCell>URL</Table.ColumnHeaderCell>
                  <Table.ColumnHeaderCell>Status</Table.ColumnHeaderCell>
                  <Table.ColumnHeaderCell>Contacts</Table.ColumnHeaderCell>
                  <Table.ColumnHeaderCell>Created</Table.ColumnHeaderCell>
                  <Table.ColumnHeaderCell>Actions</Table.ColumnHeaderCell>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {jobs.map(job => (
                  <Table.Row 
                    key={job.id}
                    onClick={() => !selectedJobs.includes(job.id) && fetchJobDetails(job.id)}
                    style={{cursor: 'pointer'}}
                  >
                    <Table.Cell onClick={(e) => e.stopPropagation()}>
                      <Checkbox 
                        checked={selectedJobs.includes(job.id)}
                        disabled={job.status !== 'completed'}
                        onCheckedChange={(checked) => handleJobSelection(job.id, !!checked)}
                      />
                    </Table.Cell>
                    <Table.Cell>
                      <Text size="2" weight="bold">{job.name || 'Unnamed Job'}</Text>
                    </Table.Cell>
                    <Table.Cell>
                      <Text size="1" color="gray" truncate style={{maxWidth: '300px'}}>
                        {job.start_url}
                      </Text>
                    </Table.Cell>
                    <Table.Cell>
                      <Badge color={statusColors[job.status]}>
                        {statusLabels[job.status]}
                      </Badge>
                      {job.status === 'processing' && job.contact_count > 0 && (
                        <Text size="1" color="blue"> ({job.contact_count})</Text>
                      )}
                    </Table.Cell>
                    <Table.Cell>
                      <Text size="2">{job.contact_count}</Text>
                    </Table.Cell>
                    <Table.Cell>
                      <Text size="1" color="gray">
                        {new Date(job.created_at).toLocaleDateString()}
                      </Text>
                    </Table.Cell>
                    <Table.Cell onClick={(e) => e.stopPropagation()}>
                      <Flex gap="2">
                        {(job.status === 'pending' || job.status === 'processing') && (
                          <Button 
                            size="1" 
                            color="orange" 
                            variant="ghost"
                            onClick={(e) => handleStopJob(job.id, e)}
                          >
                            Stop
                          </Button>
                        )}
                        <Button 
                          size="1" 
                          color="red" 
                          variant="ghost"
                          onClick={(e) => handleDeleteJob(job.id, e)}
                        >
                          Delete
                        </Button>
                      </Flex>
                    </Table.Cell>
                  </Table.Row>
                ))}
              </Table.Body>
            </Table.Root>
          </Card>
        )}
      </Box>

      {/* Job Details Section */}
      <Box width="100%">
        <Heading size="5" mb="3">Job Details</Heading>
        {selectedJob ? (
            <Card>
                <Box mb="3">
                    <Text size="3" weight="bold">{selectedJob.name || 'Unnamed Job'}</Text>
                    <Text size="2" color="gray">{selectedJob.start_url}</Text>
                    <Text size="1" color="gray" mt="1">
                        Created: {new Date(selectedJob.created_at).toLocaleString()} • 
                        Status: {statusLabels[selectedJob.status]} • 
                        Contacts: {selectedJob.contact_count}
                    </Text>
                </Box>
                {selectedJob.error_message && (
                    <Callout.Root color="red" mb="3">
                        <Callout.Icon><ExclamationTriangleIcon /></Callout.Icon>
                        <Callout.Text>Error: {selectedJob.error_message}</Callout.Text>
                    </Callout.Root>
                )}
                {selectedJob.realtor_contacts && selectedJob.realtor_contacts.length > 0 && (
                    <Flex justify="between" align="center" mb="3">
                        <Text size="2" weight="bold">
                            {selectedJob.status === 'processing' ? 'Scraping in progress: ' : 'Found '}
                            {selectedJob.realtor_contacts.length} contacts
                            {selectedJob.realtor_contacts.length === 700 && ' (limit reached)'}
                        </Text>
                        <Flex gap="2" align="center">
                            {selectedJob.status === 'processing' && (
                                <Text size="1" color="blue">
                                    Results are displayed as they're scraped...
                                </Text>
                            )}
                            {selectedJob.status === 'completed' && selectedJob.realtor_contacts.length > 0 && (
                                <Button 
                                    size="2" 
                                    variant="soft"
                                    onClick={() => {
                                        window.location.href = `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/realtor-importer/${selectedJob.id}/export/csv`;
                                    }}
                                >
                                    Download CSV
                                </Button>
                            )}
                        </Flex>
                    </Flex>
                )}
                <Box style={{ overflowX: 'auto' }}>
                  <Table.Root variant="surface" size="1" style={{ fontSize: '0.8em' }}>
                      <Table.Header>
                          <Table.Row>
                              <Table.ColumnHeaderCell style={{ whiteSpace: 'nowrap' }}>Name</Table.ColumnHeaderCell>
                              <Table.ColumnHeaderCell style={{ whiteSpace: 'nowrap' }}>Company</Table.ColumnHeaderCell>
                              <Table.ColumnHeaderCell style={{ whiteSpace: 'nowrap' }}>Location</Table.ColumnHeaderCell>
                              <Table.ColumnHeaderCell style={{ whiteSpace: 'nowrap' }}>Phone</Table.ColumnHeaderCell>
                              <Table.ColumnHeaderCell style={{ whiteSpace: 'nowrap' }}>Phone 2</Table.ColumnHeaderCell>
                              <Table.ColumnHeaderCell style={{ whiteSpace: 'nowrap' }}>Email</Table.ColumnHeaderCell>
                              <Table.ColumnHeaderCell style={{ whiteSpace: 'nowrap' }}>Personal Email</Table.ColumnHeaderCell>
                              <Table.ColumnHeaderCell style={{ whiteSpace: 'nowrap' }}>Agent Website</Table.ColumnHeaderCell>
                              <Table.ColumnHeaderCell style={{ whiteSpace: 'nowrap' }}>Facebook</Table.ColumnHeaderCell>
                              <Table.ColumnHeaderCell style={{ whiteSpace: 'nowrap' }}>Seller Value</Table.ColumnHeaderCell>
                              <Table.ColumnHeaderCell style={{ whiteSpace: 'nowrap' }}>HC Profile</Table.ColumnHeaderCell>
                          </Table.Row>
                      </Table.Header>
                      <Table.Body>
                          {selectedJob.realtor_contacts?.map(contact => (
                              <Table.Row key={contact.id}>
                                  <Table.Cell style={{ whiteSpace: 'nowrap' }}>{contact.first_name} {contact.last_name}</Table.Cell>
                                  <Table.Cell style={{ whiteSpace: 'nowrap' }}>{contact.company || 'N/A'}</Table.Cell>
                                  <Table.Cell style={{ whiteSpace: 'nowrap' }}>{contact.city}, {contact.state}</Table.Cell>
                                  <Table.Cell style={{ whiteSpace: 'nowrap' }}>{contact.cell_phone || 'N/A'}</Table.Cell>
                                  <Table.Cell style={{ whiteSpace: 'nowrap' }}>{contact.phone2 || 'N/A'}</Table.Cell>
                                  <Table.Cell style={{ whiteSpace: 'nowrap', maxWidth: '150px', overflow: 'hidden', textOverflow: 'ellipsis' }} title={contact.email || 'N/A'}>{contact.email || 'N/A'}</Table.Cell>
                                  <Table.Cell style={{ whiteSpace: 'nowrap', maxWidth: '150px', overflow: 'hidden', textOverflow: 'ellipsis' }} title={contact.personal_email || 'N/A'}>{contact.personal_email || 'N/A'}</Table.Cell>
                                  <Table.Cell style={{ whiteSpace: 'nowrap' }}>
                                      {contact.agent_website ? (
                                          <a href={contact.agent_website} target="_blank" rel="noopener noreferrer">
                                              View
                                          </a>
                                      ) : 'N/A'}
                                  </Table.Cell>
                                  <Table.Cell style={{ whiteSpace: 'nowrap' }}>
                                      {contact.facebook_profile ? (
                                          <a href={contact.facebook_profile} target="_blank" rel="noopener noreferrer">
                                              View
                                          </a>
                                      ) : 'N/A'}
                                  </Table.Cell>
                                  <Table.Cell style={{ whiteSpace: 'nowrap' }}>{formatCurrency(contact.seller_deals_total_value)}</Table.Cell>
                                  <Table.Cell style={{ whiteSpace: 'nowrap' }}>
                                      {contact.profile_url && (
                                          <a href={contact.profile_url} target="_blank" rel="noopener noreferrer">
                                              View
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
      
      {/* Processed Job Modal */}
      <Dialog.Root open={showProcessedModal} onOpenChange={setShowProcessedModal}>
        <Dialog.Content maxWidth="800px">
          <Dialog.Title>Processing Complete</Dialog.Title>
          
          {processedJobDetails && (
            <Box>
              <Flex direction="column" gap="3">
                {processedJobDetails.status === 'COMPLETED' ? (
                  <>
                    <Callout.Root color="green">
                      <Callout.Icon><InfoCircledIcon /></Callout.Icon>
                      <Callout.Text>
                        Successfully processed {processedJobDetails.source_job_ids?.length || 0} jobs
                      </Callout.Text>
                    </Callout.Root>
                    
                    <Card>
                      <Flex direction="column" gap="2">
                        <Text size="3" weight="bold">Processing Summary</Text>
                        <Flex gap="4" wrap="wrap">
                          <Box>
                            <Text size="1" color="gray">Total Contacts</Text>
                            <Text size="3" weight="bold">{processedJobDetails.total_contacts}</Text>
                          </Box>
                          <Box>
                            <Text size="1" color="gray">Duplicates Removed</Text>
                            <Text size="3" weight="bold" color="orange">{processedJobDetails.duplicates_removed}</Text>
                          </Box>
                          <Box>
                            <Text size="1" color="gray">Emails Validated</Text>
                            <Text size="3" weight="bold" color="blue">{processedJobDetails.emails_validated}</Text>
                          </Box>
                          <Box>
                            <Text size="1" color="gray">Websites Crawled</Text>
                            <Text size="3" weight="bold" color="green">{processedJobDetails.websites_crawled}</Text>
                          </Box>
                        </Flex>
                      </Flex>
                    </Card>
                    
                    {processedJobDetails.contacts && processedJobDetails.contacts.length > 0 && (
                      <Box>
                        <Text size="2" weight="bold" mb="2">Sample Contacts (First 10)</Text>
                        <Box style={{ overflowX: 'auto' }}>
                          <Table.Root variant="surface" size="1">
                            <Table.Header>
                              <Table.Row>
                                <Table.ColumnHeaderCell>Name</Table.ColumnHeaderCell>
                                <Table.ColumnHeaderCell>Company</Table.ColumnHeaderCell>
                                <Table.ColumnHeaderCell>Email</Table.ColumnHeaderCell>
                                <Table.ColumnHeaderCell>Email Status</Table.ColumnHeaderCell>
                                <Table.ColumnHeaderCell>Website Crawled</Table.ColumnHeaderCell>
                              </Table.Row>
                            </Table.Header>
                            <Table.Body>
                              {processedJobDetails.contacts.slice(0, 10).map((contact: any) => (
                                <Table.Row key={contact.id}>
                                  <Table.Cell>{contact.first_name} {contact.last_name}</Table.Cell>
                                  <Table.Cell>{contact.company || 'N/A'}</Table.Cell>
                                  <Table.Cell>{contact.email || 'N/A'}</Table.Cell>
                                  <Table.Cell>
                                    {contact.email_status && (
                                      <Badge color={contact.email_valid ? 'green' : 'red'}>
                                        {contact.email_status}
                                      </Badge>
                                    )}
                                  </Table.Cell>
                                  <Table.Cell>
                                    {contact.website_content ? '✓' : '✗'}
                                  </Table.Cell>
                                </Table.Row>
                              ))}
                            </Table.Body>
                          </Table.Root>
                        </Box>
                      </Box>
                    )}
                    
                    <Flex gap="3" justify="end" mt="3">
                      <Button variant="soft" onClick={() => setShowProcessedModal(false)}>
                        Close
                      </Button>
                      <Button onClick={handlePersonalizeEmails}>
                        Create Personalized Emails
                      </Button>
                    </Flex>
                  </>
                ) : (
                  <Callout.Root color="red">
                    <Callout.Icon><ExclamationTriangleIcon /></Callout.Icon>
                    <Callout.Text>Processing failed. Please try again.</Callout.Text>
                  </Callout.Root>
                )}
              </Flex>
            </Box>
          )}
        </Dialog.Content>
      </Dialog.Root>
    </div>
  );
}; 
import React, { useState, useEffect } from 'react';
import { Box, Flex, Text, Button, Heading, Tabs, Card, Badge, Progress, IconButton, Dialog, TextField, TextArea } from '@radix-ui/themes';
import { Upload, Download, Trash2, Play, Settings, RefreshCw, FileText, Mail, Phone, Globe, Facebook } from 'lucide-react';
import api from '../services/api';

interface EnrichmentProject {
  id: string;
  name: string;
  description: string;
  original_filename: string;
  original_row_count: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  processed_rows: number;
  enriched_rows: number;
  emails_found: number;
  phones_found: number;
  facebook_data_found: number;
  websites_scraped: number;
  created_at: string;
  completed_at: string | null;
  error_message?: string;
}

const ContactEnricherPage: React.FC = () => {
  const [projects, setProjects] = useState<EnrichmentProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [selectedProject, setSelectedProject] = useState<EnrichmentProject | null>(null);

  useEffect(() => {
    fetchProjects();
  }, []);

  useEffect(() => {
    // Poll for updates when any project is processing
    const processingProjects = projects.filter(p => p.status === 'processing');
    
    if (processingProjects.length > 0) {
      const interval = setInterval(() => {
        fetchProjects();
      }, 3000); // Poll every 3 seconds
      
      return () => clearInterval(interval);
    }
  }, [projects]);

  const fetchProjects = async () => {
    try {
      const response = await api.get('/api/contact-enricher/projects');
      setProjects(response.data);
    } catch (error) {
      console.error('Error fetching projects:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (file: File, name: string, description: string) => {
    console.log('Uploading file:', { 
      fileName: file.name, 
      fileSize: file.size, 
      fileType: file.type,
      name: name,
      description: description 
    });
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', name);
    if (description && description.trim()) {
      formData.append('description', description);
    }
    
    // Log FormData contents
    for (let [key, value] of formData.entries()) {
      console.log(`FormData ${key}:`, value);
    }

    try {
      await api.post('/api/contact-enricher/projects/upload', formData);
      setUploadOpen(false);
      fetchProjects();
    } catch (error: any) {
      console.error('Error uploading file:', error);
      console.error('Error response:', error.response);
      console.error('Error response data:', error.response?.data);
      console.error('Error detail array:', error.response?.data?.detail);
      
      let errorMessage = 'Failed to upload file';
      
      if (error.response?.data?.detail) {
        if (typeof error.response.data.detail === 'string') {
          errorMessage = error.response.data.detail;
        } else if (Array.isArray(error.response.data.detail)) {
          console.error('Validation errors:', error.response.data.detail);
          errorMessage = error.response.data.detail.map((e: any) => {
            if (e.msg) return e.msg;
            if (e.message) return e.message;
            if (typeof e === 'string') return e;
            return JSON.stringify(e);
          }).join(', ');
        } else if (typeof error.response.data.detail === 'object') {
          errorMessage = JSON.stringify(error.response.data.detail);
        }
      }
      
      alert(errorMessage);
    }
  };

  const startEnrichment = async (projectId: string) => {
    try {
      await api.post(`/api/contact-enricher/projects/${projectId}/enrich`);
      fetchProjects();
    } catch (error) {
      console.error('Error starting enrichment:', error);
      alert('Failed to start enrichment.');
    }
  };

  const deleteProject = async (projectId: string) => {
    if (!confirm('Are you sure you want to delete this project?')) return;
    
    try {
      await api.delete(`/api/contact-enricher/projects/${projectId}`);
      fetchProjects();
    } catch (error) {
      console.error('Error deleting project:', error);
    }
  };

  const exportProject = async (projectId: string) => {
    try {
      const response = await api.post(`/api/contact-enricher/projects/${projectId}/export`, {
        include_original: true,
        only_enriched: false,
        format: 'csv'
      }, {
        responseType: 'blob'
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `enriched_contacts_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Error exporting project:', error);
    }
  };

  const testSerpApi = async () => {
    try {
      const response = await api.get('/api/contact-enricher/test-serp-api');
      console.log('SERP API Test:', response.data);
      alert(`SERP API Test: ${response.data.status}\n${response.data.message}`);
    } catch (error) {
      console.error('Error testing SERP API:', error);
      alert('Failed to test SERP API');
    }
  };

  const getStatusBadge = (status: string) => {
    const colors: Record<string, any> = {
      pending: 'orange',
      processing: 'blue',
      completed: 'green',
      failed: 'red'
    };
    return <Badge color={colors[status] || 'gray'}>{status}</Badge>;
  };

  const ProjectCard: React.FC<{ project: EnrichmentProject }> = ({ project }) => {
    const progress = project.original_row_count > 0 
      ? (project.processed_rows / project.original_row_count) * 100 
      : 0;

    return (
      <Card style={{ marginBottom: '1rem' }}>
        <Flex direction="column" gap="3">
          <Flex justify="between" align="center">
            <Box>
              <Heading size="3">{project.name}</Heading>
              {project.description && <Text size="2" color="gray">{project.description}</Text>}
            </Box>
            {getStatusBadge(project.status)}
          </Flex>

          {project.status === 'failed' && project.error_message && (
            <Card style={{ backgroundColor: '#fee', border: '1px solid #fcc' }}>
              <Text size="2" color="red">{project.error_message}</Text>
            </Card>
          )}

          <Flex gap="4" wrap="wrap">
            <Flex align="center" gap="1">
              <FileText size={16} />
              <Text size="2">{project.original_row_count} rows</Text>
            </Flex>
            <Flex align="center" gap="1">
              <Mail size={16} />
              <Text size="2">{project.emails_found} emails</Text>
            </Flex>
            <Flex align="center" gap="1">
              <Phone size={16} />
              <Text size="2">{project.phones_found} phones</Text>
            </Flex>
            <Flex align="center" gap="1">
              <Facebook size={16} />
              <Text size="2">{project.facebook_data_found} FB data</Text>
            </Flex>
            <Flex align="center" gap="1">
              <Globe size={16} />
              <Text size="2">{project.websites_scraped} sites</Text>
            </Flex>
          </Flex>

          {project.status === 'processing' && (
            <Box>
              <Progress value={progress} />
              <Text size="1" color="gray">
                Processing {project.processed_rows} of {project.original_row_count} rows
              </Text>
            </Box>
          )}

          <Flex gap="2">
            {project.status === 'pending' && (
              <Button 
                size="2" 
                onClick={() => startEnrichment(project.id)}
              >
                <Play size={16} />
                Start Enrichment
              </Button>
            )}
            {project.status === 'completed' && (
              <Button size="2" onClick={() => exportProject(project.id)}>
                <Download size={16} />
                Export CSV
              </Button>
            )}
            <Button size="2" variant="soft" onClick={() => setSelectedProject(project)}>
              View Details
            </Button>
            <IconButton 
              size="2" 
              color="red" 
              variant="soft"
              onClick={() => deleteProject(project.id)}
            >
              <Trash2 size={16} />
            </IconButton>
          </Flex>
        </Flex>
      </Card>
    );
  };

  return (
    <Box p="4">
      <Flex justify="between" align="center" mb="4">
        <Heading size="8">Contact Enricher</Heading>
        <Flex gap="2">
          <Button onClick={fetchProjects} variant="soft">
            <RefreshCw size={16} />
            Refresh
          </Button>
          <Button onClick={testSerpApi} variant="soft">
            <Settings size={16} />
            Test API
          </Button>
          <Button onClick={() => setUploadOpen(true)}>
            <Upload size={16} />
            Upload CSV
          </Button>
        </Flex>
      </Flex>

      {loading ? (
        <Flex justify="center" py="8">
          <Text>Loading projects...</Text>
        </Flex>
      ) : projects.length === 0 ? (
        <Card>
          <Flex direction="column" align="center" py="8" gap="4">
            <Upload size={48} color="#888" />
            <Text size="4" color="gray">No projects yet</Text>
            <Text size="2" color="gray">Upload a CSV file to get started</Text>
            <Button onClick={() => setUploadOpen(true)}>
              Upload Your First File
            </Button>
          </Flex>
        </Card>
      ) : (
        <Box>
          {projects.map(project => (
            <ProjectCard key={project.id} project={project} />
          ))}
        </Box>
      )}

      {/* Upload Dialog */}
      <Dialog.Root open={uploadOpen} onOpenChange={setUploadOpen}>
        <Dialog.Content style={{ maxWidth: 450 }}>
          <Dialog.Title>Upload Contact List</Dialog.Title>
          <UploadDialog onUpload={handleFileUpload} onClose={() => setUploadOpen(false)} />
        </Dialog.Content>
      </Dialog.Root>

      {/* Project Details Dialog */}
      {selectedProject && (
        <Dialog.Root open={!!selectedProject} onOpenChange={() => setSelectedProject(null)}>
          <Dialog.Content style={{ maxWidth: 800 }}>
            <Dialog.Title>{selectedProject.name} - Details</Dialog.Title>
            <ProjectDetailsDialog project={selectedProject} />
          </Dialog.Content>
        </Dialog.Root>
      )}
    </Box>
  );
};

// Upload Dialog Component
const UploadDialog: React.FC<{ 
  onUpload: (file: File, name: string, description: string) => void;
  onClose: () => void;
}> = ({ onUpload, onClose }) => {
  const [file, setFile] = useState<File | null>(null);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');

  const handleSubmit = () => {
    if (!file || !name) {
      alert('Please select a file and provide a name');
      return;
    }
    onUpload(file, name, description);
  };

  return (
    <Flex direction="column" gap="4">
      <Box>
        <Text size="2" mb="1">Project Name *</Text>
        <TextField.Root
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g., California Realtors Q1 2024"
        />
      </Box>

      <Box>
        <Text size="2" mb="1">Description</Text>
        <TextArea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Optional description of this contact list"
          rows={3}
        />
      </Box>

      <Box>
        <Text size="2" mb="1">CSV File *</Text>
        <input
          type="file"
          accept=".csv"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          style={{ width: '100%' }}
        />
      </Box>

      <Flex gap="3" mt="4" justify="end">
        <Button variant="soft" onClick={onClose}>
          Cancel
        </Button>
        <Button onClick={handleSubmit} disabled={!file || !name}>
          Upload & Create Project
        </Button>
      </Flex>
    </Flex>
  );
};

// Project Details Dialog Component
const ProjectDetailsDialog: React.FC<{ project: EnrichmentProject }> = ({ project }) => {
  const [contacts, setContacts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchContacts();
  }, [project.id]);

  const fetchContacts = async () => {
    try {
      const response = await api.get(`/api/contact-enricher/projects/${project.id}/contacts`);
      setContacts(response.data);
    } catch (error) {
      console.error('Error fetching contacts:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Tabs.Root defaultValue="overview">
        <Tabs.List>
          <Tabs.Trigger value="overview">Overview</Tabs.Trigger>
          <Tabs.Trigger value="contacts">Contacts ({contacts.length})</Tabs.Trigger>
        </Tabs.List>

        <Box pt="4">
          <Tabs.Content value="overview">
            <Flex direction="column" gap="4">
              <Card>
                <Heading size="3" mb="3">Enrichment Statistics</Heading>
                <Flex gap="6" wrap="wrap">
                  <Box>
                    <Text size="1" color="gray">Total Rows</Text>
                    <Text size="5" weight="bold">{project.original_row_count}</Text>
                  </Box>
                  <Box>
                    <Text size="1" color="gray">Emails Found</Text>
                    <Text size="5" weight="bold" color="green">{project.emails_found}</Text>
                  </Box>
                  <Box>
                    <Text size="1" color="gray">Phones Found</Text>
                    <Text size="5" weight="bold" color="green">{project.phones_found}</Text>
                  </Box>
                  <Box>
                    <Text size="1" color="gray">Facebook Data</Text>
                    <Text size="5" weight="bold" color="blue">{project.facebook_data_found}</Text>
                  </Box>
                  <Box>
                    <Text size="1" color="gray">Websites Scraped</Text>
                    <Text size="5" weight="bold" color="purple">{project.websites_scraped}</Text>
                  </Box>
                </Flex>
              </Card>

              <Card>
                <Heading size="3" mb="3">Success Rates</Heading>
                <Flex direction="column" gap="3">
                  <Box>
                    <Flex justify="between" mb="1">
                      <Text size="2">Email Discovery</Text>
                      <Text size="2" weight="bold">
                        {project.original_row_count > 0 
                          ? Math.round((project.emails_found / project.original_row_count) * 100) 
                          : 0}%
                      </Text>
                    </Flex>
                    <Progress 
                      value={project.original_row_count > 0 
                        ? (project.emails_found / project.original_row_count) * 100 
                        : 0} 
                    />
                  </Box>
                  <Box>
                    <Flex justify="between" mb="1">
                      <Text size="2">Phone Discovery</Text>
                      <Text size="2" weight="bold">
                        {project.original_row_count > 0 
                          ? Math.round((project.phones_found / project.original_row_count) * 100) 
                          : 0}%
                      </Text>
                    </Flex>
                    <Progress 
                      value={project.original_row_count > 0 
                        ? (project.phones_found / project.original_row_count) * 100 
                        : 0} 
                    />
                  </Box>
                </Flex>
              </Card>
            </Flex>
          </Tabs.Content>

          <Tabs.Content value="contacts">
            {loading ? (
              <Text>Loading contacts...</Text>
            ) : (
              <Box style={{ maxHeight: '400px', overflowY: 'auto' }}>
                {contacts.map((contact, index) => (
                  <Card key={contact.id} style={{ marginBottom: '0.5rem' }}>
                    <Flex justify="between" align="center">
                      <Box>
                        <Text weight="bold">{contact.name || 'Unknown'}</Text>
                        <Text size="2" color="gray">
                          {contact.company} • {contact.city}, {contact.state}
                        </Text>
                      </Box>
                      <Flex gap="3">
                        {contact.email_found && (
                          <Badge color="green">
                            <Mail size={12} /> {contact.email_confidence}%
                          </Badge>
                        )}
                        {contact.phone_found && (
                          <Badge color="blue">
                            <Phone size={12} /> {contact.phone_confidence}%
                          </Badge>
                        )}
                        {contact.facebook_followers && (
                          <Badge color="purple">
                            <Facebook size={12} /> {contact.facebook_followers}
                          </Badge>
                        )}
                      </Flex>
                    </Flex>
                  </Card>
                ))}
              </Box>
            )}
          </Tabs.Content>
        </Box>
      </Tabs.Root>
    </Box>
  );
};

export default ContactEnricherPage; 
import { useState, useEffect } from 'react';
import { Box, Flex, Heading, Button, Card, Text, Table, IconButton, Badge } from '@radix-ui/themes';
import { DownloadIcon, TrashIcon, CalendarIcon } from '@radix-ui/react-icons';
import { MainLayout } from '../components/MainLayout';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

interface PersonalizerProject {
    id: string;
    name: string;
    template_used: string;
    generation_goal: string;
    csv_headers: string[];
    row_count: number;
    generated_csv_url: string;
    status: string;
    created_at: string;
}

const PersonalizerProjectsPage = () => {
    const [projects, setProjects] = useState<PersonalizerProject[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        fetchProjects();
    }, []);

    const fetchProjects = async () => {
        try {
            const response = await api.get('/api/personalizer/projects');
            setProjects(response.data);
        } catch (error) {
            console.error('Failed to fetch projects:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleDownload = (project: PersonalizerProject) => {
        // Extract base64 data and download
        const base64Data = project.generated_csv_url.split(',')[1];
        const blob = new Blob([atob(base64Data)], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `${project.name.replace(/[^a-z0-9]/gi, '_')}_personalized.csv`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    };

    const handleDelete = async (projectId: string) => {
        if (window.confirm('Are you sure you want to delete this project?')) {
            try {
                await api.delete(`/api/personalizer/projects/${projectId}`);
                fetchProjects();
            } catch (error) {
                console.error('Failed to delete project:', error);
            }
        }
    };

    return (
        <MainLayout onNewChat={() => {}}>
            <Box style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
                <Flex justify="between" align="center" mb="6">
                    <Box>
                        <Heading size="7">Email Personalizer Projects</Heading>
                        <Text color="gray" mt="2">View and download your personalized email campaigns</Text>
                    </Box>
                    <Button size="3" onClick={() => navigate('/agents')}>
                        Create New Project
                    </Button>
                </Flex>

                {isLoading ? (
                    <Text>Loading projects...</Text>
                ) : projects.length === 0 ? (
                    <Card>
                        <Flex direction="column" align="center" gap="4" p="6">
                            <Text size="3" color="gray">No projects yet</Text>
                            <Button onClick={() => navigate('/agents')}>
                                Create Your First Project
                            </Button>
                        </Flex>
                    </Card>
                ) : (
                    <Box style={{ overflowX: 'auto' }}>
                        <Table.Root>
                            <Table.Header>
                                <Table.Row>
                                    <Table.ColumnHeaderCell>Project Name</Table.ColumnHeaderCell>
                                    <Table.ColumnHeaderCell>Created</Table.ColumnHeaderCell>
                                    <Table.ColumnHeaderCell>Rows</Table.ColumnHeaderCell>
                                    <Table.ColumnHeaderCell>Status</Table.ColumnHeaderCell>
                                    <Table.ColumnHeaderCell>Actions</Table.ColumnHeaderCell>
                                </Table.Row>
                            </Table.Header>
                            <Table.Body>
                                {projects.map(project => (
                                    <Table.Row key={project.id}>
                                        <Table.Cell>
                                            <Text weight="medium">{project.name}</Text>
                                        </Table.Cell>
                                        <Table.Cell>
                                            <Flex align="center" gap="2">
                                                <CalendarIcon />
                                                <Text size="2">
                                                    {new Date(project.created_at).toLocaleDateString()}
                                                </Text>
                                            </Flex>
                                        </Table.Cell>
                                        <Table.Cell>
                                            <Text>{project.row_count} rows</Text>
                                        </Table.Cell>
                                        <Table.Cell>
                                            <Badge color="green" variant="soft">
                                                {project.status}
                                            </Badge>
                                        </Table.Cell>
                                        <Table.Cell>
                                            <Flex gap="2">
                                                <IconButton
                                                    size="2"
                                                    variant="soft"
                                                    onClick={() => handleDownload(project)}
                                                >
                                                    <DownloadIcon />
                                                </IconButton>
                                                <IconButton
                                                    size="2"
                                                    variant="soft"
                                                    color="red"
                                                    onClick={() => handleDelete(project.id)}
                                                >
                                                    <TrashIcon />
                                                </IconButton>
                                            </Flex>
                                        </Table.Cell>
                                    </Table.Row>
                                ))}
                            </Table.Body>
                        </Table.Root>
                    </Box>
                )}
            </Box>
        </MainLayout>
    );
};

export default PersonalizerProjectsPage; 
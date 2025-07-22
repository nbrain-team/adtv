import { useState, useEffect } from 'react';
import { Box, Flex, Heading, Button, Card, Text, TextField, TextArea, Dialog, IconButton, Badge, Grid } from '@radix-ui/themes';
import { PlusIcon, Pencil1Icon, TrashIcon, CopyIcon } from '@radix-ui/react-icons';
import { MainLayout } from '../components/MainLayout';
import api from '../api';

interface EmailTemplate {
    id: string;
    name: string;
    content: string;
    goal: string;
    created_at: string;
    updated_at: string;
    is_system: boolean; // System templates are pre-loaded templates
}

const TemplateManagerPage = () => {
    const [templates, setTemplates] = useState<EmailTemplate[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [showCreateDialog, setShowCreateDialog] = useState(false);
    const [showEditDialog, setShowEditDialog] = useState(false);
    const [selectedTemplate, setSelectedTemplate] = useState<EmailTemplate | null>(null);
    
    // Form states
    const [formName, setFormName] = useState('');
    const [formContent, setFormContent] = useState('');
    const [formGoal, setFormGoal] = useState('');

    useEffect(() => {
        fetchTemplates();
    }, []);

    const fetchTemplates = async () => {
        try {
            const response = await api.get('/api/email-templates');
            setTemplates(response.data);
        } catch (error) {
            console.error('Failed to fetch templates:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleCreate = async () => {
        try {
            await api.post('/api/email-templates', {
                name: formName,
                content: formContent,
                goal: formGoal
            });
            setShowCreateDialog(false);
            resetForm();
            fetchTemplates();
        } catch (error) {
            console.error('Failed to create template:', error);
        }
    };

    const handleUpdate = async () => {
        if (!selectedTemplate) return;
        
        try {
            await api.put(`/api/email-templates/${selectedTemplate.id}`, {
                name: formName,
                content: formContent,
                goal: formGoal
            });
            setSelectedTemplate(null);
            setShowEditDialog(false);
            fetchTemplates();
        } catch (error) {
            console.error('Failed to update template:', error);
        }
    };

    const handleDelete = async (id: string) => {
        if (window.confirm('Are you sure you want to delete this template?')) {
            try {
                await api.delete(`/api/email-templates/${id}`);
                fetchTemplates();
            } catch (error) {
                console.error('Failed to delete template:', error);
            }
        }
    };

    const handleDuplicate = async (template: EmailTemplate) => {
        try {
            await api.post('/api/email-templates', {
                name: `${template.name} (Copy)`,
                content: template.content,
                goal: template.goal
            });
            fetchTemplates();
        } catch (error) {
            console.error('Failed to duplicate template:', error);
        }
    };

    const openEditDialog = (template: EmailTemplate) => {
        setSelectedTemplate(template);
        setFormName(template.name);
        setFormContent(template.content);
        setFormGoal(template.goal);
        setShowEditDialog(true);
    };

    const resetForm = () => {
        setFormName('');
        setFormContent('');
        setFormGoal('');
        setSelectedTemplate(null);
    };

    const extractPlaceholders = (content: string) => {
        const csvRegex = /\{\{([^\}]+)\}\}/g;
        const manualRegex = /\[\[([^\]]+)\]\]/g;
        const csvFields = [...content.matchAll(csvRegex)].map(match => match[1]);
        const manualFields = [...content.matchAll(manualRegex)].map(match => match[1]);
        
        return { csvFields: [...new Set(csvFields)], manualFields: [...new Set(manualFields)] };
    };

    return (
        <MainLayout onNewChat={() => {}}>
            <Box style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
                <Flex justify="between" align="center" mb="6">
                    <Box>
                        <Heading size="7">Email Template Manager</Heading>
                        <Text color="gray" mt="2">Create and manage email templates for the personalizer</Text>
                    </Box>
                    <Button size="3" onClick={() => setShowCreateDialog(true)}>
                        <PlusIcon />
                        Create Template
                    </Button>
                </Flex>

                {isLoading ? (
                    <Text>Loading templates...</Text>
                ) : templates.length === 0 ? (
                    <Card>
                        <Flex direction="column" align="center" gap="4" p="6">
                            <Text size="3" color="gray">No templates yet</Text>
                            <Button onClick={() => setShowCreateDialog(true)}>
                                Create Your First Template
                            </Button>
                        </Flex>
                    </Card>
                ) : (
                    <Grid columns={{ initial: '1', md: '2' }} gap="4">
                        {templates.map(template => {
                            const { csvFields, manualFields } = extractPlaceholders(template.content);
                            
                            return (
                                <Card key={template.id}>
                                    <Flex direction="column" gap="3">
                                        <Flex justify="between" align="start">
                                            <Box>
                                                <Heading size="4">{template.name}</Heading>
                                                {template.is_system && (
                                                    <Badge color="blue" mt="1">System Template</Badge>
                                                )}
                                            </Box>
                                            <Flex gap="2">
                                                <IconButton
                                                    size="1"
                                                    variant="ghost"
                                                    onClick={() => openEditDialog(template)}
                                                >
                                                    <Pencil1Icon />
                                                </IconButton>
                                                <IconButton
                                                    size="1"
                                                    variant="ghost"
                                                    color="red"
                                                    onClick={() => handleDelete(template.id)}
                                                >
                                                    <TrashIcon />
                                                </IconButton>
                                                <IconButton
                                                    size="1"
                                                    variant="ghost"
                                                    onClick={() => handleDuplicate(template)}
                                                >
                                                    <CopyIcon />
                                                </IconButton>
                                            </Flex>
                                        </Flex>
                                        
                                        <Text size="2" color="gray">{template.goal}</Text>
                                        
                                        <Box>
                                            <Text size="1" weight="medium">Placeholders:</Text>
                                            <Flex gap="2" mt="1" wrap="wrap">
                                                {csvFields.map(field => (
                                                    <Badge key={field} variant="soft" color="green" size="1">
                                                        {`{{${field}}}`}
                                                    </Badge>
                                                ))}
                                                {manualFields.map(field => (
                                                    <Badge key={field} variant="soft" color="blue" size="1">
                                                        {`[[${field}]]`}
                                                    </Badge>
                                                ))}
                                            </Flex>
                                        </Box>
                                        
                                        <Card>
                                            <Text size="1" style={{ 
                                                whiteSpace: 'pre-wrap',
                                                maxHeight: '150px',
                                                overflow: 'auto'
                                            }}>
                                                {template.content.substring(0, 200)}
                                                {template.content.length > 200 && '...'}
                                            </Text>
                                        </Card>
                                    </Flex>
                                </Card>
                            );
                        })}
                    </Grid>
                )}

                {/* Create Dialog */}
                <Dialog.Root open={showCreateDialog} onOpenChange={setShowCreateDialog}>
                    <Dialog.Content style={{ maxWidth: '600px' }}>
                        <Dialog.Title>Create Email Template</Dialog.Title>
                        
                        <Flex direction="column" gap="4" mt="4">
                            <Box>
                                <Text size="2" weight="medium" mb="1">Template Name</Text>
                                <TextField.Root
                                    value={formName}
                                    onChange={(e) => setFormName(e.target.value)}
                                    placeholder="e.g., Welcome Email"
                                />
                            </Box>
                            
                            <Box>
                                <Text size="2" weight="medium" mb="1">Template Content</Text>
                                <Text size="1" color="gray" mb="2">
                                    Use {`{{FieldName}}`} for CSV fields and {`[[FieldName]]`} for manual inputs
                                </Text>
                                <TextArea
                                    value={formContent}
                                    onChange={(e) => setFormContent(e.target.value)}
                                    placeholder="Hi {{FirstName}}, welcome to..."
                                    rows={10}
                                />
                            </Box>
                            
                            <Box>
                                <Text size="2" weight="medium" mb="1">AI Generation Goal</Text>
                                <TextArea
                                    value={formGoal}
                                    onChange={(e) => setFormGoal(e.target.value)}
                                    placeholder="Personalize based on company and location..."
                                    rows={3}
                                />
                            </Box>
                        </Flex>
                        
                        <Flex gap="3" mt="4" justify="end">
                            <Dialog.Close>
                                <Button variant="soft" color="gray">Cancel</Button>
                            </Dialog.Close>
                            <Button 
                                onClick={handleCreate}
                                disabled={!formName || !formContent}
                            >
                                Create Template
                            </Button>
                        </Flex>
                    </Dialog.Content>
                </Dialog.Root>

                {/* Edit Dialog */}
                <Dialog.Root open={showEditDialog} onOpenChange={setShowEditDialog}>
                    <Dialog.Content style={{ maxWidth: '600px' }}>
                        <Dialog.Title>Edit Email Template</Dialog.Title>
                        
                        <Flex direction="column" gap="4" mt="4">
                            <Box>
                                <Text size="2" weight="medium" mb="1">Template Name</Text>
                                <TextField.Root
                                    value={formName}
                                    onChange={(e) => setFormName(e.target.value)}
                                    placeholder="e.g., Welcome Email"
                                />
                            </Box>
                            
                            <Box>
                                <Text size="2" weight="medium" mb="1">Template Content</Text>
                                <Text size="1" color="gray" mb="2">
                                    Use {`{{FieldName}}`} for CSV fields and {`[[FieldName]]`} for manual inputs
                                </Text>
                                <TextArea
                                    value={formContent}
                                    onChange={(e) => setFormContent(e.target.value)}
                                    placeholder="Hi {{FirstName}}, welcome to..."
                                    rows={10}
                                />
                            </Box>
                            
                            <Box>
                                <Text size="2" weight="medium" mb="1">AI Generation Goal</Text>
                                <TextArea
                                    value={formGoal}
                                    onChange={(e) => setFormGoal(e.target.value)}
                                    placeholder="Personalize based on company and location..."
                                    rows={3}
                                />
                            </Box>
                        </Flex>
                        
                        <Flex gap="3" mt="4" justify="end">
                            <Dialog.Close>
                                <Button variant="soft" color="gray">Cancel</Button>
                            </Dialog.Close>
                            <Button 
                                onClick={handleUpdate}
                                disabled={!formName || !formContent}
                            >
                                Save Changes
                            </Button>
                        </Flex>
                    </Dialog.Content>
                </Dialog.Root>
            </Box>
        </MainLayout>
    );
};

export default TemplateManagerPage; 
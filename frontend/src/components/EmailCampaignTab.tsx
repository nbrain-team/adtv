import React, { useState, useEffect } from 'react';
import {
    Box,
    Button,
    Card,
    Flex,
    Heading,
    Text,
    TextField,
    TextArea,
    Badge,
    Select,
    Callout,
    Dialog,
    Tabs,
    ScrollArea,
    Table,
    Checkbox
} from '@radix-ui/themes';
import {
    PlusIcon,
    EnvelopeClosedIcon,
    Pencil1Icon,
    TrashIcon,
    InfoCircledIcon,
    CheckIcon,
    Cross2Icon
} from '@radix-ui/react-icons';
import api from '../services/api';

interface Contact {
    id: string;
    first_name?: string;
    last_name?: string;
    email?: string;
    company?: string;
    title?: string;
    phone?: string;
    neighborhood?: string;
    is_rsvp?: boolean;
    enriched_phone?: string;
    enriched_company?: string;
    enriched_title?: string;
}

interface EmailTemplate {
    id: string;
    name: string;
    subject: string;
    body: string;
    template_type: string;
}

interface EmailCampaignTabProps {
    campaignId: string;
    campaign: any;
    selectedContacts: Contact[];
    onClearSelection: () => void;
}

export const EmailCampaignTab: React.FC<EmailCampaignTabProps> = ({
    campaignId,
    campaign,
    selectedContacts,
    onClearSelection
}) => {
    const [emailTemplates, setEmailTemplates] = useState<EmailTemplate[]>([]);
    const [selectedTemplate, setSelectedTemplate] = useState<string>('');
    const [emailSubject, setEmailSubject] = useState('');
    const [emailBody, setEmailBody] = useState('');
    const [showTemplateModal, setShowTemplateModal] = useState(false);
    const [editingTemplate, setEditingTemplate] = useState<EmailTemplate | null>(null);
    const [templateForm, setTemplateForm] = useState({
        name: '',
        subject: '',
        body: '',
        template_type: 'general'
    });
    const [activeSubTab, setActiveSubTab] = useState('selected');
    const [generating, setGenerating] = useState(false);

    useEffect(() => {
        fetchEmailTemplates();
    }, [campaignId]);

    const fetchEmailTemplates = async () => {
        try {
            const response = await api.get(`/api/campaigns/${campaignId}/email-templates`);
            setEmailTemplates(response.data);
        } catch (err) {
            console.error('Failed to fetch email templates:', err);
        }
    };

    const handleCreateTemplate = async () => {
        try {
            const response = await api.post(`/api/campaigns/${campaignId}/email-templates`, templateForm);
            setEmailTemplates([...emailTemplates, response.data]);
            setShowTemplateModal(false);
            setTemplateForm({ name: '', subject: '', body: '', template_type: 'general' });
            alert('Template created successfully!');
        } catch (err) {
            console.error('Failed to create template:', err);
            alert('Failed to create template');
        }
    };

    const handleUpdateTemplate = async () => {
        if (!editingTemplate) return;
        
        try {
            const response = await api.put(
                `/api/campaigns/${campaignId}/email-templates/${editingTemplate.id}`,
                templateForm
            );
            setEmailTemplates(emailTemplates.map(t => 
                t.id === editingTemplate.id ? response.data : t
            ));
            setShowTemplateModal(false);
            setEditingTemplate(null);
            setTemplateForm({ name: '', subject: '', body: '', template_type: 'general' });
            alert('Template updated successfully!');
        } catch (err) {
            console.error('Failed to update template:', err);
            alert('Failed to update template');
        }
    };

    const handleDeleteTemplate = async (templateId: string) => {
        if (!confirm('Are you sure you want to delete this template?')) return;
        
        try {
            await api.delete(`/api/campaigns/${campaignId}/email-templates/${templateId}`);
            setEmailTemplates(emailTemplates.filter(t => t.id !== templateId));
            alert('Template deleted successfully!');
        } catch (err) {
            console.error('Failed to delete template:', err);
            alert('Failed to delete template');
        }
    };

    const handleUseTemplate = (template: EmailTemplate) => {
        setSelectedTemplate(template.id);
        setEmailSubject(template.subject);
        setEmailBody(template.body);
        setActiveSubTab('compose');
    };

    const handleGenerateEmails = async () => {
        if (!emailSubject || !emailBody) {
            alert('Please provide both subject and body for the email');
            return;
        }

        if (selectedContacts.length === 0) {
            alert('Please select contacts from the Contacts or RSVP tabs first');
            return;
        }

        setGenerating(true);
        try {
            // First save the template to the campaign
            await api.put(`/api/campaigns/${campaignId}`, {
                email_template: emailBody,
                email_subject: emailSubject
            });

            // Then generate emails for selected contacts
            const response = await api.post(`/api/campaigns/${campaignId}/generate-emails`, {
                contact_ids: selectedContacts.map(c => c.id)
            });

            alert(`Successfully started email generation for ${selectedContacts.length} contacts!`);
            onClearSelection();
        } catch (err) {
            console.error('Failed to generate emails:', err);
            alert('Failed to generate emails. Please try again.');
        } finally {
            setGenerating(false);
        }
    };

    return (
        <Card>
            {/* Header with selected contacts count */}
            <Flex align="center" justify="between" mb="4">
                <Heading size="4">Email Campaign</Heading>
                {selectedContacts.length > 0 && (
                    <Badge size="2" color="blue">
                        {selectedContacts.length} contacts selected
                    </Badge>
                )}
            </Flex>

            {/* Info callout */}
            {selectedContacts.length === 0 ? (
                <Callout.Root color="blue" mb="4">
                    <Callout.Icon>
                        <InfoCircledIcon />
                    </Callout.Icon>
                    <Callout.Text>
                        Select contacts from the Contacts or RSVP tabs, then come here to compose and send emails.
                    </Callout.Text>
                </Callout.Root>
            ) : (
                <Callout.Root color="green" mb="4">
                    <Callout.Icon>
                        <CheckIcon />
                    </Callout.Icon>
                    <Callout.Text>
                        {selectedContacts.length} contacts selected. Choose a template or create a new email below.
                    </Callout.Text>
                </Callout.Root>
            )}

            {/* Sub-tabs for workflow */}
            <Tabs.Root value={activeSubTab} onValueChange={setActiveSubTab}>
                <Tabs.List mb="4">
                    <Tabs.Trigger value="selected">
                        Selected Contacts ({selectedContacts.length})
                    </Tabs.Trigger>
                    <Tabs.Trigger value="templates">
                        Templates ({emailTemplates.length})
                    </Tabs.Trigger>
                    <Tabs.Trigger value="compose">
                        Compose Email
                    </Tabs.Trigger>
                </Tabs.List>

                {/* Selected Contacts Sub-tab */}
                <Tabs.Content value="selected">
                    {selectedContacts.length === 0 ? (
                        <Flex align="center" justify="center" style={{ padding: '4rem' }}>
                            <Text color="gray">No contacts selected. Go to Contacts or RSVP tab to select contacts.</Text>
                        </Flex>
                    ) : (
                        <Box>
                            <Flex justify="between" mb="3">
                                <Text size="2" weight="medium">Selected Recipients</Text>
                                <Button size="2" variant="soft" color="red" onClick={onClearSelection}>
                                    <Cross2Icon />
                                    Clear Selection
                                </Button>
                            </Flex>
                            <ScrollArea style={{ height: '400px' }}>
                                <Table.Root>
                                    <Table.Header>
                                        <Table.Row>
                                            <Table.ColumnHeaderCell>Name</Table.ColumnHeaderCell>
                                            <Table.ColumnHeaderCell>Email</Table.ColumnHeaderCell>
                                            <Table.ColumnHeaderCell>Company</Table.ColumnHeaderCell>
                                            <Table.ColumnHeaderCell>Type</Table.ColumnHeaderCell>
                                        </Table.Row>
                                    </Table.Header>
                                    <Table.Body>
                                        {selectedContacts.map(contact => (
                                            <Table.Row key={contact.id}>
                                                <Table.Cell>
                                                    {contact.first_name} {contact.last_name}
                                                </Table.Cell>
                                                <Table.Cell>{contact.email || 'No email'}</Table.Cell>
                                                <Table.Cell>{contact.company || '-'}</Table.Cell>
                                                <Table.Cell>
                                                    {contact.is_rsvp ? (
                                                        <Badge color="green">RSVP</Badge>
                                                    ) : (
                                                        <Badge>Contact</Badge>
                                                    )}
                                                </Table.Cell>
                                            </Table.Row>
                                        ))}
                                    </Table.Body>
                                </Table.Root>
                            </ScrollArea>
                        </Box>
                    )}
                </Tabs.Content>

                {/* Templates Sub-tab */}
                <Tabs.Content value="templates">
                    <Flex justify="end" mb="4">
                        <Button
                            variant="solid"
                            onClick={() => {
                                setEditingTemplate(null);
                                setTemplateForm({ name: '', subject: '', body: '', template_type: 'general' });
                                setShowTemplateModal(true);
                            }}
                        >
                            <PlusIcon />
                            Create Template
                        </Button>
                    </Flex>

                    {emailTemplates.length === 0 ? (
                        <Flex align="center" justify="center" style={{ padding: '4rem' }}>
                            <Text color="gray">No templates yet. Create your first template!</Text>
                        </Flex>
                    ) : (
                        <Box style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1rem' }}>
                            {emailTemplates.map(template => (
                                <Card key={template.id} style={{ padding: '1.5rem' }}>
                                    <Flex direction="column" gap="3">
                                        <Flex align="center" justify="between">
                                            <Heading size="3">{template.name}</Heading>
                                            <Badge>{template.template_type}</Badge>
                                        </Flex>
                                        <Box>
                                            <Text size="2" color="gray" weight="bold">Subject:</Text>
                                            <Text size="2">{template.subject}</Text>
                                        </Box>
                                        <Box>
                                            <Text size="2" color="gray" weight="bold">Preview:</Text>
                                            <Text size="2" style={{
                                                whiteSpace: 'pre-wrap',
                                                overflow: 'hidden',
                                                textOverflow: 'ellipsis',
                                                display: '-webkit-box',
                                                WebkitLineClamp: 3,
                                                WebkitBoxOrient: 'vertical'
                                            }}>
                                                {template.body}
                                            </Text>
                                        </Box>
                                        <Flex gap="2" mt="2">
                                            <Button
                                                size="2"
                                                variant="solid"
                                                onClick={() => handleUseTemplate(template)}
                                            >
                                                <CheckIcon />
                                                Use Template
                                            </Button>
                                            <Button
                                                size="2"
                                                variant="soft"
                                                onClick={() => {
                                                    setEditingTemplate(template);
                                                    setTemplateForm({
                                                        name: template.name,
                                                        subject: template.subject,
                                                        body: template.body,
                                                        template_type: template.template_type
                                                    });
                                                    setShowTemplateModal(true);
                                                }}
                                            >
                                                <Pencil1Icon />
                                            </Button>
                                            <Button
                                                size="2"
                                                variant="soft"
                                                color="red"
                                                onClick={() => handleDeleteTemplate(template.id)}
                                            >
                                                <TrashIcon />
                                            </Button>
                                        </Flex>
                                    </Flex>
                                </Card>
                            ))}
                        </Box>
                    )}
                </Tabs.Content>

                {/* Compose Email Sub-tab */}
                <Tabs.Content value="compose">
                    <Flex direction="column" gap="4">
                        {/* Template Selector */}
                        {emailTemplates.length > 0 && (
                            <Box>
                                <Text as="label" size="2" mb="1" weight="medium">
                                    Use Template (Optional)
                                </Text>
                                <Select.Root value={selectedTemplate} onValueChange={(value) => {
                                    setSelectedTemplate(value);
                                    const template = emailTemplates.find(t => t.id === value);
                                    if (template) {
                                        setEmailSubject(template.subject);
                                        setEmailBody(template.body);
                                    }
                                }}>
                                    <Select.Trigger placeholder="Select a template..." />
                                    <Select.Content>
                                        <Select.Item value="">None</Select.Item>
                                        {emailTemplates.map(template => (
                                            <Select.Item key={template.id} value={template.id}>
                                                {template.name}
                                            </Select.Item>
                                        ))}
                                    </Select.Content>
                                </Select.Root>
                            </Box>
                        )}

                        {/* Email Subject */}
                        <Box>
                            <Text as="label" size="2" mb="1" weight="medium">
                                Email Subject
                            </Text>
                            <TextField.Root
                                value={emailSubject}
                                onChange={(e) => setEmailSubject(e.target.value)}
                                placeholder="Join us for an exclusive event, {{first_name}}!"
                            />
                        </Box>

                        {/* Email Body */}
                        <Box>
                            <Text as="label" size="2" mb="1" weight="medium">
                                Email Body
                            </Text>
                            <TextArea
                                value={emailBody}
                                onChange={(e) => setEmailBody(e.target.value)}
                                placeholder="Dear {{first_name}},

We're excited to invite you to our upcoming event on {{event_date}} at {{event_time}}.

Location: {{hotel_name}}
Address: {{hotel_address}}

Best regards,
{{owner_name}}"
                                rows={15}
                            />
                            <Text size="1" color="gray" mt="1">
                                Available variables: {`{{first_name}}, {{last_name}}, {{company}}, {{title}}, {{event_date}}, {{event_time}}, {{hotel_name}}, {{hotel_address}}, {{calendly_link}}, {{owner_name}}`}
                            </Text>
                        </Box>

                        {/* Action Buttons */}
                        <Flex gap="3">
                            <Button
                                onClick={handleGenerateEmails}
                                disabled={!emailBody || !emailSubject || selectedContacts.length === 0 || generating}
                            >
                                <EnvelopeClosedIcon />
                                {generating ? 'Generating...' : `Generate Emails for ${selectedContacts.length} Contacts`}
                            </Button>
                            <Button
                                variant="soft"
                                onClick={() => {
                                    setTemplateForm({
                                        name: '',
                                        subject: emailSubject,
                                        body: emailBody,
                                        template_type: 'general'
                                    });
                                    setShowTemplateModal(true);
                                }}
                                disabled={!emailBody || !emailSubject}
                            >
                                Save as Template
                            </Button>
                        </Flex>
                    </Flex>
                </Tabs.Content>
            </Tabs.Root>

            {/* Template Modal */}
            <Dialog.Root open={showTemplateModal} onOpenChange={setShowTemplateModal}>
                <Dialog.Content style={{ maxWidth: 600 }}>
                    <Dialog.Title>
                        {editingTemplate ? 'Edit Template' : 'Create New Template'}
                    </Dialog.Title>
                    
                    <Flex direction="column" gap="4" mt="4">
                        <Box>
                            <Text as="label" size="2" mb="1" weight="medium">
                                Template Name
                            </Text>
                            <TextField.Root
                                value={templateForm.name}
                                onChange={(e) => setTemplateForm({ ...templateForm, name: e.target.value })}
                                placeholder="e.g., Welcome Email"
                            />
                        </Box>

                        <Box>
                            <Text as="label" size="2" mb="1" weight="medium">
                                Subject Line
                            </Text>
                            <TextField.Root
                                value={templateForm.subject}
                                onChange={(e) => setTemplateForm({ ...templateForm, subject: e.target.value })}
                                placeholder="e.g., You're invited to {{event_name}}!"
                            />
                        </Box>

                        <Box>
                            <Text as="label" size="2" mb="1" weight="medium">
                                Email Body
                            </Text>
                            <TextArea
                                value={templateForm.body}
                                onChange={(e) => setTemplateForm({ ...templateForm, body: e.target.value })}
                                rows={10}
                            />
                        </Box>

                        <Box>
                            <Text as="label" size="2" mb="1" weight="medium">
                                Template Type
                            </Text>
                            <Select.Root 
                                value={templateForm.template_type} 
                                onValueChange={(value) => setTemplateForm({ ...templateForm, template_type: value })}
                            >
                                <Select.Trigger />
                                <Select.Content>
                                    <Select.Item value="general">General</Select.Item>
                                    <Select.Item value="invitation">Invitation</Select.Item>
                                    <Select.Item value="reminder">Reminder</Select.Item>
                                    <Select.Item value="follow-up">Follow-up</Select.Item>
                                </Select.Content>
                            </Select.Root>
                        </Box>
                    </Flex>

                    <Flex gap="3" mt="5" justify="end">
                        <Dialog.Close>
                            <Button variant="soft" color="gray">
                                Cancel
                            </Button>
                        </Dialog.Close>
                        <Button 
                            onClick={editingTemplate ? handleUpdateTemplate : handleCreateTemplate}
                            disabled={!templateForm.name || !templateForm.subject || !templateForm.body}
                        >
                            {editingTemplate ? 'Update Template' : 'Create Template'}
                        </Button>
                    </Flex>
                </Dialog.Content>
            </Dialog.Root>
        </Card>
    );
}; 
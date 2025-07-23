import { Box, Card, Text, Button, Flex, TextArea, Select, Spinner, Checkbox, Heading, Grid, TextField, Badge, IconButton } from '@radix-ui/themes';
import { UploadIcon, DownloadIcon, ChevronDownIcon, GearIcon, ClockIcon, CheckCircledIcon, TrashIcon } from '@radix-ui/react-icons';
import { useState, useRef, ChangeEvent, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Papa from 'papaparse';
import ReactMarkdown from 'react-markdown';
import api from '../api';

interface EmailTemplate {
    id: string;
    name: string;
    content: string;
    goal: string;
    is_system: boolean;
}

interface SavedProject {
    id: string;
    name: string;
    csvContent: string;
    status: 'processing' | 'completed';
    createdAt: string;
    rowCount?: number;
}

// Agent data for email signatures
const AGENTS = [
    { id: '1', name: 'Kalena Conley', phone: '619-374-7405', email: 'kalena@adtvmedia.com' },
    { id: '2', name: 'Evan Jones', phone: '619-374-2561', email: 'evan@adtvmedia.com' },
    { id: '3', name: 'Sigrid Smith', phone: '619-292-8580', email: 'sigrid@adtvmedia.com' },
    { id: '4', name: 'Amy Dodsworth', phone: '619-259-0014', email: 'amy@adtvmedia.com' },
    { id: '5', name: 'Bailey Jacobs', phone: '619-333-0342', email: 'bailey@adtvmedia.com' },
];

// A modern, reusable file input component
const FileInput = ({ onFileSelect, disabled }: { onFileSelect: (file: File) => void, disabled: boolean }) => {
    const inputRef = useRef<HTMLInputElement>(null);

    const handleClick = () => {
        inputRef.current?.click();
    };

    const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file) {
            onFileSelect(file);
        }
    };

    return (
        <Box>
            <input
                type="file"
                accept=".csv"
                ref={inputRef}
                onChange={handleFileChange}
                style={{ display: 'none' }}
                disabled={disabled}
            />
            <Button onClick={handleClick} disabled={disabled} style={{ width: '100%', cursor: disabled ? 'not-allowed' : 'pointer' }}>
                <Flex align="center" gap="2">
                    <UploadIcon />
                    <Text>Upload CSV</Text>
                </Flex>
            </Button>
        </Box>
    );
};

// Custom function to safely convert an array of arrays to a CSV string
// This avoids using Papa.unparse which can cause CSP issues.
const arrayToCsv = (data: string[][]): string => {
    return data.map(row =>
        row.map(field => {
            const str = String(field === null || field === undefined ? '' : field);
            // Handle fields containing commas, quotes, or newlines
            if (/[",\n]/.test(str)) {
                return `"${str.replace(/"/g, '""')}"`;
            }
            return str;
        }).join(',')
    ).join('\r\n');  // Changed from '\\r\\n' to '\r\n'
};

export const GeneratorWorkflow = () => {
    const navigate = useNavigate();
    const [csvFile, setCsvFile] = useState<File | null>(null);
    const [csvHeaders, setCsvHeaders] = useState<string[]>([]);
    const [keyFields, setKeyFields] = useState<string[]>([]);
    const [currentStep, setCurrentStep] = useState(1);
    const [coreContent, setCoreContent] = useState('');
    const [generationGoal, setGenerationGoal] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [previewContent, setPreviewContent] = useState<{template: string, content: string}[]>([]);
    const [finalCsv, setFinalCsv] = useState<string | null>(null);
    const [selectedTemplates, setSelectedTemplates] = useState<string[]>([]);
    const [workflowType, setWorkflowType] = useState<'template' | 'scratch' | null>(null);
    const [manualFields, setManualFields] = useState<Record<string, string>>({});
    const [templates, setTemplates] = useState<EmailTemplate[]>([]);
    const [isLoadingTemplates, setIsLoadingTemplates] = useState(true);
    const [projectName, setProjectName] = useState('');
    const [rowCount, setRowCount] = useState(0);
    const [savedProjects, setSavedProjects] = useState<SavedProject[]>([]);
    const [selectedAgent, setSelectedAgent] = useState<string>('');
    
    // Ref for the textarea to handle cursor position
    const textAreaRef = useRef<HTMLTextAreaElement>(null);

    const openBraces = '{{';
    const closeBraces = '}}';

    // Fetch templates on component mount
    useEffect(() => {
        fetchTemplates();
        loadSavedProjects();
    }, []);
    
    // Check for data from realtor importer
    useEffect(() => {
        const savedData = sessionStorage.getItem('emailPersonalizerData');
        if (savedData) {
            try {
                const { fileName, fileContent, fromRealtorImporter } = JSON.parse(savedData);
                
                if (fromRealtorImporter && fileContent) {
                    // Create a File object from the content
                    const blob = new Blob([fileContent], { type: 'text/csv' });
                    const file = new File([blob], fileName, { type: 'text/csv' });
                    
                    // Process the file
                    handleFileSelect(file);
                    
                    // Clear the sessionStorage
                    sessionStorage.removeItem('emailPersonalizerData');
                }
            } catch (error) {
                console.error('Error loading data from realtor importer:', error);
            }
        }
    }, []);

    const fetchTemplates = async () => {
        try {
            const response = await api.get('/api/email-templates');
            setTemplates(response.data);
        } catch (error) {
            console.error('Failed to fetch templates:', error);
        } finally {
            setIsLoadingTemplates(false);
        }
    };

    const loadSavedProjects = () => {
        const saved = localStorage.getItem('emailPersonalizerProjects');
        if (saved) {
            setSavedProjects(JSON.parse(saved));
        }
    };

    const saveProject = (status: 'processing' | 'completed') => {
        const project: SavedProject = {
            id: Date.now().toString(),
            name: projectName || `Project ${new Date().toLocaleDateString()}`,
            csvContent: finalCsv || '',
            status,
            createdAt: new Date().toISOString(),
            rowCount: rowCount
        };

        const saved = localStorage.getItem('emailPersonalizerProjects');
        const projects = saved ? JSON.parse(saved) : [];
        
        // Remove any existing project with same name
        const filtered = projects.filter((p: SavedProject) => p.name !== project.name);
        
        // Add new project at beginning
        const updated = [project, ...filtered].slice(0, 10); // Keep last 10 projects
        
        localStorage.setItem('emailPersonalizerProjects', JSON.stringify(updated));
        setSavedProjects(updated);
    };

    const loadProject = (project: SavedProject) => {
        setProjectName(project.name);
        setFinalCsv(project.csvContent);
        setRowCount(project.rowCount || 0);
        setCurrentStep(6);
    };

    const deleteProject = (projectId: string) => {
        const saved = localStorage.getItem('emailPersonalizerProjects');
        const projects = saved ? JSON.parse(saved) : [];
        const filtered = projects.filter((p: SavedProject) => p.id !== projectId);
        localStorage.setItem('emailPersonalizerProjects', JSON.stringify(filtered));
        setSavedProjects(filtered);
    };

    // Extract fields that need manual input from template content
    const extractManualFields = (content: string): string[] => {
        const regex = /\[\[([^\]]+)\]\]/g;
        const fields: string[] = [];
        const agentFields = ['AssociateName', 'ContactInfo', 'AssociatePhone', 'AssociateEmail'];
        let match;
        while ((match = regex.exec(content)) !== null) {
            // Exclude agent-related fields as they'll be handled by the agent selector
            if (!fields.includes(match[1]) && !agentFields.includes(match[1])) {
                fields.push(match[1]);
            }
        }
        return fields;
    };

    // Get all manual fields from all selected templates
    const getAllManualFields = (): string[] => {
        const allFields: string[] = [];
        selectedTemplates.forEach(templateId => {
            const template = templates.find(t => t.id === templateId);
            if (template) {
                const fields = extractManualFields(template.content);
                fields.forEach(field => {
                    if (!allFields.includes(field)) {
                        allFields.push(field);
                    }
                });
            }
        });
        return allFields;
    };

    // Combine all selected templates into one
    const combineTemplates = (): string => {
        return selectedTemplates.map(templateId => {
            const template = templates.find(t => t.id === templateId);
            return template ? template.content : '';
        }).join('\n\n---\n\n');
    };

    // Replace manual fields in content
    const replaceManualFields = (content: string): string => {
        let updatedContent = content;
        
        // Replace manual fields from the form
        Object.entries(manualFields).forEach(([field, value]) => {
            const regex = new RegExp(`\\[\\[${field}\\]\\]`, 'g');
            updatedContent = updatedContent.replace(regex, value);
        });
        
        // Replace agent-specific fields
        if (selectedAgent) {
            const agent = AGENTS.find(a => a.id === selectedAgent);
            if (agent) {
                // Replace AssociateName
                updatedContent = updatedContent.replace(/\[\[AssociateName\]\]/g, agent.name);
                
                // Replace ContactInfo (format: phone email)
                const contactInfo = `${agent.phone} ${agent.email}`;
                updatedContent = updatedContent.replace(/\[\[ContactInfo\]\]/g, contactInfo);
                
                // Also replace individual fields if they exist
                updatedContent = updatedContent.replace(/\[\[AssociatePhone\]\]/g, agent.phone);
                updatedContent = updatedContent.replace(/\[\[AssociateEmail\]\]/g, agent.email);
            }
        }
        
        return updatedContent;
    };

    const handleFileSelect = (file: File) => {
        setCsvFile(file);
        Papa.parse(file, {
            header: true,
            skipEmptyLines: true,
            complete: (results: Papa.ParseResult<Record<string, unknown>>) => {
                if (results.meta.fields) {
                    setCsvHeaders(results.meta.fields);
                    // Set row count from parsed data
                    setRowCount(results.data.length);
                    // Reset key fields on new file upload
                    setKeyFields([]);
                    if (workflowType === 'scratch') {
                        setCurrentStep(3);
                    } else {
                        setCurrentStep(4);
                    }
                }
            }
        });
    };

    const handleKeyFieldChange = (header: string, checked: boolean) => {
        setKeyFields(prev =>
            checked ? [...prev, header] : prev.filter(f => f !== header)
        );
    };
    
    // New function to insert field placeholder at cursor position
    const insertFieldPlaceholder = (fieldName: string) => {
        const textarea = textAreaRef.current;
        if (!textarea) return;
        
        const placeholder = `${openBraces}${fieldName}${closeBraces}`;
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const text = textarea.value;
        
        // Insert the placeholder at cursor position
        const newText = text.substring(0, start) + placeholder + text.substring(end);
        setCoreContent(newText);
        
        // Set cursor position after the inserted placeholder
        setTimeout(() => {
            textarea.focus();
            textarea.setSelectionRange(start + placeholder.length, start + placeholder.length);
        }, 0);
    };
    
    // Handle template selection
    const handleTemplateToggle = (templateId: string) => {
        if (selectedTemplates.includes(templateId)) {
            // Remove template
            setSelectedTemplates(selectedTemplates.filter(t => t !== templateId));
        } else {
            // Add template
            setSelectedTemplates([...selectedTemplates, templateId]);
        }
        
        // Update manual fields for all selected templates
        const allFields = getAllManualFieldsForTemplates(
            selectedTemplates.includes(templateId) 
                ? selectedTemplates.filter(t => t !== templateId)
                : [...selectedTemplates, templateId]
        );
        
        const newManualFields: Record<string, string> = {};
        allFields.forEach(field => {
            newManualFields[field] = manualFields[field] || '';
        });
        setManualFields(newManualFields);
    };

    // Helper function to get manual fields for specific templates
    const getAllManualFieldsForTemplates = (templateIds: string[]): string[] => {
        const allFields: string[] = [];
        templateIds.forEach(templateId => {
            const template = templates.find(t => t.id === templateId);
            if (template) {
                const fields = extractManualFields(template.content);
                fields.forEach(field => {
                    if (!allFields.includes(field)) {
                        allFields.push(field);
                    }
                });
            }
        });
        return allFields;
    };

    // Update content when templates change
    useEffect(() => {
        if (selectedTemplates.length > 0) {
            const combinedContent = selectedTemplates.map(templateId => {
                const template = templates.find(t => t.id === templateId);
                return template ? template.content : '';
            }).join('\n\n---\n\n');
            setCoreContent(combinedContent);
            
            // Set combined goals
            const goals = selectedTemplates.map(templateId => {
                const template = templates.find(t => t.id === templateId);
                return template ? `[${template.name}]: ${template.goal}` : '';
            }).filter(g => g).join('\n\n');
            setGenerationGoal(goals);
        }
    }, [selectedTemplates]);

    const handleGenerate = async (isPreview: boolean) => {
        if (!csvFile || !coreContent) {
            alert("Please upload a file and provide the core content.");
            return;
        }

        // Replace manual fields before sending
        const processedContent = replaceManualFields(coreContent);

        setIsLoading(true);
        setPreviewContent([]); // Clear previous preview content
        setFinalCsv(null);
        if (isPreview) {
            setCurrentStep(currentStep); // Stay on current step for preview
        } else {
            setCurrentStep(6); // Move to generating step
            // Save project as processing when starting full generation
            if (!projectName) {
                setProjectName(`Campaign ${new Date().toLocaleDateString()}`);
            }
            saveProject('processing');
        }

        const formData = new FormData();
        formData.append('file', csvFile);
        formData.append('key_fields', JSON.stringify(keyFields));
        formData.append('core_content', processedContent);
        formData.append('is_preview', String(isPreview));
        formData.append('generation_goal', generationGoal);
        formData.append('selected_templates', JSON.stringify(selectedTemplates));

        try {
            const apiUrl = import.meta.env.VITE_API_BASE_URL || '';
            const response = await fetch(`${apiUrl}/generator/process`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorText = await response.text().catch(() => 'Failed to get error details from server.');
                throw new Error(`Server responded with status ${response.status}: ${errorText}`);
            }

            const reader = response.body?.getReader();
            const decoder = new TextDecoder();
            if (!reader) throw new Error("Failed to get response reader.");

            let header: string[] = [];
            let csvRows: string[][] = [];
            let buffer = '';
            let foundPreview = false; // Add this flag

            const processLine = (line: string) => {
                if (line.trim() === '') return;
                try {
                    // Replace NaN with null before parsing
                    const sanitizedLine = line.replace(/\bNaN\b/g, 'null');
                    const parsed = JSON.parse(sanitizedLine);
                    if (parsed.type === 'error') throw new Error(parsed.detail || 'An error occurred during generation.');
                    if (parsed.type === 'header') header = parsed.data;
                    else if (parsed.type === 'row') {
                        if (isPreview) {
                            // For preview, extract generated contents
                            const originalLength = csvHeaders.length;
                            const generatedParts = parsed.data.slice(originalLength);
                            const previews = [];
                            if (selectedTemplates.length > 0) {
                                selectedTemplates.forEach((id, idx) => {
                                    const template = templates.find(t => t.id === id);
                                    previews.push({
                                        template: template?.name || 'Template ' + (idx + 1),
                                        content: generatedParts[idx] || 'No content generated'
                                    });
                                });
                            } else {
                                previews.push({
                                    template: 'Generated Content',
                                    content: generatedParts[0] || 'No content generated'
                                });
                            }
                            setPreviewContent(previews);
                            foundPreview = true; // Set the flag
                        } else {
                            if (csvRows.length === 0) csvRows.push(header);
                            csvRows.push(parsed.data);
                        }
                    } else if (parsed.type === 'done' && !isPreview) {
                        console.log('CSV Generation complete. Rows collected:', csvRows.length);
                        console.log('First few rows:', csvRows.slice(0, 3));
                        const csvString = arrayToCsv(csvRows);
                        setFinalCsv(csvString);
                        setRowCount(csvRows.length - 1); // Subtract 1 for header row
                        setCurrentStep(6); // Move to download step
                        // Save project as completed
                        saveProject('completed');
                    }
                } catch (e) {
                    console.error("Failed to parse streamed line:", line, e);
                }
            };

            while (true) {
                const { done, value } = await reader.read();
                if (done) {
                    if (buffer) processLine(buffer); // Process any remaining text
                    break;
                }
                
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || ''; // Keep the last, possibly incomplete, line for the next iteration

                for (const line of lines) {
                    processLine(line);
                }

                if (isPreview && foundPreview) { // Use the flag instead of state
                    reader.cancel();
                    break;
                }
            }
        } catch (error) {
            console.error('There was a problem with the fetch operation:', error);
            alert(`An error occurred during generation: ${error instanceof Error ? error.message : String(error)}`);
            setCurrentStep(3); // Revert to a safe step on error
        } finally {
            setIsLoading(false);
        }
    };

    const handleSaveAndDownload = () => {
        if (finalCsv) {
            // Update the saved project with the final name
            saveProject('completed');
            
            const blob = new Blob([finalCsv], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            const url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            link.setAttribute('download', `${projectName.trim() || 'personalized_output'}.csv`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    };

    const placeholderText = `Example: Hi ${openBraces}FirstName${closeBraces}, I saw you work at ${openBraces}CompanyName${closeBraces} and wanted to reach out...`;

    return (
        <Card>
            <Flex direction="column" gap="4">
                {/* Step 1: Choose Workflow Type */}
                {currentStep === 1 && (
                    <Box>
                        <Heading as="h2" size="4" mb="1">Choose Your Starting Point</Heading>
                        <Text as="p" size="2" color="gray" mb="3">
                            Would you like to start with a template or create from scratch?
                        </Text>
                        <Grid columns="2" gap="4">
                            <Card 
                                style={{ 
                                    cursor: 'pointer', 
                                    border: workflowType === 'template' ? '2px solid var(--accent-9)' : '1px solid var(--gray-6)',
                                    transition: 'all 0.2s'
                                }}
                                onClick={() => {
                                    setWorkflowType('template');
                                    setCurrentStep(2);
                                }}
                            >
                                <Flex direction="column" gap="2" align="center" p="4">
                                    <Heading size="3">Use a Template</Heading>
                                    <Text size="2" color="gray" align="center">
                                        Start with pre-written emails and customize them
                                    </Text>
                                </Flex>
                            </Card>
                            <Card 
                                style={{ 
                                    cursor: 'pointer', 
                                    border: workflowType === 'scratch' ? '2px solid var(--accent-9)' : '1px solid var(--gray-6)',
                                    transition: 'all 0.2s'
                                }}
                                onClick={() => {
                                    setWorkflowType('scratch');
                                    setCurrentStep(2);
                                }}
                            >
                                <Flex direction="column" gap="2" align="center" p="4">
                                    <Heading size="3">Start from Scratch</Heading>
                                    <Text size="2" color="gray" align="center">
                                        Write your own template with full control
                                    </Text>
                                </Flex>
                            </Card>
                        </Grid>
                    </Box>
                )}

                {/* Recent Projects Section */}
                {currentStep === 1 && savedProjects.length > 0 && (
                    <Box mt="6">
                        <Heading as="h3" size="4" mb="3">Recent Projects</Heading>
                        <Grid columns={{ initial: '1', md: '2' }} gap="3">
                            {savedProjects.map(project => (
                                <Card 
                                    key={project.id}
                                    style={{ 
                                        cursor: 'pointer',
                                        transition: 'all 0.2s'
                                    }}
                                    onClick={() => loadProject(project)}
                                >
                                    <Flex justify="between" align="start">
                                        <Box>
                                            <Flex align="center" gap="2" mb="1">
                                                <Text weight="medium">{project.name}</Text>
                                                <Badge 
                                                    color={project.status === 'completed' ? 'green' : 'orange'} 
                                                    variant="soft"
                                                    size="1"
                                                >
                                                    {project.status === 'completed' ? (
                                                        <Flex align="center" gap="1">
                                                            <CheckCircledIcon width="12" height="12" />
                                                            Completed
                                                        </Flex>
                                                    ) : (
                                                        <Flex align="center" gap="1">
                                                            <ClockIcon width="12" height="12" />
                                                            Processing
                                                        </Flex>
                                                    )}
                                                </Badge>
                                            </Flex>
                                            <Text size="1" color="gray">
                                                {new Date(project.createdAt).toLocaleString()}
                                            </Text>
                                            {project.rowCount && (
                                                <Text size="1" color="gray">
                                                    {project.rowCount} rows
                                                </Text>
                                            )}
                                        </Box>
                                        <IconButton
                                            size="1"
                                            variant="ghost"
                                            color="red"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                if (window.confirm('Delete this project?')) {
                                                    deleteProject(project.id);
                                                }
                                            }}
                                        >
                                            <TrashIcon />
                                        </IconButton>
                                    </Flex>
                                </Card>
                            ))}
                        </Grid>
                    </Box>
                )}

                {/* Template Workflow - Step 2: Select Template */}
                {workflowType === 'template' && currentStep === 2 && (
                    <Box>
                        <Flex justify="between" align="center" mb="1">
                            <Heading as="h2" size="4">Step 1: Select Email Templates</Heading>
                            <Button 
                                size="2" 
                                variant="ghost"
                                onClick={() => navigate('/template-manager')}
                            >
                                <GearIcon />
                                Manage Templates
                            </Button>
                        </Flex>
                        <Text as="p" size="2" color="gray" mb="3">
                            Choose one or more templates. You can combine multiple templates for different scenarios.
                        </Text>
                        
                        {isLoadingTemplates ? (
                            <Flex justify="center" p="4">
                                <Spinner />
                            </Flex>
                        ) : templates.length === 0 ? (
                            <Card>
                                <Flex direction="column" align="center" gap="3" p="4">
                                    <Text color="gray">No templates available yet.</Text>
                                    <Button onClick={() => navigate('/template-manager')}>
                                        Create Templates
                                    </Button>
                                </Flex>
                            </Card>
                        ) : (
                            <Flex direction="column" gap="3">
                                {templates.map(template => (
                                    <Card 
                                        key={template.id}
                                        style={{ 
                                            cursor: 'pointer',
                                            border: selectedTemplates.includes(template.id) ? '2px solid var(--accent-9)' : '1px solid var(--gray-6)',
                                            transition: 'all 0.2s'
                                        }}
                                    >
                                        <Flex gap="3" align="start">
                                            <Checkbox
                                                checked={selectedTemplates.includes(template.id)}
                                                onCheckedChange={() => handleTemplateToggle(template.id)}
                                            />
                                            <Box style={{ flex: 1 }} onClick={() => handleTemplateToggle(template.id)}>
                                                <Text weight="medium" size="3">{template.name}</Text>
                                                <Text size="2" color="gray" mt="1">{template.goal}</Text>
                                            </Box>
                                        </Flex>
                                    </Card>
                                ))}
                            </Flex>
                        )}
                        
                        <Flex gap="3" mt="4">
                            <Button 
                                onClick={() => setCurrentStep(3)}
                                disabled={selectedTemplates.length === 0}
                            >
                                Continue ({selectedTemplates.length} selected)
                            </Button>
                            <Button 
                                variant="ghost" 
                                onClick={() => {
                                    setCurrentStep(1);
                                    setWorkflowType(null);
                                    setSelectedTemplates([]);
                                }}
                            >
                                ← Back
                            </Button>
                        </Flex>
                    </Box>
                )}

                {/* Template Workflow - Step 3: Fill Manual Fields */}
                {workflowType === 'template' && currentStep === 3 && (Object.keys(manualFields).length > 0 || !selectedAgent) && (
                    <Box>
                        <Heading as="h2" size="4" mb="1">Step 2: Fill in Template Fields</Heading>
                        <Text as="p" size="2" color="gray" mb="3">
                            Please fill in the following fields for your template:
                        </Text>
                        
                        {/* Agent Selector */}
                        <Box mb="4">
                            <Text size="2" weight="medium" mb="1">Select Agent</Text>
                            <Select.Root value={selectedAgent} onValueChange={setSelectedAgent}>
                                <Select.Trigger placeholder="Choose an agent for email signature..." />
                                <Select.Content>
                                    {AGENTS.map(agent => (
                                        <Select.Item key={agent.id} value={agent.id}>
                                            {agent.name} - {agent.phone}
                                        </Select.Item>
                                    ))}
                                </Select.Content>
                            </Select.Root>
                            <Text size="1" color="gray" mt="1">
                                This will populate [[AssociateName]] and [[ContactInfo]] in your emails
                            </Text>
                        </Box>
                        
                        <Flex direction="column" gap="3">
                            {Object.keys(manualFields).map(field => (
                                <Box key={field}>
                                    <Text size="2" weight="medium" mb="1">{field}</Text>
                                    <TextField.Root
                                        value={manualFields[field]}
                                        onChange={(e) => setManualFields({
                                            ...manualFields,
                                            [field]: e.target.value
                                        })}
                                        placeholder={`Enter ${field}...`}
                                    />
                                </Box>
                            ))}
                        </Flex>
                        <Flex gap="3" mt="4">
                            <Button 
                                onClick={() => setCurrentStep(4)}
                                disabled={Object.values(manualFields).some(v => !v.trim()) || !selectedAgent}
                            >
                                Continue
                            </Button>
                            <Button 
                                variant="ghost" 
                                onClick={() => setCurrentStep(2)}
                            >
                                ← Back
                            </Button>
                        </Flex>
                    </Box>
                )}

                {/* Step for Upload CSV (both workflows) */}
                {((workflowType === 'scratch' && currentStep === 2) || 
                  (workflowType === 'template' && (currentStep === 3 || currentStep === 4))) && !csvFile && (
                    <Box>
                        <Heading as="h2" size="4" mb="1">
                            {workflowType === 'template' ? 'Step 3: Upload Your Data' : 'Step 1: Upload Your Data'}
                        </Heading>
                        <Text as="p" size="2" color="gray" mb="3">
                            Upload a CSV file with your contact data. Make sure it has a header row.
                        </Text>
                        <FileInput onFileSelect={handleFileSelect} disabled={false} />
                        <Button 
                            variant="ghost" 
                            onClick={() => {
                                if (workflowType === 'template') {
                                    setCurrentStep(3);
                                } else {
                                    setCurrentStep(1);
                                }
                            }}
                        >
                            ← Back
                        </Button>
                    </Box>
                )}

                {csvFile && <Text mt="2" size="2" color="green">File selected: {csvFile.name}</Text>}

                {/* Scratch Workflow - Select Key Fields */}
                {workflowType === 'scratch' && currentStep === 3 && csvFile && (
                    <Box>
                        <Heading as="h2" size="4" mb="1" mt="4">Step 2: Select Key Fields</Heading>
                        <Text as="p" size="2" color="gray" mb="3">
                            Check the fields for direct replacements. Click any field name to insert it into your template.
                        </Text>
                        <Grid columns={{ initial: '1', sm: '2', md: '3' }} gap="3">
                            {csvHeaders.map(header => (
                                <Text as="label" size="2" key={header} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                    <Checkbox
                                        checked={keyFields.includes(header)}
                                        onCheckedChange={(checked) => handleKeyFieldChange(header, checked as boolean)}
                                    />
                                    <Text 
                                        onClick={() => insertFieldPlaceholder(header)}
                                        style={{ 
                                            cursor: 'pointer', 
                                            color: 'var(--accent-9)',
                                            textDecoration: 'underline',
                                            userSelect: 'none'
                                        }}
                                    >
                                        {header}
                                    </Text>
                                </Text>
                            ))}
                        </Grid>
                        <Button onClick={() => setCurrentStep(4)} mt="3">Continue</Button>
                    </Box>
                )}
                
                {/* Scratch Workflow - Create Content */}
                {workflowType === 'scratch' && currentStep === 4 && (
                    <Box>
                        <Heading as="h2" size="4" mb="1" mt="4">
                            Step 3: Write Your Smart Template
                        </Heading>
                        <Text as="p" size="2" color="gray" mb="3">
                            Write your template. Click field names above to insert them.
                        </Text>
                        
                        {/* Agent Selector */}
                        <Box mb="4">
                            <Text size="2" weight="medium" mb="1">Select Agent</Text>
                            <Select.Root value={selectedAgent} onValueChange={setSelectedAgent}>
                                <Select.Trigger placeholder="Choose an agent for email signature..." />
                                <Select.Content>
                                    {AGENTS.map(agent => (
                                        <Select.Item key={agent.id} value={agent.id}>
                                            {agent.name} - {agent.phone}
                                        </Select.Item>
                                    ))}
                                </Select.Content>
                            </Select.Root>
                            <Text size="1" color="gray" mt="1">
                                This will populate [[AssociateName]] and [[ContactInfo]] in your emails
                            </Text>
                        </Box>
                        
                        <TextArea
                            id="core-content"
                            name="core-content"
                            placeholder={placeholderText}
                            value={coreContent}
                            onChange={(e) => setCoreContent(e.target.value)}
                            rows={10}
                            style={{ marginBottom: '1rem' }}
                            ref={textAreaRef}
                        />

                        <Heading as="h3" size="3" mb="1" mt="2">
                            Optional: Overall Goal
                        </Heading>
                        <Text as="p" size="2" color="gray" mb="3">
                            Provide high-level instructions for the AI.
                        </Text>
                        <TextArea
                            id="generation-goal"
                            name="generation-goal"
                            placeholder="e.g., Personalize based on their company's recent news."
                            value={generationGoal}
                            onChange={(e) => setGenerationGoal(e.target.value)}
                            rows={3}
                            style={{ marginBottom: '1rem' }}
                        />

                        <Flex gap="3">
                            <Button onClick={() => handleGenerate(true)} disabled={isLoading || !coreContent} mt="3">
                                {isLoading ? <Spinner /> : 'Preview First Row'}
                            </Button>
                            <Button variant="ghost" onClick={() => setCurrentStep(3)} mt="3">
                                ← Back
                            </Button>
                        </Flex>
                    </Box>
                )}

                {/* Template Workflow - Review and Customize */}
                {workflowType === 'template' && currentStep === 4 && csvFile && (
                    <Box>
                        <Heading as="h2" size="4" mb="1" mt="4">
                            Step 4: Review and Customize Templates
                        </Heading>
                        <Text as="p" size="2" color="gray" mb="3">
                            Your selected templates with filled manual fields. CSV fields will be auto-replaced.
                        </Text>
                        
                        {/* Show selected templates */}
                        <Card mb="3">
                            <Text size="2" weight="medium" mb="2">Selected Templates:</Text>
                            <Flex gap="2" wrap="wrap">
                                {selectedTemplates.map(templateId => {
                                    const template = templates.find(t => t.id === templateId);
                                    return template ? (
                                        <Badge key={template.id} size="2" variant="soft">
                                            {template.name}
                                        </Badge>
                                    ) : null;
                                })}
                            </Flex>
                        </Card>
                        
                        <Card mb="3">
                            <Text size="2" weight="medium" mb="2">Available CSV Fields (click to insert):</Text>
                            <Flex gap="2" wrap="wrap">
                                {csvHeaders.map(header => (
                                    <Button
                                        key={header}
                                        size="1"
                                        variant="soft"
                                        onClick={() => insertFieldPlaceholder(header)}
                                    >
                                        {header}
                                    </Button>
                                ))}
                            </Flex>
                        </Card>
                        
                        <TextArea
                            id="core-content"
                            name="core-content"
                            value={coreContent}
                            onChange={(e) => setCoreContent(e.target.value)}
                            rows={15}
                            style={{ marginBottom: '1rem' }}
                            ref={textAreaRef}
                        />

                        <Heading as="h3" size="3" mb="1" mt="2">
                            Optional: Additional AI Instructions
                        </Heading>
                        <TextArea
                            id="generation-goal"
                            name="generation-goal"
                            placeholder="e.g., Focus on their industry or location..."
                            value={generationGoal}
                            onChange={(e) => setGenerationGoal(e.target.value)}
                            rows={3}
                            style={{ marginBottom: '1rem' }}
                        />

                        <Flex gap="3">
                            <Button onClick={() => handleGenerate(true)} disabled={isLoading || !coreContent}>
                                {isLoading ? <Spinner /> : 'Preview First Row'}
                            </Button>
                            <Button 
                                variant="ghost" 
                                onClick={() => {
                                    setCsvFile(null);
                                    setCurrentStep(Object.keys(manualFields).length > 0 ? 3 : 2);
                                }}
                            >
                                ← Back
                            </Button>
                        </Flex>
                    </Box>
                )}

                {/* Step 5: Preview */}
                {previewContent.length > 0 && currentStep >= 4 && (
                    <Box>
                        <Heading as="h2" size="4" mb="1" mt="4">Preview</Heading>
                        <Grid columns={{ initial: '1', md: '2' }} gap="3">
                            {previewContent.map((preview, index) => (
                                <Card key={index}>
                                    <Text size="2" weight="medium" mb="2">{preview.template}</Text>
                                    <Box className="markdown-preview" p="3" style={{ background: 'var(--gray-1)', borderRadius: 'var(--radius-2)', border: '1px solid var(--gray-4)' }}>
                                        <ReactMarkdown>{preview.content}</ReactMarkdown>
                                    </Box>
                                </Card>
                            ))}
                        </Grid>
                        <Button onClick={() => handleGenerate(false)} disabled={isLoading} mt="3">
                            {isLoading ? <Spinner /> : 'Looks Good! Generate Full CSV'}
                        </Button>
                    </Box>
                )}

                {/* Step 6: Processing/Download */}
                {currentStep === 6 && (
                    <Box>
                        {!finalCsv ? (
                            // Processing state
                            <Box>
                                <Heading as="h2" size="4" mb="1" mt="4">Processing Your Campaign...</Heading>
                                <Card>
                                    <Flex direction="column" align="center" gap="4" p="4">
                                        <Spinner size="3" />
                                        <Text size="3" weight="medium">Generating personalized emails for all rows</Text>
                                        <Text size="2" color="gray">
                                            This may take a few minutes. You can leave this page and come back later.
                                        </Text>
                                        <Text size="1" color="gray">
                                            Processing {rowCount} rows...
                                        </Text>
                                    </Flex>
                                </Card>
                            </Box>
                        ) : (
                            // Download state
                            <Box>
                                <Heading as="h2" size="4" mb="1" mt="4">Your Campaign is Ready!</Heading>
                                <Text as="p" size="2" color="gray" mb="3">
                                    Successfully generated {rowCount} personalized emails.
                                </Text>
                                
                                <Flex gap="3" align="end">
                                    <Box style={{ flex: 1 }}>
                                        <Text as="label" size="2" mb="1" weight="medium">
                                            Project Name
                                        </Text>
                                        <TextField.Root
                                            placeholder="e.g., Q4 Campaign Emails"
                                            value={projectName}
                                            onChange={(e) => setProjectName(e.target.value)}
                                        />
                                    </Box>
                                    <Button onClick={handleSaveAndDownload} disabled={!projectName.trim()}>
                                        <DownloadIcon />
                                        Save & Download CSV
                                    </Button>
                                </Flex>
                                
                                <Text size="1" color="gray" mt="2">
                                    Your CSV contains all personalized emails. Each row is a complete email ready to send.
                                </Text>
                            </Box>
                        )}
                    </Box>
                )}
            </Flex>
        </Card>
    );
}; 
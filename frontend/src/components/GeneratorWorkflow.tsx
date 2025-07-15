import { Box, Card, Text, Button, Flex, TextArea, Select, Spinner, Checkbox, Heading, Grid, TextField, Badge } from '@radix-ui/themes';
import { UploadIcon, DownloadIcon, ChevronDownIcon } from '@radix-ui/react-icons';
import { useState, useRef, ChangeEvent, useEffect } from 'react';
import Papa from 'papaparse';
import ReactMarkdown from 'react-markdown';

// Email templates
const EMAIL_TEMPLATES = {
    roadshow1: {
        name: "Roadshow 1 - Marketing Campaign Ramp Up",
        content: `Hi {{MM}},

{{City}} is in [[DaysUntilEvent]] days, and we are ramping up to begin our marketing campaign! As soon as you secure a friendly (Existing cast member/Realtor, Mortgage) please add them to the bottom of the {{City}} tab and highlight them in yellow. I will include them in the confirmation email and texts.

Thank you,
[[YourName]]`,
        goal: "Simple internal communication for marketing campaign coordination."
    },
    roadshow2: {
        name: "Roadshow 2 - Initial Outreach (Long)",
        content: `Hey {{FirstName}},
I've been asked to reach out to you, on behalf of my CEO and Executive Show Producer Craig Sewing.  
I'll keep this email short and sweet, as I know you're busy (just in case, please know this is a very real email here).
Craig did create a personal video message for you below that elaborates a bit:
[[VideoLink]]

After watching that, let me get you few more details…
You might know Craig, as he speaks at National real estate events, and was an Inman News Nominee for Most Influential in Real Estate, etc, etc. 
We've have a team that does some market research and outreach (me:), and you were referred to us as being reputable in real estate we should invite to learn about this.

My hope here is to set you up with an exploratory conversation about a new show coming into {{State}}, airing on HGTV and other major networks. 
A REAL show (not some reality TV drama thing), specifically about real estate and lifestyles, showing us the neighborhoods you sell real estate.

I do intend to call and text you as well, but figured an email makes it easier to explain, and get a reply on what you think. 
Specifically, Craig is flying into [[DestinationCity]] next week and I am responsible for coordinating some private meetings.   
He could do this with you on zoom, but he wants to meet with you if you're up for it.   
You were referred to us as someone that we should try to connect with (fyi, I have a short list of others I am reaching out to as well).

As for me, I am the associate producer for the New TV Show that will be featured on HGTV and the Travel Channel called, "Selling {{State}}"
A real show, not some reality TV thing, and honestly its a media model developed by some of the leaders in the real estate industry.  A really cool show, and concept.

It will air on TV, and showcase the cool real estate, neighborhoods, and lifestyles of {{State}} and the surrounding markets, through the lens of real estate professionals.
We've done previous shows and models in {{State}}, but NOT this.  
This is brand new to your market, and a really cool show concept we'd love to explore with you. 

We just aligned with HGTV and are looking for experts in the different micro markets of {{State}} and ALL the surrounding areas ([[ExampleCities]] to name a few NOT limited to these markets)

The show is a 2x EMMY Nominated 12x Telly Award Winning production, that garners millions of views.  
Again, A REAL show, with REAL professionals (not some drama filled reality TV.)
 
We are opening conversations with potential real estate professionals to be featured as "THE VOICE" for why people love where you live.  Pretty fun show and concept! And if it matters, the agents who get chosen tend to get a lot of referrals. 
To add some color, here is a RECENT PROMO of the show featuring real estate industry leaders, and another PROMO that features some of our real estate experts in other cities.  
Some of your industry leaders who've been on the show:  Tom Ferry, Mike Ferry, Robert Reffkin, Grant & Elena Cardone, Shannon Gillette, Ryan Serhant, to name a few…

For further validation if needed, here is the Facebook and Instagram page for the 2xEMMY nominated media network that will be producing the show.  
Click here for Instagram
Click here for Facebook

As I mentioned, our CEO Craig Sewing is holding meetings for some reputable agents, and would like to have a conversation with you.
No strings attached.
Just a casual meeting, and conversation to explain, answer all of your questions, and see if its a good fit.  If not, no worries.`,
        goal: "Comprehensive initial outreach explaining the show opportunity, establishing credibility, and requesting a meeting."
    },
    roadshow3: {
        name: "Roadshow 3 - SMS/Short Follow-up",
        content: `Hi - my name is [[YourName]].  I'm with ADTV Network.  We are launching a new show in {{City}} focusing on real estate, lifestyle and culture.  We are already airing in other markets across the country and are excited to come to your area.  My CEO Craig Sewing is flying into town/hosting a web meeting next week and would love to meet with you about it.  I sent you an email with all the details yesterday. If you didn't receive it, please text me with your email address at this number [[YourPhoneNumber]] and I'll be happy to re-send. Thanks, and I hope to see you there!`,
        goal: "Brief follow-up message suitable for SMS or quick email to ensure initial email was received."
    },
    roadshow4: {
        name: "Roadshow 4 - Meeting Scheduling",
        content: `{{FirstName}}, can you meet next [[MeetingDays]]? [[SpecificDates]]

Hi {{FirstName}}, 

I just wanted to check in as I sent an email last week and I wanted to make sure you received it! 

I'm a Producer for an Emmy nominated, national TV show centered around Real Estate and Lifestyle. We are in the process of launching a new show in {{City}} (and surrounding markets). The email I sent outlines all the details, so I'll keep this note short and sweet just in case you did see it and maybe wrote it off as spam. Let me know if you didn't receive it and I am happy to send it again if needed. 

Our CEO and Executive Producer, Craig Sewing, is flying into {{City}} next week and would like to meet with you to discuss potentially being considered as a market expert to host in {{City}}. 

As of now, Craig is available at the following dates/times below at [[HotelName]]:

[[AvailableDateTimes]]

Let me know which works best for you, and I can follow up with the calendar invitation and confirm your meeting with Craig. 

Craig recorded this video message for you that explains the show further:

[[CraigVideoLink]]

If you don't think you'd be a good fit, no worries, just let me know so I can reach out to others more interested. Thank you so much, and have a wonderful rest of your day!`,
        goal: "Follow-up email to schedule specific meeting times with Craig Sewing, includes video link and specific availability."
    },
    roadshow5: {
        name: "Roadshow 5 - Pre-Meeting Confirmation",
        content: `Sneak Peek of ADTV Network - "Selling {{City}}"

Hi {{FirstName}},

We want to share with you the official ADTV Network - "Selling {{City}}" promo!! We are excited to meet you next week, [[MeetingDateTime]] at the [[Location]]

[[PromoVideoLink]]

P.S. While you are out showing property, feel free to share this promo with your clients, and tell them you are being considered to represent {{City}} on a national Emmy nominated, Telly award winning TV show.`,
        goal: "Pre-meeting excitement builder with promo video, confirming meeting details."
    },
    followup: {
        name: "General Follow-Up Template",
        content: `Hello {{FirstName}},

I wanted to follow up on our previous conversation about {{Topic}}. I hope this email finds you well.

{{PersonalizedContent}}

Looking forward to hearing from you.

Best,
{{SenderName}}`,
        goal: "Create a personalized follow-up message based on previous interactions and current context."
    },
    introduction: {
        name: "Introduction Email",
        content: `Dear {{FirstName}},

I hope this email finds you well. My name is [[YourName]] from [[YourCompany]], and I'm reaching out because {{ReasonForContact}}.

{{PersonalizedIntro}}

I believe there could be great synergy between {{TheirCompany}} and what we're doing at [[YourCompany]].

{{CallToAction}}

Would you be available for a brief call next week to discuss this further?

Best regards,
[[YourName]]
[[YourTitle]]
[[YourCompany]]`,
        goal: "Professional introduction email for new contacts. Personalize based on their company and background."
    }
};

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
            if (/[",\\n]/.test(str)) {
                return `"${str.replace(/"/g, '""')}"`;
            }
            return str;
        }).join(',')
    ).join('\\r\\n');
};

export const GeneratorWorkflow = () => {
    const [csvFile, setCsvFile] = useState<File | null>(null);
    const [csvHeaders, setCsvHeaders] = useState<string[]>([]);
    const [keyFields, setKeyFields] = useState<string[]>([]);
    const [currentStep, setCurrentStep] = useState(1);
    const [coreContent, setCoreContent] = useState('');
    const [generationGoal, setGenerationGoal] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [previewContent, setPreviewContent] = useState('');
    const [finalCsv, setFinalCsv] = useState<string | null>(null);
    const [selectedTemplates, setSelectedTemplates] = useState<string[]>([]);
    const [workflowType, setWorkflowType] = useState<'template' | 'scratch' | null>(null);
    const [manualFields, setManualFields] = useState<Record<string, string>>({});
    
    // Ref for the textarea to handle cursor position
    const textAreaRef = useRef<HTMLTextAreaElement>(null);

    const openBraces = '{{';
    const closeBraces = '}}';

    // Extract fields that need manual input from template content
    const extractManualFields = (content: string): string[] => {
        const regex = /\[\[([^\]]+)\]\]/g;
        const fields: string[] = [];
        let match;
        while ((match = regex.exec(content)) !== null) {
            if (!fields.includes(match[1])) {
                fields.push(match[1]);
            }
        }
        return fields;
    };

    // Get all manual fields from all selected templates
    const getAllManualFields = (): string[] => {
        const allFields: string[] = [];
        selectedTemplates.forEach(templateKey => {
            const template = EMAIL_TEMPLATES[templateKey as keyof typeof EMAIL_TEMPLATES];
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
        return selectedTemplates.map(templateKey => {
            const template = EMAIL_TEMPLATES[templateKey as keyof typeof EMAIL_TEMPLATES];
            return template ? template.content : '';
        }).join('\n\n---\n\n');
    };

    // Replace manual fields in content
    const replaceManualFields = (content: string): string => {
        let updatedContent = content;
        Object.entries(manualFields).forEach(([field, value]) => {
            const regex = new RegExp(`\\[\\[${field}\\]\\]`, 'g');
            updatedContent = updatedContent.replace(regex, value);
        });
        return updatedContent;
    };

    const handleFileSelect = (file: File) => {
        setCsvFile(file);
        Papa.parse(file, {
            header: true,
            skipEmptyLines: true,
            preview: 1, // We only need the headers, so we only parse one row
            complete: (results: Papa.ParseResult<Record<string, unknown>>) => {
                if (results.meta.fields) {
                    setCsvHeaders(results.meta.fields);
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
    const handleTemplateToggle = (templateKey: string) => {
        if (selectedTemplates.includes(templateKey)) {
            // Remove template
            setSelectedTemplates(selectedTemplates.filter(t => t !== templateKey));
        } else {
            // Add template
            setSelectedTemplates([...selectedTemplates, templateKey]);
        }
        
        // Update manual fields for all selected templates
        const allFields = getAllManualFieldsForTemplates(
            selectedTemplates.includes(templateKey) 
                ? selectedTemplates.filter(t => t !== templateKey)
                : [...selectedTemplates, templateKey]
        );
        
        const newManualFields: Record<string, string> = {};
        allFields.forEach(field => {
            newManualFields[field] = manualFields[field] || '';
        });
        setManualFields(newManualFields);
    };

    // Helper function to get manual fields for specific templates
    const getAllManualFieldsForTemplates = (templates: string[]): string[] => {
        const allFields: string[] = [];
        templates.forEach(templateKey => {
            const template = EMAIL_TEMPLATES[templateKey as keyof typeof EMAIL_TEMPLATES];
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
            const combinedContent = selectedTemplates.map(templateKey => {
                const template = EMAIL_TEMPLATES[templateKey as keyof typeof EMAIL_TEMPLATES];
                return template ? template.content : '';
            }).join('\n\n---\n\n');
            setCoreContent(combinedContent);
            
            // Set combined goals
            const goals = selectedTemplates.map(templateKey => {
                const template = EMAIL_TEMPLATES[templateKey as keyof typeof EMAIL_TEMPLATES];
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
        setPreviewContent('');
        setFinalCsv(null);
        if (isPreview) {
            setCurrentStep(currentStep); // Stay on current step for preview
        } else {
            setCurrentStep(6); // Move to generating step
        }

        const formData = new FormData();
        formData.append('file', csvFile);
        formData.append('key_fields', JSON.stringify(keyFields));
        formData.append('core_content', processedContent);
        formData.append('is_preview', String(isPreview));
        formData.append('generation_goal', generationGoal);

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

            const processLine = (line: string) => {
                if (line.trim() === '') return;
                try {
                    const parsed = JSON.parse(line);
                    if (parsed.type === 'error') throw new Error(parsed.detail || 'An error occurred during generation.');
                    if (parsed.type === 'header') header = parsed.data;
                    else if (parsed.type === 'row') {
                        if (isPreview) {
                            const contentIndex = header.indexOf('ai_generated_content');
                            setPreviewContent(contentIndex > -1 ? parsed.data[contentIndex] : "Could not extract content.");
                            setCurrentStep(4);
                        } else {
                            if (csvRows.length === 0) csvRows.push(header);
                            csvRows.push(parsed.data);
                        }
                    } else if (parsed.type === 'done' && !isPreview) {
                        const csvString = arrayToCsv(csvRows);
                        setFinalCsv(csvString);
                        setCurrentStep(5);
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

                if (isPreview && previewContent) {
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

    const handleDownload = () => {
        if (finalCsv) {
            const blob = new Blob([finalCsv], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            const url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            link.setAttribute('download', 'personalized_output.csv');
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

                {/* Template Workflow - Step 2: Select Template */}
                {workflowType === 'template' && currentStep === 2 && (
                    <Box>
                        <Heading as="h2" size="4" mb="1">Step 1: Select Email Templates</Heading>
                        <Text as="p" size="2" color="gray" mb="3">
                            Choose one or more templates. You can combine multiple templates for different scenarios.
                        </Text>
                        
                        <Flex direction="column" gap="3">
                            {Object.entries(EMAIL_TEMPLATES).map(([key, template]) => (
                                <Card 
                                    key={key}
                                    style={{ 
                                        cursor: 'pointer',
                                        border: selectedTemplates.includes(key) ? '2px solid var(--accent-9)' : '1px solid var(--gray-6)',
                                        transition: 'all 0.2s'
                                    }}
                                >
                                    <Flex gap="3" align="start">
                                        <Checkbox
                                            checked={selectedTemplates.includes(key)}
                                            onCheckedChange={() => handleTemplateToggle(key)}
                                        />
                                        <Box style={{ flex: 1 }} onClick={() => handleTemplateToggle(key)}>
                                            <Text weight="medium" size="3">{template.name}</Text>
                                            <Text size="2" color="gray" mt="1">{template.goal}</Text>
                                        </Box>
                                    </Flex>
                                </Card>
                            ))}
                        </Flex>
                        
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
                {workflowType === 'template' && currentStep === 3 && Object.keys(manualFields).length > 0 && (
                    <Box>
                        <Heading as="h2" size="4" mb="1">Step 2: Fill in Template Fields</Heading>
                        <Text as="p" size="2" color="gray" mb="3">
                            Please fill in the following fields for your template:
                        </Text>
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
                                disabled={Object.values(manualFields).some(v => !v.trim())}
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
                                if (workflowType === 'template' && Object.keys(manualFields).length > 0) {
                                    setCurrentStep(3);
                                } else if (workflowType === 'template') {
                                    setCurrentStep(2);
                                } else {
                                    setCurrentStep(1);
                                    setWorkflowType(null);
                                }
                            }}
                            mt="3"
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
                                {selectedTemplates.map(templateKey => {
                                    const template = EMAIL_TEMPLATES[templateKey as keyof typeof EMAIL_TEMPLATES];
                                    return template ? (
                                        <Badge key={templateKey} size="2" variant="soft">
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
                {previewContent && (
                    <Box>
                        <Heading as="h2" size="4" mb="1" mt="4">Step 5: Preview</Heading>
                        <Card>
                            <Box className="markdown-preview" p="3">
                                <ReactMarkdown>{previewContent}</ReactMarkdown>
                            </Box>
                        </Card>
                        <Button onClick={() => handleGenerate(false)} disabled={isLoading} mt="3">
                            {isLoading ? <Spinner /> : 'Looks Good! Generate Full CSV'}
                        </Button>
                    </Box>
                )}

                {/* Step 6: Download */}
                {currentStep === 6 && finalCsv && (
                    <Box>
                        <Heading as="h2" size="4" mb="1" mt="4">Step 6: Download Your File</Heading>
                        <Text as="p" size="2" color="gray" mb="3">
                            Your personalized CSV is ready.
                        </Text>
                        <Button onClick={handleDownload}>
                            <DownloadIcon />
                            Download Personalized CSV
                        </Button>
                    </Box>
                )}
            </Flex>
        </Card>
    );
}; 
import React, { useState } from 'react';
import { Flex, IconButton, TextField, TextArea } from '@radix-ui/themes';
import { ArrowRightIcon, Share2Icon, CalendarIcon, LayersIcon } from '@radix-ui/react-icons';
import { DataSourcesPopup } from './DataSourcesPopup';
import { DateSelectionPopup } from './DateSelectionPopup';
import { TemplateAgentsPopup } from './TemplateAgentsPopup';
import api from '../api';

interface CommandCenterProps {
  onSend: (query: string) => void;
  isLoading: boolean;
}

export const CommandCenter = ({ onSend, isLoading }: CommandCenterProps) => {
    const [input, setInput] = useState('');
    const [activePopup, setActivePopup] = useState<string | null>(null);
    const [activeTemplate, setActiveTemplate] = useState<string | null>(null);

    const handleSendClick = async () => {
        if (input.trim()) {
            let finalQuery = input;
            
            // Handle different template types
            if (activeTemplate === 'roadshow' && input.includes('What is your primary geographic market?')) {
                // Hardcoded Roadshow template
                finalQuery = `Please help me write a personalized response email based on the following information from a potential host for American Dream TV:

${input}

Please write a warm, enthusiastic response that:
1. Thanks them for their response and acknowledges their passion for their market
2. Shows genuine interest in their unique story/initiatives (especially any community involvement)
3. Mentions their segment ideas positively
4. Reminds them to complete the DocuSign agreement if they haven't already
5. Clarifies that signing doesn't guarantee selection but helps with due diligence
6. Ends with excitement about possibilities ahead

Keep the tone professional but warm, similar to this example length and style:
"Thank you for your enthusiastic response and for sharing such a heartfelt vision for representing [location]. Your passion for [specific thing they mentioned] really shines through, and it's inspiring to see [specific initiative/commitment]. [Comment on their segment ideas]. If you haven't already, please be sure to complete the DocuSign agreement sent your way to solidify your interest. Remember, signing doesn't guarantee selection as host, but it really helps put you in the best position as we move forward with our due diligence. Thanks again for taking the time to share what makes you and your market special — we're excited about the possibilities ahead and look forward to connecting further."`;
            } else if (activeTemplate?.startsWith('custom_')) {
                // Custom template - fetch the full prompt
                const templateId = activeTemplate.replace('custom_', '');
                try {
                    const response = await api.get(`/template-agents/${templateId}`);
                    const fullPrompt = response.data.prompt_template;
                    
                    // Replace the questions portion with the user's filled answers
                    const lines = fullPrompt.split('\n');
                    let finalPrompt = '';
                    let inQuestionSection = true;
                    
                    for (const line of lines) {
                        if (inQuestionSection && (line.includes('?') || line.includes('>'))) {
                            // Skip template questions, we'll use the user's filled version
                            continue;
                        } else if (inQuestionSection && !line.includes('?') && !line.includes('>') && line.trim() !== '') {
                            // Found the start of instructions
                            inQuestionSection = false;
                            finalPrompt = input + '\n\n' + line + '\n';
                        } else if (!inQuestionSection) {
                            finalPrompt += line + '\n';
                        }
                    }
                    
                    finalQuery = finalPrompt.trim() || input;
                } catch (error) {
                    console.error('Failed to fetch template:', error);
                    // Fall back to just the input if we can't get the template
                    finalQuery = input;
                }
            }
            
            onSend(finalQuery);
            setInput('');
            setActiveTemplate(null);
        }
    };

    const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (event.key === 'Enter' && !event.shiftKey) {
          event.preventDefault();
          if (!isLoading && input.trim() !== '') {
            handleSendClick();
          }
        }
    };

    const togglePopup = (popupName: string) => {
        setActivePopup(prev => (prev === popupName ? null : popupName));
    };

    const handleTemplateSelect = (template: string, templateType?: string) => {
        setInput(template);
        setActiveTemplate(templateType || null);
        setActivePopup(null); // Close the popup
    };

    // Dynamically calculate rows based on content
    const calculateRows = () => {
        const lines = input.split('\n').length;
        return Math.min(Math.max(lines, 1), 10); // Min 1 row, max 10 rows
    };

    return (
        <Flex gap="3" align="center" style={{ position: 'relative' }}>
            {/* --- Text Input --- */}
            <TextArea
                placeholder="Ask a question or type a command..."
                style={{ flexGrow: 1, minHeight: '40px', resize: 'vertical' }}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={isLoading}
                rows={calculateRows()}
            />

            {/* --- Right-side Icons & Popups --- */}
            <Flex gap="5" align="center">
                <div style={{ position: 'relative' }}>
                    <IconButton variant="ghost" onClick={() => togglePopup('sources')} style={{ cursor: 'pointer', color: 'var(--gray-11)' }}>
                        <Share2Icon width={22} height={22} />
                    </IconButton>
                    {activePopup === 'sources' && <DataSourcesPopup />}
                </div>
                
                <div style={{ position: 'relative' }}>
                    <IconButton variant="ghost" onClick={() => togglePopup('date')} style={{ cursor: 'pointer', color: 'var(--gray-11)' }}>
                        <CalendarIcon width={22} height={22} />
                    </IconButton>
                    {activePopup === 'date' && <DateSelectionPopup />}
                </div>

                <div style={{ position: 'relative' }}>
                    <IconButton variant="ghost" onClick={() => togglePopup('agents')} style={{ cursor: 'pointer', color: 'var(--gray-11)' }}>
                        <LayersIcon width={22} height={22} />
                    </IconButton>
                    {activePopup === 'agents' && <TemplateAgentsPopup onSelectTemplate={handleTemplateSelect} />}
                </div>
            </Flex>

            {/* --- Send Button --- */}
            <IconButton
                color="blue"
                radius="full"
                onClick={handleSendClick}
                disabled={isLoading || input.trim() === ''}
                style={{ cursor: 'pointer' }}
            >
                <ArrowRightIcon width="18" height="18" />
            </IconButton>
        </Flex>
    );
}; 
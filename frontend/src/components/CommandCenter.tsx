import React, { useState } from 'react';
import { Flex, IconButton, TextField, TextArea } from '@radix-ui/themes';
import { ArrowRightIcon, Share2Icon, CalendarIcon, LayersIcon } from '@radix-ui/react-icons';
import { DataSourcesPopup } from './DataSourcesPopup';
import { DateSelectionPopup } from './DateSelectionPopup';
import { TemplateAgentsPopup } from './TemplateAgentsPopup';

interface CommandCenterProps {
  onSend: (query: string) => void;
  isLoading: boolean;
}

export const CommandCenter = ({ onSend, isLoading }: CommandCenterProps) => {
    const [input, setInput] = useState('');
    const [activePopup, setActivePopup] = useState<string | null>(null);

    const handleSendClick = () => {
        if (input.trim()) {
            onSend(input);
            setInput('');
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

    const handleTemplateSelect = (template: string) => {
        setInput(template);
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
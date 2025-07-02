import React, { useEffect, useState } from 'react';
import { Box, Flex, Text, Spinner } from '@radix-ui/themes';
import api from '../api';

const popupBoxStyle: React.CSSProperties = {
  position: 'absolute',
  bottom: 'calc(100% + 10px)',
  left: '50%',
  transform: 'translateX(-50%)',
  width: '300px',
  maxHeight: '400px',
  overflowY: 'auto',
  backgroundColor: 'white',
  borderRadius: 'var(--radius-3)',
  boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)',
  border: '1px solid var(--gray-a5)',
  padding: '1rem',
  zIndex: 10,
};

interface PopupItemProps {
  children: React.ReactNode;
  onClick?: () => void;
}

const PopupItem = ({ children, onClick }: PopupItemProps) => (
    <Text 
      as="div" 
      size="2" 
      style={{ 
        padding: '0.75rem', 
        borderRadius: 'var(--radius-2)', 
        cursor: 'pointer',
        transition: 'background-color 0.2s',
      }}
      className="template-item"
      onClick={onClick}
    >
        {children}
    </Text>
);

interface TemplateAgentsPopupProps {
  onSelectTemplate: (template: string, templateType?: string) => void;
}

interface TemplateAgent {
  id: string;
  name: string;
  prompt_template: string;
}

export const TemplateAgentsPopup = ({ onSelectTemplate }: TemplateAgentsPopupProps) => {
  const [templates, setTemplates] = useState<TemplateAgent[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      const response = await api.get('/template-agents');
      setTemplates(response.data);
    } catch (error) {
      console.error('Failed to fetch templates:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Hardcoded Roadshow template
  const roadshowQuestions = `What is your primary geographic market?
> 

Why would you like to host?
> 

Tell us anything you feel is important in our selection process:
> 

Do you have any segment ideas?
> `;

  const handleRoadshowClick = () => {
    onSelectTemplate(roadshowQuestions, 'roadshow');
  };

  const handleCustomTemplateClick = (template: TemplateAgent) => {
    // Extract just the questions part from the prompt template
    // The AI should have formatted it with questions followed by instructions
    const lines = template.prompt_template.split('\n');
    let questionsOnly = '';
    let foundQuestions = false;
    
    for (const line of lines) {
      // Look for lines that end with ? or contain >
      if (line.includes('?') || line.includes('>')) {
        foundQuestions = true;
        questionsOnly += line + '\n';
      } else if (foundQuestions && line.trim() === '') {
        // Keep empty lines between questions
        questionsOnly += '\n';
      } else if (foundQuestions && !line.includes('?') && !line.includes('>')) {
        // Stop when we hit instruction text
        break;
      }
    }

    // If we couldn't extract questions, use the full template
    const templateToUse = questionsOnly.trim() || template.prompt_template;
    
    // Pass the template ID so we can retrieve the full prompt later
    onSelectTemplate(templateToUse, `custom_${template.id}`);
  };

  return (
    <Box style={popupBoxStyle}>
      <Flex direction="column" gap="1">
        <Box px="2" mb="1">
            <Text as="div" size="2" weight="bold" color="gray">Template Agents</Text>
        </Box>
        
        {/* Hardcoded templates */}
        <PopupItem onClick={handleRoadshowClick}>
          Roadshow Communication
        </PopupItem>

        {/* Divider if there are custom templates */}
        {templates.length > 0 && (
          <Box style={{ borderTop: '1px solid var(--gray-a5)', margin: '0.5rem 0' }} />
        )}

        {/* User-created templates */}
        {isLoading ? (
          <Flex justify="center" p="3">
            <Spinner size="2" />
          </Flex>
        ) : (
          templates.map(template => (
            <PopupItem key={template.id} onClick={() => handleCustomTemplateClick(template)}>
              {template.name}
            </PopupItem>
          ))
        )}

        {!isLoading && templates.length === 0 && (
          <Text size="1" color="gray" style={{ padding: '0.5rem', textAlign: 'center' }}>
            No custom templates yet
          </Text>
        )}
      </Flex>
      <style>{`
        .template-item:hover {
          background-color: var(--gray-a3);
        }
      `}</style>
    </Box>
  );
}; 
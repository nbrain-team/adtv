import React from 'react';
import { Box, Flex, Text } from '@radix-ui/themes';

const popupBoxStyle: React.CSSProperties = {
  position: 'absolute',
  bottom: 'calc(100% + 10px)',
  left: '50%',
  transform: 'translateX(-50%)',
  width: '300px',
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

export const TemplateAgentsPopup = ({ onSelectTemplate }: TemplateAgentsPopupProps) => {
  // This is what the user sees and fills in
  const roadshowQuestions = `What is your primary geographic market?
> 

Why would you like to host?
> 

Tell us anything you feel is important in our selection process:
> 

Do you have any segment ideas?
> `;

  const handleRoadshowClick = () => {
    // Pass both the questions and the template type
    onSelectTemplate(roadshowQuestions, 'roadshow');
  };

  return (
    <Box style={popupBoxStyle}>
      <Flex direction="column" gap="1">
        <Box px="2" mb="1">
            <Text as="div" size="2" weight="bold" color="gray">Template Agents</Text>
        </Box>
        <PopupItem onClick={handleRoadshowClick}>
          Roadshow Communication
        </PopupItem>
      </Flex>
      <style>{`
        .template-item:hover {
          background-color: var(--gray-a3);
        }
      `}</style>
    </Box>
  );
}; 
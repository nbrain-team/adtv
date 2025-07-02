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
  onSelectTemplate: (template: string) => void;
}

export const TemplateAgentsPopup = ({ onSelectTemplate }: TemplateAgentsPopupProps) => {
  const roadshowTemplate = `Please help me write a personalized response email based on the following information from a potential host for American Dream TV:

What is your primary geographic market?
> [Their answer here]

Why would you like to host?
> [Their answer here]

Tell us anything you feel is important in our selection process:
> [Their answer here]

Do you have any segment ideas?
> [Their answer here]

Please write a warm, enthusiastic response that:
1. Thanks them for their response and acknowledges their passion for their market
2. Shows genuine interest in their unique story/initiatives (especially any community involvement)
3. Mentions their segment ideas positively
4. Reminds them to complete the DocuSign agreement if they haven't already
5. Clarifies that signing doesn't guarantee selection but helps with due diligence
6. Ends with excitement about possibilities ahead

Keep the tone professional but warm, similar to this example length and style:
"Thank you for your enthusiastic response and for sharing such a heartfelt vision for representing [location]. Your passion for [specific thing they mentioned] really shines through, and it's inspiring to see [specific initiative/commitment]. [Comment on their segment ideas]. If you haven't already, please be sure to complete the DocuSign agreement sent your way to solidify your interest. Remember, signing doesn't guarantee selection as host, but it really helps put you in the best position as we move forward with our due diligence. Thanks again for taking the time to share what makes you and your market special — we're excited about the possibilities ahead and look forward to connecting further."`;

  return (
    <Box style={popupBoxStyle}>
      <Flex direction="column" gap="1">
        <Box px="2" mb="1">
            <Text as="div" size="2" weight="bold" color="gray">Template Agents</Text>
        </Box>
        <PopupItem onClick={() => onSelectTemplate(roadshowTemplate)}>
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
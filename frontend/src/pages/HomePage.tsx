import { Box, Flex, Text, ScrollArea, IconButton, Heading } from '@radix-ui/themes';
import { CommandCenter } from '../components/CommandCenter';
import { ClientSelector } from '../components/ClientSelector';
import { useState } from 'react';
import type { Dispatch, SetStateAction } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { PersonIcon } from '@radix-ui/react-icons';
import { MainLayout } from '../components/MainLayout';

// Make this interface flexible to avoid conflict with App.tsx
interface Message {
  text: string;
  sender: 'user' | 'ai';
  sources?: (string | { source: string })[];
}

interface HomePageProps {
    messages: Message[];
    setMessages: Dispatch<SetStateAction<Message[]>>;
}

const HomePage = ({ messages, setMessages }: HomePageProps) => {
    const [isLoading, setIsLoading] = useState(false);
    const [selectedClientItemId, setSelectedClientItemId] = useState<number | null>(null);
    const { logout } = useAuth();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const handleNewChat = () => {
        setMessages([]);
    };

    const handleSendMessage = async (query: string) => {
        if (!query.trim()) return;

        const newUserMessage: Message = { text: query, sender: 'user' };
        setMessages(prev => [...prev, newUserMessage]);
        setIsLoading(true);

        try {
            const token = localStorage.getItem('token');
            if (!token) {
                // This should ideally not happen if the user is on this page,
                // but it's a good safeguard.
                throw new Error("Authentication token not found.");
            }

            const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/chat/stream?token=${token}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
                body: JSON.stringify({
                    query: query,
                    history: messages,
                    use_mcp: true,
                    include_sources: ["pinecone", "customer_service", "podio"],
                    podio_client_item_id: selectedClientItemId
                }),
            });

            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }

            const reader = response.body!.getReader();
            const decoder = new TextDecoder();
            let aiResponse = '';
            
            setMessages(prev => [...prev, { text: '', sender: 'ai', sources: [] }]);
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                const eventLines = chunk.split('\n\n').filter(line => line.startsWith('data:'));

                for (const line of eventLines) {
                    const jsonStr = line.substring(6);
                    if (jsonStr.trim() === '[DONE]') continue;
                    try {
                        const parsedData = JSON.parse(jsonStr);
                        if (parsedData.content) {
                            aiResponse += parsedData.content;
                        }
                        
                        setMessages(prev => {
                            const newMessages = [...prev];
                            const lastMessage = newMessages[newMessages.length - 1];
                            if (lastMessage?.sender === 'ai') {
                                lastMessage.text = aiResponse;
                                if (parsedData.sources) {
                                    lastMessage.sources = parsedData.sources;
                                }
                            }
                            return newMessages;
                        });
                    } catch (e) {
                        console.error('Error parsing stream JSON:', e, 'Received:', jsonStr);
                    }
                }
            }
        } catch (error) {
            console.error('Error fetching stream:', error);
            setMessages(prev => [...prev, { text: 'Sorry, I ran into an issue.', sender: 'ai' }]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <MainLayout onNewChat={handleNewChat}>
            <Flex direction="column" style={{ height: '100vh', backgroundColor: 'var(--gray-1)' }}>
                <Box style={{ padding: '1.5rem 2rem', borderBottom: '1px solid var(--gray-4)', backgroundColor: 'white' }}>
                    <Flex align="center" justify="between">
                        <div>
                            <Heading size="7" style={{ color: 'var(--gray-12)' }}>AI Chat</Heading>
                            <Text as="p" size="3" style={{ color: 'var(--gray-10)', marginTop: '0.25rem' }}>
                                Ask questions and get answers from your internal knowledge base, powered by AI.
                            </Text>
                        </div>
                        <div>
                            <ClientSelector value={selectedClientItemId} onChange={setSelectedClientItemId} />
                        </div>
                    </Flex>
                </Box>

                <ScrollArea style={{ flex: 1, padding: '1rem', width: '100%' }}>
                    <Box style={{ maxWidth: '1000px', margin: '0' }}>
                        {messages.map((msg, index) => (
                            <div key={index} className="message-container">
                                <div className={`message-bubble ${msg.sender}`}>
                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                        {msg.text}
                                    </ReactMarkdown>
                                </div>
                                {msg.sender === 'ai' && msg.sources && msg.sources.length > 0 && (
                                    <div className="citations">
                                        <span className="citation-title">Sources:</span>
                                        {msg.sources.map((source, i) => {
                                            const sourceText = typeof source === 'string' ? source : source.source;
                                            return <span key={i} className="citation-source">{sourceText}</span>
                                        })}
                                    </div>
                                )}
                            </div>
                        ))}
                        {isLoading && messages[messages.length - 1]?.sender === 'user' && (
                             <div className="message-bubble ai">
                                <div className="thinking-indicator">
                                    <span></span>
                                    <span></span>
                                    <span></span>
                                </div>
                             </div>
                        )}
                    </Box>
                </ScrollArea>
                
                <Box style={{ 
                    padding: '1.5rem 1rem', 
                    borderTop: '1px solid var(--gray-4)', 
                    backgroundColor: 'white'
                }}>
                    <CommandCenter 
                        onSend={handleSendMessage} 
                        isLoading={isLoading}
                        leftSlot={<ClientSelector value={selectedClientItemId} onChange={setSelectedClientItemId} />}
                    />
                </Box>
                <style>{STYLES}</style>
            </Flex>
        </MainLayout>
    );
};

const STYLES = `
    .message-container {
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .message-bubble {
        max-width: 85%;
        padding: 0.8rem 1.2rem;
        border-radius: 18px;
        word-wrap: break-word;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid var(--gray-4);
    }
    .message-bubble.user {
        background-color: var(--gray-2); /* Light light grey */
        color: var(--gray-12);
        margin-left: auto;
        border-bottom-right-radius: 4px;
        align-self: flex-end;
    }
    .message-bubble.ai {
        background-color: white; /* White */
        color: var(--gray-12);
        margin-right: auto;
        border-bottom-left-radius: 4px;
        align-self: flex-start;
    }
    .message-bubble.ai table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
        overflow: hidden;
        border-radius: 8px;
        border: 1px solid var(--gray-5);
    }
    .message-bubble.ai th, .message-bubble.ai td {
        padding: 0.8rem;
        text-align: left;
        border-bottom: 1px solid var(--gray-5);
    }
    .message-bubble.ai th {
        background-color: var(--gray-2);
        font-weight: 600;
    }
    .message-bubble.ai tr:last-child td {
        border-bottom: none;
    }
    .citations {
        margin-top: 0.5rem;
        margin-left: 0;
        max-width: 85%;
        font-size: 0.75rem;
        color: var(--gray-10);
        align-self: flex-start;
    }
    .citation-title {
        font-weight: 600;
        margin-right: 0.5rem;
        margin-top: 0.25rem;
        font-family: monospace;
    }
    .citation-source {
        display: inline-block;
        background-color: var(--gray-3);
        padding: 0.1rem 0.5rem;
        border-radius: 99px;
        margin-right: 0.5rem;
        margin-top: 0.25rem;
        font-family: monospace;
    }
    .thinking-indicator {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0.8rem 1.2rem;
    }
    .thinking-indicator span {
        height: 8px;
        width: 8px;
        background-color: var(--gray-8);
        border-radius: 50%;
        display: inline-block;
        margin: 0 2px;
        animation: thinking 1.4s infinite ease-in-out both;
    }
    .thinking-indicator span:nth-child(1) {
        animation-delay: -0.32s;
    }
    .thinking-indicator span:nth-child(2) {
        animation-delay: -0.16s;
    }
    @keyframes thinking {
        0%, 80%, 100% {
            transform: scale(0);
        }
        40% {
            transform: scale(1.0);
        }
    }
    /* Tighter Markdown Formatting */
    .message-bubble.ai p {
        margin-block-start: 0;
        margin-block-end: 0.5em;
    }
    .message-bubble.ai p:last-child {
        margin-block-end: 0;
    }
    .message-bubble.ai ul, .message-bubble.ai ol {
        margin-block-start: 0.5em;
        margin-block-end: 0.5em;
        padding-inline-start: 2em;
    }
    .message-bubble.ai li {
        margin-bottom: 0.25em;
    }
    .message-bubble.ai li p {
        margin-block-start: 0;
        margin-block-end: 0;
    }
`;

export default HomePage; 
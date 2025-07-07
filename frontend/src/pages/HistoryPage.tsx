import { Box, Flex, Text, Card, Heading, Spinner, IconButton } from '@radix-ui/themes';
import { useQuery } from '@tanstack/react-query';
import api from '../api';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { PersonIcon } from '@radix-ui/react-icons';
import { MainLayout } from '../components/MainLayout';

interface Conversation {
  id: string;
  title: string;
  created_at: string;
}

const HistoryPage = () => {
    const { data: conversations, isLoading, error } = useQuery<Conversation[]>({
        queryKey: ['chatHistory'],
        queryFn: () => api.get('/history').then(res => res.data),
    });
    const { logout } = useAuth();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const handleConversationClick = (id: string) => {
        // This will be used to navigate to the detailed view of a chat.
        // For now, we'll just log it.
        console.log(`Navigate to chat with ID: ${id}`);
        // In the future, this will be something like: navigate(`/history/${id}`);
    };

    return (
        <MainLayout onNewChat={() => navigate('/home')}>
            <Flex direction="column" style={{ height: '100vh', backgroundColor: 'var(--gray-1)' }}>
                 <Box style={{ padding: '1.5rem 2rem', borderBottom: '1px solid var(--gray-4)', backgroundColor: 'white' }}>
                    <Heading size="7" style={{ color: 'var(--gray-12)' }}>Chat History</Heading>
                    <Text as="p" size="3" style={{ color: 'var(--gray-10)', marginTop: '0.25rem' }}>
                        Review and search past conversations.
                    </Text>
                </Box>

                <Box style={{ flex: 1, padding: '2rem', overflowY: 'auto' }}>
                    {isLoading && (
                        <Flex justify="center" align="center" style={{ height: '100%' }}>
                            <Spinner size="3" />
                        </Flex>
                    )}
                    {error && <Text color="red">Failed to load chat history. Please try again later.</Text>}
                    {conversations && (
                        <Flex direction="column" gap="3">
                            {conversations.length === 0 ? (
                                <Text>No saved conversations found.</Text>
                            ) : (
                                conversations.map(convo => (
                                    <Card 
                                        key={convo.id} 
                                        onClick={() => handleConversationClick(convo.id)}
                                        style={{ cursor: 'pointer', transition: 'box-shadow 0.2s' }}
                                        className="history-card"
                                    >
                                        <Flex direction="column" gap="1">
                                            <Text weight="bold">{convo.title}</Text>
                                            <Text size="1" color="gray">
                                                {new Date(convo.created_at).toLocaleString()}
                                            </Text>
                                        </Flex>
                                    </Card>
                                ))
                            )}
                        </Flex>
                    )}
                </Box>
                <style>{`
                    .history-card:hover {
                        box-shadow: var(--shadow-3);
                    }
                `}</style>
            </Flex>
        </MainLayout>
    );
};

export default HistoryPage; 
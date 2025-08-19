import { Box, Flex, Text, Heading, Card, Grid } from '@radix-ui/themes';
import { Rocket } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { MainLayout } from '../components/MainLayout';
import { useAuth } from '../context/AuthContext';

const LandingPage = () => {
    const navigate = useNavigate();
    const { userProfile } = useAuth();

    const modules = [
        {
            icon: "/new-icons/13.png",
            title: "AI Chat",
            description: "Engage in intelligent conversations and get instant answers from your knowledge base.",
            path: "/home",
            permission: "chat"
        },
        {
            icon: "/new-icons/4.png",
            title: "Knowledge Base",
            description: "Manage and consult your internal documents and web content with ease.",
            path: "/knowledge",
            permission: "knowledge"
        },
        {
            icon: "/new-icons/3.png",
            title: "Automation Agents",
            description: "Use AI-powered agents to automate workflows and generate content at scale.",
            path: "/agents",
            permission: "agents"
        },
        {
            icon: "/new-icons/2.png",
            title: "Chat History",
            description: "Review and continue your past conversations with the AI assistant.",
            path: "/history",
            permission: "history"
        },
        {
            icon: "/new-icons/14.png",
            title: "Data Lake",
            description: "View, filter, and manage your data records in one centralized location.",
            path: "/data-lake",
            permission: "data-lake"
        },
        {
            icon: "/new-icons/15.png",
            title: "Customer Service",
            description: "Search and manage customer service communications and answers.",
            path: "/customer-service",
            permission: "customer-service"
        },
        {
            // Use the new Rocket icon for ADTV Traffic Basic (Facebook Automation)
            iconNode: <Rocket style={{ color: 'var(--gray-11)', width: '40px', height: '40px' }} />,
            title: "Facebook Automation",
            description: "Convert organic posts into high-performing ads automatically.",
            path: "/facebook-automation",
            permission: "facebook-automation"
        }
    ];

    // Filter modules based on user permissions
    const availableModules = modules.filter(module => 
        userProfile?.permissions?.[module.permission] === true
    );

    return (
        <MainLayout onNewChat={() => navigate('/home')}>
            <Flex direction="column" align="center" justify="center" style={{ minHeight: '100vh', backgroundColor: 'var(--gray-1)', padding: '2rem' }}>
                <Box style={{ textAlign: 'center', marginBottom: '4rem' }}>
                    <img src="/new-icons/adtv-logo.png" alt="ADTV Logo" style={{ maxWidth: '300px', marginBottom: '2rem' }} />
                    <Heading align="center" size="8" style={{ color: 'var(--gray-12)', marginBottom: '1rem' }}>
                        Unlock Your Data's Potential
                    </Heading>
                    <Text as="p" size="4" style={{ color: 'var(--gray-11)', maxWidth: '600px', margin: '0 auto' }}>
                        Welcome to the ADTV AI Platform. Seamlessly integrate your knowledge base, generate personalized content, and engage in intelligent conversations to drive your business forward.
                    </Text>
                </Box>

                <Grid columns={{ initial: '1', sm: '2', md: availableModules.length >= 4 ? '4' : '3' }} gap="4" width="100%" maxWidth="1200px">
                    {availableModules.map(module => (
                        <Card 
                            key={module.title} 
                            className="module-card" 
                            onClick={() => navigate(module.path)}
                            style={{
                                cursor: 'pointer',
                                transition: 'all 0.2s',
                                border: '1px solid var(--gray-4)'
                            }}
                        >
                            <Flex direction="column" align="center" gap="3">
                                {module.iconNode ? (
                                    module.iconNode
                                ) : (
                                    <img src={module.icon} alt={`${module.title} icon`} style={{ width: '40px', height: '40px' }} />
                                )}
                                <Heading size="4" style={{ width: '100%', textAlign: 'center' }}>{module.title}</Heading>
                                <Text as="p" size="2" color="gray" style={{ textAlign: 'center' }}>{module.description}</Text>
                            </Flex>
                        </Card>
                    ))}
                </Grid>

                <style>{`
                    .module-card:hover {
                        transform: translateY(-2px);
                        box-shadow: var(--shadow-3);
                        border-color: var(--primary);
                    }
                `}</style>
            </Flex>
        </MainLayout>
    );
};

export default LandingPage; 
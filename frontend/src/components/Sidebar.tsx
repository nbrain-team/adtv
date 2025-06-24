import { Flex } from '@radix-ui/themes';
import { useNavigate } from 'react-router-dom';

export const Sidebar = ({ onNewChat }: { onNewChat: () => void }) => {
    const navigate = useNavigate();

    const handleNewChatClick = () => {
        navigate('/');
        onNewChat();
    };

    return (
        <Flex 
            direction="column" 
            align="center" 
            gap="4"
            style={{ 
                width: 'var(--sidebar-width)', 
                height: '100vh', 
                padding: '1.5rem 0',
                backgroundColor: 'var(--sidebar-bg)',
                borderRight: '1px solid var(--border)',
                boxShadow: 'var(--shadow)',
                position: 'fixed',
                left: 0,
                top: 0,
                zIndex: 100
            }}
        >
            <button className="sidebar-icon" title="Home" onClick={() => navigate('/home')} style={{ background: 'none', border: 'none', padding: 0, cursor: 'pointer' }}>
                <img src="/new-icons/1.png" alt="ADTV Logo" style={{ width: '60px', height: '60px', marginBottom: '1rem' }} />
            </button>
            
            <Flex direction="column" align="center" gap="8" style={{ marginTop: '125px' }}>
                <button className="sidebar-icon" title="New Chat" onClick={handleNewChatClick}>
                    <img src="/new-icons/13.png" alt="New Chat" />
                </button>
                <button className="sidebar-icon" title="Chat History" onClick={() => navigate('/history')}>
                    <img src="/new-icons/2.png" alt="History" />
                </button>
                <button className="sidebar-icon" title="Knowledge Base" onClick={() => navigate('/knowledge')}>
                    <img src="/new-icons/4.png" alt="Upload" />
                </button>
                <button className="sidebar-icon" title="1-2-1 Email Personalizer" onClick={() => navigate('/agents')}>
                    <img src="/new-icons/7.png" alt="1-2-1 Email Personalizer" />
                </button>
                <button className="sidebar-icon" title="Automation Agents" onClick={() => navigate('/agents')}>
                    <img src="/new-icons/3.png" alt="Automation Agents" />
                </button>
            </Flex>
        </Flex>
    );
}; 
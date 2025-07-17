import { Flex } from '@radix-ui/themes';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export const Sidebar = ({ onNewChat }: { onNewChat: () => void }) => {
    const navigate = useNavigate();
    const { userProfile } = useAuth();

    const handleNewChatClick = () => {
        navigate('/home');
        onNewChat();
    };

    const hasPermission = (module: string) => {
        // Admins always have access to campaigns
        if (module === 'campaigns' && userProfile?.role === 'admin') {
            return true;
        }
        
        const hasIt = userProfile?.permissions?.[module] === true;
        console.log(`Permission check for ${module}:`, hasIt, userProfile?.permissions);
        return hasIt;
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
            
            <Flex direction="column" align="center" gap="8" style={{ marginTop: '125px', flex: 1 }}>
                {hasPermission('chat') && (
                    <button className="sidebar-icon" title="New Chat" onClick={handleNewChatClick}>
                        <img src="/new-icons/13.png" alt="New Chat" />
                    </button>
                )}
                {hasPermission('history') && (
                    <button className="sidebar-icon" title="Chat History" onClick={() => navigate('/history')}>
                        <img src="/new-icons/2.png" alt="History" />
                    </button>
                )}
                {hasPermission('knowledge') && (
                    <button className="sidebar-icon" title="Knowledge Base" onClick={() => navigate('/knowledge')}>
                        <img src="/new-icons/4.png" alt="Upload" />
                    </button>
                )}
                {hasPermission('agents') && (
                    <button className="sidebar-icon" title="Automation Agents" onClick={() => navigate('/agents')}>
                        <img src="/new-icons/3.png" alt="Automation Agents" />
                    </button>
                )}
                {hasPermission('data-lake') && (
                    <button className="sidebar-icon" title="Data Lake" onClick={() => navigate('/data-lake')}>
                        <img src="/new-icons/data-lake.png" alt="Data Lake" />
                    </button>
                )}
                {hasPermission('realtor') && (
                    <button className="sidebar-icon" title="Realtor" onClick={() => navigate('/realtor')}>
                        <img src="/new-icons/15.png" alt="Realtor" />
                    </button>
                )}
                {userProfile?.role === 'admin' && (
                    <button className="sidebar-icon" title="Email Templates" onClick={() => navigate('/template-manager')}>
                        <img src="/new-icons/9.png" alt="Email Templates" />
                    </button>
                )}
            </Flex>
            
            <button className="sidebar-icon" title="Profile" onClick={() => navigate('/profile')} style={{ marginBottom: '1rem' }}>
                <img src="/new-icons/16.png" alt="Profile" />
            </button>
        </Flex>
    );
}; 
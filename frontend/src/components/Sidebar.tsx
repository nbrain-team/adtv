import React from 'react';
import { Flex } from '@radix-ui/themes';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export const Sidebar = ({ onNewChat }: { onNewChat: () => void }) => {
    const navigate = useNavigate();
    const location = useLocation();
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

    const handleNavigation = (path: string) => {
        // Force navigation even if we're on a nested route
        if (location.pathname !== path) {
            navigate(path);
        }
    };

    return (
        <Flex 
            direction="column" 
            align="center"
            style={{ 
                position: 'fixed',
                left: 0,
                top: 0,
                width: 'var(--sidebar-width)', 
                height: '100vh', 
                background: 'linear-gradient(180deg, #191970 0%, #000033 100%)', 
                padding: '40px 0',
                zIndex: 1000
            }}
        >
            <button onClick={() => handleNavigation('/landing')} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, marginBottom: '10px' }}>
                <img src="/new-icons/adtv-logo.png" alt="ADTV Logo" style={{ width: '80px', height: 'auto' }} />
            </button>
            
            <Flex direction="column" align="center" gap="8" style={{ marginTop: '125px', flex: 1 }}>
                {hasPermission('chat') && (
                    <button className="sidebar-icon" title="New Chat" onClick={handleNewChatClick}>
                        <img src="/new-icons/13.png" alt="New Chat" />
                    </button>
                )}
                {hasPermission('history') && (
                    <button className="sidebar-icon" title="Chat History" onClick={() => handleNavigation('/history')}>
                        <img src="/new-icons/2.png" alt="History" />
                    </button>
                )}
                {hasPermission('knowledge') && (
                    <button className="sidebar-icon" title="Knowledge Base" onClick={() => handleNavigation('/knowledge')}>
                        <img src="/new-icons/4.png" alt="Upload" />
                    </button>
                )}
                {hasPermission('agents') && (
                    <button className="sidebar-icon" title="Automation Agents" onClick={() => handleNavigation('/agents')}>
                        <img src="/new-icons/3.png" alt="Automation Agents" />
                    </button>
                )}
                {userProfile?.permissions?.['data-lake'] && (
                    <button className="sidebar-icon" title="Data Lake" onClick={() => handleNavigation('/data-lake')}>
                        <img src="/new-icons/14.png" alt="Data Lake" />
                    </button>
                )}
                {userProfile?.permissions?.['ad-traffic'] && (
                    <button className="sidebar-icon" title="ADTV Traffic" onClick={() => handleNavigation('/ad-traffic')}>
                        <img src="/new-icons/5.png" alt="Ad Traffic" />
                    </button>
                )}
                {hasPermission('campaigns') && (
                    <button className="sidebar-icon" title="Event Campaigns" onClick={() => handleNavigation('/campaigns')}>
                        <img src="/new-icons/6.png" alt="Campaigns" />
                    </button>
                )}
            </Flex>
            
            <Flex
                direction="column" 
                align="center"
                gap="3"
                style={{ marginTop: 'auto' }}
            >
                <button className="sidebar-icon" title="User Profile" onClick={() => handleNavigation('/profile')}>
                    <img src="/new-icons/user.png" alt="User Profile" />
                </button>
            </Flex>
        </Flex>
    );
}; 
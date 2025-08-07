import React from 'react';
import { AdTrafficDashboard } from '../components/AdTraffic';
import { MainLayout } from '../components/MainLayout';
import { useNavigate } from 'react-router-dom';

const AdTrafficPage: React.FC = () => {
  const navigate = useNavigate();
  
  return (
    <MainLayout onNewChat={() => navigate('/home')}>
      <AdTrafficDashboard />
    </MainLayout>
  );
};

export default AdTrafficPage; 
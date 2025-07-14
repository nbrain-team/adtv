import React from 'react';
import { MainLayout } from '../components/MainLayout';
import { CampaignDetail } from '../components/CampaignDetail';

const CampaignDetailPage = () => {
  return (
    <MainLayout onNewChat={() => {}}>
      <CampaignDetail />
    </MainLayout>
  );
};

export default CampaignDetailPage; 
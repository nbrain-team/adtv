import React, { useState, useEffect } from 'react';
import { 
  Box, Flex, Heading, Text, Button, Tabs, ScrollArea, 
  Badge, Spinner, Dialog, AlertDialog, Card, IconButton 
} from '@radix-ui/themes';
import { 
  ArrowLeftIcon, VideoIcon, PlayIcon, DownloadIcon, 
  CalendarIcon, EyeOpenIcon, Cross2Icon, PlusIcon, TrashIcon 
} from '@radix-ui/react-icons';
import { Client, Campaign, VideoClip, SocialPost } from './types';
import { CalendarView } from './CalendarView';
import { PostModal } from './PostModal';
import { CampaignModal } from './CampaignModal';
import VideoEditor from './VideoEditor';
import { Edit3 } from 'lucide-react';
import { api } from '../../services/api';

interface ClientDetailViewProps {
  client: Client;
  onBack: () => void;
  onClientUpdate?: () => void;
}

interface CampaignWithClips extends Campaign {
  video_clips?: VideoClip[];
  video_urls?: string[];
}

interface ClientProfile {
  client: Client;
  campaigns: CampaignWithClips[];
  campaign_videos: Record<string, {
    campaign_name: string;
    videos: string[];
    clips: VideoClip[];
    total_clips: number;
  }>;
  metrics: {
    total_campaigns: number;
    total_videos: number;
    total_clips: number;
    total_posts: number;
    published_posts: number;
  };
}

export const ClientDetailView: React.FC<ClientDetailViewProps> = ({ client, onBack, onClientUpdate }) => {
  const [profile, setProfile] = useState<ClientProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedVideo, setSelectedVideo] = useState<string | null>(null);
  const [selectedClip, setSelectedClip] = useState<VideoClip | null>(null);
  const [posts, setPosts] = useState<SocialPost[]>([]);
  const [showPostModal, setShowPostModal] = useState(false);
  const [showCampaignModal, setShowCampaignModal] = useState(false);
  const [editingPost, setEditingPost] = useState<SocialPost | null>(null);
  const [showVideoEditor, setShowVideoEditor] = useState(false);
  const [editingVideoUrl, setEditingVideoUrl] = useState('');
  const [editingVideoPublicId, setEditingVideoPublicId] = useState('');

  useEffect(() => {
    fetchClientProfile();
    fetchClientPosts();
  }, [client.id]);

  const fetchClientProfile = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/api/ad-traffic/clients/${client.id}/profile`);
      setProfile(response.data);
    } catch (error) {
      console.error('Error fetching client profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchClientPosts = async () => {
    try {
      const response = await api.get(`/api/ad-traffic/clients/${client.id}/calendar`);
      setPosts(response.data);
    } catch (error) {
      console.error('Error fetching posts:', error);
    }
  };

  const handleCreatePost = () => {
    setEditingPost(null);
    setShowPostModal(true);
  };

  const handleEditPost = (post: SocialPost) => {
    setEditingPost(post);
    setShowPostModal(true);
  };

  const handlePostSaved = async () => {
    await fetchClientPosts();
    setShowPostModal(false);
    setEditingPost(null);
  };

  const handleDeletePost = async (postId: string) => {
    try {
      await api.delete(`/api/ad-traffic/posts/${postId}`);
      await fetchClientPosts();
    } catch (error) {
      console.error('Error deleting post:', error);
    }
  };

  const handleApprovePost = async (postId: string, approved: boolean) => {
    try {
      await api.post(`/api/ad-traffic/posts/${postId}/approve`, { approved });
      await fetchClientPosts();
    } catch (error) {
      console.error('Error approving post:', error);
    }
  };

  const handleCreateCampaign = () => {
    setShowCampaignModal(true);
  };

  const handleCampaignCreated = async (campaign: Campaign) => {
    setShowCampaignModal(false);
    await fetchClientProfile();
    if (onClientUpdate) {
      onClientUpdate();
    }
  };

  const handleDeleteCampaign = async (campaignId: string) => {
    if (window.confirm('Are you sure you want to delete this campaign and all its assets?')) {
      try {
        await api.delete(`/api/ad-traffic/campaigns/${campaignId}`);
        await fetchClientProfile();
        if (onClientUpdate) {
          onClientUpdate();
        }
      } catch (error) {
        console.error('Error deleting campaign:', error);
        alert('Failed to delete campaign');
      }
    }
  };

  const handleEditVideo = (videoUrl: string) => {
    setEditingVideoUrl(videoUrl);
    
    // Extract public ID from Cloudinary URL
    if (videoUrl && videoUrl.includes('cloudinary.com')) {
      const urlParts = videoUrl.split('/');
      if (urlParts.includes('upload')) {
        const uploadIdx = urlParts.indexOf('upload');
        if (uploadIdx + 2 < urlParts.length) {
          const publicId = urlParts.slice(uploadIdx + 2).join('/').replace('.mp4', '');
          setEditingVideoPublicId(publicId);
          setShowVideoEditor(true);
        }
      }
    }
  };

  const handleSaveEditedVideo = (editedUrl: string, transformations: any) => {
    // For now, just close the editor
    // In production, you'd save this to the database
    console.log('Edited video URL:', editedUrl);
    console.log('Transformations:', transformations);
    setShowVideoEditor(false);
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'processing': return 'blue';
      case 'ready': return 'green';
      case 'failed': return 'red';
      default: return 'gray';
    }
  };

  if (loading) {
    return (
      <Box style={{ padding: '2rem' }}>
        <Flex align="center" justify="center" style={{ minHeight: '400px' }}>
          <Spinner size="3" />
        </Flex>
      </Box>
    );
  }

  if (!profile) {
    return (
      <Box style={{ padding: '2rem' }}>
        <Text>Failed to load client details</Text>
      </Box>
    );
  }

  return (
    <Box style={{ padding: '2rem' }}>
      {/* Header */}
      <Flex align="center" gap="3" mb="4">
        <IconButton variant="ghost" onClick={onBack}>
          <ArrowLeftIcon />
        </IconButton>
        <Box>
          <Heading size="6">{client.name}</Heading>
          {client.company_name && (
            <Text size="2" color="gray">{client.company_name}</Text>
          )}
        </Box>
        <Flex gap="3" ml="auto">
          <Button onClick={handleCreatePost}>
            <PlusIcon />
            New Post
          </Button>
          <Button onClick={handleCreateCampaign} variant="soft">
            <VideoIcon />
            New Campaign
          </Button>
        </Flex>
      </Flex>

      {/* Summary Stats */}
      <Flex gap="3" mb="6">
        <Card>
          <Flex direction="column" align="center">
            <Text size="6" weight="bold">{profile.metrics.total_campaigns || profile.campaigns.length}</Text>
            <Text size="2" color="gray">Campaigns</Text>
          </Flex>
        </Card>
        <Card>
          <Flex direction="column" align="center">
            <Text size="6" weight="bold">{profile.metrics.total_videos || profile.campaigns.reduce((sum, c) => sum + (profile.campaign_videos[c.id]?.videos?.length || 0), 0)}</Text>
            <Text size="2" color="gray">Videos Uploaded</Text>
          </Flex>
        </Card>
        <Card>
          <Flex direction="column" align="center">
            <Text size="6" weight="bold">{profile.metrics.total_clips || profile.campaigns.reduce((sum, c) => sum + (profile.campaign_videos[c.id]?.clips?.length || 0), 0)}</Text>
            <Text size="2" color="gray">Clips Generated</Text>
          </Flex>
        </Card>
        <Card>
          <Flex direction="column" align="center">
            <Text size="6" weight="bold">{profile.metrics.published_posts || 0}</Text>
            <Text size="2" color="gray">Published Posts</Text>
          </Flex>
        </Card>
      </Flex>

      {/* Campaigns and Assets */}
      <Tabs.Root defaultValue="timeline">
        <Tabs.List>
          <Tabs.Trigger value="timeline">
            <CalendarIcon style={{ marginRight: '8px' }} />
            Timeline
          </Tabs.Trigger>
          <Tabs.Trigger value="campaigns">
            <VideoIcon style={{ marginRight: '8px' }} />
            Campaigns & Assets
          </Tabs.Trigger>
        </Tabs.List>

        <Box mt="4">
          <Tabs.Content value="timeline">
            <Flex direction="column" gap="4">
              {/* Calendar View */}
              <Box style={{ height: '400px' }}>
                <CalendarView
                  client={client}
                  posts={posts}
                  onCreatePost={handleCreatePost}
                  onEditPost={handleEditPost}
                  onDeletePost={handleDeletePost}
                  onApprovePost={handleApprovePost}
                  onCreateCampaign={handleCreateCampaign}
                />
              </Box>
              
              {/* Campaigns List */}
              <Box>
                <Flex align="center" justify="between" mb="3">
                  <Heading size="4">Campaigns</Heading>
                  <Button onClick={() => setShowCampaignModal(true)} size="2">
                    <PlusIcon />
                    New Campaign
                  </Button>
                </Flex>
                
                <ScrollArea style={{ height: '300px' }}>
                  <Flex direction="column" gap="3">
                    {profile.campaigns.length === 0 ? (
                      <Card>
                        <Text size="2" color="gray" align="center">
                          No campaigns yet. Create your first campaign to get started.
                        </Text>
                      </Card>
                    ) : (
                      profile.campaigns.map(campaign => {
                        const campaignVideos = profile.campaign_videos[campaign.id];
                        const clipCount = campaignVideos?.total_clips || 0;
                        const videoCount = campaignVideos?.videos?.length || 0;
                        
                        return (
                          <Card key={campaign.id} style={{ cursor: 'pointer' }}>
                            <Flex justify="between" align="center">
                              <Box onClick={() => {
                                // Navigate to campaigns tab with this campaign expanded
                                // You could add state to track which campaign to expand
                                const tabsList = document.querySelector('[role="tablist"]');
                                const campaignsTab = tabsList?.querySelector('[value="campaigns"]');
                                if (campaignsTab instanceof HTMLElement) {
                                  campaignsTab.click();
                                }
                              }}>
                                <Heading size="3">{campaign.name}</Heading>
                                <Flex gap="3" mt="1">
                                  <Badge color={getStatusColor(campaign.status)}>
                                    {campaign.status}
                                  </Badge>
                                  <Text size="2" color="gray">
                                    {videoCount} videos • {clipCount} clips
                                  </Text>
                                  <Text size="2" color="gray">
                                    Created {new Date(campaign.created_at).toLocaleDateString()}
                                  </Text>
                                </Flex>
                              </Box>
                              
                              <Flex gap="2">
                                <IconButton
                                  size="2"
                                  variant="ghost"
                                  color="red"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleDeleteCampaign(campaign.id);
                                  }}
                                >
                                  <TrashIcon />
                                </IconButton>
                              </Flex>
                            </Flex>
                          </Card>
                        );
                      })
                    )}
                  </Flex>
                </ScrollArea>
              </Box>
            </Flex>
          </Tabs.Content>

          <Tabs.Content value="campaigns">
            <ScrollArea style={{ height: '600px' }}>
              <Flex direction="column" gap="4">
                {profile.campaigns.map(campaign => {
                  const campaignVideos = profile.campaign_videos[campaign.id];
                  
                  return (
                    <Card key={campaign.id} size="3">
                      <Flex direction="column" gap="3">
                        {/* Campaign Header */}
                        <Flex justify="between" align="start">
                          <Box>
                            <Heading size="4">{campaign.name}</Heading>
                            <Flex gap="2" mt="1">
                              <Badge color={getStatusColor(campaign.status)}>
                                {campaign.status}
                              </Badge>
                              <Text size="2" color="gray">
                                <CalendarIcon style={{ display: 'inline', marginRight: '4px' }} />
                                {new Date(campaign.created_at).toLocaleDateString()}
                              </Text>
                              <Text size="2" color="gray">
                                {campaign.duration_weeks} weeks
                              </Text>
                            </Flex>
                          </Box>
                          <Flex gap="2" align="center">
                            {campaign.platforms.map(platform => (
                              <Badge key={platform} variant="soft">
                                {platform}
                              </Badge>
                            ))}
                            <IconButton
                              size="2"
                              color="red"
                              variant="ghost"
                              onClick={() => handleDeleteCampaign(campaign.id)}
                              title="Delete Campaign"
                            >
                              <TrashIcon />
                            </IconButton>
                          </Flex>
                        </Flex>

                        {/* Original Videos */}
                        {campaignVideos && campaignVideos.videos.length > 0 && (
                          <Box>
                            <Text size="2" weight="bold" mb="2">
                              Original Videos ({campaignVideos.videos.length})
                            </Text>
                            <Flex gap="3" wrap="wrap">
                              {campaignVideos.videos.map((videoUrl, index) => (
                                <Card key={index} style={{ width: '200px' }}>
                                  <Box 
                                    style={{ 
                                      position: 'relative',
                                      paddingBottom: '56.25%',
                                      backgroundColor: 'var(--gray-3)',
                                      borderRadius: '4px',
                                      overflow: 'hidden',
                                      cursor: 'pointer'
                                    }}
                                    onClick={() => setSelectedVideo(videoUrl)}
                                  >
                                    <Flex
                                      align="center"
                                      justify="center"
                                      style={{
                                        position: 'absolute',
                                        inset: 0
                                      }}
                                    >
                                      <VideoIcon width="40" height="40" />
                                    </Flex>
                                    <IconButton
                                      size="3"
                                      variant="solid"
                                      style={{
                                        position: 'absolute',
                                        top: '50%',
                                        left: '50%',
                                        transform: 'translate(-50%, -50%)'
                                      }}
                                    >
                                      <PlayIcon />
                                    </IconButton>
                                  </Box>
                                  <Text size="1" mt="2">
                                    Original Video {index + 1}
                                  </Text>
                                </Card>
                              ))}
                            </Flex>
                          </Box>
                        )}

                        {/* Generated Clips */}
                        {campaignVideos && campaignVideos.clips.length > 0 && (
                          <Box>
                            <Text size="2" weight="bold" mb="2">
                              Generated Clips ({campaignVideos.clips.length})
                            </Text>
                            <Box 
                              style={{ 
                                display: 'grid',
                                gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
                                gap: '1rem'
                              }}
                            >
                              {campaignVideos.clips.map(clip => (
                                <Card 
                                  key={clip.id}
                                  style={{ cursor: 'pointer' }}
                                >
                                  <Box 
                                    style={{ 
                                      position: 'relative',
                                      paddingBottom: '56.25%',
                                      backgroundColor: 'var(--gray-3)',
                                      borderRadius: '4px',
                                      overflow: 'hidden'
                                    }}
                                    onClick={() => setSelectedClip(clip)}
                                  >
                                    {clip.thumbnail_url ? (
                                      <img 
                                        src={clip.thumbnail_url} 
                                        alt={clip.title}
                                        style={{
                                          position: 'absolute',
                                          width: '100%',
                                          height: '100%',
                                          objectFit: 'cover'
                                        }}
                                      />
                                    ) : (
                                      <Flex
                                        align="center"
                                        justify="center"
                                        style={{
                                          position: 'absolute',
                                          inset: 0
                                        }}
                                      >
                                        <VideoIcon width="30" height="30" />
                                      </Flex>
                                    )}
                                    <Badge 
                                      size="1"
                                      style={{
                                        position: 'absolute',
                                        bottom: '4px',
                                        right: '4px'
                                      }}
                                    >
                                      {formatDuration(clip.duration)}
                                    </Badge>
                                  </Box>
                                  <Flex justify="between" align="center" mt="2">
                                    <Text size="1" weight="medium">
                                      {clip.title}
                                    </Text>
                                    <Button
                                      size="1"
                                      variant="soft"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        handleEditVideo(clip.video_url);
                                      }}
                                    >
                                      <Edit3 size={12} />
                                      Edit
                                    </Button>
                                  </Flex>
                                  {clip.content_type && (
                                    <Badge size="1" variant="soft" mt="1">
                                      {clip.content_type}
                                    </Badge>
                                  )}
                                  {/* Show platform versions if available */}
                                  {clip.platform_versions && Object.keys(clip.platform_versions).length > 0 && (
                                    <Flex gap="1" wrap="wrap" mt="1">
                                      {Object.entries(clip.platform_versions).map(([version, details]: [string, any]) => (
                                        <Badge key={version} size="1" variant="outline">
                                          {version.replace('_', ' ')} {details.aspect_ratio}
                                        </Badge>
                                      ))}
                                    </Flex>
                                  )}
                                </Card>
                              ))}
                            </Box>
                          </Box>
                        )}

                        {/* No assets message */}
                        {(!campaignVideos || (campaignVideos.videos.length === 0 && campaignVideos.clips.length === 0)) && (
                          <Text size="2" color="gray">No videos or clips available for this campaign</Text>
                        )}
                      </Flex>
                    </Card>
                  );
                })}

                {profile.campaigns.length === 0 && (
                  <Card>
                    <Flex align="center" justify="center" style={{ padding: '3rem' }}>
                      <Text color="gray">No campaigns created yet</Text>
                    </Flex>
                  </Card>
                )}
              </Flex>
            </ScrollArea>
          </Tabs.Content>
        </Box>
      </Tabs.Root>

      {/* Video Preview Dialog */}
      <Dialog.Root open={!!selectedVideo} onOpenChange={() => setSelectedVideo(null)}>
        <Dialog.Content style={{ maxWidth: '800px' }}>
          <Dialog.Title>Video Preview</Dialog.Title>
          <Box mt="3">
            <video 
              controls 
              style={{ width: '100%', maxHeight: '500px' }}
              src={selectedVideo || ''}
            />
          </Box>
          <Flex gap="3" mt="4" justify="end">
            <Dialog.Close>
              <Button variant="soft">Close</Button>
            </Dialog.Close>
            <Button>
              <DownloadIcon />
              Download
            </Button>
          </Flex>
        </Dialog.Content>
      </Dialog.Root>

      {/* Clip Preview Dialog */}
      <Dialog.Root open={!!selectedClip} onOpenChange={() => setSelectedClip(null)}>
        <Dialog.Content style={{ maxWidth: '800px' }}>
          <Dialog.Title>{selectedClip?.title}</Dialog.Title>
          <Box mt="3">
            {/* Platform version selector if available */}
            {selectedClip?.platform_versions && Object.keys(selectedClip.platform_versions).length > 0 && (
              <Box mb="3">
                <Text size="2" weight="medium" mb="2">Select Version:</Text>
                <Flex gap="2" wrap="wrap">
                  <Button 
                    size="2" 
                    variant={!selectedVideo ? 'solid' : 'soft'}
                    onClick={() => setSelectedVideo(null)}
                  >
                    Original
                  </Button>
                  {Object.entries(selectedClip.platform_versions).map(([version, details]: [string, any]) => (
                    <Button 
                      key={version}
                      size="2" 
                      variant={selectedVideo === details.url ? 'solid' : 'soft'}
                      onClick={() => setSelectedVideo(details.url)}
                    >
                      {version.replace('_', ' ').toUpperCase()} ({details.aspect_ratio})
                    </Button>
                  ))}
                </Flex>
              </Box>
            )}
            <video 
              controls 
              style={{ width: '100%', maxHeight: '500px' }}
              src={selectedVideo || selectedClip?.video_url || ''}
              key={selectedVideo || selectedClip?.video_url} // Force re-render on URL change
            />
          </Box>
          {selectedClip && (
            <Box mt="3">
              <Flex direction="column" gap="2">
                <Text size="2">
                  <strong>Duration:</strong> {formatDuration(selectedClip.duration)}
                </Text>
                <Text size="2">
                  <strong>Time Range:</strong> {formatDuration(selectedClip.start_time)} - {formatDuration(selectedClip.end_time)}
                </Text>
                {selectedClip.description && (
                  <Text size="2">
                    <strong>Description:</strong> {selectedClip.description}
                  </Text>
                )}
                {selectedClip.suggested_caption && (
                  <Box>
                    <Text size="2" weight="bold">Suggested Caption:</Text>
                    <Text size="2">{selectedClip.suggested_caption}</Text>
                  </Box>
                )}
                {selectedClip.suggested_hashtags.length > 0 && (
                  <Box>
                    <Text size="2" weight="bold">Suggested Hashtags:</Text>
                    <Flex gap="1" wrap="wrap" mt="1">
                      {selectedClip.suggested_hashtags.map((tag, i) => (
                        <Badge key={i} size="1" variant="soft">
                          #{tag}
                        </Badge>
                      ))}
                    </Flex>
                  </Box>
                )}
              </Flex>
            </Box>
          )}
          <Flex gap="3" mt="4" justify="end">
            <Dialog.Close>
              <Button variant="soft">Close</Button>
            </Dialog.Close>
            <Button>
              <DownloadIcon />
              Download Clip
            </Button>
          </Flex>
        </Dialog.Content>
      </Dialog.Root>

      {/* Post Modal */}
      <Dialog.Root open={showPostModal} onOpenChange={setShowPostModal}>
        <Dialog.Content style={{ maxWidth: 600 }}>
          <Dialog.Title>{editingPost ? 'Edit Post' : 'Create Post'}</Dialog.Title>
          <PostModal
            client={client}
            post={editingPost}
            onSave={handlePostSaved}
            onCancel={() => setShowPostModal(false)}
            onDelete={editingPost ? handleDeletePost : undefined}
            onApprove={editingPost ? (postId) => {
              handleApprovePost(postId, true);
              setShowPostModal(false);
            } : undefined}
          />
        </Dialog.Content>
      </Dialog.Root>

      {/* Campaign Modal */}
      <Dialog.Root open={showCampaignModal} onOpenChange={setShowCampaignModal}>
        <Dialog.Content style={{ maxWidth: 600 }}>
          <Dialog.Title>Create Campaign</Dialog.Title>
          <CampaignModal
            client={client}
            onComplete={handleCampaignCreated}
            onCancel={() => setShowCampaignModal(false)}
          />
        </Dialog.Content>
      </Dialog.Root>

      {/* Video Editor Modal */}
      {showVideoEditor && editingVideoPublicId && (
        <VideoEditor
          videoUrl={editingVideoUrl}
          publicId={editingVideoPublicId}
          cloudName={process.env.REACT_APP_CLOUDINARY_CLOUD_NAME || 'your-cloud-name'}
          onSave={handleSaveEditedVideo}
          onClose={() => setShowVideoEditor(false)}
        />
      )}
    </Box>
  );
}; 
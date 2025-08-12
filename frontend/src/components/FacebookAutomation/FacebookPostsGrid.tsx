import { useState, useEffect } from 'react';
import { Box, Flex, Text, Card, Grid, Badge, Button, Dialog } from '@radix-ui/themes';
import PostToAdConverter from './PostToAdConverter';
import api from '../../api';

interface FacebookPost {
  id: string;
  facebook_post_id: string;
  post_url: string;
  message: string;
  created_time: string;
  post_type: string;
  media_urls: string[];
  thumbnail_url: string;
  likes_count: number;
  comments_count: number;
  shares_count: number;
  reach: number;
  status: 'imported' | 'reviewed' | 'converted' | 'skipped';
  ai_quality_score: number;
  ai_suggestions: any;
}

interface FacebookPostsGridProps {
  clientId: string | null;
}

const FacebookPostsGrid: React.FC<FacebookPostsGridProps> = ({ clientId }) => {
  const [posts, setPosts] = useState<FacebookPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPost, setSelectedPost] = useState<FacebookPost | null>(null);
  const [showConverter, setShowConverter] = useState(false);

  useEffect(() => {
    if (clientId) {
      fetchPosts();
    }
  }, [clientId]);

  const fetchPosts = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/facebook-automation/posts', {
        params: { client_id: clientId, limit: 50 }
      });
      setPosts(response.data);
    } catch (error) {
      console.error('Failed to fetch posts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleReviewPost = async (postId: string, status: string) => {
    try {
      await api.put(`/facebook-automation/posts/${postId}/review`, { status });
      fetchPosts();
    } catch (error) {
      console.error('Failed to review post:', error);
    }
  };

  const handleConvertToAd = (post: FacebookPost) => {
    setSelectedPost(post);
    setShowConverter(true);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'imported': return 'blue';
      case 'reviewed': return 'orange';
      case 'converted': return 'green';
      case 'skipped': return 'gray';
      default: return 'gray';
    }
  };

  const formatEngagement = (post: FacebookPost) => {
    const total = post.likes_count + post.comments_count + post.shares_count;
    if (total > 1000) return `${(total / 1000).toFixed(1)}k`;
    return total.toString();
  };

  if (loading) {
    return (
      <Card>
        <Box p="6">
          <Text>Loading posts...</Text>
        </Box>
      </Card>
    );
  }

  if (posts.length === 0) {
    return (
      <Card>
        <Flex direction="column" align="center" p="8">
          <Text size="3" color="gray" mb="4">No posts found</Text>
          <Text size="2" color="gray">Sync your Facebook page to import posts</Text>
        </Flex>
      </Card>
    );
  }

  return (
    <>
      <Grid columns={{ initial: '1', md: '2', lg: '3' }} gap="4">
        {posts.map(post => (
          <Card key={post.id} style={{ overflow: 'hidden' }}>
            {/* Post Image */}
            {post.thumbnail_url && (
              <Box style={{ height: 200, overflow: 'hidden', position: 'relative' }}>
                <img 
                  src={post.thumbnail_url} 
                  alt="Post" 
                  style={{ 
                    width: '100%', 
                    height: '100%', 
                    objectFit: 'cover' 
                  }}
                />
                <Badge 
                  color={getStatusColor(post.status)} 
                  style={{ 
                    position: 'absolute', 
                    top: 8, 
                    right: 8 
                  }}
                >
                  {post.status}
                </Badge>
              </Box>
            )}

            {/* Post Content */}
            <Box p="4">
              <Text size="2" weight="bold" mb="2" style={{ 
                display: '-webkit-box',
                WebkitLineClamp: 3,
                WebkitBoxOrient: 'vertical',
                overflow: 'hidden'
              }}>
                {post.message || 'No text content'}
              </Text>

              {/* Metrics */}
              <Flex gap="3" mb="3">
                <Flex align="center" gap="1">
                  <Text size="1" color="gray">👍</Text>
                  <Text size="1">{post.likes_count}</Text>
                </Flex>
                <Flex align="center" gap="1">
                  <Text size="1" color="gray">💬</Text>
                  <Text size="1">{post.comments_count}</Text>
                </Flex>
                <Flex align="center" gap="1">
                  <Text size="1" color="gray">🔄</Text>
                  <Text size="1">{post.shares_count}</Text>
                </Flex>
                {post.reach > 0 && (
                  <Flex align="center" gap="1">
                    <Text size="1" color="gray">👁</Text>
                    <Text size="1">{post.reach}</Text>
                  </Flex>
                )}
              </Flex>

              {/* AI Score */}
              {post.ai_quality_score && (
                <Flex align="center" gap="2" mb="3">
                  <Text size="1" color="gray">AI Score:</Text>
                  <Box style={{ 
                    width: 100, 
                    height: 6, 
                    backgroundColor: 'var(--gray-3)', 
                    borderRadius: 3,
                    overflow: 'hidden'
                  }}>
                    <Box style={{ 
                      width: `${post.ai_quality_score}%`, 
                      height: '100%',
                      backgroundColor: post.ai_quality_score > 70 ? 'var(--green-9)' : 
                                      post.ai_quality_score > 40 ? 'var(--orange-9)' : 'var(--red-9)'
                    }} />
                  </Box>
                  <Text size="1">{post.ai_quality_score}%</Text>
                </Flex>
              )}

              {/* Actions */}
              <Flex gap="2">
                {post.status === 'imported' && (
                  <>
                    <Button 
                      size="1" 
                      variant="soft"
                      onClick={() => handleConvertToAd(post)}
                    >
                      Convert to Ad
                    </Button>
                    <Button 
                      size="1" 
                      variant="outline"
                      onClick={() => handleReviewPost(post.id, 'skipped')}
                    >
                      Skip
                    </Button>
                  </>
                )}
                {post.status === 'reviewed' && (
                  <Button 
                    size="1" 
                    onClick={() => handleConvertToAd(post)}
                  >
                    Create Ad
                  </Button>
                )}
                {post.status === 'converted' && (
                  <Button 
                    size="1" 
                    variant="outline"
                    onClick={() => window.open(post.post_url, '_blank')}
                  >
                    View Ad
                  </Button>
                )}
              </Flex>

              {/* Post Date */}
              <Text size="1" color="gray" style={{ display: 'block', marginTop: 8 }}>
                {new Date(post.created_time).toLocaleDateString()}
              </Text>
            </Box>
          </Card>
        ))}
      </Grid>

      {/* Post to Ad Converter Dialog */}
      <Dialog.Root open={showConverter} onOpenChange={setShowConverter}>
        <Dialog.Content maxWidth="800px">
          {selectedPost && (
            <PostToAdConverter 
              post={selectedPost}
              onComplete={() => {
                setShowConverter(false);
                fetchPosts();
              }}
              onCancel={() => setShowConverter(false)}
            />
          )}
        </Dialog.Content>
      </Dialog.Root>
    </>
  );
};

export default FacebookPostsGrid; 
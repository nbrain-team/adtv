import { useState, useEffect } from 'react';
import { Box, Flex, Text, Card, Badge, Button, IconButton, Dialog, Heading } from '@radix-ui/themes';
import { ChevronLeftIcon, ChevronRightIcon, PlusIcon, DotsHorizontalIcon } from '@radix-ui/react-icons';
import api from '../../api';
import PostToAdConverter from './PostToAdConverter';

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

interface DateRange {
  start: Date;
  end: Date;
}

interface FacebookVisualCalendarProps {
  clientId: string;
  dateRange: DateRange;
  onDateRangeChange: (range: DateRange) => void;
}

const FacebookVisualCalendar: React.FC<FacebookVisualCalendarProps> = ({ 
  clientId, 
  dateRange, 
  onDateRangeChange 
}) => {
  const [posts, setPosts] = useState<FacebookPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPost, setSelectedPost] = useState<FacebookPost | null>(null);
  const [showConverter, setShowConverter] = useState(false);
  const [currentWeek, setCurrentWeek] = useState(new Date());

  useEffect(() => {
    if (clientId) {
      fetchPosts();
    }
  }, [clientId, currentWeek]);

  const fetchPosts = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/facebook-automation/posts', {
        params: { client_id: clientId, limit: 100 }
      });
      setPosts(response.data);
    } catch (error) {
      console.error('Failed to fetch posts:', error);
    } finally {
      setLoading(false);
    }
  };

  const getWeekDays = () => {
    const days = [];
    const startOfWeek = new Date(currentWeek);
    startOfWeek.setDate(startOfWeek.getDate() - startOfWeek.getDay());
    
    for (let i = 0; i < 7; i++) {
      const day = new Date(startOfWeek);
      day.setDate(startOfWeek.getDate() + i);
      days.push(day);
    }
    return days;
  };

  const getPostsForDay = (date: Date) => {
    return posts.filter(post => {
      const postDate = new Date(post.created_time);
      return postDate.toDateString() === date.toDateString();
    });
  };

  const navigateWeek = (direction: number) => {
    const newWeek = new Date(currentWeek);
    newWeek.setDate(currentWeek.getDate() + (direction * 7));
    setCurrentWeek(newWeek);
  };

  const formatMonthYear = () => {
    const days = getWeekDays();
    const firstDay = days[0];
    const lastDay = days[6];
    
    if (firstDay.getMonth() === lastDay.getMonth()) {
      return firstDay.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
    } else if (firstDay.getFullYear() === lastDay.getFullYear()) {
      return `${firstDay.toLocaleDateString('en-US', { month: 'long' })} - ${lastDay.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}`;
    } else {
      return `${firstDay.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })} - ${lastDay.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}`;
    }
  };

  const PostCard = ({ post }: { post: FacebookPost }) => (
    <Card 
      style={{ 
        marginBottom: 8,
        cursor: 'pointer',
        transition: 'all 0.2s',
        border: '1px solid var(--gray-5)'
      }}
      onClick={() => {
        setSelectedPost(post);
        setShowConverter(true);
      }}
    >
      <Box p="2">
        {/* Time */}
        <Text size="1" color="gray" style={{ display: 'block', marginBottom: 4 }}>
          {new Date(post.created_time).toLocaleTimeString('en-US', { 
            hour: 'numeric', 
            minute: '2-digit',
            hour12: true 
          })}
        </Text>

        {/* Message Preview */}
        <Text size="2" weight="medium" style={{ 
          display: '-webkit-box',
          WebkitLineClamp: 2,
          WebkitBoxOrient: 'vertical',
          overflow: 'hidden',
          marginBottom: 8
        }}>
          {post.message || 'No text content'}
        </Text>

        {/* Thumbnail */}
        {post.thumbnail_url && (
          <Box style={{ 
            width: '100%', 
            height: 120, 
            borderRadius: 4,
            overflow: 'hidden',
            marginBottom: 8
          }}>
            <img 
              src={post.thumbnail_url} 
              alt=""
              style={{ 
                width: '100%', 
                height: '100%', 
                objectFit: 'cover' 
              }}
            />
          </Box>
        )}

        {/* Engagement Stats */}
        <Flex justify="between" align="center">
          <Flex gap="2">
            <Badge size="1" variant="soft" color="blue">
              <Flex align="center" gap="1">
                <Text size="1">👍 {post.likes_count}</Text>
              </Flex>
            </Badge>
            <Badge size="1" variant="soft" color="green">
              <Flex align="center" gap="1">
                <Text size="1">💬 {post.comments_count}</Text>
              </Flex>
            </Badge>
          </Flex>
          
          {/* Status */}
          <Badge 
            size="1" 
            color={
              post.status === 'converted' ? 'green' : 
              post.status === 'reviewed' ? 'orange' : 
              post.status === 'skipped' ? 'gray' : 'blue'
            }
          >
            {post.status}
          </Badge>
        </Flex>

        {/* Platform Icons */}
        <Flex gap="1" mt="2">
          <Box style={{ 
            width: 20, 
            height: 20, 
            borderRadius: '50%',
            background: '#1877f2',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Text size="1" style={{ color: 'white' }}>f</Text>
          </Box>
        </Flex>
      </Box>
    </Card>
  );

  const EmptyDayCard = () => (
    <Card style={{ 
      height: 100,
      border: '2px dashed var(--gray-5)',
      cursor: 'pointer',
      opacity: 0.5,
      transition: 'all 0.2s'
    }}>
      <Flex align="center" justify="center" style={{ height: '100%' }}>
        <PlusIcon style={{ width: 24, height: 24, color: 'var(--gray-8)' }} />
      </Flex>
    </Card>
  );

  return (
    <Box>
      {/* Calendar Header */}
      <Card mb="4">
        <Flex justify="between" align="center" p="4">
          <Flex align="center" gap="4">
            <Heading size="5">{formatMonthYear()}</Heading>
            <Text size="2" color="gray">
              Week of {getWeekDays()[0].toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
            </Text>
          </Flex>
          
          <Flex gap="2">
            <Button variant="soft" onClick={() => setCurrentWeek(new Date())}>
              Today
            </Button>
            <IconButton variant="ghost" onClick={() => navigateWeek(-1)}>
              <ChevronLeftIcon />
            </IconButton>
            <IconButton variant="ghost" onClick={() => navigateWeek(1)}>
              <ChevronRightIcon />
            </IconButton>
          </Flex>
        </Flex>
      </Card>

      {/* Calendar Grid */}
      <Box style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(7, 1fr)', 
        gap: 12 
      }}>
        {getWeekDays().map((day, index) => {
          const dayPosts = getPostsForDay(day);
          const isToday = day.toDateString() === new Date().toDateString();
          
          return (
            <Box key={index}>
              {/* Day Header */}
              <Card style={{ 
                marginBottom: 8,
                background: isToday ? 'var(--accent-3)' : 'white'
              }}>
                <Box p="3">
                  <Text size="2" weight="bold" style={{ display: 'block' }}>
                    {day.toLocaleDateString('en-US', { weekday: 'short' })}
                  </Text>
                  <Text size="5" weight={isToday ? 'bold' : 'medium'}>
                    {day.getDate()}
                  </Text>
                </Box>
              </Card>

              {/* Posts for this day */}
              <Box style={{ minHeight: 400 }}>
                {dayPosts.length > 0 ? (
                  dayPosts.map(post => (
                    <PostCard key={post.id} post={post} />
                  ))
                ) : (
                  <EmptyDayCard />
                )}
              </Box>
            </Box>
          );
        })}
      </Box>

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
    </Box>
  );
};

export default FacebookVisualCalendar; 
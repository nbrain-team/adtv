import React, { useState, useMemo } from 'react';
import { Box, Flex, Text, Button, IconButton, Badge } from '@radix-ui/themes';
import { 
  PlusIcon, 
  VideoIcon, 
  ChevronLeftIcon, 
  ChevronRightIcon,
  CalendarIcon 
} from '@radix-ui/react-icons';
import { Client, SocialPost, Platform, PostStatus } from './types';
import { PostCard } from './PostCard';

interface CalendarViewProps {
  client: Client;
  posts: SocialPost[];
  onCreatePost: () => void;
  onEditPost: (post: SocialPost) => void;
  onDeletePost: (postId: string) => void;
  onCreateCampaign: () => void;
}

export const CalendarView: React.FC<CalendarViewProps> = ({
  client,
  posts,
  onCreatePost,
  onEditPost,
  onDeletePost,
  onCreateCampaign
}) => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [viewMode, setViewMode] = useState<'week' | 'month'>('week');

  // Calculate date range
  const dateRange = useMemo(() => {
    const start = new Date(currentDate);
    const end = new Date(currentDate);

    if (viewMode === 'week') {
      start.setDate(start.getDate() - start.getDay());
      end.setDate(start.getDate() + 6);
    } else {
      start.setDate(1);
      end.setMonth(end.getMonth() + 1);
      end.setDate(0);
    }

    return { start, end };
  }, [currentDate, viewMode]);

  // Group posts by date
  const postsByDate = useMemo(() => {
    const grouped: Record<string, SocialPost[]> = {};
    
    posts.forEach(post => {
      const date = new Date(post.scheduled_time).toDateString();
      if (!grouped[date]) {
        grouped[date] = [];
      }
      grouped[date].push(post);
    });

    return grouped;
  }, [posts]);

  // Generate calendar days
  const calendarDays = useMemo(() => {
    const days = [];
    const current = new Date(dateRange.start);
    
    while (current <= dateRange.end) {
      days.push(new Date(current));
      current.setDate(current.getDate() + 1);
    }
    
    return days;
  }, [dateRange]);

  const navigatePeriod = (direction: 'prev' | 'next') => {
    const newDate = new Date(currentDate);
    
    if (viewMode === 'week') {
      newDate.setDate(newDate.getDate() + (direction === 'next' ? 7 : -7));
    } else {
      newDate.setMonth(newDate.getMonth() + (direction === 'next' ? 1 : -1));
    }
    
    setCurrentDate(newDate);
  };

  const formatDateHeader = (date: Date) => {
    const options: Intl.DateTimeFormatOptions = { 
      weekday: 'short', 
      month: 'short', 
      day: 'numeric' 
    };
    return date.toLocaleDateString('en-US', options);
  };

  const getPlatformColor = (platform: Platform) => {
    switch (platform) {
      case Platform.FACEBOOK:
        return '#1877f2';
      case Platform.INSTAGRAM:
        return '#E4405F';
      case Platform.TIKTOK:
        return '#000000';
      default:
        return '#gray';
    }
  };

  const getStatusColor = (status: PostStatus) => {
    switch (status) {
      case PostStatus.DRAFT:
        return 'gray';
      case PostStatus.SCHEDULED:
        return 'blue';
      case PostStatus.PUBLISHED:
        return 'green';
      case PostStatus.FAILED:
        return 'red';
      default:
        return 'gray';
    }
  };

  return (
    <Box style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Flex 
        justify="between" 
        align="center" 
        style={{ 
          padding: '1rem 2rem',
          borderBottom: '1px solid var(--gray-4)',
          backgroundColor: 'white',
          flexShrink: 0
        }}
      >
        <Flex gap="3" align="center">
          <IconButton onClick={() => navigatePeriod('prev')} variant="soft">
            <ChevronLeftIcon />
          </IconButton>
          
          <Flex align="center" gap="2">
            <CalendarIcon />
            <Text size="3" weight="medium">
              {viewMode === 'week' 
                ? `Week of ${dateRange.start.toLocaleDateString()}`
                : currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
              }
            </Text>
          </Flex>
          
          <IconButton onClick={() => navigatePeriod('next')} variant="soft">
            <ChevronRightIcon />
          </IconButton>
          
          <Button
            variant="soft"
            size="2"
            onClick={() => setViewMode(viewMode === 'week' ? 'month' : 'week')}
          >
            {viewMode === 'week' ? 'Month View' : 'Week View'}
          </Button>
        </Flex>

        <Flex gap="3">
          <Button onClick={onCreatePost} size="2">
            <PlusIcon /> Create Post
          </Button>
          <Button onClick={onCreateCampaign} size="2" color="purple">
            <VideoIcon /> Create Campaign
          </Button>
        </Flex>
      </Flex>

      {/* Calendar Grid */}
      <Box style={{ flex: 1, overflow: 'auto', padding: '1rem' }}>
        <Box
          style={{
            display: 'grid',
            gridTemplateColumns: viewMode === 'week' ? 'repeat(7, 1fr)' : 'repeat(7, 1fr)',
            gap: '1px',
            backgroundColor: 'var(--gray-4)',
            border: '1px solid var(--gray-4)',
            minHeight: 'min-content'
          }}
        >
          {/* Day Headers */}
          {calendarDays.slice(0, 7).map((day, index) => (
            <Box
              key={`header-${index}`}
              style={{
                backgroundColor: 'var(--gray-2)',
                padding: '0.5rem',
                textAlign: 'center',
                fontWeight: 'bold'
              }}
            >
              <Text size="2">
                {day.toLocaleDateString('en-US', { weekday: 'short' })}
              </Text>
            </Box>
          ))}

          {/* Calendar Days */}
          {calendarDays.map((day, index) => {
            const dateStr = day.toDateString();
            const dayPosts = postsByDate[dateStr] || [];
            const isToday = dateStr === new Date().toDateString();

            return (
              <Box
                key={`day-${index}`}
                style={{
                  backgroundColor: isToday ? 'var(--blue-1)' : 'white',
                  minHeight: '120px',
                  padding: '0.5rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.5rem',
                  overflow: 'auto'
                }}
              >
                <Flex justify="between" align="center">
                  <Text 
                    size="2" 
                    weight={isToday ? 'bold' : 'regular'}
                    color={isToday ? 'blue' : undefined}
                  >
                    {day.getDate()}
                  </Text>
                  {dayPosts.length > 0 && (
                    <Badge size="1" variant="soft">
                      {dayPosts.length}
                    </Badge>
                  )}
                </Flex>

                {dayPosts.map(post => (
                  <PostCard
                    key={post.id}
                    post={post}
                    onEdit={() => onEditPost(post)}
                    onDelete={() => onDeletePost(post.id)}
                    compact
                  />
                ))}
              </Box>
            );
          })}
        </Box>
      </Box>
    </Box>
  );
}; 
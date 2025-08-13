import { useEffect, useMemo, useState } from 'react';
import { Button, Flex, Heading, Text, Box, TextField, Select } from '@radix-ui/themes';
import { MagnifyingGlassIcon } from '@radix-ui/react-icons';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import api from '../api';
import { MainLayout } from '../components/MainLayout';

interface CSRecord {
  id: string;
  title?: string;
  category?: string;
  status?: string;
  channel?: string;
  tags?: string[];
  source_file?: string;
  author?: string;
  created_at?: string;
}

export default function CustomerServicePage() {
  const navigate = useNavigate();

  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const [status, setStatus] = useState('');
  const [channel, setChannel] = useState('');
  const [dateStart, setDateStart] = useState('');
  const [dateEnd, setDateEnd] = useState('');
  const [page, setPage] = useState(1);
  const [queryText, setQueryText] = useState('');
  const [queryResults, setQueryResults] = useState<Array<{text?: string; source?: string; created_at?: string; score?: number}>>([]);
  const pageSize = 50;

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['cs-records', search, category, status, channel, dateStart, dateEnd, page],
    queryFn: async () => {
      const params = new URLSearchParams({
        skip: String((page - 1) * pageSize),
        limit: String(pageSize),
      });
      if (search) params.set('search', search);
      if (category) params.set('category', category);
      if (status) params.set('status', status);
      if (channel) params.set('channel', channel);
      if (dateStart) params.set('start_date', dateStart);
      if (dateEnd) params.set('end_date', dateEnd);
      const res = await api.get(`/api/customer-service/records?${params.toString()}`);
      return res.data as {records: CSRecord[]; total: number};
    }
  });

  const doQuery = async () => {
    if (!queryText.trim()) return;
    setQueryResults([]);
    const res = await api.get(`/api/customer-service/search`, {
      params: { query: queryText, top_k: 10, prioritize_recent: true }
    });
    setQueryResults(res.data.results || []);
  };

  return (
    <MainLayout onNewChat={() => navigate('/home')}>
      <Flex direction="column" style={{ height: '100vh' }}>
        <Box style={{ padding: '1.5rem 2rem', borderBottom: '1px solid var(--gray-4)', backgroundColor: 'white', position: 'sticky', top: 0, zIndex: 1 }}>
          <Heading size="7" style={{ color: 'var(--gray-12)' }}>Customer Service</Heading>
          <Text as="p" size="3" style={{ color: 'var(--gray-10)', marginTop: '0.25rem' }}>
            Search, filter, and query your customer communications.
          </Text>
        </Box>

        <div style={{ padding: '1.5rem', display: 'grid', gridTemplateColumns: '1fr', gap: '1rem', overflowY: 'auto' }}>
          <Box style={{ background: 'white', border: '1px solid var(--border)', borderRadius: 8, padding: 16 }}>
            <Flex gap="2" align="center" wrap="wrap">
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1, minWidth: 280 }}>
                <MagnifyingGlassIcon />
                <input
                  style={{ border: '1px solid var(--border)', borderRadius: 6, padding: '8px 10px', flex: 1 }}
                  placeholder="Search title/content/categories/status..."
                  value={search}
                  onChange={e => { setSearch(e.target.value); setPage(1); }}
                />
              </div>
              <input type="date" value={dateStart} onChange={e => setDateStart(e.target.value)} />
              <input type="date" value={dateEnd} onChange={e => setDateEnd(e.target.value)} />
              <input placeholder="Category" value={category} onChange={e => setCategory(e.target.value)} />
              <input placeholder="Status" value={status} onChange={e => setStatus(e.target.value)} />
              <input placeholder="Channel" value={channel} onChange={e => setChannel(e.target.value)} />
              <Button onClick={() => { setPage(1); refetch(); }}>Apply</Button>
            </Flex>
          </Box>

          <Box style={{ background: 'white', border: '1px solid var(--border)', borderRadius: 8, padding: 16 }}>
            <Heading size="5">Records</Heading>
            <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: 12 }}>
              <thead>
                <tr>
                  <th style={{ textAlign: 'left', borderBottom: '1px solid var(--border)', padding: 8 }}>Title</th>
                  <th style={{ textAlign: 'left', borderBottom: '1px solid var(--border)', padding: 8 }}>Category</th>
                  <th style={{ textAlign: 'left', borderBottom: '1px solid var(--border)', padding: 8 }}>Status</th>
                  <th style={{ textAlign: 'left', borderBottom: '1px solid var(--border)', padding: 8 }}>Channel</th>
                  <th style={{ textAlign: 'left', borderBottom: '1px solid var(--border)', padding: 8 }}>Created</th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  <tr><td colSpan={5}>Loading...</td></tr>
                ) : (data?.records || []).length === 0 ? (
                  <tr><td colSpan={5}>No records</td></tr>
                ) : (
                  data!.records.map((r) => (
                    <tr key={r.id}>
                      <td style={{ padding: 8, borderBottom: '1px solid var(--border)' }}>{r.title || r.source_file || r.id}</td>
                      <td style={{ padding: 8, borderBottom: '1px solid var(--border)' }}>{r.category || '-'}</td>
                      <td style={{ padding: 8, borderBottom: '1px solid var(--border)' }}>{r.status || '-'}</td>
                      <td style={{ padding: 8, borderBottom: '1px solid var(--border)' }}>{r.channel || '-'}</td>
                      <td style={{ padding: 8, borderBottom: '1px solid var(--border)' }}>{r.created_at ? new Date(r.created_at).toLocaleDateString() : '-'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
            <div style={{ marginTop: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
              <Button disabled={page <= 1} onClick={() => setPage(p => Math.max(1, p - 1))}>Prev</Button>
              <Text>Page {page}</Text>
              <Button disabled={!!data && page * pageSize >= (data.total || 0)} onClick={() => setPage(p => p + 1)}>Next</Button>
              <Text style={{ marginLeft: 'auto' }}>{data ? `${Math.min(page * pageSize, data.total)} / ${data.total}` : ''}</Text>
            </div>
          </Box>

          <Box style={{ background: 'white', border: '1px solid var(--border)', borderRadius: 8, padding: 16 }}>
            <Heading size="5">Ask AI</Heading>
            <Flex gap="2" align="center" style={{ marginTop: 8 }}>
              <input
                style={{ border: '1px solid var(--border)', borderRadius: 6, padding: '8px 10px', flex: 1 }}
                placeholder="Ask a question about customer service communications..."
                value={queryText}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setQueryText(e.target.value)}
              />
              <Button onClick={doQuery}>Ask</Button>
            </Flex>
            <div style={{ marginTop: 12, display: 'grid', gap: 8 }}>
              {queryResults.map((r, i) => (
                <div key={i} style={{ border: '1px solid var(--gray-4)', borderRadius: 8, padding: 12 }}>
                  <div style={{ color: 'var(--gray-11)', fontSize: 12 }}>{r.source} {r.created_at ? `• ${new Date(r.created_at).toLocaleDateString()}` : ''}</div>
                  <div style={{ whiteSpace: 'pre-wrap' }}>{r.text}</div>
                </div>
              ))}
              {queryResults.length === 0 && (
                <Text size="2" color="gray">Results will appear here.</Text>
              )}
            </div>
          </Box>
        </div>
      </Flex>
    </MainLayout>
  );
} 
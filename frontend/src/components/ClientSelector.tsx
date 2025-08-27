import React, { useEffect, useMemo, useState } from 'react';
import { Box, TextField, Flex, Spinner, Text } from '@radix-ui/themes';

export interface ClientItem {
  id: number | null;
  title: string;
  app_id: number;
  app_name: string;
  error?: boolean;
}

interface ClientSelectorProps {
  value: number | null;
  onChange: (itemId: number | null) => void;
}

export const ClientSelector: React.FC<ClientSelectorProps> = ({ value, onChange }) => {
  const [items, setItems] = useState<ClientItem[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState<boolean>(false);

  useEffect(() => {
    const fetchClients = async () => {
      setLoading(true);
      try {
        const token = localStorage.getItem('token');
        const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/podio/clients?token=${token}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();
        setItems(Array.isArray(data.items) ? data.items : []);
      } catch (e) {
        setItems([]);
      } finally {
        setLoading(false);
      }
    };
    fetchClients();
  }, []);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return items.slice(0, 20);
    return items.filter(i => (i.title || '').toLowerCase().includes(q) || (i.app_name || '').toLowerCase().includes(q)).slice(0, 20);
  }, [items, query]);

  const selected = items.find(i => i.id === value) || null;

  return (
    <Box style={{ position: 'relative', width: '420px' }}>
      <TextField.Root
        placeholder={selected ? `${selected.title} (${selected.app_name})` : 'Select client (type to search...)'}
        value={query}
        onChange={(e) => { setQuery(e.target.value); setOpen(true); }}
        onFocus={() => setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
      />
      {open && (
        <Box style={{ position: 'absolute', top: '42px', left: 0, right: 0, maxHeight: '260px', overflowY: 'auto', background: 'white', border: '1px solid var(--gray-5)', borderRadius: '8px', zIndex: 20 }}>
          {loading ? (
            <Flex align="center" justify="center" style={{ padding: '12px' }}>
              <Spinner />
            </Flex>
          ) : (
            filtered.length === 0 ? (
              <Text size="2" style={{ padding: '8px 12px', color: 'var(--gray-10)' }}>No results</Text>
            ) : (
              filtered.map(item => (
                <div
                  key={`${item.app_id}-${item.id ?? item.title}`}
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={() => { onChange(item.id); setQuery(''); setOpen(false); }}
                  style={{ padding: '8px 12px', cursor: 'pointer', borderBottom: '1px solid var(--gray-3)' }}
                >
                  <div style={{ fontWeight: 600 }}>{item.title}</div>
                  <div style={{ fontSize: '12px', color: 'var(--gray-10)' }}>{item.app_name} · Item {item.id ?? 'N/A'}</div>
                </div>
              ))
            )
          )}
        </Box>
      )}
    </Box>
  );
};

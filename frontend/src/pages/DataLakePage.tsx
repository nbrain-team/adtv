import { useState, useMemo, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Checkbox, IconButton, Button, Flex, Heading, Text, Box, Dialog } from '@radix-ui/themes';
import { TrashIcon, ChevronLeftIcon, ChevronRightIcon, UploadIcon, DownloadIcon, EyeOpenIcon, EyeNoneIcon, MagnifyingGlassIcon, Cross2Icon } from '@radix-ui/react-icons';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import api from '../api';

interface DataLakeRecord {
  id: number;
  [key: string]: any;
}

const DataLakePage = () => {
  const queryClient = useQueryClient();
  const { token } = useAuth();
  const navigate = useNavigate();
  const [selectedRecords, setSelectedRecords] = useState<number[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [showAllColumns, setShowAllColumns] = useState(false);
  const [showImportDialog, setShowImportDialog] = useState(false);
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [columnMapping, setColumnMapping] = useState<Record<string, string>>({});
  const [csvColumns, setCsvColumns] = useState<string[]>([]);
  const [isImporting, setIsImporting] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const recordsPerPage = 50;

  // Define the first 10 columns to show initially
  const initialColumns = [
    'unique_id', 'lead_source', 'tier', 'city', 'first_name',
    'last_name', 'company', 'phone', 'email', 'dma'
  ];

  const allColumns = [
    'unique_id', 'lead_source', 'tier', 'city', 'first_name', 'last_name', 'company', 
    'phone', 'email', 'dma', 'one_yr_total_sales_usd', 'state_initials', 'state_spelled_out',
    'website', 'business_facebook_url', 'instagram_url', 'years_experience',
    'one_yr_seller_deals_count', 'one_yr_seller_deals_usd', 'one_yr_buyer_deals_count',
    'one_yr_buyer_deals_usd', 'one_yr_total_transactions_count', 'average_home_sale_price_usd'
  ];

  const visibleColumns = showAllColumns ? allColumns : initialColumns;

  // Fetch records from API
  const { data: recordsData = { records: [], total: 0 }, isLoading, error } = useQuery({
    queryKey: ['dataLakeRecords', currentPage, searchTerm, showAllColumns],
    queryFn: async () => {
      const params = new URLSearchParams({
        skip: ((currentPage - 1) * recordsPerPage).toString(),
        limit: recordsPerPage.toString(),
        ...(searchTerm && { search: searchTerm }),
        columns: visibleColumns.join(',')
      });
      
      const response = await api.get(`/data-lake/records?${params}`);
      return response.data;
    },
    retry: (failureCount, error: any) => {
      // Don't retry on 401 errors
      if (error?.response?.status === 401) {
        return false;
      }
      return failureCount < 3;
    }
  });

  // Handle authentication errors
  if (error && (error as any)?.response?.status === 401) {
    navigate('/login');
    return null;
  }

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/data-lake/records/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dataLakeRecords'] });
    }
  });

  // Export CSV
  const handleExport = async () => {
    try {
      const params = new URLSearchParams({
        columns: visibleColumns.join(',')
      });
      const response = await api.get(`/data-lake/export-csv?${params}`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.download = `data_lake_export_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting data:', error);
    }
  };

  // CSV Import handlers
  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    
    setCsvFile(file);
    
    // Analyze CSV to get column suggestions
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await api.post('/data-lake/analyze-csv', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      setCsvColumns(response.data.csv_columns);
      setColumnMapping(response.data.suggestions);
      setShowImportDialog(true);
    } catch (error) {
      console.error('Error analyzing CSV:', error);
      alert('Error analyzing CSV file. Please check the file format.');
    }
  };

  const handleImport = async () => {
    if (!csvFile) return;
    
    setIsImporting(true);
    try {
      const formData = new FormData();
      formData.append('file', csvFile);
      
      const response = await api.post(`/data-lake/import-csv?mapping=${encodeURIComponent(JSON.stringify(columnMapping))}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      alert(`Successfully imported ${response.data.imported} records!`);
      setShowImportDialog(false);
      setCsvFile(null);
      setColumnMapping({});
      setCsvColumns([]);
      queryClient.invalidateQueries({ queryKey: ['dataLakeRecords'] });
    } catch (error) {
      console.error('Error importing CSV:', error);
      alert('Error importing CSV. Please check the file and try again.');
    } finally {
      setIsImporting(false);
    }
  };

  const totalPages = Math.ceil(recordsData.total / recordsPerPage);

  const handleRecordSelection = (id: number, isSelected: boolean) => {
    if (isSelected) {
      setSelectedRecords(prev => [...prev, id]);
    } else {
      setSelectedRecords(prev => prev.filter(recordId => recordId !== id));
    }
  };

  const formatColumnName = (column: string) => {
    return column
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ')
      .replace(/Usd/g, 'USD')
      .replace(/One Yr/g, '1YR');
  };

  const formatCellValue = (value: any, column: string) => {
    if (value === null || value === undefined) return '-';
    
    if (column.includes('_date')) {
      return new Date(value).toLocaleDateString();
    }
    
    if (column.includes('_usd') || column === 'initiation_fee' || column === 'monthly_recurring_revenue') {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
      }).format(value);
    }
    
    if (typeof value === 'boolean') {
      return value ? '✓' : '✗';
    }
    
    return value;
  };

  return (
    <Flex direction="column" style={{ height: '100vh' }}>
      <style>{STYLES}</style>
      
      <Box style={{ padding: '1.5rem 2rem', borderBottom: '1px solid var(--gray-4)', backgroundColor: 'white', position: 'sticky', top: 0, zIndex: 1 }}>
        <Heading size="7" style={{ color: 'var(--gray-12)' }}>Data Lake</Heading>
        <Text as="p" size="3" style={{ color: 'var(--gray-10)', marginTop: '0.25rem' }}>
          View, filter, and manage your data records.
        </Text>
      </Box>

      <div className="data-lake-container" style={{ flex: 1, overflowY: 'auto' }}>
        <section className="controls-section">
          <div className="search-bar">
            <MagnifyingGlassIcon />
            <input 
              type="text" 
              placeholder="Search across all fields..." 
              value={searchTerm}
              onChange={e => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
            />
          </div>
          
          <div className="action-buttons">
            <Button variant="soft" onClick={() => setShowAllColumns(!showAllColumns)}>
              {showAllColumns ? <EyeNoneIcon /> : <EyeOpenIcon />}
              {showAllColumns ? 'Show Less' : 'Show All Columns'}
            </Button>
            
            <Button variant="soft" color="blue" onClick={() => fileInputRef.current?.click()}>
              <UploadIcon />
              Import CSV
            </Button>
            
            <Button variant="soft" color="green" onClick={handleExport}>
              <DownloadIcon />
              Export CSV
            </Button>
          </div>
        </section>

        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          style={{ display: 'none' }}
          onChange={handleFileSelect}
        />

        <section className="table-section">
          <table id="data-lake-table">
            <thead>
              <tr>
                <th><Checkbox disabled /></th>
                {visibleColumns.map(column => (
                  <th key={column}>{formatColumnName(column)}</th>
                ))}
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr><td colSpan={visibleColumns.length + 2}>Loading records...</td></tr>
              ) : recordsData.records.length > 0 ? (
                recordsData.records.map((record: DataLakeRecord) => (
                  <tr 
                    key={record.id}
                    onClick={() => handleRecordSelection(record.id, !selectedRecords.includes(record.id))}
                    style={{ 
                      cursor: 'pointer',
                      backgroundColor: selectedRecords.includes(record.id) ? 'var(--blue-2)' : 'transparent'
                    }}
                  >
                    <td>
                      <Checkbox 
                        checked={selectedRecords.includes(record.id)}
                        onCheckedChange={(checked) => handleRecordSelection(record.id, !!checked)} 
                      />
                    </td>
                    {visibleColumns.map(column => (
                      <td key={column}>{formatCellValue(record[column], column)}</td>
                    ))}
                    <td>
                      <IconButton 
                        variant="ghost" 
                        color="red" 
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteMutation.mutate(record.id);
                        }} 
                        disabled={deleteMutation.isPending}
                      >
                        <TrashIcon />
                      </IconButton>
                    </td>
                  </tr>
                ))
              ) : (
                <tr><td colSpan={visibleColumns.length + 2}>No records found.</td></tr>
              )}
            </tbody>
          </table>
          
          {error ? (
            <div style={{ 
              padding: '2rem', 
              textAlign: 'center', 
              color: 'var(--red-11)',
              backgroundColor: 'var(--red-2)',
              borderRadius: '8px',
              margin: '1rem 0'
            }}>
              {(error as any)?.response?.status === 401 
                ? 'Please log in to access the Data Lake.' 
                : 'Error loading records. Please try again.'}
            </div>
          ) : null}
          
          {totalPages > 1 && (
            <div className="pagination-controls">
              <Button 
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                variant="soft"
              >
                <ChevronLeftIcon /> Previous
              </Button>
              <span>
                Page {currentPage} of {totalPages}
              </span>
              <Button 
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                variant="soft"
              >
                Next <ChevronRightIcon />
              </Button>
            </div>
          )}
          
          <div style={{ marginTop: '1rem', color: 'var(--gray-10)' }}>
            Showing {recordsData.records.length > 0 ? ((currentPage - 1) * recordsPerPage) + 1 : 0} to {Math.min(currentPage * recordsPerPage, recordsData.total)} of {recordsData.total} records
          </div>
        </section>
      </div>

      <Dialog.Root open={showImportDialog} onOpenChange={setShowImportDialog}>
        <Dialog.Content maxWidth="600px">
          <Dialog.Title>Import CSV - Map Columns</Dialog.Title>
          <Dialog.Description>
            Map your CSV columns to the database fields. We've suggested some mappings based on column names.
          </Dialog.Description>
          
          <div style={{ marginTop: '1rem', maxHeight: '400px', overflowY: 'auto' }}>
            {csvColumns.map((csvCol) => (
              <div key={csvCol} style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <Text style={{ flex: 1, fontWeight: '500' }}>{csvCol}</Text>
                <select
                  value={columnMapping[csvCol] || ''}
                  onChange={(e) => setColumnMapping(prev => ({ ...prev, [csvCol]: e.target.value }))}
                  style={{
                    flex: 1,
                    padding: '0.5rem',
                    borderRadius: '4px',
                    border: '1px solid var(--gray-6)'
                  }}
                >
                  <option value="">-- Skip this column --</option>
                  {allColumns.map(dbCol => (
                    <option key={dbCol} value={dbCol}>{formatColumnName(dbCol)}</option>
                  ))}
                </select>
              </div>
            ))}
          </div>
          
          <Flex gap="3" mt="4" justify="end">
            <Dialog.Close>
              <Button variant="soft" color="gray">
                Cancel
              </Button>
            </Dialog.Close>
            <Button onClick={handleImport} disabled={isImporting}>
              {isImporting ? 'Importing...' : 'Import'}
            </Button>
          </Flex>
        </Dialog.Content>
      </Dialog.Root>
    </Flex>
  );
};

const STYLES = `
  .data-lake-container {
    display: flex;
    flex-direction: column;
    gap: 2rem;
    padding: 1.5rem;
    max-width: 1400px;
    margin: 0 auto;
    width: 100%;
  }
  
  .controls-section {
    background: var(--card-bg);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
    border: 1px solid var(--border);
    padding: 1.5rem;
    display: flex;
    gap: 1rem;
    align-items: center;
    flex-wrap: wrap;
  }
  
  .search-bar {
    flex: 1;
    min-width: 300px;
    position: relative;
    display: flex;
    align-items: center;
    background: white;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0 1rem;
  }
  
  .search-bar svg {
    color: var(--gray-8);
    width: 20px;
    height: 20px;
  }
  
  .search-bar input {
    flex: 1;
    border: none;
    outline: none;
    padding: 0.75rem;
    font-size: 1rem;
    background: transparent;
  }
  
  .action-buttons {
    display: flex;
    gap: 0.75rem;
  }
  
  .table-section {
    background: var(--card-bg);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
    border: 1px solid var(--border);
    padding: 1.5rem;
    overflow-x: auto;
  }
  
  #data-lake-table {
    width: 100%;
    border-collapse: collapse;
  }
  
  #data-lake-table th, #data-lake-table td {
    text-align: left;
    padding: 0.75rem;
    border-bottom: 1px solid var(--gray-3);
  }
  
  #data-lake-table th {
    font-weight: 600;
    color: var(--gray-11);
    background-color: var(--gray-1);
  }
  
  #data-lake-table tbody tr:hover {
    background-color: var(--gray-2);
  }
  
  #data-lake-table tbody tr.selected {
    background-color: var(--blue-2);
  }
  
  .pagination-controls {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    margin-top: 1.5rem;
  }
  
  .pagination-controls span {
    color: var(--gray-10);
  }
`;

export default DataLakePage; 
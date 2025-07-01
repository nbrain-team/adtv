import React, { useState, useEffect, useCallback } from 'react';
import { Upload, Download, Filter, Search, Eye, EyeOff, Edit, Trash2, Save } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import DataLakeTable from '../components/DataLake/DataLakeTable';
import DataLakeFilters from '../components/DataLake/DataLakeFilters';
import CSVImportModal from '../components/DataLake/CSVImportModal';
import BulkEditModal from '../components/DataLake/BulkEditModal';

interface DataLakeRecord {
  id: number;
  [key: string]: any;
}

const DataLakePage: React.FC = () => {
  const { token } = useAuth();
  const [records, setRecords] = useState<DataLakeRecord[]>([]);
  const [totalRecords, setTotalRecords] = useState(0);
  const [loading, setLoading] = useState(false);
  const [showAllColumns, setShowAllColumns] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<Record<string, any>>({});
  const [selectedRecords, setSelectedRecords] = useState<number[]>([]);
  const [showImportModal, setShowImportModal] = useState(false);
  const [showBulkEditModal, setShowBulkEditModal] = useState(false);
  const [sortConfig, setSortConfig] = useState<{ field: string; order: 'asc' | 'desc' } | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(50);
  const [fieldDefinitions, setFieldDefinitions] = useState<Record<string, string[]>>({});

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
    'one_yr_buyer_deals_usd', 'one_yr_total_transactions_count', 'average_home_sale_price_usd',
    'invitation_response', 'invitation_response_notes', 'appointment_set_date', 'rep',
    'b2b_call_center_vsa', 'interest_level', 'attendance', 'tims_notes', 'craigs_notes',
    'rejected_by_presenter', 'profession', 'event_date', 'event_time', 'time_zone',
    'hotel_name', 'hotel_street_address', 'hotel_city', 'hotel_state', 'hotel_zip_code',
    'hotel_meeting_room_name', 'lion_flag', 'sale_date', 'contract_status', 'event_type',
    'client_type', 'partner_show_market', 'sale_type', 'sale_closed_by_market_manager',
    'sale_closed_by_bdr', 'friday_deadline', 'start_date', 'initiation_fee',
    'monthly_recurring_revenue', 'paid_membership_in_advance', 'account_manager_notes',
    'referred_by', 'speaker_source', 'data_source', 'lender_one_yr_volume_usd',
    'lender_one_yr_closed_loans_count', 'lender_banker_or_broker'
  ];

  const visibleColumns = showAllColumns ? allColumns : initialColumns;

  useEffect(() => {
    fetchFieldDefinitions();
    fetchRecords();
  }, [currentPage, sortConfig, searchQuery, filters]);

  const fetchFieldDefinitions = async () => {
    try {
      const response = await fetch('/api/data-lake/field-definitions', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setFieldDefinitions(data);
      }
    } catch (error) {
      console.error('Error fetching field definitions:', error);
    }
  };

  const fetchRecords = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        skip: ((currentPage - 1) * pageSize).toString(),
        limit: pageSize.toString(),
        ...(searchQuery && { search: searchQuery }),
        ...(Object.keys(filters).length > 0 && { filters: JSON.stringify(filters) }),
        ...(sortConfig && { sort_by: sortConfig.field, sort_order: sortConfig.order }),
        columns: visibleColumns.join(',')
      });

      const response = await fetch(`/api/data-lake/records?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setRecords(data.records);
        setTotalRecords(data.total);
      }
    } catch (error) {
      console.error('Error fetching records:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      const params = new URLSearchParams({
        ...(Object.keys(filters).length > 0 && { filters: JSON.stringify(filters) }),
        columns: visibleColumns.join(',')
      });

      const response = await fetch(`/api/data-lake/export-csv?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `data_lake_export_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      console.error('Error exporting data:', error);
    }
  };

  const handleDeleteRecord = async (id: number) => {
    if (!confirm('Are you sure you want to delete this record?')) return;

    try {
      const response = await fetch(`/api/data-lake/records/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        fetchRecords();
      }
    } catch (error) {
      console.error('Error deleting record:', error);
    }
  };

  const handleBulkEdit = async (updates: Record<string, any>) => {
    try {
      const response = await fetch('/api/data-lake/bulk-edit', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          record_ids: selectedRecords,
          updates
        })
      });

      if (response.ok) {
        setSelectedRecords([]);
        setShowBulkEditModal(false);
        fetchRecords();
      }
    } catch (error) {
      console.error('Error bulk editing records:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-full mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold">Data Lake</h1>
          <div className="flex gap-4">
            <button
              onClick={() => setShowImportModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
            >
              <Upload className="w-4 h-4" />
              Import CSV
            </button>
            <button
              onClick={handleExport}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition-colors"
            >
              <Download className="w-4 h-4" />
              Export CSV
            </button>
          </div>
        </div>

        {/* Search and Filter Bar */}
        <div className="bg-gray-800 rounded-lg p-4 mb-6">
          <div className="flex gap-4 items-center">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search across all fields..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <button
              onClick={() => setShowAllColumns(!showAllColumns)}
              className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
            >
              {showAllColumns ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              {showAllColumns ? 'Show Less' : 'Show All Columns'}
            </button>
            {selectedRecords.length > 0 && (
              <button
                onClick={() => setShowBulkEditModal(true)}
                className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors"
              >
                <Edit className="w-4 h-4" />
                Bulk Edit ({selectedRecords.length})
              </button>
            )}
          </div>
          
          <DataLakeFilters
            filters={filters}
            onFiltersChange={setFilters}
            fieldDefinitions={fieldDefinitions}
          />
        </div>

        {/* Data Table */}
        <DataLakeTable
          records={records}
          visibleColumns={visibleColumns}
          loading={loading}
          selectedRecords={selectedRecords}
          onSelectRecords={setSelectedRecords}
          sortConfig={sortConfig}
          onSort={setSortConfig}
          onEdit={(record) => console.log('Edit record:', record)}
          onDelete={handleDeleteRecord}
          fieldDefinitions={fieldDefinitions}
        />

        {/* Pagination */}
        <div className="mt-6 flex justify-between items-center">
          <div className="text-gray-400">
            Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, totalRecords)} of {totalRecords} records
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <span className="px-4 py-2 bg-gray-800 rounded-lg">
              Page {currentPage} of {Math.ceil(totalRecords / pageSize)}
            </span>
            <button
              onClick={() => setCurrentPage(p => p + 1)}
              disabled={currentPage >= Math.ceil(totalRecords / pageSize)}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>

        {/* Modals */}
        {showImportModal && (
          <CSVImportModal
            onClose={() => setShowImportModal(false)}
            onImportComplete={() => {
              setShowImportModal(false);
              fetchRecords();
            }}
          />
        )}

        {showBulkEditModal && (
          <BulkEditModal
            selectedCount={selectedRecords.length}
            fieldDefinitions={fieldDefinitions}
            onClose={() => setShowBulkEditModal(false)}
            onSave={handleBulkEdit}
          />
        )}
      </div>
    </div>
  );
};

export default DataLakePage; 
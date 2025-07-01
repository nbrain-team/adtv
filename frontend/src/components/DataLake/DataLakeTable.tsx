import React from 'react';
import { ChevronUp, ChevronDown, Edit2, Trash2, CheckSquare, Square } from 'lucide-react';

interface DataLakeTableProps {
  records: any[];
  visibleColumns: string[];
  loading: boolean;
  selectedRecords: number[];
  onSelectRecords: (ids: number[]) => void;
  sortConfig: { field: string; order: 'asc' | 'desc' } | null;
  onSort: (config: { field: string; order: 'asc' | 'desc' }) => void;
  onEdit: (record: any) => void;
  onDelete: (id: number) => void;
  fieldDefinitions: Record<string, string[]>;
}

const DataLakeTable: React.FC<DataLakeTableProps> = ({
  records,
  visibleColumns,
  loading,
  selectedRecords,
  onSelectRecords,
  sortConfig,
  onSort,
  onEdit,
  onDelete,
  fieldDefinitions
}) => {
  const formatColumnName = (column: string) => {
    return column
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ')
      .replace(/Usd/g, 'USD')
      .replace(/Url/g, 'URL')
      .replace(/Vsa/g, 'VSA')
      .replace(/Bdr/g, 'BDR')
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

  const handleSort = (column: string) => {
    const newOrder = sortConfig?.field === column && sortConfig.order === 'asc' ? 'desc' : 'asc';
    onSort({ field: column, order: newOrder });
  };

  const handleSelectAll = () => {
    if (selectedRecords.length === records.length) {
      onSelectRecords([]);
    } else {
      onSelectRecords(records.map(r => r.id));
    }
  };

  const handleSelectRecord = (id: number) => {
    if (selectedRecords.includes(id)) {
      onSelectRecords(selectedRecords.filter(rid => rid !== id));
    } else {
      onSelectRecords([...selectedRecords, id]);
    }
  };

  if (loading) {
    return (
      <div className="bg-gray-800 rounded-lg p-8 text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
        <p className="mt-4 text-gray-400">Loading records...</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-700">
            <tr>
              <th className="sticky left-0 bg-gray-700 p-3 text-left">
                <button onClick={handleSelectAll} className="hover:text-blue-400">
                  {selectedRecords.length === records.length && records.length > 0 ? (
                    <CheckSquare className="w-5 h-5" />
                  ) : (
                    <Square className="w-5 h-5" />
                  )}
                </button>
              </th>
              {visibleColumns.map(column => (
                <th key={column} className="p-3 text-left whitespace-nowrap">
                  <button
                    onClick={() => handleSort(column)}
                    className="flex items-center gap-1 hover:text-blue-400"
                  >
                    {formatColumnName(column)}
                    {sortConfig?.field === column && (
                      sortConfig.order === 'asc' ? (
                        <ChevronUp className="w-4 h-4" />
                      ) : (
                        <ChevronDown className="w-4 h-4" />
                      )
                    )}
                  </button>
                </th>
              ))}
              <th className="p-3 text-center">Actions</th>
            </tr>
          </thead>
          <tbody>
            {records.length === 0 ? (
              <tr>
                <td colSpan={visibleColumns.length + 2} className="p-8 text-center text-gray-400">
                  No records found
                </td>
              </tr>
            ) : (
              records.map((record, index) => (
                <tr 
                  key={record.id} 
                  className={`border-t border-gray-700 hover:bg-gray-700/50 ${
                    selectedRecords.includes(record.id) ? 'bg-gray-700/30' : ''
                  }`}
                >
                  <td className="sticky left-0 bg-gray-800 p-3">
                    <button onClick={() => handleSelectRecord(record.id)}>
                      {selectedRecords.includes(record.id) ? (
                        <CheckSquare className="w-5 h-5 text-blue-400" />
                      ) : (
                        <Square className="w-5 h-5" />
                      )}
                    </button>
                  </td>
                  {visibleColumns.map(column => (
                    <td key={column} className="p-3 whitespace-nowrap">
                      {formatCellValue(record[column], column)}
                    </td>
                  ))}
                  <td className="p-3">
                    <div className="flex gap-2 justify-center">
                      <button
                        onClick={() => onEdit(record)}
                        className="p-1 hover:bg-gray-600 rounded"
                        title="Edit"
                      >
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => onDelete(record.id)}
                        className="p-1 hover:bg-red-600 rounded"
                        title="Delete"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default DataLakeTable; 
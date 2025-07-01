import React, { useState } from 'react';
import { Filter, X } from 'lucide-react';

interface DataLakeFiltersProps {
  filters: Record<string, any>;
  onFiltersChange: (filters: Record<string, any>) => void;
  fieldDefinitions: Record<string, string[]>;
}

const DataLakeFilters: React.FC<DataLakeFiltersProps> = ({
  filters,
  onFiltersChange,
  fieldDefinitions
}) => {
  const [showFilters, setShowFilters] = useState(false);

  const filterableFields = [
    { key: 'lead_source', label: 'Lead Source', type: 'text' },
    { key: 'tier', label: 'Tier', type: 'number' },
    { key: 'city', label: 'City', type: 'text' },
    { key: 'state_initials', label: 'State', type: 'text' },
    { key: 'invitation_response', label: 'Invitation Response', type: 'select' },
    { key: 'profession', label: 'Profession', type: 'select' },
    { key: 'contract_status', label: 'Contract Status', type: 'select' },
    { key: 'event_type', label: 'Event Type', type: 'select' },
    { key: 'client_type', label: 'Client Type', type: 'select' },
    { key: 'sale_type', label: 'Sale Type', type: 'select' },
  ];

  const handleFilterChange = (key: string, value: any) => {
    if (value === '' || value === null) {
      const newFilters = { ...filters };
      delete newFilters[key];
      onFiltersChange(newFilters);
    } else {
      onFiltersChange({ ...filters, [key]: value });
    }
  };

  const clearFilters = () => {
    onFiltersChange({});
  };

  const activeFilterCount = Object.keys(filters).length;

  return (
    <div className="mt-4">
      <button
        onClick={() => setShowFilters(!showFilters)}
        className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
      >
        <Filter className="w-4 h-4" />
        Filters {activeFilterCount > 0 && `(${activeFilterCount})`}
      </button>

      {showFilters && (
        <div className="mt-4 p-4 bg-gray-700 rounded-lg">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">Filter Records</h3>
            {activeFilterCount > 0 && (
              <button
                onClick={clearFilters}
                className="text-sm text-red-400 hover:text-red-300"
              >
                Clear All
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filterableFields.map(field => (
              <div key={field.key}>
                <label className="block text-sm font-medium mb-1">
                  {field.label}
                </label>
                {field.type === 'select' && fieldDefinitions[field.key] ? (
                  <select
                    value={filters[field.key] || ''}
                    onChange={(e) => handleFilterChange(field.key, e.target.value)}
                    className="w-full px-3 py-2 bg-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">All</option>
                    {fieldDefinitions[field.key].map(option => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                ) : field.type === 'number' ? (
                  <input
                    type="number"
                    value={filters[field.key] || ''}
                    onChange={(e) => handleFilterChange(field.key, e.target.value ? parseInt(e.target.value) : null)}
                    placeholder={`Filter by ${field.label.toLowerCase()}`}
                    className="w-full px-3 py-2 bg-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                ) : (
                  <input
                    type="text"
                    value={filters[field.key] || ''}
                    onChange={(e) => handleFilterChange(field.key, e.target.value)}
                    placeholder={`Filter by ${field.label.toLowerCase()}`}
                    className="w-full px-3 py-2 bg-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                )}
              </div>
            ))}
          </div>

          {/* Active Filters Display */}
          {activeFilterCount > 0 && (
            <div className="mt-4 flex flex-wrap gap-2">
              {Object.entries(filters).map(([key, value]) => {
                const field = filterableFields.find(f => f.key === key);
                return (
                  <div
                    key={key}
                    className="flex items-center gap-2 px-3 py-1 bg-blue-600 rounded-full text-sm"
                  >
                    <span>{field?.label}: {value}</span>
                    <button
                      onClick={() => handleFilterChange(key, null)}
                      className="hover:text-gray-300"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default DataLakeFilters; 
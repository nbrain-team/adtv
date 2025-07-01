import React, { useState } from 'react';
import { X, Save } from 'lucide-react';

interface BulkEditModalProps {
  selectedCount: number;
  fieldDefinitions: Record<string, string[]>;
  onClose: () => void;
  onSave: (updates: Record<string, any>) => void;
}

const BulkEditModal: React.FC<BulkEditModalProps> = ({
  selectedCount,
  fieldDefinitions,
  onClose,
  onSave
}) => {
  const [updates, setUpdates] = useState<Record<string, any>>({});
  const [selectedFields, setSelectedFields] = useState<string[]>([]);

  const editableFields = [
    { key: 'lead_source', label: 'Lead Source', type: 'text' },
    { key: 'tier', label: 'Tier', type: 'number' },
    { key: 'city', label: 'City', type: 'text' },
    { key: 'state_initials', label: 'State', type: 'text' },
    { key: 'invitation_response', label: 'Invitation Response', type: 'select' },
    { key: 'interest_level', label: 'Interest Level', type: 'select' },
    { key: 'attendance', label: 'Attendance', type: 'select' },
    { key: 'profession', label: 'Profession', type: 'select' },
    { key: 'contract_status', label: 'Contract Status', type: 'select' },
    { key: 'event_type', label: 'Event Type', type: 'select' },
    { key: 'client_type', label: 'Client Type', type: 'select' },
    { key: 'sale_type', label: 'Sale Type', type: 'select' },
    { key: 'b2b_call_center_vsa', label: 'B2B Call Center (VSA)', type: 'boolean' },
    { key: 'rejected_by_presenter', label: 'Rejected by Presenter', type: 'boolean' },
    { key: 'lion_flag', label: 'Lion Flag', type: 'boolean' },
  ];

  const handleFieldToggle = (fieldKey: string) => {
    if (selectedFields.includes(fieldKey)) {
      setSelectedFields(selectedFields.filter(f => f !== fieldKey));
      const newUpdates = { ...updates };
      delete newUpdates[fieldKey];
      setUpdates(newUpdates);
    } else {
      setSelectedFields([...selectedFields, fieldKey]);
    }
  };

  const handleValueChange = (fieldKey: string, value: any) => {
    setUpdates({
      ...updates,
      [fieldKey]: value
    });
  };

  const handleSave = () => {
    // Only send updates for selected fields
    const finalUpdates: Record<string, any> = {};
    selectedFields.forEach(field => {
      if (field in updates) {
        finalUpdates[field] = updates[field];
      }
    });
    onSave(finalUpdates);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-2xl font-bold">Bulk Edit Records</h2>
            <p className="text-gray-400 mt-1">Editing {selectedCount} selected records</p>
          </div>
          <button onClick={onClose} className="hover:text-gray-400">
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="space-y-4">
          {editableFields.map(field => (
            <div key={field.key} className="border border-gray-700 rounded-lg p-4">
              <div className="flex items-center gap-3 mb-3">
                <input
                  type="checkbox"
                  id={field.key}
                  checked={selectedFields.includes(field.key)}
                  onChange={() => handleFieldToggle(field.key)}
                  className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500"
                />
                <label htmlFor={field.key} className="font-medium">
                  {field.label}
                </label>
              </div>

              {selectedFields.includes(field.key) && (
                <div className="ml-7">
                  {field.type === 'select' && fieldDefinitions[field.key] ? (
                    <select
                      value={updates[field.key] || ''}
                      onChange={(e) => handleValueChange(field.key, e.target.value)}
                      className="w-full px-3 py-2 bg-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">-- Select --</option>
                      {fieldDefinitions[field.key].map(option => (
                        <option key={option} value={option}>
                          {option}
                        </option>
                      ))}
                    </select>
                  ) : field.type === 'boolean' ? (
                    <div className="flex gap-4">
                      <label className="flex items-center gap-2">
                        <input
                          type="radio"
                          name={field.key}
                          value="true"
                          checked={updates[field.key] === true}
                          onChange={() => handleValueChange(field.key, true)}
                          className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                        />
                        <span>Yes</span>
                      </label>
                      <label className="flex items-center gap-2">
                        <input
                          type="radio"
                          name={field.key}
                          value="false"
                          checked={updates[field.key] === false}
                          onChange={() => handleValueChange(field.key, false)}
                          className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                        />
                        <span>No</span>
                      </label>
                    </div>
                  ) : field.type === 'number' ? (
                    <input
                      type="number"
                      value={updates[field.key] || ''}
                      onChange={(e) => handleValueChange(field.key, e.target.value ? parseInt(e.target.value) : null)}
                      placeholder={`Enter ${field.label.toLowerCase()}`}
                      className="w-full px-3 py-2 bg-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  ) : (
                    <input
                      type="text"
                      value={updates[field.key] || ''}
                      onChange={(e) => handleValueChange(field.key, e.target.value)}
                      placeholder={`Enter ${field.label.toLowerCase()}`}
                      className="w-full px-3 py-2 bg-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  )}
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="flex justify-end gap-4 mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={selectedFields.length === 0}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Save className="w-4 h-4" />
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
};

export default BulkEditModal; 
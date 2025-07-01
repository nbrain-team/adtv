import React, { useState, useRef } from 'react';
import { X, Upload, FileText, AlertCircle, CheckCircle } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface CSVImportModalProps {
  onClose: () => void;
  onImportComplete: () => void;
}

interface ColumnMapping {
  [csvColumn: string]: string | null;
}

const CSVImportModal: React.FC<CSVImportModalProps> = ({ onClose, onImportComplete }) => {
  const { token } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [csvColumns, setCsvColumns] = useState<string[]>([]);
  const [dbColumns, setDbColumns] = useState<string[]>([]);
  const [columnMapping, setColumnMapping] = useState<ColumnMapping>({});
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [importResult, setImportResult] = useState<{
    imported: number;
    errors: string[];
    total_errors: number;
  } | null>(null);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    setFile(selectedFile);
    setIsAnalyzing(true);
    setImportResult(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch('/api/data-lake/analyze-csv', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        setCsvColumns(data.csv_columns);
        setDbColumns(data.db_columns);
        setColumnMapping(data.suggestions);
      }
    } catch (error) {
      console.error('Error analyzing CSV:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleMappingChange = (csvColumn: string, dbField: string | null) => {
    setColumnMapping({
      ...columnMapping,
      [csvColumn]: dbField
    });
  };

  const handleImport = async () => {
    if (!file) return;

    setIsImporting(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`/api/data-lake/import-csv?mapping=${encodeURIComponent(JSON.stringify(columnMapping))}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });

      if (response.ok) {
        const result = await response.json();
        setImportResult(result);
        if (result.errors.length === 0) {
          setTimeout(() => {
            onImportComplete();
          }, 2000);
        }
      }
    } catch (error) {
      console.error('Error importing CSV:', error);
    } finally {
      setIsImporting(false);
    }
  };

  const formatDbColumnName = (column: string) => {
    return column
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ')
      .replace(/Usd/g, 'USD')
      .replace(/One Yr/g, '1YR');
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold">Import CSV Data</h2>
          <button onClick={onClose} className="hover:text-gray-400">
            <X className="w-6 h-6" />
          </button>
        </div>

        {!file ? (
          <div className="text-center py-12">
            <FileText className="w-16 h-16 mx-auto text-gray-500 mb-4" />
            <p className="text-gray-400 mb-4">Select a CSV file to import</p>
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              onChange={handleFileSelect}
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg mx-auto"
            >
              <Upload className="w-5 h-5" />
              Choose File
            </button>
          </div>
        ) : (
          <>
            <div className="mb-6 p-4 bg-gray-700 rounded-lg">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-blue-400" />
                <span className="font-medium">{file.name}</span>
                <button
                  onClick={() => {
                    setFile(null);
                    setCsvColumns([]);
                    setColumnMapping({});
                    setImportResult(null);
                  }}
                  className="ml-auto text-sm text-red-400 hover:text-red-300"
                >
                  Remove
                </button>
              </div>
            </div>

            {isAnalyzing ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                <p className="text-gray-400">Analyzing CSV file...</p>
              </div>
            ) : csvColumns.length > 0 ? (
              <>
                <h3 className="text-lg font-semibold mb-4">Map CSV Columns to Database Fields</h3>
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {csvColumns.map(csvCol => (
                    <div key={csvCol} className="flex items-center gap-4">
                      <div className="w-1/3 text-sm font-medium">{csvCol}</div>
                      <div className="w-1/3">→</div>
                      <select
                        value={columnMapping[csvCol] || ''}
                        onChange={(e) => handleMappingChange(csvCol, e.target.value || null)}
                        className="w-1/3 px-3 py-2 bg-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="">-- Skip --</option>
                        {dbColumns.map(dbCol => (
                          <option key={dbCol} value={dbCol}>
                            {formatDbColumnName(dbCol)}
                          </option>
                        ))}
                      </select>
                    </div>
                  ))}
                </div>

                {importResult && (
                  <div className={`mt-6 p-4 rounded-lg ${importResult.errors.length > 0 ? 'bg-yellow-900' : 'bg-green-900'}`}>
                    <div className="flex items-center gap-2 mb-2">
                      {importResult.errors.length > 0 ? (
                        <AlertCircle className="w-5 h-5 text-yellow-400" />
                      ) : (
                        <CheckCircle className="w-5 h-5 text-green-400" />
                      )}
                      <span className="font-medium">
                        Import Complete: {importResult.imported} records imported
                      </span>
                    </div>
                    {importResult.errors.length > 0 && (
                      <>
                        <p className="text-sm text-yellow-300 mb-2">
                          {importResult.total_errors} errors encountered
                        </p>
                        <div className="text-sm space-y-1 max-h-32 overflow-y-auto">
                          {importResult.errors.map((error, index) => (
                            <div key={index} className="text-yellow-200">{error}</div>
                          ))}
                        </div>
                      </>
                    )}
                  </div>
                )}

                <div className="flex justify-end gap-4 mt-6">
                  <button
                    onClick={onClose}
                    className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleImport}
                    disabled={isImporting || Object.keys(columnMapping).length === 0}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isImporting ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        Importing...
                      </>
                    ) : (
                      <>
                        <Upload className="w-4 h-4" />
                        Import Data
                      </>
                    )}
                  </button>
                </div>
              </>
            ) : null}
          </>
        )}
      </div>
    </div>
  );
};

export default CSVImportModal; 
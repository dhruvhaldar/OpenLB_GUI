import { useState, useEffect } from 'react';
import { FileText } from 'lucide-react';
import type { Case } from '../types';
import { API_URL } from '../config';

interface ConfigEditorProps {
  selectedCase: Case;
}

const ConfigEditor: React.FC<ConfigEditorProps> = ({ selectedCase }) => {
  const [config, setConfig] = useState('');
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved'>('idle');

  useEffect(() => {
    const fetchConfig = async (casePath: string) => {
      try {
        const res = await fetch(`${API_URL}/config?path=${encodeURIComponent(casePath)}`);
        const data = await res.json();
        setConfig(data.content);
      } catch {
        console.error('Failed to fetch config');
      }
    };
    fetchConfig(selectedCase.path);
  }, [selectedCase]);

  const handleSave = async () => {
    setSaveStatus('saving');
    try {
      await fetch(`${API_URL}/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ case_path: selectedCase.path, content: config })
      });
      setSaveStatus('saved');
      setTimeout(() => setSaveStatus('idle'), 2000);
    } catch {
      console.error('Failed to save config');
      setSaveStatus('idle');
    }
  };

  return (
    <div className="w-1/2 p-4 flex flex-col border-r border-gray-700">
      <div className="flex justify-between items-center mb-2">
        <h3 className="font-semibold text-gray-400 flex items-center gap-2">
          <FileText size={16} /> Configuration
        </h3>
        <button
          onClick={handleSave}
          disabled={saveStatus === 'saving'}
          className="text-sm text-blue-400 hover:text-blue-300 disabled:opacity-50"
        >
          {saveStatus === 'idle' ? 'Save' : saveStatus === 'saving' ? 'Saving...' : 'Saved!'}
        </button>
      </div>
      <textarea
        value={config}
        onChange={e => setConfig(e.target.value)}
        className="flex-1 bg-gray-950 text-gray-300 p-4 rounded font-mono text-sm resize-none focus:outline-none focus:ring-1 focus:ring-blue-500"
      />
    </div>
  );
};

export default ConfigEditor;

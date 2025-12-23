import { useState, useEffect, useCallback } from 'react';
import { Terminal, Play, Settings, FileText, Loader2 } from 'lucide-react';
import Sidebar from './components/Sidebar';
import type { Case } from './types';

const API_URL = 'http://localhost:8080';

function App() {
  const [cases, setCases] = useState<Case[]>([]);
  const [selectedCase, setSelectedCase] = useState<Case | null>(null);
  const [config, setConfig] = useState('');
  const [output, setOutput] = useState('');
  const [status, setStatus] = useState('idle'); // idle, building, running
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');

  useEffect(() => {
    let ignore = false;
    const fetchCases = async () => {
      try {
        const res = await fetch(`${API_URL}/cases`);
        const data = await res.json();
        if (!ignore) {
          setCases(data);
        }
      } catch (e) {
        console.error('Failed to fetch cases', e);
      }
    };
    fetchCases();
    return () => { ignore = true; };
  }, []);


  const fetchConfig = useCallback(async (casePath: string) => {
    try {
      const res = await fetch(`${API_URL}/config?path=${encodeURIComponent(casePath)}`);
      const data = await res.json();
      setConfig(data.content);
    } catch (e) {
      console.error('Failed to fetch config', e);
    }
  }, []);

  const handleSelectCase = useCallback((c: Case) => {
    setSelectedCase(c);
    fetchConfig(c.path);
    setOutput('');
  }, [fetchConfig]);

  const saveConfig = async () => {
    if (!selectedCase) return;
    setSaveStatus('saving');
    try {
      await fetch(`${API_URL}/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ case_path: selectedCase.path, content: config })
      });
      setSaveStatus('saved');
      setTimeout(() => setSaveStatus('idle'), 2000);
    } catch (e) {
      console.error('Failed to save config', e);
      setSaveStatus('error');
      setTimeout(() => setSaveStatus('idle'), 2000);
    }
  };

  const handleBuild = async () => {
    if (!selectedCase) return;
    setStatus('building');
    setOutput('Building...\n');
    try {
      const res = await fetch(`${API_URL}/build`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ case_path: selectedCase.path })
      });
      const data = await res.json();
      setOutput(prev => prev + (data.stdout || '') + (data.stderr || ''));
      if (data.success) setOutput(prev => prev + '\nBuild Successful.\n');
      else setOutput(prev => prev + '\nBuild Failed.\n');
    } catch {
      setOutput(prev => prev + '\nError connecting to server.\n');
    }
    setStatus('idle');
  };

  const handleRun = async () => {
    if (!selectedCase) return;
    setStatus('running');
    setOutput(prev => prev + '\nRunning...\n');
    try {
      const res = await fetch(`${API_URL}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ case_path: selectedCase.path })
      });
      const data = await res.json();
      setOutput(prev => prev + (data.stdout || '') + (data.stderr || ''));
      if (data.success) setOutput(prev => prev + '\nRun Finished.\n');
      else setOutput(prev => prev + '\nRun Failed.\n');
    } catch {
      setOutput(prev => prev + '\nError connecting to server.\n');
    }
    setStatus('idle');
  };

  return (
    <div className="flex h-screen bg-gray-900 text-white font-sans">
      <Sidebar
        cases={cases}
        selectedCaseId={selectedCase?.id}
        onSelectCase={handleSelectCase}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {selectedCase ? (
          <>
            <header className="bg-gray-800 p-4 border-b border-gray-700 flex justify-between items-center">
              <h2 className="text-lg font-medium">{selectedCase.domain} / {selectedCase.name}</h2>
              <div className="flex gap-2">
                <button
                  onClick={handleBuild}
                  disabled={status !== 'idle'}
                  className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  aria-label={status === 'building' ? 'Building project' : 'Build project'}
                >
                  {status === 'building' ? <Loader2 size={16} className="animate-spin" /> : <Settings size={16} />}
                  {status === 'building' ? 'Building...' : 'Build'}
                </button>
                <button
                  onClick={handleRun}
                  disabled={status !== 'idle'}
                  className="px-4 py-2 bg-green-600 hover:bg-green-500 rounded flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  aria-label={status === 'running' ? 'Running project' : 'Run project'}
                >
                  {status === 'running' ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} />}
                  {status === 'running' ? 'Running...' : 'Run'}
                </button>
              </div>
            </header>

            <div className="flex-1 flex overflow-hidden">
              {/* Config Editor */}
              <div className="w-1/2 p-4 flex flex-col border-r border-gray-700">
                <div className="flex justify-between items-center mb-2">
                  <h3 className="font-semibold text-gray-400 flex items-center gap-2">
                    <FileText size={16} /> Configuration
                  </h3>
                  <button
                    onClick={saveConfig}
                    disabled={saveStatus === 'saving'}
                    className={`text-sm ${saveStatus === 'saved' ? 'text-green-400' : 'text-blue-400 hover:text-blue-300'}`}
                    aria-label="Save configuration"
                  >
                    {saveStatus === 'saving' ? 'Saving...' : saveStatus === 'saved' ? 'Saved!' : 'Save'}
                  </button>
                </div>
                <textarea
                  value={config}
                  onChange={e => setConfig(e.target.value)}
                  className="flex-1 bg-gray-950 text-gray-300 p-4 rounded font-mono text-sm resize-none focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>

              {/* Output Terminal */}
              <div className="w-1/2 p-4 flex flex-col bg-black">
                <h3 className="font-semibold text-gray-400 mb-2 flex items-center gap-2">
                  <Terminal size={16} /> Output
                </h3>
                <pre className="flex-1 overflow-auto text-green-400 font-mono text-sm p-2">
                  {output}
                </pre>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-500">
            Select a case to begin
          </div>
        )}
      </div>
    </div>
  );
}

export default App;

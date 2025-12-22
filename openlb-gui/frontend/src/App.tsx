import { useState, useEffect } from 'react';
import { Terminal, Play, Settings, Folder, FileText, Activity, Check, AlertCircle } from 'lucide-react';

interface Case {
  id: string;
  path: string;
  name: string;
  domain: string;
}

const API_URL = 'http://localhost:8080';

function App() {
  const [cases, setCases] = useState<Case[]>([]);
  const [selectedCase, setSelectedCase] = useState<Case | null>(null);
  const [config, setConfig] = useState('');
  const [output, setOutput] = useState('');
  const [status, setStatus] = useState('idle'); // idle, building, running
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');

  useEffect(() => {
    const fetchCases = async () => {
      try {
        const res = await fetch(`${API_URL}/cases`);
        const data = await res.json();
        setCases(data);
      } catch {
        console.error('Failed to fetch cases');
      }
    };
    fetchCases();
  }, []);

  const fetchConfig = async (casePath: string) => {
    try {
      const res = await fetch(`${API_URL}/config?path=${encodeURIComponent(casePath)}`);
      const data = await res.json();
      setConfig(data.content);
    } catch {
      console.error('Failed to fetch config');
    }
  };

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
    } catch {
      console.error('Failed to save config');
      setSaveStatus('error');
      setTimeout(() => setSaveStatus('idle'), 3000);
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
      {/* Sidebar */}
      <div className="w-64 bg-gray-800 p-4 border-r border-gray-700">
        <h1 className="text-xl font-bold mb-6 flex items-center gap-2">
          <Activity className="text-blue-500" /> OpenLB Manager
        </h1>
        <div className="space-y-4">
          <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Cases</h2>
          <div className="space-y-1">
            {cases.map(c => (
              <button
                key={c.id}
                onClick={() => { setSelectedCase(c); fetchConfig(c.path); setOutput(''); }}
                className={`w-full text-left px-3 py-2 rounded flex items-center gap-2 ${selectedCase?.id === c.id ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-gray-700'}`}
              >
                <Folder size={16} />
                <span className="truncate">{c.name}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

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
                  className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded flex items-center gap-2 disabled:opacity-50"
                >
                  <Settings size={16} /> Build
                </button>
                <button
                  onClick={handleRun}
                  disabled={status !== 'idle'}
                  className="px-4 py-2 bg-green-600 hover:bg-green-500 rounded flex items-center gap-2 disabled:opacity-50"
                >
                  <Play size={16} /> Run
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
                  <div className="flex items-center gap-3">
                    <div role="status" aria-live="polite" className="text-sm">
                      {saveStatus === 'saved' && (
                        <span className="text-green-400 flex items-center gap-1 animate-pulse">
                          <Check size={14} /> Saved!
                        </span>
                      )}
                      {saveStatus === 'error' && (
                        <span className="text-red-400 flex items-center gap-1">
                          <AlertCircle size={14} /> Error
                        </span>
                      )}
                    </div>
                    <button
                      onClick={saveConfig}
                      disabled={saveStatus === 'saving'}
                      className="text-sm text-blue-400 hover:text-blue-300 disabled:opacity-50 transition-colors"
                    >
                      {saveStatus === 'saving' ? 'Saving...' : 'Save'}
                    </button>
                  </div>
                </div>
                <textarea
                  value={config}
                  onChange={e => setConfig(e.target.value)}
                  aria-label="Configuration Editor"
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

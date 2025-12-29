import { useState, useEffect, useCallback, useRef } from 'react';
import { Terminal, Play, Settings, Loader2, Copy, Check, FolderOpen } from 'lucide-react';
import Sidebar from './components/Sidebar';
import ConfigEditor from './components/ConfigEditor';
import LogViewer from './components/LogViewer';
import type { Case } from './types';

const API_URL = 'http://localhost:8080';

function App() {
  const [cases, setCases] = useState<Case[]>([]);
  const [selectedCase, setSelectedCase] = useState<Case | null>(null);
  const [config, setConfig] = useState<string | null>(null);
  const [output, setOutput] = useState('');
  const [status, setStatus] = useState('idle'); // idle, building, running
  const [copyStatus, setCopyStatus] = useState<'idle' | 'copied'>('idle');

  // Optimization: Cache config content to avoid unnecessary network requests
  const configCache = useRef<Record<string, string>>({});

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
    // Optimization: Check cache first
    if (configCache.current[casePath]) {
      setConfig(configCache.current[casePath]);
      return;
    }

    try {
      const res = await fetch(`${API_URL}/config?path=${encodeURIComponent(casePath)}`);
      const data = await res.json();
      setConfig(data.content);
      // Optimization: Update cache
      configCache.current[casePath] = data.content;
    } catch (e) {
      console.error('Failed to fetch config', e);
    }
  }, []);

  const handleSelectCase = useCallback((c: Case) => {
    setSelectedCase(c);
    // Optimization: If cached, we don't need to reset to null and flash loader
    // fetchConfig will handle setting the state.
    if (!configCache.current[c.path]) {
      setConfig(null); // Reset config to trigger loading state only if not cached
    }
    fetchConfig(c.path);
    setOutput('');
  }, [fetchConfig]);

  const handleSaveConfig = useCallback(async (content: string) => {
    if (!selectedCase) return;
    try {
      const res = await fetch(`${API_URL}/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ case_path: selectedCase.path, content })
      });
      if (!res.ok) throw new Error('Failed to save');
      // Optimization: Update cache on save
      configCache.current[selectedCase.path] = content;
    } catch (e) {
      console.error('Failed to save config', e);
      throw e;
    }
  }, [selectedCase]);

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

  const handleCopyOutput = async () => {
    try {
      await navigator.clipboard.writeText(output);
      setCopyStatus('copied');
      setTimeout(() => setCopyStatus('idle'), 2000);
    } catch (err) {
      console.error('Failed to copy', err);
    }
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
                  className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded flex items-center gap-2 disabled:opacity-50"
                >
                  {status === 'building' ? (
                    <Loader2 className="animate-spin" size={16} />
                  ) : (
                    <Settings size={16} />
                  )}
                  {status === 'building' ? 'Building...' : 'Build'}
                </button>
                <button
                  onClick={handleRun}
                  disabled={status !== 'idle'}
                  className="px-4 py-2 bg-green-600 hover:bg-green-500 rounded flex items-center gap-2 disabled:opacity-50"
                >
                  {status === 'running' ? (
                    <Loader2 className="animate-spin" size={16} />
                  ) : (
                    <Play size={16} />
                  )}
                  {status === 'running' ? 'Running...' : 'Run'}
                </button>
              </div>
            </header>

            <div className="flex-1 flex overflow-hidden">
              {config !== null ? (
                <ConfigEditor
                  initialContent={config}
                  onSave={handleSaveConfig}
                  caseId={selectedCase.id}
                  className="w-1/2 p-4 border-r border-gray-700"
                />
              ) : (
                <div className="w-1/2 p-4 border-r border-gray-700 flex items-center justify-center text-gray-500">
                  <Loader2 className="animate-spin mr-2" /> Loading config...
                </div>
              )}

              {/* Output Terminal */}
              <div className="w-1/2 p-4 flex flex-col bg-black">
                <div className="flex justify-between items-center mb-2">
                  <h3 className="font-semibold text-gray-400 flex items-center gap-2">
                    <Terminal size={16} /> Output
                  </h3>
                  <button
                    onClick={handleCopyOutput}
                    className="text-gray-400 hover:text-white transition-colors"
                    aria-label="Copy output"
                    title="Copy to clipboard"
                  >
                    {copyStatus === 'copied' ? <Check size={16} /> : <Copy size={16} />}
                  </button>
                </div>
                <LogViewer output={output} />
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-gray-500 gap-4">
            <div className="p-4 bg-gray-800 rounded-full">
              <FolderOpen size={48} className="text-gray-600" aria-hidden="true" />
            </div>
            <div className="text-center">
              <h3 className="text-lg font-medium text-gray-300">No Case Selected</h3>
              <p className="text-sm mt-1 text-gray-400">Select a simulation case from the sidebar to begin.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;

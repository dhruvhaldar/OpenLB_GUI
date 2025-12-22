import { useState, useEffect } from 'react';
import { Terminal, Play, Settings } from 'lucide-react';
import Sidebar from './components/Sidebar';
import ConfigEditor from './components/ConfigEditor';
import { API_URL } from './config';
import type { Case } from './types';

function App() {
  const [cases, setCases] = useState<Case[]>([]);
  const [selectedCase, setSelectedCase] = useState<Case | null>(null);
  const [output, setOutput] = useState('');
  const [status, setStatus] = useState('idle'); // idle, building, running

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

  const handleSelectCase = (c: Case) => {
    setSelectedCase(c);
    setOutput('');
  };

  return (
    <div className="flex h-screen bg-gray-900 text-white font-sans">
      <Sidebar
        cases={cases}
        selectedCase={selectedCase}
        onSelect={handleSelectCase}
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
              <ConfigEditor selectedCase={selectedCase} />

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

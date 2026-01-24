import { useState, useEffect, useCallback, useRef } from 'react';
import { Terminal, Play, Settings, Loader2, Copy, Check, FolderOpen, Trash2, Download, CopyPlus, Eraser, WrapText, RefreshCw, FolderPlus } from 'lucide-react';
import Sidebar from './components/Sidebar';
import ConfigEditor from './components/ConfigEditor';
import LogViewer from './components/LogViewer';
import DuplicateCaseModal from './components/DuplicateCaseModal';
import DeleteCaseModal from './components/DeleteCaseModal';
import type { Case } from './types';

const API_URL = 'http://localhost:8080';
// Optimization: Limit log history to prevent memory exhaustion and DOM rendering lag
const MAX_LOG_LENGTH = 100000;

function App() {
  const [cases, setCases] = useState<Case[]>([]);
  const [isLoadingCases, setIsLoadingCases] = useState(true);
  const [selectedCase, setSelectedCase] = useState<Case | null>(null);
  const [config, setConfig] = useState<string | null>(null);
  const [output, setOutput] = useState('');
  const [status, setStatus] = useState('idle'); // idle, building, running
  const [copyStatus, setCopyStatus] = useState<'idle' | 'copied'>('idle');
  const [headerCopyStatus, setHeaderCopyStatus] = useState<'idle' | 'copied'>('idle');
  const [downloadStatus, setDownloadStatus] = useState<'idle' | 'downloaded'>('idle');
  const [isLogWrapped, setIsLogWrapped] = useState(false);
  const [isDuplicating, setIsDuplicating] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isDuplicateModalOpen, setIsDuplicateModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [duplicateName, setDuplicateName] = useState('');
  const [duplicateError, setDuplicateError] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  // Optimization: Cache config content to avoid unnecessary network requests
  // Use a Map to implement LRU (Least Recently Used) eviction policy.
  // Limit to 20 items to prevent memory bloat from large config files.
  const configCache = useRef<Map<string, string>>(new Map());

  // Optimization: Helper to append logs and enforce size limit
  // Optimized to avoid allocating intermediate string larger than MAX_LOG_LENGTH
  const appendLog = useCallback((currentLog: string, newLog: string) => {
    // If new log is larger than limit, we only need the end of it
    if (newLog.length >= MAX_LOG_LENGTH) {
      return newLog.slice(newLog.length - MAX_LOG_LENGTH);
    }

    const totalLength = currentLog.length + newLog.length;
    // If total length fits, just concatenate
    if (totalLength <= MAX_LOG_LENGTH) {
      return currentLog + newLog;
    }

    // We need to trim from the beginning of currentLog to make room for newLog
    // Calculate how many characters to keep from currentLog
    const keepLength = MAX_LOG_LENGTH - newLog.length;
    return currentLog.slice(currentLog.length - keepLength) + newLog;
  }, []);

  // Optimization: Deep comparison helper for cases
  // Prevents unnecessary React.memo re-calculations in Sidebar and layout thrashing
  // when the fetched case list is identical to the current state.
  // UPDATE: Replaced JSON.stringify with a Map-based comparison.
  // This provides two benefits:
  // 1. Performance: Avoids O(N) string serialization and allocation.
  // 2. Stability: Ignores order differences. If the backend returns the same cases
  //    in a different order (common with os.scandir), we treat it as "equal"
  //    and preserve the current frontend order, preventing UI jumps.
  const areCasesEqual = useCallback((prev: Case[], next: Case[]) => {
    if (prev === next) return true;
    if (prev.length !== next.length) return false;

    // Optimization: Create a Map of the previous cases for O(1) lookup
    const prevMap = new Map(prev.map(c => [c.id, c]));

    for (const nextItem of next) {
      const prevItem = prevMap.get(nextItem.id);
      if (!prevItem) return false;

      // Check for content changes
      if (
        prevItem.name !== nextItem.name ||
        prevItem.domain !== nextItem.domain ||
        prevItem.path !== nextItem.path
      ) {
        return false;
      }
    }
    return true;
  }, []);

  const refreshCases = useCallback(async () => {
    setIsLoadingCases(true);
    try {
      const res = await fetch(`${API_URL}/cases`);
      if (!res.ok) throw new Error('Failed to fetch cases');
      const data = await res.json();

      // Optimization: Avoid state update if data is identical
      setCases(prev => {
        if (areCasesEqual(prev, data)) return prev;
        return data;
      });
    } catch (e) {
      console.error('Failed to fetch cases', e);
    } finally {
      setIsLoadingCases(false);
    }
  }, [areCasesEqual]);

  useEffect(() => {
    refreshCases();
  }, [refreshCases]);

  const fetchConfig = useCallback(async (casePath: string) => {
    // Optimization: Check cache first (LRU)
    if (configCache.current.has(casePath)) {
      const content = configCache.current.get(casePath)!;
      // LRU: Refresh entry by re-inserting
      configCache.current.delete(casePath);
      configCache.current.set(casePath, content);
      setConfig(content);
      return;
    }

    try {
      const res = await fetch(`${API_URL}/config?path=${encodeURIComponent(casePath)}`);
      const data = await res.json();
      const content = data.content;
      setConfig(content);

      // Optimization: Update cache with LRU eviction
      if (configCache.current.size >= 20) {
        const firstKey = configCache.current.keys().next().value;
        if (firstKey) configCache.current.delete(firstKey);
      }
      configCache.current.set(casePath, content);
    } catch (e) {
      console.error('Failed to fetch config', e);
    }
  }, []);

  const handleSelectCase = useCallback((c: Case) => {
    setSelectedCase(c);
    // Optimization: If cached, we don't need to reset to null and flash loader
    // fetchConfig will handle setting the state.
    if (!configCache.current.has(c.path)) {
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
      // LRU: Refresh/Update
      if (configCache.current.has(selectedCase.path)) {
        configCache.current.delete(selectedCase.path);
      } else if (configCache.current.size >= 20) {
        const firstKey = configCache.current.keys().next().value;
        if (firstKey) configCache.current.delete(firstKey);
      }
      configCache.current.set(selectedCase.path, content);
    } catch (e) {
      console.error('Failed to save config', e);
      throw e;
    }
  }, [selectedCase]);

  const handleBuild = useCallback(async () => {
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
      // Optimization: Batch output updates to minimize re-renders and string copying overhead
      // Prevents O(N) copy of the entire output history for the final status update
      let newOutput = (data.stdout || '') + (data.stderr || '');
      if (data.success) newOutput += '\nBuild Successful.\n';
      else newOutput += '\nBuild Failed.\n';
      setOutput(prev => appendLog(prev, newOutput));
    } catch {
      setOutput(prev => appendLog(prev, '\nError connecting to server.\n'));
    }
    setStatus('idle');
  }, [selectedCase, appendLog]);

  const handleRun = useCallback(async () => {
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
      // Optimization: Batch output updates to minimize re-renders and string copying overhead
      // Prevents O(N) copy of the entire output history for the final status update
      let newOutput = (data.stdout || '') + (data.stderr || '');
      if (data.success) newOutput += '\nRun Finished.\n';
      else newOutput += '\nRun Failed.\n';
      setOutput(prev => appendLog(prev, newOutput));
    } catch {
      setOutput(prev => appendLog(prev, '\nError connecting to server.\n'));
    }
    setStatus('idle');
  }, [selectedCase, appendLog]);

  // Global Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if no case is selected or busy
      if (!selectedCase || status !== 'idle') return;

      if (e.ctrlKey || e.metaKey) {
        if (e.key === 'b' || e.key === 'B') {
          e.preventDefault();
          handleBuild();
        } else if (e.key === 'Enter') {
          e.preventDefault();
          handleRun();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedCase, status, handleBuild, handleRun]);

  const handleCopyOutput = async () => {
    try {
      await navigator.clipboard.writeText(output);
      setCopyStatus('copied');
      setTimeout(() => setCopyStatus('idle'), 2000);
    } catch (err) {
      console.error('Failed to copy', err);
    }
  };

  const handleCopyPath = async () => {
    if (!selectedCase) return;
    try {
      await navigator.clipboard.writeText(selectedCase.path);
      setHeaderCopyStatus('copied');
      setTimeout(() => setHeaderCopyStatus('idle'), 2000);
    } catch (err) {
      console.error('Failed to copy path', err);
    }
  };

  const handleClearOutput = () => {
    setOutput('');
  };

  const handleDownloadOutput = () => {
    const blob = new Blob([output], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'output.txt';
    a.click();
    URL.revokeObjectURL(url);
    setDownloadStatus('downloaded');
    setTimeout(() => setDownloadStatus('idle'), 2000);
  };

  const handleDuplicate = () => {
    if (!selectedCase) return;
    setDuplicateName(`${selectedCase.name}_copy`);
    setDuplicateError(null);
    setIsDuplicateModalOpen(true);
  };

  const handleDuplicateSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCase || !duplicateName) return;

    setIsDuplicating(true);
    setDuplicateError(null);
    try {
      const res = await fetch(`${API_URL}/cases/duplicate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source_path: selectedCase.path, new_name: duplicateName })
      });
      if (!res.ok) {
        const err = await res.json();
        setDuplicateError(err.detail || 'Failed to duplicate');
        return;
      }
      const data = await res.json();
      // Refresh cases
      const casesRes = await fetch(`${API_URL}/cases`);
      const casesData = await casesRes.json();

      // Optimization: Avoid state update if data is identical (though unlikely for duplicate)
      setCases(prev => {
        if (areCasesEqual(prev, casesData)) return prev;
        return casesData;
      });

      // Select the new case
      const newCase = casesData.find((c: Case) => c.path === data.new_path);
      if (newCase) {
        handleSelectCase(newCase);
      }
      setIsDuplicateModalOpen(false);
    } catch (e) {
      console.error('Duplicate failed', e);
      setDuplicateError('Failed to duplicate case');
    } finally {
      setIsDuplicating(false);
    }
  }, [selectedCase, duplicateName, handleSelectCase, areCasesEqual]);

  const handleDeleteClick = useCallback(() => {
    if (!selectedCase) return;
    setDeleteError(null);
    setIsDeleteModalOpen(true);
  }, [selectedCase]);

  const confirmDelete = useCallback(async () => {
    if (!selectedCase) return;

    setIsDeleting(true);
    setDeleteError(null);
    try {
      const res = await fetch(`${API_URL}/cases?case_path=${encodeURIComponent(selectedCase.path)}`, {
        method: 'DELETE'
      });
      if (!res.ok) {
        const err = await res.json();
        setDeleteError(err.detail || 'Failed to delete');
        return;
      }
      // Refresh cases
      const casesRes = await fetch(`${API_URL}/cases`);
      const casesData = await casesRes.json();

      // Optimization: Avoid state update if data is identical
      setCases(prev => {
        if (areCasesEqual(prev, casesData)) return prev;
        return casesData;
      });

      setSelectedCase(null);
      setConfig(null);
      setOutput('');
      setIsDeleteModalOpen(false);
    } catch (e) {
      console.error('Delete failed', e);
      setDeleteError('Failed to delete case');
    } finally {
      setIsDeleting(false);
    }
  }, [selectedCase, areCasesEqual]);

  const handleCloseDuplicate = useCallback(() => {
    setIsDuplicateModalOpen(false);
  }, []);

  const handleCloseDelete = useCallback(() => {
    setIsDeleteModalOpen(false);
  }, []);

  return (
    <div className="flex h-screen bg-gray-900 text-white font-sans">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:px-4 focus:py-2 focus:bg-blue-600 focus:text-white focus:font-medium focus:shadow-lg focus:rounded-md focus:outline-none focus:ring-2 focus:ring-white"
      >
        Skip to main content
      </a>
      <Sidebar
        cases={cases}
        selectedCaseId={selectedCase?.id}
        onSelectCase={handleSelectCase}
        isLoading={isLoadingCases}
        onRefresh={refreshCases}
      />

      {/* Main Content */}
      <div id="main-content" tabIndex={-1} className="flex-1 flex flex-col overflow-hidden focus:outline-none">
        {selectedCase ? (
          <>
            <header className="bg-gray-800 p-4 border-b border-gray-700 flex justify-between items-center">
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2 group">
                  <h2 className="text-lg font-medium">{selectedCase.domain} / {selectedCase.name}</h2>
                  <button
                    onClick={handleCopyPath}
                    className={`opacity-0 group-hover:opacity-100 focus:opacity-100 p-1 rounded transition-all focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none ${
                      headerCopyStatus === 'copied' ? 'text-green-400' : 'text-gray-500 hover:text-white'
                    }`}
                    aria-label={headerCopyStatus === 'copied' ? "Copied path" : "Copy case path"}
                    title={headerCopyStatus === 'copied' ? "Copied!" : "Copy case path"}
                  >
                    {headerCopyStatus === 'copied' ? <Check size={14} /> : <Copy size={14} />}
                  </button>
                </div>
                <div className="flex gap-1">
                  <button
                    onClick={handleDuplicate}
                    disabled={isDuplicating}
                    className="p-1.5 text-gray-400 hover:text-white hover:bg-gray-700 rounded transition-colors focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none disabled:opacity-50"
                    title={isDuplicating ? "Duplicating..." : "Duplicate Case"}
                    aria-label={isDuplicating ? "Duplicating case..." : "Duplicate Case"}
                  >
                    {isDuplicating ? <Loader2 size={18} className="animate-spin" /> : <CopyPlus size={18} />}
                  </button>
                  <button
                    onClick={handleDeleteClick}
                    disabled={isDeleting}
                    className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-gray-700 rounded transition-colors focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none disabled:opacity-50"
                    title={isDeleting ? "Deleting..." : "Delete Case"}
                    aria-label={isDeleting ? "Deleting case..." : "Delete Case"}
                  >
                    {isDeleting ? <Loader2 size={18} className="animate-spin" /> : <Trash2 size={18} />}
                  </button>
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={handleBuild}
                  disabled={status !== 'idle'}
                  title={status === 'building' ? 'Building simulation...' : status === 'running' ? 'Cannot build while simulation is running' : 'Build simulation (Ctrl+B)'}
                  className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded flex items-center gap-2 disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none"
                >
                  {status === 'building' ? (
                    <Loader2 className="animate-spin" size={16} />
                  ) : (
                    <Settings size={16} aria-hidden="true" />
                  )}
                  {status === 'building' ? 'Building...' : (
                    <>
                      Build
                      <kbd className="hidden md:inline-block px-1.5 py-0.5 text-[10px] font-mono bg-black/20 rounded opacity-80">Ctrl+B</kbd>
                    </>
                  )}
                </button>
                <button
                  onClick={handleRun}
                  disabled={status !== 'idle'}
                  title={status === 'running' ? 'Running simulation...' : status === 'building' ? 'Cannot run while simulation is building' : 'Run simulation (Ctrl+Enter)'}
                  className="px-4 py-2 bg-green-600 hover:bg-green-500 rounded flex items-center gap-2 disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none"
                >
                  {status === 'running' ? (
                    <Loader2 className="animate-spin" size={16} />
                  ) : (
                    <Play size={16} aria-hidden="true" />
                  )}
                  {status === 'running' ? 'Running...' : (
                    <>
                      Run
                      <kbd className="hidden md:inline-block px-1.5 py-0.5 text-[10px] font-mono bg-black/20 rounded opacity-80">Ctrl+Enter</kbd>
                    </>
                  )}
                </button>
              </div>
            </header>

            <div className="flex-1 flex overflow-hidden">
              <ConfigEditor
                key={selectedCase.id}
                initialContent={config || ''}
                isLoading={config === null}
                onSave={handleSaveConfig}
                className="w-1/2 p-4 border-r border-gray-700"
              />

              {/* Output Terminal */}
              <div className="w-1/2 p-4 flex flex-col bg-black">
                <div className="flex justify-between items-center mb-2">
                  <h3 className="font-semibold text-gray-400 flex items-center gap-2">
                    <Terminal size={16} /> Output
                  </h3>
                  <div className="flex gap-2">
                    <button
                        onClick={() => setIsLogWrapped(!isLogWrapped)}
                        disabled={!output}
                        className={`p-1 rounded transition-colors focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none disabled:opacity-50 disabled:cursor-not-allowed ${
                            isLogWrapped ? 'text-blue-400 hover:text-blue-300 bg-gray-800' : 'text-gray-400 hover:text-white'
                        }`}
                        aria-label={!output ? "No output to wrap" : isLogWrapped ? "Disable word wrap" : "Enable word wrap"}
                        aria-pressed={isLogWrapped}
                        title={!output ? "No output to wrap" : isLogWrapped ? "Disable word wrap" : "Enable word wrap"}
                    >
                        <WrapText size={16} />
                    </button>
                    <button
                        onClick={handleClearOutput}
                        disabled={!output}
                        className="p-1 rounded text-gray-400 hover:text-white transition-colors focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none disabled:opacity-50 disabled:cursor-not-allowed"
                        aria-label={!output ? "No output to clear" : "Clear output"}
                        title={!output ? "No output to clear" : "Clear output"}
                    >
                        <Eraser size={16} />
                    </button>
                    <button
                        onClick={handleDownloadOutput}
                        disabled={!output}
                        className={`p-1 rounded transition-colors focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none disabled:opacity-50 disabled:cursor-not-allowed ${
                          downloadStatus === 'downloaded' ? 'text-green-400 hover:text-green-300' : 'text-gray-400 hover:text-white'
                        }`}
                        aria-label={!output ? "No output to download" : downloadStatus === 'downloaded' ? "Download complete" : "Download output"}
                        title={!output ? "No output to download" : downloadStatus === 'downloaded' ? "Downloaded!" : "Download output"}
                    >
                        {downloadStatus === 'downloaded' ? <Check size={16} /> : <Download size={16} />}
                    </button>
                    <button
                        onClick={handleCopyOutput}
                        disabled={!output}
                        className={`p-1 rounded transition-colors focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none disabled:opacity-50 disabled:cursor-not-allowed ${
                          copyStatus === 'copied' ? 'text-green-400 hover:text-green-300' : 'text-gray-400 hover:text-white'
                        }`}
                        aria-label={!output ? "No output to copy" : copyStatus === 'copied' ? "Copied successfully" : "Copy output"}
                        title={!output ? "No output to copy" : copyStatus === 'copied' ? "Copied!" : "Copy to clipboard"}
                    >
                        {copyStatus === 'copied' ? <Check size={16} /> : <Copy size={16} />}
                    </button>
                  </div>
                </div>
                <LogViewer
                  output={output}
                  isWrapped={isLogWrapped}
                  onBuild={handleBuild}
                  onRun={handleRun}
                />
              </div>
            </div>
          </>
        ) : !isLoadingCases && cases.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center text-gray-500 gap-4 p-8">
            <div className="p-4 bg-gray-800 rounded-full ring-1 ring-gray-700">
              <FolderPlus size={48} className="text-blue-500" aria-hidden="true" />
            </div>
            <div className="text-center max-w-md">
              <h3 className="text-lg font-medium text-gray-200">No Cases Found</h3>
              <p className="text-sm mt-2 text-gray-400 leading-relaxed">
                Your case library is empty. To get started, add your OpenLB simulation directories to the <code className="bg-gray-800 px-1.5 py-0.5 rounded text-gray-300 font-mono text-xs border border-gray-700">my_cases/</code> folder.
              </p>
              <button
                onClick={refreshCases}
                className="mt-6 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-md shadow-lg shadow-blue-900/20 transition-all flex items-center gap-2 mx-auto focus-visible:ring-2 focus-visible:ring-blue-400 focus-visible:outline-none"
              >
                <RefreshCw size={16} />
                Refresh Cases
              </button>
            </div>
          </div>
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

      <DuplicateCaseModal
        isOpen={isDuplicateModalOpen}
        onClose={handleCloseDuplicate}
        duplicateName={duplicateName}
        onNameChange={setDuplicateName}
        onSubmit={handleDuplicateSubmit}
        isDuplicating={isDuplicating}
        error={duplicateError}
      />

      <DeleteCaseModal
        isOpen={isDeleteModalOpen}
        onClose={handleCloseDelete}
        caseName={selectedCase?.name}
        onConfirm={confirmDelete}
        isDeleting={isDeleting}
        error={deleteError}
      />
    </div>
  );
}

export default App;

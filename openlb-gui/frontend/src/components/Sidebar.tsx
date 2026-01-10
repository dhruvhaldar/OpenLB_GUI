import React, { memo, useState, useMemo, useRef } from 'react';
import { Folder, Activity, RefreshCw, Search, X } from 'lucide-react';
import type { Case } from '../types';

interface SidebarItemProps {
  item: Case;
  isSelected: boolean;
  onSelect: (c: Case) => void;
}

const SidebarItem = memo(({ item, isSelected, onSelect }: SidebarItemProps) => {
  return (
    <button
      onClick={() => onSelect(item)}
      title={item.name}
      aria-current={isSelected ? 'true' : undefined}
      className={`w-full text-left px-3 py-2 rounded flex items-center gap-2 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none ${isSelected ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-gray-700'}`}
    >
      <Folder size={16} aria-hidden="true" />
      <span className="truncate">{item.name}</span>
    </button>
  );
}, (prev, next) => {
  // Optimization: Custom comparison to prevent re-renders when parent 'cases' list is refreshed
  // but this individual item hasn't changed. Standard React.memo (shallow compare) fails here
  // because the 'item' object reference changes on every fetch.
  return (
    prev.isSelected === next.isSelected &&
    prev.item.id === next.item.id &&
    prev.item.name === next.item.name &&
    prev.onSelect === next.onSelect
  );
});

interface SidebarProps {
  cases: Case[];
  selectedCaseId: string | undefined;
  onSelectCase: (c: Case) => void;
  isLoading?: boolean;
  onRefresh?: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ cases, selectedCaseId, onSelectCase, isLoading, onRefresh }) => {
  const [filter, setFilter] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const filteredCases = useMemo(() => {
    if (!filter) return cases;
    const lowerFilter = filter.toLowerCase();
    return cases.filter(c =>
      c.name.toLowerCase().includes(lowerFilter) ||
      c.domain.toLowerCase().includes(lowerFilter)
    );
  }, [cases, filter]);

  const handleClearFilter = () => {
    setFilter('');
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      handleClearFilter();
    }
  };

  return (
    <aside className="w-64 bg-gray-800 border-r border-gray-700 flex flex-col">
      <div className="p-4 flex items-center justify-between">
        <h1 className="text-xl font-bold flex items-center gap-2">
          <Activity className="text-blue-500" aria-hidden="true" /> OpenLB Manager
        </h1>
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-full transition-colors focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none"
            aria-label={isLoading ? "Refreshing cases..." : "Refresh cases"}
            title={isLoading ? "Refreshing..." : "Refresh cases"}
            disabled={isLoading}
          >
            <RefreshCw
              size={18}
              className={isLoading ? 'animate-spin' : ''}
              aria-hidden="true"
            />
          </button>
        )}
      </div>
      <nav className="flex-1 overflow-y-auto px-4 pb-4" aria-label="Simulation Cases">
        <div className="space-y-4">
          <div className="relative">
            <Search className="absolute left-2 top-2.5 text-gray-500" size={14} />
            <input
              ref={inputRef}
              type="text"
              placeholder="Filter cases..."
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              onKeyDown={handleKeyDown}
              className="w-full bg-gray-900 text-xs text-gray-300 rounded border border-gray-700 pl-8 pr-8 py-1.5 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 placeholder:text-gray-600"
              aria-label="Filter cases"
            />
            {filter && (
              <button
                onClick={handleClearFilter}
                className="absolute right-2 top-2.5 text-gray-500 hover:text-white focus:outline-none focus:text-white"
                aria-label="Clear filter"
                title="Clear filter (Esc)"
              >
                <X size={14} />
              </button>
            )}
          </div>
          <div>
            <h2 id="cases-heading" className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Cases</h2>
            <ul className="space-y-1" aria-labelledby="cases-heading" aria-busy={isLoading}>
              {isLoading ? (
                <>
                  <li className="animate-pulse flex items-center gap-2 px-3 py-2">
                    <div className="w-4 h-4 bg-gray-700 rounded" />
                    <div className="h-4 bg-gray-700 rounded w-32" />
                  </li>
                  <li className="animate-pulse flex items-center gap-2 px-3 py-2">
                    <div className="w-4 h-4 bg-gray-700 rounded" />
                    <div className="h-4 bg-gray-700 rounded w-24" />
                  </li>
                  <li className="animate-pulse flex items-center gap-2 px-3 py-2">
                    <div className="w-4 h-4 bg-gray-700 rounded" />
                    <div className="h-4 bg-gray-700 rounded w-28" />
                  </li>
                </>
              ) : filteredCases.length > 0 ? (
                filteredCases.map(c => (
                  <li key={c.id}>
                    <SidebarItem
                      item={c}
                      isSelected={selectedCaseId === c.id}
                      onSelect={onSelectCase}
                    />
                  </li>
                ))
              ) : (
                <li className="text-gray-500 text-sm px-3 py-2 italic text-center">
                  {cases.length === 0 ? 'No cases found' : 'No matching cases'}
                </li>
              )}
            </ul>
          </div>
        </div>
      </nav>
    </aside>
  );
};

export default memo(Sidebar);

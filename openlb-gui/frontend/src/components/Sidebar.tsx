import React, { memo, useState, useMemo, useRef, useDeferredValue, useEffect } from 'react';
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

interface SidebarListItemsProps {
  cases: Case[];
  selectedId: string | undefined;
  onSelect: (c: Case) => void;
}

// Optimization: Isolate the list rendering to prevent reconciliation of the entire list
// when parent Sidebar re-renders (e.g. during typing in the filter input).
// Even though SidebarItem is memoized, re-rendering the mapping loop creates N new Element objects
// and triggers N prop comparisons. By memoizing the list container, we skip this entirely
// when 'cases' (filtered list) hasn't changed.
const SidebarListItems = memo(({ cases, selectedId, onSelect }: SidebarListItemsProps) => {
  return (
    <>
      {cases.map(c => (
        <li key={c.id} className="cv-auto">
          <SidebarItem
            item={c}
            isSelected={selectedId === c.id}
            onSelect={onSelect}
          />
        </li>
      ))}
    </>
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
  // Optimization: Defer the filter value to keep the input responsive
  // This allows the UI to update the input immediately while the list filtering (which could be expensive)
  // happens in the background/next render, preventing input lag on large lists.
  const deferredFilter = useDeferredValue(filter);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);

  // Optimization: Pre-compute search strings to avoid repeated .toLowerCase() calls during filtering
  // This reduces the filtering complexity from O(N * M) to O(N) where M is the string length.
  // We compute this once when 'cases' changes, rather than on every keystroke.
  const searchIndex = useMemo(() => {
    return cases.map(c =>
      `${c.name} ${c.domain}`.toLowerCase()
    );
  }, [cases]);

  const filteredCases = useMemo(() => {
    if (!deferredFilter) return cases;
    const lowerFilter = deferredFilter.toLowerCase();

    // Optimization: Use the pre-computed index for fast lookup
    // accessing searchIndex[i] is O(1)
    return cases.filter((_, i) =>
      searchIndex[i].includes(lowerFilter)
    );
  }, [cases, deferredFilter, searchIndex]);

  const handleClearFilter = () => {
    setFilter('');
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      handleClearFilter();
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      // UX: Allow seamless navigation from search to results
      const firstItem = listRef.current?.querySelector('button');
      if (firstItem) {
        (firstItem as HTMLElement).focus();
      }
    } else if (e.key === 'Enter') {
      e.preventDefault();
      // UX: "Power User" shortcut - automatically select the top result
      if (filteredCases.length > 0) {
        onSelectCase(filteredCases[0]);
        inputRef.current?.blur();
      }
    }
  };

  useEffect(() => {
    const handleGlobalKeyDown = (e: KeyboardEvent) => {
      // Focus search on '/'
      if (e.key === '/' && !e.ctrlKey && !e.metaKey && !e.altKey) {
        // Don't trigger if user is typing in an input/textarea
        const target = e.target as HTMLElement;
        if (['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName)) {
          return;
        }
        e.preventDefault();
        inputRef.current?.focus();
      }
    };

    window.addEventListener('keydown', handleGlobalKeyDown);
    return () => window.removeEventListener('keydown', handleGlobalKeyDown);
  }, []);

  const handleListKeyDown = (e: React.KeyboardEvent) => {
    if (!['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(e.key)) return;

    e.preventDefault();
    const buttons = Array.from(listRef.current?.querySelectorAll('button') || []) as HTMLButtonElement[];
    const currentIndex = buttons.indexOf(document.activeElement as HTMLButtonElement);

    // Fallback if focus is somehow lost but inside list area
    if (currentIndex === -1 && buttons.length > 0) {
      buttons[0].focus();
      return;
    }

    let nextIndex = currentIndex;
    if (e.key === 'ArrowDown') {
      nextIndex = Math.min(currentIndex + 1, buttons.length - 1);
    } else if (e.key === 'ArrowUp') {
      nextIndex = Math.max(currentIndex - 1, 0);
    } else if (e.key === 'Home') {
      nextIndex = 0;
    } else if (e.key === 'End') {
      nextIndex = buttons.length - 1;
    }

    if (nextIndex !== currentIndex) {
      buttons[nextIndex]?.focus();
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
            <Search className="absolute left-2 top-2.5 text-gray-500" size={14} aria-hidden="true" />
            <input
              ref={inputRef}
              type="text"
              placeholder="Filter cases... (Press /)"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              onKeyDown={handleKeyDown}
              className="w-full bg-gray-900 text-xs text-gray-300 rounded border border-gray-700 pl-8 pr-8 py-1.5 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 placeholder:text-gray-600"
              aria-label="Filter cases"
            />
            {filter && (
              <button
                onClick={handleClearFilter}
                className="absolute right-2 top-2.5 text-gray-500 hover:text-white focus:outline-none focus:text-white rounded-full focus-visible:ring-2 focus-visible:ring-blue-500"
                aria-label="Clear filter"
                title="Clear filter (Esc)"
              >
                <X size={14} />
              </button>
            )}
          </div>
          <div>
            <h2 id="cases-heading" className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Cases</h2>
            <ul
              ref={listRef}
              className="space-y-1"
              aria-labelledby="cases-heading"
              aria-busy={isLoading}
              onKeyDown={handleListKeyDown}
            >
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
                <SidebarListItems
                  cases={filteredCases}
                  selectedId={selectedCaseId}
                  onSelect={onSelectCase}
                />
              ) : (
                <li className="text-gray-500 text-sm px-3 py-2 text-center flex flex-col items-center gap-2">
                  <span className="italic">{cases.length === 0 ? 'No cases found' : 'No matching cases'}</span>
                  {cases.length > 0 && (
                    <button
                      onClick={handleClearFilter}
                      className="text-xs text-blue-400 hover:text-blue-300 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 rounded px-2 py-1"
                    >
                      Clear filter
                    </button>
                  )}
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

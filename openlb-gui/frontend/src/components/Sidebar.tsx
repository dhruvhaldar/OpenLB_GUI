import React, { memo, useState, useMemo, useRef, useDeferredValue, useEffect } from 'react';
import { Folder, Activity, RefreshCw, Search, X } from 'lucide-react';
import type { Case } from '../types';

interface SidebarItemProps {
  item: Case;
  isSelected: boolean;
  onSelect: (c: Case) => void;
  searchTerm?: string;
}

const HighlightMatch = ({ text, match }: { text: string; match?: string }) => {
  if (!match) return <span className="truncate">{text}</span>;

  // Escape special characters to prevent regex crashes
  const escapedMatch = match.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const parts = text.split(new RegExp(`(${escapedMatch})`, 'gi'));
  return (
    <span className="truncate">
      {parts.map((part, i) =>
        part.toLowerCase() === match.toLowerCase() ? (
          <span
            key={i}
            className="font-bold text-blue-400 group-aria-[current=true]:text-white group-aria-[current=true]:underline"
          >
            {part}
          </span>
        ) : (
          <span key={i}>{part}</span>
        )
      )}
    </span>
  );
};

const SidebarItem = memo(({ item, isSelected, onSelect, searchTerm }: SidebarItemProps) => {
  return (
    <button
      onClick={() => onSelect(item)}
      title={item.name}
      aria-current={isSelected ? 'true' : undefined}
      className={`group w-full text-left px-3 py-2 rounded flex items-center gap-2 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none ${isSelected ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-gray-700'}`}
    >
      <Folder size={16} aria-hidden="true" />
      <HighlightMatch text={item.name} match={searchTerm} />
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
    prev.onSelect === next.onSelect &&
    prev.searchTerm === next.searchTerm
  );
});

interface SidebarListItemsProps {
  cases: Case[];
  selectedId: string | undefined;
  onSelect: (c: Case) => void;
  searchTerm?: string;
}

// Optimization: Isolate the list rendering to prevent reconciliation of the entire list
// when parent Sidebar re-renders (e.g. during typing in the filter input).
// Even though SidebarItem is memoized, re-rendering the mapping loop creates N new Element objects
// and triggers N prop comparisons. By memoizing the list container, we skip this entirely
// when 'cases' (filtered list) hasn't changed.
const SidebarListItems = memo(({ cases, selectedId, onSelect, searchTerm }: SidebarListItemsProps) => {
  return (
    <>
      {cases.map(c => (
        <li key={c.id} className="cv-auto">
          <SidebarItem
            item={c}
            isSelected={selectedId === c.id}
            onSelect={onSelect}
            searchTerm={searchTerm}
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

  useEffect(() => {
    if (selectedCaseId && listRef.current) {
      requestAnimationFrame(() => {
        const selectedEl = listRef.current?.querySelector('[aria-current="true"]');
        if (selectedEl) {
          selectedEl.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        }
      });
    }
  }, [selectedCaseId]);

  const handleListKeyDown = (e: React.KeyboardEvent) => {
    if (!['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(e.key)) return;

    e.preventDefault();
    const list = listRef.current;
    if (!list) return;

    // Optimization: Use direct DOM traversal (O(1)) instead of querySelectorAll (O(N))
    // This significantly improves responsiveness on large lists (e.g. 1000+ cases).

    if (e.key === 'Home') {
      const firstBtn = list.firstElementChild?.querySelector('button');
      if (firstBtn) (firstBtn as HTMLElement).focus();
      return;
    }

    if (e.key === 'End') {
      const lastBtn = list.lastElementChild?.querySelector('button');
      if (lastBtn) (lastBtn as HTMLElement).focus();
      return;
    }

    const activeEl = document.activeElement as HTMLElement;
    const currentLi = activeEl.closest('li');

    // If focus is not on an item (e.g. just focused the list or lost focus), try to focus the first item
    if (!currentLi || !list.contains(currentLi)) {
      const firstBtn = list.firstElementChild?.querySelector('button');
      if (firstBtn) (firstBtn as HTMLElement).focus();
      return;
    }

    if (e.key === 'ArrowDown') {
      const nextLi = currentLi.nextElementSibling;
      if (nextLi) {
        const btn = nextLi.querySelector('button');
        if (btn) (btn as HTMLElement).focus();
      }
    } else if (e.key === 'ArrowUp') {
      const prevLi = currentLi.previousElementSibling;
      if (prevLi) {
        const btn = prevLi.querySelector('button');
        if (btn) (btn as HTMLElement).focus();
      }
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
              className="w-full bg-gray-900 text-xs text-gray-300 rounded border border-gray-700 pl-8 pr-8 py-1.5 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 placeholder:text-gray-500"
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
            <div className="flex items-center justify-between mb-2">
              <h2 id="cases-heading" className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Cases</h2>
              <span className="text-[10px] text-gray-500 font-mono" aria-label={`${filteredCases.length} of ${cases.length} cases shown`}>
                {filteredCases.length < cases.length ? `${filteredCases.length}/${cases.length}` : cases.length}
              </span>
            </div>
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
                  searchTerm={deferredFilter}
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

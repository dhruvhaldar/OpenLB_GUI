import React, { memo } from 'react';
import { Folder, Activity, RefreshCw } from 'lucide-react';
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
});

interface SidebarProps {
  cases: Case[];
  selectedCaseId: string | undefined;
  onSelectCase: (c: Case) => void;
  isLoading?: boolean;
  onRefresh?: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ cases, selectedCaseId, onSelectCase, isLoading, onRefresh }) => {
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
          <h2 id="cases-heading" className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Cases</h2>
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
            ) : cases.length > 0 ? (
              cases.map(c => (
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
                No cases found
              </li>
            )}
          </ul>
        </div>
      </nav>
    </aside>
  );
};

export default memo(Sidebar);

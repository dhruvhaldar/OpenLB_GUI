import React, { memo } from 'react';
import { Folder, Activity } from 'lucide-react';
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
      <Folder size={16} />
      <span className="truncate">{item.name}</span>
    </button>
  );
});

interface SidebarProps {
  cases: Case[];
  selectedCaseId: string | undefined;
  onSelectCase: (c: Case) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ cases, selectedCaseId, onSelectCase }) => {
  return (
    <div className="w-64 bg-gray-800 p-4 border-r border-gray-700">
      <h1 className="text-xl font-bold mb-6 flex items-center gap-2">
        <Activity className="text-blue-500" /> OpenLB Manager
      </h1>
      <div className="space-y-4">
        <h2 id="cases-heading" className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Cases</h2>
        <ul className="space-y-1" aria-labelledby="cases-heading">
          {cases.length > 0 ? (
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
    </div>
  );
};

export default memo(Sidebar);

import React, { memo } from 'react';
import { Activity, Folder } from 'lucide-react';
import type { Case } from '../types';

interface SidebarProps {
  cases: Case[];
  selectedCase: Case | null;
  onSelect: (c: Case) => void;
}

const Sidebar: React.FC<SidebarProps> = memo(({ cases, selectedCase, onSelect }) => {
  return (
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
              onClick={() => onSelect(c)}
              className={`w-full text-left px-3 py-2 rounded flex items-center gap-2 ${
                selectedCase?.id === c.id ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-gray-700'
              }`}
            >
              <Folder size={16} />
              <span className="truncate">{c.name}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
});

export default Sidebar;

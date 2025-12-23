import React, { memo } from 'react';
import { Folder, Activity } from 'lucide-react';
import type { Case } from '../types';

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
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Cases</h2>
        <div className="space-y-1">
          {cases.map(c => (
            <button
              key={c.id}
              onClick={() => onSelectCase(c)}
              className={`w-full text-left px-3 py-2 rounded flex items-center gap-2 ${selectedCaseId === c.id ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-gray-700'}`}
            >
              <Folder size={16} />
              <span className="truncate">{c.name}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default memo(Sidebar);

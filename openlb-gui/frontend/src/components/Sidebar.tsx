import { memo } from 'react';
import { Folder, Activity } from 'lucide-react';

export interface Case {
  id: string;
  path: string;
  name: string;
  domain: string;
}

interface SidebarProps {
  cases: Case[];
  selectedCase: Case | null;
  onSelectCase: (c: Case) => void;
}

// Optimization: Memoize Sidebar to prevent unnecessary re-renders when parent state (config/output) changes.
// The list of cases is static relative to typing in the config editor.
const Sidebar = memo(({ cases, selectedCase, onSelectCase }: SidebarProps) => {
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

Sidebar.displayName = 'Sidebar';

export default Sidebar;

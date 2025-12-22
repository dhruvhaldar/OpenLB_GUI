import React from 'react';
import { Folder } from 'lucide-react';
import type { Case } from '../types';

interface CaseListProps {
  cases: Case[];
  selectedCaseId: string | undefined;
  onSelectCase: (c: Case) => void;
}

// Optimization: React.memo prevents unnecessary re-renders when parent state (like output log) changes
const CaseList = React.memo(({ cases, selectedCaseId, onSelectCase }: CaseListProps) => {
  return (
    <div className="space-y-1">
      {cases.map(c => (
        <button
          key={c.id}
          onClick={() => onSelectCase(c)}
          className={`w-full text-left px-3 py-2 rounded flex items-center gap-2 ${
            selectedCaseId === c.id ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-gray-700'
          }`}
        >
          <Folder size={16} />
          <span className="truncate">{c.name}</span>
        </button>
      ))}
    </div>
  );
});

CaseList.displayName = 'CaseList';

export default CaseList;

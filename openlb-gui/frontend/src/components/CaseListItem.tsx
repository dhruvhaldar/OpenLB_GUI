import React from 'react';
import { Folder } from 'lucide-react';
import type { Case } from '../App';

interface CaseListItemProps {
  c: Case;
  isSelected: boolean;
  onSelect: (c: Case) => void;
}

export const CaseListItem = React.memo(({ c, isSelected, onSelect }: CaseListItemProps) => {
  return (
    <button
      onClick={() => onSelect(c)}
      className={`w-full text-left px-3 py-2 rounded flex items-center gap-2 ${
        isSelected ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-gray-700'
      }`}
    >
      <Folder size={16} />
      <span className="truncate">{c.name}</span>
    </button>
  );
});

CaseListItem.displayName = 'CaseListItem';

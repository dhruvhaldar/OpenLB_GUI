import React, { memo, useEffect, useRef } from 'react';
import { Loader2 } from 'lucide-react';
import { Modal } from './Modal';

interface DuplicateCaseModalProps {
  isOpen: boolean;
  onClose: () => void;
  duplicateName: string;
  onNameChange: (name: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  isDuplicating: boolean;
  error: string | null;
}

const DuplicateCaseModal: React.FC<DuplicateCaseModalProps> = ({
  isOpen,
  onClose,
  duplicateName,
  onNameChange,
  onSubmit,
  isDuplicating,
  error
}) => {
  const duplicateInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      // Small timeout to allow dialog to open and settle
      const timer = setTimeout(() => {
        duplicateInputRef.current?.focus();
        duplicateInputRef.current?.select();
      }, 50);
      return () => clearTimeout(timer);
    }
  }, [isOpen]);

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Duplicate Case"
    >
      <form onSubmit={onSubmit}>
        <div className="mb-4">
          <label htmlFor="caseName" className="block text-sm font-medium mb-2 text-gray-300">
            New Case Name
          </label>
          <input
            ref={duplicateInputRef}
            id="caseName"
            type="text"
            value={duplicateName}
            onChange={(e) => onNameChange(e.target.value)}
            className={`w-full bg-gray-900 border rounded px-3 py-2 text-white focus:outline-none placeholder-gray-600 transition-colors ${
              error
                ? 'border-red-500 focus:ring-2 focus:ring-red-500'
                : 'border-gray-600 focus:ring-2 focus:ring-blue-500'
            }`}
            placeholder="e.g. cylinder-flow-v2"
            aria-invalid={!!error}
            aria-describedby={error ? "duplicate-error-msg" : undefined}
          />
          {error && (
            <p id="duplicate-error-msg" className="mt-2 text-sm text-red-400">{error}</p>
          )}
        </div>
        <div className="flex justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded transition-colors focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={!duplicateName.trim() || isDuplicating}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded flex items-center gap-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus-visible:ring-2 focus-visible:ring-white focus-visible:outline-none"
          >
            {isDuplicating && <Loader2 className="animate-spin" size={16} />}
            Duplicate
          </button>
        </div>
      </form>
    </Modal>
  );
};

// Optimization: Memoize to prevent re-renders when parent state (logs, build status) changes
// This component should only re-render when its specific props change.
export default memo(DuplicateCaseModal);

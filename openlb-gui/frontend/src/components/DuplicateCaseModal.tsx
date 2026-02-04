import React, { memo, useEffect, useRef, useState } from 'react';
import { Loader2 } from 'lucide-react';
import { Modal } from './Modal';

const VALID_NAME_PATTERN = /^[a-zA-Z0-9_-]+$/;
const RESERVED_WINDOWS_NAMES = new Set([
  "CON", "PRN", "AUX", "NUL",
  "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
  "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
]);

interface DuplicateCaseModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialName: string;
  onSubmit: (name: string) => void;
  isDuplicating: boolean;
  error: string | null;
}

const DuplicateCaseModal: React.FC<DuplicateCaseModalProps> = ({
  isOpen,
  onClose,
  initialName,
  onSubmit,
  isDuplicating,
  error
}) => {
  const duplicateInputRef = useRef<HTMLInputElement>(null);
  const [name, setName] = useState(initialName);

  const validationError = (() => {
    if (!name) return null;
    if (!VALID_NAME_PATTERN.test(name)) {
      return "Invalid name. Use alphanumeric, underscore, and hyphen only.";
    }
    if (RESERVED_WINDOWS_NAMES.has(name.toUpperCase())) {
      return "Invalid name. This name is reserved by Windows.";
    }
    return null;
  })();

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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validationError) {
      onSubmit(name);
    }
  };

  const displayError = error || validationError;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Duplicate Case"
    >
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label htmlFor="caseName" className="block text-sm font-medium mb-2 text-gray-300">
            New Case Name
          </label>
          <input
            ref={duplicateInputRef}
            id="caseName"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className={`w-full bg-gray-900 border rounded px-3 py-2 text-white focus:outline-none placeholder-gray-600 transition-colors ${
              displayError
                ? 'border-red-500 focus:ring-2 focus:ring-red-500'
                : 'border-gray-600 focus:ring-2 focus:ring-blue-500'
            }`}
            placeholder="e.g. cylinder-flow-v2"
            aria-invalid={!!displayError}
            aria-describedby={displayError ? "duplicate-error-msg" : undefined}
          />
          {displayError && (
            <p id="duplicate-error-msg" className="mt-2 text-sm text-red-400">{displayError}</p>
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
            disabled={!name.trim() || isDuplicating || !!validationError}
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

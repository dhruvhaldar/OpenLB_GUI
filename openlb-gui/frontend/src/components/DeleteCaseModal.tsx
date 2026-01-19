import React, { memo } from 'react';
import { Loader2 } from 'lucide-react';
import { Modal } from './Modal';

interface DeleteCaseModalProps {
  isOpen: boolean;
  onClose: () => void;
  caseName: string | undefined;
  onConfirm: () => void;
  isDeleting: boolean;
  error?: string | null;
}

const DeleteCaseModal: React.FC<DeleteCaseModalProps> = ({
  isOpen,
  onClose,
  caseName,
  onConfirm,
  isDeleting,
  error
}) => {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Delete Case"
    >
      <div className="flex flex-col gap-4">
        <p className="text-gray-300">
          Are you sure you want to delete <span className="font-semibold text-white">{caseName}</span>? This action cannot be undone.
        </p>

        {error && (
          <div className="p-3 bg-red-900/50 border border-red-700/50 rounded text-red-200 text-sm" role="alert">
            {error}
          </div>
        )}

        <div className="flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded transition-colors focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={isDeleting}
            className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded transition-colors focus-visible:ring-2 focus-visible:ring-white focus-visible:outline-none flex items-center gap-2 disabled:opacity-50"
          >
            {isDeleting && <Loader2 className="animate-spin" size={16} />}
            Delete
          </button>
        </div>
      </div>
    </Modal>
  );
};

// Optimization: Memoize to prevent re-renders when parent state (logs, build status) changes
export default memo(DeleteCaseModal);

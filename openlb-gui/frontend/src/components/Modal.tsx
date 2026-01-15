import React, { useEffect, useRef } from 'react';
import { X } from 'lucide-react';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}

export const Modal: React.FC<ModalProps> = ({ isOpen, onClose, title, children }) => {
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (isOpen) {
      if (!dialog?.open) {
          dialog?.showModal();
      }
    } else {
      if (dialog?.open) {
          dialog?.close();
      }
    }
  }, [isOpen]);

  const handleCancel = (e: React.SyntheticEvent<HTMLDialogElement, Event>) => {
    e.preventDefault();
    onClose();
  };

  const handleClick = (e: React.MouseEvent<HTMLDialogElement>) => {
    const dialog = dialogRef.current;
    if (dialog && e.target === dialog) {
      onClose();
    }
  };

  return (
    <dialog
      ref={dialogRef}
      className="bg-gray-800 text-white rounded-lg shadow-xl p-0 backdrop:bg-black/50 backdrop:backdrop-blur-sm border border-gray-700 w-full max-w-md"
      onCancel={handleCancel}
      onClick={handleClick}
    >
      <div className="flex items-center justify-between p-4 border-b border-gray-700">
        <h3 className="font-semibold text-lg">{title}</h3>
        <button
            onClick={onClose}
            className="text-gray-400 hover:text-white rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 p-1"
            aria-label="Close modal"
        >
          <X size={20} />
        </button>
      </div>
      <div className="p-4">
        {children}
      </div>
    </dialog>
  );
};

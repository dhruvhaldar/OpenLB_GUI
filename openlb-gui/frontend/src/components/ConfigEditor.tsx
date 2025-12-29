import React, { memo, useState, useEffect, useRef, useLayoutEffect } from 'react';
import { FileText, Save, Check, Loader2 } from 'lucide-react';

interface ConfigEditorProps {
  initialContent: string;
  onSave: (content: string) => Promise<void>;
  className?: string;
  caseId?: string; // Optional ID for tracking case context switches
}

const ConfigEditor: React.FC<ConfigEditorProps> = ({ initialContent, onSave, className, caseId }) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  const [prevCaseId, setPrevCaseId] = useState(caseId);

  // Reset status when case context changes
  if (prevCaseId !== caseId) {
    setPrevCaseId(caseId);
    setSaveStatus('idle');
  }

  // Optimization: Update the textarea value directly when initialContent changes
  // to support reusing the component instance without unmounting/remounting.
  useLayoutEffect(() => {
    if (textareaRef.current) {
      // Force update if content changed.
      // Note: We depend on caseId to force update even if initialContent is identical
      // when switching cases, ensuring dirty state is reset.
      textareaRef.current.value = initialContent;
      // Reset scroll position to top when content changes (new file loaded)
      textareaRef.current.scrollTop = 0;
    }
  }, [initialContent, caseId]);

  useEffect(() => {
    if (saveStatus === 'saved') {
      const timer = setTimeout(() => setSaveStatus('idle'), 2000);
      return () => clearTimeout(timer);
    }
  }, [saveStatus]);

  const handleSave = async () => {
    setSaveStatus('saving');
    try {
      // Optimization: Read directly from ref to avoid re-renders on every keystroke
      const currentContent = textareaRef.current?.value || '';
      await onSave(currentContent);
      setSaveStatus('saved');
    } catch {
      setSaveStatus('error');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
      e.preventDefault();
      handleSave();
    }
  };

  return (
    <div className={`flex flex-col ${className || ''}`}>
      <div className="flex justify-between items-center mb-2">
        <h3 id="config-editor-title" className="font-semibold text-gray-400 flex items-center gap-2">
          <FileText size={16} /> Configuration
        </h3>
        <button
          onClick={handleSave}
          disabled={saveStatus === 'saving'}
          title="Save (Ctrl+S)"
          aria-keyshortcuts="Control+S"
          className={`text-sm flex items-center gap-2 px-3 py-1 rounded transition-colors ${
            saveStatus === 'saved'
              ? 'text-green-400 hover:text-green-300'
              : saveStatus === 'error'
              ? 'text-red-400 hover:text-red-300'
              : 'text-blue-400 hover:text-blue-300 hover:bg-gray-800'
          }`}
        >
          {saveStatus === 'saving' ? (
            <Loader2 className="animate-spin" size={14} />
          ) : saveStatus === 'saved' ? (
            <Check size={14} />
          ) : (
            <Save size={14} />
          )}
          {saveStatus === 'saved' ? 'Saved' : saveStatus === 'error' ? 'Error' : 'Save'}
        </button>
      </div>
      <textarea
        ref={textareaRef}
        aria-labelledby="config-editor-title"
        defaultValue={initialContent}
        onKeyDown={handleKeyDown}
        className="flex-1 bg-gray-950 text-gray-300 p-4 rounded font-mono text-sm resize-none focus:outline-none focus:ring-1 focus:ring-blue-500"
      />
    </div>
  );
};

export default memo(ConfigEditor);

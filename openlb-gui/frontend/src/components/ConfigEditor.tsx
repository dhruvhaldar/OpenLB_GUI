import React, { memo, useState, useEffect, useRef } from 'react';
import { FileText, Save, Check, Loader2, Copy } from 'lucide-react';

interface ConfigEditorProps {
  initialContent: string;
  onSave: (content: string) => Promise<void>;
  className?: string;
  isLoading?: boolean;
}

const ConfigEditor: React.FC<ConfigEditorProps> = ({ initialContent, onSave, className, isLoading = false }) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const lastSavedContent = useRef(initialContent);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  const [isDirty, setIsDirty] = useState(false);
  const [copyStatus, setCopyStatus] = useState<'idle' | 'copied' | 'error'>('idle');

  // Optimization: Debounce dirty check to prevent heavy string allocation/comparison on every keystroke
  // Accessing textareaRef.current.value creates a new string (potentially large).
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    // When content finishes loading, sync the dirty tracking baseline
    if (!isLoading) {
      lastSavedContent.current = initialContent;
      // If the textarea is mounted (which it should be if !isLoading),
      // we don't need to force update it because defaultValue handles the mount.
      // But if we transition from !isLoading -> !isLoading (prop update),
      // we might need to sync. However, this component is designed
      // to rely on key-based remounting or manual resets.
      // For the specific case of Loading -> Loaded, this sync is sufficient.
    }
  }, [initialContent, isLoading]);

  useEffect(() => {
    if (saveStatus === 'saved') {
      const timer = setTimeout(() => setSaveStatus('idle'), 2000);
      return () => clearTimeout(timer);
    }
  }, [saveStatus]);

  useEffect(() => {
    if (copyStatus !== 'idle') {
      const timer = setTimeout(() => setCopyStatus('idle'), 2000);
      return () => clearTimeout(timer);
    }
  }, [copyStatus]);

  // Optimization: Cleanup debounce timer on unmount
  useEffect(() => {
    return () => {
        if (debounceRef.current) clearTimeout(debounceRef.current);
    }
  }, []);

  const handleCopy = async () => {
    try {
      const currentContent = textareaRef.current?.value || '';
      await navigator.clipboard.writeText(currentContent);
      setCopyStatus('copied');
    } catch {
      setCopyStatus('error');
    }
  };

  const handleSave = async () => {
    setSaveStatus('saving');
    // Clear any pending dirty checks as we are about to save
    if (debounceRef.current) clearTimeout(debounceRef.current);

    try {
      // Optimization: Read directly from ref to avoid re-renders on every keystroke
      const currentContent = textareaRef.current?.value || '';
      await onSave(currentContent);
      setSaveStatus('saved');
      lastSavedContent.current = currentContent;
      setIsDirty(false);
    } catch {
      setSaveStatus('error');
    }
  };

  const handleChange = () => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    // Optimization: Debounce the dirty check by 300ms.
    // This avoids accessing .value (which allocates a new string) and comparing it
    // on every single keystroke, significantly reducing GC pressure for large config files.
    debounceRef.current = setTimeout(() => {
        if (textareaRef.current) {
             // Optimization: Check length first to avoid string allocation
             // accessing .value allocates a new string, but .textLength is a fast property
             if (textareaRef.current.textLength !== lastSavedContent.current.length) {
                 setIsDirty(true);
             } else {
                 setIsDirty(textareaRef.current.value !== lastSavedContent.current);
             }
        }
    }, 300);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Save shortcut
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
      e.preventDefault();
      if (!isLoading) {
        handleSave();
      }
      return;
    }

    // UX: Allow standard Tab indentation for better coding experience
    if (e.key === 'Tab' && !e.shiftKey) {
      e.preventDefault();
      const target = e.currentTarget;
      const start = target.selectionStart;
      const end = target.selectionEnd;
      const value = target.value;

      // Insert 2 spaces
      target.value = value.substring(0, start) + '  ' + value.substring(end);

      // Move cursor after the inserted spaces
      target.selectionStart = target.selectionEnd = start + 2;

      // Trigger dirty check
      handleChange();
    }

    // Accessibility: Ensure users can escape the trapped focus
    if (e.key === 'Escape') {
      e.currentTarget.blur();
    }
  };

  const getButtonTitle = () => {
    if (isLoading) return 'Loading...';
    switch (saveStatus) {
      case 'saving': return 'Saving...';
      case 'saved': return 'Configuration Saved';
      case 'error': return 'Save Failed - Click to retry';
      default: return isDirty ? 'Unsaved changes (Ctrl+S)' : 'Save (Ctrl+S)';
    }
  };

  return (
    <div className={`flex flex-col ${className || ''}`}>
      <div className="flex justify-between items-center mb-2">
        <h3 id="config-editor-title" className="font-semibold text-gray-400 flex items-center gap-2">
          <FileText size={16} /> Configuration
          <span className="text-[10px] text-gray-500 font-normal ml-1 hidden sm:inline-block" aria-hidden="true">(Esc to exit)</span>
        </h3>
        <div className="flex gap-2">
          <button
            onClick={handleCopy}
            disabled={isLoading}
            className={`p-1 rounded transition-colors focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none disabled:opacity-50 ${
              copyStatus === 'copied' ? 'text-green-400 hover:text-green-300' : 'text-gray-400 hover:text-white'
            }`}
            aria-label={copyStatus === 'copied' ? "Copied configuration" : "Copy configuration"}
            title={copyStatus === 'copied' ? "Copied!" : "Copy configuration"}
          >
            {copyStatus === 'copied' ? <Check size={16} /> : <Copy size={16} />}
          </button>
          <button
            onClick={handleSave}
            disabled={saveStatus === 'saving' || isLoading}
            title={getButtonTitle()}
            aria-keyshortcuts="Control+S"
            aria-live="polite"
            className={`text-sm flex items-center gap-2 px-3 py-1 rounded transition-colors focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none disabled:opacity-50 ${
              saveStatus === 'saved'
                ? 'text-green-400 hover:text-green-300'
                : saveStatus === 'error'
                ? 'text-red-400 hover:text-red-300'
                : isDirty
                ? 'text-amber-400 hover:text-amber-300 bg-gray-800'
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
            {saveStatus === 'saved' ? 'Saved' : saveStatus === 'error' ? 'Failed' : isDirty ? 'Save*' : 'Save'}
            {saveStatus === 'idle' && (
              <kbd className="hidden md:inline-block px-1.5 py-0.5 text-[10px] font-mono bg-white/10 rounded opacity-80 ml-1">Ctrl+S</kbd>
            )}
          </button>
        </div>
      </div>
      {isLoading ? (
        <div className="flex-1 bg-gray-950 text-gray-500 p-4 rounded font-mono text-sm flex items-center justify-center border border-gray-800">
          <Loader2 className="animate-spin mr-2" /> Loading config...
        </div>
      ) : (
        <>
          <span id="editor-help-text" className="sr-only">
            Press Tab to insert spaces. Press Escape to exit the editor.
          </span>
          <textarea
          ref={textareaRef}
          aria-labelledby="config-editor-title"
          aria-describedby="editor-help-text"
          defaultValue={initialContent}
          onKeyDown={handleKeyDown}
          onChange={handleChange}
          spellCheck={false}
          autoCorrect="off"
          autoCapitalize="off"
          className="flex-1 bg-gray-950 text-gray-300 p-4 rounded font-mono text-sm resize-none focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
        </>
      )}
    </div>
  );
};

export default memo(ConfigEditor);

import React, { memo, useState, useEffect } from 'react';
import { FileText } from 'lucide-react';

interface ConfigEditorProps {
  initialContent: string;
  onSave: (content: string) => Promise<void>;
  className?: string;
}

const ConfigEditor: React.FC<ConfigEditorProps> = ({ initialContent, onSave, className }) => {
  const [content, setContent] = useState(initialContent);

  // Sync state if initialContent changes (e.g. from fetching a new case)
  useEffect(() => {
    setContent(initialContent);
  }, [initialContent]);

  const handleSave = async () => {
    await onSave(content);
  };

  return (
    <div className={`flex flex-col ${className || ''}`}>
      <div className="flex justify-between items-center mb-2">
        <h3 className="font-semibold text-gray-400 flex items-center gap-2">
          <FileText size={16} /> Configuration
        </h3>
        <button
          onClick={handleSave}
          className="text-sm text-blue-400 hover:text-blue-300"
        >
          Save
        </button>
      </div>
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        className="flex-1 bg-gray-950 text-gray-300 p-4 rounded font-mono text-sm resize-none focus:outline-none focus:ring-1 focus:ring-blue-500"
      />
    </div>
  );
};

export default memo(ConfigEditor);

import React, { memo, useEffect, useRef, useState } from 'react';
import { ArrowDown } from 'lucide-react';

interface LogViewerProps {
  output: string;
}

/**
 * LogViewer Component
 *
 * Displays the simulation output logs.
 *
 * PERFORMANCE OPTIMIZATION:
 * This component is wrapped in React.memo() to prevent unnecessary re-renders.
 * The terminal output can become very large (hundreds of KB), making Virtual DOM diffing expensive.
 * By isolating it here, we ensure it only re-renders when the 'output' prop actually changes,
 * avoiding re-renders when parent state (like copy button status, build status) changes.
 */
const LogViewer: React.FC<LogViewerProps> = ({ output }) => {
  const logRef = useRef<HTMLPreElement>(null);
  // Default to true so it scrolls on first load
  const isAtBottomRef = useRef(true);
  const [showScrollButton, setShowScrollButton] = useState(false);

  const handleScroll = () => {
    if (!logRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = logRef.current;
    // We consider "at bottom" if within 50px of the bottom to allow for some buffer
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;
    isAtBottomRef.current = isAtBottom;
    setShowScrollButton(!isAtBottom);
  };

  const scrollToBottom = () => {
    if (logRef.current) {
      logRef.current.scrollTo({ top: logRef.current.scrollHeight, behavior: 'smooth' });
    }
  };

  useEffect(() => {
    // Only auto-scroll if the user was already at the bottom
    if (logRef.current && isAtBottomRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [output]);

  return (
    <div className="relative flex-1 min-h-0">
      <pre
        ref={logRef}
        onScroll={handleScroll}
        role="log"
        tabIndex={0}
        aria-label="Process Output"
        className="absolute inset-0 overflow-auto text-green-400 font-mono text-sm p-2 focus:outline-none focus:ring-1 focus:ring-gray-500 rounded"
      >
        {output}
      </pre>
      {showScrollButton && (
        <button
          onClick={scrollToBottom}
          className="absolute bottom-4 right-4 bg-gray-700 p-2 rounded-full shadow-lg hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 text-white opacity-80 hover:opacity-100 transition-opacity"
          aria-label="Scroll to bottom"
          title="Scroll to bottom"
        >
          <ArrowDown size={20} />
        </button>
      )}
    </div>
  );
};

export default memo(LogViewer);

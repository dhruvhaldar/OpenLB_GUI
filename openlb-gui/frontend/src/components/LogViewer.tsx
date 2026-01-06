import React, { memo, useLayoutEffect, useRef, useState } from 'react';
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
      // UX Improvement: Move focus to the log container when button is clicked.
      // Since the button will disappear (unmount) when at the bottom, we need to ensure
      // focus is not lost (which would reset to body). This allows keyboard users
      // to continue navigating the logs immediately.
      logRef.current.focus({ preventScroll: true });
    }
  };

  // Optimization: Use useLayoutEffect instead of useEffect to update scroll position synchronously
  // before the browser paints. This prevents a visual "jump" where the new content is rendered
  // at the old scroll position first, then immediately scrolled to the bottom.
  // It ensures the user sees the logs appearing at the correct position instantly.
  useLayoutEffect(() => {
    // Only auto-scroll if the user was already at the bottom
    if (logRef.current && isAtBottomRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [output]);

  return (
    <div className="flex-1 relative min-h-0 flex flex-col group">
      <pre
        ref={logRef}
        onScroll={handleScroll}
        role="log"
        tabIndex={0}
        aria-label="Process Output"
        className="flex-1 overflow-auto text-green-400 font-mono text-sm p-2 focus:outline-none focus:ring-1 focus:ring-gray-500 rounded scroll-smooth"
      >
        {output}
      </pre>
      {showScrollButton && (
        <button
          onClick={scrollToBottom}
          aria-label="Scroll to bottom"
          title="Scroll to bottom"
          className="absolute bottom-4 right-4 p-2 bg-gray-700/80 text-white rounded-full shadow-lg hover:bg-gray-600 backdrop-blur-sm transition-all focus:outline-none focus:ring-2 focus:ring-blue-500 animate-in fade-in slide-in-from-bottom-2"
        >
          <ArrowDown size={20} />
        </button>
      )}
    </div>
  );
};

export default memo(LogViewer);

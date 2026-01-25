import React, { memo, useLayoutEffect, useRef, useState, useEffect } from 'react';
import { ArrowDown, Terminal, Play, Settings } from 'lucide-react';

interface LogViewerProps {
  output: string;
  isWrapped?: boolean;
  onRun?: () => void;
  onBuild?: () => void;
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
const LogViewer: React.FC<LogViewerProps> = ({ output, isWrapped = false, onRun, onBuild }) => {
  const logRef = useRef<HTMLPreElement>(null);
  // Default to true so it scrolls on first load
  const isAtBottomRef = useRef(true);
  const [showScrollButton, setShowScrollButton] = useState(false);
  const scrollRafRef = useRef<number | null>(null);

  const handleScroll = () => {
    // Optimization: Throttling scroll event with requestAnimationFrame
    // Scroll events fire at a high rate (often 60fps+). Reading layout properties (scrollTop, scrollHeight)
    // forces a browser reflow (layout calculation) which is expensive.
    // By using requestAnimationFrame, we ensure we only perform this check once per frame,
    // avoiding layout thrashing and improving scroll performance.
    if (scrollRafRef.current) return;

    scrollRafRef.current = requestAnimationFrame(() => {
      if (logRef.current) {
        const { scrollTop, scrollHeight, clientHeight } = logRef.current;
        // We consider "at bottom" if within 50px of the bottom to allow for some buffer
        const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;
        isAtBottomRef.current = isAtBottom;
        setShowScrollButton(!isAtBottom);
      }
      scrollRafRef.current = null;
    });
  };

  useEffect(() => {
    return () => {
      if (scrollRafRef.current) {
        cancelAnimationFrame(scrollRafRef.current);
      }
    };
  }, []);

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
      {output ? (
        <pre
          ref={logRef}
          onScroll={handleScroll}
          role="log"
          tabIndex={0}
          aria-label="Process Output"
          className={`flex-1 overflow-auto text-green-400 font-mono text-sm p-2 focus:outline-none focus:ring-1 focus:ring-gray-500 rounded scroll-smooth ${
            isWrapped ? 'whitespace-pre-wrap' : 'whitespace-pre'
          }`}
        >
          {output}
        </pre>
      ) : (
        <div className="flex-1 flex flex-col items-center justify-center font-mono text-sm">
          <Terminal size={48} className="mb-4 text-gray-600" aria-hidden="true" />
          <p className="text-gray-400">No output generated yet.</p>
          <p className="text-xs mt-1 text-gray-400/75 mb-6">Build or run the simulation to view logs.</p>
          {(onBuild || onRun) && (
            <div className="flex gap-4">
              {onBuild && (
                <button
                  onClick={onBuild}
                  className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-200 rounded flex items-center gap-2 text-xs transition-colors focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none"
                  aria-label="Build simulation"
                  title="Build simulation (Ctrl+B)"
                  aria-keyshortcuts="Control+B"
                >
                  <Settings size={14} /> Build
                  <kbd className="hidden md:inline-block px-1.5 py-0.5 text-[10px] font-mono bg-black/20 rounded opacity-80">Ctrl+B</kbd>
                </button>
              )}
              {onRun && (
                <button
                  onClick={onRun}
                  className="px-4 py-2 bg-green-700 hover:bg-green-600 text-white rounded flex items-center gap-2 text-xs transition-colors focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none"
                  aria-label="Run simulation"
                  title="Run simulation (Ctrl+Enter)"
                  aria-keyshortcuts="Control+Enter"
                >
                  <Play size={14} /> Run
                  <kbd className="hidden md:inline-block px-1.5 py-0.5 text-[10px] font-mono bg-black/20 rounded opacity-80">Ctrl+Enter</kbd>
                </button>
              )}
            </div>
          )}
        </div>
      )}
      {output && (
        <button
          onClick={scrollToBottom}
          aria-label="Scroll to bottom"
          title="Scroll to bottom"
          aria-hidden={!showScrollButton}
          tabIndex={showScrollButton ? 0 : -1}
          className={`absolute bottom-4 right-4 p-2 bg-gray-700/80 text-white rounded-full shadow-lg hover:bg-gray-600 backdrop-blur-sm transition-all duration-300 ease-out focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            showScrollButton
              ? 'opacity-100 translate-y-0 pointer-events-auto'
              : 'opacity-0 translate-y-2 pointer-events-none'
          }`}
        >
          <ArrowDown size={20} />
        </button>
      )}
    </div>
  );
};

export default memo(LogViewer);

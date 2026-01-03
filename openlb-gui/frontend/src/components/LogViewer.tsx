import React, { memo, useEffect, useRef } from 'react';

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

  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [output]);

  return (
    <pre
      ref={logRef}
      role="log"
      tabIndex={0}
      aria-label="Process Output"
      className="flex-1 overflow-auto text-green-400 font-mono text-sm p-2 focus:outline-none focus:ring-1 focus:ring-gray-500 rounded"
    >
      {output}
    </pre>
  );
};

export default memo(LogViewer);

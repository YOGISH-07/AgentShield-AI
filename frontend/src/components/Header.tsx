import React from 'react';

interface HeaderProps {
  isOnline: boolean;
  lastUpdated: Date | null;
}

export const Header: React.FC<HeaderProps> = ({ isOnline, lastUpdated }) => {
  return (
    <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur-md px-6 py-4 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 font-bold text-lg shadow-sm">
              🛡️
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold tracking-wider text-slate-100 uppercase">
                  AGENTSHIELD <span className="text-cyan-400">AI</span>
                </h1>
                <span className="px-2 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/30 text-[10px] font-extrabold text-cyan-400 uppercase tracking-widest">
                  ● DEVHOST 2026 PS 2.1 MVP
                </span>
              </div>
              <p className="text-xs text-slate-400 tracking-wide font-medium">
                AI Agent Safety & Interception Control System — Real-time Action Monitoring & Explainable Policy Interception.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-950/60 border border-slate-800 text-xs">
            <span
              className={`w-2.5 h-2.5 rounded-full ${
                isOnline ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'
              }`}
            />
            <span className={`font-semibold ${isOnline ? 'text-emerald-400' : 'text-rose-400'}`}>
              {isOnline ? '● SAFETY ENGINE OPERATIONAL' : '● CONTROL BACKEND OFFLINE'}
            </span>
          </div>

          {lastUpdated && (
            <div className="text-xs text-slate-500 hidden sm:block font-mono">
              Telemetry: {lastUpdated.toLocaleTimeString()}
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

import React from 'react';

export interface DemoPhaseInfo {
  timeSeconds: number;
  duration: number;
  phaseName: string;
  riskScore: number;
  classification: string;
  description: string;
  isAlertActive: boolean;
  isPlaying: boolean;
}

interface DemoTimelineProps {
  demoState: DemoPhaseInfo;
  onStartDemo: () => void;
  onPauseDemo: () => void;
  onRestartDemo: () => void;
  onStartPresentationDemo?: () => void;
  onResetDemo?: () => void;
}

export const DemoTimeline: React.FC<DemoTimelineProps> = ({
  demoState,
  onStartDemo,
  onPauseDemo,
  onRestartDemo,
  onStartPresentationDemo,
  onResetDemo,
}) => {
  const { timeSeconds, duration, phaseName, riskScore, description, isAlertActive, isPlaying } =
    demoState;

  const progressPct = Math.min(100, Math.max(0, (timeSeconds / (duration || 25)) * 100));

  const formatTime = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    const ms = Math.floor((sec % 1) * 10);
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}.${ms}`;
  };

  const getPhaseBadgeStyle = () => {
    if (riskScore >= 70) {
      return 'bg-rose-500/20 text-rose-400 border-rose-500/50 animate-pulse';
    } else if (riskScore >= 40) {
      return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
    }
    return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
  };

  const getMeterColor = () => {
    if (riskScore >= 70) return 'bg-rose-500';
    if (riskScore >= 40) return 'bg-amber-500';
    if (riskScore > 0) return 'bg-cyan-500';
    return 'bg-emerald-500';
  };

  return (
    <div
      className={`bg-slate-900 border rounded-xl p-5 shadow-xl transition-all ${
        isAlertActive
          ? 'border-rose-500/50 shadow-rose-950/30 ring-1 ring-rose-500/30'
          : 'border-slate-800'
      }`}
    >
      {/* Top Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping" />
            <h3 className="text-xs font-extrabold text-slate-100 uppercase tracking-widest">
              LIVE AGENT SAFETY TIMELINE SIMULATION
            </h3>
            <span className="text-[10px] font-mono text-cyan-400 bg-cyan-950/80 px-2 py-0.5 rounded border border-cyan-800">
              SYNCED WITH AGENT TELEMETRY
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Real-time AI agent action monitoring and explainable policy decisioning.
          </p>
        </div>

        {/* Demo Controls */}
        <div className="flex flex-wrap items-center gap-2">
          {onStartPresentationDemo && (
            <button
              onClick={onStartPresentationDemo}
              className="px-3.5 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-extrabold text-xs flex items-center gap-1.5 transition-all shadow-md ring-1 ring-cyan-400/50"
            >
              <span>⚡</span> START 25s AGENT DEMO
            </button>
          )}

          {!isPlaying ? (
            <button
              onClick={onStartDemo}
              className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs transition-colors"
            >
              ▶ PLAY
            </button>
          ) : (
            <button
              onClick={onPauseDemo}
              className="px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs transition-colors"
            >
              ⏸ PAUSE
            </button>
          )}

          <button
            onClick={onRestartDemo}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs transition-colors border border-slate-700"
          >
            🔄 RESTART
          </button>

          {onResetDemo && (
            <button
              onClick={onResetDemo}
              className="px-3 py-1.5 rounded-lg bg-rose-950/80 hover:bg-rose-900/60 text-rose-300 font-semibold text-xs border border-rose-800/80 transition-colors"
            >
              🧹 RESET DATA
            </button>
          )}
        </div>
      </div>

      {/* Progress Bar & Meter */}
      <div className="space-y-2 mb-4">
        <div className="flex justify-between text-xs font-mono">
          <span className="text-slate-400">ELAPSED AGENT TIME: <strong className="text-slate-100">{formatTime(timeSeconds)}</strong></span>
          <span className="text-slate-400">DURATION: <strong className="text-slate-100">{formatTime(duration)}</strong></span>
        </div>

        <div className="w-full bg-slate-950 h-2.5 rounded-full overflow-hidden border border-slate-800 relative">
          <div
            className={`h-full transition-all duration-200 ${getMeterColor()}`}
            style={{ width: `${progressPct}%` }}
          />
        </div>
      </div>

      {/* Current Phase & Description */}
      <div className="bg-slate-950/70 p-3.5 rounded-xl border border-slate-850 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-bold">ACTIVE AGENT PHASE:</span>
            <span className={`px-2.5 py-0.5 rounded text-xs font-extrabold border ${getPhaseBadgeStyle()}`}>
              {phaseName}
            </span>
          </div>
          <p className="text-xs text-slate-300">{description}</p>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right">
            <span className="text-[10px] text-slate-500 font-bold uppercase block">Risk Score</span>
            <span className="text-lg font-mono font-extrabold text-slate-100">{riskScore}/100</span>
          </div>
        </div>
      </div>
    </div>
  );
};

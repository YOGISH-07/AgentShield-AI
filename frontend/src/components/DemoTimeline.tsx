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
    switch (phaseName) {
      case 'PHONE DETECTED':
        return 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30';
      case 'WATCH':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      case 'SUSPECTED RECORDING BEHAVIOR':
        return 'bg-rose-500/20 text-rose-400 border-rose-500/50 animate-pulse';
      default:
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
    }
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
              LIVE DEMO TIMELINE SIMULATION
            </h3>
            <span className="text-[10px] font-mono text-cyan-400 bg-cyan-950/80 px-2 py-0.5 rounded border border-cyan-800">
              SYNCED WITH VIDEO FEED
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Real-time computer vision behavioral risk progression synced with input stream.
          </p>
        </div>

        {/* Demo Controls */}
        <div className="flex flex-wrap items-center gap-2">
          {onStartPresentationDemo && (
            <button
              onClick={onStartPresentationDemo}
              className="px-3.5 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-extrabold text-xs flex items-center gap-1.5 transition-all shadow-md ring-1 ring-cyan-400/50"
            >
              <span>⚡</span> START PRESENTATION DEMO
            </button>
          )}

          {!isPlaying ? (
            <button
              onClick={onStartDemo}
              className="px-3 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs flex items-center gap-1 transition-colors shadow-sm"
            >
              <span>▶</span> PLAY
            </button>
          ) : (
            <button
              onClick={onPauseDemo}
              className="px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs flex items-center gap-1 transition-colors shadow-sm"
            >
              <span>⏸</span> PAUSE
            </button>
          )}

          <button
            onClick={onRestartDemo}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs flex items-center gap-1 transition-colors border border-slate-700"
          >
            <span>↻</span> RESTART
          </button>

          {onResetDemo && (
            <button
              onClick={onResetDemo}
              className="px-3 py-1.5 rounded-lg bg-rose-950/80 hover:bg-rose-900/60 text-rose-300 font-semibold text-xs flex items-center gap-1 transition-colors border border-rose-800/80"
            >
              <span>🧹</span> RESET DATA
            </button>
          )}
        </div>
      </div>

      {/* Progress Track & Key Phase Segment Markers */}
      <div className="mb-4 space-y-1.5">
        <div className="flex justify-between items-center text-[11px] font-mono text-slate-400">
          <span>Stream Timestamp: <strong className="text-slate-200">{formatTime(timeSeconds)}</strong></span>
          <span>Duration: <strong className="text-slate-200">{formatTime(duration)}</strong></span>
        </div>

        {/* Multi-segment Timeline Track */}
        <div className="relative w-full h-3 bg-slate-950 rounded-full overflow-hidden border border-slate-800 flex">
          {/* 0-5s NORMAL */}
          <div className="w-[20%] h-full bg-emerald-900/40 border-r border-slate-800/80" title="0-5s: NORMAL" />
          {/* 5-10s PHONE DETECTED */}
          <div className="w-[20%] h-full bg-cyan-900/40 border-r border-slate-800/80" title="5-10s: PHONE DETECTED" />
          {/* 10-12s WATCH */}
          <div className="w-[8%] h-full bg-amber-900/40 border-r border-slate-800/80" title="10-12s: WATCH" />
          {/* 12-20s ALERT */}
          <div className="w-[32%] h-full bg-rose-900/50 border-r border-slate-800/80" title="12-20s: SUSPECTED RECORDING" />
          {/* 20-25s NORMAL */}
          <div className="w-[20%] h-full bg-emerald-900/40" title="20-25s: NORMAL" />

          {/* Active Progress Overlay Bar */}
          <div
            className="absolute left-0 top-0 bottom-0 bg-cyan-400/30 transition-all duration-100 border-r-2 border-cyan-400"
            style={{ width: `${progressPct}%` }}
          />
        </div>

        {/* Timeline Markers */}
        <div className="grid grid-cols-5 text-[10px] font-mono text-slate-500 pt-1">
          <div>0s: Normal</div>
          <div>5s: Phone</div>
          <div>10s: Watch</div>
          <div className="text-rose-400 font-bold">12s: Alert (Risk ≥70)</div>
          <div>20s: Baseline</div>
        </div>
      </div>

      {/* Live Phase HUD & Risk Score Meter */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 bg-slate-950/60 rounded-lg p-4 border border-slate-850">
        {/* Active Phase Badge */}
        <div>
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
            Current Phase State
          </span>
          <span
            className={`inline-block px-3 py-1 rounded text-xs font-extrabold border uppercase tracking-wider ${getPhaseBadgeStyle()}`}
          >
            {phaseName}
          </span>
        </div>

        {/* Simulated Risk Meter */}
        <div>
          <div className="flex justify-between items-center text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">
            <span>Simulated Risk Score</span>
            <span className="text-slate-100 font-mono text-xs">{riskScore} / 100</span>
          </div>
          <div className="w-full h-2.5 bg-slate-900 rounded-full overflow-hidden border border-slate-800">
            <div
              className={`h-full transition-all duration-200 ${getMeterColor()}`}
              style={{ width: `${riskScore}%` }}
            />
          </div>
        </div>

        {/* Phase Description */}
        <div>
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
            Observed Behavioral Context
          </span>
          <p className="text-xs text-slate-300 leading-tight">{description}</p>
        </div>
      </div>

      {/* Alert Active Warning Banner */}
      {isAlertActive && (
        <div className="mt-3 bg-rose-500/10 border border-rose-500/40 rounded-lg p-3 flex items-center justify-between text-xs text-rose-300 animate-pulse">
          <div className="flex items-center gap-2 font-bold">
            <span className="text-sm">🚨</span>
            <span>ALERT THRESHOLD CROSSED AT 12.0s — Behavioral Risk: {riskScore}/100</span>
          </div>
          <span className="text-[10px] font-mono text-rose-400 bg-rose-950/80 px-2 py-0.5 rounded border border-rose-800 uppercase">
            Awaiting Staff Review
          </span>
        </div>
      )}
    </div>
  );
};
export default DemoTimeline;

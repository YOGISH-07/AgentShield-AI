import React, { useState } from 'react';
import { AlertItem } from '../services/api';
import { RiskBadge } from './RiskBadge';

interface AlertCardProps {
  alert: AlertItem;
  onReview: (alertId: string) => Promise<void>;
  onConfirm: (alertId: string) => Promise<void>;
  onDismiss: (alertId: string) => Promise<void>;
  isDemoAlertActive?: boolean;
  onSelectAlert?: (alert: AlertItem) => void;
}

export const AlertCard: React.FC<AlertCardProps> = ({
  alert,
  onReview,
  onConfirm,
  onDismiss,
  isDemoAlertActive = false,
  onSelectAlert,
}) => {
  const [loading, setLoading] = useState(false);

  const handleAction = async (actionFn: (id: string) => Promise<void>) => {
    setLoading(true);
    try {
      await actionFn(alert.alert_id);
    } catch (err) {
      console.error('Alert action error:', err);
    } finally {
      setLoading(false);
    }
  };

  const statusColors = {
    NEW: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30',
    UNDER_REVIEW: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
    CONFIRMED: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
    DISMISSED: 'bg-slate-700/30 text-slate-400 border-slate-700',
  };

  const isHighRisk = alert.risk_score >= 70;

  return (
    <div
      className={`bg-slate-900 border rounded-xl p-5 shadow-xl transition-all flex flex-col justify-between gap-4 ${
        isDemoAlertActive
          ? 'border-rose-500 ring-2 ring-rose-500/80 shadow-rose-500/30 shadow-2xl animate-pulse'
          : isHighRisk
          ? 'border-rose-500/40 shadow-rose-950/20 ring-1 ring-rose-500/20'
          : 'border-slate-800'
      }`}
    >
      <div>
        {/* Live Demo Highlight Banner */}
        {isDemoAlertActive && (
          <div className="mb-3 px-2.5 py-1 rounded bg-rose-600/30 border border-rose-500 text-[10px] font-extrabold text-rose-300 text-center uppercase tracking-widest flex items-center justify-center gap-1.5">
            <span className="animate-ping">🚨</span>
            <span>LIVE DEMO STREAM MATCH (12s–20s)</span>
          </div>
        )}

        {/* Header */}
        <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs font-bold text-cyan-400 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800/50">
              {alert.alert_id}
            </span>
            <span className="text-xs text-slate-400 font-semibold">{alert.camera_id}</span>
          </div>

          <span
            className={`px-2 py-0.5 text-[11px] font-bold rounded border uppercase tracking-wider ${
              statusColors[alert.status]
            }`}
          >
            {alert.status.replace('_', ' ')}
          </span>
        </div>

        {/* Title & Badge */}
        <div className="mb-3 space-y-1.5">
          <h4 className="text-sm font-extrabold text-slate-100 flex items-center gap-1.5">
            {isHighRisk ? '🚨 SUSPECTED RECORDING BEHAVIOR' : 'WATCH BEHAVIOR MONITOR'}
          </h4>
          <RiskBadge score={alert.risk_score} classification={alert.classification} />
        </div>

        {/* Target Tracks & Timestamp */}
        <div className="text-xs text-slate-400 space-y-1 my-3 bg-slate-950/40 p-2.5 rounded border border-slate-850">
          <div className="flex justify-between">
            <span>Anonymous Person Track:</span>
            <strong className="text-slate-200 font-mono">
              Person #{alert.person_track_id !== undefined && alert.person_track_id !== null ? alert.person_track_id : 'N/A'}
            </strong>
          </div>
          <div className="flex justify-between">
            <span>Anonymous Device Track:</span>
            <strong className="text-slate-200 font-mono">
              Phone #{alert.phone_track_id !== undefined && alert.phone_track_id !== null ? alert.phone_track_id : 'N/A'}
            </strong>
          </div>
          <div className="flex justify-between">
            <span>Stream Timestamp:</span>
            <span className="font-mono text-slate-300">
              {Math.floor((alert.timestamp_seconds || 0) / 60).toString().padStart(2, '0')}:
              {Math.floor((alert.timestamp_seconds || 0) % 60).toString().padStart(2, '0')}
            </span>
          </div>
        </div>

        {/* Observed Reasons List */}
        <div className="bg-slate-950/80 rounded-lg p-3 border border-slate-800 mb-3">
          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">
            Observed Behavioral Reasons:
          </p>
          <ul className="text-xs text-slate-300 space-y-1">
            {alert.reasons.map((reason, idx) => (
              <li key={idx} className="flex items-start gap-1.5">
                <span className="text-cyan-400 font-bold">•</span>
                <span>{reason}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Human Verification Badge */}
        <div className="px-2.5 py-1 rounded bg-amber-500/10 border border-amber-500/20 text-[10px] font-bold text-amber-400 text-center uppercase tracking-wider">
          HUMAN VERIFICATION REQUIRED
        </div>
      </div>

      {/* Interactive Workflow Buttons & Details View */}
      <div className="pt-3 border-t border-slate-800 flex flex-col gap-2">
        {onSelectAlert && (
          <button
            onClick={() => onSelectAlert(alert)}
            className="w-full py-1.5 rounded-lg bg-cyan-950/80 hover:bg-cyan-900/60 text-cyan-300 border border-cyan-800/80 font-bold text-xs transition-colors flex items-center justify-center gap-1.5"
          >
            <span>🔍</span> VIEW EXPLAINABLE EVIDENCE
          </button>
        )}

        <div className="flex items-center justify-end gap-2">
          {alert.status === 'NEW' && (
            <>
              <button
                onClick={() => handleAction(onReview)}
                disabled={loading}
                className="px-3.5 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs transition-colors shadow-sm disabled:opacity-50"
              >
                {loading ? '[ REVIEWING... ]' : '[ REVIEW ]'}
              </button>
              <button
                onClick={() => handleAction(onDismiss)}
                disabled={loading}
                className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs transition-colors border border-slate-700 disabled:opacity-50"
              >
                {loading ? '[ DISMISSING... ]' : '[ DISMISS ]'}
              </button>
            </>
          )}

          {alert.status === 'UNDER_REVIEW' && (
            <>
              <button
                onClick={() => handleAction(onConfirm)}
                disabled={loading}
                className="px-3.5 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs transition-colors shadow-sm disabled:opacity-50"
              >
                {loading ? '[ CONFIRMING... ]' : '[ CONFIRM INCIDENT ]'}
              </button>
              <button
                onClick={() => handleAction(onDismiss)}
                disabled={loading}
                className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs transition-colors border border-slate-700 disabled:opacity-50"
              >
                {loading ? '[ DISMISSING... ]' : '[ DISMISS ]'}
              </button>
            </>
          )}

          {(alert.status === 'CONFIRMED' || alert.status === 'DISMISSED') && (
            <span className="text-xs text-slate-500 font-mono italic">
              Workflow Action Completed
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

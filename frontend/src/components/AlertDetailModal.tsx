import React, { useState } from 'react';
import { AlertItem, IncidentItem } from '../services/api';
import { RiskBadge } from './RiskBadge';

interface AlertDetailModalProps {
  alert: AlertItem | null;
  matchingIncident?: IncidentItem | null;
  onClose: () => void;
  onReview: (alertId: string) => Promise<void>;
  onConfirm: (alertId: string) => Promise<void>;
  onDismiss: (alertId: string) => Promise<void>;
}

export const AlertDetailModal: React.FC<AlertDetailModalProps> = ({
  alert,
  matchingIncident,
  onClose,
  onReview,
  onConfirm,
  onDismiss,
}) => {
  const [loading, setLoading] = useState(false);

  if (!alert) return null;

  const handleAction = async (actionFn: (id: string) => Promise<void>) => {
    setLoading(true);
    try {
      await actionFn(alert.alert_id);
    } catch (err) {
      console.error('Action failed:', err);
    } finally {
      setLoading(false);
    }
  };

  // Map backend reasons to explicit explainable score contribution items
  const parseReasonEvidence = (reasons: string[]) => {
    const defaultItems = [
      { text: 'Mobile device detected', points: 15, match: false },
      { text: 'Associated with tracked person', points: 15, match: false },
      { text: 'Device inside screen region', points: 20, match: false },
      { text: 'Sustained behavior duration', points: 25, match: false },
      { text: 'Movement toward screen region', points: 10, match: false },
    ];

    const mapped = defaultItems.map((item) => {
      let isMatched = false;
      let scoreWeight = item.points;

      for (const r of reasons) {
        const lower = r.toLowerCase();
        if (item.text.includes('Mobile device') && lower.includes('mobile device')) {
          isMatched = true;
        } else if (item.text.includes('Associated') && (lower.includes('associated') || lower.includes('person'))) {
          isMatched = true;
        } else if (item.text.includes('screen region') && lower.includes('screen region')) {
          isMatched = true;
        } else if (item.text.includes('Sustained') && (lower.includes('persisted') || lower.includes('observed') || lower.includes('sustained'))) {
          isMatched = true;
          if (lower.includes('observed')) scoreWeight = 10;
        } else if (item.text.includes('Movement') && lower.includes('movement')) {
          isMatched = true;
        }
      }
      return { ...item, points: scoreWeight, match: isMatched };
    });

    // Also include any raw reason strings from backend not matched
    reasons.forEach((r) => {
      const lower = r.toLowerCase();
      if (
        !lower.includes('mobile device') &&
        !lower.includes('associated') &&
        !lower.includes('screen region') &&
        !lower.includes('persisted') &&
        !lower.includes('observed') &&
        !lower.includes('movement')
      ) {
        mapped.push({ text: r, points: 10, match: true });
      }
    });

    return mapped;
  };

  const evidenceItems = parseReasonEvidence(alert.reasons);

  // Risk progression steps
  const progressionSteps = [
    { label: 'NORMAL', minScore: 0, maxScore: 39, color: 'emerald' },
    { label: 'PHONE DETECTED', minScore: 15, maxScore: 39, color: 'cyan' },
    { label: 'WATCH', minScore: 40, maxScore: 69, color: 'amber' },
    { label: 'SUSPECTED RECORDING BEHAVIOR', minScore: 70, maxScore: 100, color: 'rose' },
  ];

  const currentStepIdx =
    alert.risk_score >= 70 ? 3 : alert.risk_score >= 40 ? 2 : alert.risk_score >= 15 ? 1 : 0;

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4 sm:p-6 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl max-w-3xl w-full shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Top Header Bar */}
        <div className="px-6 py-4 bg-slate-950/90 border-b border-slate-800 flex items-center justify-between sticky top-0 z-10">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 font-bold text-sm">
              🔍
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-extrabold text-slate-100 font-mono tracking-tight">
                  {alert.alert_id}
                </h3>
                <span className="text-xs font-mono text-cyan-400 bg-cyan-950/80 px-2 py-0.5 rounded border border-cyan-800">
                  {alert.camera_id}
                </span>
                <span className="px-2 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/30 text-[10px] font-extrabold text-cyan-400 uppercase">
                  DEMO MODE
                </span>
              </div>
              <p className="text-xs text-slate-400">Explainable Behavioral Evidence & Incident Audit</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 flex items-center justify-center font-bold text-base transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Modal Content Scroll Area */}
        <div className="p-6 space-y-6 overflow-y-auto flex-1 text-slate-200">
          {/* 1. Basic Alert Metadata Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-950/60 p-4 rounded-xl border border-slate-850 text-xs">
            <div>
              <span className="text-[10px] font-bold text-slate-500 uppercase block">Anonymous Person Track</span>
              <strong className="text-slate-100 font-mono text-sm">
                Person #{alert.person_track_id !== undefined && alert.person_track_id !== null ? alert.person_track_id : 'N/A'}
              </strong>
            </div>
            <div>
              <span className="text-[10px] font-bold text-slate-500 uppercase block">Anonymous Device Track</span>
              <strong className="text-slate-100 font-mono text-sm">
                Phone #{alert.phone_track_id !== undefined && alert.phone_track_id !== null ? alert.phone_track_id : 'N/A'}
              </strong>
            </div>
            <div>
              <span className="text-[10px] font-bold text-slate-500 uppercase block">Stream Timestamp</span>
              <span className="text-slate-200 font-mono text-sm">
                {Math.floor((alert.timestamp_seconds || 0) / 60).toString().padStart(2, '0')}:
                {Math.floor((alert.timestamp_seconds || 0) % 60).toString().padStart(2, '0')} ({(alert.timestamp_seconds || 0).toFixed(1)}s)
              </span>
            </div>
            <div>
              <span className="text-[10px] font-bold text-slate-500 uppercase block">Current Workflow State</span>
              <span className="font-bold text-cyan-400 font-mono text-xs uppercase">
                {alert.status.replace('_', ' ')}
              </span>
            </div>
          </div>

          {/* 2. Risk Score & Classification Summary */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-950/40 p-4 rounded-xl border border-slate-800">
            <RiskBadge score={alert.risk_score} classification={alert.classification} />
            <div className="text-xs text-slate-400">
              Computed by RiskEngine heuristic scoring rules ($0 - 100$).
            </div>
          </div>

          {/* 3. EXPLAINABLE EVIDENCE breakdown */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-cyan-400" />
              <h4 className="text-xs font-extrabold text-slate-100 uppercase tracking-wider">
                WHY WAS THIS ALERT GENERATED?
              </h4>
            </div>

            <div className="space-y-2">
              {evidenceItems.map((item, idx) => (
                <div
                  key={idx}
                  className={`p-3 rounded-lg border flex items-center justify-between text-xs transition-all ${
                    item.match
                      ? 'bg-slate-950 border-cyan-500/40 text-slate-200 shadow-sm'
                      : 'bg-slate-950/30 border-slate-800/60 text-slate-500 opacity-60'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <span
                      className={`w-5 h-5 rounded-full flex items-center justify-center font-bold text-xs ${
                        item.match ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40' : 'bg-slate-800 text-slate-600'
                      }`}
                    >
                      {item.match ? '✓' : '•'}
                    </span>
                    <span className="font-medium">{item.text}</span>
                  </div>

                  <span
                    className={`px-2 py-0.5 rounded font-mono font-bold text-xs ${
                      item.match
                        ? 'bg-cyan-500/10 text-cyan-300 border border-cyan-500/30'
                        : 'bg-slate-900 text-slate-600 border border-slate-800'
                    }`}
                  >
                    +{item.points}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* 4. Visual Risk Progression Flow Bar */}
          <div className="space-y-2">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
              Visual Behavioral Risk Progression
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-2">
              {progressionSteps.map((step, idx) => {
                const isActive = idx === currentStepIdx;
                const isPast = idx < currentStepIdx;

                return (
                  <div
                    key={step.label}
                    className={`p-3 rounded-lg border text-center transition-all flex flex-col justify-between ${
                      isActive
                        ? 'bg-rose-500/10 border-rose-500 text-rose-300 ring-1 ring-rose-500/50 shadow-lg'
                        : isPast
                        ? 'bg-cyan-950/40 border-cyan-800/60 text-cyan-400'
                        : 'bg-slate-950/40 border-slate-850 text-slate-600'
                    }`}
                  >
                    <span className="text-[10px] font-mono text-slate-500 block mb-1">
                      Step 0{idx + 1}
                    </span>
                    <strong className="text-[11px] font-bold uppercase tracking-wider block">
                      {step.label}
                    </strong>
                    <span className="text-[10px] font-mono mt-1 opacity-80">
                      Score: {step.minScore}–{step.maxScore}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* 5. Mandatory Privacy & Safety Section */}
          <div className="bg-cyan-950/40 border border-cyan-900/60 rounded-xl p-4 flex items-start gap-3">
            <span className="text-lg">🛡️</span>
            <div className="space-y-1">
              <h5 className="text-xs font-extrabold text-cyan-300 uppercase tracking-wider">
                HUMAN VERIFICATION REQUIRED
              </h5>
              <p className="text-xs text-cyan-200/90 leading-relaxed">
                CineGuard identifies observable behavioral signals. It does not identify people or determine intent. Staff verification is required before an incident is confirmed.
              </p>
            </div>
          </div>

          {/* 6. Incident Outcome & Workflow Progression */}
          <div className="space-y-3 bg-slate-950/60 p-4 rounded-xl border border-slate-800">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
              Incident Outcome & Workflow Lifecycle
            </h4>

            {/* Workflow Diagram */}
            <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 py-2 border-b border-slate-800">
              <span className="px-2 py-0.5 bg-slate-900 rounded border border-slate-800">ALERT</span>
              <span>→</span>
              <span className="px-2 py-0.5 bg-slate-900 rounded border border-slate-800">REVIEW</span>
              <span>→</span>
              <span className="px-2 py-0.5 bg-slate-900 rounded border border-slate-800">CONFIRM / DISMISS</span>
              <span>→</span>
              <span className="px-2 py-0.5 bg-slate-900 rounded border border-slate-800">INCIDENT RECORD</span>
            </div>

            {/* Outcome Display */}
            {alert.status === 'CONFIRMED' && (
              <div className="bg-rose-500/10 border border-rose-500/30 rounded-lg p-3 space-y-1 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-rose-400 uppercase">INCIDENT RECORD GENERATED</span>
                  <span className="font-mono text-rose-300 font-bold">
                    {matchingIncident?.incident_id || 'INC-CONFIRMED'}
                  </span>
                </div>
                <p className="text-slate-300 text-[11px]">
                  Verified by staff reviewer action: <code className="text-rose-300">{matchingIncident?.reviewer_action || 'Staff Verified'}</code>
                </p>
              </div>
            )}

            {alert.status === 'DISMISSED' && (
              <div className="bg-slate-800/40 border border-slate-700/60 rounded-lg p-3 text-xs text-slate-400 font-semibold flex items-center justify-between">
                <span>DISMISSED — NO INCIDENT CREATED</span>
                <span className="text-[10px] font-mono text-slate-500">Non-Critical / False Event</span>
              </div>
            )}

            {(alert.status === 'NEW' || alert.status === 'UNDER_REVIEW') && (
              <div className="pt-2 flex items-center justify-between">
                <span className="text-xs text-slate-400">Action Required by Authorized Staff:</span>
                <div className="flex items-center gap-2">
                  {alert.status === 'NEW' && (
                    <button
                      onClick={() => handleAction(onReview)}
                      disabled={loading}
                      className="px-3.5 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs transition-colors shadow-sm disabled:opacity-50"
                    >
                      {loading ? 'Processing...' : '[ REVIEW ]'}
                    </button>
                  )}
                  {alert.status === 'UNDER_REVIEW' && (
                    <button
                      onClick={() => handleAction(onConfirm)}
                      disabled={loading}
                      className="px-3.5 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs transition-colors shadow-sm disabled:opacity-50"
                    >
                      {loading ? 'Processing...' : '[ CONFIRM INCIDENT ]'}
                    </button>
                  )}
                  <button
                    onClick={() => handleAction(onDismiss)}
                    disabled={loading}
                    className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs transition-colors border border-slate-700 disabled:opacity-50"
                  >
                    {loading ? 'Processing...' : '[ DISMISS ]'}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3 bg-slate-950/90 border-t border-slate-800 flex items-center justify-between text-xs text-slate-500 sticky bottom-0">
          <span>CineGuard AI — TechNova Presentation Audit View</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold rounded-lg text-xs transition-colors"
          >
            Close Evidence Panel
          </button>
        </div>
      </div>
    </div>
  );
};
export default AlertDetailModal;

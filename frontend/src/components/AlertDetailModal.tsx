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

  const agentId = alert.agent_id || alert.camera_id || 'AGENT-07';
  const toolName = alert.tool_name || 'execute_sql_query';
  const targetResource = alert.target_resource || 'production_db.user_credentials';
  const payload = alert.action_payload || 'DROP TABLE user_credentials; -- EXFILTRATE';
  const decision = alert.decision || (alert.risk_score >= 70 ? 'BLOCK' : 'HUMAN APPROVAL');

  // Parse evidence rules
  const defaultItems = [
    { text: 'Baseline agent action risk', points: 15, match: false },
    { text: 'Target resource marked high-sensitivity', points: 20, match: false },
    { text: 'Destructive command payload pattern detected', points: 30, match: false },
    { text: 'High privilege escalation request', points: 20, match: false },
    { text: 'Adversarial prompt injection pattern', points: 20, match: false },
    { text: 'Unauthorized tool invocation attempt', points: 25, match: false },
    { text: 'Rapid automated tool execution loop', points: 10, match: false },
  ];

  const evidenceItems = defaultItems.map((item) => {
    let isMatched = false;
    for (const r of alert.reasons) {
      const lower = r.toLowerCase();
      if (item.text.includes('Baseline') && (lower.includes('baseline') || lower.includes('base'))) {
        isMatched = true;
      } else if (item.text.includes('Unauthorized') && (lower.includes('unauthorized') || lower.includes('tool'))) {
        isMatched = true;
      } else if (item.text.includes('high-sensitivity') && (lower.includes('sensitive') || lower.includes('resource'))) {
        isMatched = true;
      } else if (item.text.includes('Destructive') && (lower.includes('destructive') || lower.includes('drop') || lower.includes('delete'))) {
        isMatched = true;
      } else if (item.text.includes('privilege') && lower.includes('privilege')) {
        isMatched = true;
      } else if (item.text.includes('prompt injection') && (lower.includes('injection') || lower.includes('prompt'))) {
        isMatched = true;
      } else if (item.text.includes('execution loop') && (lower.includes('loop') || lower.includes('rapid'))) {
        isMatched = true;
      }
    }
    return { ...item, match: isMatched };
  });

  const progressionSteps = [
    { label: 'ALLOW (NORMAL)', minScore: 0, maxScore: 39 },
    { label: 'HUMAN APPROVAL REQUIRED', minScore: 40, maxScore: 69 },
    { label: 'BLOCK (CRITICAL VIOLATION)', minScore: 70, maxScore: 100 },
  ];

  const currentStepIdx = alert.risk_score >= 70 ? 2 : alert.risk_score >= 40 ? 1 : 0;

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4 sm:p-6 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl max-w-3xl w-full shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="px-6 py-4 bg-slate-950/90 border-b border-slate-800 flex items-center justify-between sticky top-0 z-10">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 font-bold text-sm">
              🛡️
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-extrabold text-slate-100 font-mono tracking-tight">
                  {alert.alert_id}
                </h3>
                <span className="text-xs font-mono text-purple-300 bg-purple-950/80 px-2 py-0.5 rounded border border-purple-800">
                  {agentId}
                </span>
                <span className="px-2 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/30 text-[10px] font-extrabold text-cyan-400 uppercase">
                  DEVHOST 2026 PS 2.1
                </span>
              </div>
              <p className="text-xs text-slate-400">Explainable AI Agent Safety Evidence & Interception Audit</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 flex items-center justify-center font-bold text-base transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Modal Scroll Content */}
        <div className="p-6 space-y-6 overflow-y-auto flex-1 text-slate-200">
          {/* Metadata Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-950/60 p-4 rounded-xl border border-slate-850 text-xs font-mono">
            <div>
              <span className="text-[10px] font-bold text-slate-500 uppercase block font-sans">MONITORED AGENT</span>
              <strong className="text-purple-300 text-sm">{agentId}</strong>
            </div>
            <div>
              <span className="text-[10px] font-bold text-slate-500 uppercase block font-sans">TOOL CALL</span>
              <strong className="text-cyan-300 text-sm">{toolName}</strong>
            </div>
            <div>
              <span className="text-[10px] font-bold text-slate-500 uppercase block font-sans">SAFETY DECISION</span>
              <span className={`text-xs font-bold font-sans uppercase ${decision === 'BLOCK' ? 'text-rose-400' : 'text-amber-400'}`}>
                {decision}
              </span>
            </div>
            <div>
              <span className="text-[10px] font-bold text-slate-500 uppercase block font-sans">WORKFLOW STATE</span>
              <span className="font-bold text-cyan-400 font-sans text-xs uppercase">
                {alert.status.replace('_', ' ')}
              </span>
            </div>
          </div>

          {/* Command Payload Terminal Box */}
          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 font-mono text-xs">
            <span className="text-slate-500 text-[11px] uppercase tracking-wider block mb-2 font-sans font-bold">
              TARGET RESOURCE & COMMAND PAYLOAD:
            </span>
            <div className="text-purple-300 text-xs mb-1">
              RESOURCE: <strong className="text-slate-100">{targetResource}</strong>
            </div>
            <div className="p-2.5 bg-slate-900 border border-slate-800 rounded text-red-300 font-bold overflow-x-auto">
              <code>$ {payload}</code>
            </div>
          </div>

          {/* Risk Score & Badge */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-950/40 p-4 rounded-xl border border-slate-800">
            <RiskBadge score={alert.risk_score} classification={alert.classification} />
            <div className="text-xs text-slate-400 font-sans">
              Calculated by AgentShield Safety Policy Scoring Rules (0–100).
            </div>
          </div>

          {/* Explainable Evidence */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-cyan-400" />
              <h4 className="text-xs font-extrabold text-slate-100 uppercase tracking-wider">
                WHY WAS THIS ACTION INTERCEPTED?
              </h4>
            </div>

            <div className="space-y-2 font-sans">
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

          {/* Risk Progression */}
          <div className="space-y-2 font-sans">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
              Safety Decision Progression
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
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

          {/* Workflow Outcome & Actions */}
          <div className="space-y-3 bg-slate-950/60 p-4 rounded-xl border border-slate-800 font-sans">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
              Human Interception & Operator Decision
            </h4>

            {alert.status === 'CONFIRMED' && (
              <div className="bg-rose-500/10 border border-rose-500/30 rounded-lg p-3 space-y-1 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-rose-400 uppercase">POLICY VIOLATION INCIDENT RECORDED</span>
                  <span className="font-mono text-rose-300 font-bold">
                    {matchingIncident?.incident_id || 'INC-CONFIRMED'}
                  </span>
                </div>
                <p className="text-slate-300 text-[11px]">
                  Operator decision: <code className="text-rose-300">{matchingIncident?.reviewer_action || 'Confirmed Violation'}</code>
                </p>
              </div>
            )}

            {alert.status === 'DISMISSED' && (
              <div className="bg-slate-800/40 border border-slate-700/60 rounded-lg p-3 text-xs text-slate-400 font-semibold flex items-center justify-between">
                <span>ACTION INTERCEPTED & BLOCKED</span>
                <span className="text-[10px] font-mono text-slate-500">Denied Execution</span>
              </div>
            )}

            {(alert.status === 'NEW' || alert.status === 'UNDER_REVIEW') && (
              <div className="pt-2 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">Operator Decision Controls:</span>
                  <div className="flex items-center gap-2">
                    {alert.status === 'NEW' && (
                      <button
                        onClick={() => handleAction(onReview)}
                        disabled={loading}
                        className="px-3.5 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs transition-colors shadow-sm disabled:opacity-50"
                      >
                        {loading ? 'Inspecting...' : '[ INSPECT EVIDENCE ]'}
                      </button>
                    )}
                    {alert.status === 'UNDER_REVIEW' && (
                      <button
                        onClick={() => handleAction(onConfirm)}
                        disabled={loading}
                        className="px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs transition-colors shadow-sm disabled:opacity-50"
                      >
                        {loading ? 'Overriding...' : '[ OVERRIDE & ALLOW ]'}
                      </button>
                    )}
                    <button
                      onClick={() => handleAction(onDismiss)}
                      disabled={loading}
                      className="px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs transition-colors disabled:opacity-50"
                    >
                      {loading ? 'Blocking...' : '[ BLOCK ACTION ]'}
                    </button>
                  </div>
                </div>
                <p className="text-[11px] text-amber-300/80 italic text-right font-sans">
                  Override requires explicit human authorization and is recorded in the audit trail.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3 bg-slate-950/90 border-t border-slate-800 flex items-center justify-between text-xs text-slate-500 sticky bottom-0 font-sans">
          <span>AgentShield AI — Safety Interception Panel</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold rounded-lg text-xs transition-colors"
          >
            Close Panel
          </button>
        </div>
      </div>
    </div>
  );
};
export default AlertDetailModal;

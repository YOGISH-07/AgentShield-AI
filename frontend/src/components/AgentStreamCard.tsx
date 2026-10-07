import React from 'react';
import { AgentActionStream } from '../services/api';
import { RiskBadge } from './RiskBadge';

interface AgentStreamCardProps {
  streamData: AgentActionStream | null;
  isPlaying: boolean;
  onStart: () => void;
  onPause: () => void;
  onRestart: () => void;
}

export const AgentStreamCard: React.FC<AgentStreamCardProps> = ({
  streamData,
  isPlaying,
  onStart,
  onPause,
  onRestart,
}) => {
  const agentId = streamData?.agent_id || 'CUSTOMER-SUPPORT-AI';
  const toolName = streamData?.tool_name || 'read_schema';
  const targetResource = streamData?.target_resource || 'public_catalog';
  const payload = streamData?.action_payload || 'SELECT table_name FROM information_schema.tables;';
  const riskScore = streamData?.risk_score ?? 15;
  const decision = streamData?.decision || 'ALLOW';

  const getDecisionBadge = (dec: string) => {
    if (dec === 'BLOCK') {
      return 'bg-red-500/20 text-red-400 border-red-500/40 animate-pulse';
    } else if (dec === 'HUMAN APPROVAL') {
      return 'bg-amber-500/20 text-amber-400 border-amber-500/40';
    }
    return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40';
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-xl backdrop-blur-sm relative overflow-hidden">
      {/* Top Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4 border-b border-slate-800 pb-3">
        <div className="flex items-center space-x-3">
          <div className="w-3 h-3 rounded-full bg-emerald-500 animate-ping" />
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            🤖 AI AGENT LIVE ACTION STREAM — <span className="font-mono text-cyan-400">{agentId}</span>
          </h2>
        </div>
        <div className="flex items-center space-x-3">
          <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${getDecisionBadge(decision)}`}>
            DECISION: {decision}
          </span>
          <RiskBadge score={riskScore} />
        </div>
      </div>

      {/* Terminal Telemetry Viewer */}
      <div className="bg-slate-950 font-mono text-xs text-slate-300 p-4 rounded-lg border border-slate-800 space-y-3 min-h-[220px] relative">
        <div className="flex items-center justify-between text-slate-500 text-[11px] border-b border-slate-800/80 pb-2">
          <span>MONITORED AGENT: {agentId}</span>
          <span>PROTOCOL: AgentShield Real-Time Control v1.0</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-slate-300">
          <div>
            <span className="text-slate-500">TOOL CALL:</span>{' '}
            <span className="text-cyan-300 font-bold">{toolName}</span>
          </div>
          <div>
            <span className="text-slate-500">TARGET RESOURCE:</span>{' '}
            <span className="text-purple-300 font-bold">{targetResource}</span>
          </div>
        </div>

        <div>
          <span className="text-slate-500">COMMAND / PAYLOAD INJECTION:</span>
          <div className="mt-1 p-2.5 bg-slate-900 border border-slate-800 rounded text-red-300 font-semibold text-xs overflow-x-auto">
            <code>$ {payload}</code>
          </div>
        </div>

        {/* Explainable Reasons Log */}
        {streamData?.reasons && streamData.reasons.length > 0 && (
          <div className="mt-2 pt-2 border-t border-slate-800/80">
            <span className="text-slate-500 text-[11px] font-sans font-bold">SAFETY REASONS EVALUATED:</span>
            <ul className="mt-1 space-y-1 text-[11px] text-amber-300/90 font-sans">
              {streamData.reasons.map((reason, idx) => (
                <li key={idx} className="flex items-center space-x-1.5">
                  <span className="text-amber-400">⚠️</span>
                  <span>{reason}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Interactive Controls */}
      <div className="mt-4 flex items-center justify-between">
        <div className="flex space-x-2">
          {!isPlaying ? (
            <button
              onClick={onStart}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-bold transition-colors shadow-lg shadow-emerald-900/20"
            >
              ▶ START AGENT DEMO
            </button>
          ) : (
            <button
              onClick={onPause}
              className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-xs font-bold transition-colors shadow-lg shadow-amber-900/20"
            >
              ⏸ PAUSE AGENT DEMO
            </button>
          )}
          <button
            onClick={onRestart}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-bold transition-colors border border-slate-700"
          >
            🔄 RESTART TIMELINE
          </button>
        </div>

        <div className="text-[11px] text-slate-400">
          <span className="font-semibold text-slate-300">Mandatory Verification:</span> Enabled (Human Operator Interception)
        </div>
      </div>
    </div>
  );
};

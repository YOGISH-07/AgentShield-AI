import React from 'react';

export const TechNovaSummary: React.FC = () => {
  const items = [
    { label: 'Action Telemetry Stream', value: '✓' },
    { label: 'Agent Tool Inspection', value: '✓' },
    { label: 'Payload Risk Scoring', value: '✓' },
    { label: 'Explainable Safety Reasons', value: '✓' },
    { label: 'Automated Decision (ALLOW/BLOCK)', value: '✓' },
    { label: 'Human Operator Interception', value: '✓' },
    { label: 'SQLite Incident Audit Trail', value: '✓' },
  ];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl max-w-md w-full font-sans">
      <div className="border-b border-slate-800 pb-3 mb-4">
        <h3 className="text-sm font-extrabold text-slate-100 tracking-wider font-mono uppercase flex items-center justify-between">
          <span>AGENTSHIELD AI</span>
          <span className="text-[10px] text-cyan-400 bg-cyan-950/80 px-2 py-0.5 rounded border border-cyan-800 font-mono">
            DEVHOST 2026 PS 2.1
          </span>
        </h3>
        <p className="text-[11px] text-slate-400 tracking-wider uppercase mt-1 font-semibold font-mono">
          AI AGENT SAFETY & INTERCEPTION CONTROL
        </p>
      </div>

      <div className="space-y-2 mb-5 font-mono text-xs">
        {items.map((item) => (
          <div key={item.label} className="flex items-center justify-between py-1 border-b border-slate-850/60 font-sans">
            <span className="text-slate-300 font-medium">{item.label}</span>
            <span className="font-bold text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800 font-mono">
              {item.value}
            </span>
          </div>
        ))}
      </div>

      <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-xs">
        <span className="font-bold text-slate-200">Safety & Human Control</span>
        <span className="font-extrabold text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded border border-emerald-500/30 font-mono">
          ✓ ENFORCED
        </span>
      </div>

      <p className="text-[10px] text-slate-500 mt-4 leading-relaxed italic border-t border-slate-850 pt-2">
        Notice: AgentShield AI monitors autonomous agent tool executions and intercepts risky operations to enforce human-in-the-loop safety governance.
      </p>
    </div>
  );
};
export default TechNovaSummary;

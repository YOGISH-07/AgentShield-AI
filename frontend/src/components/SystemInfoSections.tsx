import React from 'react';

export const HowItWorksSection: React.FC = () => {
  const steps = [
    { num: '01', title: 'Stream', desc: 'Real-time telemetry ingests AI Agent tool invocations, target resources, and parameters.' },
    { num: '02', title: 'Inspect', desc: 'Policy Engine inspects payloads for unauthorized tools, sensitive resources, and destructive commands.' },
    { num: '03', title: 'Analyze', desc: 'Prompt injection signals and execution frequency loop anomalies are evaluated.' },
    { num: '04', title: 'Score', desc: 'Explainable Risk Engine computes a 0–100 safety score with human-readable evidence.' },
    { num: '05', title: 'Decision', desc: 'Automated policy decisioning routes actions to ALLOW, HUMAN APPROVAL, or BLOCK.' },
    { num: '06', title: 'Interception', desc: 'Safety operator approves or blocks intercepted actions before database commitment.' },
  ];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg font-sans">
      <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider mb-4 flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-cyan-400" />
        How AgentShield AI Safety Engine Works
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {steps.map((step) => (
          <div
            key={step.num}
            className="bg-slate-950/60 border border-slate-800 rounded-lg p-4 flex flex-col justify-between"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-mono font-bold text-cyan-400 bg-cyan-950/80 px-2 py-0.5 rounded border border-cyan-800">
                {step.num}
              </span>
              <h4 className="text-xs font-bold text-slate-200 uppercase">{step.title}</h4>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">{step.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export const PrivacyNoticeSection: React.FC = () => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg font-sans">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider mb-1">
            🛡️ AI Agent Governance Guarantee
          </h4>
          <p className="text-xs text-slate-400">
            Explainable safety rules, zero black-box scoring, and mandatory human operator interception for high-risk actions.
          </p>
        </div>
        <div className="px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-xs font-semibold text-emerald-400 whitespace-nowrap">
          DevHost 2026 PS 2.1 Compliant
        </div>
      </div>
    </div>
  );
};

export const LimitationsSection: React.FC = () => {
  const limitations = [
    'Deterministic scenario simulator is used for DevHost 2026 MVP demonstration.',
    'Policy evaluation latency is <10ms for inline tool interception.',
    'Risk scoring uses transparent weighted rules (0–100).',
    'Human operator interception is strictly required for BLOCK / HUMAN APPROVAL decisions.',
    'SQLite audit database logs all policy violations and operator decisions.',
    'Fully extensible to custom LLM agent tool schemas and API gateways.',
  ];

  return (
    <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-5 shadow-lg font-sans">
      <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3">
        ⚠️ AgentShield AI — Evaluation Scope & Safety Guarantee
      </h4>
      <ul className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs text-slate-400">
        {limitations.map((item, idx) => (
          <li key={idx} className="flex items-start gap-2">
            <span className="text-slate-500 font-bold">•</span>
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
};

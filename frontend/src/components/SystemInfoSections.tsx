import React from 'react';

export const HowItWorksSection: React.FC = () => {
  const steps = [
    { num: '01', title: 'Detect', desc: 'YOLO object detection identifies people and mobile devices.' },
    { num: '02', title: 'Track', desc: 'Multi-object tracker maintains anonymous object continuity across frames.' },
    { num: '03', title: 'Analyze', desc: 'Spatial proximity and cinema screen region alignment features are calculated.' },
    { num: '04', title: 'Score', desc: 'Explainable risk engine combines observable signals into a 0–100 score.' },
    { num: '05', title: 'Alert', desc: 'Authorized security staff receive real-time explainable alerts on threshold crossing.' },
    { num: '06', title: 'Verify', desc: 'Human staff review evidence before confirming or dismissing any incident.' },
  ];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg">
      <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider mb-4 flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-cyan-400" />
        How CineGuard AI Works
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
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider mb-1">
            🔒 Privacy by Design Guarantee
          </h4>
          <p className="text-xs text-slate-400">
            No facial recognition, biometric extraction, personal names, or automatic legal accusations.
          </p>
        </div>
        <div className="px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-xs font-semibold text-emerald-400 whitespace-nowrap">
          Mandatory Human-in-the-Loop
        </div>
      </div>
    </div>
  );
};

export const LimitationsSection: React.FC = () => {
  const limitations = [
    'Synthetic test footage is used for computer-vision pipeline validation.',
    'Detection accuracy depends on camera angle, lighting, occlusion, and video resolution.',
    'YOLO object detection may miss small or partially occluded devices.',
    'Behavioral risk score is an engineering heuristic, not a probability or legal determination.',
    'Human verification is strictly required before an incident is confirmed.',
    'This working prototype does not establish legal wrongdoing.',
  ];

  return (
    <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-5 shadow-lg">
      <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3">
        ⚠️ Prototype Technical Limitations & Evaluation Scope
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

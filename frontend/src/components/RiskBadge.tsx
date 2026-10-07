import React from 'react';

interface RiskBadgeProps {
  score: number;
  classification?: string;
  showScoreText?: boolean;
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({
  score,
  classification,
  showScoreText = true,
}) => {
  let badgeStyle = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
  let label = classification || 'NORMAL';

  if (score >= 70) {
    badgeStyle = 'bg-rose-500/10 text-rose-400 border-rose-500/30';
    label = 'CRITICAL AGENT POLICY VIOLATION';
  } else if (score >= 40) {
    badgeStyle = 'bg-amber-500/10 text-amber-400 border-amber-500/30';
    label = 'EVALUATE';
  }

  return (
    <div className="flex flex-wrap items-center gap-2 font-sans">
      <span
        className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-bold border ${badgeStyle} tracking-wide uppercase font-mono`}
      >
        {label}
      </span>
      {showScoreText && (
        <span className="text-xs font-semibold text-slate-300">
          Safety Risk: <strong className="text-slate-100 font-mono">{score}/100</strong>
        </span>
      )}
    </div>
  );
};

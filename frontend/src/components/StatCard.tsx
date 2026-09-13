import React from 'react';

interface StatCardProps {
  label: string;
  value: string | number;
  subtext?: string;
  variant?: 'cyan' | 'amber' | 'emerald' | 'slate' | 'rose';
}

export const StatCard: React.FC<StatCardProps> = ({
  label,
  value,
  subtext,
  variant = 'cyan',
}) => {
  const borderColors = {
    cyan: 'border-cyan-500/20 hover:border-cyan-500/40 text-cyan-400',
    amber: 'border-amber-500/20 hover:border-amber-500/40 text-amber-400',
    emerald: 'border-emerald-500/20 hover:border-emerald-500/40 text-emerald-400',
    slate: 'border-slate-700/50 hover:border-slate-600 text-slate-300',
    rose: 'border-rose-500/20 hover:border-rose-500/40 text-rose-400',
  };

  return (
    <div
      className={`bg-slate-900/80 border ${borderColors[variant]} rounded-xl p-5 transition-all duration-200 shadow-lg`}
    >
      <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
        {label}
      </p>
      <div className="flex items-baseline justify-between">
        <h3 className="text-2xl lg:text-3xl font-extrabold text-slate-100 tracking-tight">
          {value}
        </h3>
      </div>
      {subtext && <p className="text-xs text-slate-500 mt-2">{subtext}</p>}
    </div>
  );
};

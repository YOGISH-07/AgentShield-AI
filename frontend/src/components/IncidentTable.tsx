import React from 'react';
import { IncidentItem } from '../services/api';

interface IncidentTableProps {
  incidents: IncidentItem[];
}

export const IncidentTable: React.FC<IncidentTableProps> = ({ incidents }) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg font-sans">
      <div className="px-5 py-4 bg-slate-950/80 border-b border-slate-800 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
            Verified Safety Interceptions & Violation Audit Log
          </h3>
          <p className="text-xs text-slate-400">
            Audit records confirmed through human operator safety verification workflow
          </p>
        </div>
        <span className="px-2.5 py-1 rounded-full bg-rose-500/10 border border-rose-500/30 text-xs font-bold text-rose-400">
          {incidents.length} Recorded Violations
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-slate-950/40 text-slate-400 uppercase font-semibold text-[11px] border-b border-slate-800 font-mono">
            <tr>
              <th className="px-5 py-3">Incident ID</th>
              <th className="px-5 py-3">Agent ID</th>
              <th className="px-5 py-3">Tool Call</th>
              <th className="px-5 py-3">Time</th>
              <th className="px-5 py-3">Risk Score</th>
              <th className="px-5 py-3">Verification Status</th>
              <th className="px-5 py-3">Operator Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono">
            {incidents.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-5 py-8 text-center text-slate-500 italic font-sans">
                  No policy violations confirmed in audit database.
                </td>
              </tr>
            ) : (
              incidents.map((inc) => (
                <tr key={inc.id} className="hover:bg-slate-850/50 transition-colors">
                  <td className="px-5 py-3 font-bold text-cyan-400">
                    {inc.incident_id}
                  </td>
                  <td className="px-5 py-3 font-semibold text-purple-300">
                    {inc.agent_id || inc.camera_id || 'AGENT-07'}
                  </td>
                  <td className="px-5 py-3 font-semibold text-cyan-300">
                    {inc.tool_name || 'execute_command'}
                  </td>
                  <td className="px-5 py-3 text-slate-400">
                    {typeof inc.timestamp_seconds === 'number' ? inc.timestamp_seconds.toFixed(1) : (inc.timestamp_seconds || '0')}s
                  </td>
                  <td className="px-5 py-3">
                    <span className="px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 font-bold border border-rose-500/30">
                      {inc.risk_score_at_alert}/100
                    </span>
                  </td>
                  <td className="px-5 py-3 font-sans">
                    <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-semibold border border-emerald-500/30">
                      {inc.verification_status}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-slate-300 font-sans">
                    {inc.reviewer_action}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

import React, { useEffect, useState, useCallback, useRef } from 'react';
import {
  fetchHealth,
  fetchStats,
  fetchAlerts,
  fetchIncidents,
  fetchAgentStream,
  reviewAlert,
  confirmAlert,
  dismissAlert,
  resetDemo,
  API_BASE_URL,
  OperationalStats,
  AlertItem,
  IncidentItem,
  AgentActionStream,
} from './services/api';
import { Header } from './components/Header';
import { StatCard } from './components/StatCard';
import { AgentStreamCard } from './components/AgentStreamCard';
import { AlertCard } from './components/AlertCard';
import { IncidentTable } from './components/IncidentTable';
import {
  HowItWorksSection,
  PrivacyNoticeSection,
  LimitationsSection,
} from './components/SystemInfoSections';
import { DemoTimeline, DemoPhaseInfo } from './components/DemoTimeline';
import { AlertDetailModal } from './components/AlertDetailModal';
import { TechNovaSummary } from './components/TechNovaSummary';

export const App: React.FC = () => {
  const [isOnline, setIsOnline] = useState<boolean>(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [stats, setStats] = useState<OperationalStats>({
    active_alerts: 0,
    total_alerts: 0,
    confirmed_incidents: 0,
    dismissed_alerts: 0,
    false_alarm_rate: 0,
  });
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [incidents, setIncidents] = useState<IncidentItem[]>([]);
  const [streamData, setStreamData] = useState<AgentActionStream | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedAlert, setSelectedAlert] = useState<AlertItem | null>(null);
  const [demoBannerMessage, setDemoBannerMessage] = useState<string | null>(null);

  // Demo simulation timer state
  const [elapsedTime, setElapsedTime] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const refreshDashboard = useCallback(async () => {
    try {
      await fetchHealth();
      setIsOnline(true);
      setError(null);

      const [statsData, alertsData, incidentsData, agentStreamData] = await Promise.all([
        fetchStats(),
        fetchAlerts(),
        fetchIncidents(),
        fetchAgentStream(elapsedTime),
      ]);

      setStats(statsData);
      setAlerts(alertsData);
      setIncidents(incidentsData);
      setStreamData(agentStreamData);
      setLastUpdated(new Date());

      // Update selectedAlert state if modal is open
      setSelectedAlert((prev) => {
        if (!prev) return null;
        const updated = alertsData.find((a) => a.alert_id === prev.alert_id);
        return updated || prev;
      });
    } catch (err) {
      setIsOnline(false);
      setError(`Cannot connect to AgentShield AI backend API (${API_BASE_URL}).`);
    }
  }, [elapsedTime]);

  useEffect(() => {
    refreshDashboard();
    const interval = setInterval(refreshDashboard, 3000);
    return () => clearInterval(interval);
  }, [refreshDashboard]);

  // Demo simulation timer loop
  useEffect(() => {
    if (isPlaying) {
      timerRef.current = setInterval(() => {
        setElapsedTime((prev) => {
          if (prev >= 25) {
            setIsPlaying(false);
            return 25;
          }
          return prev + 1.0;
        });
      }, 1000);
    } else if (timerRef.current) {
      clearInterval(timerRef.current);
    }

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isPlaying]);

  const handleReview = async (alertId: string) => {
    await reviewAlert(alertId);
    await refreshDashboard();
  };

  const handleConfirm = async (alertId: string) => {
    await confirmAlert(alertId);
    await refreshDashboard();
  };

  const handleDismiss = async (alertId: string) => {
    await dismissAlert(alertId);
    await refreshDashboard();
  };

  const handleResetDemoData = async () => {
    try {
      await resetDemo();
      setElapsedTime(0);
      setIsPlaying(false);
      await refreshDashboard();
      setDemoBannerMessage('🧹 AgentShield Demo Database Reset to Baseline Clean State');
      setTimeout(() => setDemoBannerMessage(null), 4000);
    } catch (err) {
      console.error('Reset error:', err);
    }
  };

  const handleStartPresentationDemo = async () => {
    await handleResetDemoData();
    setElapsedTime(0);
    setIsPlaying(true);
    setDemoBannerMessage('⚡ 25s AGENTSHIELD MVP DEMO STARTED — Synchronized Telemetry');
    setTimeout(() => setDemoBannerMessage(null), 5000);
  };

  const handleStartDemo = () => setIsPlaying(true);
  const handlePauseDemo = () => setIsPlaying(false);
  const handleRestartDemo = () => {
    setElapsedTime(0);
    setIsPlaying(true);
  };

  // Calculate live demo timeline phase from elapsedTime, consuming evaluated streamData
  const getDemoPhaseInfo = (): DemoPhaseInfo => {
    const t = elapsedTime;
    const dur = 25;

    // Use evaluated backend stream record if available
    const riskScore = streamData?.risk_score ?? (t >= 9 && t < 18 ? 85 : t >= 4 && t < 9 ? 55 : 15);
    const classification = streamData?.classification ?? (t >= 9 && t < 18 ? 'CRITICAL_VIOLATION' : t >= 4 && t < 9 ? 'EVALUATE' : 'NORMAL');
    const decision = streamData?.decision ?? (t >= 9 && t < 18 ? 'BLOCK' : t >= 4 && t < 9 ? 'HUMAN APPROVAL' : 'ALLOW');

    let phaseName = 'ALLOW (LOW RISK)';
    let description = 'CUSTOMER-SUPPORT-AI executing low-risk query read_schema on public_catalog.';
    let isAlertActive = false;

    if (t >= 4 && t < 9) {
      phaseName = 'HUMAN APPROVAL REQUIRED';
      description = 'DATA-OPS-AI requesting export_customer_data to external analytics S3 bucket.';
    } else if (t >= 9 && t < 18) {
      phaseName = 'CRITICAL VIOLATION / BLOCK';
      description = 'FINANCE-AI destructive payload pattern detected: DROP TABLE user_credentials; -- IGNORE SYSTEM PROMPT.';
      isAlertActive = decision === 'BLOCK' || riskScore >= 70;
    } else if (t >= 18) {
      phaseName = 'ALLOW (SAFE RESUME)';
      description = 'Safe logging action resumed by FINANCE-AI. Threat mitigated by AgentShield safety controls.';
    }

    return {
      timeSeconds: t,
      duration: dur,
      phaseName,
      riskScore,
      classification,
      description,
      isAlertActive,
      isPlaying,
    };
  };

  const demoPhaseInfo = getDemoPhaseInfo();

  const sortedAlerts = [...alerts].sort((a, b) => {
    const statusPriority: Record<string, number> = {
      NEW: 1,
      UNDER_REVIEW: 2,
      CONFIRMED: 3,
      DISMISSED: 4,
    };
    const prioA = statusPriority[a.status] || 99;
    const prioB = statusPriority[b.status] || 99;
    if (prioA !== prioB) return prioA - prioB;
    return b.risk_score - a.risk_score;
  });

  const selectedIncident = selectedAlert
    ? incidents.find((inc) => inc.alert_id === selectedAlert.alert_id)
    : null;

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 font-sans">
      {/* Header */}
      <Header isOnline={isOnline} lastUpdated={lastUpdated} />

      {/* Mandatory Human Interception Disclaimer Banner */}
      <div className="bg-cyan-950/60 border-b border-cyan-900/50 px-6 py-2.5 text-center text-xs font-semibold text-cyan-300">
        🛡️ AgentShield monitors AI agent actions. High-risk actions require human operator interception before execution.
      </div>

      {/* Demo Notification Toast */}
      {demoBannerMessage && (
        <div className="bg-cyan-500/20 border-b border-cyan-500/40 px-6 py-2 text-center text-xs font-extrabold text-cyan-200 animate-pulse">
          {demoBannerMessage}
        </div>
      )}

      <main className="flex-1 max-w-7xl w-full mx-auto p-6 space-y-8">
        {/* Backend Offline Warning Banner */}
        {!isOnline && (
          <div className="bg-rose-500/10 border border-rose-500/30 rounded-xl p-4 text-xs text-rose-300 flex items-center justify-between">
            <div>
              <strong className="font-bold">CONTROL BACKEND OFFLINE:</strong> {error}
            </div>
            <button
              onClick={refreshDashboard}
              aria-label="Retry connection to backend"
              className="px-3 py-1 bg-rose-600 hover:bg-rose-500 text-white rounded font-bold text-xs transition-colors"
            >
              Retry Connection
            </button>
          </div>
        )}

        {/* 1. Operational KPI Stat Cards */}
        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          <StatCard
            label="Active Interceptions"
            value={stats.active_alerts}
            subtext="Awaiting operator decision"
            variant="cyan"
          />
          <StatCard
            label="Total Agent Actions"
            value={stats.total_alerts}
            subtext="Monitored tool calls"
            variant="slate"
          />
          <StatCard
            label="Policy Violations"
            value={stats.confirmed_incidents}
            subtext="Confirmed & logged"
            variant="rose"
          />
          <StatCard
            label="Blocked Actions"
            value={stats.dismissed_alerts}
            subtext="Denied by operator"
            variant="emerald"
          />
          <StatCard
            label="Violation Rate"
            value={`${(stats.false_alarm_rate || 0).toFixed(1)}%`}
            subtext="Intercepted vs Total"
            variant="amber"
          />
        </section>

        {/* 2. Real-Time Demo Simulation Timeline HUD */}
        <section>
          <DemoTimeline
            demoState={demoPhaseInfo}
            onStartDemo={handleStartDemo}
            onPauseDemo={handlePauseDemo}
            onRestartDemo={handleRestartDemo}
            onStartPresentationDemo={handleStartPresentationDemo}
            onResetDemo={handleResetDemoData}
          />
        </section>

        {/* 3. AI Agent Stream Viewer */}
        <section>
          <AgentStreamCard
            streamData={streamData}
            isPlaying={isPlaying}
            onStart={handleStartDemo}
            onPause={handlePauseDemo}
            onRestart={handleRestartDemo}
          />
        </section>

        {/* 4. Agent Safety Interceptions & Operator Workflow */}
        <section className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
                Agent Safety Policy Interceptions
              </h2>
              <p className="text-xs text-slate-400">
                High-risk actions requiring human safety operator inspection and authorization.
              </p>
            </div>
            <span className="text-xs font-mono text-cyan-400 bg-cyan-950/60 px-3 py-1 rounded border border-cyan-800 self-start sm:self-auto">
              {alerts.filter((a) => a.status === 'NEW' || a.status === 'UNDER_REVIEW').length} Pending Operator Decision
            </span>
          </div>

          {sortedAlerts.length === 0 ? (
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-8 text-center text-slate-500 text-sm flex flex-col items-center justify-center gap-3">
              <p>No agent safety interceptions in database.</p>
              <button
                onClick={handleStartPresentationDemo}
                className="px-4 py-2 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs rounded-lg transition-colors"
              >
                ⚡ Start 25s AgentShield Demo
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {sortedAlerts.map((alert) => (
                <AlertCard
                  key={alert.alert_id}
                  alert={alert}
                  onReview={handleReview}
                  onConfirm={handleConfirm}
                  onDismiss={handleDismiss}
                  isDemoAlertActive={demoPhaseInfo.isAlertActive}
                  onSelectAlert={setSelectedAlert}
                />
              ))}
            </div>
          )}
        </section>

        {/* 5. Verified Incidents Table */}
        <section>
          <IncidentTable incidents={incidents} />
        </section>

        {/* 6. How AgentShield AI Works Section */}
        <section>
          <HowItWorksSection />
        </section>

        {/* 7. DevHost 2026 Evaluation Summary & Privacy Notice */}
        <section className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
          <TechNovaSummary />
          <div className="space-y-6">
            <PrivacyNoticeSection />
            <LimitationsSection />
          </div>
        </section>
      </main>

      {/* 8. Explainable Safety Evidence Modal */}
      {selectedAlert && (
        <AlertDetailModal
          alert={selectedAlert}
          matchingIncident={selectedIncident}
          onClose={() => setSelectedAlert(null)}
          onReview={handleReview}
          onConfirm={handleConfirm}
          onDismiss={handleDismiss}
        />
      )}

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-950 p-6 text-center text-xs text-slate-500 space-y-1 font-sans">
        <p className="font-semibold text-slate-400">AgentShield AI — DevHost 2026 PS 2.1 Working Prototype</p>
        <p className="text-[11px] text-slate-600 font-mono">
          AI Agent Telemetry $\rightarrow$ Tool Inspection $\rightarrow$ Risk Engine $\rightarrow$ Alert Manager $\rightarrow$ SQLite $\rightarrow$ FastAPI $\rightarrow$ React Control Dashboard.
        </p>
      </footer>
    </div>
  );
};

export default App;

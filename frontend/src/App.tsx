import React, { useEffect, useState, useCallback, useRef } from 'react';
import {
  fetchHealth,
  fetchStats,
  fetchAlerts,
  fetchIncidents,
  reviewAlert,
  confirmAlert,
  dismissAlert,
  resetDemo,
  API_BASE_URL,
  OperationalStats,
  AlertItem,
  IncidentItem,
} from './services/api';
import { Header } from './components/Header';
import { StatCard } from './components/StatCard';
import { CameraCard } from './components/CameraCard';
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
  const [error, setError] = useState<string | null>(null);
  const [selectedAlert, setSelectedAlert] = useState<AlertItem | null>(null);
  const [demoBannerMessage, setDemoBannerMessage] = useState<string | null>(null);

  // Demo simulation video sync state
  const videoRef = useRef<HTMLVideoElement>(null);
  const [videoTime, setVideoTime] = useState<number>(0);
  const [videoDuration, setVideoDuration] = useState<number>(25);
  const [isPlaying, setIsPlaying] = useState<boolean>(true);

  const refreshDashboard = useCallback(async () => {
    try {
      await fetchHealth();
      setIsOnline(true);
      setError(null);

      const [statsData, alertsData, incidentsData] = await Promise.all([
        fetchStats(),
        fetchAlerts(),
        fetchIncidents(),
      ]);

      setStats(statsData);
      setAlerts(alertsData);
      setIncidents(incidentsData);
      setLastUpdated(new Date());

      // Update selectedAlert state if modal is open
      setSelectedAlert((prev) => {
        if (!prev) return null;
        const updated = alertsData.find((a) => a.alert_id === prev.alert_id);
        return updated || prev;
      });
    } catch (err) {
      setIsOnline(false);
      setError(`Cannot connect to CineGuard AI backend API (${API_BASE_URL}).`);
    }
  }, []);

  useEffect(() => {
    refreshDashboard();
    const interval = setInterval(refreshDashboard, 5000);
    return () => clearInterval(interval);
  }, [refreshDashboard]);

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
      await refreshDashboard();
      setDemoBannerMessage('🧹 Prototype Demo Database Reset to Baseline Clean State');
      setTimeout(() => setDemoBannerMessage(null), 4000);
    } catch (err) {
      console.error('Reset error:', err);
    }
  };

  const handleStartPresentationDemo = async () => {
    await handleResetDemoData();
    if (videoRef.current) {
      videoRef.current.currentTime = 0;
      videoRef.current.play();
      setIsPlaying(true);
    }
    setDemoBannerMessage('⚡ ONE-CLICK PRESENTATION DEMO STARTED — Synchronized with Video Stream');
    setTimeout(() => setDemoBannerMessage(null), 5000);
  };

  // Demo Controls
  const handleTimeUpdate = (currentTime: number, duration: number) => {
    setVideoTime(currentTime);
    if (duration && !isNaN(duration)) {
      setVideoDuration(duration);
    }
  };

  const handleStartDemo = () => {
    if (videoRef.current) {
      videoRef.current.play();
      setIsPlaying(true);
    }
  };

  const handlePauseDemo = () => {
    if (videoRef.current) {
      videoRef.current.pause();
      setIsPlaying(false);
    }
  };

  const handleRestartDemo = () => {
    if (videoRef.current) {
      videoRef.current.currentTime = 0;
      videoRef.current.play();
      setIsPlaying(true);
    }
  };

  // Calculate live demo timeline phase from video currentTime
  const getDemoPhaseInfo = (): DemoPhaseInfo => {
    const t = videoTime;
    const dur = videoDuration || 25;
    let phaseName = 'NORMAL';
    let riskScore = 0;
    let classification = 'NORMAL';
    let description = 'Person detected in cinema seating area. Baseline behavior.';
    let isAlertActive = false;

    if (t >= 5 && t < 10) {
      phaseName = 'PHONE DETECTED';
      riskScore = 15;
      classification = 'NORMAL';
      description = 'Mobile device (Phone #1) detected near Person #4.';
    } else if (t >= 10 && t < 12) {
      phaseName = 'WATCH';
      riskScore = 45;
      classification = 'WATCH';
      description = 'Phone raised & aligned with screen region threshold.';
    } else if (t >= 12 && t < 20) {
      phaseName = 'SUSPECTED RECORDING BEHAVIOR';
      // Risk score curve peaking around ~15s
      const progress = (t - 12) / 8;
      riskScore = Math.min(85, Math.round(70 + Math.sin(progress * Math.PI) * 15));
      classification = 'SUSPECTED RECORDING BEHAVIOR';
      description = 'Phone aligned with screen region for > 2 seconds. Risk threshold >= 70 crossed.';
      isAlertActive = true;
    } else if (t >= 20) {
      phaseName = 'NORMAL';
      riskScore = 0;
      classification = 'NORMAL';
      description = 'Phone lowered / stowed away. Behavioral risk score returns to baseline.';
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
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100">
      {/* Header with DEMO MODE indicator */}
      <Header isOnline={isOnline} lastUpdated={lastUpdated} />

      {/* Mandatory Human-in-the-loop Disclaimer Banner */}
      <div className="bg-cyan-950/60 border-b border-cyan-900/50 px-6 py-2.5 text-center text-xs font-semibold text-cyan-300">
        🛡️ AI identifies potentially suspicious behavior. Human verification is required before an incident is confirmed.
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
              <strong className="font-bold">BACKEND OFFLINE:</strong> {error}
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
            label="Active Alerts"
            value={stats.active_alerts}
            subtext="Awaiting review / action"
            variant="cyan"
          />
          <StatCard
            label="Total Alerts"
            value={stats.total_alerts}
            subtext="Recorded events"
            variant="slate"
          />
          <StatCard
            label="Confirmed Incidents"
            value={stats.confirmed_incidents}
            subtext="Verified by staff"
            variant="rose"
          />
          <StatCard
            label="Dismissed Alerts"
            value={stats.dismissed_alerts}
            subtext="Non-critical / false"
            variant="emerald"
          />
          <StatCard
            label="False Alarm Rate"
            value={`${(stats.false_alarm_rate * 100).toFixed(1)}%`}
            subtext="Dismissed / Resolved"
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

        {/* 3. Surveillance Camera Grid */}
        <section>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
              Cinema Video Surveillance Monitoring
            </h2>
            <span className="text-xs text-slate-500 font-mono">
              DEMO STREAM FEED (videos/demo_output_risk_h264.mp4)
            </span>
          </div>
          <CameraCard videoRef={videoRef} onTimeUpdate={handleTimeUpdate} />
        </section>

        {/* 4. Behavioral Risk Alerts & Human Review Workflow */}
        <section className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
                Behavioral Risk Alerts
              </h2>
              <p className="text-xs text-slate-400">
                Suspected Recording Behavior events requiring human staff review.
                <span className="text-slate-500 italic ml-1">
                  (Behavioral risk score — not a probability or legal determination.)
                </span>
              </p>
            </div>
            <span className="text-xs font-mono text-cyan-400 bg-cyan-950/60 px-3 py-1 rounded border border-cyan-800 self-start sm:self-auto">
              {alerts.filter((a) => a.status === 'NEW' || a.status === 'UNDER_REVIEW').length} Pending Action
            </span>
          </div>

          {sortedAlerts.length === 0 ? (
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-8 text-center text-slate-500 text-sm flex flex-col items-center justify-center gap-3">
              <p>No alert events found in SQLite database.</p>
              <button
                onClick={handleStartPresentationDemo}
                className="px-4 py-2 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs rounded-lg transition-colors"
              >
                ⚡ Start One-Click Presentation Demo
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

        {/* 6. How CineGuard AI Works Section */}
        <section>
          <HowItWorksSection />
        </section>

        {/* 7. TechNova Evaluation Summary & Privacy Notice */}
        <section className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
          <TechNovaSummary />
          <div className="space-y-6">
            <PrivacyNoticeSection />
            <LimitationsSection />
          </div>
        </section>
      </main>

      {/* 8. Explainable Evidence & Incident Detail Modal */}
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
      <footer className="border-t border-slate-800 bg-slate-950 p-6 text-center text-xs text-slate-500 space-y-1">
        <p className="font-semibold text-slate-400">CineGuard AI — TechNova Working Prototype</p>
        <p className="text-[11px] text-slate-600">
          Computer Vision Surveillance Architecture: YOLOv8 $\rightarrow$ Object Tracking $\rightarrow$ Behavior Analysis $\rightarrow$ Risk Engine $\rightarrow$ Alert Manager $\rightarrow$ SQLite $\rightarrow$ FastAPI $\rightarrow$ React Dashboard.
        </p>
      </footer>
    </div>
  );
};

export default App;

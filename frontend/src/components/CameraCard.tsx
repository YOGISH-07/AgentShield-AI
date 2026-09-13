import React, { useState } from 'react';
import { getVideoUrl } from '../services/api';

interface CameraCardProps {
  onTimeUpdate?: (currentTime: number, duration: number) => void;
  videoRef?: React.RefObject<HTMLVideoElement>;
}

export const CameraCard: React.FC<CameraCardProps> = ({ onTimeUpdate, videoRef }) => {
  const videoSrc = getVideoUrl();
  const [videoError, setVideoError] = useState(false);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* CAM-01 (Demo Camera Feed) */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg flex flex-col">
        <div className="px-4 py-3 bg-slate-950/80 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span
              className={`w-2 h-2 rounded-full ${
                videoError ? 'bg-rose-500' : 'bg-emerald-500 animate-pulse'
              }`}
            />
            <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
              CAM-01 — DEMO CAMERA FEED
            </h3>
          </div>
          <span className="px-2 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/30 text-[10px] font-semibold text-cyan-400">
            PROTOTYPE INPUT
          </span>
        </div>

        <div className="relative bg-black aspect-video flex items-center justify-center overflow-hidden group">
          <video
            ref={videoRef}
            src={videoSrc}
            controls
            autoPlay
            loop
            muted
            playsInline
            preload="metadata"
            onTimeUpdate={(e) =>
              onTimeUpdate?.(e.currentTarget.currentTime, e.currentTarget.duration)
            }
            onError={() => setVideoError(true)}
            onLoadedData={() => setVideoError(false)}
            className="w-full h-full object-contain"
          />

          {/* Visible Fallback / Error State */}
          {videoError && (
            <div className="absolute inset-0 bg-slate-950/95 flex flex-col items-center justify-center p-6 text-center z-10">
              <div className="w-10 h-10 rounded-full bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-rose-400 mb-2 font-bold text-sm">
                !
              </div>
              <p className="text-xs font-bold text-rose-300 uppercase tracking-wider">
                Surveillance Feed Disconnected
              </p>
              <p className="text-[11px] text-slate-400 mt-1 max-w-xs">
                Unable to load demonstration video stream from{' '}
                <code className="text-slate-300 font-mono">/api/video/risk</code>.
              </p>
              <button
                onClick={() => setVideoError(false)}
                className="mt-3 px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded text-xs font-semibold border border-slate-700 transition-colors"
              >
                Retry Video Stream
              </button>
            </div>
          )}

          {/* Watermark Overlay */}
          <div className="absolute top-3 right-3 px-2 py-1 rounded bg-slate-950/70 backdrop-blur border border-slate-700 text-[10px] font-mono text-slate-300 pointer-events-none z-20">
            CineGuard AI
          </div>
        </div>

        <div className="px-4 py-2 bg-slate-950/40 text-[11px] text-slate-400 flex justify-between items-center">
          <span>Targeting Screen Region & Phone Proximity</span>
          <span className="font-mono text-slate-500">640x480 @ 30fps</span>
        </div>
      </div>

      {/* CAM-02 (No Signal) */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg flex flex-col">
        <div className="px-4 py-3 bg-slate-950/80 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-slate-600" />
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              CAM-02 — NO SIGNAL
            </h3>
          </div>
          <span className="px-2 py-0.5 rounded bg-slate-800 text-[10px] font-semibold text-slate-400">
            OFFLINE
          </span>
        </div>

        <div className="relative bg-slate-950 aspect-video flex flex-col items-center justify-center p-6 text-center border-dashed border-slate-800">
          <div className="w-12 h-12 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-600 mb-3 font-mono font-bold">
            02
          </div>
          <p className="text-sm font-semibold text-slate-400">CAM-02 DISCONNECTED</p>
          <p className="text-xs text-slate-600 mt-1 max-w-xs">
            No input video channel configured for secondary cinema hall.
          </p>
        </div>

        <div className="px-4 py-2 bg-slate-950/40 text-[11px] text-slate-500 flex justify-between items-center">
          <span>Channel 02</span>
          <span className="font-mono text-slate-600">INACTIVE</span>
        </div>
      </div>
    </div>
  );
};

export default CameraCard;

import React from "react";
import { AppTab, BiometricPalmSample } from "../types";
import {
  Scan,
  Crop,
  Sparkles,
  ShieldCheck,
  Fingerprint,
  SplitSquareVertical,
  Database,
  Bot,
  Download,
  Upload,
} from "lucide-react";

interface HeaderProps {
  activeTab: AppTab;
  setActiveTab: (tab: AppTab) => void;
  activeSample: BiometricPalmSample | null;
  onOpenExport: () => void;
  onOpenUploadModal: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  setActiveTab,
  activeSample,
  onOpenExport,
  onOpenUploadModal,
}) => {
  const tabs: { id: AppTab; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
    { id: "overview", label: "Acquisition", icon: Scan },
    { id: "roi_extraction", label: "ROI & Landmarks", icon: Crop },
    { id: "enhancement", label: "Enhancement", icon: Sparkles },
    { id: "quality", label: "Quality (PQI)", icon: ShieldCheck },
    { id: "recognition", label: "Recognition (1:1 / 1:N)", icon: Fingerprint },
    { id: "comparison", label: "Comparison", icon: SplitSquareVertical },
    { id: "benchmarks", label: "Benchmarks", icon: Database },
    { id: "ai_assistant", label: "AI Co-Pilot", icon: Bot },
  ];

  return (
    <header className="sticky top-0 z-40 bg-[#0A0A0B]/95 backdrop-blur-md border-b border-white/10 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-18">
          {/* Logo & Title */}
          <div className="flex items-center space-x-3.5">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 via-indigo-500 to-fuchsia-500 p-0.5 shadow-lg shadow-cyan-500/10 flex items-center justify-center">
              <div className="w-full h-full bg-[#0A0A0B] rounded-[10px] flex items-center justify-center">
                <Scan className="w-5 h-5 text-cyan-400 stroke-[2.5]" />
              </div>
            </div>
            <div>
              <div className="flex items-center space-x-2.5">
                <span className="font-black text-xl text-white tracking-tight uppercase">PALMRESEARCH</span>
                <span className="text-[10px] font-mono font-bold tracking-widest px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 uppercase">
                  PhD v2.4
                </span>
              </div>
              <p className="text-[11px] font-medium text-zinc-400 hidden sm:block tracking-wide uppercase">
                Biometrics & Feature Engineering Platform
              </p>
            </div>
          </div>

          {/* Active sample pill & Actions */}
          <div className="flex items-center space-x-3">
            {activeSample ? (
              <div className="hidden md:flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-zinc-900/90 border border-white/10 text-xs">
                <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shadow-sm shadow-emerald-400/50" />
                <span className="text-[10px] font-mono uppercase font-bold tracking-wider text-zinc-400">SAMPLE:</span>
                <span className="font-mono text-white font-bold tracking-tight truncate max-w-[150px]">
                  {activeSample.subjectId}
                </span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-white/5 text-zinc-300 border border-white/10 uppercase">
                  {activeSample.datasetName.split(" ")[0]}
                </span>
              </div>
            ) : (
              <div className="hidden md:flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-zinc-900 border border-white/10 text-xs text-zinc-500 font-mono uppercase font-bold">
                <span>NO SAMPLE LOADED</span>
              </div>
            )}

            <button
              onClick={onOpenUploadModal}
              className="inline-flex items-center space-x-1.5 px-3.5 py-2 rounded-lg bg-zinc-900 hover:bg-zinc-800 border border-white/10 hover:border-white/20 text-zinc-200 text-xs font-bold uppercase tracking-wider transition cursor-pointer"
            >
              <Upload className="w-3.5 h-3.5 text-cyan-400 stroke-[2.5]" />
              <span>LOAD PALM</span>
            </button>

            <button
              onClick={onOpenExport}
              disabled={!activeSample}
              className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 disabled:opacity-40 disabled:cursor-not-allowed text-black font-black text-xs uppercase tracking-wider shadow-lg shadow-cyan-500/20 transition cursor-pointer"
            >
              <Download className="w-3.5 h-3.5 stroke-[2.5]" />
              <span className="hidden sm:inline">EXPORT DATA</span>
            </button>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex space-x-1 overflow-x-auto py-2.5 scrollbar-none border-t border-white/10">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wider whitespace-nowrap transition cursor-pointer ${
                  isActive
                    ? "bg-white text-black shadow-md"
                    : "text-zinc-400 hover:text-white hover:bg-white/5"
                }`}
              >
                <Icon className={`w-3.5 h-3.5 stroke-[2.5] ${isActive ? "text-black" : "text-zinc-400"}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
};

import React, { useState, useRef } from "react";
import { BiometricPalmSample } from "../types";
import { BENCHMARK_DATASETS } from "../data/benchmarkDatasets";
import {
  SplitSquareVertical,
  Columns,
  Layers,
  Crosshair,
  Sliders,
  CheckCircle2,
  XCircle,
} from "lucide-react";

interface ComparisonViewerProps {
  primarySample: BiometricPalmSample;
}

export const ComparisonViewer: React.FC<ComparisonViewerProps> = ({
  primarySample,
}) => {
  const [secondarySampleId, setSecondarySampleId] = useState<string>("");
  const [comparisonMode, setComparisonMode] = useState<"split" | "side_by_side" | "diff_overlay">("split");
  const [sliderPos, setSliderPos] = useState<number>(50); // percentage 0 - 100
  const [viewType, setViewType] = useState<"compcode" | "roi" | "source">("compcode");

  // Collect all benchmark samples
  const allSamples: BiometricPalmSample[] = [];
  BENCHMARK_DATASETS.forEach((ds) => {
    ds.samples.forEach((s) => allSamples.push(s));
  });

  // Default secondary sample
  const secondarySample =
    allSamples.find((s) => s.id === secondarySampleId) ||
    allSamples.find((s) => s.subjectId === primarySample.subjectId && s.id !== primarySample.id) ||
    allSamples[1];

  const getImageForView = (sample: BiometricPalmSample) => {
    if (viewType === "compcode") return sample.compCodeImageUrl || sample.roiImageDataUrl || sample.sourceImageUrl;
    if (viewType === "roi") return sample.roiImageDataUrl || sample.sourceImageUrl;
    return sample.sourceImageUrl;
  };

  const imgA = getImageForView(primarySample);
  const imgB = secondarySample ? getImageForView(secondarySample) : imgA;

  const isGenuinePair = secondarySample?.subjectId === primarySample.subjectId;

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-[#121318] border border-white/10 p-5 rounded-2xl shadow-xl">
        <div>
          <div className="flex items-center space-x-2.5 mb-1">
            <h2 className="text-xl font-black tracking-tight text-white uppercase">
              Dual Image Comparison & Ridge Inspection
            </h2>
            <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 font-mono font-bold uppercase tracking-widest">
              PIXEL-BY-PIXEL VERIFICATION
            </span>
          </div>
          <p className="text-xs font-medium text-zinc-400">
            Compare two palmprint samples across sessions or subjects using split wipe, side-by-side sync, and feature overlays.
          </p>
        </div>

        {/* View Mode Controls */}
        <div className="flex items-center space-x-2 font-mono">
          {/* Layer type */}
          <div className="flex items-center space-x-1 bg-black/50 p-1.5 rounded-xl border border-white/10 text-xs uppercase font-bold">
            <button
              onClick={() => setViewType("compcode")}
              className={`px-3 py-1.5 rounded-lg transition cursor-pointer ${
                viewType === "compcode" ? "bg-white text-black font-black shadow-md" : "text-zinc-400 hover:text-white"
              }`}
            >
              CompCode
            </button>
            <button
              onClick={() => setViewType("roi")}
              className={`px-3 py-1.5 rounded-lg transition cursor-pointer ${
                viewType === "roi" ? "bg-white text-black font-black shadow-md" : "text-zinc-400 hover:text-white"
              }`}
            >
              ROI Window
            </button>
            <button
              onClick={() => setViewType("source")}
              className={`px-3 py-1.5 rounded-lg transition cursor-pointer ${
                viewType === "source" ? "bg-white text-black font-black shadow-md" : "text-zinc-400 hover:text-white"
              }`}
            >
              Full Palm
            </button>
          </div>

          {/* Display style */}
          <div className="flex items-center space-x-1 bg-black/50 p-1.5 rounded-xl border border-white/10 text-xs">
            <button
              onClick={() => setComparisonMode("split")}
              className={`p-2 rounded-lg transition cursor-pointer ${
                comparisonMode === "split" ? "bg-cyan-500 text-black shadow-md" : "text-zinc-400 hover:text-white"
              }`}
              title="Split Slider"
            >
              <SplitSquareVertical className="w-4 h-4 stroke-[2.5]" />
            </button>
            <button
              onClick={() => setComparisonMode("side_by_side")}
              className={`p-2 rounded-lg transition cursor-pointer ${
                comparisonMode === "side_by_side" ? "bg-cyan-500 text-black shadow-md" : "text-zinc-400 hover:text-white"
              }`}
              title="Side by Side"
            >
              <Columns className="w-4 h-4 stroke-[2.5]" />
            </button>
            <button
              onClick={() => setComparisonMode("diff_overlay")}
              className={`p-2 rounded-lg transition cursor-pointer ${
                comparisonMode === "diff_overlay" ? "bg-cyan-500 text-black shadow-md" : "text-zinc-400 hover:text-white"
              }`}
              title="Difference Overlay"
            >
              <Layers className="w-4 h-4 stroke-[2.5]" />
            </button>
          </div>
        </div>
      </div>

      {/* Target Sample Quick Picker */}
      <div className="bg-[#121318] border border-white/10 rounded-2xl p-5 shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center space-x-3 text-xs">
          <span className="text-zinc-300 font-black font-mono uppercase tracking-wider">COMPARE SAMPLE A (ACTIVE) WITH SAMPLE B:</span>
          <select
            value={secondarySample?.id || ""}
            onChange={(e) => setSecondarySampleId(e.target.value)}
            className="bg-black/60 border border-white/10 rounded-xl px-3 py-2 text-xs text-white font-mono font-bold focus:outline-none focus:border-cyan-400 shadow-inner"
          >
            {allSamples.map((s) => (
              <option key={s.id} value={s.id} className="bg-zinc-900 text-white">
                {s.subjectId} - Session {s.session} ({s.datasetName})
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center space-x-2 text-xs font-mono">
          {isGenuinePair ? (
            <span className="flex items-center space-x-1.5 px-3 py-1.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-bold uppercase tracking-wider">
              <CheckCircle2 className="w-4 h-4 stroke-[2.5]" />
              <span>GENUINE PAIR (INTRA-CLASS)</span>
            </span>
          ) : (
            <span className="flex items-center space-x-1.5 px-3 py-1.5 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/30 font-bold uppercase tracking-wider">
              <XCircle className="w-4 h-4 stroke-[2.5]" />
              <span>IMPOSTOR PAIR (INTER-CLASS)</span>
            </span>
          )}
        </div>
      </div>

      {/* Main Comparison Canvas Stage */}
      <div className="bg-[#121318] border border-white/10 rounded-2xl p-8 shadow-xl flex flex-col items-center justify-center min-h-[420px]">
        {/* Split Slider Mode */}
        {comparisonMode === "split" && (
          <div className="relative w-full max-w-lg aspect-square rounded-2xl overflow-hidden border-2 border-white/20 bg-black shadow-2xl select-none">
            {/* Background Image (Sample B) */}
            <img
              src={imgB}
              alt="Sample B"
              className="absolute inset-0 w-full h-full object-contain pointer-events-none"
            />
            <div className="absolute top-3 right-3 bg-black/80 backdrop-blur px-3 py-1 rounded-xl text-[10px] font-mono font-bold uppercase text-indigo-400 border border-indigo-500/30">
              Sample B: {secondarySample?.subjectId} (S{secondarySample?.session})
            </div>

            {/* Foreground Image (Sample A clipped) */}
            <div
              className="absolute inset-0 overflow-hidden pointer-events-none"
              style={{ width: `${sliderPos}%` }}
            >
              <img
                src={imgA}
                alt="Sample A"
                className="absolute inset-0 max-w-none w-[512px] h-[512px] object-contain pointer-events-none"
                style={{ width: "100%", height: "100%" }}
              />
              <div className="absolute top-3 left-3 bg-black/80 backdrop-blur px-3 py-1 rounded-xl text-[10px] font-mono font-bold uppercase text-cyan-400 border border-cyan-500/30">
                Sample A: {primarySample.subjectId} (S{primarySample.session})
              </div>
            </div>

            {/* Vertical Divider line */}
            <div
              className="absolute top-0 bottom-0 w-0.5 bg-cyan-400 shadow-[0_0_12px_rgba(34,211,238,0.8)] pointer-events-none flex items-center justify-center"
              style={{ left: `${sliderPos}%` }}
            >
              <div className="w-8 h-8 rounded-full bg-cyan-400 text-black font-bold shadow-2xl flex items-center justify-center -ml-4">
                <SplitSquareVertical className="w-4 h-4 stroke-[2.5]" />
              </div>
            </div>

            {/* Slider Input overlay */}
            <input
              type="range"
              min="0"
              max="100"
              value={sliderPos}
              onChange={(e) => setSliderPos(parseFloat(e.target.value))}
              className="absolute inset-0 w-full h-full opacity-0 cursor-ew-resize z-20"
            />
          </div>
        )}

        {/* Side-by-Side Mode */}
        {comparisonMode === "side_by_side" && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-3xl">
            <div className="flex flex-col items-center bg-black/50 p-5 rounded-2xl border border-white/10 space-y-3">
              <span className="text-xs font-mono text-cyan-400 font-bold uppercase tracking-wider">
                SAMPLE A: {primarySample.subjectId} (SESSION {primarySample.session})
              </span>
              <img
                src={imgA}
                alt="Sample A"
                className="w-64 h-64 rounded-xl object-contain border-2 border-cyan-400 bg-black p-1 shadow-lg"
              />
            </div>
            <div className="flex flex-col items-center bg-black/50 p-5 rounded-2xl border border-white/10 space-y-3">
              <span className="text-xs font-mono text-indigo-400 font-bold uppercase tracking-wider">
                SAMPLE B: {secondarySample?.subjectId} (SESSION {secondarySample?.session})
              </span>
              <img
                src={imgB}
                alt="Sample B"
                className="w-64 h-64 rounded-xl object-contain border-2 border-indigo-400 bg-black p-1 shadow-lg"
              />
            </div>
          </div>
        )}

        {/* Difference Overlay Mode */}
        {comparisonMode === "diff_overlay" && (
          <div className="flex flex-col items-center space-y-4 max-w-md w-full">
            <div className="relative w-72 h-72 rounded-2xl overflow-hidden border-2 border-white/20 bg-black shadow-2xl">
              <img
                src={imgA}
                alt="Base"
                className="absolute inset-0 w-full h-full object-contain"
              />
              <img
                src={imgB}
                alt="Overlay"
                className="absolute inset-0 w-full h-full object-contain opacity-50 mix-blend-difference"
              />
            </div>
            <p className="text-xs text-zinc-400 text-center font-mono">
              Difference blend mode: Identical overlapping ridges cancel to black; divergent or displaced ridges appear bright.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

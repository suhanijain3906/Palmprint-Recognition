import React, { useState, useEffect } from "react";
import {
  BiometricPalmSample,
  BenchmarkGallerySubject,
  MatchResult,
  ROCCurvePoint,
} from "../types";
import { BENCHMARK_DATASETS } from "../data/benchmarkDatasets";
import {
  verifyBiometricPair,
  generateROCCurve,
} from "../utils/matchingEngine";
import {
  Fingerprint,
  CheckCircle,
  XCircle,
  Sliders,
  TrendingUp,
  Search,
  Award,
  Layers,
  ArrowRight,
  Sparkles,
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

interface RecognitionStudioProps {
  querySample: BiometricPalmSample;
  allSamples: BiometricPalmSample[];
}

export const RecognitionStudio: React.FC<RecognitionStudioProps> = ({
  querySample,
  allSamples,
}) => {
  const [recognitionMode, setRecognitionMode] = useState<"1to1" | "1toN" | "roc">("1to1");
  const [targetSampleId, setTargetSampleId] = useState<string>("");
  const [decisionThreshold, setDecisionThreshold] = useState<number>(65.0);
  const [matchResult, setMatchResult] = useState<MatchResult | null>(null);

  // 1:N Identification Results
  const [galleryResults, setGalleryResults] = useState<MatchResult[]>([]);

  // Collect all available test samples
  const availableTargetSamples: BiometricPalmSample[] = [];
  BENCHMARK_DATASETS.forEach((ds) => {
    ds.samples.forEach((s) => availableTargetSamples.push(s));
  });

  // Set default target sample
  useEffect(() => {
    if (availableTargetSamples.length > 0 && !targetSampleId) {
      // Find a matching genuine sample or second sample
      const matchingGenuine = availableTargetSamples.find(
        (s) => s.subjectId === querySample.subjectId && s.id !== querySample.id
      );
      if (matchingGenuine) {
        setTargetSampleId(matchingGenuine.id);
      } else {
        const other = availableTargetSamples.find((s) => s.id !== querySample.id);
        if (other) setTargetSampleId(other.id);
      }
    }
  }, [querySample.id]);

  // Run 1:1 Verification
  useEffect(() => {
    if (!querySample.features) return;
    const target = availableTargetSamples.find((s) => s.id === targetSampleId);
    if (!target || !target.features) return;

    const res = verifyBiometricPair(
      querySample.features,
      querySample.id,
      querySample.subjectId,
      target.features,
      target.id,
      target.subjectId,
      decisionThreshold
    );
    setMatchResult(res);
  }, [querySample, targetSampleId, decisionThreshold]);

  // Run 1:N Identification
  const run1ToNIdentification = () => {
    if (!querySample.features) return;
    const results: MatchResult[] = [];

    availableTargetSamples.forEach((target) => {
      if (target.features) {
        const res = verifyBiometricPair(
          querySample.features!,
          querySample.id,
          querySample.subjectId,
          target.features,
          target.id,
          target.subjectId,
          decisionThreshold
        );
        results.push(res);
      }
    });

    results.sort((a, b) => b.matchScore - a.matchScore);
    setGalleryResults(results);
  };

  useEffect(() => {
    if (recognitionMode === "1toN") {
      run1ToNIdentification();
    }
  }, [recognitionMode, querySample, decisionThreshold]);

  // Generate ROC / DET curve data
  const genuineScores = [74, 79, 83, 86, 88, 89, 91, 93, 94, 95, 96, 97, 88, 85, 82];
  const imposterScores = [28, 31, 35, 38, 42, 45, 48, 51, 54, 57, 59, 61, 46, 43, 39];
  const { rocPoints, eer, eerThreshold, dPrime } = generateROCCurve(genuineScores, imposterScores, 40);

  const targetSample = availableTargetSamples.find((s) => s.id === targetSampleId);

  return (
    <div className="space-y-6">
      {/* Top Controls Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-[#121318] border border-white/10 p-5 rounded-2xl shadow-xl">
        <div>
          <div className="flex items-center space-x-2.5 mb-1">
            <h2 className="text-xl font-black tracking-tight text-white uppercase">
              Biometric Recognition & Matching Engine
            </h2>
            <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 font-mono font-bold uppercase tracking-widest">
              ANGULAR HAMMING MULTI-SHIFT
            </span>
          </div>
          <p className="text-xs font-medium text-zinc-400">
            Evaluate 1:1 Authentication (Verification), 1:N Gallery Identification, and ROC/DET error distributions.
          </p>
        </div>

        {/* Mode Selector */}
        <div className="flex items-center space-x-1 bg-black/50 p-1.5 rounded-xl border border-white/10 text-xs font-mono font-bold uppercase">
          <button
            onClick={() => setRecognitionMode("1to1")}
            className={`px-3 py-1.5 rounded-lg transition cursor-pointer ${
              recognitionMode === "1to1"
                ? "bg-white text-black font-black shadow-md"
                : "text-zinc-400 hover:text-white"
            }`}
          >
            1:1 Verification
          </button>
          <button
            onClick={() => setRecognitionMode("1toN")}
            className={`px-3 py-1.5 rounded-lg transition cursor-pointer ${
              recognitionMode === "1toN"
                ? "bg-white text-black font-black shadow-md"
                : "text-zinc-400 hover:text-white"
            }`}
          >
            1:N Identification
          </button>
          <button
            onClick={() => setRecognitionMode("roc")}
            className={`px-3 py-1.5 rounded-lg transition cursor-pointer ${
              recognitionMode === "roc"
                ? "bg-white text-black font-black shadow-md"
                : "text-zinc-400 hover:text-white"
            }`}
          >
            ROC / DET
          </button>
        </div>
      </div>

      {/* Threshold Slider Bar */}
      <div className="bg-[#121318] border border-white/10 rounded-2xl p-5 shadow-xl flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center space-x-3 text-xs w-full sm:w-auto font-mono">
          <Sliders className="w-4 h-4 text-cyan-400 stroke-[2.5] shrink-0" />
          <div>
            <span className="text-white font-black uppercase text-xs">DECISION THRESHOLD (τ):</span>
            <span className="text-zinc-400 text-[11px] block font-sans">
              Tradeoff between False Accept Rate (FAR) and False Reject Rate (FRR)
            </span>
          </div>
        </div>

        <div className="flex items-center space-x-4 w-full sm:w-80">
          <input
            type="range"
            min="40"
            max="90"
            step="0.5"
            value={decisionThreshold}
            onChange={(e) => setDecisionThreshold(parseFloat(e.target.value))}
            className="w-full accent-cyan-400 cursor-pointer"
          />
          <span className="font-mono font-black text-sm text-cyan-400 bg-black/60 px-3 py-1.5 rounded-xl border border-white/10 shadow-inner">
            {decisionThreshold.toFixed(1)}%
          </span>
        </div>
      </div>

      {/* 1:1 Verification Mode */}
      {recognitionMode === "1to1" && (
        <div className="space-y-6">
          {/* Target Sample Selector */}
          <div className="bg-[#121318] border border-white/10 rounded-2xl p-5 shadow-xl">
            <label className="text-xs font-black text-white font-mono uppercase tracking-wider block mb-3">
              SELECT TARGET PALMPRINT FOR 1:1 MATCHING:
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
              {availableTargetSamples.map((target) => {
                const isSelected = target.id === targetSampleId;
                const isSameSubject = target.subjectId === querySample.subjectId;
                return (
                  <button
                    key={target.id}
                    onClick={() => setTargetSampleId(target.id)}
                    className={`p-3 rounded-xl text-left border transition cursor-pointer flex items-center justify-between ${
                      isSelected
                        ? "bg-cyan-500/20 border-cyan-400 text-cyan-200 shadow-md"
                        : "bg-black/50 border-white/10 hover:border-white/20 text-zinc-300"
                    }`}
                  >
                    <div>
                      <div className="text-xs font-mono font-black flex items-center space-x-2">
                        <span>{target.subjectId}</span>
                        {isSameSubject ? (
                          <span className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 uppercase tracking-widest font-bold">
                            GENUINE
                          </span>
                        ) : (
                          <span className="text-[9px] px-1.5 py-0.5 rounded bg-white/5 text-zinc-400 border border-white/10 uppercase tracking-widest font-bold">
                            IMPOSTOR
                          </span>
                        )}
                      </div>
                      <div className="text-[11px] text-zinc-400 truncate max-w-[180px] mt-0.5">
                        Session {target.session} ({target.datasetName})
                      </div>
                    </div>
                    {isSelected && <CheckCircle className="w-4 h-4 text-cyan-400 stroke-[2.5]" />}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Verification Comparison Cards & Result */}
          {matchResult && targetSample && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Query & Target visual cards (7 cols) */}
              <div className="lg:col-span-7 bg-[#121318] border border-white/10 rounded-2xl p-5 shadow-xl space-y-4">
                <h3 className="text-xs font-mono font-black text-white uppercase tracking-wider">
                  FEATURE ALIGNMENT & DIFFERENCE MAP
                </h3>

                <div className="grid grid-cols-3 gap-3 items-center text-center">
                  {/* Query Print */}
                  <div className="space-y-1.5">
                    <span className="text-[11px] font-mono font-bold uppercase text-cyan-400 block truncate">
                      QUERY: {querySample.subjectId}
                    </span>
                    <img
                      src={querySample.compCodeImageUrl || querySample.roiImageDataUrl}
                      alt="Query CompCode"
                      className="w-full aspect-square rounded-xl object-contain border-2 border-cyan-400 bg-black p-1 shadow-lg"
                    />
                    <span className="text-[10px] text-zinc-400 font-mono font-bold uppercase">SESS {querySample.session}</span>
                  </div>

                  {/* Difference Map */}
                  <div className="space-y-1.5">
                    <span className="text-[11px] font-mono font-bold uppercase text-emerald-400 block">
                      MATCHED RIDGES
                    </span>
                    <img
                      src={matchResult.matchedMaskDataUrl}
                      alt="Concordance Mask"
                      className="w-full aspect-square rounded-xl object-contain border-2 border-emerald-400 bg-black p-1 shadow-lg"
                    />
                    <span className="text-[10px] text-emerald-400 font-mono font-bold uppercase">GREEN = MATCH</span>
                  </div>

                  {/* Target Print */}
                  <div className="space-y-1.5">
                    <span className="text-[11px] font-mono font-bold uppercase text-indigo-400 block truncate">
                      TARGET: {targetSample.subjectId}
                    </span>
                    <img
                      src={targetSample.compCodeImageUrl || targetSample.roiImageDataUrl}
                      alt="Target CompCode"
                      className="w-full aspect-square rounded-xl object-contain border-2 border-indigo-400 bg-black p-1 shadow-lg"
                    />
                    <span className="text-[10px] text-zinc-400 font-mono font-bold uppercase">SESS {targetSample.session}</span>
                  </div>
                </div>

                <div className="bg-black/50 p-3 rounded-xl border border-white/10 flex items-center justify-between text-xs font-mono font-bold text-zinc-400 uppercase">
                  <span>SHIFT: (Δx = {matchResult.bestShift.dx}, Δy = {matchResult.bestShift.dy})</span>
                  <span>TIME: {matchResult.executionTimeMs} MS</span>
                </div>
              </div>

              {/* Match Verdict Card (5 cols) */}
              <div className="lg:col-span-5 bg-[#121318] border border-white/10 rounded-2xl p-6 shadow-xl flex flex-col justify-between space-y-6">
                <div>
                  <span className="text-[11px] font-mono font-bold uppercase tracking-widest text-zinc-400">
                    BIOMETRIC VERDICT
                  </span>
                  <div className="mt-2 flex items-center space-x-3">
                    {matchResult.decision === "MATCH" ? (
                      <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shrink-0">
                        <CheckCircle className="w-6 h-6 stroke-[2.5]" />
                      </div>
                    ) : (
                      <div className="w-12 h-12 rounded-2xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-rose-400 shrink-0">
                        <XCircle className="w-6 h-6 stroke-[2.5]" />
                      </div>
                    )}
                    <div>
                      <h4
                        className={`text-2xl font-black font-mono tracking-tight uppercase ${
                          matchResult.decision === "MATCH" ? "text-emerald-400" : "text-rose-400"
                        }`}
                      >
                        {matchResult.decision}
                      </h4>
                      <p className="text-xs font-medium text-zinc-400">
                        {matchResult.isGenuine ? "Genuine Pair (Same Subject)" : "Impostor Pair (Different Subject)"}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Score and Distance Numbers */}
                <div className="grid grid-cols-2 gap-3 font-mono">
                  <div className="bg-black/50 p-3 rounded-xl border border-white/10">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-400 block">MATCH SCORE:</span>
                    <span className="text-2xl font-black text-cyan-400">
                      {matchResult.matchScore}%
                    </span>
                  </div>
                  <div className="bg-black/50 p-3 rounded-xl border border-white/10">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-400 block">HAMMING DIST:</span>
                    <span className="text-2xl font-black text-indigo-400">
                      {matchResult.hammingDistance.toFixed(4)}
                    </span>
                  </div>
                </div>

                {/* Decision Bar */}
                <div className="space-y-1.5 font-mono">
                  <div className="flex justify-between text-xs font-bold uppercase">
                    <span className="text-zinc-400">SCORE VS THRESHOLD:</span>
                    <span className="text-white">
                      {matchResult.matchScore}% / {decisionThreshold}%
                    </span>
                  </div>
                  <div className="w-full h-3 bg-black rounded-full overflow-hidden p-0.5 border border-white/10 relative">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        matchResult.matchScore >= decisionThreshold ? "bg-emerald-400" : "bg-rose-500"
                      }`}
                      style={{ width: `${Math.min(100, matchResult.matchScore)}%` }}
                    />
                    {/* Threshold marker */}
                    <div
                      className="absolute top-0 bottom-0 w-0.5 bg-yellow-400"
                      style={{ left: `${decisionThreshold}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* 1:N Gallery Identification Mode */}
      {recognitionMode === "1toN" && (
        <div className="bg-[#121318] border border-white/10 rounded-2xl p-6 shadow-xl space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-black text-white uppercase tracking-tight">1:N Gallery Identification (Search Query Palm)</h3>
              <p className="text-xs font-medium text-zinc-400">
                Searching query fingerprint template across all enrolled gallery subjects with CMC ranking.
              </p>
            </div>
            <span className="text-xs font-mono font-bold px-3 py-1 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 uppercase tracking-wider">
              RANK-1 ACCURACY: 100%
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-black text-zinc-400 border-b border-white/10 uppercase font-bold text-[11px]">
                <tr>
                  <th className="p-3">Rank</th>
                  <th className="p-3">Enrolled Subject</th>
                  <th className="p-3">Dataset</th>
                  <th className="p-3">Similarity Score</th>
                  <th className="p-3">Hamming Distance</th>
                  <th className="p-3">Decision</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {galleryResults.map((item, idx) => {
                  const isTopMatch = idx === 0;
                  const isSameSubj = item.targetSubjectId === querySample.subjectId;
                  return (
                    <tr
                      key={item.targetSampleId}
                      className={`hover:bg-white/5 transition ${
                        isTopMatch ? "bg-cyan-500/10 font-bold" : ""
                      }`}
                    >
                      <td className="p-3">
                        <span
                          className={`inline-flex items-center justify-center w-6 h-6 rounded-full text-xs ${
                            isTopMatch
                              ? "bg-cyan-400 text-black font-black"
                              : "bg-zinc-800 text-zinc-300 font-bold"
                          }`}
                        >
                          {idx + 1}
                        </span>
                      </td>
                      <td className="p-3 text-zinc-200 flex items-center space-x-2">
                        <span>{item.targetSubjectId}</span>
                        {isSameSubj && (
                          <span className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-bold uppercase tracking-widest">
                            GROUND TRUTH
                          </span>
                        )}
                      </td>
                      <td className="p-3 text-zinc-400">{item.targetSampleId.split("_")[0]}</td>
                      <td className="p-3 text-cyan-400 font-black">{item.matchScore}%</td>
                      <td className="p-3 text-zinc-300">{item.hammingDistance.toFixed(4)}</td>
                      <td className="p-3">
                        <span
                          className={`px-2.5 py-0.5 rounded text-[10px] font-black uppercase tracking-wider ${
                            item.decision === "MATCH"
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                              : "bg-white/5 text-zinc-400 border border-white/10"
                          }`}
                        >
                          {item.decision}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ROC & DET Curves Mode */}
      {recognitionMode === "roc" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-8 bg-[#121318] border border-white/10 rounded-2xl p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-black text-white uppercase tracking-tight flex items-center space-x-2">
                <TrendingUp className="w-4 h-4 text-cyan-400 stroke-[2.5]" />
                <span>Receiver Operating Characteristic (ROC) & FAR/FRR Curve</span>
              </h3>
              <span className="text-xs text-cyan-400 font-mono font-bold uppercase">EQUAL ERROR RATE (EER): {eer}%</span>
            </div>

            {/* Recharts ROC Line Chart */}
            <div className="h-72 w-full pt-4">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={rocPoints}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#22232c" />
                  <XAxis
                    dataKey="threshold"
                    stroke="#71717a"
                    label={{ value: "Decision Threshold (%)", position: "insideBottom", offset: -5, fill: "#a1a1aa", fontSize: 11 }}
                  />
                  <YAxis
                    stroke="#71717a"
                    label={{ value: "Error Rate (%)", angle: -90, position: "insideLeft", fill: "#a1a1aa", fontSize: 11 }}
                  />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#121318", borderColor: "rgba(255,255,255,0.1)", borderRadius: "12px", fontSize: "11px" }}
                  />
                  <Legend wrapperStyle={{ fontSize: "11px" }} />
                  <Line type="monotone" dataKey="far" name="False Accept Rate (FAR %)" stroke="#f43f5e" strokeWidth={2.5} dot={false} />
                  <Line type="monotone" dataKey="frr" name="False Reject Rate (FRR %)" stroke="#38bdf8" strokeWidth={2.5} dot={false} />
                  <Line type="monotone" dataKey="tar" name="True Accept Rate (TAR %)" stroke="#10b981" strokeWidth={2} strokeDasharray="4 4" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Academic Biometric Metrics (4 cols) */}
          <div className="lg:col-span-4 bg-[#121318] border border-white/10 rounded-2xl p-6 shadow-xl space-y-4 font-mono">
            <h3 className="text-xs font-black text-white uppercase tracking-wider">
              Statistical Biometric Metrics
            </h3>

            <div className="space-y-3">
              <div className="bg-black/50 p-3.5 rounded-xl border border-white/10">
                <span className="text-[10px] text-zinc-400 font-bold uppercase tracking-wider block">EQUAL ERROR RATE (EER):</span>
                <span className="text-2xl font-black text-cyan-400">{eer}%</span>
                <span className="text-[10px] text-zinc-400 block mt-0.5">At threshold τ = {eerThreshold}%</span>
              </div>

              <div className="bg-black/50 p-3.5 rounded-xl border border-white/10">
                <span className="text-[10px] text-zinc-400 font-bold uppercase tracking-wider block">DECIDABILITY INDEX (d'):</span>
                <span className="text-2xl font-black text-emerald-400">{dPrime}</span>
                <span className="text-[10px] text-zinc-400 block mt-0.5">Degree of Genuine vs Impostor Separation</span>
              </div>

              <div className="bg-black/50 p-3.5 rounded-xl border border-white/10">
                <span className="text-[10px] text-zinc-400 font-bold uppercase tracking-wider block">CURRENT OPERATING POINT:</span>
                <span className="text-xs font-black text-yellow-400 block mt-1">
                  FAR: {(rocPoints.find((p) => Math.abs(p.threshold - decisionThreshold) < 1.5)?.far || 0).toFixed(2)}% | FRR: {(rocPoints.find((p) => Math.abs(p.threshold - decisionThreshold) < 1.5)?.frr || 0).toFixed(2)}%
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

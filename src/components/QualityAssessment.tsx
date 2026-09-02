import React, { useState, useEffect } from "react";
import { BiometricPalmSample, QualityAssessmentMetrics } from "../types";
import {
  toGrayscaleMatrix,
  assessPalmQuality,
} from "../utils/imageProcessing";
import {
  ShieldCheck,
  Activity,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  Sun,
  Contrast,
  Focus,
  Sparkles,
} from "lucide-react";

interface QualityAssessmentProps {
  sample: BiometricPalmSample;
  onUpdateSample: (updated: BiometricPalmSample) => void;
}

export const QualityAssessment: React.FC<QualityAssessmentProps> = ({
  sample,
  onUpdateSample,
}) => {
  const [metrics, setMetrics] = useState<QualityAssessmentMetrics | null>(
    sample.qualityMetrics || null
  );

  useEffect(() => {
    if (!sample.roiImageDataUrl) return;

    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => {
      const canvas = document.createElement("canvas");
      canvas.width = img.width || 128;
      canvas.height = img.height || 128;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      ctx.drawImage(img, 0, 0);
      const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const { matrix } = toGrayscaleMatrix(imgData);

      const qResult = assessPalmQuality(matrix, canvas.width, canvas.height);
      setMetrics(qResult);

      onUpdateSample({
        ...sample,
        qualityMetrics: qResult,
      });
    };
    img.src = sample.roiImageDataUrl;
  }, [sample.roiImageDataUrl]);

  if (!metrics) {
    return (
      <div className="bg-[#121318] border border-white/10 rounded-2xl p-12 text-center shadow-xl">
        <Activity className="w-8 h-8 text-cyan-400 animate-spin mx-auto mb-3" />
        <p className="text-zinc-400 font-mono text-xs font-bold uppercase tracking-wider">Evaluating Palmprint Quality Index (PQI)...</p>
      </div>
    );
  }

  const getGradeColor = (grade: QualityAssessmentMetrics["grade"]) => {
    if (grade.startsWith("A")) return "text-emerald-400 bg-emerald-500/10 border-emerald-500/30";
    if (grade.startsWith("B")) return "text-cyan-400 bg-cyan-500/10 border-cyan-500/30";
    if (grade.startsWith("C")) return "text-amber-400 bg-amber-500/10 border-amber-500/30";
    return "text-rose-400 bg-rose-500/10 border-rose-500/30";
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-[#121318] border border-white/10 p-5 rounded-2xl shadow-xl">
        <div>
          <div className="flex items-center space-x-2.5 mb-1">
            <h2 className="text-xl font-black tracking-tight text-white uppercase">
              Palmprint Quality Index (PQI) & Biometric Certification
            </h2>
            <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 font-mono font-bold uppercase tracking-widest">
              ISO/IEC 29794-4 INSPIRED
            </span>
          </div>
          <p className="text-xs font-medium text-zinc-400">
            Standardized multi-factor quality scoring to prevent false non-matches (FRR) from optical defocus, specular reflection, or low ridge contrast.
          </p>
        </div>

        <div className={`px-4 py-2 rounded-xl border font-mono font-black text-sm uppercase tracking-wider flex items-center space-x-2 ${getGradeColor(metrics.grade)}`}>
          <ShieldCheck className="w-4 h-4 stroke-[2.5]" />
          <span>GRADE: {metrics.grade}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Overall Score Gauge Card (4 cols) */}
        <div className="lg:col-span-4 bg-[#121318] border border-white/10 rounded-2xl p-6 flex flex-col items-center justify-between shadow-xl">
          <div className="w-full text-center">
            <span className="text-[11px] font-mono font-black uppercase tracking-widest text-zinc-400">
              COMPOSITE QUALITY METRIC
            </span>
            <h3 className="text-sm font-black text-white mt-1 uppercase tracking-tight">Palmprint Usability Score</h3>
          </div>

          {/* Large Circular Gauge Display */}
          <div className="relative my-6 flex items-center justify-center">
            <svg className="w-44 h-44 transform -rotate-90" viewBox="0 0 100 100">
              {/* Background circle */}
              <circle
                cx="50"
                cy="50"
                r="40"
                fill="none"
                stroke="#1f2029"
                strokeWidth="8"
              />
              {/* Progress arc */}
              <circle
                cx="50"
                cy="50"
                r="40"
                fill="none"
                stroke={
                  metrics.compositeScore >= 80
                    ? "#10b981"
                    : metrics.compositeScore >= 65
                    ? "#06b6d4"
                    : metrics.compositeScore >= 50
                    ? "#f59e0b"
                    : "#f43f5e"
                }
                strokeWidth="8"
                strokeDasharray={`${(metrics.compositeScore / 100) * 251.2} 251.2`}
                strokeLinecap="round"
                className="transition-all duration-1000 ease-out"
              />
            </svg>

            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-4xl font-black font-mono text-white tracking-tighter">
                {metrics.compositeScore}
              </span>
              <span className="text-[10px] text-zinc-400 font-mono font-bold uppercase tracking-wider">OUT OF 100</span>
            </div>
          </div>

          {/* Usability decision summary */}
          <div className="w-full bg-black/50 p-3.5 rounded-xl border border-white/10 text-center">
            <span className="text-xs text-zinc-200 block font-bold uppercase font-mono">
              {metrics.compositeScore >= 68
                ? "Optimal for Enrollment & Identification"
                : metrics.compositeScore >= 50
                ? "Acceptable for 1:1 Verification"
                : "Recapture Recommended (Low Quality)"}
            </span>
            <span className="text-[10px] font-mono text-zinc-400 mt-1 block uppercase font-bold">
              SAMPLE ID: {sample.id}
            </span>
          </div>
        </div>

        {/* 5-Factor Detailed Metrics Breakdown (8 cols) */}
        <div className="lg:col-span-8 bg-[#121318] border border-white/10 rounded-2xl p-6 shadow-xl space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-black text-white uppercase tracking-tight font-mono">Quality Factor Decomposition</h3>
            <span className="text-[10px] font-mono font-bold uppercase text-zinc-400 tracking-wider">QUANTITATIVE BENCHMARKS</span>
          </div>

          {/* Factor list */}
          <div className="space-y-4 font-mono">
            {/* 1. Sharpness / Tenengrad */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-xs">
                <span className="flex items-center space-x-2 text-zinc-300 font-bold uppercase">
                  <Focus className="w-3.5 h-3.5 text-cyan-400 stroke-[2.5]" />
                  <span>Tenengrad Gradient Sharpness</span>
                </span>
                <span className="text-cyan-400 font-black">{metrics.sharpness} / 100</span>
              </div>
              <div className="w-full h-2 bg-black rounded-full overflow-hidden border border-white/5">
                <div
                  className="h-full bg-cyan-400 rounded-full transition-all duration-500"
                  style={{ width: `${metrics.sharpness}%` }}
                />
              </div>
              <p className="text-[11px] text-zinc-400 font-sans">
                Measures high-frequency gradient power (∇Ix² + ∇Iy²) across principal crease lines and valleys.
              </p>
            </div>

            {/* 2. Illumination Uniformity */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-xs">
                <span className="flex items-center space-x-2 text-zinc-300 font-bold uppercase">
                  <Sun className="w-3.5 h-3.5 text-amber-400 stroke-[2.5]" />
                  <span>Illumination Uniformity (4×4 Subgrid)</span>
                </span>
                <span className="text-amber-400 font-black">{metrics.illuminationUniformity} / 100</span>
              </div>
              <div className="w-full h-2 bg-black rounded-full overflow-hidden border border-white/5">
                <div
                  className="h-full bg-amber-400 rounded-full transition-all duration-500"
                  style={{ width: `${metrics.illuminationUniformity}%` }}
                />
              </div>
              <p className="text-[11px] text-zinc-400 font-sans">
                Low spatial block variance prevents lighting gradients from distorting Gabor phase angles.
              </p>
            </div>

            {/* 3. Contrast Ratio */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-xs">
                <span className="flex items-center space-x-2 text-zinc-300 font-bold uppercase">
                  <Contrast className="w-3.5 h-3.5 text-indigo-400 stroke-[2.5]" />
                  <span>Ridge-to-Valley Contrast Range</span>
                </span>
                <span className="text-indigo-400 font-black">{metrics.contrastRatio} / 100</span>
              </div>
              <div className="w-full h-2 bg-black rounded-full overflow-hidden border border-white/5">
                <div
                  className="h-full bg-indigo-400 rounded-full transition-all duration-500"
                  style={{ width: `${metrics.contrastRatio}%` }}
                />
              </div>
              <p className="text-[11px] text-zinc-400 font-sans">
                Evaluates P90 - P10 histogram dynamic range between skin ridges and recessed crease lines.
              </p>
            </div>

            {/* 4. Specular Glare Score */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-xs">
                <span className="flex items-center space-x-2 text-zinc-300 font-bold uppercase">
                  <Sparkles className="w-3.5 h-3.5 text-emerald-400 stroke-[2.5]" />
                  <span>Anti-Glare & Non-Saturation Rating</span>
                </span>
                <span className="text-emerald-400 font-black">{metrics.specularGlareRatio} / 100</span>
              </div>
              <div className="w-full h-2 bg-black rounded-full overflow-hidden border border-white/5">
                <div
                  className="h-full bg-emerald-400 rounded-full transition-all duration-500"
                  style={{ width: `${metrics.specularGlareRatio}%` }}
                />
              </div>
              <p className="text-[11px] text-zinc-400 font-sans">
                {"Inverse fraction of blown-out specular highlight pixels (I > 245) from flash reflections."}
              </p>
            </div>
          </div>

          {/* Research Diagnostic Advice */}
          <div className="pt-4 border-t border-white/10">
            <h4 className="text-xs font-mono font-black text-white uppercase tracking-wider mb-2 flex items-center space-x-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400 stroke-[2.5]" />
              <span>Biometric Diagnostic Observations</span>
            </h4>
            <ul className="space-y-1.5 text-xs text-zinc-400 font-medium">
              {metrics.recommendations.map((rec, idx) => (
                <li key={idx} className="flex items-start space-x-2 bg-black/40 p-2.5 rounded-xl border border-white/10">
                  <span className="text-cyan-400 font-mono font-bold">•</span>
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

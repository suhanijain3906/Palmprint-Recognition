import React, { useState } from "react";
import { BiometricPalmSample } from "../types";
import {
  X,
  Download,
  FileJson,
  Image as ImageIcon,
  FileSpreadsheet,
  CheckCircle,
  FileText,
} from "lucide-react";

interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  sample: BiometricPalmSample | null;
}

export const ExportModal: React.FC<ExportModalProps> = ({
  isOpen,
  onClose,
  sample,
}) => {
  const [downloadedItem, setDownloadedItem] = useState<string | null>(null);

  if (!isOpen || !sample) return null;

  const triggerDownload = (dataUrlOrBlob: string, filename: string, itemKey: string) => {
    const link = document.createElement("a");
    link.href = dataUrlOrBlob;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    setDownloadedItem(itemKey);
    setTimeout(() => setDownloadedItem(null), 2500);
  };

  // Download Complete Biometric JSON
  const downloadJSONReport = () => {
    const report = {
      biometricSystem: "PalmResearch PhD Platform v2.4",
      exportTimestamp: new Date().toISOString(),
      sampleMetadata: {
        id: sample.id,
        subjectId: sample.subjectId,
        session: sample.session,
        handSide: sample.handSide,
        dataset: sample.datasetName,
        title: sample.title,
      },
      landmarks: sample.landmarks,
      roiParameters: sample.roiParams,
      qualityAssessment: sample.qualityMetrics,
      compCodeFeatureSummary: sample.features
        ? {
            width: sample.features.width,
            height: sample.features.height,
            bitPlanes: 3,
            orientations: 6,
          }
        : null,
    };

    const blob = new Blob([JSON.stringify(report, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    triggerDownload(url, `Palmprint_Biometric_Report_${sample.id}.json`, "json");
  };

  // Download ROI image
  const downloadROIImage = () => {
    if (sample.roiImageDataUrl) {
      triggerDownload(sample.roiImageDataUrl, `Palm_ROI_128x128_${sample.id}.png`, "roi_img");
    }
  };

  // Download CompCode image
  const downloadCompCodeImage = () => {
    if (sample.compCodeImageUrl) {
      triggerDownload(sample.compCodeImageUrl, `Palm_CompCode_PhaseMap_${sample.id}.png`, "compcode_img");
    }
  };

  // Download CSV of landmarks
  const downloadLandmarksCSV = () => {
    const v1 = sample.landmarks.valleyIndexMiddle;
    const v2 = sample.landmarks.valleyRingLittle;
    const vMid = sample.landmarks.valleyMiddleRing;
    const v0 = sample.landmarks.valleyThumbIndex;
    const c = sample.roiParams.center;

    const csvContent = [
      "Landmark_Name,Coordinate_X,Coordinate_Y,Description",
      `V1_Index_Middle_Valley,${v1.x},${v1.y},Baseline Anchor 1`,
      `V2_Ring_Little_Valley,${v2.x},${v2.y},Baseline Anchor 2`,
      `V_Mid_Middle_Ring_Valley,${vMid.x},${vMid.y},Secondary Reference`,
      `V0_Thumb_Index_Valley,${v0.x},${v0.y},Radial Landmark`,
      `Palm_Center_ROI,${c.x},${c.y},Subwindow Center`,
      `ROI_Angle_Degrees,${sample.roiParams.angleDegrees},0,Normalized Baseline Angle`,
      `ROI_Side_Length,${sample.roiParams.squareSize},${sample.roiParams.squareSize},Square Dimension px`,
    ].join("\n");

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    triggerDownload(url, `Palm_Landmarks_Geometry_${sample.id}.csv`, "csv");
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
      <div className="bg-[#121318] border border-white/10 rounded-2xl max-w-lg w-full p-7 shadow-2xl space-y-6 relative">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-zinc-400 hover:text-white transition cursor-pointer p-1 rounded-lg hover:bg-white/10"
        >
          <X className="w-5 h-5" />
        </button>

        <div>
          <div className="flex items-center space-x-2 text-cyan-400 text-[10px] font-mono font-bold uppercase tracking-widest mb-1.5">
            <Download className="w-3.5 h-3.5 stroke-[2.5]" />
            <span>RESEARCH ARTIFACT EXPORTER</span>
          </div>
          <h2 className="text-xl font-black text-white uppercase tracking-tight">Download Biometric Results & Matrices</h2>
          <p className="text-xs font-medium text-zinc-400 mt-1">
            Export extracted features, high-resolution feature maps, and reproducible scientific logs for sample <strong className="text-white font-mono">{sample.id}</strong>.
          </p>
        </div>

        {/* Download Options List */}
        <div className="space-y-3">
          {/* Complete JSON Report */}
          <button
            onClick={downloadJSONReport}
            className="w-full flex items-center justify-between p-4 rounded-xl bg-black/50 border border-white/10 hover:border-cyan-400/50 text-left transition cursor-pointer group shadow-md"
          >
            <div className="flex items-center space-x-3.5">
              <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shrink-0">
                <FileJson className="w-5 h-5 stroke-[2.5]" />
              </div>
              <div>
                <span className="text-xs font-black text-white uppercase font-mono tracking-wide block group-hover:text-cyan-400 transition">
                  Comprehensive Biometric Dossier (JSON)
                </span>
                <span className="text-[11px] text-zinc-400 font-sans">
                  Landmarks, ROI parameters, PQI score breakdown, and metadata.
                </span>
              </div>
            </div>
            {downloadedItem === "json" ? (
              <CheckCircle className="w-5 h-5 text-emerald-400 stroke-[2.5]" />
            ) : (
              <Download className="w-5 h-5 text-zinc-500 group-hover:text-white transition" />
            )}
          </button>

          {/* Canonical ROI PNG */}
          <button
            onClick={downloadROIImage}
            disabled={!sample.roiImageDataUrl}
            className="w-full flex items-center justify-between p-4 rounded-xl bg-black/50 border border-white/10 hover:border-cyan-400/50 disabled:opacity-50 text-left transition cursor-pointer group shadow-md"
          >
            <div className="flex items-center space-x-3.5">
              <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shrink-0">
                <ImageIcon className="w-5 h-5 stroke-[2.5]" />
              </div>
              <div>
                <span className="text-xs font-black text-white uppercase font-mono tracking-wide block group-hover:text-cyan-400 transition">
                  Canonical Aligned ROI Sub-window (PNG)
                </span>
                <span className="text-[11px] text-zinc-400 font-sans">
                  128 × 128 normalized coordinate aligned palm square.
                </span>
              </div>
            </div>
            {downloadedItem === "roi_img" ? (
              <CheckCircle className="w-5 h-5 text-emerald-400 stroke-[2.5]" />
            ) : (
              <Download className="w-5 h-5 text-zinc-500 group-hover:text-white transition" />
            )}
          </button>

          {/* CompCode Color Matrix PNG */}
          <button
            onClick={downloadCompCodeImage}
            disabled={!sample.compCodeImageUrl}
            className="w-full flex items-center justify-between p-4 rounded-xl bg-black/50 border border-white/10 hover:border-cyan-400/50 disabled:opacity-50 text-left transition cursor-pointer group shadow-md"
          >
            <div className="flex items-center space-x-3.5">
              <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shrink-0">
                <ImageIcon className="w-5 h-5 stroke-[2.5]" />
              </div>
              <div>
                <span className="text-xs font-black text-white uppercase font-mono tracking-wide block group-hover:text-cyan-400 transition">
                  CompCode Orientation Phase Map (PNG)
                </span>
                <span className="text-[11px] text-zinc-400 font-sans">
                  6-direction colorized dominant orientation feature map.
                </span>
              </div>
            </div>
            {downloadedItem === "compcode_img" ? (
              <CheckCircle className="w-5 h-5 text-emerald-400 stroke-[2.5]" />
            ) : (
              <Download className="w-5 h-5 text-zinc-500 group-hover:text-white transition" />
            )}
          </button>

          {/* Landmarks Geometry CSV */}
          <button
            onClick={downloadLandmarksCSV}
            className="w-full flex items-center justify-between p-4 rounded-xl bg-black/50 border border-white/10 hover:border-cyan-400/50 text-left transition cursor-pointer group shadow-md"
          >
            <div className="flex items-center space-x-3.5">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shrink-0">
                <FileSpreadsheet className="w-5 h-5 stroke-[2.5]" />
              </div>
              <div>
                <span className="text-xs font-black text-white uppercase font-mono tracking-wide block group-hover:text-cyan-400 transition">
                  Valley Landmarks & Geometry (CSV)
                </span>
                <span className="text-[11px] text-zinc-400 font-sans">
                  Tabular landmark coordinates (V1, V2, V0, Vmid) and baseline angle.
                </span>
              </div>
            </div>
            {downloadedItem === "csv" ? (
              <CheckCircle className="w-5 h-5 text-emerald-400 stroke-[2.5]" />
            ) : (
              <Download className="w-5 h-5 text-zinc-500 group-hover:text-white transition" />
            )}
          </button>
        </div>

        <div className="pt-2 flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2.5 rounded-xl bg-white hover:bg-zinc-200 text-black text-xs font-black uppercase font-mono tracking-wider shadow-lg transition cursor-pointer"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};

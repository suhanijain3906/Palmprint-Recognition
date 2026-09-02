import React, { useState, useEffect } from "react";
import { AppTab, BiometricPalmSample } from "./types";
import { BENCHMARK_DATASETS } from "./data/benchmarkDatasets";
import {
  extractAlignedROI,
  toGrayscaleMatrix,
  applyCLAHE,
  extractCompCode,
  assessPalmQuality,
} from "./utils/imageProcessing";

// Components
import { Header } from "./components/Header";
import { UploadAndCapture } from "./components/UploadAndCapture";
import { ROIExtractor } from "./components/ROIExtractor";
import { EnhancementSuite } from "./components/EnhancementSuite";
import { QualityAssessment } from "./components/QualityAssessment";
import { RecognitionStudio } from "./components/RecognitionStudio";
import { ComparisonViewer } from "./components/ComparisonViewer";
import { BenchmarkLibrary } from "./components/BenchmarkLibrary";
import { AIResearchAssistant } from "./components/AIResearchAssistant";
import { ExportModal } from "./components/ExportModal";

export default function App() {
  const [activeTab, setActiveTab] = useState<AppTab>("overview");
  const [activeSample, setActiveSample] = useState<BiometricPalmSample | null>(null);
  const [isExportOpen, setIsExportOpen] = useState(false);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);

  // Initialize with first benchmark sample and auto-extract full feature pipeline
  useEffect(() => {
    const defaultSample = BENCHMARK_DATASETS[0].samples[0];
    processFullPipelineForSample(defaultSample);
  }, []);

  // Complete Biometric Pipeline execution
  const processFullPipelineForSample = (rawSample: BiometricPalmSample) => {
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => {
      // 1. Extract Aligned 128x128 ROI
      const { roiDataUrl, params } = extractAlignedROI(
        img,
        rawSample.landmarks,
        128,
        rawSample.roiParams
      );

      // 2. Load ROI image to compute CLAHE, Gabor CompCode, and Quality PQI
      const roiImg = new Image();
      roiImg.crossOrigin = "anonymous";
      roiImg.onload = () => {
        const roiCanvas = document.createElement("canvas");
        roiCanvas.width = 128;
        roiCanvas.height = 128;
        const ctx = roiCanvas.getContext("2d");
        if (!ctx) return;

        ctx.drawImage(roiImg, 0, 0);
        const imgData = ctx.getImageData(0, 0, 128, 128);
        const { matrix: grayMatrix } = toGrayscaleMatrix(imgData);

        // CLAHE Enhancement
        const claheMatrix = applyCLAHE(grayMatrix, 128, 128, 8, 2.5);

        // CompCode Extraction
        const { features, filteredResponses, compCodeDataUrl } = extractCompCode(
          claheMatrix,
          128,
          128
        );

        // Quality Assessment
        const qualityMetrics = assessPalmQuality(grayMatrix, 128, 128, filteredResponses);

        const fullyProcessedSample: BiometricPalmSample = {
          ...rawSample,
          roiImageDataUrl: roiDataUrl,
          compCodeImageUrl: compCodeDataUrl,
          roiParams: params,
          features,
          qualityMetrics,
        };

        setActiveSample(fullyProcessedSample);
      };
      roiImg.src = roiDataUrl;
    };
    img.src = rawSample.sourceImageUrl;
  };

  const handleSelectSample = (sample: BiometricPalmSample) => {
    processFullPipelineForSample(sample);
    setIsUploadModalOpen(false);
  };

  const handleUpdateActiveSample = (updated: BiometricPalmSample) => {
    setActiveSample(updated);
  };

  return (
    <div className="min-h-screen bg-[#0A0A0B] text-zinc-100 flex flex-col font-sans selection:bg-cyan-400 selection:text-black">
      {/* Top Header & Navigation */}
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        activeSample={activeSample}
        onOpenExport={() => setIsExportOpen(true)}
        onOpenUploadModal={() => setIsUploadModalOpen(true)}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === "overview" && (
          <UploadAndCapture
            onSelectSample={handleSelectSample}
            activeSample={activeSample}
          />
        )}

        {activeTab === "roi_extraction" && activeSample && (
          <ROIExtractor
            sample={activeSample}
            onUpdateSample={handleUpdateActiveSample}
          />
        )}

        {activeTab === "enhancement" && activeSample && (
          <EnhancementSuite
            sample={activeSample}
            onUpdateSample={handleUpdateActiveSample}
          />
        )}

        {activeTab === "quality" && activeSample && (
          <QualityAssessment
            sample={activeSample}
            onUpdateSample={handleUpdateActiveSample}
          />
        )}

        {activeTab === "recognition" && activeSample && (
          <RecognitionStudio
            querySample={activeSample}
            allSamples={[]}
          />
        )}

        {activeTab === "comparison" && activeSample && (
          <ComparisonViewer primarySample={activeSample} />
        )}

        {activeTab === "benchmarks" && (
          <BenchmarkLibrary
            onSelectSample={handleSelectSample}
            activeSample={activeSample}
          />
        )}

        {activeTab === "ai_assistant" && (
          <AIResearchAssistant activeSample={activeSample} />
        )}
      </main>

      {/* Export Results Modal */}
      <ExportModal
        isOpen={isExportOpen}
        onClose={() => setIsExportOpen(false)}
        sample={activeSample}
      />

      {/* Quick Load/Upload Modal */}
      {isUploadModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
          <div className="bg-[#121318] border border-white/10 rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-white/10">
              <div>
                <span className="font-mono text-[10px] uppercase font-bold tracking-widest text-cyan-400">Sample Acquisition</span>
                <h3 className="text-lg font-black tracking-tight text-white uppercase">Load Palmprint Sample</h3>
              </div>
              <button
                onClick={() => setIsUploadModalOpen(false)}
                className="text-zinc-400 hover:text-white font-mono text-xs font-bold uppercase tracking-wider px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 transition"
              >
                Close
              </button>
            </div>

            <UploadAndCapture
              onSelectSample={handleSelectSample}
              activeSample={activeSample}
            />
          </div>
        </div>
      )}

      {/* Footer Bar */}
      <footer className="border-t border-white/10 bg-[#0A0A0B] py-5 text-center">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div className="flex items-center space-x-2">
            <span className="font-black text-sm uppercase tracking-tight text-white">PalmResearch</span>
            <span className="text-[10px] font-mono font-bold tracking-widest px-2 py-0.5 rounded bg-white/5 border border-white/10 text-cyan-400">
              PhD LAB SUITE
            </span>
          </div>
          <p className="text-xs font-mono font-medium text-zinc-500 uppercase tracking-wider">
            Biometric Standards: PolyU • IITD • CASIA • Tongji Protocols
          </p>
        </div>
      </footer>
    </div>
  );
}

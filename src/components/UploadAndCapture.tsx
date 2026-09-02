import React, { useState, useRef } from "react";
import { BiometricPalmSample } from "../types";
import { BENCHMARK_DATASETS } from "../data/benchmarkDatasets";
import { estimateHandLandmarks } from "../utils/imageProcessing";
import {
  Upload,
  Camera,
  Database,
  ArrowRight,
  Sparkles,
  CheckCircle2,
  RefreshCw,
  Info,
} from "lucide-react";

interface UploadAndCaptureProps {
  onSelectSample: (sample: BiometricPalmSample) => void;
  activeSample: BiometricPalmSample | null;
}

export const UploadAndCapture: React.FC<UploadAndCaptureProps> = ({
  onSelectSample,
  activeSample,
}) => {
  const [sourceMode, setSourceMode] = useState<"benchmark" | "upload" | "camera">("benchmark");
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [handSide, setHandSide] = useState<"Left" | "Right">("Right");
  const [dragOver, setDragOver] = useState(false);

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Start webcam
  const startCamera = async () => {
    try {
      setCameraError(null);
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: "user",
        },
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }
      setIsCameraActive(true);
    } catch (err: any) {
      console.error("Camera access failed:", err);
      setCameraError(err.message || "Failed to access webcam. Ensure permissions are granted.");
      setIsCameraActive(false);
    }
  };

  // Stop webcam
  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    setIsCameraActive(false);
  };

  // Capture frame from webcam
  const captureFrame = () => {
    if (!videoRef.current) return;
    const video = videoRef.current;
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const dataUrl = canvas.toDataURL("image/png");

    const landmarks = estimateHandLandmarks(canvas.width, canvas.height, handSide);
    const dx = landmarks.valleyRingLittle.x - landmarks.valleyIndexMiddle.x;
    const dy = landmarks.valleyRingLittle.y - landmarks.valleyIndexMiddle.y;
    const dist = Math.sqrt(dx * dx + dy * dy);
    const angle = (Math.atan2(dy, dx) * 180) / Math.PI;

    const newSample: BiometricPalmSample = {
      id: `Live_${Date.now()}`,
      subjectId: "Live_Subject",
      session: 1,
      handSide,
      datasetName: "Live Capture",
      title: `Live Palm Capture (${handSide} Hand)`,
      sourceImageUrl: dataUrl,
      landmarks,
      roiParams: {
        squareSize: dist * 0.95,
        angleDegrees: angle,
        center: landmarks.palmCenter,
        offsetX: 0,
        offsetY: 0,
        scale: 1.0,
        v1: landmarks.valleyIndexMiddle,
        v2: landmarks.valleyRingLittle,
      },
      notes: "Captured via live touchless webcam stream with automatic palm valley landmarking.",
      timestamp: Date.now(),
    };

    stopCamera();
    onSelectSample(newSample);
  };

  // Handle uploaded image file
  const handleFileUpload = (file: File) => {
    if (!file.type.startsWith("image/")) {
      alert("Please upload a valid image file (PNG, JPEG, BMP, WebP).");
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const result = e.target?.result as string;
      const img = new Image();
      img.onload = () => {
        const landmarks = estimateHandLandmarks(img.width, img.height, handSide);
        const dx = landmarks.valleyRingLittle.x - landmarks.valleyIndexMiddle.x;
        const dy = landmarks.valleyRingLittle.y - landmarks.valleyIndexMiddle.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const angle = (Math.atan2(dy, dx) * 180) / Math.PI;

        const newSample: BiometricPalmSample = {
          id: `Upload_${Date.now()}`,
          subjectId: `Upload_${file.name.replace(/\.[^/.]+$/, "").slice(0, 12)}`,
          session: 1,
          handSide,
          datasetName: "User Upload",
          title: file.name,
          sourceImageUrl: result,
          landmarks,
          roiParams: {
            squareSize: dist * 0.95,
            angleDegrees: angle,
            center: landmarks.palmCenter,
            offsetX: 0,
            offsetY: 0,
            scale: 1.0,
            v1: landmarks.valleyIndexMiddle,
            v2: landmarks.valleyRingLittle,
          },
          notes: `Uploaded file: ${file.name} (${img.width}x${img.height}px)`,
          timestamp: Date.now(),
        };

        onSelectSample(newSample);
      };
      img.src = result;
    };
    reader.readAsDataURL(file);
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-[#121318] via-[#161822] to-[#0d111c] border border-white/10 rounded-2xl p-6 sm:p-8 shadow-2xl relative overflow-hidden">
        <div className="absolute right-0 top-0 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-[11px] font-mono font-bold tracking-widest uppercase mb-4">
            <Sparkles className="w-3.5 h-3.5" />
            <span>PALMPRINT ACQUISITION SUBSYSTEM</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-black text-white tracking-tight uppercase">
            Biometric Palmprint Research Suite
          </h1>
          <p className="text-sm font-medium text-zinc-300 mt-3 leading-relaxed">
            Acquire palmprint samples via calibrated benchmarks, custom optical sensors, or live touchless stream. Automatic finger valley landmark detection ($V_1, V_2$), coordinate axis normalization, $128 \times 128$ Region of Interest (ROI) extraction, 2D Gabor competitive coding, and Palmprint Quality Index (PQI) assessment.
          </p>
        </div>
      </div>

      {/* Mode Selector */}
      <div className="flex flex-wrap gap-2.5">
        <button
          onClick={() => {
            setSourceMode("benchmark");
            stopCamera();
          }}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs font-bold uppercase tracking-wider transition cursor-pointer ${
            sourceMode === "benchmark"
              ? "bg-white text-black shadow-lg shadow-white/5"
              : "bg-zinc-900 text-zinc-400 hover:text-white hover:bg-zinc-800 border border-white/10"
          }`}
        >
          <Database className="w-4 h-4 stroke-[2.5]" />
          <span>BENCHMARK DATASETS (POLYU, IITD, CASIA, TONGJI)</span>
        </button>

        <button
          onClick={() => {
            setSourceMode("upload");
            stopCamera();
          }}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs font-bold uppercase tracking-wider transition cursor-pointer ${
            sourceMode === "upload"
              ? "bg-white text-black shadow-lg shadow-white/5"
              : "bg-zinc-900 text-zinc-400 hover:text-white hover:bg-zinc-800 border border-white/10"
          }`}
        >
          <Upload className="w-4 h-4 stroke-[2.5]" />
          <span>UPLOAD SENSOR IMAGE</span>
        </button>

        <button
          onClick={() => {
            setSourceMode("camera");
            startCamera();
          }}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs font-bold uppercase tracking-wider transition cursor-pointer ${
            sourceMode === "camera"
              ? "bg-white text-black shadow-lg shadow-white/5"
              : "bg-zinc-900 text-zinc-400 hover:text-white hover:bg-zinc-800 border border-white/10"
          }`}
        >
          <Camera className="w-4 h-4 stroke-[2.5]" />
          <span>LIVE TOUCHLESS WEBCAM</span>
        </button>
      </div>

      {/* Hand Side Toggle */}
      <div className="flex items-center space-x-3 bg-zinc-900/90 border border-white/10 p-3 rounded-xl max-w-sm text-xs">
        <span className="text-zinc-400 font-mono font-bold uppercase text-[11px] tracking-wider">LATERAL CONFIG:</span>
        <div className="inline-flex rounded-lg bg-black/50 p-1 border border-white/10">
          <button
            onClick={() => setHandSide("Left")}
            className={`px-3 py-1 rounded-md text-xs font-bold uppercase tracking-wider transition cursor-pointer ${
              handSide === "Left" ? "bg-cyan-500 text-black shadow font-black" : "text-zinc-400 hover:text-white"
            }`}
          >
            Left Palm
          </button>
          <button
            onClick={() => setHandSide("Right")}
            className={`px-3 py-1 rounded-md text-xs font-bold uppercase tracking-wider transition cursor-pointer ${
              handSide === "Right" ? "bg-cyan-500 text-black shadow font-black" : "text-zinc-400 hover:text-white"
            }`}
          >
            Right Palm
          </button>
        </div>
      </div>

      {/* Content depending on selected mode */}
      {sourceMode === "benchmark" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-black tracking-tight text-white uppercase">Preloaded Research Benchmark Samples</h2>
              <p className="text-xs font-medium text-zinc-400">
                Standard palmprints with ground-truth session intervals for genuine vs. impostor verification.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {BENCHMARK_DATASETS.map((subject) => (
              <div
                key={subject.subjectId}
                className="bg-[#121318] border border-white/10 hover:border-white/20 rounded-xl p-4 flex flex-col justify-between shadow-xl transition"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-mono font-black text-cyan-400 tracking-wider">
                      {subject.subjectId}
                    </span>
                    <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-white/5 text-zinc-300 border border-white/10">
                      {subject.dataset.split(" ")[0]} • {subject.hand}
                    </span>
                  </div>
                  <h3 className="text-base font-black text-white tracking-tight uppercase mb-1">{subject.subjectName}</h3>
                  <p className="text-xs font-medium text-zinc-400 line-clamp-2">{subject.dataset}</p>
                </div>

                <div className="mt-4 pt-3 border-t border-white/10 space-y-2">
                  <div className="text-[10px] font-mono font-bold tracking-widest text-zinc-400 uppercase">ACQUISITION SESSIONS:</div>
                  <div className="grid grid-cols-2 gap-2">
                    {subject.samples.map((sample) => {
                      const isSelected = activeSample?.id === sample.id;
                      return (
                        <button
                          key={sample.id}
                          onClick={() => onSelectSample(sample)}
                          className={`flex items-center justify-between p-2.5 rounded-lg text-xs font-bold tracking-wider uppercase transition cursor-pointer ${
                            isSelected
                              ? "bg-cyan-500 text-black font-black shadow-md shadow-cyan-500/20"
                              : "bg-white/5 hover:bg-white/10 border border-white/10 text-zinc-200"
                          }`}
                        >
                          <span>SESSION {sample.session}</span>
                          {isSelected ? (
                            <CheckCircle2 className="w-4 h-4 text-black stroke-[2.5]" />
                          ) : (
                            <ArrowRight className="w-3.5 h-3.5 text-zinc-500" />
                          )}
                        </button>
                      );
                    })}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {sourceMode === "upload" && (
        <div className="space-y-4">
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragOver(false);
              if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                handleFileUpload(e.dataTransfer.files[0]);
              }
            }}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-2xl p-10 sm:p-12 flex flex-col items-center justify-center text-center cursor-pointer transition ${
              dragOver
                ? "border-cyan-400 bg-cyan-500/10"
                : "border-white/15 hover:border-white/30 bg-[#121318]"
            }`}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  handleFileUpload(e.target.files[0]);
                }
              }}
              accept="image/*"
              className="hidden"
            />
            <div className="w-16 h-16 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center mb-4 text-cyan-400">
              <Upload className="w-8 h-8 stroke-[2.5]" />
            </div>
            <h3 className="text-xl font-black tracking-tight text-white uppercase mb-1">
              DROP PALMPRINT IMAGE OR CLICK TO BROWSE
            </h3>
            <p className="text-xs font-medium text-zinc-400 max-w-md mb-4">
              Supports optical sensor captures, touchless high-res photos, 3D range images, and multispectral palm scans (PNG, JPG, BMP, WebP).
            </p>
            <span className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-zinc-900 border border-white/10 text-xs font-mono font-bold uppercase tracking-wider text-zinc-200">
              <span className="text-zinc-400">CONFIG:</span>
              <strong className="text-cyan-400">{handSide} HAND</strong>
            </span>
          </div>

          <div className="bg-[#121318] border border-white/10 rounded-xl p-4 flex items-start space-x-3 text-xs text-zinc-300">
            <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5 stroke-[2.5]" />
            <p>
              <strong className="text-white uppercase font-bold">Biometric Acquisition Standard:</strong> For highest-precision ROI landmark alignment, keep fingers naturally splayed with the palm facing directly towards the sensor under uniform illumination.
            </p>
          </div>
        </div>
      )}

      {sourceMode === "camera" && (
        <div className="space-y-4">
          <div className="bg-[#121318] border border-white/10 rounded-2xl p-6 flex flex-col items-center">
            {cameraError ? (
              <div className="text-center py-8">
                <p className="text-rose-400 text-sm font-bold mb-3">{cameraError}</p>
                <button
                  onClick={startCamera}
                  className="px-4 py-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs font-bold uppercase tracking-wider text-zinc-200 inline-flex items-center space-x-2 border border-white/10"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>RETRY CAMERA</span>
                </button>
              </div>
            ) : (
              <div className="relative w-full max-w-lg aspect-[4/3] rounded-xl overflow-hidden bg-black border border-white/10">
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  className="w-full h-full object-cover"
                />

                {/* Hand guide overlay */}
                <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
                  <svg className="w-3/4 h-3/4 opacity-50 animate-pulse" viewBox="0 0 100 100">
                    <path
                      d="M 30 90 C 20 80, 15 60, 15 45 C 15 35, 20 25, 30 25 C 38 25, 40 32, 40 40 C 42 28, 48 18, 55 18 C 62 18, 64 28, 64 38 C 66 28, 72 22, 78 22 C 84 22, 85 30, 85 45 C 85 65, 75 80, 65 90 Z"
                      fill="none"
                      stroke="#06b6d4"
                      strokeWidth="1.5"
                      strokeDasharray="4 3"
                    />
                  </svg>
                  <div className="absolute bottom-4 bg-black/80 backdrop-blur px-3.5 py-1.5 rounded-full text-[10px] text-cyan-300 font-mono font-bold uppercase tracking-widest border border-cyan-500/40">
                    ALIGN {handSide} PALM WITHIN CONTOUR
                  </div>
                </div>
              </div>
            )}

            {isCameraActive && (
              <div className="mt-6 flex items-center space-x-4">
                <button
                  onClick={captureFrame}
                  className="flex items-center space-x-2 px-6 py-3 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-black text-xs font-black uppercase tracking-wider shadow-lg shadow-cyan-500/20 transition cursor-pointer"
                >
                  <Camera className="w-4 h-4 stroke-[2.5]" />
                  <span>CAPTURE PALMPRINT</span>
                </button>
                <button
                  onClick={stopCamera}
                  className="px-4 py-3 rounded-xl bg-zinc-900 hover:bg-zinc-800 text-zinc-300 text-xs font-bold uppercase tracking-wider border border-white/10 cursor-pointer"
                >
                  STOP STREAM
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

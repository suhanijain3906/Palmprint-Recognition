import React, { useState, useEffect, useRef } from "react";
import { BiometricPalmSample, HandLandmarks, ROICropParams, Point2D } from "../types";
import { extractAlignedROI, estimateHandLandmarks } from "../utils/imageProcessing";
import {
  RotateCcw,
  Sliders,
  Eye,
  EyeOff,
  Maximize2,
  CheckCircle,
  HelpCircle,
  Sparkles,
} from "lucide-react";

interface ROIExtractorProps {
  sample: BiometricPalmSample;
  onUpdateSample: (updated: BiometricPalmSample) => void;
}

export const ROIExtractor: React.FC<ROIExtractorProps> = ({
  sample,
  onUpdateSample,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [landmarks, setLandmarks] = useState<HandLandmarks>(sample.landmarks);
  const [roiParams, setRoiParams] = useState<ROICropParams>(sample.roiParams);
  const [extractedDataUrl, setExtractedDataUrl] = useState<string>(sample.roiImageDataUrl || "");

  // Visualization toggles
  const [showValleys, setShowValleys] = useState(true);
  const [showBaseline, setShowBaseline] = useState(true);
  const [showROIBound, setShowROIBound] = useState(true);
  const [showPrincipalLines, setShowPrincipalLines] = useState(true);

  // Dragging state
  const [draggingPoint, setDraggingPoint] = useState<"v1" | "v2" | "center" | null>(null);

  const imageElementRef = useRef<HTMLImageElement | null>(null);

  // Load sample image
  useEffect(() => {
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => {
      imageElementRef.current = img;
      renderCanvas();
      performROIExtraction(img, landmarks, roiParams);
    };
    img.src = sample.sourceImageUrl;
  }, [sample.sourceImageUrl]);

  // Re-extract whenever landmarks or roiParams change
  const performROIExtraction = (
    img: HTMLImageElement,
    currentLandmarks: HandLandmarks,
    currentRoiParams: ROICropParams
  ) => {
    try {
      const { roiCanvas, roiDataUrl, params } = extractAlignedROI(
        img,
        currentLandmarks,
        128,
        currentRoiParams
      );
      setExtractedDataUrl(roiDataUrl);
      setRoiParams(params);

      // Propagate update to parent sample
      onUpdateSample({
        ...sample,
        landmarks: currentLandmarks,
        roiParams: params,
        roiImageDataUrl: roiDataUrl,
      });
    } catch (err) {
      console.error("ROI Extraction failed:", err);
    }
  };

  // Render original image with landmark annotations on canvas
  const renderCanvas = () => {
    const canvas = canvasRef.current;
    const img = imageElementRef.current;
    if (!canvas || !img) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    canvas.width = img.width || 400;
    canvas.height = img.height || 480;

    // Draw base image
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, 0, 0);

    const v1 = landmarks.valleyIndexMiddle;
    const v2 = landmarks.valleyRingLittle;
    const vMid = landmarks.valleyMiddleRing;
    const v0 = landmarks.valleyThumbIndex;
    const center = roiParams.center;

    // 1. Draw Principal Lines if enabled
    if (showPrincipalLines && landmarks.principalLines) {
      const { lifeLine, headLine, heartLine } = landmarks.principalLines;

      const drawSmoothLine = (pts: Point2D[], strokeColor: string) => {
        if (pts.length < 2) return;
        ctx.beginPath();
        ctx.moveTo(pts[0].x, pts[0].y);
        for (let i = 1; i < pts.length; i++) {
          ctx.lineTo(pts[i].x, pts[i].y);
        }
        ctx.strokeStyle = strokeColor;
        ctx.lineWidth = 2.5;
        ctx.lineCap = "round";
        ctx.stroke();
      };

      drawSmoothLine(lifeLine, "#f43f5e"); // Life line (Rose)
      drawSmoothLine(headLine, "#38bdf8"); // Head line (Sky Blue)
      drawSmoothLine(heartLine, "#a855f7"); // Heart line (Purple)
    }

    // 2. Draw Baseline & Coordinate Frame
    if (showBaseline) {
      ctx.beginPath();
      ctx.moveTo(v1.x, v1.y);
      ctx.lineTo(v2.x, v2.y);
      ctx.strokeStyle = "#06b6d4";
      ctx.lineWidth = 2;
      ctx.setLineDash([4, 4]);
      ctx.stroke();
      ctx.setLineDash([]);

      // Baseline Midpoint
      const midX = (v1.x + v2.x) / 2;
      const midY = (v1.y + v2.y) / 2;

      // Normal vector to center
      ctx.beginPath();
      ctx.moveTo(midX, midY);
      ctx.lineTo(center.x, center.y);
      ctx.strokeStyle = "#eab308";
      ctx.lineWidth = 1.5;
      ctx.setLineDash([2, 2]);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // 3. Draw Rotated ROI Square Bounding Box
    if (showROIBound) {
      const halfSide = roiParams.squareSize / 2;
      const angleRad = (roiParams.angleDegrees * Math.PI) / 180;

      ctx.save();
      ctx.translate(center.x, center.y);
      ctx.rotate(angleRad);

      // ROI semi-transparent fill
      ctx.fillStyle = "rgba(6, 182, 212, 0.12)";
      ctx.fillRect(-halfSide, -halfSide, roiParams.squareSize, roiParams.squareSize);

      // ROI border
      ctx.strokeStyle = "#22d3ee";
      ctx.lineWidth = 2.5;
      ctx.strokeRect(-halfSide, -halfSide, roiParams.squareSize, roiParams.squareSize);

      // Center crosshair
      ctx.beginPath();
      ctx.moveTo(-8, 0);
      ctx.lineTo(8, 0);
      ctx.moveTo(0, -8);
      ctx.lineTo(0, 8);
      ctx.strokeStyle = "#eab308";
      ctx.lineWidth = 2;
      ctx.stroke();

      ctx.restore();
    }

    // 4. Draw Valley Landmark points
    if (showValleys) {
      const drawHandle = (pt: Point2D, label: string, color: string, radius: number = 7) => {
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, radius, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
        ctx.lineWidth = 2;
        ctx.strokeStyle = "#ffffff";
        ctx.stroke();

        // Label pill
        ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
        ctx.fillRect(pt.x + 8, pt.y - 12, 28, 16);
        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 10px monospace";
        ctx.fillText(label, pt.x + 12, pt.y);
      };

      drawHandle(v1, "V1", "#06b6d4", 8); // Index-Middle Valley
      drawHandle(v2, "V2", "#10b981", 8); // Ring-Little Valley
      drawHandle(vMid, "Vm", "#a855f7", 5);
      drawHandle(v0, "V0", "#f97316", 5);
    }
  };

  useEffect(() => {
    renderCanvas();
  }, [landmarks, roiParams, showValleys, showBaseline, showROIBound, showPrincipalLines]);

  // Handle Mouse/Touch Interaction on Canvas for dragging landmarks
  const handleCanvasMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const mouseX = (e.clientX - rect.left) * scaleX;
    const mouseY = (e.clientY - rect.top) * scaleY;

    const hitRadius = 16;
    const distV1 = Math.hypot(mouseX - landmarks.valleyIndexMiddle.x, mouseY - landmarks.valleyIndexMiddle.y);
    const distV2 = Math.hypot(mouseX - landmarks.valleyRingLittle.x, mouseY - landmarks.valleyRingLittle.y);
    const distCenter = Math.hypot(mouseX - roiParams.center.x, mouseY - roiParams.center.y);

    if (distV1 < hitRadius) {
      setDraggingPoint("v1");
    } else if (distV2 < hitRadius) {
      setDraggingPoint("v2");
    } else if (distCenter < hitRadius) {
      setDraggingPoint("center");
    }
  };

  const handleCanvasMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!draggingPoint) return;
    const canvas = canvasRef.current;
    const img = imageElementRef.current;
    if (!canvas || !img) return;

    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const mouseX = Math.max(0, Math.min(canvas.width, (e.clientX - rect.left) * scaleX));
    const mouseY = Math.max(0, Math.min(canvas.height, (e.clientY - rect.top) * scaleY));

    let updatedLandmarks = { ...landmarks };
    let updatedRoiParams = { ...roiParams };

    if (draggingPoint === "v1") {
      updatedLandmarks.valleyIndexMiddle = { x: mouseX, y: mouseY };
    } else if (draggingPoint === "v2") {
      updatedLandmarks.valleyRingLittle = { x: mouseX, y: mouseY };
    } else if (draggingPoint === "center") {
      updatedRoiParams.center = { x: mouseX, y: mouseY };
    }

    setLandmarks(updatedLandmarks);
    setRoiParams(updatedRoiParams);
    performROIExtraction(img, updatedLandmarks, updatedRoiParams);
  };

  const handleCanvasMouseUp = () => {
    setDraggingPoint(null);
  };

  // Reset to auto-estimated landmarks
  const handleResetToAuto = () => {
    const img = imageElementRef.current;
    if (!img) return;
    const autoLandmarks = estimateHandLandmarks(img.width, img.height, sample.handSide);
    setLandmarks(autoLandmarks);
    const dx = autoLandmarks.valleyRingLittle.x - autoLandmarks.valleyIndexMiddle.x;
    const dy = autoLandmarks.valleyRingLittle.y - autoLandmarks.valleyIndexMiddle.y;
    const dist = Math.sqrt(dx * dx + dy * dy);
    const angle = (Math.atan2(dy, dx) * 180) / Math.PI;

    const defaultParams: ROICropParams = {
      squareSize: dist * 0.95,
      angleDegrees: angle,
      center: autoLandmarks.palmCenter,
      offsetX: 0,
      offsetY: 0,
      scale: 1.0,
      v1: autoLandmarks.valleyIndexMiddle,
      v2: autoLandmarks.valleyRingLittle,
    };
    setRoiParams(defaultParams);
    performROIExtraction(img, autoLandmarks, defaultParams);
  };

  return (
    <div className="space-y-6">
      {/* Header info */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-[#121318] border border-white/10 p-5 rounded-2xl shadow-xl">
        <div>
          <div className="flex items-center space-x-2.5 mb-1">
            <h2 className="text-xl font-black tracking-tight text-white uppercase">
              Landmark Detection & Canonical ROI Alignment
            </h2>
            <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 font-mono font-bold uppercase tracking-widest">
              ZHANG-KONG PROTOCOL
            </span>
          </div>
          <p className="text-xs font-medium text-zinc-400">
            Drag landmark handles on the canvas or adjust calibrated parameters to align the local palmprint coordinate frame ($V_1 \to V_2$).
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={handleResetToAuto}
            className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-zinc-900 hover:bg-zinc-800 border border-white/10 text-zinc-200 text-xs font-bold uppercase tracking-wider transition cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>AUTO LANDMARKS</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Main Canvas Viewport (7 cols) */}
        <div className="lg:col-span-7 bg-[#121318] border border-white/10 rounded-2xl p-5 flex flex-col items-center justify-center shadow-xl">
          <div className="flex items-center justify-between w-full mb-3 text-xs">
            <span className="font-mono font-bold uppercase text-[11px] tracking-wider text-zinc-300">
              GEOMETRY INSPECTOR • {sample.handSide.toUpperCase()} HAND
            </span>
            <div className="flex items-center space-x-3 text-zinc-400 font-mono text-[11px] font-bold uppercase">
              <label className="flex items-center space-x-1.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={showValleys}
                  onChange={(e) => setShowValleys(e.target.checked)}
                  className="rounded bg-zinc-800 border-white/10 text-cyan-500"
                />
                <span>VALLEYS (V1, V2)</span>
              </label>
              <label className="flex items-center space-x-1.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={showROIBound}
                  onChange={(e) => setShowROIBound(e.target.checked)}
                  className="rounded bg-zinc-800 border-white/10 text-cyan-500"
                />
                <span>ROI BOX</span>
              </label>
              <label className="flex items-center space-x-1.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={showPrincipalLines}
                  onChange={(e) => setShowPrincipalLines(e.target.checked)}
                  className="rounded bg-zinc-800 border-white/10 text-cyan-500"
                />
                <span>PRINCIPAL LINES</span>
              </label>
            </div>
          </div>

          {/* Canvas container */}
          <div className="relative border border-white/10 rounded-xl overflow-hidden bg-black shadow-inner max-w-full">
            <canvas
              ref={canvasRef}
              onMouseDown={handleCanvasMouseDown}
              onMouseMove={handleCanvasMouseMove}
              onMouseUp={handleCanvasMouseUp}
              onMouseLeave={handleCanvasMouseUp}
              className="cursor-crosshair max-h-[460px] w-auto object-contain block mx-auto"
            />
          </div>

          <div className="w-full mt-3 flex items-center justify-between text-[11px] text-zinc-400 font-mono font-bold uppercase">
            <span>DRAG V1 (CYAN), V2 (EMERALD), OR CENTER CROSSHAIR (YELLOW)</span>
            <span>FRAME: {imageElementRef.current?.width || 400} × {imageElementRef.current?.height || 480} PX</span>
          </div>
        </div>

        {/* ROI Sub-window & Controls (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          {/* Extracted 128x128 Preview Card */}
          <div className="bg-[#121318] border border-white/10 rounded-2xl p-5 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                <div className="w-2.5 h-2.5 rounded-full bg-cyan-400 shadow-sm shadow-cyan-400/50" />
                <h3 className="text-sm font-black tracking-tight text-white uppercase">Canonical ROI Sub-window</h3>
              </div>
              <span className="text-xs px-2.5 py-1 rounded bg-white/5 text-cyan-300 font-mono font-bold uppercase tracking-wider border border-white/10">
                128 × 128 PX
              </span>
            </div>

            <div className="flex items-center justify-center p-5 bg-black rounded-xl border border-white/10">
              {extractedDataUrl ? (
                <div className="relative group">
                  <img
                    src={extractedDataUrl}
                    alt="Aligned Palmprint ROI"
                    className="w-36 h-36 rounded-lg object-contain shadow-xl border-2 border-cyan-400"
                  />
                </div>
              ) : (
                <div className="w-36 h-36 flex items-center justify-center text-zinc-500 font-mono text-xs font-bold uppercase">
                  EXTRACTING ROI...
                </div>
              )}
            </div>

            {/* Coordinate Frame Metrics */}
            <div className="grid grid-cols-2 gap-2.5 mt-4 text-xs font-mono">
              <div className="bg-black/50 p-2.5 rounded-xl border border-white/10">
                <span className="text-zinc-400 block text-[10px] font-bold uppercase tracking-wider">BASELINE DIST:</span>
                <span className="text-white font-black text-sm">
                  {Math.round(Math.hypot(landmarks.valleyRingLittle.x - landmarks.valleyIndexMiddle.x, landmarks.valleyRingLittle.y - landmarks.valleyIndexMiddle.y))} px
                </span>
              </div>
              <div className="bg-black/50 p-2.5 rounded-xl border border-white/10">
                <span className="text-zinc-400 block text-[10px] font-bold uppercase tracking-wider">ALIGNMENT ANGLE:</span>
                <span className="text-white font-black text-sm">
                  {Math.round(roiParams.angleDegrees * 10) / 10}°
                </span>
              </div>
              <div className="bg-black/50 p-2.5 rounded-xl border border-white/10">
                <span className="text-zinc-400 block text-[10px] font-bold uppercase tracking-wider">CENTER (X, Y):</span>
                <span className="text-white font-black text-sm">
                  ({Math.round(roiParams.center.x)}, {Math.round(roiParams.center.y)})
                </span>
              </div>
              <div className="bg-black/50 p-2.5 rounded-xl border border-white/10">
                <span className="text-zinc-400 block text-[10px] font-bold uppercase tracking-wider">ROI CROP SIZE:</span>
                <span className="text-white font-black text-sm">
                  {Math.round(roiParams.squareSize)} px
                </span>
              </div>
            </div>
          </div>

          {/* Geometric Fine-Tuning Slider Controls */}
          <div className="bg-[#121318] border border-white/10 rounded-2xl p-5 shadow-xl space-y-4">
            <h3 className="text-xs font-mono font-black text-white uppercase tracking-wider flex items-center space-x-2">
              <Sliders className="w-3.5 h-3.5 text-cyan-400 stroke-[2.5]" />
              <span>GEOMETRIC CALIBRATION CONTROLS</span>
            </h3>

            {/* Scale Slider */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-mono">
                <span className="text-zinc-400 font-bold uppercase text-[11px]">WINDOW SCALE:</span>
                <span className="text-cyan-400 font-black">{Math.round(roiParams.scale * 100)}%</span>
              </div>
              <input
                type="range"
                min="0.6"
                max="1.5"
                step="0.02"
                value={roiParams.scale}
                onChange={(e) => {
                  const scale = parseFloat(e.target.value);
                  const updated = { ...roiParams, scale };
                  setRoiParams(updated);
                  if (imageElementRef.current) {
                    performROIExtraction(imageElementRef.current, landmarks, updated);
                  }
                }}
                className="w-full accent-cyan-400 cursor-pointer"
              />
            </div>

            {/* Rotation Offset Slider */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-mono">
                <span className="text-zinc-400 font-bold uppercase text-[11px]">ANGLE OFFSET:</span>
                <span className="text-cyan-400 font-black">
                  {Math.round((roiParams.angleDegrees - ((Math.atan2(landmarks.valleyRingLittle.y - landmarks.valleyIndexMiddle.y, landmarks.valleyRingLittle.x - landmarks.valleyIndexMiddle.x) * 180) / Math.PI)) * 10) / 10}°
                </span>
              </div>
              <input
                type="range"
                min="-25"
                max="25"
                step="0.5"
                value={roiParams.angleDegrees - ((Math.atan2(landmarks.valleyRingLittle.y - landmarks.valleyIndexMiddle.y, landmarks.valleyRingLittle.x - landmarks.valleyIndexMiddle.x) * 180) / Math.PI)}
                onChange={(e) => {
                  const offset = parseFloat(e.target.value);
                  const baseAngle = (Math.atan2(landmarks.valleyRingLittle.y - landmarks.valleyIndexMiddle.y, landmarks.valleyRingLittle.x - landmarks.valleyIndexMiddle.x) * 180) / Math.PI;
                  const updated = { ...roiParams, angleDegrees: baseAngle + offset };
                  setRoiParams(updated);
                  if (imageElementRef.current) {
                    performROIExtraction(imageElementRef.current, landmarks, updated);
                  }
                }}
                className="w-full accent-cyan-400 cursor-pointer"
              />
            </div>

            {/* Vertical & Horizontal Offset */}
            <div className="grid grid-cols-2 gap-3 pt-1">
              <div className="space-y-1">
                <span className="text-[10px] font-mono font-bold uppercase text-zinc-400">OFFSET X:</span>
                <input
                  type="range"
                  min="-40"
                  max="40"
                  value={roiParams.offsetX}
                  onChange={(e) => {
                    const offsetX = parseInt(e.target.value, 10);
                    const updated = { ...roiParams, offsetX };
                    setRoiParams(updated);
                    if (imageElementRef.current) {
                      performROIExtraction(imageElementRef.current, landmarks, updated);
                    }
                  }}
                  className="w-full accent-cyan-400 cursor-pointer"
                />
              </div>
              <div className="space-y-1">
                <span className="text-[10px] font-mono font-bold uppercase text-zinc-400">OFFSET Y:</span>
                <input
                  type="range"
                  min="-40"
                  max="40"
                  value={roiParams.offsetY}
                  onChange={(e) => {
                    const offsetY = parseInt(e.target.value, 10);
                    const updated = { ...roiParams, offsetY };
                    setRoiParams(updated);
                    if (imageElementRef.current) {
                      performROIExtraction(imageElementRef.current, landmarks, updated);
                    }
                  }}
                  className="w-full accent-cyan-400 cursor-pointer"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

import React, { useState, useEffect, useRef } from "react";
import { BiometricPalmSample, GaborFilterParams } from "../types";
import {
  toGrayscaleMatrix,
  applyCLAHE,
  extractCompCode,
  generateGaborKernel,
  grayscaleToImageData,
} from "../utils/imageProcessing";
import {
  Sparkles,
  Sliders,
  Layers,
  Activity,
  Maximize2,
  RefreshCw,
  Cpu,
  Info,
} from "lucide-react";

interface EnhancementSuiteProps {
  sample: BiometricPalmSample;
  onUpdateSample: (updated: BiometricPalmSample) => void;
}

export const EnhancementSuite: React.FC<EnhancementSuiteProps> = ({
  sample,
  onUpdateSample,
}) => {
  // Gabor Parameters
  const [gaborParams, setGaborParams] = useState<GaborFilterParams>({
    wavelength: 8.0,
    orientationCount: 6,
    sigma: 5.0,
    gamma: 0.5,
    psi: 0,
    kernelSize: 21,
  });

  // CLAHE Parameters
  const [claheClipLimit, setClaheClipLimit] = useState(2.5);
  const [claheGridSize, setClaheGridSize] = useState(8);
  const [enableCLAHE, setEnableCLAHE] = useState(true);

  // Active viewing tab inside enhancement suite
  const [viewMode, setViewMode] = useState<"compcode" | "kernels" | "responses" | "clahe">("compcode");

  // Output images & canvases
  const [compCodeUrl, setCompCodeUrl] = useState<string>("");
  const [claheUrl, setClaheUrl] = useState<string>("");
  const [responseUrls, setResponseUrls] = useState<string[]>([]);
  const [kernelUrls, setKernelUrls] = useState<string[]>([]);
  const [activeKernelOri, setActiveKernelOri] = useState<number>(0);

  // Processing trigger
  useEffect(() => {
    if (!sample.roiImageDataUrl) return;

    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => {
      processEnhancement(img);
    };
    img.src = sample.roiImageDataUrl;
  }, [sample.roiImageDataUrl, gaborParams, enableCLAHE, claheClipLimit, claheGridSize]);

  const processEnhancement = (roiImg: HTMLImageElement) => {
    const width = roiImg.width || 128;
    const height = roiImg.height || 128;

    const tempCanvas = document.createElement("canvas");
    tempCanvas.width = width;
    tempCanvas.height = height;
    const ctx = tempCanvas.getContext("2d");
    if (!ctx) return;

    ctx.drawImage(roiImg, 0, 0);
    const rawImageData = ctx.getImageData(0, 0, width, height);
    const { matrix: rawGrayMatrix } = toGrayscaleMatrix(rawImageData);

    // Apply CLAHE if enabled
    let processedGray = rawGrayMatrix;
    if (enableCLAHE) {
      processedGray = applyCLAHE(rawGrayMatrix, width, height, claheGridSize, claheClipLimit);
      const claheImgData = grayscaleToImageData(processedGray, width, height);
      ctx.putImageData(claheImgData, 0, 0);
      setClaheUrl(tempCanvas.toDataURL("image/png"));
    } else {
      setClaheUrl(sample.roiImageDataUrl || "");
    }

    // Extract Competitive Code & Gabor Responses
    const { features, filteredResponses, compCodeCanvas, compCodeDataUrl } = extractCompCode(
      processedGray,
      width,
      height,
      gaborParams
    );

    setCompCodeUrl(compCodeDataUrl);

    // Generate thumbnails for the 6 orientation responses
    const respThumbnails: string[] = [];
    filteredResponses.forEach((resp) => {
      // Normalize response [-max, max] into [0, 255]
      let maxVal = 0.001;
      for (let i = 0; i < resp.length; i++) {
        if (Math.abs(resp[i]) > maxVal) maxVal = Math.abs(resp[i]);
      }

      const normMatrix = new Float32Array(resp.length);
      for (let i = 0; i < resp.length; i++) {
        normMatrix[i] = ((resp[i] / maxVal) * 0.5 + 0.5) * 255;
      }

      const respImgData = grayscaleToImageData(normMatrix, width, height);
      ctx.putImageData(respImgData, 0, 0);
      respThumbnails.push(tempCanvas.toDataURL("image/png"));
    });
    setResponseUrls(respThumbnails);

    // Generate visualization of Gabor Kernels
    const kUrls: string[] = [];
    const kSize = gaborParams.kernelSize;
    const kCanvas = document.createElement("canvas");
    kCanvas.width = kSize;
    kCanvas.height = kSize;
    const kCtx = kCanvas.getContext("2d");

    for (let j = 0; j < gaborParams.orientationCount; j++) {
      const theta = (j * Math.PI) / gaborParams.orientationCount;
      const { kernel } = generateGaborKernel(
        theta,
        gaborParams.wavelength,
        gaborParams.sigma,
        gaborParams.gamma,
        gaborParams.psi,
        gaborParams.kernelSize
      );

      let maxK = 0.001;
      for (let i = 0; i < kernel.length; i++) {
        if (Math.abs(kernel[i]) > maxK) maxK = Math.abs(kernel[i]);
      }

      const kNorm = new Float32Array(kernel.length);
      for (let i = 0; i < kernel.length; i++) {
        kNorm[i] = ((kernel[i] / maxK) * 0.5 + 0.5) * 255;
      }

      if (kCtx) {
        const kImgData = grayscaleToImageData(kNorm, kSize, kSize);
        kCtx.putImageData(kImgData, 0, 0);
        kUrls.push(kCanvas.toDataURL("image/png"));
      }
    }
    setKernelUrls(kUrls);

    // Propagate updated features to parent sample
    onUpdateSample({
      ...sample,
      enhancedImageUrl: claheUrl,
      compCodeImageUrl: compCodeDataUrl,
      features,
    });
  };

  const orientationLabels = ["0°", "30°", "60°", "90°", "120°", "150°"];
  const orientationColors = [
    { label: "0°", hex: "#ef4444" },
    { label: "30°", hex: "#f97316" },
    { label: "60°", hex: "#eab308" },
    { label: "90°", hex: "#22c55e" },
    { label: "120°", hex: "#3b82f6" },
    { label: "150°", hex: "#a855f7" },
  ];

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-[#121318] border border-white/10 p-5 rounded-2xl shadow-xl">
        <div>
          <div className="flex items-center space-x-2.5 mb-1">
            <h2 className="text-xl font-black tracking-tight text-white uppercase">
              2D Gabor Filter Bank & Competitive Coding (CompCode)
            </h2>
            <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 font-mono font-bold uppercase tracking-widest">
              6-ORIENTATION PHASE SPACE
            </span>
          </div>
          <p className="text-xs font-medium text-zinc-400">
            Dominant orientation competitive coding (arg min I * ψ_θ) extracts palm line valleys invariant to illumination shifts.
          </p>
        </div>

        {/* View mode toggle */}
        <div className="flex items-center space-x-1 bg-black/50 p-1.5 rounded-xl border border-white/10 text-xs font-mono font-bold uppercase">
          <button
            onClick={() => setViewMode("compcode")}
            className={`px-3 py-1.5 rounded-lg transition cursor-pointer ${
              viewMode === "compcode" ? "bg-white text-black shadow-md font-black" : "text-zinc-400 hover:text-white"
            }`}
          >
            CompCode
          </button>
          <button
            onClick={() => setViewMode("clahe")}
            className={`px-3 py-1.5 rounded-lg transition cursor-pointer ${
              viewMode === "clahe" ? "bg-white text-black shadow-md font-black" : "text-zinc-400 hover:text-white"
            }`}
          >
            CLAHE
          </button>
          <button
            onClick={() => setViewMode("responses")}
            className={`px-3 py-1.5 rounded-lg transition cursor-pointer ${
              viewMode === "responses" ? "bg-white text-black shadow-md font-black" : "text-zinc-400 hover:text-white"
            }`}
          >
            Responses
          </button>
          <button
            onClick={() => setViewMode("kernels")}
            className={`px-3 py-1.5 rounded-lg transition cursor-pointer ${
              viewMode === "kernels" ? "bg-white text-black shadow-md font-black" : "text-zinc-400 hover:text-white"
            }`}
          >
            Kernels
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Visualizer Display (7 cols) */}
        <div className="lg:col-span-7 bg-[#121318] border border-white/10 rounded-2xl p-5 flex flex-col items-center justify-between shadow-xl">
          <div className="w-full flex items-center justify-between mb-4">
            <span className="text-xs font-black text-white uppercase tracking-wider font-mono">
              {viewMode === "compcode" && "COMPETITIVE CODE (COMPCODE) ORIENTATION MATRIX"}
              {viewMode === "clahe" && "CLAHE CONTRAST LIMITED ADAPTIVE HISTOGRAM EQUALIZATION"}
              {viewMode === "responses" && "INDIVIDUAL 6-DIRECTIONAL GABOR CONVOLUTIONS"}
              {viewMode === "kernels" && "2D GABOR WAVELET IMPULSE RESPONSE KERNELS"}
            </span>
            <span className="text-[10px] font-mono font-bold uppercase tracking-widest text-cyan-400 bg-cyan-500/10 px-2.5 py-1 rounded border border-cyan-500/30">
              128 × 128 FEATURE SPACE
            </span>
          </div>

          {/* Center Main Visualization */}
          <div className="w-full flex flex-col items-center justify-center p-6 bg-black rounded-xl border border-white/10 min-h-[320px]">
            {viewMode === "compcode" && (
              <div className="flex flex-col items-center space-y-4">
                <div className="relative group">
                  <img
                    src={compCodeUrl}
                    alt="CompCode Feature Map"
                    className="w-56 h-56 rounded-xl object-contain shadow-2xl border-2 border-cyan-400"
                  />
                </div>

                {/* 6-Orientation Color Legend */}
                <div className="flex flex-wrap justify-center gap-2 pt-2">
                  {orientationColors.map((item) => (
                    <div
                      key={item.label}
                      className="flex items-center space-x-1.5 px-3 py-1 rounded-lg bg-[#121318] border border-white/10 text-xs font-mono font-bold"
                    >
                      <span
                        className="w-3 h-3 rounded-sm shadow-sm"
                        style={{ backgroundColor: item.hex }}
                      />
                      <span className="text-zinc-200">{item.label}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {viewMode === "clahe" && (
              <div className="grid grid-cols-2 gap-6 items-center">
                <div className="flex flex-col items-center space-y-2">
                  <span className="text-xs font-mono font-bold uppercase text-zinc-400">RAW INPUT ROI:</span>
                  <img
                    src={sample.roiImageDataUrl}
                    alt="Raw ROI"
                    className="w-40 h-40 rounded-lg object-contain border border-white/10 bg-black"
                  />
                </div>
                <div className="flex flex-col items-center space-y-2">
                  <span className="text-xs font-mono font-bold uppercase text-cyan-400">CLAHE ENHANCED:</span>
                  <img
                    src={claheUrl}
                    alt="CLAHE Enhanced"
                    className="w-40 h-40 rounded-lg object-contain border-2 border-cyan-400 bg-black shadow-lg"
                  />
                </div>
              </div>
            )}

            {viewMode === "responses" && (
              <div className="grid grid-cols-3 gap-3 w-full">
                {responseUrls.map((url, idx) => (
                  <div
                    key={idx}
                    className="flex flex-col items-center bg-[#121318] p-2.5 rounded-xl border border-white/10"
                  >
                    <span className="text-[10px] font-mono font-bold uppercase text-cyan-400 mb-1">
                      θ = {orientationLabels[idx]}
                    </span>
                    <img
                      src={url}
                      alt={`Gabor response ${idx}`}
                      className="w-24 h-24 rounded-lg object-contain border border-white/10 bg-black"
                    />
                  </div>
                ))}
              </div>
            )}

            {viewMode === "kernels" && (
              <div className="space-y-4 w-full flex flex-col items-center">
                <div className="grid grid-cols-6 gap-2">
                  {kernelUrls.map((kUrl, idx) => (
                    <button
                      key={idx}
                      onClick={() => setActiveKernelOri(idx)}
                      className={`flex flex-col items-center p-2 rounded-xl transition cursor-pointer ${
                        activeKernelOri === idx
                          ? "bg-cyan-500/20 border-2 border-cyan-400 shadow-md"
                          : "bg-[#121318] border border-white/10 hover:border-white/20"
                      }`}
                    >
                      <span className="text-[10px] font-mono font-bold uppercase text-zinc-300 mb-1">
                        {orientationLabels[idx]}
                      </span>
                      <img
                        src={kUrl}
                        alt={`Kernel ${idx}`}
                        className="w-12 h-12 rounded object-contain pixelated bg-black"
                      />
                    </button>
                  ))}
                </div>

                <div className="bg-[#121318] p-4 rounded-xl border border-white/10 text-xs font-mono max-w-md w-full text-zinc-300 space-y-1">
                  <div className="text-cyan-400 font-bold uppercase mb-1">
                    Gabor Kernel Formulation at θ = {orientationLabels[activeKernelOri]}:
                  </div>
                  <div className="text-[11px] text-zinc-400">
                    {"G(x', y') = exp(-(x'^2 + γ^2 y'^2)/(2σ^2)) · cos(2πx'/λ)"}
                  </div>
                  <div className="text-[11px] text-zinc-400">
                    Kernel Window: {gaborParams.kernelSize} × {gaborParams.kernelSize} px | DC Bias Removed
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="w-full mt-4 flex items-center justify-between text-xs text-zinc-400 font-mono font-bold uppercase">
            <span className="flex items-center space-x-1.5">
              <Cpu className="w-3.5 h-3.5 text-cyan-400 stroke-[2.5]" />
              <span>Real-time 2D Spatial Convolution</span>
            </span>
            <span className="text-cyan-400">CompCode: 3-bit Gray Coding</span>
          </div>
        </div>

        {/* Hyperparameter Controls (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          {/* Gabor Parameters Card */}
          <div className="bg-[#121318] border border-white/10 rounded-2xl p-5 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-mono font-black text-white uppercase tracking-wider flex items-center space-x-2">
                <Sliders className="w-3.5 h-3.5 text-cyan-400 stroke-[2.5]" />
                <span>GABOR WAVELET HYPERPARAMETERS</span>
              </h3>
              <span className="text-[10px] text-cyan-400 font-mono font-bold uppercase">IEEE TPAMI</span>
            </div>

            {/* Wavelength Lambda */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-mono">
                <span className="text-zinc-400 font-bold uppercase text-[11px]">WAVELENGTH (λ):</span>
                <span className="text-cyan-400 font-black">{gaborParams.wavelength} px</span>
              </div>
              <input
                type="range"
                min="4"
                max="16"
                step="0.5"
                value={gaborParams.wavelength}
                onChange={(e) =>
                  setGaborParams({ ...gaborParams, wavelength: parseFloat(e.target.value) })
                }
                className="w-full accent-cyan-400 cursor-pointer"
              />
            </div>

            {/* Gaussian Bandwidth Sigma */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-mono">
                <span className="text-zinc-400 font-bold uppercase text-[11px]">VARIANCE (σ):</span>
                <span className="text-cyan-400 font-black">{gaborParams.sigma}</span>
              </div>
              <input
                type="range"
                min="2.0"
                max="10.0"
                step="0.2"
                value={gaborParams.sigma}
                onChange={(e) =>
                  setGaborParams({ ...gaborParams, sigma: parseFloat(e.target.value) })
                }
                className="w-full accent-cyan-400 cursor-pointer"
              />
            </div>

            {/* Aspect Ratio Gamma */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-mono">
                <span className="text-zinc-400 font-bold uppercase text-[11px]">ASPECT RATIO (γ):</span>
                <span className="text-cyan-400 font-black">{gaborParams.gamma}</span>
              </div>
              <input
                type="range"
                min="0.2"
                max="1.0"
                step="0.05"
                value={gaborParams.gamma}
                onChange={(e) =>
                  setGaborParams({ ...gaborParams, gamma: parseFloat(e.target.value) })
                }
                className="w-full accent-cyan-400 cursor-pointer"
              />
            </div>

            {/* Kernel Size Selector */}
            <div className="space-y-1.5 pt-1">
              <span className="text-[11px] font-mono font-bold uppercase text-zinc-400 block">KERNEL SIZE (K × K):</span>
              <div className="grid grid-cols-4 gap-2">
                {[15, 21, 27, 35].map((size) => (
                  <button
                    key={size}
                    onClick={() => setGaborParams({ ...gaborParams, kernelSize: size })}
                    className={`py-2 rounded-lg text-xs font-mono font-bold uppercase transition cursor-pointer ${
                      gaborParams.kernelSize === size
                        ? "bg-cyan-500 text-black font-black shadow-md shadow-cyan-500/20"
                        : "bg-white/5 hover:bg-white/10 text-zinc-300 border border-white/10"
                    }`}
                  >
                    {size}×{size}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* CLAHE Preprocessing Card */}
          <div className="bg-[#121318] border border-white/10 rounded-2xl p-5 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-mono font-black text-white uppercase tracking-wider flex items-center space-x-2">
                <Layers className="w-3.5 h-3.5 text-cyan-400 stroke-[2.5]" />
                <span>CLAHE RIDGE ENHANCEMENT</span>
              </h3>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={enableCLAHE}
                  onChange={(e) => setEnableCLAHE(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-9 h-5 bg-zinc-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-black after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-zinc-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-cyan-500"></div>
              </label>
            </div>

            {enableCLAHE && (
              <div className="space-y-3 pt-1">
                <div className="space-y-1">
                  <div className="flex justify-between text-xs font-mono">
                    <span className="text-zinc-400 font-bold uppercase text-[11px]">CLIP LIMIT:</span>
                    <span className="text-cyan-400 font-black">{claheClipLimit}</span>
                  </div>
                  <input
                    type="range"
                    min="1.0"
                    max="6.0"
                    step="0.2"
                    value={claheClipLimit}
                    onChange={(e) => setClaheClipLimit(parseFloat(e.target.value))}
                    className="w-full accent-cyan-400 cursor-pointer"
                  />
                </div>

                <div className="space-y-1">
                  <div className="flex justify-between text-xs font-mono">
                    <span className="text-zinc-400 font-bold uppercase text-[11px]">CONTEXT TILES:</span>
                    <span className="text-cyan-400 font-black">{claheGridSize} × {claheGridSize}</span>
                  </div>
                  <input
                    type="range"
                    min="4"
                    max="16"
                    step="2"
                    value={claheGridSize}
                    onChange={(e) => setClaheGridSize(parseInt(e.target.value, 10))}
                    className="w-full accent-cyan-400 cursor-pointer"
                  />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

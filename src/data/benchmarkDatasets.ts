import {
  BiometricPalmSample,
  BenchmarkGallerySubject,
} from "../types";
import {
  estimateHandLandmarks,
} from "../utils/imageProcessing";

/**
 * Generate a realistic research-grade palmprint image as a data URL using SVG canvas
 */
export function generateSyntheticPalmprintDataUrl(
  subjectSeed: number,
  session: number = 1,
  handSide: "Left" | "Right" = "Right",
  noiseLevel: number = 0.05
): string {
  const width = 400;
  const height = 480;
  const isRight = handSide === "Right";

  // Pseudo-random variations based on subject seed & session
  const lineShift = (subjectSeed % 5) * 4 + (session - 1) * 2;
  const curvature = 0.8 + ((subjectSeed * 7) % 10) * 0.05;

  // Palm contour paths
  const handContour = isRight
    ? `M 140 450 
       C 100 420, 70 340, 70 240 
       C 70 190, 80 150, 100 130 
       C 120 110, 140 140, 145 180 
       C 150 120, 160 80, 180 80 
       C 200 80, 205 120, 205 170 
       C 215 110, 230 60, 250 60 
       C 270 60, 275 110, 270 165 
       C 285 115, 305 85, 325 90 
       C 345 95, 340 140, 330 185 
       C 345 160, 370 160, 385 180 
       C 400 200, 380 270, 350 330 
       C 320 400, 280 440, 240 450 Z`
    : `M 260 450 
       C 300 420, 330 340, 330 240 
       C 330 190, 320 150, 300 130 
       C 280 110, 260 140, 255 180 
       C 250 120, 240 80, 220 80 
       C 200 80, 195 120, 195 170 
       C 185 110, 170 60, 150 60 
       C 130 60, 125 110, 130 165 
       C 115 115, 95 85, 75 90 
       C 55 95, 60 140, 70 185 
       C 55 160, 30 160, 15 180 
       C 0 200, 20 270, 50 330 
       C 80 400, 120 440, 160 450 Z`;

  // Dynamic principal palm lines
  const lifeLine = isRight
    ? `M ${120 + lineShift} ${220 + lineShift} Q ${165 + lineShift * 0.5} ${290 * curvature} ${175 + lineShift} 390`
    : `M ${280 - lineShift} ${220 + lineShift} Q ${235 - lineShift * 0.5} ${290 * curvature} ${225 - lineShift} 390`;

  const headLine = isRight
    ? `M ${125 + lineShift} ${225 + lineShift} Q ${210 + lineShift} ${260} ${285 + lineShift} 280`
    : `M ${275 - lineShift} ${225 + lineShift} Q ${190 - lineShift} ${260} ${115 - lineShift} 280`;

  const heartLine = isRight
    ? `M ${310 - lineShift} ${195 + lineShift} Q ${230} ${185 + lineShift} ${150 - lineShift} 205`
    : `M ${90 + lineShift} ${195 + lineShift} Q ${170} ${185 + lineShift} ${250 + lineShift} 205`;

  // Secondary crease lines & ridge textures
  let secondaryLinesSvg = "";
  for (let i = 0; i < 18; i++) {
    const yBase = 200 + i * 11;
    const offset = Math.sin((i + subjectSeed) * 0.8) * 14;
    const x1 = isRight ? 130 + offset : 170 - offset;
    const x2 = isRight ? 290 - offset : 270 + offset;
    secondaryLinesSvg += `<path d="M ${x1} ${yBase} Q ${(x1 + x2) / 2 + offset} ${yBase + 5} ${x2} ${yBase + 2}" stroke="#64748b" stroke-width="1.2" stroke-opacity="0.35" fill="none" />`;
  }

  const svg = `
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}">
    <defs>
      <radialGradient id="skinGrad_${subjectSeed}_${session}" cx="50%" cy="55%" r="50%">
        <stop offset="0%" stop-color="#f5d0b5" />
        <stop offset="60%" stop-color="#e2b492" />
        <stop offset="100%" stop-color="#c99773" />
      </radialGradient>
      <filter id="noiseFilter_${subjectSeed}">
        <feTurbulence type="fractalNoise" baseFrequency="0.04" numOctaves="3" result="noise" />
        <feColorMatrix type="matrix" values="0 0 0 0 0.1  0 0 0 0 0.1  0 0 0 0 0.1  0 0 0 0.25 0" />
        <feBlend in="SourceGraphic" mode="multiply" />
      </filter>
    </defs>
    
    <!-- Background -->
    <rect width="100%" height="100%" fill="#0f172a" />

    <!-- Hand Silhouette -->
    <g filter="url(#noiseFilter_${subjectSeed})">
      <path d="${handContour}" fill="url(#skinGrad_${subjectSeed}_${session})" stroke="#78350f" stroke-width="2.5" />
      
      <!-- Ridge Lines -->
      ${secondaryLinesSvg}
      
      <!-- Principal Palm Lines -->
      <!-- Life Line -->
      <path d="${lifeLine}" stroke="#451a03" stroke-width="3.8" stroke-linecap="round" fill="none" opacity="0.85" />
      <path d="${lifeLine}" stroke="#78350f" stroke-width="1.8" stroke-linecap="round" fill="none" opacity="0.9" />

      <!-- Head Line -->
      <path d="${headLine}" stroke="#451a03" stroke-width="3.5" stroke-linecap="round" fill="none" opacity="0.85" />
      <path d="${headLine}" stroke="#78350f" stroke-width="1.6" stroke-linecap="round" fill="none" opacity="0.9" />

      <!-- Heart Line -->
      <path d="${heartLine}" stroke="#451a03" stroke-width="3.6" stroke-linecap="round" fill="none" opacity="0.85" />
      <path d="${heartLine}" stroke="#78350f" stroke-width="1.7" stroke-linecap="round" fill="none" opacity="0.9" />
    </g>

    <!-- Biometric Metadata Watermark -->
    <text x="20" y="30" fill="#94a3b8" font-family="monospace" font-size="12" opacity="0.7">
      BIO-BENCHMARK: SUBJ_${String(subjectSeed).padStart(3, "0")} | SESS_${session} | ${handSide}
    </text>
  </svg>
  `;

  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
}

/**
 * Preloaded Benchmark Gallery Subjects with Ground-Truth Annotations
 */
export const BENCHMARK_DATASETS: BenchmarkGallerySubject[] = [
  {
    subjectId: "PolyU_001",
    subjectName: "Subject 01 (PolyU 2D)",
    dataset: "PolyU 2D Palmprint Database",
    hand: "Right",
    samples: [
      createBenchmarkSample("PolyU_001", 1, "Right", "PolyU 2D", "Subject 01 - Session 1 (Standard Contact)"),
      createBenchmarkSample("PolyU_001", 2, "Right", "PolyU 2D", "Subject 01 - Session 2 (2-Week Interval)"),
    ],
  },
  {
    subjectId: "PolyU_002",
    subjectName: "Subject 02 (PolyU 2D)",
    dataset: "PolyU 2D Palmprint Database",
    hand: "Right",
    samples: [
      createBenchmarkSample("PolyU_002", 1, "Right", "PolyU 2D", "Subject 02 - Session 1 (High Quality)"),
      createBenchmarkSample("PolyU_002", 2, "Right", "PolyU 2D", "Subject 02 - Session 2 (Slight Rotation)"),
    ],
  },
  {
    subjectId: "IITD_101",
    subjectName: "Subject 101 (IITD Touchless)",
    dataset: "IITD Touchless Palmprint",
    hand: "Right",
    samples: [
      createBenchmarkSample("IITD_101", 1, "Right", "IITD Touchless", "Subject 101 - Touchless Baseline"),
      createBenchmarkSample("IITD_101", 2, "Right", "IITD Touchless", "Subject 101 - Touchless Ambient"),
    ],
  },
  {
    subjectId: "CASIA_201",
    subjectName: "Subject 201 (CASIA Palm)",
    dataset: "CASIA Palmprint Database",
    hand: "Right",
    samples: [
      createBenchmarkSample("CASIA_201", 1, "Right", "CASIA Palm", "Subject 201 - Optical Sensor"),
      createBenchmarkSample("CASIA_201", 2, "Right", "CASIA Palm", "Subject 201 - Optical Re-enrollment"),
    ],
  },
  {
    subjectId: "Tongji_301",
    subjectName: "Subject 301 (Tongji MS)",
    dataset: "Tongji Multi-Spectral",
    hand: "Right",
    samples: [
      createBenchmarkSample("Tongji_301", 1, "Right", "Tongji MS", "Subject 301 - Near Infrared 850nm"),
      createBenchmarkSample("Tongji_301", 2, "Right", "Tongji MS", "Subject 301 - White Light Spectrum"),
    ],
  },
  {
    subjectId: "PolyU_003",
    subjectName: "Subject 03 (PolyU 3D)",
    dataset: "PolyU 3D Palmprint Database",
    hand: "Left",
    samples: [
      createBenchmarkSample("PolyU_003", 1, "Left", "PolyU 3D", "Subject 03 - Left Palm 3D Range Map"),
      createBenchmarkSample("PolyU_003", 2, "Left", "PolyU 3D", "Subject 03 - Left Palm Session 2"),
    ],
  },
];

function createBenchmarkSample(
  subjectId: string,
  session: number,
  handSide: "Left" | "Right",
  datasetName: BiometricPalmSample["datasetName"],
  title: string
): BiometricPalmSample {
  const seed = parseInt(subjectId.replace(/\D/g, ""), 10) || 1;
  const sourceImageUrl = generateSyntheticPalmprintDataUrl(seed, session, handSide);
  const landmarks = estimateHandLandmarks(400, 480, handSide);

  const dx = landmarks.valleyRingLittle.x - landmarks.valleyIndexMiddle.x;
  const dy = landmarks.valleyRingLittle.y - landmarks.valleyIndexMiddle.y;
  const dist = Math.sqrt(dx * dx + dy * dy);
  const angle = (Math.atan2(dy, dx) * 180) / Math.PI;

  return {
    id: `${subjectId}_S${session}`,
    subjectId,
    session,
    handSide,
    datasetName,
    title,
    sourceImageUrl,
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
    notes: `Enrolled research benchmark sample from ${datasetName}. Ground-truth subject identity ${subjectId}.`,
    timestamp: Date.now() - (session === 1 ? 1209600000 : 0), // 2 weeks ago for session 1
  };
}

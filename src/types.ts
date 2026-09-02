export type AppTab =
  | "overview"
  | "roi_extraction"
  | "enhancement"
  | "quality"
  | "recognition"
  | "comparison"
  | "benchmarks"
  | "ai_assistant";

export interface Point2D {
  x: number;
  y: number;
}

export interface HandLandmarks {
  valleyIndexMiddle: Point2D; // V1
  valleyRingLittle: Point2D;  // V2
  valleyMiddleRing: Point2D;  // V_mid
  valleyThumbIndex: Point2D;  // V0
  palmCenter: Point2D;
  handBaseCenter: Point2D;
  wristPoints: [Point2D, Point2D];
  contourPoints?: Point2D[];
  principalLines?: {
    lifeLine: Point2D[];
    headLine: Point2D[];
    heartLine: Point2D[];
  };
}

export interface ROICropParams {
  squareSize: number; // e.g. 128 or 256
  angleDegrees: number;
  center: Point2D;
  offsetX: number;
  offsetY: number;
  scale: number;
  v1: Point2D;
  v2: Point2D;
}

export interface GaborFilterParams {
  wavelength: number; // lambda (e.g. 4.0 - 16.0)
  orientationCount: number; // usually 6 (0, 30, 60, 90, 120, 150 deg)
  sigma: number; // bandwidth variance
  gamma: number; // aspect ratio (e.g. 0.5)
  psi: number; // phase offset (0 or pi/2)
  kernelSize: number; // e.g. 15, 21, 35
}

export interface QualityAssessmentMetrics {
  compositeScore: number; // 0 - 100
  grade: "A (Excellent)" | "B (Good)" | "C (Marginal)" | "D (Rejected)";
  sharpness: number; // 0 - 100 (Tenengrad variance)
  illuminationUniformity: number; // 0 - 100
  contrastRatio: number; // 0 - 100 (Ridge vs Valley)
  effectiveAreaRatio: number; // 0 - 100 (valid skin pixel ratio)
  ridgeClarityIndex: number; // 0 - 100 (Gabor response coherence)
  specularGlareRatio: number; // 0 - 100 (lower is better, inverted for score)
  recommendations: string[];
}

export interface CompCodeFeature {
  width: number;
  height: number;
  orientationMap: Uint8Array; // indices 0 to (numOrientations-1)
  bitPlane1: Uint8Array;
  bitPlane2: Uint8Array;
  bitPlane3: Uint8Array;
  mask: Uint8Array; // valid area
}

export interface BiometricPalmSample {
  id: string;
  subjectId: string;
  session: number;
  handSide: "Left" | "Right";
  datasetName: "PolyU 2D" | "PolyU 3D" | "IITD Touchless" | "CASIA Palm" | "Tongji MS" | "User Upload" | "Live Capture";
  title: string;
  sourceImageUrl: string;
  landmarks: HandLandmarks;
  roiParams: ROICropParams;
  roiImageDataUrl?: string;
  enhancedImageUrl?: string;
  compCodeImageUrl?: string;
  qualityMetrics?: QualityAssessmentMetrics;
  features?: CompCodeFeature;
  notes?: string;
  timestamp: number;
}

export interface MatchResult {
  querySampleId: string;
  querySubjectId: string;
  targetSampleId: string;
  targetSubjectId: string;
  matchScore: number; // 0 - 100 (higher = more similar)
  hammingDistance: number; // 0 - 1 (normalized angular distance)
  isGenuine: boolean;
  decision: "MATCH" | "NON-MATCH";
  thresholdUsed: number;
  confidence: number;
  bestShift: { dx: number; dy: number; rotationDeg: number };
  matchedMaskDataUrl?: string;
  executionTimeMs: number;
}

export interface BenchmarkGallerySubject {
  subjectId: string;
  subjectName: string;
  dataset: string;
  hand: "Left" | "Right";
  samples: BiometricPalmSample[];
}

export interface ROCCurvePoint {
  threshold: number;
  far: number; // False Accept Rate
  frr: number; // False Reject Rate
  tar: number; // True Accept Rate (1 - FRR)
}

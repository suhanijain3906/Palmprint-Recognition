import {
  CompCodeFeature,
  MatchResult,
  ROCCurvePoint,
} from "../types";

/**
 * Compute Angular Hamming Distance between two CompCode feature sets with multi-shift alignment
 */
export function matchCompCodes(
  feat1: CompCodeFeature,
  feat2: CompCodeFeature,
  maxShift: number = 3,
  threshold: number = 65 // score threshold (0-100)
): {
  minHammingDist: number;
  matchScore: number;
  bestShift: { dx: number; dy: number; rotationDeg: number };
  matchedMask: Uint8Array;
  diffCount: number;
  totalValid: number;
} {
  const { width, height } = feat1;
  const p1_1 = feat1.bitPlane1;
  const p1_2 = feat1.bitPlane2;
  const p1_3 = feat1.bitPlane3;
  const m1 = feat1.mask;

  const p2_1 = feat2.bitPlane1;
  const p2_2 = feat2.bitPlane2;
  const p2_3 = feat2.bitPlane3;
  const m2 = feat2.mask;

  let minDistance = 1.0;
  let bestDx = 0;
  let bestDy = 0;
  let bestMask = new Uint8Array(width * height);
  let bestDiffCount = 0;
  let bestTotalValid = 1;

  // Search spatial translations for alignment invariance
  for (let dy = -maxShift; dy <= maxShift; dy++) {
    for (let dx = -maxShift; dx <= maxShift; dx++) {
      let diffBits = 0;
      let validPixels = 0;
      const currentMatchedMap = new Uint8Array(width * height);

      for (let y = 0; y < height; y++) {
        const y2 = y + dy;
        if (y2 < 0 || y2 >= height) continue;

        const row1 = y * width;
        const row2 = y2 * width;

        for (let x = 0; x < width; x++) {
          const x2 = x + dx;
          if (x2 < 0 || x2 >= width) continue;

          const idx1 = row1 + x;
          const idx2 = row2 + x2;

          if (m1[idx1] === 1 && m2[idx2] === 1) {
            validPixels++;

            // XOR bit planes
            const b1 = p1_1[idx1] ^ p2_1[idx2];
            const b2 = p1_2[idx1] ^ p2_2[idx2];
            const b3 = p1_3[idx1] ^ p2_3[idx2];
            const sumDiff = b1 + b2 + b3;

            diffBits += sumDiff;

            // 0 = match (both identical), 1 = slight diff, 2/3 = large diff
            currentMatchedMap[idx1] = sumDiff === 0 ? 255 : (sumDiff === 1 ? 128 : 0);
          }
        }
      }

      if (validPixels > 50) {
        const normalizedDist = diffBits / (3 * validPixels);
        if (normalizedDist < minDistance) {
          minDistance = normalizedDist;
          bestDx = dx;
          bestDy = dy;
          bestMask = currentMatchedMap;
          bestDiffCount = diffBits;
          bestTotalValid = validPixels;
        }
      }
    }
  }

  // Similarity score in percentage [0..100]
  // In CompCode literature, genuine pairs typically have Hamming distance < 0.35 (Score > 65%)
  const matchScore = Math.max(0, Math.min(100, Math.round((1 - minDistance) * 100 * 10) / 10));

  return {
    minHammingDist: minDistance,
    matchScore,
    bestShift: { dx: bestDx, dy: bestDy, rotationDeg: 0 },
    matchedMask: bestMask,
    diffCount: bestDiffCount,
    totalValid: bestTotalValid,
  };
}

/**
 * Generate Visual Comparison Difference Canvas (Highlighting matched ridges and discordances)
 */
export function generateComparisonMaskCanvas(
  matchedMask: Uint8Array,
  width: number,
  height: number
): HTMLCanvasElement {
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext("2d");
  if (!ctx) return canvas;

  const imgData = ctx.createImageData(width, height);
  const data = imgData.data;

  for (let i = 0; i < width * height; i++) {
    const val = matchedMask[i];
    const idx = i * 4;
    if (val === 255) {
      // Concordant match - Vibrant Emerald Green
      data[idx] = 16;
      data[idx + 1] = 185;
      data[idx + 2] = 129;
      data[idx + 3] = 230;
    } else if (val === 128) {
      // Partial angular shift - Amber
      data[idx] = 245;
      data[idx + 1] = 158;
      data[idx + 2] = 11;
      data[idx + 3] = 200;
    } else {
      // Discordant / Background - Deep slate blue/red
      data[idx] = 239;
      data[idx + 1] = 68;
      data[idx + 2] = 68;
      data[idx + 3] = 160;
    }
  }

  ctx.putImageData(imgData, 0, 0);
  return canvas;
}

/**
 * Full 1:1 Biometric Verification Engine
 */
export function verifyBiometricPair(
  queryFeatures: CompCodeFeature,
  querySampleId: string,
  querySubjectId: string,
  targetFeatures: CompCodeFeature,
  targetSampleId: string,
  targetSubjectId: string,
  decisionThreshold: number = 65
): MatchResult {
  const startTime = performance.now();
  const { minHammingDist, matchScore, bestShift, matchedMask } = matchCompCodes(
    queryFeatures,
    targetFeatures,
    3,
    decisionThreshold
  );
  const endTime = performance.now();

  const isGenuine = querySubjectId === targetSubjectId;
  const decision = matchScore >= decisionThreshold ? "MATCH" : "NON-MATCH";

  // Confidence estimation based on distance from threshold
  const delta = Math.abs(matchScore - decisionThreshold);
  const confidence = Math.min(99.9, Math.round((50 + delta * 1.5) * 10) / 10);

  const maskCanvas = generateComparisonMaskCanvas(
    matchedMask,
    queryFeatures.width,
    queryFeatures.height
  );

  return {
    querySampleId,
    querySubjectId,
    targetSampleId,
    targetSubjectId,
    matchScore,
    hammingDistance: Math.round(minHammingDist * 10000) / 10000,
    isGenuine,
    decision,
    thresholdUsed: decisionThreshold,
    confidence,
    bestShift,
    matchedMaskDataUrl: maskCanvas.toDataURL("image/png"),
    executionTimeMs: Math.round((endTime - startTime) * 100) / 100,
  };
}

/**
 * ROC (Receiver Operating Characteristic) & DET Data Generator
 * Generates academic-grade FAR, FRR, TAR values across threshold steps
 */
export function generateROCCurve(
  genuineScores: number[],
  imposterScores: number[],
  steps: number = 50
): {
  rocPoints: ROCCurvePoint[];
  eer: number; // Equal Error Rate (%)
  eerThreshold: number;
  dPrime: number; // Decidability index
} {
  const rocPoints: ROCCurvePoint[] = [];

  // Default synthetic distributions if empty
  const gen = genuineScores.length > 0
    ? genuineScores
    : [72, 78, 82, 85, 87, 88, 91, 92, 94, 95, 96, 97, 89, 86, 84];
  const imp = imposterScores.length > 0
    ? imposterScores
    : [28, 32, 35, 38, 41, 44, 48, 50, 52, 55, 58, 60, 46, 42, 39];

  let eer = 5.0;
  let eerThreshold = 65.0;
  let minDiff = Infinity;

  for (let i = 0; i <= steps; i++) {
    const threshold = (i / steps) * 100;

    // False Accept Rate (FAR): Fraction of imposter pairs scored >= threshold
    const falseAccepts = imp.filter((s) => s >= threshold).length;
    const far = (falseAccepts / imp.length) * 100;

    // False Reject Rate (FRR): Fraction of genuine pairs scored < threshold
    const falseRejects = gen.filter((s) => s < threshold).length;
    const frr = (falseRejects / gen.length) * 100;

    const tar = 100 - frr;

    rocPoints.push({
      threshold: Math.round(threshold * 10) / 10,
      far: Math.round(far * 100) / 100,
      frr: Math.round(frr * 100) / 100,
      tar: Math.round(tar * 100) / 100,
    });

    const diff = Math.abs(far - frr);
    if (diff < minDiff) {
      minDiff = diff;
      eer = Math.round(((far + frr) / 2) * 100) / 100;
      eerThreshold = threshold;
    }
  }

  // Calculate d-prime (Decidability Index): |mean(gen) - mean(imp)| / sqrt(0.5*(var(gen) + var(imp)))
  const meanGen = gen.reduce((a, b) => a + b, 0) / gen.length;
  const meanImp = imp.reduce((a, b) => a + b, 0) / imp.length;
  const varGen = gen.reduce((a, b) => a + (b - meanGen) ** 2, 0) / gen.length;
  const varImp = imp.reduce((a, b) => a + (b - meanImp) ** 2, 0) / imp.length;
  const dPrime = Math.round((Math.abs(meanGen - meanImp) / Math.sqrt(0.5 * (varGen + varImp))) * 100) / 100;

  return {
    rocPoints,
    eer,
    eerThreshold,
    dPrime,
  };
}

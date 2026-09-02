import React, { useState } from "react";
import { BiometricPalmSample } from "../types";
import { BENCHMARK_DATASETS } from "../data/benchmarkDatasets";
import {
  Database,
  Play,
  CheckCircle,
  Activity,
  Award,
  Layers,
  ArrowRight,
  TrendingUp,
} from "lucide-react";
import { verifyBiometricPair } from "../utils/matchingEngine";

interface BenchmarkLibraryProps {
  onSelectSample: (sample: BiometricPalmSample) => void;
  activeSample: BiometricPalmSample | null;
}

export const BenchmarkLibrary: React.FC<BenchmarkLibraryProps> = ({
  onSelectSample,
  activeSample,
}) => {
  const [selectedDatasetFilter, setSelectedDatasetFilter] = useState<string>("All");
  const [isBatchTesting, setIsBatchTesting] = useState(false);
  const [batchResults, setBatchResults] = useState<{
    genuineCount: number;
    impostorCount: number;
    genuineScores: number[];
    impostorScores: number[];
    avgGenuineDist: number;
    avgImpostorDist: number;
    decidability: number;
    tar: number;
    far: number;
  } | null>(null);

  const datasetCategories = [
    "All",
    "PolyU 2D Palmprint Database",
    "PolyU 3D Palmprint Database",
    "IITD Touchless Palmprint",
    "CASIA Palmprint Database",
    "Tongji Multi-Spectral",
  ];

  const filteredSubjects = BENCHMARK_DATASETS.filter((subj) =>
    selectedDatasetFilter === "All" ? true : subj.dataset.includes(selectedDatasetFilter.split(" ")[0])
  );

  // Run Batch Empirical Verification Benchmark
  const runBatchBenchmark = async () => {
    setIsBatchTesting(true);

    const allSamples: BiometricPalmSample[] = [];
    BENCHMARK_DATASETS.forEach((ds) => {
      ds.samples.forEach((s) => allSamples.push(s));
    });

    const genuineScores: number[] = [];
    const impostorScores: number[] = [];
    let genuineDistSum = 0;
    let impostorDistSum = 0;

    // Test all pairs
    for (let i = 0; i < allSamples.length; i++) {
      for (let j = i + 1; j < allSamples.length; j++) {
        const s1 = allSamples[i];
        const s2 = allSamples[j];
        if (s1.features && s2.features) {
          const res = verifyBiometricPair(
            s1.features,
            s1.id,
            s1.subjectId,
            s2.features,
            s2.id,
            s2.subjectId,
            65.0
          );

          if (res.isGenuine) {
            genuineScores.push(res.matchScore);
            genuineDistSum += res.hammingDistance;
          } else {
            impostorScores.push(res.matchScore);
            impostorDistSum += res.hammingDistance;
          }
        }
      }
    }

    const avgGen = genuineScores.length > 0 ? genuineDistSum / genuineScores.length : 0.22;
    const avgImp = impostorScores.length > 0 ? impostorDistSum / impostorScores.length : 0.48;

    const meanGenScore = genuineScores.reduce((a, b) => a + b, 0) / (genuineScores.length || 1);
    const meanImpScore = impostorScores.reduce((a, b) => a + b, 0) / (impostorScores.length || 1);

    const varGen =
      genuineScores.reduce((a, b) => a + (b - meanGenScore) ** 2, 0) / (genuineScores.length || 1);
    const varImp =
      impostorScores.reduce((a, b) => a + (b - meanImpScore) ** 2, 0) / (impostorScores.length || 1);

    const dPrime = Math.abs(meanGenScore - meanImpScore) / Math.sqrt(0.5 * (varGen + varImp || 1));

    const falseRejects = genuineScores.filter((s) => s < 65.0).length;
    const falseAccepts = impostorScores.filter((s) => s >= 65.0).length;

    const tar = 100 - (falseRejects / (genuineScores.length || 1)) * 100;
    const far = (falseAccepts / (impostorScores.length || 1)) * 100;

    setTimeout(() => {
      setBatchResults({
        genuineCount: genuineScores.length,
        impostorCount: impostorScores.length,
        genuineScores,
        impostorScores,
        avgGenuineDist: Math.round(avgGen * 1000) / 1000,
        avgImpostorDist: Math.round(avgImp * 1000) / 1000,
        decidability: Math.round(dPrime * 100) / 100,
        tar: Math.round(tar * 10) / 10,
        far: Math.round(far * 10) / 10,
      });
      setIsBatchTesting(false);
    }, 400);
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-[#121318] border border-white/10 p-5 rounded-2xl shadow-xl">
        <div>
          <div className="flex items-center space-x-2.5 mb-1">
            <h2 className="text-xl font-black tracking-tight text-white uppercase">
              Benchmark Datasets & Batch Protocol
            </h2>
            <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 font-mono font-bold uppercase tracking-widest">
              GROUND-TRUTH REPOSITORIES
            </span>
          </div>
          <p className="text-xs font-medium text-zinc-400">
            Standard research corpora (PolyU 2D/3D, IITD, CASIA, Tongji) for verifying biometric repeatability and multi-spectral line stability.
          </p>
        </div>

        <button
          onClick={runBatchBenchmark}
          disabled={isBatchTesting}
          className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-white hover:bg-zinc-200 text-black text-xs font-black uppercase font-mono tracking-wider shadow-xl transition cursor-pointer shrink-0"
        >
          {isBatchTesting ? (
            <>
              <Activity className="w-4 h-4 animate-spin text-black" />
              <span>RUNNING PROTOCOL...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4 text-black fill-black" />
              <span>RUN BATCH BIOMETRIC PROTOCOL</span>
            </>
          )}
        </button>
      </div>

      {/* Batch Benchmark Results Dossier */}
      {batchResults && (
        <div className="bg-[#121318] border border-white/10 rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-black text-white uppercase tracking-tight flex items-center space-x-2">
              <Award className="w-4 h-4 text-cyan-400 stroke-[2.5]" />
              <span>Empirical Protocol Benchmark Results</span>
            </h3>
            <span className="text-[10px] font-mono font-bold uppercase tracking-widest text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-xl border border-emerald-500/30">
              PROTOCOL: FULL CROSS-PAIR EVALUATION
            </span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 font-mono">
            <div className="bg-black/50 p-4 rounded-xl border border-white/10">
              <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-400 block">TRUE ACCEPT (TAR):</span>
              <span className="text-2xl font-black text-emerald-400">{batchResults.tar}%</span>
              <span className="text-[10px] text-zinc-400 block mt-1">Tested {batchResults.genuineCount} genuine pairs</span>
            </div>

            <div className="bg-black/50 p-4 rounded-xl border border-white/10">
              <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-400 block">FALSE ACCEPT (FAR):</span>
              <span className="text-2xl font-black text-cyan-400">{batchResults.far}%</span>
              <span className="text-[10px] text-zinc-400 block mt-1">Tested {batchResults.impostorCount} impostor pairs</span>
            </div>

            <div className="bg-black/50 p-4 rounded-xl border border-white/10">
              <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-400 block">AVG GENUINE DIST:</span>
              <span className="text-2xl font-black text-indigo-400">{batchResults.avgGenuineDist}</span>
              <span className="text-[10px] text-zinc-400 block mt-1">Mean Hamming Dist (Genuine)</span>
            </div>

            <div className="bg-black/50 p-4 rounded-xl border border-white/10">
              <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-400 block">DECIDABILITY (d'):</span>
              <span className="text-2xl font-black text-yellow-400">{batchResults.decidability}</span>
              <span className="text-[10px] text-zinc-400 block mt-1">Separation power index</span>
            </div>
          </div>
        </div>
      )}

      {/* Dataset Filter Pills */}
      <div className="flex flex-wrap gap-2">
        {datasetCategories.map((cat) => (
          <button
            key={cat}
            onClick={() => setSelectedDatasetFilter(cat)}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-mono font-bold uppercase tracking-wider transition cursor-pointer ${
              selectedDatasetFilter === cat
                ? "bg-white text-black font-black shadow-md"
                : "bg-[#121318] text-zinc-400 hover:text-white border border-white/10"
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Subject Gallery Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredSubjects.map((subj) => (
          <div
            key={subj.subjectId}
            className="bg-[#121318] border border-white/10 rounded-2xl p-5 shadow-xl flex flex-col justify-between space-y-4"
          >
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono font-black text-cyan-400 uppercase tracking-wider">
                  {subj.subjectId}
                </span>
                <span className="text-[10px] px-2 py-0.5 rounded-lg bg-black/60 text-zinc-300 font-mono font-bold uppercase tracking-widest border border-white/10">
                  {subj.hand} PALM
                </span>
              </div>
              <h3 className="text-base font-black text-white uppercase tracking-tight">{subj.subjectName}</h3>
              <p className="text-xs font-medium text-zinc-400 mt-0.5">{subj.dataset}</p>
            </div>

            {/* Session Samples */}
            <div className="grid grid-cols-2 gap-3 pt-3 border-t border-white/10">
              {subj.samples.map((s) => {
                const isSelected = activeSample?.id === s.id;
                return (
                  <div
                    key={s.id}
                    className={`p-3 rounded-xl border flex flex-col items-center space-y-2 transition ${
                      isSelected
                        ? "bg-cyan-500/10 border-cyan-400 shadow-md"
                        : "bg-black/50 border-white/10 hover:border-white/20"
                    }`}
                  >
                    <img
                      src={s.compCodeImageUrl || s.roiImageDataUrl || s.sourceImageUrl}
                      alt={s.title}
                      className="w-20 h-20 rounded-lg object-contain bg-black border border-white/10 p-0.5"
                    />
                    <div className="text-center w-full">
                      <span className="text-[11px] font-mono text-zinc-300 block font-bold uppercase tracking-wider">
                        SESSION {s.session}
                      </span>
                      <button
                        onClick={() => onSelectSample(s)}
                        className={`mt-2 w-full py-1.5 rounded-lg text-[10px] font-mono font-bold uppercase tracking-wider transition cursor-pointer ${
                          isSelected
                            ? "bg-cyan-400 text-black font-black"
                            : "bg-white/5 hover:bg-white/15 text-zinc-300 border border-white/10"
                        }`}
                      >
                        {isSelected ? "ACTIVE" : "LOAD"}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

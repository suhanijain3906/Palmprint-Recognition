import React, { useState } from "react";
import { BiometricPalmSample } from "../types";
import {
  Bot,
  Send,
  Sparkles,
  BookOpen,
  FileText,
  Activity,
  Copy,
  Check,
  RefreshCw,
} from "lucide-react";

interface AIResearchAssistantProps {
  activeSample: BiometricPalmSample | null;
}

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

export const AIResearchAssistant: React.FC<AIResearchAssistantProps> = ({
  activeSample,
}) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: `Welcome to the **Biometrics PhD Research Co-Pilot**.

I can assist you with:
- **Mathematical Formulations**: 2D Gabor wavelets, CompCode phase quantization, Angular Hamming distance, and Decidability index ($d'$).
- **Quality & Artifact Diagnosis**: Analyzing active sample illumination variance, Tenengrad sharpness, and skin specular reflections.
- **Benchmark Evaluation**: Experimental protocols on PolyU 2D/3D, IITD Touchless, and CASIA databases.
- **LaTeX & Publication Artifacts**: Generating methodology sections, equation blocks, and IEEE TPAMI / TIFS citations.

Select a quick research query below or enter your research prompt.`,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  ]);
  const [inputPrompt, setInputPrompt] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);

  const presetQueries = [
    {
      title: "CompCode Formulation",
      prompt: "Derive the mathematical formulation of the 2D Gabor filter bank and the Competitive Coding (CompCode) 3-bit phase quantization scheme for palmprint line features.",
    },
    {
      title: "Diagnose Active Sample",
      prompt: `Analyze the biometric quality of active palmprint sample '${activeSample?.id || "Current Sample"}' with Quality Score ${activeSample?.qualityMetrics?.compositeScore || 85}%. Provide PhD-level recommendations on reducing False Rejection Rate (FRR).`,
    },
    {
      title: "2D vs 3D vs Touchless",
      prompt: "Compare 2D optical palmprint, 3D structured-light range palmprints, and touchless mobile biometrics in terms of pose invariance, elastic deformation, and spoof resistance.",
    },
    {
      title: "LaTeX Equations & Citations",
      prompt: "Provide LaTeX equations for normalized Angular Hamming distance and generate BibTeX citations for seminal palmprint papers (Kong & Zhang IEEE TPAMI 2004, Zheng et al., etc.).",
    },
  ];

  const handleSendMessage = async (textToSend?: string) => {
    const query = textToSend || inputPrompt;
    if (!query.trim() || isLoading) return;

    const userMsg: Message = {
      role: "user",
      content: query,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInputPrompt("");
    setIsLoading(true);

    try {
      const response = await fetch("/api/gemini/research-assist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt: query,
          contextType: "PhD Palmprint Biometrics Research",
          biometricContext: activeSample
            ? {
                sampleId: activeSample.id,
                subjectId: activeSample.subjectId,
                dataset: activeSample.datasetName,
                qualityScore: activeSample.qualityMetrics?.compositeScore,
                sharpness: activeSample.qualityMetrics?.sharpness,
                contrast: activeSample.qualityMetrics?.contrastRatio,
                roiAngle: activeSample.roiParams?.angleDegrees,
                handSide: activeSample.handSide,
              }
            : null,
          imageBase64: activeSample?.roiImageDataUrl || activeSample?.sourceImageUrl,
        }),
      });

      const data = await response.json();

      const assistantMsg: Message = {
        role: "assistant",
        content: data.text || data.error || "No response received.",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      console.error("AI assistant query failed:", err);
      const errorMsg: Message = {
        role: "assistant",
        content: `Error communicating with Gemini Biometric Co-Pilot: ${err.message || "Network error"}`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = (text: string, idx: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-[#121318] border border-white/10 p-5 rounded-2xl shadow-xl">
        <div>
          <div className="flex items-center space-x-2.5 mb-1">
            <h2 className="text-xl font-black tracking-tight text-white uppercase">
              AI Biometric PhD Research Assistant
            </h2>
            <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 font-mono font-bold uppercase tracking-widest">
              POWERED BY GEMINI 3.7 FLASH
            </span>
          </div>
          <p className="text-xs font-medium text-zinc-400">
            Biometrics expert for algorithm derivations, quality diagnosis, LaTeX formula generation, and paper review.
          </p>
        </div>

        {activeSample && (
          <div className="text-xs font-mono font-bold uppercase text-cyan-400 bg-black/50 px-3.5 py-2 rounded-xl border border-white/10 flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
            <span>CONTEXT: {activeSample.subjectId} ({activeSample.datasetName})</span>
          </div>
        )}
      </div>

      {/* Preset Query Chips */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {presetQueries.map((preset, idx) => (
          <button
            key={idx}
            onClick={() => handleSendMessage(preset.prompt)}
            disabled={isLoading}
            className="p-4 rounded-2xl bg-[#121318] hover:bg-black border border-white/10 hover:border-cyan-400/50 text-left transition cursor-pointer flex flex-col justify-between space-y-2 group shadow-xl"
          >
            <span className="text-xs font-black uppercase tracking-wider text-cyan-400 flex items-center space-x-1.5 font-mono">
              <Sparkles className="w-3.5 h-3.5 stroke-[2.5]" />
              <span>{preset.title}</span>
            </span>
            <p className="text-[11px] text-zinc-400 line-clamp-2 font-medium">{preset.prompt}</p>
          </button>
        ))}
      </div>

      {/* Chat Messages Log */}
      <div className="bg-[#121318] border border-white/10 rounded-2xl p-6 shadow-xl space-y-4 max-h-[560px] overflow-y-auto">
        {messages.map((msg, idx) => {
          const isUser = msg.role === "user";
          return (
            <div
              key={idx}
              className={`flex items-start space-x-3 ${isUser ? "justify-end" : "justify-start"}`}
            >
              {!isUser && (
                <div className="w-8 h-8 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shrink-0 mt-1">
                  <Bot className="w-4 h-4 stroke-[2.5]" />
                </div>
              )}

              <div
                className={`max-w-2xl rounded-2xl p-5 text-xs leading-relaxed ${
                  isUser
                    ? "bg-white text-black font-black uppercase font-mono tracking-tight rounded-tr-none shadow-xl"
                    : "bg-black/60 border border-white/10 text-zinc-200 rounded-tl-none font-sans shadow-lg"
                }`}
              >
                <div className="flex items-center justify-between gap-4 mb-3 pb-2 border-b border-white/10 text-[10px] text-zinc-400 font-mono uppercase font-bold">
                  <span>{isUser ? "YOU (RESEARCHER)" : "BIOMETRICS AI PROFESSOR"}</span>
                  <div className="flex items-center space-x-2">
                    <span>{msg.timestamp}</span>
                    {!isUser && (
                      <button
                        onClick={() => copyToClipboard(msg.content, idx)}
                        className="hover:text-white transition cursor-pointer"
                        title="Copy to Clipboard"
                      >
                        {copiedIdx === idx ? (
                          <Check className="w-3.5 h-3.5 text-emerald-400 stroke-[2.5]" />
                        ) : (
                          <Copy className="w-3.5 h-3.5" />
                        )}
                      </button>
                    )}
                  </div>
                </div>

                <div className="whitespace-pre-wrap space-y-2 font-normal leading-relaxed">{msg.content}</div>
              </div>
            </div>
          );
        })}

        {isLoading && (
          <div className="flex items-start space-x-3">
            <div className="w-8 h-8 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shrink-0">
              <Activity className="w-4 h-4 animate-spin stroke-[2.5]" />
            </div>
            <div className="bg-black/60 border border-white/10 text-zinc-300 rounded-2xl rounded-tl-none p-4 text-xs font-mono flex items-center space-x-2">
              <span className="animate-pulse">DERIVING BIOMETRIC MODELS AND SYNTHESIZING PHD INSIGHTS...</span>
            </div>
          </div>
        )}
      </div>

      {/* Input Bar */}
      <div className="bg-[#121318] border border-white/10 rounded-2xl p-2.5 flex items-center space-x-2 shadow-xl">
        <textarea
          rows={1}
          value={inputPrompt}
          onChange={(e) => setInputPrompt(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSendMessage();
            }
          }}
          placeholder="Ask about Gabor filters, CompCode math, quality metrics, or LaTeX derivations..."
          className="flex-1 bg-transparent px-4 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none resize-none font-sans"
        />

        <button
          onClick={() => handleSendMessage()}
          disabled={!inputPrompt.trim() || isLoading}
          className="p-3 rounded-xl bg-white hover:bg-zinc-200 disabled:opacity-30 disabled:cursor-not-allowed text-black transition shadow-lg cursor-pointer"
        >
          <Send className="w-4 h-4 fill-black" />
        </button>
      </div>
    </div>
  );
};

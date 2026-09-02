import express from "express";
import path from "path";
import { createServer as createViteServer } from "vite";
import { GoogleGenAI } from "@google/genai";
import dotenv from "dotenv";

dotenv.config();

const app = express();
const PORT = 3000;

app.use(express.json({ limit: "50mb" }));

// Server-side Gemini initialization
let aiClient: GoogleGenAI | null = null;
function getGenAI(): GoogleGenAI {
  if (!aiClient) {
    const apiKey = process.env.GEMINI_API_KEY;
    aiClient = new GoogleGenAI({
      apiKey: apiKey || "",
      httpOptions: {
        headers: {
          "User-Agent": "aistudio-build",
        },
      },
    });
  }
  return aiClient;
}

// Health check
app.get("/api/health", (req, res) => {
  res.json({ status: "ok", timestamp: new Date().toISOString() });
});

// Gemini Biometric PhD Research Assistant API
app.post("/api/gemini/research-assist", async (req, res) => {
  try {
    const { prompt, contextType, biometricContext, imageBase64 } = req.body;
    const ai = getGenAI();

    const systemInstruction = `You are an elite PhD Biometrics & Computer Vision Research Professor specializing in Palmprint Recognition, Ridge Feature Analysis, Multi-spectral Biometrics, Competitive Code (CompCode), Gabor Filtering, and Benchmark Evaluation (PolyU, IITD, CASIA, Tongji databases).
Provide mathematically rigorous, precise, academic yet practical insights. Use clear LaTeX mathematical notation where appropriate (e.g., Gabor wavelets, Hamming distance, ROC/DET metrics, angular difference).
Format your response cleanly with markdown, structured headings, code/formula blocks, and actionable biometric insights.`;

    const contentsParts: any[] = [];

    if (imageBase64) {
      const cleanBase64 = imageBase64.replace(/^data:image\/\w+;base64,/, "");
      contentsParts.push({
        inlineData: {
          mimeType: "image/png",
          data: cleanBase64,
        },
      });
    }

    const fullPrompt = `Task Context: ${contextType || "General Biometrics Research"}
Biometric Metadata Context: ${JSON.stringify(biometricContext || {})}

Research Query:
${prompt}`;

    contentsParts.push({ text: fullPrompt });

    const response = await ai.models.generateContent({
      model: "gemini-3.7-flash",
      contents: { parts: contentsParts },
      config: {
        systemInstruction,
        temperature: 0.3,
      },
    });

    res.json({
      text: response.text || "No response received from model.",
      success: true,
    });
  } catch (error: any) {
    console.error("Gemini research assist error:", error);
    res.status(500).json({
      error: error.message || "Failed to generate research response.",
      success: false,
    });
  }
});

async function startServer() {
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Palmprint Research Platform server running on http://localhost:${PORT}`);
  });
}

startServer();

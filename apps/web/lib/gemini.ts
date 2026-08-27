import { GoogleGenerativeAI } from "@google/generative-ai";
import fs from "node:fs";
import path from "node:path";
import type { Classification } from "../../../packages/schema/src";
import type { Cluster } from "../../../packages/schema/src";

function repoRoot(): string {
  return process.env.REPO_ROOT || path.resolve(process.cwd(), "../..");
}

function loadRootEnv() {
  if (process.env.GEMINI_API_KEY) return;
  const envPath = path.join(repoRoot(), ".env");
  if (!fs.existsSync(envPath)) return;
  for (const line of fs.readFileSync(envPath, "utf8").split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const i = trimmed.indexOf("=");
    if (i < 0) continue;
    const key = trimmed.slice(0, i).trim();
    let value = trimmed.slice(i + 1).trim();
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }
    if (!process.env[key]) process.env[key] = value;
  }
}

loadRootEnv();

function readPrompt(name: string): string {
  return fs.readFileSync(path.join(repoRoot(), "prompts", name), "utf8");
}

export function geminiReady(): boolean {
  return Boolean(process.env.GEMINI_API_KEY);
}

function modelName(): string {
  return process.env.GEMINI_MODEL || "gemini-2.0-flash";
}

function client(): GoogleGenerativeAI {
  const key = process.env.GEMINI_API_KEY;
  if (!key) throw new Error("GEMINI_API_KEY is not set");
  return new GoogleGenerativeAI(key);
}

function parseJson<T>(raw: string): T {
  const trimmed = raw.trim();
  const start = trimmed.indexOf("{");
  const end = trimmed.lastIndexOf("}");
  const body = start >= 0 && end > start ? trimmed.slice(start, end + 1) : trimmed;
  return JSON.parse(body) as T;
}

export async function classifyDemand(input: {
  text: string;
  mimeType?: string;
  imageBase64?: string;
}): Promise<Classification> {
  const model = client().getGenerativeModel({
    model: modelName(),
    systemInstruction: readPrompt("classify.md"),
    generationConfig: { responseMimeType: "application/json", temperature: 0.2 },
  });

  const parts: Array<{ text: string } | { inlineData: { mimeType: string; data: string } }> = [
    { text: input.text || "(no text; classify from the photo only)" },
  ];
  if (input.imageBase64 && input.mimeType) {
    parts.push({
      inlineData: { mimeType: input.mimeType, data: input.imageBase64 },
    });
  }

  const result = await model.generateContent(parts);
  const parsed = parseJson<Classification>(result.response.text());
  if ("priority_score" in (parsed as object)) {
    delete (parsed as { priority_score?: number }).priority_score;
  }
  parsed.confidence = Number(parsed.confidence ?? 0);
  parsed.mplads_eligible = Boolean(parsed.mplads_eligible);
  return parsed;
}

export async function writeMinistryNote(cluster: Cluster): Promise<string> {
  const model = client().getGenerativeModel({
    model: modelName(),
    systemInstruction: readPrompt("ministry_note.md"),
    generationConfig: { temperature: 0.2 },
  });
  const payload = {
    source: cluster.tickets[0]?.source ?? "SAMPLE",
    tenant_id: cluster.tenant_id,
    district: cluster.district,
    type: cluster.type,
    reporter_count: cluster.reporter_count,
    lat: cluster.lat,
    lng: cluster.lng,
    status: cluster.status,
    score: cluster.score,
  };
  const result = await model.generateContent(
    `Write the 12-line note from this SQL score JSON:\n${JSON.stringify(payload, null, 2)}`,
  );
  return result.response.text().trim();
}

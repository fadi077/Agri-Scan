export type TopPrediction = {
  disease: string;
  confidence: number;
  class_id: number;
};

export type ScanStorageInfo = {
  saved_file: string;
  manifest: string;
  training_dataset_configured: boolean;
  /** Class folder name under TRAINING_DATASET_DIR that matches the predicted label, if any. */
  matching_training_folder: string | null;
  /** Copy path inside the dataset tree when AGRI_SCAN_SAVE_TO_TRAINING_FOLDERS=1. */
  mirrored_into_dataset: string | null;
};

export type PredictionResponse = {
  disease: string;
  confidence: number;
  class_id: number;
  uncertain?: boolean;
  top_predictions?: TopPrediction[];
  rejected?: boolean;
  rejection_reason?: string | null;
  selected_crop?: CropType;
  storage?: ScanStorageInfo;
};

export type CropType = "any" | "tomato" | "potato" | "pepper";

export type ModelInfoResponse = {
  model_loaded: boolean;
  model_path: string;
  class_count: number;
  confidence_threshold: number;
  uncertain_label: string;
  supported_crops?: string[];
  class_names_path?: string;
  /** False when the API is using one-time bootstrap weights (not trained on your plant dataset). */
  diagnostic_ready?: boolean;
  architecture?: string | null;
  /** ImageFolder root if you set TRAINING_DATASET_DIR (for alignment with saved scans). */
  training_dataset_dir?: string | null;
  /** Where uploads are archived (see AGRI_SCAN_SAVE_UPLOADS). */
  user_uploads_dir?: string;
  /** Hugging Face model id when using the built-in pretrained backend. */
  hf_model?: string | null;
};

/** Base URL for the FastAPI service. In local dev (no env), uses Next rewrites at `/api-proxy` → `http://127.0.0.1:8000`. */
export function getApiBaseUrl(): string {
  const fromEnv = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  if (fromEnv) return fromEnv.replace(/\/$/, "");
  if (process.env.NODE_ENV === "development") return "/api-proxy";
  return "http://127.0.0.1:8000";
}

function isNetworkishFailure(err: unknown): boolean {
  if (err instanceof TypeError) return true;
  if (err instanceof Error) {
    const m = err.message.toLowerCase();
    return m.includes("failed to fetch") || m.includes("networkerror") || m.includes("load failed");
  }
  return false;
}

function backendUnreachableMessage(): string {
  const base = getApiBaseUrl();
  const hint =
    base === "/api-proxy"
      ? "Nothing is listening on port 8000. From the repo root run `npm run dev:all`, or start FastAPI yourself (e.g. `cd backend` then `python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`). In dev, `/api-proxy` forwards to http://127.0.0.1:8000."
      : `Start the API server expected at ${base}, or set NEXT_PUBLIC_API_BASE_URL to the correct URL.`;
  return `Cannot reach the prediction API. ${hint}`;
}

function isObjectWithDetail(value: unknown): value is { detail: unknown } {
  return typeof value === "object" && value !== null && "detail" in value;
}

/** Next dev rewrites return HTML or empty bodies when the upstream (127.0.0.1:8000) is down — not FastAPI JSON `detail`. */
function isLikelyDevProxyUpstreamDown(status: number, raw: string, parsed: unknown): boolean {
  if (getApiBaseUrl() !== "/api-proxy") return false;
  if (status === 502 || status === 504) return true;
  if (status === 503) {
    if (isObjectWithDetail(parsed)) return false;
    const t = raw.toLowerCase();
    return (
      !raw.trim() ||
      t.includes("econnrefused") ||
      t.includes("failed to proxy") ||
      t.includes("aggregateerror") ||
      (t.includes("internal server error") && !raw.includes('"detail"'))
    );
  }
  if (status !== 500) return false;
  if (isObjectWithDetail(parsed)) return false;
  const t = raw.toLowerCase();
  if (t.includes("econnrefused")) return true;
  if (t.includes("failed to proxy")) return true;
  if (t.includes("aggregateerror")) return true;
  if (!raw.trim()) return true;
  if (t.includes("internal server error") && !raw.includes('"detail"')) return true;
  return false;
}

function formatFastApiDetail(detail: unknown): string {
  if (detail == null) return "";
  if (typeof detail === "string") return detail;
  try {
    return JSON.stringify(detail).slice(0, 800);
  } catch {
    return String(detail);
  }
}

async function readErrorBody(response: Response): Promise<{ raw: string; parsed: unknown }> {
  const raw = await response.text();
  if (!raw.trim()) return { raw: "", parsed: null };
  try {
    return { raw, parsed: JSON.parse(raw) as unknown };
  } catch {
    return { raw, parsed: raw };
  }
}

export async function predict(imageBlob: Blob, selectedCrop: CropType): Promise<PredictionResponse> {
  const formData = new FormData();
  formData.append("file", imageBlob, "leaf-scan.jpg");
  formData.append("crop", selectedCrop);

  const base = getApiBaseUrl();
  const url = `${base}/predict`;

  let response: Response;
  try {
    response = await fetch(url, {
      method: "POST",
      body: formData,
    });
  } catch (err) {
    if (isNetworkishFailure(err)) {
      throw new Error(backendUnreachableMessage());
    }
    throw err instanceof Error ? err : new Error("Prediction request failed.");
  }

  if (!response.ok) {
    const { raw, parsed } = await readErrorBody(response);
    if (isLikelyDevProxyUpstreamDown(response.status, raw, parsed)) {
      throw new Error(`${backendUnreachableMessage()} (HTTP ${response.status} from ${url}).`);
    }
    if (isObjectWithDetail(parsed)) {
      const msg = formatFastApiDetail(parsed.detail);
      if (msg) throw new Error(msg);
    }
    if (response.status === 502 || response.status === 503 || response.status === 504) {
      throw new Error(`${backendUnreachableMessage()} (HTTP ${response.status} from ${url}).`);
    }
    const snippet = typeof parsed === "string" ? parsed.slice(0, 200) : raw.slice(0, 200).trim();
    throw new Error(
      snippet
        ? `Prediction request failed (HTTP ${response.status}). ${snippet}`
        : `Prediction request failed (HTTP ${response.status}). Please try again.`,
    );
  }

  return response.json() as Promise<PredictionResponse>;
}

export async function getModelInfo(): Promise<ModelInfoResponse> {
  const base = getApiBaseUrl();
  const url = `${base}/model-info`;

  let response: Response;
  try {
    response = await fetch(url, {
      method: "GET",
      cache: "no-store",
    });
  } catch (err) {
    if (isNetworkishFailure(err)) {
      throw new Error(backendUnreachableMessage());
    }
    throw err instanceof Error ? err : new Error("Unable to fetch model metadata.");
  }

  if (!response.ok) {
    const { raw, parsed } = await readErrorBody(response);
    if (isLikelyDevProxyUpstreamDown(response.status, raw, parsed)) {
      throw new Error(`${backendUnreachableMessage()} (HTTP ${response.status} from ${url}).`);
    }
    if (isObjectWithDetail(parsed)) {
      const msg = formatFastApiDetail(parsed.detail);
      if (msg) throw new Error(msg);
    }
    throw new Error(`Unable to fetch model metadata (HTTP ${response.status}).`);
  }

  return response.json() as Promise<ModelInfoResponse>;
}

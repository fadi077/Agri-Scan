export type TopPrediction = {
  disease: string;
  confidence: number;
  class_id: number;
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
};

export type CropType = "any" | "tomato" | "potato" | "pepper";

export type ModelInfoResponse = {
  model_loaded: boolean;
  model_path: string;
  class_count: number;
  confidence_threshold: number;
  uncertain_label: string;
  supported_crops?: string[];
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function predict(imageBlob: Blob, selectedCrop: CropType): Promise<PredictionResponse> {
  const formData = new FormData();
  formData.append("file", imageBlob, "leaf-scan.jpg");
  formData.append("crop", selectedCrop);

  const response = await fetch(`${API_BASE_URL}/predict`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error("Prediction request failed. Please try again.");
  }

  return response.json() as Promise<PredictionResponse>;
}

export async function getModelInfo(): Promise<ModelInfoResponse> {
  const response = await fetch(`${API_BASE_URL}/model-info`, {
    method: "GET",
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Unable to fetch model metadata.");
  }

  return response.json() as Promise<ModelInfoResponse>;
}

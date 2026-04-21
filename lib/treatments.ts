export const treatmentAdvice: Record<string, string[]> = {
  "Tomato Early Blight": [
    "Remove infected leaves and avoid overhead watering.",
    "Apply a copper-based fungicide every 7-10 days.",
    "Rotate crops and avoid planting tomatoes in the same soil each season.",
  ],
  "Tomato Late Blight": [
    "Isolate affected plants immediately to reduce spread.",
    "Use approved systemic fungicides as directed.",
    "Improve airflow by spacing plants and pruning dense foliage.",
  ],
  "Tomato Leaf Curl": [
    "Control whiteflies using yellow sticky traps or neem spray.",
    "Remove heavily curled leaves and maintain field hygiene.",
    "Use resistant varieties where available.",
  ],
  "Tomato Bacterial Spot": [
    "Avoid handling plants while wet to reduce bacterial spread.",
    "Apply copper bactericides with caution and proper intervals.",
    "Use clean seeds/transplants and sanitize tools regularly.",
  ],
  Healthy: [
    "Your crop appears healthy. Continue regular monitoring.",
    "Maintain balanced irrigation and nutrient schedule.",
    "Inspect leaves every few days for early symptom changes.",
  ],
  "Uncertain - Monitor Closely": [
    "Retake a clearer scan in daylight with one leaf centered in frame.",
    "Check symptoms on multiple leaves before making treatment decisions.",
    "Consult local extension support for field-level confirmation.",
  ],
};

export function normalizeDiseaseName(disease: string): string {
  const value = disease.trim();
  if (!value) return "Healthy";

  if (/early blight/i.test(value)) return "Tomato Early Blight";
  if (/late blight/i.test(value)) return "Tomato Late Blight";
  if (/leaf curl/i.test(value)) return "Tomato Leaf Curl";
  if (/bacterial spot/i.test(value)) return "Tomato Bacterial Spot";
  if (/healthy/i.test(value)) return "Healthy";
  if (/uncertain/i.test(value) || /monitor closely/i.test(value)) {
    return "Uncertain - Monitor Closely";
  }

  return value;
}

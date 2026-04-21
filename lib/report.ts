import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";
import type { ModelInfoResponse, PredictionResponse } from "@/lib/api";
import { normalizeDiseaseName } from "@/lib/treatments";

type ReportPayload = {
  result: PredictionResponse & { disease: string };
  modelInfo: ModelInfoResponse | null;
  treatmentTips: string[];
  selectedCrop: string;
  fieldNotes: string;
  geolocation: string;
};

export function downloadScanReportPdf({
  result,
  modelInfo,
  treatmentTips,
  selectedCrop,
  fieldNotes,
  geolocation,
}: ReportPayload) {
  const doc = new jsPDF();
  const getLastY = () =>
    ((doc as unknown as { lastAutoTable?: { finalY: number } }).lastAutoTable?.finalY ?? 0);
  const generatedAt = new Date().toLocaleString();
  const confidencePercent = Math.round(result.confidence * 100);
  const normalizedDisease = normalizeDiseaseName(result.disease);

  doc.setFillColor(22, 163, 74);
  doc.rect(0, 0, 210, 24, "F");
  doc.setTextColor(255, 255, 255);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(16);
  doc.text("Agri Scan - Crop Health Report", 14, 15);

  doc.setTextColor(33, 37, 41);
  doc.setFont("helvetica", "normal");
  doc.setFontSize(10);
  doc.text(`Generated: ${generatedAt}`, 14, 32);

  autoTable(doc, {
    startY: 38,
    theme: "grid",
    styles: { fontSize: 10 },
    headStyles: { fillColor: [22, 163, 74] },
    head: [["Field", "Value"]],
    body: [
      ["Detected Condition", normalizedDisease],
      ["Selected Crop", selectedCrop],
      ["Confidence", `${confidencePercent}%`],
      ["Status", result.rejected ? "Rejected Scan" : result.uncertain ? "Monitor Closely" : "Actionable"],
      ["Scan Quality", result.rejected ? `Rejected: ${result.rejection_reason ?? "Unknown reason"}` : "Accepted"],
      ["Model Status", modelInfo?.model_loaded ? "Loaded" : "Fallback"],
      ["Class Count", String(modelInfo?.class_count ?? "N/A")],
      [
        "Confidence Threshold",
        modelInfo ? `${Math.round(modelInfo.confidence_threshold * 100)}%` : "N/A",
      ],
      ["Field Location", geolocation || "Not provided"],
      ["Field Notes", fieldNotes || "Not provided"],
    ],
  });

  if ((result.top_predictions?.length ?? 0) > 0) {
    autoTable(doc, {
      startY: getLastY() > 0 ? getLastY() + 8 : 105,
      theme: "striped",
      styles: { fontSize: 10 },
      headStyles: { fillColor: [22, 163, 74] },
      head: [["Top Predictions", "Confidence"]],
      body: (result.top_predictions ?? []).slice(0, 3).map((item) => [
        normalizeDiseaseName(item.disease),
        `${Math.round(item.confidence * 100)}%`,
      ]),
    });
  }

  autoTable(doc, {
    startY: getLastY() > 0 ? getLastY() + 8 : 150,
    theme: "plain",
    styles: { fontSize: 10 },
    headStyles: { fillColor: [22, 163, 74] },
    head: [["Recommended Next Steps"]],
    body: treatmentTips.map((tip) => [tip]),
  });

  doc.setFontSize(9);
  doc.setTextColor(95, 99, 104);
  doc.text(
    "Disclaimer: AI output is advisory only. Verify with local agricultural experts before pesticide use.",
    14,
    286,
  );

  const safeName = normalizedDisease.toLowerCase().replace(/[^a-z0-9]+/gi, "-");
  doc.save(`agri-scan-report-${safeName || "result"}.pdf`);
}

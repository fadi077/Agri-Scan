"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, Clipboard, Download, LocateFixed, ScanSearch, Sparkles } from "lucide-react";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { FarmerActionPlan } from "@/components/FarmerActionPlan";
import { InvalidScanNotice } from "@/components/InvalidScanNotice";
import { ResultCard } from "@/components/ResultCard";
import { SafetyDisclaimer } from "@/components/SafetyDisclaimer";
import { TopPredictions } from "@/components/TopPredictions";
import { TreatmentAdvice } from "@/components/TreatmentAdvice";
import { getModelInfo, type ModelInfoResponse, type PredictionResponse } from "@/lib/api";
import { downloadScanReportPdf } from "@/lib/report";
import { normalizeDiseaseName, treatmentAdvice } from "@/lib/treatments";

type StoredResult = PredictionResponse & {
  disease: string;
};

export default function ResultPage() {
  const [shareLabel, setShareLabel] = useState("Share Report");
  const [modelInfo, setModelInfo] = useState<ModelInfoResponse | null>(null);
  const [fieldNotes, setFieldNotes] = useState("");
  const [geoText, setGeoText] = useState("Not provided");

  useEffect(() => {
    getModelInfo().then(setModelInfo).catch(() => setModelInfo(null));
  }, []);

  const result = useMemo<StoredResult | null>(() => {
    if (typeof window === "undefined") return null;
    const resultRaw = sessionStorage.getItem("agri-scan-result");
    if (!resultRaw) return null;

    const parsed = JSON.parse(resultRaw) as StoredResult;
    return {
      ...parsed,
      disease: normalizeDiseaseName(parsed.disease),
    };
  }, []);

  const preview = useMemo(() => {
    if (typeof window === "undefined") return "";
    return sessionStorage.getItem("agri-scan-preview") ?? "";
  }, []);

  const reportText = useMemo(() => {
    if (!result) return "";
    return `Agri Scan Report\nDisease: ${result.disease}\nConfidence: ${Math.round(
      result.confidence * 100,
    )}%`;
  }, [result]);

  const onShare = async () => {
    if (!reportText) return;
    await navigator.clipboard.writeText(reportText);
    setShareLabel("Copied!");
    setTimeout(() => setShareLabel("Share Report"), 1500);
  };

  const onDownloadPdf = () => {
    if (!result) return;

    const treatmentTips =
      treatmentAdvice[result.disease] ?? [
        "Consult your local agriculture extension officer for a field-specific treatment plan.",
        "Monitor neighboring plants and isolate visibly affected leaves quickly.",
      ];

    const selectedCrop = (result.selected_crop ?? "any").toUpperCase();

    downloadScanReportPdf({
      result,
      modelInfo,
      treatmentTips,
      selectedCrop,
      fieldNotes,
      geolocation: geoText,
    });
  };

  const captureLocation = () => {
    if (!navigator.geolocation) {
      setGeoText("Geolocation not supported on this device");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        setGeoText(`${latitude.toFixed(5)}, ${longitude.toFixed(5)}`);
      },
      () => setGeoText("Location permission denied"),
      { enableHighAccuracy: true, timeout: 10000 },
    );
  };

  if (typeof window === "undefined") {
    return (
      <div className="mx-auto w-full max-w-4xl px-4 py-8 sm:px-6">
        <div className="animate-pulse space-y-4">
          <div className="h-10 w-56 rounded-md bg-gray-200" />
          <div className="h-72 w-full rounded-2xl bg-gray-200" />
          <div className="h-40 w-full rounded-2xl bg-gray-200" />
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="content-shell py-8">
        <Card className="soft-panel border-amber-200 bg-amber-50">
          <CardContent className="space-y-3 p-6">
            <h1 className="text-2xl font-semibold text-amber-900">No result found</h1>
            <p className="text-sm text-amber-800">
              Start a new scan to generate a disease report.
            </p>
            <Link
              href="/scan"
              className={buttonVariants({
                className: "bg-green-600 text-white hover:bg-green-700",
              })}
            >
              <ScanSearch className="mr-2 h-4 w-4" />
              Scan Again
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="w-full">
      <section className="relative overflow-hidden border-b border-white/40">
        <div className="absolute inset-0 bg-[linear-gradient(120deg,rgba(22,101,52,0.90),rgba(22,101,52,0.58)),linear-gradient(to_right,rgba(255,255,255,0.06)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.05)_1px,transparent_1px)] bg-[size:auto,48px_48px,48px_48px]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_10%_20%,rgba(134,239,172,0.25),transparent_35%),radial-gradient(circle_at_85%_80%,rgba(187,247,208,0.22),transparent_35%)]" />
        <div className="content-shell relative py-14 text-center md:py-18">
          <p className="mx-auto mb-4 inline-flex items-center gap-1 rounded-full border border-green-200/60 bg-white/20 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-green-50">
            <Sparkles className="h-3.5 w-3.5" />
            AI Result Summary
          </p>
          <h1 className="mx-auto max-w-3xl text-4xl font-semibold tracking-tight text-white md:text-5xl">
            Disease Analysis Result
          </h1>
          <p className="mx-auto mt-3 max-w-2xl text-sm text-green-50/90 md:text-base">
            Review confidence, compare top conditions, and follow recommended next steps.
          </p>
          <div className="mt-6 grid gap-2 text-sm text-green-50/95 sm:grid-cols-3">
            <p className="inline-flex items-center justify-center gap-2 rounded-lg border border-white/25 bg-white/15 px-3 py-2">
              <CheckCircle2 className="h-4 w-4 text-amber-300" />
              Confidence-aware output
            </p>
            <p className="inline-flex items-center justify-center gap-2 rounded-lg border border-white/25 bg-white/15 px-3 py-2">
              <CheckCircle2 className="h-4 w-4 text-amber-300" />
              Top condition ranking
            </p>
            <p className="inline-flex items-center justify-center gap-2 rounded-lg border border-white/25 bg-white/15 px-3 py-2">
              <CheckCircle2 className="h-4 w-4 text-amber-300" />
              Actionable treatment tips
            </p>
          </div>
        </div>
      </section>

      <div className="content-shell flex flex-col gap-6 py-8 md:py-10">
        <SafetyDisclaimer />
        {modelInfo && (
          <p className="rounded-xl border border-green-100 bg-white/75 px-4 py-3 text-xs text-gray-600">
            Model status: {modelInfo.model_loaded ? "Loaded" : "Fallback"} | Classes:{" "}
            {modelInfo.class_count} | Confidence threshold:{" "}
            {Math.round(modelInfo.confidence_threshold * 100)}%
          </p>
        )}
        <Card className="soft-panel rounded-2xl">
          <CardContent className="grid gap-3 p-4 md:grid-cols-[1fr_auto]">
            <div className="space-y-2">
              <p className="text-xs font-medium uppercase tracking-wide text-gray-500">
                Field Context (for better reports)
              </p>
              <textarea
                value={fieldNotes}
                onChange={(event) => setFieldNotes(event.target.value)}
                className="min-h-24 w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none focus:border-green-500"
                placeholder="Add field notes (symptoms observed, weather, recent spray, etc.)"
              />
              <p className="text-xs text-gray-600">Location: {geoText}</p>
            </div>
            <Button variant="outline" className="h-fit" onClick={captureLocation}>
              <LocateFixed className="mr-2 h-4 w-4" />
              Use Current Location
            </Button>
          </CardContent>
        </Card>
        <ResultCard
          disease={result.disease}
          confidence={result.confidence}
          previewSrc={preview}
          uncertain={Boolean(result.uncertain)}
        />
        {result.storage && (
          <p className="soft-panel rounded-xl px-4 py-3 text-xs leading-relaxed text-gray-700">
            This scan was saved on the API machine under{" "}
            <code className="break-all rounded bg-gray-100 px-1 py-0.5 text-[11px]">
              {result.storage.saved_file}
            </code>
            {result.storage.matching_training_folder ? (
              <>
                {" "}
                The predicted label matches a subfolder in your training dataset:{" "}
                <span className="font-medium">{result.storage.matching_training_folder}</span>.
              </>
            ) : result.storage.training_dataset_configured ? (
              <> No folder with the exact predicted class name was found under your configured training dataset.</>
            ) : (
              <>
                {" "}
                Set <code className="text-[11px]">TRAINING_DATASET_DIR</code> in the backend env to link scans to
                your ImageFolder layout.
              </>
            )}
          </p>
        )}
        {result.rejected ? (
          <InvalidScanNotice
            reason={result.rejection_reason}
            onRetry={() => {
              window.location.href = "/scan";
            }}
          />
        ) : (
          <>
            <TopPredictions predictions={result.top_predictions ?? []} />
            <FarmerActionPlan
              confidence={result.confidence}
              uncertain={Boolean(result.uncertain)}
              rejected={Boolean(result.rejected)}
            />
            <TreatmentAdvice disease={result.disease} />
          </>
        )}

        <div className="sticky bottom-3 z-10 flex flex-col gap-3 rounded-2xl border border-green-100 bg-white/95 p-3 shadow-xl backdrop-blur-md sm:flex-row">
          <Link
            href="/scan"
            className={buttonVariants({
              className: "bg-green-600 text-white hover:bg-green-700",
            })}
          >
            Scan Again
          </Link>
          <Button variant="outline" onClick={onShare} aria-label="Share report">
            <Clipboard className="mr-2 h-4 w-4" />
            {shareLabel}
          </Button>
          <Button variant="outline" onClick={onDownloadPdf} aria-label="Download PDF report">
            <Download className="mr-2 h-4 w-4" />
            Download PDF
          </Button>
        </div>
      </div>
    </div>
  );
}

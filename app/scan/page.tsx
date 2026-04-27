"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Camera, CheckCircle2, ShieldCheck, Sparkles } from "lucide-react";
import { CameraScanner } from "@/components/CameraScanner";
import { SafetyDisclaimer } from "@/components/SafetyDisclaimer";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { getModelInfo, predict, type ModelInfoResponse } from "@/lib/api";
import { normalizeDiseaseName } from "@/lib/treatments";

export default function ScanPage() {
  const router = useRouter();
  const [language, setLanguage] = useState<"en" | "ur">("en");
  const [modelInfo, setModelInfo] = useState<ModelInfoResponse | null>(null);

  useEffect(() => {
    getModelInfo().then(setModelInfo).catch(() => setModelInfo(null));
  }, []);

  const copy = useMemo(
    () =>
      language === "en"
        ? {
            title: "Scan Your Leaf",
            subtitle:
              "Use the live camera feed and place the leaf inside the guide frame, then tap Scan Now.",
            sunlight: "Use natural daylight when possible.",
            frame: "Fill the frame with one clear leaf.",
            blur: "Avoid motion blur while capturing.",
            languageLabel: "Language",
            frameInstruction: "Position leaf inside the frame",
            scanNow: "Scan Now",
            scanning: "Scanning...",
            uploadFallback: "Upload an image instead",
            placeholderModel:
              "The API is using temporary weights so scans work end-to-end. Train on your real leaf dataset (see project README), save artifacts/best.pt, then restart the backend for real disease detection.",
          }
        : {
            title: "پتے کو اسکین کریں",
            subtitle: "کیمرہ میں پتے کو فریم کے اندر رکھیں اور اسکین کریں۔",
            sunlight: "ممکن ہو تو دن کی روشنی میں تصویر لیں۔",
            frame: "ایک واضح پتے کو فریم میں رکھیں۔",
            blur: "تصویر دھندلی نہ ہو۔",
            languageLabel: "زبان",
            frameInstruction: "پتے کو فریم کے اندر رکھیں",
            scanNow: "اسکین کریں",
            scanning: "اسکین ہو رہا ہے...",
            uploadFallback: "متبادل طور پر تصویر اپ لوڈ کریں",
            placeholderModel:
              "سرور عارضی وزن استعمال کر رہا ہے۔ اصل پتے کی تصاویر پر تربیت کریں، artifacts/best.pt محفوظ کریں، اور پھر بیک اینڈ دوبارہ چلائیں۔",
          },
    [language],
  );

  const handleCapture = async (imageBlob: Blob) => {
    const result = await predict(imageBlob, "any");
    const disease = normalizeDiseaseName(result.disease);

    sessionStorage.setItem(
      "agri-scan-result",
      JSON.stringify({
        ...result,
        disease,
        selected_crop: "any",
      }),
    );

    router.push("/result");
  };

  const handlePreviewReady = (previewDataUrl: string) => {
    sessionStorage.setItem("agri-scan-preview", previewDataUrl);
  };

  return (
    <div className="w-full">
      <section className="relative overflow-hidden border-b border-white/40">
        <div className="absolute inset-0 bg-[linear-gradient(120deg,rgba(22,101,52,0.90),rgba(22,101,52,0.58)),linear-gradient(to_right,rgba(255,255,255,0.06)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.05)_1px,transparent_1px)] bg-[size:auto,48px_48px,48px_48px]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_10%_20%,rgba(134,239,172,0.25),transparent_35%),radial-gradient(circle_at_85%_80%,rgba(187,247,208,0.22),transparent_35%)]" />
        <div className="content-shell relative py-14 text-center md:py-18">
          <p className="mx-auto mb-4 inline-flex items-center gap-1 rounded-full border border-green-200/60 bg-white/20 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-green-50">
            <Sparkles className="h-3.5 w-3.5" />
            Smart Capture
          </p>
          <h1 className="mx-auto max-w-3xl text-4xl font-semibold tracking-tight text-white md:text-5xl">
            {copy.title}
          </h1>
          <p className="mx-auto mt-3 max-w-2xl text-sm text-green-50/90 md:text-base">{copy.subtitle}</p>
          <div className="mt-6 grid gap-2 text-sm text-green-50/95 sm:grid-cols-3">
            <p className="inline-flex items-center justify-center gap-2 rounded-lg border border-white/25 bg-white/15 px-3 py-2">
              <CheckCircle2 className="h-4 w-4 text-amber-300" />
              {copy.sunlight}
            </p>
            <p className="inline-flex items-center justify-center gap-2 rounded-lg border border-white/25 bg-white/15 px-3 py-2">
              <CheckCircle2 className="h-4 w-4 text-amber-300" />
              {copy.frame}
            </p>
            <p className="inline-flex items-center justify-center gap-2 rounded-lg border border-white/25 bg-white/15 px-3 py-2">
              <CheckCircle2 className="h-4 w-4 text-amber-300" />
              {copy.blur}
            </p>
          </div>
          <div className="mx-auto mt-4 max-w-3xl">
            <SafetyDisclaimer compact />
          </div>
          {modelInfo?.model_loaded && modelInfo.diagnostic_ready === false && (
            <p className="mx-auto mt-4 max-w-3xl rounded-xl border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-950">
              {copy.placeholderModel}
            </p>
          )}
        </div>
      </section>

      <div className="content-shell flex flex-col gap-6 py-8 md:py-10">
        <Card className="soft-panel rounded-2xl">
          <CardContent className="grid gap-4 p-5 md:grid-cols-[1fr_auto] md:items-end">
            <div>
              <p className="mb-2 text-sm font-medium text-gray-700">{copy.languageLabel}</p>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant={language === "en" ? "default" : "outline"}
                  className={language === "en" ? "bg-green-600 text-white hover:bg-green-700" : ""}
                  onClick={() => setLanguage("en")}
                >
                  English
                </Button>
                <Button
                  type="button"
                  variant={language === "ur" ? "default" : "outline"}
                  className={language === "ur" ? "bg-green-600 text-white hover:bg-green-700" : ""}
                  onClick={() => setLanguage("ur")}
                >
                  اردو
                </Button>
              </div>
            </div>
            <div className="inline-flex items-center gap-2 rounded-xl border border-green-100 bg-green-50/70 px-3 py-2 text-xs text-green-800">
              <ShieldCheck className="h-4 w-4" />
              Safer predictions with confidence checks
            </div>
          </CardContent>
        </Card>

        <Card className="soft-panel rounded-2xl">
          <CardContent className="grid gap-3 p-5 text-sm text-gray-700 md:grid-cols-3">
            <p className="inline-flex items-center gap-2">
              <Camera className="h-4 w-4 text-green-600" />
              {copy.sunlight}
            </p>
            <p className="inline-flex items-center gap-2">
              <Camera className="h-4 w-4 text-green-600" />
              {copy.frame}
            </p>
            <p className="inline-flex items-center gap-2">
              <Camera className="h-4 w-4 text-green-600" />
              {copy.blur}
            </p>
          </CardContent>
        </Card>

        <div className="hero-surface p-4 md:p-6">
          <CameraScanner
            onCapture={handleCapture}
            onPreviewReady={handlePreviewReady}
            labels={{
              frameInstruction: copy.frameInstruction,
              scanNow: copy.scanNow,
              scanning: copy.scanning,
              uploadFallback: copy.uploadFallback,
            }}
          />
        </div>
      </div>
    </div>
  );
}

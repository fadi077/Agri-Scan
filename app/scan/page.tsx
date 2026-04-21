"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { CameraScanner } from "@/components/CameraScanner";
import { SafetyDisclaimer } from "@/components/SafetyDisclaimer";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { type CropType, predict } from "@/lib/api";
import { normalizeDiseaseName } from "@/lib/treatments";

export default function ScanPage() {
  const router = useRouter();
  const [selectedCrop, setSelectedCrop] = useState<CropType>("tomato");
  const [language, setLanguage] = useState<"en" | "ur">("en");

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
            cropLabel: "Select Crop",
            languageLabel: "Language",
            frameInstruction: "Position leaf inside the frame",
            scanNow: "Scan Now",
            scanning: "Scanning...",
            uploadFallback: "Upload an image instead",
          }
        : {
            title: "پتے کو اسکین کریں",
            subtitle: "کیمرہ میں پتے کو فریم کے اندر رکھیں اور اسکین کریں۔",
            sunlight: "ممکن ہو تو دن کی روشنی میں تصویر لیں۔",
            frame: "ایک واضح پتے کو فریم میں رکھیں۔",
            blur: "تصویر دھندلی نہ ہو۔",
            cropLabel: "فصل منتخب کریں",
            languageLabel: "زبان",
            frameInstruction: "پتے کو فریم کے اندر رکھیں",
            scanNow: "اسکین کریں",
            scanning: "اسکین ہو رہا ہے...",
            uploadFallback: "متبادل طور پر تصویر اپ لوڈ کریں",
          },
    [language],
  );

  const handleCapture = async (imageBlob: Blob) => {
    const result = await predict(imageBlob, selectedCrop);
    const disease = normalizeDiseaseName(result.disease);

    sessionStorage.setItem(
      "agri-scan-result",
      JSON.stringify({
        ...result,
        disease,
        selected_crop: selectedCrop,
      }),
    );

    router.push("/result");
  };

  const handlePreviewReady = (previewDataUrl: string) => {
    sessionStorage.setItem("agri-scan-preview", previewDataUrl);
  };

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-4 py-10 sm:px-6">
      <section className="glass-card rounded-3xl p-6 md:p-8">
        <h1 className="section-title">{copy.title}</h1>
        <p className="mt-2 text-sm text-gray-600 md:text-base">{copy.subtitle}</p>
        <div className="mt-3">
          <SafetyDisclaimer compact />
        </div>
      </section>

      <Card className="glass-card rounded-2xl">
        <CardContent className="grid gap-4 p-4 md:grid-cols-2">
          <div>
            <p className="mb-2 text-sm font-medium text-gray-700">{copy.cropLabel}</p>
            <div className="flex flex-wrap gap-2">
              {[
                { id: "tomato", label: "Tomato" },
                { id: "potato", label: "Potato" },
                { id: "pepper", label: "Pepper" },
                { id: "any", label: "Any Crop" },
              ].map((crop) => (
                <Button
                  key={crop.id}
                  type="button"
                  variant={selectedCrop === crop.id ? "default" : "outline"}
                  className={selectedCrop === crop.id ? "bg-green-600 text-white hover:bg-green-700" : ""}
                  onClick={() => setSelectedCrop(crop.id as CropType)}
                >
                  {crop.label}
                </Button>
              ))}
            </div>
          </div>
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
        </CardContent>
      </Card>

      <Card className="glass-card rounded-2xl">
        <CardContent className="grid gap-2 p-4 text-sm text-gray-700 md:grid-cols-3">
          <p>{copy.sunlight}</p>
          <p>{copy.frame}</p>
          <p>{copy.blur}</p>
        </CardContent>
      </Card>

      <div className="glass-card rounded-3xl p-4 md:p-6">
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
  );
}

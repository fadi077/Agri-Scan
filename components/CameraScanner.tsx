"use client";

import { ChangeEvent, useEffect, useMemo, useRef, useState } from "react";
import Webcam from "react-webcam";
import { Camera, Loader2, TriangleAlert, WifiOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { LoadingOverlay } from "@/components/LoadingOverlay";

type CameraScannerProps = {
  onCapture: (imageBlob: Blob) => Promise<void> | void;
  onPreviewReady?: (previewDataUrl: string) => void;
  labels?: {
    frameInstruction: string;
    scanNow: string;
    scanning: string;
    uploadFallback: string;
  };
};

function dataUrlToBlob(dataUrl: string): Blob {
  const [metadata, content] = dataUrl.split(",");
  const mime = metadata.match(/:(.*?);/)?.[1] ?? "image/jpeg";
  const bytes = atob(content);
  const length = bytes.length;
  const array = new Uint8Array(length);
  for (let i = 0; i < length; i += 1) {
    array[i] = bytes.charCodeAt(i);
  }
  return new Blob([array], { type: mime });
}

export function CameraScanner({ onCapture, onPreviewReady, labels }: CameraScannerProps) {
  const text = labels ?? {
    frameInstruction: "Position leaf inside the frame",
    scanNow: "Scan Now",
    scanning: "Scanning...",
    uploadFallback: "Upload an image instead",
  };

  const webcamRef = useRef<Webcam | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [scanError, setScanError] = useState<string | null>(null);
  const [isOnline, setIsOnline] = useState(true);

  const cameraSupported = useMemo(
    () => typeof navigator !== "undefined" && !!navigator.mediaDevices?.getUserMedia,
    [],
  );

  useEffect(() => {
    if (typeof window === "undefined") return;
    const updateStatus = () => setIsOnline(navigator.onLine);
    updateStatus();
    window.addEventListener("online", updateStatus);
    window.addEventListener("offline", updateStatus);
    return () => {
      window.removeEventListener("online", updateStatus);
      window.removeEventListener("offline", updateStatus);
    };
  }, []);

  const captureAndScan = async () => {
    if (!isOnline) {
      setScanError("You are offline. Reconnect to run AI disease analysis.");
      return;
    }

    const imageData = webcamRef.current?.getScreenshot();
    if (!imageData) {
      setCameraError("Unable to capture frame. Please allow camera access and try again.");
      return;
    }

    const blob = dataUrlToBlob(imageData);
    onPreviewReady?.(imageData);

    try {
      setIsLoading(true);
      setScanError(null);
      await onCapture(blob);
    } catch (err) {
      setScanError(err instanceof Error ? err.message : "Scan request failed. Check backend status and try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const onFileFallback = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const preview = URL.createObjectURL(file);
    onPreviewReady?.(preview);

    try {
      setIsLoading(true);
      setScanError(null);
      await onCapture(file);
    } catch (err) {
      setScanError(err instanceof Error ? err.message : "Upload scan failed. Check backend connection and retry.");
    } finally {
      setIsLoading(false);
      event.target.value = "";
    }
  };

  return (
    <section className="mx-auto w-full max-w-2xl">
      {!cameraSupported ? (
        <div className="rounded-2xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900">
          <p className="flex items-center gap-2 font-medium">
            <TriangleAlert className="h-4 w-4" />
            Camera is not supported in this browser.
          </p>
          <p className="mt-2">Use the upload fallback to continue scanning your leaf.</p>
        </div>
      ) : (
        <div className="relative overflow-hidden rounded-2xl border border-green-200 bg-black shadow-sm">
          {isLoading && <LoadingOverlay />}
          <Webcam
            ref={webcamRef}
            audio={false}
            mirrored={false}
            screenshotFormat="image/jpeg"
            videoConstraints={{ facingMode: { ideal: "environment" } }}
            className="h-auto w-full"
            aria-label="Live camera feed for leaf scanning"
            onUserMediaError={() =>
              setCameraError(
                "Camera permission denied or unavailable. Please allow camera access or use upload.",
              )
            }
          />
          <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
            <div className="h-56 w-72 rounded-xl border-4 border-green-400/90 shadow-[0_0_0_9999px_rgba(0,0,0,0.35)] md:h-64 md:w-96" />
            <p className="absolute top-4 rounded-full bg-green-600/95 px-3 py-1 text-xs font-medium text-white">
              {text.frameInstruction}
            </p>
          </div>
        </div>
      )}

      {cameraError && (
        <p className="mt-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {cameraError}
        </p>
      )}

      {!isOnline && (
        <p className="mt-3 rounded-md border border-blue-200 bg-blue-50 px-3 py-2 text-sm text-blue-700">
          <span className="inline-flex items-center gap-2">
            <WifiOff className="h-4 w-4" />
            Offline mode detected. Capture is available, but AI prediction needs internet/backend
            access.
          </span>
        </p>
      )}

      {scanError && (
        <p className="mt-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {scanError}
        </p>
      )}

      <div className="mt-5 flex flex-col items-center gap-3">
        <Button
          onClick={captureAndScan}
          disabled={isLoading || !cameraSupported}
          className="h-11 w-full max-w-xs bg-green-600 text-white hover:bg-green-700"
          aria-label="Scan now"
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              {text.scanning}
            </>
          ) : (
            <>
              <Camera className="mr-2 h-4 w-4" />
              {text.scanNow}
            </>
          )}
        </Button>

        <button
          type="button"
          className="text-sm text-green-700 underline underline-offset-4 hover:text-green-800"
          onClick={() => fileInputRef.current?.click()}
          aria-label="Upload an image instead"
        >
          {text.uploadFallback}
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png"
          className="hidden"
          onChange={onFileFallback}
        />
      </div>
    </section>
  );
}

import Link from "next/link";
import {
  ArrowUpFromLine,
  BrainCircuit,
  CheckCircle2,
  ClipboardList,
  Leaf,
  ScanLine,
  ShieldCheck,
  Sprout,
} from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function Home() {
  return (
    <div className="w-full">
      <section className="relative overflow-hidden border-b border-white/40">
        <div className="absolute inset-0 bg-[linear-gradient(120deg,rgba(22,101,52,0.90),rgba(22,101,52,0.58)),linear-gradient(to_right,rgba(255,255,255,0.06)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.05)_1px,transparent_1px)] bg-[size:auto,48px_48px,48px_48px]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_10%_20%,rgba(134,239,172,0.25),transparent_35%),radial-gradient(circle_at_85%_80%,rgba(187,247,208,0.22),transparent_35%)]" />
        <div className="content-shell relative py-16 text-center md:py-24">
          <p className="mx-auto mb-4 inline-flex items-center rounded-full border border-green-200/60 bg-white/20 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-green-50">
            <Leaf className="mr-1 h-3.5 w-3.5" />
            AI-Powered Crop Health Predictor
          </p>
          <h1 className="mx-auto max-w-3xl text-4xl font-semibold tracking-tight text-white md:text-6xl">
            Protect Your Crops with <span className="text-amber-300">Intelligent Scanning</span>
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-sm text-green-50/90 md:text-base">
            Upload a photo of your crop leaf and get instant AI-powered disease detection with
            targeted treatment recommendations.
          </p>
          <div className="mt-7 flex flex-wrap justify-center gap-3">
            <Link
              href="/scan"
              className={buttonVariants({
                className: "h-11 bg-amber-400 px-5 font-semibold text-green-950 hover:bg-amber-300",
              })}
            >
              Scan Your Crop
            </Link>
            <Link
              href="/about"
              className={buttonVariants({
                variant: "outline",
                className: "h-11 border-white/70 bg-white/15 px-5 text-white hover:bg-white/25",
              })}
            >
              Learn More
            </Link>
          </div>
          <div className="mx-auto mt-8 grid max-w-3xl gap-3 text-left sm:grid-cols-3">
            <div className="rounded-xl border border-white/30 bg-white/15 p-3 text-white">
              <p className="inline-flex items-center gap-2 text-sm font-semibold">
                <CheckCircle2 className="h-4 w-4 text-amber-300" />
                95% Accuracy
              </p>
              <p className="mt-1 text-xs text-green-50/85">High quality predictions on trained crops</p>
            </div>
            <div className="rounded-xl border border-white/30 bg-white/15 p-3 text-white">
              <p className="inline-flex items-center gap-2 text-sm font-semibold">
                <BrainCircuit className="h-4 w-4 text-amber-300" />
                AI Inference
              </p>
              <p className="mt-1 text-xs text-green-50/85">Fast confidence-aware model inference</p>
            </div>
            <div className="rounded-xl border border-white/30 bg-white/15 p-3 text-white">
              <p className="inline-flex items-center gap-2 text-sm font-semibold">
                <ClipboardList className="h-4 w-4 text-amber-300" />
                PDF Reports
              </p>
              <p className="mt-1 text-xs text-green-50/85">Treatment plan and scan summary export</p>
            </div>
          </div>
        </div>
      </section>

      <section id="features" className="content-shell py-14 md:py-16">
        <p className="text-center text-xs font-semibold uppercase tracking-[0.14em] text-green-700/80">
          Features
        </p>
        <h2 className="mt-2 text-center text-3xl font-semibold text-green-900 md:text-4xl">
          Smart Farming Made Simple
        </h2>
        <p className="mx-auto mt-3 max-w-2xl text-center text-sm text-gray-600 md:text-base">
          Upload crop leaves and receive fast disease detection, treatment insights, and exportable reports.
        </p>
        <div className="mt-8 grid gap-4 md:grid-cols-4">
          <Card className="soft-panel rounded-xl">
            <CardHeader>
              <ArrowUpFromLine className="h-5 w-5 text-green-700" />
              <CardTitle className="text-base">Image Upload</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-gray-600">
              Drag and drop or choose files from your device in seconds.
            </CardContent>
          </Card>
          <Card className="soft-panel rounded-xl">
            <CardHeader>
              <BrainCircuit className="h-5 w-5 text-green-700" />
              <CardTitle className="text-base">AI Detection</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-gray-600">
              Predict likely diseases with confidence-aware logic.
            </CardContent>
          </Card>
          <Card className="soft-panel rounded-xl">
            <CardHeader>
              <ClipboardList className="h-5 w-5 text-green-700" />
              <CardTitle className="text-base">Treatment Plans</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-gray-600">
              Get practical next-step recommendations after each scan.
            </CardContent>
          </Card>
          <Card className="soft-panel rounded-xl">
            <CardHeader>
              <ShieldCheck className="h-5 w-5 text-green-700" />
              <CardTitle className="text-base">Reliable Checks</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-gray-600">
              Safety gating avoids risky low-confidence predictions.
            </CardContent>
          </Card>
        </div>
      </section>

      <section className="border-y border-gray-200/70 bg-gray-50/70">
        <div className="content-shell py-14">
          <p className="text-center text-xs font-semibold uppercase tracking-[0.14em] text-green-700/80">
            Diagnose
          </p>
          <h2 className="mt-2 text-center text-3xl font-semibold text-green-900 md:text-4xl">
            Scan Your Crop Leaf
          </h2>
          <p className="mx-auto mt-3 max-w-2xl text-center text-sm text-gray-600 md:text-base">
            Capture or upload a leaf image to start AI diagnosis and receive treatment guidance.
          </p>
          <div className="mx-auto mt-8 grid max-w-4xl gap-4 md:grid-cols-2">
            <Link
              href="/scan"
              className="group rounded-2xl border border-dashed border-green-300 bg-white p-8 text-center shadow-sm transition hover:border-green-500 hover:shadow-md"
            >
              <ScanLine className="mx-auto h-8 w-8 text-green-700" />
              <p className="mt-4 text-base font-semibold text-green-900">Open Scanner</p>
              <p className="mt-2 text-sm text-gray-600">Use camera or upload a crop leaf image</p>
            </Link>
            <div className="rounded-2xl border border-gray-200 bg-white p-8 text-center shadow-sm">
              <Sprout className="mx-auto h-8 w-8 text-green-700" />
              <p className="mt-4 text-base font-semibold text-green-900">Fast AI Analysis</p>
              <p className="mt-2 text-sm text-gray-600">
                View confidence, top predictions, and treatment suggestions
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="content-shell py-14 md:py-16">
        <p className="text-center text-xs font-semibold uppercase tracking-[0.14em] text-green-700/80">
          About The Project
        </p>
        <h2 className="mt-2 text-center text-3xl font-semibold text-green-900 md:text-4xl">
          Fighting Crop Loss with AI
        </h2>
        <p className="mx-auto mt-3 max-w-3xl text-center text-sm text-gray-600 md:text-base">
          Crop diseases can significantly reduce yield. Agri Scan helps farmers make faster and safer decisions by
          combining intelligent diagnosis, confidence checks, and practical action plans.
        </p>
        <div className="mt-8 grid gap-4 md:grid-cols-3">
          <Card className="soft-panel rounded-xl">
            <CardHeader>
              <CardTitle className="text-base text-green-900">Our Mission</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-gray-600">
              Bring reliable AI crop diagnostics to farmers and field workers.
            </CardContent>
          </Card>
          <Card className="soft-panel rounded-xl">
            <CardHeader>
              <CardTitle className="text-base text-green-900">For Farmers</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-gray-600">
              Improve field decisions with quick scans and easy-to-understand outputs.
            </CardContent>
          </Card>
          <Card className="soft-panel rounded-xl">
            <CardHeader>
              <CardTitle className="text-base text-green-900">Sustainability</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-gray-600">
              Reduce unnecessary pesticide use with targeted recommendations.
            </CardContent>
          </Card>
        </div>
      </section>

      <footer className="border-t border-green-900/20 bg-green-900 text-green-100">
        <div className="content-shell flex flex-col items-center justify-between gap-2 py-5 text-sm md:flex-row">
          <p className="inline-flex items-center gap-2 font-medium">
            <Leaf className="h-4 w-4" />
            Agri Scan
          </p>
          <p className="text-green-100/80">AI Crop Diagnostics - Built for practical farming workflows</p>
        </div>
      </footer>
    </div>
  );
}

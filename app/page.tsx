import Link from "next/link";
import { ArrowRight, Leaf, ScanLine, ShieldCheck, Smartphone } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SafetyDisclaimer } from "@/components/SafetyDisclaimer";

export default function Home() {
  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-12 px-4 py-10 sm:px-6 md:py-14">
      <section className="glass-card relative overflow-hidden rounded-3xl p-7 md:p-12">
        <div className="pointer-events-none absolute -right-12 -top-14 h-56 w-56 rounded-full bg-green-300/35 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-14 left-16 h-44 w-44 rounded-full bg-emerald-300/20 blur-3xl" />
        <p className="mb-3 inline-flex items-center rounded-full border border-green-200 bg-green-50 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-green-700">
          <Leaf className="mr-1 h-3.5 w-3.5" />
          AI Crop Health Assistant
        </p>
        <h1 className="section-title">Agri Scan</h1>
        <p className="mt-2 text-xl font-medium text-gray-800">A Plant Doctor in Your Pocket</p>
        <p className="mt-4 max-w-2xl text-gray-600">
          Detect crop diseases in seconds with 95% accuracy. Built for real field conditions
          with confidence-aware recommendations and practical next steps.
        </p>
        <div className="mt-7 flex flex-wrap gap-3">
          <Link
            href="/scan"
            className={buttonVariants({
              className: "h-11 bg-green-600 px-5 text-white hover:bg-green-700",
            })}
          >
            Start Live Scan <ArrowRight className="ml-2 h-4 w-4" />
          </Link>
          <Link
            href="/about"
            className={buttonVariants({
              variant: "outline",
              className: "h-11 border-green-200 bg-white/80 text-green-700 hover:bg-green-50",
            })}
          >
            Learn More
          </Link>
        </div>
      </section>
      <SafetyDisclaimer compact />

      <section className="grid gap-4 md:grid-cols-3">
        <Card className="glass-card rounded-2xl">
          <CardHeader>
            <ScanLine className="h-6 w-6 text-green-600" aria-hidden="true" />
            <CardTitle className="text-lg">Instant Detection</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-gray-600">
            Scan live through your camera and get disease predictions in moments.
          </CardContent>
        </Card>

        <Card className="glass-card rounded-2xl">
          <CardHeader>
            <ShieldCheck className="h-6 w-6 text-green-600" aria-hidden="true" />
            <CardTitle className="text-lg">Treatment Advice</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-gray-600">
            Receive actionable recommendations after every diagnosis.
          </CardContent>
        </Card>

        <Card className="glass-card rounded-2xl">
          <CardHeader>
            <Smartphone className="h-6 w-6 text-green-600" aria-hidden="true" />
            <CardTitle className="text-lg">Works on Any Device</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-gray-600">
            Mobile-first design makes it easy to use in the field.
          </CardContent>
        </Card>
      </section>
    </div>
  );
}

"use client";

import Link from "next/link";
import { useState } from "react";
import { usePathname } from "next/navigation";
import { ChevronRight, Leaf, Menu, X } from "lucide-react";
import { Button } from "@/components/ui/button";

const navItems = [
  { href: "/#features", label: "Features" },
  { href: "/scan", label: "Scan" },
  { href: "/about", label: "About" },
];

export function Navbar() {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-40 border-b border-green-100/70 bg-white/85 backdrop-blur-xl">
      <nav className="content-shell flex h-[4.5rem] items-center justify-between">
        <Link href="/" className="group flex items-center gap-2.5">
          <div className="flex size-9 items-center justify-center rounded-xl bg-green-100 text-green-700 ring-1 ring-green-200 transition group-hover:bg-green-200">
            <Leaf className="h-5 w-5" aria-hidden="true" />
          </div>
          <div>
            <p className="text-base font-semibold leading-tight text-green-800">Agri Scan</p>
            <p className="text-xs text-green-700/80">AI Disease Assistant</p>
          </div>
        </Link>

        <div className="hidden items-center gap-6 md:flex">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`rounded-full px-3 py-1.5 text-sm font-medium transition ${
                pathname === item.href
                  ? "bg-green-100 text-green-800"
                  : "text-gray-700 hover:bg-green-50 hover:text-green-700"
              }`}
            >
              {item.label}
            </Link>
          ))}
          <Link
            href="/scan"
            className="inline-flex items-center gap-1 rounded-full bg-green-600 px-3.5 py-2 text-sm font-medium text-white transition hover:bg-green-700"
          >
            Start Scanning <ChevronRight className="h-4 w-4" />
          </Link>
        </div>

        <Button
          variant="ghost"
          size="icon"
          className="md:hidden"
          aria-label={open ? "Close navigation menu" : "Open navigation menu"}
          onClick={() => setOpen((prev) => !prev)}
        >
          {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </Button>
      </nav>

      {open && (
        <div className="border-t border-green-100 bg-white/95 md:hidden">
          <div className="mx-auto flex max-w-6xl flex-col px-4 py-2">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`rounded-md px-2 py-3 text-sm font-medium transition ${
                  pathname === item.href
                    ? "bg-green-100 text-green-700"
                    : "text-gray-700 hover:bg-green-50 hover:text-green-700"
                }`}
                onClick={() => setOpen(false)}
              >
                {item.label}
              </Link>
            ))}
          </div>
        </div>
      )}
    </header>
  );
}

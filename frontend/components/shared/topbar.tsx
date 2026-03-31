"use client";

import { Eye } from "lucide-react";

export function Topbar() {
  return (
    <header className="flex h-16 items-center justify-end border-b border-midnight-100 bg-porcelain px-8">
      <div className="flex items-center gap-3 px-4 py-2 rounded-full bg-midnight-50 border border-midnight-200">
        <Eye className="h-3.5 w-3.5 text-midnight-500" />
        <span className="text-xs font-semibold text-midnight-600 tracking-wide">
          INCOGNITO MODE ACTIVE
        </span>
      </div>
    </header>
  );
}

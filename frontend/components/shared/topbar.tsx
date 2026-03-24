"use client";

import { Wifi, WifiOff } from "lucide-react";
import { ConnectionStatus } from "@/components/features/connection-status";

export function Topbar() {
  return (
    <header className="flex h-16 items-center justify-between border-b border-gray-200 bg-white px-6">
      <div className="flex items-center">
        <h2 className="text-lg font-semibold text-gray-900">
          Smart Learning Dashboard
        </h2>
      </div>

      <div className="flex items-center space-x-4">
        <ConnectionStatus />
      </div>
    </header>
  );
}

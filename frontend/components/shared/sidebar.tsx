"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { GraduationCap } from "lucide-react";

const navigation = [
  { name: "Dashboard", href: "/dashboard" },
  { name: "Daily Test", href: "/dashboard/daily-test" },
  { name: "Analytics", href: "/dashboard/analytics" },
  { name: "Counseling", href: "/dashboard/counseling" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="flex h-full w-80 flex-col bg-midnight-800 border-r border-midnight-700">
      {/* Logo */}
      <div className="flex h-20 items-center px-8 border-b border-midnight-700">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center shadow-lg">
            <GraduationCap className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-display font-bold text-white tracking-tight">
              English Test-Prep
            </h1>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-6 py-8">
        <div className="space-y-1">
          {navigation.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "relative flex items-center px-4 py-3.5 text-base font-sans font-medium transition-all duration-200 group",
                  isActive
                    ? "text-white"
                    : "text-midnight-300 hover:text-white"
                )}
              >
                {item.name}
                {isActive && (
                  <span className="absolute left-0 top-1/2 -translate-y-1/2 w-2 h-2 bg-primary-500 rounded-full shadow-lg shadow-primary-500/60 animate-pulse" />
                )}
              </Link>
            );
          })}
        </div>
      </nav>
    </div>
  );
}

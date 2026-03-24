"use client";

import { useEffect, useState } from "react";
import { Wifi, WifiOff, Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import api from "@/lib/api";

type ConnectionStatus = "connecting" | "connected" | "disconnected";

export function ConnectionStatus() {
  const [status, setStatus] = useState<ConnectionStatus>("connecting");
  const [lastCheck, setLastCheck] = useState<Date | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;

    const checkConnection = async () => {
      try {
        await api.healthCheck();
        setStatus("connected");
      } catch {
        setStatus("disconnected");
      }
      setLastCheck(new Date());
    };

    checkConnection();
    const interval = setInterval(checkConnection, 30000); // Check every 30s

    return () => clearInterval(interval);
  }, [mounted]);

  const statusConfig = {
    connecting: {
      icon: Loader2,
      label: "Connecting...",
      variant: "default" as const,
      iconClass: "animate-spin text-gray-500",
    },
    connected: {
      icon: Wifi,
      label: "Connected",
      variant: "success" as const,
      iconClass: "text-green-600",
    },
    disconnected: {
      icon: WifiOff,
      label: "Disconnected",
      variant: "error" as const,
      iconClass: "text-red-600",
    },
  };

  const config = statusConfig[status];
  const Icon = config.icon;

  return (
    <div className="flex items-center space-x-2">
      <Icon className={`h-4 w-4 ${config.iconClass}`} />
      <Badge variant={config.variant}>{config.label}</Badge>
      {lastCheck && (
        <span className="text-xs text-gray-500">
          {lastCheck.toLocaleTimeString()}
        </span>
      )}
    </div>
  );
}

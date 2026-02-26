import { useEffect, useRef } from "react";
import { useStore } from "../store/useStore";
import { useWorker } from "./useWorker";

export function useGPU(intervalMs = 2000) {
  const setGpuInfo = useStore((s) => s.setGpuInfo);
  const workerReady = useStore((s) => s.workerReady);
  const { send } = useWorker();
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!workerReady) return;

    async function poll() {
      try {
        const res = await send("get_gpu_info");
        if (res.status === "ok" && res.data) {
          setGpuInfo({
            gpu_name: (res.data.gpu_name as string) ?? "",
            vram_total: (res.data.vram_total as number) ?? 0,
            vram_used: (res.data.vram_used as number) ?? 0,
            gpu_util: (res.data.gpu_util as number) ?? 0,
            driver: (res.data.driver as string) ?? "",
          });
        }
      } catch {
        // GPU info unavailable
      }
    }

    poll();
    timerRef.current = setInterval(poll, intervalMs);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [workerReady, intervalMs, send, setGpuInfo]);
}

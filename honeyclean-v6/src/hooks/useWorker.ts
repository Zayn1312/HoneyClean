import { useCallback, useEffect, useRef } from "react";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import { useStore } from "../store/useStore";
import { v4 as uuid } from "uuid";

interface WorkerResponse {
  id: string;
  status?: string;
  event?: string;
  data?: Record<string, unknown>;
  error?: string;
}

type PendingResolve = (value: WorkerResponse) => void;

const pending = new Map<string, PendingResolve>();
let workerInitialized = false;
let workerInitPromise: Promise<void> | null = null;

export function useWorker() {
  const setWorkerReady = useStore((s) => s.setWorkerReady);
  const addToast = useStore((s) => s.addToast);
  const unlistenRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    let mounted = true;

    async function setup() {
      // Only spawn the worker once across all hook instances
      if (workerInitialized) return;
      if (workerInitPromise) {
        await workerInitPromise;
        if (mounted) setWorkerReady(true);
        return;
      }

      workerInitPromise = (async () => {
        try {
          // Listen for worker messages from Tauri backend
          const unlisten = await listen<WorkerResponse>("worker-message", (event) => {
            const msg = event.payload;
            if (msg.id && pending.has(msg.id) && (msg.status || !msg.event)) {
              const resolve = pending.get(msg.id)!;
              pending.delete(msg.id);
              resolve(msg);
            }
          });
          unlistenRef.current = unlisten;

          // Spawn the worker
          await invoke("spawn_worker");
          workerInitialized = true;
          if (mounted) {
            setWorkerReady(true);
          }
        } catch (e) {
          console.error("Worker setup failed:", e);
          workerInitPromise = null;
          if (mounted) {
            addToast(`Worker failed to start: ${e}`, "error");
          }
        }
      })();

      await workerInitPromise;
    }

    setup();

    return () => {
      mounted = false;
    };
  }, [setWorkerReady, addToast]);

  const send = useCallback(
    async (action: string, params: Record<string, unknown> = {}): Promise<WorkerResponse> => {
      const id = uuid();
      return new Promise((resolve, reject) => {
        pending.set(id, resolve);
        invoke("send_to_worker", { message: JSON.stringify({ action, id, params }) })
          .catch((err) => {
            pending.delete(id);
            reject(err);
          });

        // Timeout after 120s
        setTimeout(() => {
          if (pending.has(id)) {
            pending.delete(id);
            reject(new Error(`Worker timeout for action: ${action}`));
          }
        }, 120_000);
      });
    },
    []
  );

  const sendFire = useCallback(
    (action: string, params: Record<string, unknown> = {}) => {
      const id = uuid();
      invoke("send_to_worker", { message: JSON.stringify({ action, id, params }) }).catch(
        console.error
      );
    },
    []
  );

  return { send, sendFire };
}

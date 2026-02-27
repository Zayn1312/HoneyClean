import { create } from "zustand";

export type Page = "queue" | "editor" | "models" | "settings" | "about";
export type ProcessingState = "idle" | "processing" | "paused" | "stopped";
export type QualityPreset = "fast" | "balanced" | "quality" | "anime" | "portrait";

export interface QueueItem {
  id: string;
  path: string;
  name: string;
  size: number;
  type: "image" | "video";
  thumbnail?: string;
  outputPath?: string;
  status: "pending" | "processing" | "done" | "error" | "skipped" | "paused";
  elapsed?: number;
  selected: boolean;
}

export interface GPUInfo {
  gpu_name: string;
  vram_total: number;
  vram_used: number;
  gpu_util: number;
  driver: string;
}

export interface EditorState {
  beforeSrc: string | null;
  afterSrc: string | null;
  tool: "erase" | "restore";
  brushSize: number;
  feather: number;
  shadowType: "none" | "drop" | "float" | "contact";
  bgType: "transparent" | "white" | "color";
  bgColor: string;
  dividerPos: number;
  undoStack: string[];
  redoStack: string[];
}

export interface WorkerMessage {
  id: string;
  status?: string;
  event?: string;
  data?: Record<string, unknown>;
  error?: string;
}

interface AppState {
  // Navigation
  page: Page;
  setPage: (page: Page) => void;

  // Config
  config: Record<string, unknown>;
  setConfig: (config: Record<string, unknown>) => void;
  updateConfig: (partial: Record<string, unknown>) => void;

  // Queue
  queue: QueueItem[];
  addToQueue: (items: QueueItem[]) => void;
  removeFromQueue: (ids: string[]) => void;
  clearQueue: () => void;
  updateQueueItem: (id: string, update: Partial<QueueItem>) => void;
  toggleSelectItem: (id: string) => void;
  selectAll: () => void;
  deselectAll: () => void;
  sortQueue: (by: "name" | "size" | "folder") => void;

  // Processing
  processingState: ProcessingState;
  setProcessingState: (state: ProcessingState) => void;
  currentIndex: number;
  setCurrentIndex: (i: number) => void;
  progress: number;
  setProgress: (p: number) => void;
  currentFile: string;
  setCurrentFile: (f: string) => void;
  speed: number;
  setSpeed: (s: number) => void;
  eta: string;
  setEta: (e: string) => void;
  provider: string;
  setProvider: (p: string) => void;
  isGpu: boolean;
  setIsGpu: (g: boolean) => void;

  // Quality/Platform presets
  qualityPreset: QualityPreset;
  setQualityPreset: (p: QualityPreset) => void;
  platformPreset: string;
  setPlatformPreset: (p: string) => void;
  skipProcessed: boolean;
  setSkipProcessed: (s: boolean) => void;

  // GPU
  gpuInfo: GPUInfo;
  setGpuInfo: (info: GPUInfo) => void;

  // Editor
  editor: EditorState;
  setEditor: (update: Partial<EditorState>) => void;

  // Worker
  workerReady: boolean;
  setWorkerReady: (ready: boolean) => void;

  // Toast
  toasts: { id: string; message: string; type: "info" | "success" | "warning" | "error" }[];
  addToast: (message: string, type?: "info" | "success" | "warning" | "error") => void;
  removeToast: (id: string) => void;

  // Language
  language: "en" | "de" | "fr" | "es" | "zh";
  setLanguage: (lang: "en" | "de" | "fr" | "es" | "zh") => void;

  // EULA
  eulaAccepted: boolean;
  setEulaAccepted: (accepted: boolean) => void;
  showFirstRun: boolean;
  setShowFirstRun: (show: boolean) => void;
}

export const useStore = create<AppState>((set) => ({
  // Navigation
  page: "queue",
  setPage: (page) => set({ page }),

  // Config
  config: {},
  setConfig: (config) => set({ config }),
  updateConfig: (partial) => set((s) => ({ config: { ...s.config, ...partial } })),

  // Queue
  queue: [],
  addToQueue: (items) => set((s) => ({ queue: [...s.queue, ...items] })),
  removeFromQueue: (ids) => set((s) => ({
    queue: s.queue.filter((item) => !ids.includes(item.id)),
  })),
  clearQueue: () => set({ queue: [] }),
  updateQueueItem: (id, update) => set((s) => ({
    queue: s.queue.map((item) => (item.id === id ? { ...item, ...update } : item)),
  })),
  toggleSelectItem: (id) => set((s) => ({
    queue: s.queue.map((item) =>
      item.id === id ? { ...item, selected: !item.selected } : item
    ),
  })),
  selectAll: () => set((s) => ({
    queue: s.queue.map((item) => ({ ...item, selected: true })),
  })),
  deselectAll: () => set((s) => ({
    queue: s.queue.map((item) => ({ ...item, selected: false })),
  })),
  sortQueue: (by) => set((s) => {
    const sorted = [...s.queue];
    if (by === "name") sorted.sort((a, b) => a.name.localeCompare(b.name));
    else if (by === "size") sorted.sort((a, b) => a.size - b.size);
    else if (by === "folder") sorted.sort((a, b) => a.path.localeCompare(b.path));
    return { queue: sorted };
  }),

  // Processing
  processingState: "idle",
  setProcessingState: (state) => set({ processingState: state }),
  currentIndex: 0,
  setCurrentIndex: (i) => set({ currentIndex: i }),
  progress: 0,
  setProgress: (p) => set({ progress: p }),
  currentFile: "",
  setCurrentFile: (f) => set({ currentFile: f }),
  speed: 0,
  setSpeed: (s) => set({ speed: s }),
  eta: "",
  setEta: (e) => set({ eta: e }),
  provider: "CPU",
  setProvider: (p) => set({ provider: p }),
  isGpu: false,
  setIsGpu: (g) => set({ isGpu: g }),

  // Presets
  qualityPreset: "quality",
  setQualityPreset: (p) => set({ qualityPreset: p }),
  platformPreset: "None",
  setPlatformPreset: (p) => set({ platformPreset: p }),
  skipProcessed: false,
  setSkipProcessed: (s) => set({ skipProcessed: s }),

  // GPU
  gpuInfo: { gpu_name: "", vram_total: 0, vram_used: 0, gpu_util: 0, driver: "" },
  setGpuInfo: (info) => set({ gpuInfo: info }),

  // Editor
  editor: {
    beforeSrc: null,
    afterSrc: null,
    tool: "erase",
    brushSize: 20,
    feather: 0,
    shadowType: "none",
    bgType: "transparent",
    bgColor: "#ffffff",
    dividerPos: 50,
    undoStack: [],
    redoStack: [],
  },
  setEditor: (update) => set((s) => ({ editor: { ...s.editor, ...update } })),

  // Worker
  workerReady: false,
  setWorkerReady: (ready) => set({ workerReady: ready }),

  // Toast
  toasts: [],
  addToast: (message, type = "info") => {
    const id = crypto.randomUUID();
    set((s) => ({ toasts: [...s.toasts, { id, message, type }] }));
    setTimeout(() => {
      set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }));
    }, 3000);
  },
  removeToast: (id) => set((s) => ({
    toasts: s.toasts.filter((t) => t.id !== id),
  })),

  // Language
  language: "en",
  setLanguage: (lang) => set({ language: lang }),

  // EULA
  eulaAccepted: false,
  setEulaAccepted: (accepted) => set({ eulaAccepted: accepted }),
  showFirstRun: false,
  setShowFirstRun: (show) => set({ showFirstRun: show }),
}));

export interface QualityPreset {
  model: string;
  alpha_matting: boolean;
}

export interface PlatformPreset {
  bg: [number, number, number] | null;
  size: [number, number];
  padding_pct: number;
  format: "png" | "jpeg" | "webp";
}

export interface ModelInfo {
  id: string;
  name_key: string;
  desc_key: string;
}

export const QUALITY_PRESETS: Record<string, QualityPreset> = {
  fast: { model: "silueta", alpha_matting: false },
  balanced: { model: "isnet-general-use", alpha_matting: true },
  quality: { model: "birefnet-general", alpha_matting: true },
  anime: { model: "isnet-anime", alpha_matting: false },
  portrait: { model: "birefnet-portrait", alpha_matting: true },
};

export const PLATFORM_PRESETS: Record<string, PlatformPreset> = {
  Amazon: { bg: [255, 255, 255], size: [2000, 2000], padding_pct: 0.05, format: "jpeg" },
  Shopify: { bg: [255, 255, 255], size: [2048, 2048], padding_pct: 0.08, format: "png" },
  Etsy: { bg: null, size: [2700, 2025], padding_pct: 0.05, format: "png" },
  eBay: { bg: [255, 255, 255], size: [1600, 1600], padding_pct: 0.05, format: "jpeg" },
  Instagram: { bg: null, size: [1080, 1080], padding_pct: 0.10, format: "png" },
};

export const MODEL_INFO: Record<string, ModelInfo> = {
  auto: { id: "auto", name_key: "model_auto_name", desc_key: "model_auto_desc" },
  "birefnet-general": { id: "birefnet-general", name_key: "model_birefnet_general_name", desc_key: "model_birefnet_general_desc" },
  "birefnet-massive": { id: "birefnet-massive", name_key: "model_birefnet_massive_name", desc_key: "model_birefnet_massive_desc" },
  "birefnet-portrait": { id: "birefnet-portrait", name_key: "model_birefnet_portrait_name", desc_key: "model_birefnet_portrait_desc" },
  "birefnet-general-lite": { id: "birefnet-general-lite", name_key: "model_birefnet_lite_name", desc_key: "model_birefnet_lite_desc" },
  "birefnet-dis": { id: "birefnet-dis", name_key: "model_birefnet_dis_name", desc_key: "model_birefnet_dis_desc" },
  "birefnet-hrsod": { id: "birefnet-hrsod", name_key: "model_birefnet_hrsod_name", desc_key: "model_birefnet_hrsod_desc" },
  "birefnet-cod": { id: "birefnet-cod", name_key: "model_birefnet_cod_name", desc_key: "model_birefnet_cod_desc" },
  "isnet-general-use": { id: "isnet-general-use", name_key: "model_isnet_general_name", desc_key: "model_isnet_general_desc" },
  u2net: { id: "u2net", name_key: "model_u2net_name", desc_key: "model_u2net_desc" },
  u2netp: { id: "u2netp", name_key: "model_u2netp_name", desc_key: "model_u2netp_desc" },
  "isnet-anime": { id: "isnet-anime", name_key: "model_isnet_anime_name", desc_key: "model_isnet_anime_desc" },
  u2net_human_seg: { id: "u2net_human_seg", name_key: "model_u2net_human_name", desc_key: "model_u2net_human_desc" },
  u2net_cloth_seg: { id: "u2net_cloth_seg", name_key: "model_u2net_cloth_name", desc_key: "model_u2net_cloth_desc" },
  silueta: { id: "silueta", name_key: "model_silueta_name", desc_key: "model_silueta_desc" },
  "bria-rmbg": { id: "bria-rmbg", name_key: "model_bria_name", desc_key: "model_bria_desc" },
};

export const MODEL_ORDER = [
  "auto", "birefnet-general", "birefnet-massive", "birefnet-portrait",
  "birefnet-general-lite", "birefnet-dis", "birefnet-hrsod", "birefnet-cod",
  "isnet-general-use", "u2net", "u2netp",
  "isnet-anime", "u2net_human_seg", "u2net_cloth_seg",
  "silueta", "bria-rmbg",
];

export const MODEL_PRIORITY = [
  "birefnet-general", "birefnet-massive", "birefnet-portrait",
  "birefnet-general-lite", "isnet-general-use", "u2net",
  "isnet-anime", "u2net_human_seg", "silueta",
];

export const MODEL_SIZES: Record<string, number> = {
  u2net: 176_000_000, u2netp: 4_700_000,
  u2net_human_seg: 176_000_000, u2net_cloth_seg: 176_000_000,
  silueta: 43_000_000, "isnet-general-use": 174_000_000,
  "isnet-anime": 174_000_000, "birefnet-general": 973_000_000,
  "birefnet-general-lite": 410_000_000, "birefnet-portrait": 973_000_000,
  "birefnet-massive": 973_000_000, "birefnet-dis": 973_000_000,
  "birefnet-hrsod": 973_000_000, "birefnet-cod": 973_000_000,
  "bria-rmbg": 176_000_000,
};

export const VIDEO_EXTENSIONS = new Set([".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".m4v"]);
export const IMAGE_EXTENSIONS = new Set([".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"]);

export function isVideoFile(path: string): boolean {
  const ext = path.slice(path.lastIndexOf(".")).toLowerCase();
  return VIDEO_EXTENSIONS.has(ext);
}

export function formatSize(bytes: number): string {
  if (bytes >= 1_000_000_000) return `${(bytes / 1_000_000_000).toFixed(1)} GB`;
  if (bytes >= 1_000_000) return `${Math.round(bytes / 1_000_000)} MB`;
  return `${Math.round(bytes / 1_000)} KB`;
}

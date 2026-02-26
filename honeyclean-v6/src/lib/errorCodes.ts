export interface ErrorInfo {
  code: string;
  message: string;
  category: "dependency" | "file" | "model" | "config" | "ui" | "processing";
}

export const ERROR_REGISTRY: Record<string, ErrorInfo> = {
  "HC-001": { code: "HC-001", message: "rembg not installed", category: "dependency" },
  "HC-002": { code: "HC-002", message: "Pillow not installed", category: "dependency" },
  "HC-003": { code: "HC-003", message: "pymatting not installed", category: "dependency" },
  "HC-004": { code: "HC-004", message: "onnxruntime not installed", category: "dependency" },
  "HC-005": { code: "HC-005", message: "numpy not installed", category: "dependency" },
  "HC-010": { code: "HC-010", message: "File not found", category: "file" },
  "HC-011": { code: "HC-011", message: "Invalid file type", category: "file" },
  "HC-012": { code: "HC-012", message: "Path traversal detected", category: "file" },
  "HC-013": { code: "HC-013", message: "ZIP exceeds 500MB", category: "file" },
  "HC-014": { code: "HC-014", message: "ZIP bomb detected", category: "file" },
  "HC-015": { code: "HC-015", message: "ZIP path traversal", category: "file" },
  "HC-016": { code: "HC-016", message: "ZIP extraction failed", category: "file" },
  "HC-017": { code: "HC-017", message: "Invalid image data", category: "file" },
  "HC-020": { code: "HC-020", message: "Model load failed", category: "model" },
  "HC-021": { code: "HC-021", message: "Processing failed", category: "processing" },
  "HC-022": { code: "HC-022", message: "GPU unavailable, using CPU", category: "model" },
  "HC-023": { code: "HC-023", message: "Model not found", category: "model" },
  "HC-024": { code: "HC-024", message: "Cannot create output directory", category: "file" },
  "HC-030": { code: "HC-030", message: "Config corrupted", category: "config" },
  "HC-031": { code: "HC-031", message: "Config save failed", category: "config" },
  "HC-040": { code: "HC-040", message: "UI init failed", category: "ui" },
  "HC-041": { code: "HC-041", message: "Drag-and-drop unavailable", category: "ui" },
  "HC-042": { code: "HC-042", message: "Shadow generation failed", category: "processing" },
  "HC-043": { code: "HC-043", message: "Export preset failed", category: "processing" },
  "HC-044": { code: "HC-044", message: "Edge feather failed", category: "processing" },
  "HC-045": { code: "HC-045", message: "Color decontamination failed", category: "processing" },
};

export const WIKI_BASE = "https://github.com/Zayn1312/HoneyClean/wiki/Error-Codes";

export function getErrorMessage(code: string): string {
  return ERROR_REGISTRY[code]?.message ?? `Unknown error: ${code}`;
}

export function getErrorLink(code: string): string {
  return `${WIKI_BASE}#${code.toLowerCase()}`;
}

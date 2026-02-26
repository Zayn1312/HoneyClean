import { motion, AnimatePresence } from "framer-motion";
import { useStore } from "../store/useStore";
import { X, CheckCircle, AlertTriangle, AlertCircle, Info } from "lucide-react";

const icons = {
  info: Info,
  success: CheckCircle,
  warning: AlertTriangle,
  error: AlertCircle,
};

const colors = {
  info: "border-blue-500/40 bg-blue-950/60",
  success: "border-green-500/40 bg-green-950/60",
  warning: "border-yellow-500/40 bg-yellow-950/60",
  error: "border-red-500/40 bg-red-950/60",
};

const iconColors = {
  info: "text-blue-400",
  success: "text-green-400",
  warning: "text-yellow-400",
  error: "text-red-400",
};

export function ToastContainer() {
  const toasts = useStore((s) => s.toasts);
  const removeToast = useStore((s) => s.removeToast);

  return (
    <div className="fixed bottom-10 right-4 z-50 flex flex-col gap-2 pointer-events-none">
      <AnimatePresence mode="popLayout">
        {toasts.map((toast) => {
          const Icon = icons[toast.type];
          return (
            <motion.div
              key={toast.id}
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.95 }}
              transition={{ duration: 0.2 }}
              className={`pointer-events-auto flex items-center gap-3 px-4 py-3
                rounded-lg border backdrop-blur-md shadow-lg
                ${colors[toast.type]}`}
            >
              <Icon size={16} className={iconColors[toast.type]} />
              <span className="text-sm text-honey-100">{toast.message}</span>
              <button
                onClick={() => removeToast(toast.id)}
                className="ml-2 text-honey-600 hover:text-honey-300 transition-colors"
              >
                <X size={14} />
              </button>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}

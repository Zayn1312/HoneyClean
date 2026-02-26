import { motion } from "framer-motion";

interface ToggleProps {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
}

export function Toggle({ label, checked, onChange, disabled }: ToggleProps) {
  return (
    <label className={`flex items-center justify-between gap-3 cursor-pointer
      ${disabled ? "opacity-40 cursor-not-allowed" : ""}`}>
      <span className="text-sm text-honey-200">{label}</span>
      <button
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => !disabled && onChange(!checked)}
        className={`relative w-10 h-5.5 rounded-full transition-colors duration-200
          ${checked ? "bg-honey-500" : "bg-void-600"}`}
      >
        <motion.div
          layout
          transition={{ type: "spring", stiffness: 500, damping: 30 }}
          className="absolute top-0.75 w-4 h-4 rounded-full bg-white shadow-sm"
          style={{ left: checked ? "calc(100% - 1.25rem)" : "0.1875rem" }}
        />
      </button>
    </label>
  );
}

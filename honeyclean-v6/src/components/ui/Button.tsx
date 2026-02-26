import { motion } from "framer-motion";
import type { ButtonHTMLAttributes, ReactNode } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  icon?: ReactNode;
  children: ReactNode;
}

const variants = {
  primary: "bg-honey-500 hover:bg-honey-400 text-void-900 font-semibold",
  secondary: "bg-void-700 hover:bg-void-600 text-honey-100 border border-void-500",
  ghost: "bg-transparent hover:bg-void-700 text-honey-200",
  danger: "bg-red-600 hover:bg-red-500 text-white font-semibold",
};

const sizes = {
  sm: "px-3 py-1.5 text-xs gap-1.5",
  md: "px-4 py-2 text-sm gap-2",
  lg: "px-6 py-3 text-base gap-2.5",
};

export function Button({
  variant = "secondary",
  size = "md",
  icon,
  children,
  className = "",
  disabled,
  ...props
}: ButtonProps) {
  return (
    <motion.button
      whileHover={disabled ? undefined : { scale: 1.02 }}
      whileTap={disabled ? undefined : { scale: 0.97 }}
      className={`inline-flex items-center justify-center rounded-lg transition-colors
        ${variants[variant]} ${sizes[size]}
        ${disabled ? "opacity-40 cursor-not-allowed" : "cursor-pointer"}
        ${className}`}
      disabled={disabled}
      {...(props as Record<string, unknown>)}
    >
      {icon && <span className="shrink-0">{icon}</span>}
      {children}
    </motion.button>
  );
}

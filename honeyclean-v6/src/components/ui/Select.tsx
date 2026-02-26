interface SelectProps {
  label?: string;
  value: string;
  options: { value: string; label: string }[];
  onChange: (value: string) => void;
  className?: string;
}

export function Select({ label, value, options, onChange, className = "" }: SelectProps) {
  return (
    <div className={`flex flex-col gap-1 ${className}`}>
      {label && <label className="text-xs text-honey-300">{label}</label>}
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="bg-void-700 border border-void-500 text-honey-100 rounded-lg
          px-3 py-2 text-sm appearance-none cursor-pointer
          hover:border-honey-600 focus:border-honey-500 focus:outline-none
          transition-colors"
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}

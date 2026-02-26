interface SliderProps {
  label: string;
  value: number;
  min: number;
  max: number;
  step?: number;
  onChange: (value: number) => void;
  suffix?: string;
}

export function Slider({ label, value, min, max, step = 1, onChange, suffix = "" }: SliderProps) {
  return (
    <div className="flex flex-col gap-1">
      <div className="flex justify-between text-xs text-honey-300">
        <span>{label}</span>
        <span className="text-honey-100 font-mono">
          {value}{suffix}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full h-1.5 rounded-full appearance-none cursor-pointer
          bg-void-700 accent-honey-500
          [&::-webkit-slider-thumb]:w-3.5 [&::-webkit-slider-thumb]:h-3.5
          [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-honey-400
          [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:shadow-md"
      />
    </div>
  );
}

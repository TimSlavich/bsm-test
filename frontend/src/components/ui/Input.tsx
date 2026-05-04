import { forwardRef, type InputHTMLAttributes, type ReactNode } from "react";
import { cn } from "../../lib/cn";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  leftIcon?: ReactNode;
  rightSlot?: ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { leftIcon, rightSlot, className, ...rest },
  ref,
) {
  return (
    <span className={cn("input", className)}>
      {leftIcon && <span className="input__icon">{leftIcon}</span>}
      <input ref={ref} className="input__el" {...rest} />
      {rightSlot && <span className="input__right">{rightSlot}</span>}
    </span>
  );
});

interface FieldProps {
  label: ReactNode;
  hint?: ReactNode;
  htmlFor?: string;
  children: ReactNode;
  /** When truthy, paints the input border red. The actual user-facing
   * message lives in a separate modal — we deliberately don't render
   * anything underneath so the form stays compact. Pass an empty string
   * to flag invalid without text content; pass non-empty to also render
   * a small caption (kept for non-form contexts that want both). */
  error?: ReactNode;
}

export function Field({ label, hint, htmlFor, children, error }: FieldProps) {
  const invalid = error !== undefined && error !== null && error !== false;
  return (
    <label className="field" htmlFor={htmlFor} data-invalid={invalid ? "true" : undefined}>
      <span className="field__label">
        {label}
        {hint && !invalid && <span className="field__hint">{hint}</span>}
      </span>
      {children}
    </label>
  );
}

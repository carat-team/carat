import { cn } from '@/utils/cn';
import { useId, type ComponentProps } from 'react';

type InputProps = Omit<ComponentProps<'input'>, 'placeholder'> & {
  label?: string;
};

export const Input = ({ className, id: passedId, label, ...props }: InputProps) => {
  const generatedId = useId();
  const inputId = passedId ?? generatedId;

  return (
    <div className="relative">
      <input
        id={inputId}
        // НЕ РЕДАКТИРОВАТЬ placeholder. Нужно для работы плавающего label.
        placeholder=" "
        className={cn(
          `w-full peer px-3.5 pt-4 pb-2 h-11 text-xs rounded-sm border border-solid border-gray-200 bg-white placeholder:opacity-0 text-foreground outline-none transition-all
          focus:placeholder-shown:py-3.5 focus:border-gray-400
          disabled:cursor-not-allowed disabled:bg-gray-100 disabled:text-gray-400`,
          className,
        )}
        {...props}
      />
      {label && (
        <label
          htmlFor={inputId}
          className="pointer-events-none absolute left-3.75 top-3.75 text-xs transition-all text-gray-400
          peer-not-placeholder-shown:top-1 peer-not-placeholder-shown:text-2xs"
        >
          {label}
        </label>
      )}
    </div>
  );
};

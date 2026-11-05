import { cn } from '@/utils/cn';
import { useId, type ComponentProps } from 'react';

type InputProps = ComponentProps<'input'> & {
  label?: string;
};

export const Input = ({ className, id: passedId, label, ...props }: InputProps) => {
  const generatedId = useId();
  const inputId = passedId ?? generatedId;

  return (
    <div className="flex w-full flex-col gap-2">
      {label && (
        <label htmlFor={inputId} className="text-xs font-medium text-secondary">
          {label}
        </label>
      )}
      <input
        id={inputId}
        className={cn(
          `w-full h-12 px-3.5 text-sm rounded-md border border-solid border-[#dde4e9] bg-white text-foreground outline-none transition-all
          focus:border-gray-400
          disabled:cursor-not-allowed disabled:bg-gray-100 disabled:text-gray-400`,
          className,
        )}
        {...props}
      />
    </div>
  );
};

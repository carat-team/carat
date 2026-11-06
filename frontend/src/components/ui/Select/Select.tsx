import { cn } from '@/utils/cn';
import * as SelectPrimitive from '@radix-ui/react-select';
import { IconCheck, IconChevronDown, IconChevronUp } from '@tabler/icons-react';
import { useId, type ComponentProps } from 'react';

export type SelectOption = {
  value: string;
  label: string;
  disabled?: boolean;
};

type SelectProps = Omit<
  ComponentProps<typeof SelectPrimitive.Trigger>,
  'value' | 'defaultValue' | 'onChange' | 'children' | 'name'
> & {
  options: SelectOption[];
  label?: string;
  name?: string;
  required?: boolean;
  value?: string;
  defaultValue?: string;
  placeholder?: string;
  onChange?: (value: string) => void;
};

export const Select = ({
  className,
  id: passedId,
  label,
  name,
  required,
  options,
  value,
  defaultValue,
  placeholder = 'Выберите значение',
  onChange,
  disabled,
  ...props
}: SelectProps) => {
  const generatedId = useId();
  const selectId = passedId ?? generatedId;

  return (
    <div className="flex w-full flex-col gap-2">
      {label && (
        <label htmlFor={selectId} className="text-xs font-medium text-secondary">
          {label}
        </label>
      )}
      <SelectPrimitive.Root
        name={name}
        required={required}
        value={value}
        defaultValue={defaultValue}
        onValueChange={onChange}
        disabled={disabled}
      >
        <SelectPrimitive.Trigger
          {...props}
          id={selectId}
          className={cn(
            `flex w-full h-12 items-center justify-between gap-2 px-3.5 text-left text-sm rounded-md border border-solid border-[#dde4e9] bg-white text-foreground outline-none transition-all
            focus:border-gray-400 data-[state=open]:border-gray-400 data-[placeholder]:text-gray-400
            disabled:cursor-not-allowed disabled:bg-gray-100 disabled:text-gray-400`,
            className,
          )}
        >
          <span className="min-w-0 truncate">
            <SelectPrimitive.Value placeholder={placeholder} />
          </span>
          <SelectPrimitive.Icon asChild>
            <IconChevronDown className="shrink-0 text-gray-400" />
          </SelectPrimitive.Icon>
        </SelectPrimitive.Trigger>

        <SelectPrimitive.Portal>
          <SelectPrimitive.Content
            position="popper"
            align="start"
            sideOffset={4}
            className="z-50 max-h-(--radix-select-content-available-height) w-(--radix-select-trigger-width) overflow-hidden rounded-md border border-solid border-[#dde4e9] bg-white text-foreground shadow-md"
          >
            <SelectPrimitive.ScrollUpButton className="flex justify-center py-1 text-gray-400">
              <IconChevronUp />
            </SelectPrimitive.ScrollUpButton>
            <SelectPrimitive.Viewport className="max-h-60 p-1">
              {options.map((option) => (
                <SelectPrimitive.Item
                  key={option.value}
                  value={option.value}
                  disabled={option.disabled}
                  className="relative flex cursor-pointer items-center rounded-sm py-2 pl-3.5 pr-9 text-sm outline-none data-[highlighted]:bg-gray-100 data-[state=checked]:font-medium data-[disabled]:pointer-events-none data-[disabled]:opacity-40"
                >
                  <SelectPrimitive.ItemText>{option.label}</SelectPrimitive.ItemText>
                  <SelectPrimitive.ItemIndicator className="absolute right-3.5">
                    <IconCheck />
                  </SelectPrimitive.ItemIndicator>
                </SelectPrimitive.Item>
              ))}
            </SelectPrimitive.Viewport>
            <SelectPrimitive.ScrollDownButton className="flex justify-center py-1 text-gray-400">
              <IconChevronDown />
            </SelectPrimitive.ScrollDownButton>
          </SelectPrimitive.Content>
        </SelectPrimitive.Portal>
      </SelectPrimitive.Root>
    </div>
  );
};

import { cn } from '@/utils/cn';
import { IconChevronDown } from '@tabler/icons-react';
import { useEffect, useId, useRef, useState, type ComponentProps, type KeyboardEvent } from 'react';

export type SelectOption = {
  value: string;
  label: string;
  disabled?: boolean;
};

type SelectProps = Omit<
  ComponentProps<'button'>,
  'value' | 'defaultValue' | 'onChange' | 'children' | 'onClick' | 'onKeyDown' | 'onKeyUp' | 'type'
> & {
  options: SelectOption[];
  label?: string;
  /** Если передан, добавляется скрытый input — значение попадёт в нативную форму */
  name?: string;
  /** Controlled-режим */
  value?: string;
  /** Uncontrolled-режим */
  defaultValue?: string;
  onChange?: (value: string) => void;
};

export const Select = ({
  className,
  id: passedId,
  label,
  name,
  options,
  value,
  defaultValue = '',
  onChange,
  disabled,
  ...props
}: SelectProps) => {
  const generatedId = useId();
  const selectId = passedId ?? generatedId;
  const labelId = `${selectId}-label`;
  const listboxId = `${selectId}-listbox`;
  const optionIdPrefix = `${selectId}-option-`;

  const [innerValue, setInnerValue] = useState(defaultValue);
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const rootRef = useRef<HTMLDivElement>(null);

  const currentValue = value ?? innerValue;
  const selectedIndex = options.findIndex((option) => option.value === currentValue);
  const selectedOption = options[selectedIndex];
  const hasValue = Boolean(selectedOption);

  const findEnabledIndex = (from: number, step: 1 | -1) => {
    for (let i = from; i >= 0 && i < options.length; i += step) {
      if (!options[i].disabled) return i;
    }
    return -1;
  };

  const openList = () => {
    if (disabled) return;
    setActiveIndex(selectedIndex >= 0 ? selectedIndex : findEnabledIndex(0, 1));
    setIsOpen(true);
  };

  const closeList = () => setIsOpen(false);
  const toggleList = () => setIsOpen((prev) => !prev);

  const selectOption = (index: number) => {
    const option = options[index];
    if (!option || option.disabled) return;

    if (value === undefined) setInnerValue(option.value);
    onChange?.(option.value);
    closeList();
  };

  // Закрытие по клику вне компонента
  useEffect(() => {
    if (!isOpen) return;

    const handlePointerDown = (event: PointerEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setIsOpen(false);
    };

    document.addEventListener('pointerdown', handlePointerDown);
    return () => document.removeEventListener('pointerdown', handlePointerDown);
  }, [isOpen]);

  // Подскролл к активной опции при навигации с клавиатуры
  useEffect(() => {
    if (!isOpen || activeIndex < 0) return;
    document
      .getElementById(`${optionIdPrefix}${activeIndex}`)
      ?.scrollIntoView({ block: 'nearest' });
  }, [isOpen, activeIndex, optionIdPrefix]);

  const handleKeyDown = (event: KeyboardEvent<HTMLButtonElement>) => {
    if (disabled) return;

    if (!isOpen) {
      if (['ArrowDown', 'ArrowUp', 'Enter', ' '].includes(event.key)) {
        event.preventDefault();
        openList();
      }
      return;
    }

    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        setActiveIndex((prev) => {
          const next = findEnabledIndex(prev + 1, 1);
          return next === -1 ? prev : next;
        });
        break;
      case 'ArrowUp':
        event.preventDefault();
        setActiveIndex((prev) => {
          const next = findEnabledIndex(prev - 1, -1);
          return next === -1 ? prev : next;
        });
        break;
      case 'Home':
        event.preventDefault();
        setActiveIndex(findEnabledIndex(0, 1));
        break;
      case 'End':
        event.preventDefault();
        setActiveIndex(findEnabledIndex(options.length - 1, -1));
        break;
      case 'Enter':
      case ' ':
        event.preventDefault();
        selectOption(activeIndex);
        break;
      case 'Escape':
        event.preventDefault();
        closeList();
        break;
      case 'Tab':
        closeList();
        break;
    }
  };

  return (
    <div ref={rootRef} className="relative w-full">
      <button
        {...props}
        id={selectId}
        type="button"
        role="combobox"
        disabled={disabled}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-controls={isOpen ? listboxId : undefined}
        aria-activedescendant={
          isOpen && activeIndex >= 0 ? `${optionIdPrefix}${activeIndex}` : undefined
        }
        onClick={toggleList}
        onKeyDown={handleKeyDown}
        // Пробел в Firefox/Chrome вызывает click на keyup — гасим, чтобы не было двойного переключения
        onKeyUp={(event) => {
          if (event.key === ' ') event.preventDefault();
        }}
        className={cn(
          `flex items-center w-full h-11 pl-3.5 pr-9 pt-4 pb-2 text-left text-xs rounded-sm border border-solid border-gray-200 bg-white text-foreground outline-none transition-all
          focus:border-gray-400
          disabled:cursor-not-allowed disabled:bg-gray-100 disabled:text-gray-400`,
          isOpen && 'border-gray-400',
          className,
        )}
      >
        <span className="block truncate">{selectedOption?.label}</span>
      </button>

      <IconChevronDown
        className={cn(
          'pointer-events-none absolute right-3.5 top-1/2 size-3 -translate-y-1/2 text-gray-400 transition-transform',
          isOpen && 'rotate-180',
        )}
      />

      {label && (
        <label
          id={labelId}
          htmlFor={selectId}
          className={cn(
            'pointer-events-none absolute left-3.75 text-gray-400 transition-all',
            hasValue ? 'top-1 text-2xs' : 'top-3.75 text-xs',
          )}
        >
          {label}
        </label>
      )}

      {name && <input type="hidden" name={name} value={currentValue} />}

      {isOpen && (
        <ul
          id={listboxId}
          role="listbox"
          aria-labelledby={label ? labelId : undefined}
          // Не даём кнопке терять фокус при клике по опции
          onMouseDown={(event) => event.preventDefault()}
          className="absolute inset-x-0 top-full z-10 mt-1 max-h-60 overflow-auto rounded-sm border border-solid border-gray-200 bg-white py-1 shadow-md"
        >
          {options.map((option, index) => (
            <li
              key={option.value}
              id={`${optionIdPrefix}${index}`}
              role="option"
              aria-selected={index === selectedIndex}
              aria-disabled={option.disabled || undefined}
              onMouseEnter={() => !option.disabled && setActiveIndex(index)}
              onClick={() => selectOption(index)}
              className={cn(
                'cursor-pointer px-3.5 py-2 text-xs text-foreground',
                index === activeIndex && 'bg-gray-100',
                index === selectedIndex && 'font-medium',
                option.disabled && 'cursor-not-allowed opacity-40',
              )}
            >
              <span className="block truncate">{option.label}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

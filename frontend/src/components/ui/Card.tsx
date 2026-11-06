import { cn } from '@/utils/cn';
import type { ComponentPropsWithoutRef, ElementType } from 'react';

type CardProps<T extends ElementType> = {
  as?: T;
} & Omit<ComponentPropsWithoutRef<T>, 'as'>;

export const Card = <T extends ElementType = 'div'>({ className, as, ...props }: CardProps<T>) => {
  const Component: ElementType = as ?? 'div';

  return (
    <Component
      className={cn('rounded-lg border border-gray-200 bg-white p-5', className)}
      {...props}
    />
  );
};

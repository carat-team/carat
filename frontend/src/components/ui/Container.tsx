import { cn } from '@/utils/cn';
import type { ComponentPropsWithoutRef, ElementType } from 'react';

type ContainerProps<T extends ElementType> = {
  as?: T;
} & Omit<ComponentPropsWithoutRef<T>, 'as'>;

export const Container = <T extends ElementType = 'div'>({
  className,
  as,
  ...props
}: ContainerProps<T>) => {
  const Component: ElementType = as ?? 'div';

  return <Component className={cn('px-4 w-full max-w-7xl mx-auto', className)} {...props} />;
};

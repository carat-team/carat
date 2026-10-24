import { cn } from '@/utils/cn';
import { cva, type VariantProps } from 'class-variance-authority';
import type { ComponentProps } from 'react';

const buttonVariants = cva(
  `enabled:active:brightness-92 font-medium cursor-pointer text-xs uppercase flex gap-1.5 justify-center items-center rounded-sm transition-all
  disabled:cursor-not-allowed disabled:opacity-75 
  `,
  {
    variants: {
      variant: {
        primary: 'bg-primary',
        secondary: 'bg-secondary text-white',
        outline: 'border border-gray-200 border-solid bg-white',
      },
      size: {
        default: 'px-6 h-11',
        icon: 'size-11 p-0',
      },
    },
  },
);

export type ButtonVariantProps = VariantProps<typeof buttonVariants>;

type ButtonProps = ComponentProps<'button'> & ButtonVariantProps;

export const Button = ({
  className,
  variant = 'primary',
  size = 'default',
  ...props
}: ButtonProps) => {
  return <button className={cn(buttonVariants({ variant, size }), className)} {...props} />;
};

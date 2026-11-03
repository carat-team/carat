import { cn } from '@/utils/cn';
import { Link, useRoute } from 'wouter';
import { PRODUCT_STEPS } from '../constants';

export const ProductStepper = () => {
  const [, params] = useRoute('/:step');
  const currentId = params?.step;

  return (
    <nav className="flex gap-0.5 items-stretch">
      {PRODUCT_STEPS.map((step) => {
        const active = step.id === currentId;
        return (
          <Link
            key={step.id}
            href={`/${step.id}`}
            aria-current={active ? 'step' : undefined}
            className={cn(
              'flex-1 p-4 flex justify-center items-center text-center text-xs font-medium',
              active ? 'bg-primary' : 'bg-gray-200 text-gray-500',
            )}
          >
            {step.title}
          </Link>
        );
      })}
    </nav>
  );
};

import { useLocation } from 'wouter';

import { Button } from '@/components/ui';
import { NotFoundIllustration } from './components';

export const NotFoundPage = () => {
  const [, navigate] = useLocation();

  const handleBackClick = () => navigate('/');

  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-8 px-4 text-center">
      <NotFoundIllustration />

      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold sm:text-3xl">Страница не найдена</h1>
        <p className="text-secondary max-w-sm">
          Мы поискали, но ничего не нашли. Проверьте адрес: возможно, страница была удалена.
        </p>
      </div>

      <Button variant="secondary" onClick={handleBackClick}>
        На главную
      </Button>
    </div>
  );
};

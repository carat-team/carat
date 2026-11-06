import { Container } from '@/components/ui';

export const Header = () => {
  return (
    <header className="shrink-0 bg-secondary">
      <Container className="flex h-18 items-center">
        {/* Logo */}
        <div className="flex items-center gap-4">
          <span className="flex size-10 items-center justify-center rounded-lg bg-primary text-xl font-bold text-secondary">
            К
          </span>

          <span className="text-2xl font-bold text-white">КАРАТ</span>
        </div>

        {/* Section name */}
        <span className="ml-8 text-sm text-white">Каталог продукции</span>

        {/* Project information */}
        <span className="ml-auto text-sm text-gray-200">MVP · Парфюмерная продукция</span>
      </Container>
    </header>
  );
};

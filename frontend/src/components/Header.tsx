import { Container } from '@/components/ui';
import { IconCheck } from '@tabler/icons-react';
import { Link } from 'wouter';

export const Header = () => {
  return (
    <header className="bg-secondary mb-5">
      <Container className="flex items-center h-12">
        <Link href="/" className="flex items-center gap-3 text-primary text-xs">
          <span className="flex items-center justify-center size-6 rounded-sm bg-primary text-secondary">
            <IconCheck className="size-3.5!" />
          </span>
          Carat
        </Link>
      </Container>
    </header>
  );
};

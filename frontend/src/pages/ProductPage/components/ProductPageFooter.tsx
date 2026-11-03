import { Button, Container } from '@/components/ui';
import { IconArrowLeft, IconArrowRight } from '@tabler/icons-react';
import { Link } from 'wouter';

type ProductPageFooterProps = {
  prevHref?: string;
  nextHref?: string;
};

export const ProductPageFooter = ({ prevHref, nextHref }: ProductPageFooterProps) => {
  return (
    <footer>
      <Container className="flex gap-3">
        {prevHref && (
          <Link href={prevHref}>
            <Button size="icon" aria-label="Предыдущий шаг">
              <IconArrowLeft />
            </Button>
          </Link>
        )}
        {nextHref && (
          <Link href={nextHref}>
            <Button size="icon" aria-label="Следующий шаг">
              <IconArrowRight />
            </Button>
          </Link>
        )}
      </Container>
    </footer>
  );
};

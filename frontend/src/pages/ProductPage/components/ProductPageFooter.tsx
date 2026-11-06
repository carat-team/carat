import { Button, Container } from '@/components/ui';
import { IconArrowLeft, IconArrowRight } from '@tabler/icons-react';
import { useLocation } from 'wouter';

type ProductPageFooterProps = {
  prevHref?: string;
  prevLabel?: string;
  nextHref?: string;
  nextLabel?: string;
  saveHref?: string;
  saveLabel?: string;
};

export const ProductPageFooter = ({
  prevHref,
  prevLabel,
  nextHref,
  nextLabel,
  saveHref,
  saveLabel,
}: ProductPageFooterProps) => {
  const [, navigate] = useLocation();

  return (
    <footer className="mt-auto shrink-0">
      <Container className="flex flex-wrap gap-3">
        {prevHref && (
          <Button type="button" variant="outline" onClick={() => navigate(prevHref)}>
            <IconArrowLeft />
            {prevLabel}
          </Button>
        )}
        <div className="ml-auto flex flex-wrap gap-3">
          {saveHref && (
            <Button
              type="button"
              variant={nextHref ? 'outline' : 'primary'}
              onClick={() => navigate(saveHref)}
            >
              {saveLabel}
            </Button>
          )}
          {nextHref && (
            <Button type="button" onClick={() => navigate(nextHref)}>
              {nextLabel}
              <IconArrowRight />
            </Button>
          )}
        </div>
      </Container>
    </footer>
  );
};

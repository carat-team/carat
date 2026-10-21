import { Container } from '@/components/ui';
import { Redirect, Route, Switch, useParams, useRoute } from 'wouter';
import { ProductPageFooter, ProductStepper } from './components';
import { PRODUCT_STEPS } from './constants';

export const ProductPage = () => {
  const { code } = useParams<{ code: string }>();
  const [, params] = useRoute('/:step');

  const index = PRODUCT_STEPS.findIndex((s) => s.id === params?.step);
  const prev = index > 0 ? PRODUCT_STEPS[index - 1] : null;
  const next = index >= 0 && index < PRODUCT_STEPS.length - 1 ? PRODUCT_STEPS[index + 1] : null;

  const prevHref = prev ? `/${prev.id}` : '';
  const nextHref = next ? `/${next.id}` : '';

  return (
    <div className="flex flex-col flex-1 min-h-0 gap-4 pb-5">
      <Container className="flex flex-col gap-2">
        <h2 className="font-semibold text-sm">Код товара {code}</h2>
        <ProductStepper />
      </Container>

      <Switch>
        {PRODUCT_STEPS.map(({ id, component: Component }) => (
          <Route key={id} path={`/${id}`}>
            <main className="flex flex-col min-h-0">
              <Container className="flex-1 min-h-0 overflow-y-auto">
                <Component />
              </Container>
            </main>
          </Route>
        ))}

        {/* /product/:code и неизвестный шаг -> первый шаг */}
        <Route>
          <Redirect to={`/${PRODUCT_STEPS[0].id}`} replace />
        </Route>
      </Switch>

      <ProductPageFooter prevHref={prevHref} nextHref={nextHref} />
    </div>
  );
};

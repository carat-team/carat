import { Container } from '@/components/ui';
import type { FC } from 'react';
import { FormProvider } from 'react-hook-form';
import { Redirect, Route, Switch, useRoute } from 'wouter';
import { ProductPageFooter, ProductStepper } from './components';
import { PRODUCT_STEPS } from './constants';
import { useProductForm } from './form/useProductForm';

type ProductPageProps = {
  mode: 'create' | 'edit';
};

export const ProductPage: FC<ProductPageProps> = () => {
  const form = useProductForm();
  const [, params] = useRoute('/:step');

  const index = PRODUCT_STEPS.findIndex((s) => s.id === params?.step);
  const currentStep = PRODUCT_STEPS[index] ?? PRODUCT_STEPS[0];
  const isFirstStep = index === 0;
  const isLastStep = index === PRODUCT_STEPS.length - 1;
  const prevStep = index > 0 ? PRODUCT_STEPS[index - 1] : null;
  const nextStep = index >= 0 && index < PRODUCT_STEPS.length - 1 ? PRODUCT_STEPS[index + 1] : null;

  let prevHref = '';
  if (isFirstStep) {
    prevHref = '~/';
  } else if (prevStep) {
    prevHref = `/${prevStep.id}`;
  }
  const nextHref = nextStep ? `/${nextStep.id}` : '';

  return (
    <FormProvider {...form}>
      <div key={currentStep.id} className="flex-1 min-h-0 overflow-y-auto">
        <div className="flex min-h-full flex-col gap-4 pb-5">
          <Container className="flex shrink-0 flex-col pt-7 gap-7">
            <div className="flex flex-col gap-2">
              <h1 className="text-3xl font-semibold leading-tight">{currentStep.title}</h1>

              <p className="text-sm text-slate-500">{currentStep.subtitle}</p>
            </div>
            <ProductStepper />
          </Container>

          <Switch>
            {PRODUCT_STEPS.map(({ id, component: Component }) => (
              <Route key={id} path={`/${id}`}>
                <main>
                  <Container>
                    <Component />
                  </Container>
                </main>
              </Route>
            ))}

            {/* Redirect the base URL and unknown steps to the first step. */}
            <Route>
              <Redirect to={`/${PRODUCT_STEPS[0].id}`} replace />
            </Route>
          </Switch>

          <ProductPageFooter
            prevHref={prevHref}
            prevLabel={prevStep?.title ?? 'Каталог'}
            nextHref={nextHref}
            nextLabel={nextStep?.title}
            saveHref={index >= 0 ? '/saved' : ''}
            saveLabel={isLastStep ? 'Сохранить карточку' : 'Сохранить черновик'}
          />
        </div>
      </div>
    </FormProvider>
  );
};

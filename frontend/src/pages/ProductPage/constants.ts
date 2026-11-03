import { ProductInfoStep } from './steps/info';
import { ProductPhotosStep } from './steps/photo';
import { ProductRegistrationStep } from './steps/registration';

export const PRODUCT_STEPS = [
  {
    id: 'registration',
    title: 'Регистрация кода товара',
    component: ProductRegistrationStep,
  },
  {
    id: 'info',
    title: 'Сведения о товаре',
    component: ProductInfoStep,
  },
  {
    id: 'photos',
    title: 'Фото',
    component: ProductPhotosStep,
  },
] as const;

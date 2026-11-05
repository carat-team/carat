import { ProductInfoStep } from './steps/info';
import { ProductPhotosStep } from './steps/photo';
import { ProductRegistrationStep } from './steps/registration';

export const PRODUCT_STEPS = [
  {
    id: 'registration',
    title: 'Регистрация товара',
    subtitle: 'Первый этап, как в исходном макете: название, классификация и идентификация.',
    component: ProductRegistrationStep,
  },
  {
    id: 'info',
    title: 'Сведения о товаре',
    subtitle: 'Атрибуты сгруппированы по разделам исходной формы КМТ.',
    component: ProductInfoStep,
  },
  {
    id: 'photos',
    title: 'Фото',
    subtitle: 'Фотоконтент прикрепляется отдельно: файл, ракурс, упаковка.',
    component: ProductPhotosStep,
  },
] as const;

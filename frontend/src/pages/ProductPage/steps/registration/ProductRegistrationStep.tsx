import { Card, Input, Select, type SelectOption } from '@/components/ui';
import { Controller, useFormContext } from 'react-hook-form';
import type { ProductFormValues } from '../../form/types';

const TNVED_OPTIONS: SelectOption[] = [
  { value: '3303001000', label: '3303001000 - Духи' },
  { value: '3303009000', label: '3303009000 - Прочие' },
];

export const ProductRegistrationStep = () => {
  const { register, control } = useFormContext<ProductFormValues>();

  return (
    <Card className="flex flex-col gap-4">
      <h2 className="text-lg font-semibold uppercase">Регистрация кода товара</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-2">
        <Input label="Категория товара" value="Парфюмерия" disabled />
        <Input
          label="Полное наименование товара"
          placeholder="Наименование товара"
          {...register('fullName')}
        />
        <Input label="Группа ТН ВЭД" {...register('tnVedCode')} disabled />
        <Controller
          name="tnVedCode10"
          control={control}
          render={({ field }) => (
            <Select {...field} label="Код ТН ВЭД (10 знаков)" options={TNVED_OPTIONS} />
          )}
        />
        <Input
          label="Код товара (GTIN)"
          placeholder="01234567890123"
          {...register('gtin')}
          inputMode="numeric"
        />

        <Input
          label="Товарный знак (необязательно)"
          placeholder="Товарный знак"
          {...register('brand')}
        />
      </div>

      <span className="text-xs text-gray-400">
        GTIN - демонстрационный код, не генерируется как официальный идентификатор.
      </span>
    </Card>
  );
};

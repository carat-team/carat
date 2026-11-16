import { Card, Input, Select, type SelectOption } from '@/components/ui';
import { IconX } from '@tabler/icons-react';
import { Controller, useFormContext } from 'react-hook-form';
import type { ProductFormValues } from '../../form/types';

const PERFUMERY_TYPE_OPTIONS: SelectOption[] = [
  { value: 'Духи', label: 'Духи' },
  { value: 'Парфюмерная вода', label: 'Парфюмерная вода' },
  { value: 'Туалетная вода', label: 'Туалетная вода' },
];

const COUNTRY_OPTIONS: SelectOption[] = [
  { value: 'Россия', label: 'Россия · RU' },
  { value: 'Франция', label: 'Франция · FR' },
];

const VOLUME_UNIT_OPTIONS: SelectOption[] = [
  { value: 'мл', label: 'мл' },
  { value: 'л', label: 'л' },
];

const PACKAGE_TYPE_OPTIONS: SelectOption[] = [
  { value: 'Флакон', label: 'ФЛАКОН' },
  { value: 'Коробка', label: 'КОРОБКА' },
];

const PACKAGE_MATERIAL_OPTIONS: SelectOption[] = [
  { value: 'Стекло', label: 'СТЕКЛО' },
  { value: 'Пластик', label: 'ПЛАСТИК' },
];

const STANDARD_OPTIONS: SelectOption[] = [{ value: 'ТР ТС 009/2011', label: 'ТР ТС 009/2011' }];

const cardTitleClassName = 'text-base font-semibold uppercase text-[#374149]';

const fieldLabelClassName = 'text-xs font-medium text-secondary';

export const ProductInfoStep = () => {
  const { control } = useFormContext<ProductFormValues>();

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      {/* Идентификация товара */}
      <Card className="flex min-h-[280px] flex-col gap-4">
        <h2 className={cardTitleClassName}>Идентификация товара</h2>

        <Controller
          name="country"
          control={control}
          render={({ field }) => (
            <Select {...field} label="Страна производства" options={COUNTRY_OPTIONS} />
          )}
        />

        <div className="grid grid-cols-[minmax(0,1fr)_140px] gap-3">
          <div className="flex flex-col gap-2">
            <label htmlFor="volume-value" className={fieldLabelClassName}>
              Заявленный объём · значение
            </label>

            <Controller
              name="volume.value"
              control={control}
              render={({ field }) => (
                <Input
                  {...field}
                  id="volume-value"
                  type="number"
                  min={0}
                  step="any"
                  value={field.value ?? ''}
                  onChange={(event) => {
                    const value = event.target.value;
                    field.onChange(value === '' ? 0 : Number(value));
                  }}
                />
              )}
            />
          </div>

          <Controller
            name="volume.unit"
            control={control}
            render={({ field }) => (
              <Select {...field} label="Единица измерения" options={VOLUME_UNIT_OPTIONS} />
            )}
          />
        </div>
      </Card>

      {/* Потребительские свойства */}
      <Card className="flex min-h-[280px] flex-col gap-4">
        <h2 className={cardTitleClassName}>Потребительские свойства</h2>

        <Controller
          name="perfumeryType"
          control={control}
          render={({ field }) => (
            <Select {...field} label="Тип парфюмерии" options={PERFUMERY_TYPE_OPTIONS} />
          )}
        />

        <p className="text-xs leading-relaxed text-slate-400">
          Демо-варианты: духи, парфюмерная вода, туалетная вода и др.
        </p>
      </Card>

      {/* Информация об упаковке */}
      <Card className="flex min-h-[280px] flex-col gap-4">
        <h2 className={cardTitleClassName}>Информация об упаковке</h2>

        <Controller
          name="packageType"
          control={control}
          render={({ field }) => (
            <Select
              {...field}
              label="Тип упаковки · необязательно"
              options={PACKAGE_TYPE_OPTIONS}
            />
          )}
        />

        <Controller
          name="packMaterial"
          control={control}
          render={({ field }) => (
            <Select
              {...field}
              label="Материал упаковки · необязательно"
              options={PACKAGE_MATERIAL_OPTIONS}
            />
          )}
        />
      </Card>

      {/* Нормативно-сопроводительная документация */}
      <Card className="flex min-h-[280px] flex-col gap-4">
        <h2 className={cardTitleClassName}>Нормативно-сопроводительная документация</h2>

        <Controller
          name="standardNumber"
          control={control}
          render={({ field }) => {
            const selectedStandards = field.value ?? [];

            return (
              <>
                <Select
                  label="Номер технического регламента · необязательно"
                  placeholder="Выбрать регламент"
                  options={STANDARD_OPTIONS}
                  value=""
                  onChange={(value) => {
                    if (!selectedStandards.includes(value)) {
                      field.onChange([...selectedStandards, value]);
                    }
                  }}
                />

                {selectedStandards.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {selectedStandards.map((standard) => (
                      <span
                        key={standard}
                        className="inline-flex items-center gap-2 rounded-full bg-[#eef2f4] px-3 py-1.5 text-xs text-[#46515a]"
                      >
                        {standard}

                        <button
                          type="button"
                          aria-label={`Удалить ${standard}`}
                          onClick={() =>
                            field.onChange(selectedStandards.filter((item) => item !== standard))
                          }
                          className="cursor-pointer text-slate-500 transition-colors hover:text-red-500"
                        >
                          <IconX size={13} />
                        </button>
                      </span>
                    ))}
                  </div>
                )}

                <p className="text-xs leading-relaxed text-slate-400">
                  Можно указать несколько регламентов. Поле необязательное.
                </p>
              </>
            );
          }}
        />
      </Card>
    </div>
  );
};

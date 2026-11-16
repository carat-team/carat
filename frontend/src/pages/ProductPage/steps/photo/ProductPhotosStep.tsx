import { Button, Card, Select, type SelectOption } from '@/components/ui';
import { IconBackspace, IconPlus } from '@tabler/icons-react';
import { Controller, useFieldArray, useFormContext } from 'react-hook-form';
import type { ProductFormValues } from '../../form/types';
import { PhotoFileField } from './PhotoFileField';

const PERSPECTIVE_OPTIONS: SelectOption[] = [
  { value: 'front', label: 'Вид спереди' },
  { value: 'left', label: 'Вид слева' },
  { value: 'right', label: 'Вид справа' },
  { value: 'back', label: 'Вид сзади' },
];

export const ProductPhotosStep = () => {
  const { control, watch } = useFormContext<ProductFormValues>();
  const { fields, append, remove } = useFieldArray({ control, name: 'photos' });

  const gtin = watch('gtin');
  const packageOptions: SelectOption[] = [
    {
      value: 'consumer',
      label: gtin ? `Потребительская упаковка (${gtin})` : 'Потребительская упаковка',
    },
  ];

  const addPhoto = () => append({ file: null, perspective: '', packageId: 'consumer' });

  return (
    <Card className="flex flex-col gap-4">
      <h2 className="text-lg font-semibold uppercase">Фотоконтент</h2>

      {fields.length === 0 && (
        <p className="text-sm text-slate-500">
          Фото пока не добавлены. Фотографии необязательны, но помогают проверке карточки.
        </p>
      )}

      {fields.map((field, index) => (
        <div
          key={field.id}
          className="grid grid-cols-1 items-end gap-3 md:grid-cols-[1fr_2fr_1.5fr_auto]"
        >
          <Controller
            name={`photos.${index}.perspective`}
            control={control}
            render={({ field }) => (
              <Select {...field} label="Ракурс" options={PERSPECTIVE_OPTIONS} />
            )}
          />
          <Controller
            name={`photos.${index}.packageId`}
            control={control}
            render={({ field }) => <Select {...field} label="Упаковка" options={packageOptions} />}
          />
          <Controller
            name={`photos.${index}.file`}
            control={control}
            render={({ field }) => <PhotoFileField file={field.value} onChange={field.onChange} />}
          />
          <Button
            type="button"
            variant="outline"
            size="icon"
            aria-label="Удалить фото"
            onClick={() => remove(index)}
          >
            <IconBackspace />
          </Button>
        </div>
      ))}

      <button
        type="button"
        className="flex w-fit cursor-pointer items-center gap-1.5 text-sm text-action"
        onClick={addPhoto}
      >
        <IconPlus />
        Добавить
      </button>
    </Card>
  );
};

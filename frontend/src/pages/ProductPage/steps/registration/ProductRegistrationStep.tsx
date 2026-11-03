import { Button, Input, Select, type SelectOption } from '@/components/ui';
import type { Product } from '@/types';
import { useState } from 'react';
import { Link } from 'wouter';

type RegistrationData = Pick<Product, 'category' | 'tnVedCode' | 'okpd2' | 'fullName' | 'brand'>;

// TODO: заменить на данные с бэкенда, когда появится API товаров
const MOCK_DATA: RegistrationData = {
  category: 'Духи',
  tnVedCode: '3303',
  okpd2: '20.42.11.110',
  fullName: 'Шины Моск Политех',
  brand: 'шиккомпот',
};

const TNVED_OPTIONS: SelectOption[] = [{ value: '3303', label: '3303 Духи и туалетная вода' }];

const OKPD2_OPTIONS: SelectOption[] = [{ value: '20.42.11.110', label: '20.42.11.110 Духи' }];

export const ProductRegistrationStep = () => {
  const [data, setData] = useState<RegistrationData>(MOCK_DATA);
  const [isEditing, setIsEditing] = useState(false);

  const update = (field: keyof RegistrationData, value: string) => {
    setData((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className="flex flex-col gap-8">
      <div className="flex gap-3">
        {isEditing ? (
          <Button onClick={() => setIsEditing(false)}>Сохранить</Button>
        ) : (
          <Button onClick={() => setIsEditing(true)}>Редактировать</Button>
        )}
        <Link href="~/">
          <Button variant="outline">Закрыть</Button>
        </Link>
      </div>

      <div className="grid grid-cols-2 gap-x-12 gap-y-2">
        <div />
        <h3 className="text-xs font-semibold uppercase">Регистрация кода товара</h3>

        <div className="flex flex-col gap-2">
          <Input label="Категория товара" value={data.category} disabled />
          <Select
            label="Код группы ТН ВЭД ЕАЭС"
            options={TNVED_OPTIONS}
            value={data.tnVedCode}
            onChange={(value) => update('tnVedCode', value)}
            disabled={!isEditing}
          />
          <Select
            label="Код ОКПД2"
            options={OKPD2_OPTIONS}
            value={data.okpd2}
            onChange={(value) => update('okpd2', value)}
            disabled={!isEditing}
          />
        </div>

        <div className="flex flex-col gap-2">
          <Input
            label="Полное наименование товара"
            value={data.fullName}
            onChange={(e) => update('fullName', e.target.value)}
            disabled={!isEditing}
          />
          <Input
            label="Товарный знак"
            value={data.brand ?? ''}
            onChange={(e) => update('brand', e.target.value)}
            disabled={!isEditing}
          />
          <Select
            label="Группа ТНВЭД"
            options={TNVED_OPTIONS}
            value={data.tnVedCode}
            onChange={(value) => update('tnVedCode', value)}
            disabled={!isEditing}
          />
        </div>
      </div>
    </div>
  );
};

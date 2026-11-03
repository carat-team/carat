import { Button, Container } from '@/components/ui';
import { IconArrowRight, IconPlus } from '@tabler/icons-react';
import { useState } from 'react';

type Product = {
  id: string;
  name: string;
  group: string;
  brand: string;
  status: string;
};

const initialProducts: Product[] = [
  {
    id: '1',
    name: 'Парфюмерная вода «Lumen», 50 мл',
    group: 'Парфюмерия',
    brand: 'Lumen',
    status: 'Черновик',
  },
  {
    id: '2',
    name: 'Туалетная вода «Atlas», 100 мл',
    group: 'Парфюмерия',
    brand: 'Atlas',
    status: 'Черновик',
  },
];

export const ProductListPage = () => {
  const [products, setProducts] = useState(initialProducts);

  // Временное добавление тестового товара
  const handleAddProduct = () => {
    const newProduct: Product = {
      id: String(Date.now()),
      name: 'Новый товар',
      group: 'Парфюмерия',
      brand: '—',
      status: 'Черновик',
    };

    setProducts((current) => [...current, newProduct]);
  };

  // Временная обработка открытия карточки
  const handleOpenProduct = (product: Product) => {
    window.alert(`Выбрана карточка: ${product.name}`);
  };

  return (
    <main className="flex-1 min-h-0 overflow-y-auto bg-[#f4f7f9]">
      <Container className="max-w-[1440px] px-4 py-7 md:py-8">
        {/* Хлебные крошки */}
        <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
          КАТАЛОГ / MVP
        </div>

        {/* Заголовок и кнопка добавления */}
        <div className="mt-4 flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-3xl font-semibold leading-tight text-[#303a40]">Товары</h1>

            <p className="mt-2 text-sm text-slate-500">
              Создание и редактирование карточек парфюмерной продукции. Данные демонстрационные.
            </p>
          </div>

          <Button
            onClick={handleAddProduct}
            className="h-[52px] w-full rounded-md text-sm font-semibold normal-case md:w-[274px]"
          >
            <IconPlus size={18} />
            Добавить товар
          </Button>
        </div>

        {/* Карточка товаров */}
        <section className="mt-14 min-h-[440px] rounded-lg border border-[#dce3e8] bg-white p-5 md:p-6">
          {/* Заголовок карточки */}
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-[#303a40]">Карточки товаров</h2>

            <span className="text-xs text-slate-500">Всего: {products.length}</span>
          </div>

          {/* Таблица */}
          <div className="mt-8 overflow-x-auto">
            <table className="w-full min-w-[760px] border-separate border-spacing-0">
              <thead>
                <tr className="bg-[#eef2f4] text-[11px] font-semibold text-slate-500">
                  <th className="rounded-l-md px-4 py-4 text-left">НАИМЕНОВАНИЕ</th>

                  <th className="px-4 py-4 text-left">ГРУППА</th>

                  <th className="px-4 py-4 text-left">БРЕНД</th>

                  <th className="px-4 py-4 text-center">СТАТУС</th>

                  <th className="rounded-r-md px-4 py-4 text-center">ДЕЙСТВИЕ</th>
                </tr>
              </thead>

              <tbody>
                {products.map((product) => (
                  <tr key={product.id}>
                    <td className="border-b border-[#e3e9ed] px-4 py-6 text-sm font-medium text-[#374149]">
                      {product.name}
                    </td>

                    <td className="border-b border-[#e3e9ed] px-4 py-6 text-sm text-[#374149]">
                      {product.group}
                    </td>

                    <td className="border-b border-[#e3e9ed] px-4 py-6 text-sm text-[#374149]">
                      {product.brand}
                    </td>

                    <td className="border-b border-[#e3e9ed] px-4 py-6 text-center">
                      <span className="inline-flex min-w-[110px] justify-center rounded-full bg-[#fbfbe8] px-4 py-2 text-xs font-medium text-[#374149]">
                        {product.status}
                      </span>
                    </td>

                    <td className="border-b border-[#e3e9ed] px-4 py-6 text-center">
                      <Button
                        variant="outline"
                        onClick={() => handleOpenProduct(product)}
                        className="mx-auto h-[46px] min-w-[147px] rounded-md text-sm normal-case"
                      >
                        Открыть
                        <IconArrowRight size={16} />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </Container>
    </main>
  );
};

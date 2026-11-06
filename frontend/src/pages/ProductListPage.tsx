import { Button, Card, Container } from '@/components/ui';
import { IconArrowRight, IconPlus } from '@tabler/icons-react';
import { useLocation } from 'wouter';

type Product = {
  id: string;
  name: string;
  group: string;
  brand: string;
  status: string;
};

const products: Product[] = [
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
  const [, navigate] = useLocation();

  const handleAddProduct = () => {
    navigate('/product/new/registration');
  };

  const handleOpenProduct = (product: Product) => {
    navigate(`/product/${product.id}/registration`);
  };

  return (
    <main className="flex-1 min-h-0 overflow-y-auto">
      <Container className="py-7">
        <div className="mb-14 flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
          <div className="flex flex-col gap-2">
            <h1 className="text-3xl font-semibold leading-tight">Товары</h1>

            <p className="text-sm text-slate-500">
              Создание и редактирование карточек парфюмерной продукции. Данные демонстрационные.
            </p>
          </div>

          <Button onClick={handleAddProduct} className="font-semibold">
            <IconPlus />
            Добавить товар
          </Button>
        </div>

        <Card as="section">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold uppercase">Карточки товаров</h2>

            <span className="text-xs text-slate-500">Всего: {products.length}</span>
          </div>

          <div className="mt-8 overflow-x-auto">
            <table className="w-full min-w-[760px] border-separate border-spacing-0">
              <thead>
                <tr className="bg-slate-100 text-xs font-semibold text-slate-500 *:p-4">
                  <th className="rounded-l-md text-left">НАИМЕНОВАНИЕ</th>

                  <th className="text-left">ГРУППА</th>

                  <th className="text-left">БРЕНД</th>

                  <th className="text-center">СТАТУС</th>

                  <th className="rounded-r-md text-center">ДЕЙСТВИЕ</th>
                </tr>
              </thead>

              <tbody>
                {products.map((product) => (
                  <tr key={product.id} className="*:border-b *:border-gray-200 *:px-4 *:py-6">
                    <td className="text-sm font-medium">{product.name}</td>

                    <td className="text-sm">{product.group}</td>

                    <td className="text-sm">{product.brand}</td>

                    <td>
                      {/* TODO: Extract a reusable status badge. */}
                      <div className="flex mx-auto w-[110px] justify-center rounded-full bg-yellow-100 px-4 py-2 text-xs font-medium">
                        {product.status}
                      </div>
                    </td>

                    <td>
                      <Button
                        variant="outline"
                        size="small"
                        onClick={() => handleOpenProduct(product)}
                        className="mx-auto"
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
        </Card>
      </Container>
    </main>
  );
};

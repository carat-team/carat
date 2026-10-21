import { Button, Container, Input, Select } from '@/components/ui';
import { IconBackspace, IconChevronLeft, IconInfoCircle, IconUpload } from '@tabler/icons-react';
import { useState } from 'react';

// TODO: сверстать реальную страницу

export const ProductListPage = () => {
  const [a, b] = useState<string>();

  return (
    <div className="flex-1 min-h-0 flex flex-col gap-2">
      <Container className="flex flex-col gap-2">
        <h1>Компоненты и разные вариации:</h1>

        <div className="flex gap-2 flex-wrap mb-6">
          <Button>Добавить</Button>
          <Button variant={'secondary'}>Импорт</Button>
          <Button variant={'outline'}>Экспорт</Button>
          <Button disabled variant={'outline'}>
            Выключенная кнопка
          </Button>
          <Button disabled variant={'secondary'}>
            Выключенная кнопка
          </Button>
          <Button disabled variant={'primary'}>
            Выключенная кнопка
          </Button>
          <Button aria-label="Назад" size={'icon'}>
            <IconChevronLeft />
          </Button>
          <Button aria-label="Информация" variant={'secondary'} size={'icon'}>
            <IconInfoCircle />
          </Button>
          <Button aria-label="Стереть" variant={'outline'} size={'icon'}>
            <IconBackspace />
          </Button>
          <Button variant={'outline'}>
            <IconUpload /> Загрузить файл
          </Button>
        </div>
      </Container>

      <div className="min-h-0 flex flex-col">
        <Container className="flex-1 min-h-0 overflow-y-auto">
          <div className="flex flex-col gap-2 w-full">
            <Input label="Заявленный объем" />
            <Input disabled label="Страна производства" value="Россия матушка" />
            <Select
              label="Город"
              name="city"
              options={[
                { value: 'msk', label: 'Москва' },
                { value: 'spb', label: 'Санкт-Петербург' },
                { value: 'kzn', label: 'Казань', disabled: true },
              ]}
              value={a}
              onChange={b}
            />
            <Select
              disabled
              label="Город"
              name="city"
              options={[
                { value: 'msk', label: 'Москва' },
                { value: 'spb', label: 'Санкт-Петербург' },
                { value: 'kzn', label: 'Казань', disabled: true },
              ]}
              value={'kzn'}
            />
          </div>

          <p className="text-2xl">
            Контент для скролла: Следует отметить, что консультация с широким активом позволяет
            выполнять важные задания по разработке новых предложений. Не вызывает сомнений, что
            управление и развитие структуры представляет собой интересный эксперимент поэтапного и
            последовательного развития общества. Следует отметить, что реализация намеченных
            плановых заданий способствует повышению качества существующий финансовых и
            административных условий. Равным образом высокотехнологичная концепция общественной
            системы напрямую зависит от соответствующих условий активизации. Для современного мира
            выбранный нами инновационный путь обеспечивает широкому кругу специалистов прогресса
            профессионального общества. Значимость этих проблем настолько очевидна, что постоянный
            количественный рост и сфера нашей активности создаёт предпосылки качественно новых шагов
            для новых предложений. Повседневная практика показывает, что реализация намеченных
            плановых заданий влечёт за собой интересный процесс внедрения модернизации поставленных
            обществом и правительством задач. Следует отметить, что социально-экономическое развитие
            играет важную роль в формировании прогресса профессионального общества. Прежде всего
            выбранный нами инновационный путь позволяет оценить значение прогресса профессионального
            общества. Разнообразный и богатый опыт выбранный нами инновационный путь представляет
            собой интересный эксперимент направлений прогрессивного развития. рыба10
          </p>
        </Container>
      </div>

      <Container as="footer" className="py-5">
        А это футер. Тут будет пагинация.
      </Container>
    </div>
  );
};

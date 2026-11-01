# Как добавить проверку

Проверка - это класс в `algorithms/`, который получает карточку товара и возвращает один результат. Бэкенд сам
запускает все зарегистрированные проверки и отдаёт результаты фронтенду, поэтому в `backend/` для новой проверки
ничего менять не нужно.

Ниже весь путь на примере требования R4 из [requirements.md](requirements.md): значение бренда «Без товарного знака»
недопустимо.

## 1. Выберите требование

Каждая проверка закрывает требование из [requirements.md](requirements.md) (R1-R8) или задачу команды из того же
файла. Номер требования и ссылку на задачу в Taiga укажите в описании pull request.

Если проверку можно сделать правилами (сравнение строк, регулярное выражение, справочник), делайте правилами. Модель
нужна, только когда правил не хватает; обучение модели живёт в `model/`, а в `algorithms/` попадает только запуск
готовой модели.

## 2. Создайте пакет

Одна проверка - один подпакет в нужной области:

| Область | Для чего |
|---|---|
| `text/` | наименование и текстовые атрибуты (бренд, объём, тип парфюмерии) |
| `identifiers/` | GTIN, коды ТН ВЭД и другие идентификаторы |
| `vision/` | фото: штрихкод, текст этикетки, качество, фон |

```text
algorithms/src/carat_algorithms/text/brand_value/
  __init__.py      from carat_algorithms.text.brand_value.check import BrandValueCheck
  check.py         сама проверка
```

## 3. Напишите проверку

```python
from carat_algorithms.core import CheckResult, CheckStatus, ProductCard


class BrandValueCheck:
    """The brand value "Без товарного знака" is not allowed."""

    check_id = "brand_value"
    algorithm_version = 1

    def run(self, card: ProductCard) -> CheckResult:
        if card.brand is None:
            return self._result(CheckStatus.NOT_CHECKED, "BRAND_VALUE_MISSING", "Бренд не указан")
        if card.brand.strip().lower() == "без товарного знака":
            return self._result(CheckStatus.WARNING, "BRAND_VALUE_FORBIDDEN", 'Бренд "Без товарного знака" недопустим')
        return self._result(CheckStatus.PASS, "BRAND_VALUE_OK", "Бренд указан")

    def _result(self, status: CheckStatus, reason_code: str, explanation: str) -> CheckResult:
        return CheckResult(
            check_id=self.check_id,
            status=status,
            reason_code=reason_code,
            explanation=explanation,
            field_refs=("brand",),
            algorithm_version=self.algorithm_version,
        )
```

Что важно:

- `check_id` - постоянное имя в snake_case. На него ссылаются фронтенд и сохранённые результаты, не переименовывайте.
- `reason_code` - `UPPER_SNAKE_CASE` с префиксом проверки (`BRAND_VALUE_FORBIDDEN`). Фронтенд различает ответы по
  нему, а не по тексту.
- `explanation` - одно предложение на русском, лучше с конкретными значениями: «Объём в названии 50 мл, в атрибуте
  100 мл».
- `field_refs` - поля карточки, на которых основан вывод, в именах API (`fullName`, `volume`). Фронтенд подсвечивает
  эти поля.
- `algorithm_version` - целое число. Увеличивайте на 1 при любом изменении, которое может дать другой результат на
  той же карточке: новое правило, порог, модель.

Поля карточки (`ProductCard` в `core/card.py`) называются как в [api.md](api.md), только в snake_case:
`full_name`, `brand`, `volume`, `photos` и т. д.

## 4. Выберите статус

| Статус | Когда |
|---|---|
| `PASS` | правило выполнено |
| `WARNING` | найдена вероятная ошибка |
| `REVIEW` | правило не может решить, нужен человек |
| `NOT_CHECKED` | не хватает данных: нет поля, нет фото |
| `ERROR` | проверка упала; ставит только бэкенд, проверка его не возвращает |

- Поле `None` - его нет в карточке, это `NOT_CHECKED`. Пустая строка - это значение, которое ввёл продавец, и правило
  оценивает её как обычный ввод.
- Если не уверены, возвращайте `REVIEW`. Ложные `WARNING` приучают пользователей игнорировать предупреждения.
- Проверка не бросает исключения на плохих данных. Если она всё же упадёт, бэкенд запишет `ERROR` с кодом
  `CHECK_CRASHED`, и остальные проверки отработают.
- Новые статусы, свои шкалы и оценки от 0 до 1 не добавляйте.

## 5. Зарегистрируйте проверку

Добавьте класс в `get_checks()` в `algorithms/src/carat_algorithms/core/registry.py`. Импорт остаётся внутри
функции:

```python
def get_checks() -> list[Check]:
    from carat_algorithms.identifiers.gtin import GtinFormatCheck
    from carat_algorithms.text.brand_value import BrandValueCheck
    from carat_algorithms.vision.barcode import BarcodeOnPhotoCheck

    return [GtinFormatCheck(), BarcodeOnPhotoCheck(), BrandValueCheck()]
```

Незарегистрированная проверка не запускается.

## 6. Напишите тесты

Тесты лежат в `algorithms/tests/` по той же структуре, что и код: `tests/text/brand_value/test_check.py`.

```python
import pytest

from carat_algorithms.core import CheckStatus, ProductCard
from carat_algorithms.text.brand_value import BrandValueCheck


@pytest.mark.parametrize(
    ("brand", "status"),
    [
        pytest.param(None, CheckStatus.NOT_CHECKED, id="missing"),
        pytest.param("Без товарного знака", CheckStatus.WARNING, id="forbidden"),
        pytest.param("  без ТОВАРНОГО знака ", CheckStatus.WARNING, id="forbidden_case_and_spaces"),
        pytest.param("Chanel", CheckStatus.PASS, id="real_brand"),
    ],
)
def test_brand_value(brand: str | None, status: CheckStatus) -> None:
    assert BrandValueCheck().run(ProductCard(brand=brand)).status == status
```

- Минимум один случай `NOT_CHECKED` и один случай с ошибкой в карточке.
- Реальные ошибки из каталога ЧЗ добавляйте отдельными именованными случаями.
- Картинки для тестов до 100 КБ или генерируются в самом тесте.

## 7. Проверьте и откройте PR

```sh
just algorithms check
```

Команда проверяет lock-файл, запускает ruff, pyright и pytest. Потом откройте pull request в `dev`: в описании номер
требования, ссылка на задачу в Taiga и пара примеров карточек с результатами.

## Если нужна модель или тяжёлая библиотека

- Зависимость добавляется в extra: `uv add --optional vision <пакет>` для работы с изображениями, `ml` для моделей.
  Перед добавлением чего-то с torch спросите команду.
- Тяжёлые библиотеки импортируются внутри функций, не в начале модуля и не в `__init__.py`.
- Веса не коммитятся. Код модели получает каталог `weights/` и читает свой подкаталог (`weights/<модель>/`), а
  источник, имя файла и контрольную сумму нужно записать в таблицу весов в
  [algorithms/README.md](../algorithms/README.md#model-weights).
- Модель загружается один раз и лениво, при первом вызове. Название модели, предобработка и порог входят в
  `algorithm_version`.

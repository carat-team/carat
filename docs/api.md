# REST API бэкенда

Контракт между фронтендом и бэкендом. Источник: согласованный MVP (`CARAT_MVP.xlsx`, листы 01-05). Изменения
согласуются с фронтендом.

## Карточка товара

Категория одна: «Парфюмерия». Поля карточки передаются внутри объекта `attributes`.

| Поле | Тип | Обязательно в форме | Проверка формата на бэкенде |
|---|---|---|---|
| `fullName` | string | да | до 250 символов |
| `tnVedCode` | string | авто | при создании подставляется `3303` |
| `tnVedCode10` | string | да | ровно 10 цифр (`3303001000`, `3303009000`) |
| `gtin` | string | да | строка; корректность кода проверяет `gtin_format` |
| `brand` | string | нет | - |
| `country` | string[] | да | коды ISO alpha-2 (`RU`, `FR`, `IT`) |
| `perfumeryType` | string | да | - (в форме один из 8 типов) |
| `volume` | `{ "value": number, "unit": string }` | да | `value` > 0, `unit`: `л`, `мл` или `г` |
| `packageType` | string | нет | - |
| `packMaterial` | string | нет | - |
| `standardNumber` | string[] | нет | - |

- Бэкенд проверяет только формат. Любое поле может отсутствовать: карточка сначала создаётся черновиком,
  обязательность полей проверяет форма.
- Значения справочников (тип парфюмерии, упаковка, материал, техрегламент) бэкенд не ограничивает: в MVP это
  демонстрационные списки, а не полная номенклатура.
- Неизвестное поле в `attributes` возвращает ошибку 422.

Статус карточки (`status`): `draft`, `on_moderation`, `published`, `rejected`. Новая карточка получает `draft`;
изменить статус через API пока нельзя.

## Эндпоинты

| Метод | Путь | Тело запроса | Ответ |
|---|---|---|---|
| GET | `/api/products` | - | список строк каталога |
| POST | `/api/products` | `{ "attributes": {...} }` или пустое тело | 201, карточка |
| GET | `/api/products/{id}` | - | карточка |
| PATCH | `/api/products/{id}` | `{ "attributes": {...} }` | карточка |
| POST | `/api/products/{id}/photos` | `multipart/form-data`: `file`, `perspective`, `packageId` | 201, фото |
| GET | `/api/products/{id}/photos/{photoId}/content` | - | файл изображения |
| DELETE | `/api/products/{id}/photos/{photoId}` | - | 204 |
| POST | `/api/products/{id}/check` | - | результаты проверок |

PATCH меняет только переданные поля. `null` удаляет поле из карточки.

### Карточка

```json
{
  "id": "6f1c2a0e-5b7d-4c1e-9a3f-2d8e4b6a1c90",
  "status": "draft",
  "createdAt": "2026-10-31T12:00:00Z",
  "updatedAt": "2026-10-31T12:05:00Z",
  "attributes": {
    "fullName": "Духи тестовые 50 мл",
    "tnVedCode": "3303",
    "country": ["RU"],
    "perfumeryType": "ДУХИ",
    "volume": { "value": 50, "unit": "мл" }
  },
  "photos": [
    {
      "id": "0b8f3d2e-7c41-4a9b-8e5f-1a2b3c4d5e6f",
      "url": "/api/products/6f1c2a0e-5b7d-4c1e-9a3f-2d8e4b6a1c90/photos/0b8f3d2e-7c41-4a9b-8e5f-1a2b3c4d5e6f/content",
      "perspective": "front",
      "packageId": "main"
    }
  ]
}
```

### Строка каталога

`GET /api/products` возвращает новые карточки первыми:

```json
[
  {
    "id": "6f1c2a0e-5b7d-4c1e-9a3f-2d8e4b6a1c90",
    "name": "Духи тестовые 50 мл",
    "status": "draft",
    "gtin": "04748756756746",
    "brand": "шиккомпот",
    "createdAt": "2026-10-31T12:00:00Z",
    "photoUrl": "/api/products/6f1c2a0e-5b7d-4c1e-9a3f-2d8e4b6a1c90/photos/0b8f3d2e-7c41-4a9b-8e5f-1a2b3c4d5e6f/content"
  }
]
```

`name` берётся из `fullName`, `photoUrl` указывает на первое фото (или `null`).

### Фото

- Файл передаётся отдельным `multipart/form-data` запросом, не внутри JSON.
- Допустимы JPEG, PNG и WEBP, размер ограничен настройкой бэкенда (по умолчанию 10 МБ).
- `perspective` обязателен (например, `front`), `packageId` можно не передавать.
- Ответ: `{ "id", "url", "perspective", "packageId" }`. По `url` фронтенд получает само изображение.

## Результат проверки

`POST /api/products/{id}/check` возвращает список объектов, по одному на каждую проверку:

```json
{
  "check_id": "volume_vs_name",
  "status": "WARNING",
  "reason_code": "VOLUME_MISMATCH",
  "explanation": "Объём в названии 50 мл, в атрибуте 100 мл",
  "field_refs": ["fullName", "volume"],
  "algorithm_version": 1
}
```

`status`: `PASS`, `WARNING`, `REVIEW`, `NOT_CHECKED`, `ERROR`. Решение «принять или отклонить» принимает
потребитель, не Carat. В MVP этого эндпоинта нет: он нужен для проверок Carat.

## Ошибки

Ошибка ввода, HTTP 422:

```json
{
  "error": "VALIDATION_ERROR",
  "fields": { "volume.value": "Значение должно быть положительным числом" }
}
```

Ключ поля - путь внутри `attributes` (`volume.value`, `country.0`); для фото - `file` или `perspective`.
Формат не меняется без согласования с фронтендом.

Карточка или фото не найдены: HTTP 404, `{ "detail": "..." }`.

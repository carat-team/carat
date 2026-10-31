# REST API бэкенда

Контракт между фронтендом и бэкендом. Источник: лист MVP (`CARAT_MVP.xlsx`). Изменения согласуются с фронтендом.

## Карточка товара

Поля (категория «Парфюмерия»):

| Поле | Тип | Примечание |
|---|---|---|
| `fullName` | string | полное наименование |
| `tnVedCode` | string | код ТН ВЭД |
| `tnVedCode10` | string | код ТН ВЭД, 10 знаков |
| `gtin` | string | |
| `brand` | string | |
| `country` | string[] | |
| `perfumeryType` | string | тип парфюмерной продукции |
| `volume` | `{ "value": number, "unit": string }` | |
| `packageType` | string | |
| `packMaterial` | string | |
| `standardNumber` | string[] | |

Фотографии хранятся отдельно: файл, ракурс (`perspective`), идентификатор упаковки (`packageId`).

## Эндпоинты

| Метод | Путь | Назначение |
|---|---|---|
| GET | `/api/products` | список карточек |
| POST | `/api/products` | создать карточку |
| GET | `/api/products/{id}` | получить карточку |
| PATCH | `/api/products/{id}` | изменить поля карточки |
| POST | `/api/products/{id}/photos` | загрузить фото, `multipart/form-data`: `file`, `perspective`, `packageId` |
| DELETE | `/api/products/{id}/photos/{photoId}` | удалить фото |
| POST | `/api/products/{id}/check` | запустить все проверки, вернуть результаты |

## Результат проверки

`POST /api/products/{id}/check` возвращает список объектов:

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

`status`: `PASS`, `WARNING`, `REVIEW`, `NOT_CHECKED`, `ERROR`. Решение «принять или отклонить» принимает потребитель, не Carat.

## Ошибки валидации

HTTP 422:

```json
{ "error": "VALIDATION_ERROR", "fields": { "volume": "Укажите объём" } }
```

Формат не меняется без согласования с фронтендом.

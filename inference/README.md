# Inference-сервис

Сервис инференса для Carat.

## Структура

- `app/` - runtime-код сервиса.
- `app/detectors/` - обертки над моделями, которые используются gRPC-обработчиками.
- `app/inference/` - вспомогательные функции runtime-предобработки.
- `weights/` - локальные веса моделей для runtime. Крупные файлы весов не коммитятся.
- `config.yaml` - конфигурация сервиса, включая относительные пути к весам.
- `generated/` - сгенерированный Python-код gRPC, не коммитится.

Сервис использует protobuf-контракты из корневой директории `proto/`.
Он не должен импортировать код из `model/training`, потому что эта часть
предназначена для исследований и обучения моделей.

## Запуск

Нужны [uv](https://docs.astral.sh/uv/) и [just](https://just.systems/). Python нужной
версии (`.python-version`) uv скачает сам.

```bash
just sync                    # установить зависимости в .venv
just proto                   # сгенерировать gRPC-код в generated/ (main.py делает это и сам)
just run                     # запустить gRPC-сервер на :50051
just test-text "some text"   # отправить текст запущенному серверу
just test-photo path/to.jpg  # отправить изображение
just test-ocr path/to.jpg    # прочитать текст на изображении (OCR)
just test-segmentation path/to.jpg  # получить маску товара
just docker                  # собрать и запустить сервис в Docker
just                         # список всех команд
```

Перед запуском положите веса из `config.yaml` в `weights/`, иначе сервер не стартует.

OCR (`ReadText` из `proto/carat/inference/ocr.proto`) работает на EasyOCR. Модели для языков из
`config.yaml` (`models.ocr.languages`) EasyOCR скачивает сам при первом запуске в `~/.EasyOCR/model/`,
в Docker-образ они скачиваются при сборке.

Сегментация товара (`SegmentProduct` из `proto/carat/inference/segmentation.proto`) работает на
[rembg](https://github.com/danielgatis/rembg) с моделью из `config.yaml` (`models.segmentation.model_name`).
Модель скачивается сама при первом запуске:

| Модель | Файл | Источник | Куда кладётся |
|---|---|---|---|
| `isnet-general-use` | `isnet-general-use.onnx` (~170 МБ) | [релизы rembg](https://github.com/danielgatis/rembg/releases/download/v0.0.0/isnet-general-use.onnx) | `$U2NET_HOME`, по умолчанию `~/.u2net/`; в Docker-образе `/app/inference/models/`, скачивается при сборке |

Проверка на запущенном сервере: `just test-segmentation path/to.jpg` сохранит маску рядом с фото.

Зависимости описаны в `pyproject.toml` и зафиксированы в `uv.lock`:

```bash
uv add <package>    # добавить зависимость
just upgrade        # обновить все зависимости в uv.lock
```

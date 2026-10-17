# Веса классификатора кадра и «духи / нет» (задача #38)

Ветка содержит только веса, без общей истории с `dev`, и в `dev` не сливается. Код обучения, оценки и использования лежит в
`model/training/frame_classifier/` (PR [carat-team/carat#10](https://github.com/carat-team/carat/pull/10)).

| Файл | Размер | SHA-256 |
|---|---|---|
| `efficientnet_b0_frame_type.pth` | 15953 КБ | `d529298adc39d0ce43a7555643fb955455a20e05c042ccef0bdb2168b96f72ec` |
| `efficientnet_b0_perfume.pth` | 15957 КБ | `fea8c4fbd67c3d0b9475c0b5baef62272aaa7630b813b4f5606d161d7c20363b` |
| `siglip2_frame_type_head.safetensors` | 12 КБ | `846f156fa378cd55e9f05a5a5c78257f0b4e486ce909db9a7385698039797002` |
| `siglip2_perfume_head.safetensors` | 3 КБ | `9e38300ea8ff781cf5d9770e0f55b761e0c1ac9fd1fdf2552331716d9267e614` |

## Что внутри

- `siglip2_frame_type_head.safetensors` – линейный слой (`weight` [4, 768], `bias` [4]) поверх L2-нормированного эмбеддинга изображения
  `google/siglip2-base-patch16-224`. Классы по порядку: studio, casual, graphic, document. Вероятности: softmax от `x @ weight.T + bias`.
- `siglip2_perfume_head.safetensors` – линейный слой (`weight` [1, 768], `bias` [1]) «духи / нет»; духи при оценке >= `0.0`.
- `efficientnet_b0_frame_type.pth`, `efficientnet_b0_perfume.pth` – `state_dict` EfficientNet-B0 (torchvision, `classifier[1]` заменён на `Linear(1280, 4)` и `Linear(1280, 2)`),
  бейзлайны для сравнения. Для боевого использования рекомендуются головы SigLIP 2.
- `weights.json` – манифест (бэкбон, классы, порог, размеры и контрольные суммы).

Сам SigLIP 2 в ветку не входит: его скачивает `transformers` с Hugging Face (`google/siglip2-base-patch16-224`).

## Как использовать

```bash
git fetch origin chore/add-frame-classifier-weights
git worktree add /tmp/frame-weights origin/chore/add-frame-classifier-weights   # или: git checkout origin/... -- .
cd model/training/frame_classifier
python predict.py --weights-dir /tmp/frame-weights photo1.jpg photo2.jpg
```

`predict.py` печатает по одной JSON-строке на фото: тип кадра с вероятностями и оценку «духи / нет».
Перед головой «духи / нет» применяется та же нормализация изображений, что при обучении (ограничение 256 px и одно JPEG-сжатие), перед головой типа кадра – обычное сжатие до 224x224.

Проверка целостности: `sha256sum *.pth *.safetensors` и сравнение с таблицей выше.

"""Демонстрационный запуск проверки 100 карточек и построение метрик."""

from pathlib import Path
import json

from perfumery_name_check import check_products_with_metrics


def build_100_products():
    """Создаёт воспроизводимый набор из 100 тестовых карточек."""
    templates = [
        ("Духи Rose 50 мл", "ДУХИ"),
        ("Парфюмированная вода Rose 50 мл", "EDP"),
        ("Туалетная вода Rose 50 мл", "EDT"),
        ("Одеколон Classic 100 мл", "ОДЕКОЛОН"),
        ("Туалетная вода Aqua 100 мл", "ДУХИ"),  # ожидаемое предупреждение
        ("Духи Amber 30 мл", "Туалетная вода"),  # ожидаемое предупреждение
        ("White Horse ALREHAB, 6 мл", "ДУХИ"),  # нельзя проверить по названию
        ("Body mist Rose 100 мл", "МИСТ"),
        ("Perfume mist Rose", "Парфюмерный спрей"),
        ("Твердые духи Rose", "Твердые духи"),
        ("Духи Rose 50 мл", "неизвестный тип"),  # ручная проверка
        ("", "ДУХИ"),  # недостаточно данных
        ("Eau de Parfum Rose 50 ml", "Парфюмерная вода"),
        ("Eau de Toilette Fresh 100 ml", "EDT"),
        ("Одеколон Citrus 50 мл", "EDC"),
        ("Парфюмерная вода Jasmine 50 мл", "Парфюмированная вода"),
        ("Духи Vanilla 10 мл", "parfum"),
        ("Hair mist Cherry 100 ml", "Мист"),
        ("Solid perfume Musk", "Твердые духи"),
        ("Спрей для тела Fresh", "ДУХИ"),
    ]
    products = []
    for i in range(100):
        name, declared_type = templates[i % len(templates)]
        products.append(
            {
                "name": name,
                "declared_type": declared_type,
                "test_id": f"TEST-{i + 1:03d}",
            }
        )
    return products


def save_dashboard(report, output_path):
    """Сохраняет PNG-дашборд. Для построения требуется matplotlib."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    metrics = report["metrics"]
    labels = ["Совпадения", "Предупреждения", "Ручная проверка", "Не проверено"]
    keys = ["ok_count", "warning_count", "manual_review_count", "not_checked_count"]
    values = [metrics[key] for key in keys]
    colors = ["#23866B", "#E4A23A", "#8B7BB8", "#718096"]

    fig = plt.figure(figsize=(12, 7), facecolor="#F4F6FA")
    ax = fig.add_axes([0.08, 0.17, 0.52, 0.65])
    ax.set_facecolor("#F4F6FA")
    bars = ax.barh(labels, values, color=colors, height=0.58)
    ax.invert_yaxis()
    ax.set_xlim(0, max(10, max(values, default=0) * 1.2))
    ax.set_xlabel("Количество карточек")
    ax.grid(axis="x", linestyle="--", alpha=0.25)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_visible(False)
    for bar, value in zip(bars, values):
        ax.text(
            value + 0.5,
            bar.get_y() + bar.get_height() / 2,
            str(value),
            va="center",
            fontsize=11,
            fontweight="bold",
            color="#202A3C",
        )

    fig.text(
        0.07,
        0.92,
        "Метрики проверки карточек парфюмерии",
        fontsize=20,
        fontweight="bold",
        color="#172033",
    )
    fig.text(
        0.07,
        0.875,
        f"Результаты тестового набора · {metrics['total_rows']} карточек",
        fontsize=12,
        color="#667085",
    )

    kpis = [
        ("Всего карточек", str(metrics["total_rows"]), "в тестовом наборе"),
        (
            "Доля предупреждений",
            f"{metrics['warning_rate_percent']:.2f}%",
            "от всех карточек",
        ),
        (
            "Покрытие автопроверкой",
            f"{metrics['coverage_rate_percent']:.2f}%",
            "совпадения + предупреждения",
        ),
        (
            "Скорость обработки",
            f"{metrics['rows_per_second']:.0f}",
            "карточек в секунду",
        ),
    ]
    positions = [(0.68, 0.68), (0.68, 0.49), (0.68, 0.30), (0.68, 0.11)]
    for (title, value, subtitle), (x, y) in zip(kpis, positions):
        card = FancyBboxPatch(
            (x, y),
            0.27,
            0.135,
            boxstyle="round,pad=0.012,rounding_size=0.02",
            transform=fig.transFigure,
            facecolor="white",
            edgecolor="#E0E5EE",
            linewidth=1,
        )
        fig.patches.append(card)
        fig.text(x + 0.018, y + 0.091, title, fontsize=9, color="#667085")
        fig.text(
            x + 0.018, y + 0.050, value, fontsize=18, fontweight="bold", color="#172033"
        )
        fig.text(x + 0.018, y + 0.018, subtitle, fontsize=8, color="#667085")

    fig.text(
        0.07,
        0.055,
        "Демонстрационные данные. "
        "«Не проверено» не означает, что карточка корректна.",
        fontsize=9,
        color="#667085",
    )
    fig.savefig(
        output_path, dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor()
    )
    plt.close(fig)


def main():
    products = build_100_products()
    report = check_products_with_metrics(products)
    metrics = report["metrics"]

    print("\n===== МЕТРИКИ ПРОВЕРКИ (100 КАРТОЧЕК) =====")
    print(f"Всего карточек: {metrics['total_rows']}")
    print(f"Совпадений: {metrics['ok_count']}")
    print(f"Предупреждений: {metrics['warning_count']}")
    print(f"Ручная проверка: {metrics['manual_review_count']}")
    print(f"Не проверено: {metrics['not_checked_count']}")
    print(f"Доля предупреждений: {metrics['warning_rate_percent']}%")
    print(f"Покрытие автопроверкой: {metrics['coverage_rate_percent']}%")
    print(f"Время обработки: {metrics['processing_time_sec']} сек.")
    print(f"Скорость: {metrics['rows_per_second']} карточек/сек.")

    output_dir = Path(__file__).resolve().parent
    dashboard_path = output_dir / "metrics_dashboard.png"
    try:
        save_dashboard(report, dashboard_path)
        print(f"\nГрафик метрик сохранён: {dashboard_path}")
    except ImportError:
        print(
            "\nДля PNG-графика установите matplotlib: python -m pip install matplotlib"
        )

    with (output_dir / "metrics_report.json").open("w", encoding="utf-8") as file:
        json.dump(
            {"metrics": metrics, "results": report["results"]},
            file,
            ensure_ascii=False,
            indent=2,
        )
    print(f"JSON-отчёт сохранён: {output_dir / 'metrics_report.json'}")


if __name__ == "__main__":
    main()

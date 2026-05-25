import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QSpinBox, QTableWidget, QTableWidgetItem,
    QFileDialog, QHeaderView, QGroupBox, QSplitter
)
from PyQt6.QtCore import Qt
import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure

from utils import CurrencyDataLoader, MovingAverageForecaster


class CurrencyTab(QWidget):
    """
    Вкладка анализа курса рубля (Вариант 2).
    """

    def __init__(self):
        super().__init__()
        self.records = []
        self.month = ""
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        control_group = QGroupBox("Управление")
        control_layout = QHBoxLayout(control_group)

        self.btn_load = QPushButton("📂 Открыть файл")
        self.btn_load.clicked.connect(self._load_file)

        self.lbl_window = QLabel("Окно прогноза (n):")
        self.spin_window = QSpinBox()
        self.spin_window.setRange(2, 15)
        self.spin_window.setValue(3)

        self.lbl_steps = QLabel("Дней вперёд (N):")
        self.spin_steps = QSpinBox()
        self.spin_steps.setRange(1, 30)
        self.spin_steps.setValue(7)

        self.btn_forecast = QPushButton("📈 Построить прогноз")
        self.btn_forecast.clicked.connect(self._update_chart)
        self.btn_forecast.setEnabled(False)

        self.btn_export = QPushButton("💾 Экспорт графика")
        self.btn_export.clicked.connect(self._export_chart)
        self.btn_export.setEnabled(False)

        for w in [self.btn_load, self.lbl_window, self.spin_window,
                  self.lbl_steps, self.spin_steps,
                  self.btn_forecast, self.btn_export]:
            control_layout.addWidget(w)
        control_layout.addStretch()

        layout.addWidget(control_group)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Таблица
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        self.lbl_info = QLabel("Файл не загружен")
        self.lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Дата", "USD (руб)", "EUR (руб)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table_layout.addWidget(self.lbl_info)
        table_layout.addWidget(self.table)

        self.lbl_stats = QLabel("")
        self.lbl_stats.setWordWrap(True)
        table_layout.addWidget(self.lbl_stats)
        splitter.addWidget(table_widget)

        # График
        chart_widget = QWidget()
        chart_layout = QVBoxLayout(chart_widget)
        self.figure = Figure(figsize=(6, 4))
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        chart_layout.addWidget(self.toolbar)
        chart_layout.addWidget(self.canvas)
        splitter.addWidget(chart_widget)

        splitter.setSizes([350, 650])
        layout.addWidget(splitter)

    def _load_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Открыть файл с данными о курсе валют",
            os.path.join(os.path.dirname(__file__), "..", "data"),
            "JSON файлы (*.json)"
        )
        if not path:
            return
        try:
            loader = CurrencyDataLoader(path)
            self.month, self.records = loader.load()
            self._fill_table()
            self._show_stats()
            self._update_chart()
            self.btn_forecast.setEnabled(True)
            self.btn_export.setEnabled(True)
            self.lbl_info.setText(f"Курс рубля — {self.month}")
        except Exception as e:
            self.lbl_info.setText(f"Ошибка загрузки: {e}")

    def _fill_table(self):
        self.table.setRowCount(len(self.records))
        for row, rec in enumerate(self.records):
            self.table.setItem(row, 0, QTableWidgetItem(rec.date))
            self.table.setItem(row, 1, QTableWidgetItem(f"{rec.usd:.2f}"))
            self.table.setItem(row, 2, QTableWidgetItem(f"{rec.eur:.2f}"))

    def _show_stats(self):
        if not self.records:
            return
        usd_vals = [(rec.usd, rec.date) for rec in self.records]
        eur_vals = [(rec.eur, rec.date) for rec in self.records]

        # Максимальный прирост/падение рубля (минимум курса = рубль сильнее)
        usd_max = max(usd_vals, key=lambda x: x[0])
        usd_min = min(usd_vals, key=lambda x: x[0])
        eur_max = max(eur_vals, key=lambda x: x[0])
        eur_min = min(eur_vals, key=lambda x: x[0])

        # Дневные изменения
        usd_changes = [
            abs(self.records[i].usd - self.records[i-1].usd)
            for i in range(1, len(self.records))
        ]
        eur_changes = [
            abs(self.records[i].eur - self.records[i-1].eur)
            for i in range(1, len(self.records))
        ]
        max_usd_change_idx = usd_changes.index(max(usd_changes)) + 1
        max_eur_change_idx = eur_changes.index(max(eur_changes)) + 1

        self.lbl_stats.setText(
            f"💵 USD: макс {usd_max[0]} ({usd_max[1]}), мин {usd_min[0]} ({usd_min[1]})\n"
            f"   Макс изменение за день: {max(usd_changes):.2f} руб ({self.records[max_usd_change_idx].date})\n"
            f"💶 EUR: макс {eur_max[0]} ({eur_max[1]}), мин {eur_min[0]} ({eur_min[1]})\n"
            f"   Макс изменение за день: {max(eur_changes):.2f} руб ({self.records[max_eur_change_idx].date})"
        )

    def _update_chart(self):
        if not self.records:
            return

        n = self.spin_window.value()
        steps = self.spin_steps.value()

        dates = [rec.date[5:] for rec in self.records]
        usd_vals = [rec.usd for rec in self.records]
        eur_vals = [rec.eur for rec in self.records]

        forecaster = MovingAverageForecaster(window=n)
        forecast_usd = forecaster.forecast(usd_vals, steps)
        forecast_eur = forecaster.forecast(eur_vals, steps)

        self.figure.clear()
        ax = self.figure.add_subplot(111)

        x = list(range(len(dates)))
        ax.plot(x, usd_vals, color="green", label="USD", linewidth=2)
        ax.plot(x, eur_vals, color="blue", label="EUR", linewidth=2)

        x_forecast = list(range(len(dates), len(dates) + steps))
        ax.plot(x_forecast, forecast_usd, color="lime", linestyle="--",
                marker="o", markersize=4, label=f"Прогноз USD (n={n})")
        ax.plot(x_forecast, forecast_eur, color="cornflowerblue", linestyle="--",
                marker="o", markersize=4, label=f"Прогноз EUR (n={n})")

        ax.axvline(x=len(dates) - 0.5, color="gray", linestyle=":", linewidth=1)

        tick_positions = x[::3] + x_forecast[::3]
        tick_labels = dates[::3] + [f"+{i+1}д" for i in range(0, steps, 3)]
        ax.set_xticks(tick_positions[:len(tick_labels)])
        ax.set_xticklabels(tick_labels, rotation=45, fontsize=8)

        ax.set_title(f"Курс рубля — {self.month}")
        ax.set_ylabel("Рублей за 1 ед. валюты")
        ax.legend()
        ax.grid(True, alpha=0.3)
        self.figure.tight_layout()
        self.canvas.draw()

    def _export_chart(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить график", "currency_chart",
            "PNG (*.png);;PDF (*.pdf);;SVG (*.svg)"
        )
        if path:
            self.figure.savefig(path, dpi=150, bbox_inches="tight")
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QSpinBox, QTableWidget, QTableWidgetItem,
    QFileDialog, QHeaderView, QGroupBox, QSplitter
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure

from utils import WeatherDataLoader, MovingAverageForecaster


class WeatherTab(QWidget):
    """
    Вкладка анализа погоды (Вариант 3).
    Загружает данные, строит графики, прогнозирует скользящей средней.
    """

    def __init__(self):
        super().__init__()
        self.records = []
        self.city = ""
        self.month = ""
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # --- Панель управления ---
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

        # --- Сплиттер: таблица слева, график справа ---
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Таблица
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        self.lbl_info = QLabel("Файл не загружен")
        self.lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Дата", "Макс °C", "Мин °C", "Средн °C", "Описание"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table_layout.addWidget(self.lbl_info)
        table_layout.addWidget(self.table)

        # Статистика
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
            self, "Открыть файл с данными о погоде",
            os.path.join(os.path.dirname(__file__), "..", "data"),
            "JSON файлы (*.json)"
        )
        if not path:
            return
        try:
            loader = WeatherDataLoader(path)
            self.city, self.month, self.records = loader.load()
            self._fill_table()
            self._show_stats()
            self._update_chart()
            self.btn_forecast.setEnabled(True)
            self.btn_export.setEnabled(True)
            self.lbl_info.setText(f"{self.city} — {self.month}")
        except Exception as e:
            self.lbl_info.setText(f"Ошибка загрузки: {e}")

    def _fill_table(self):
        self.table.setRowCount(len(self.records))
        for row, rec in enumerate(self.records):
            self.table.setItem(row, 0, QTableWidgetItem(rec.date))

            # Максимальная температура — красный фон
            item_max = QTableWidgetItem(str(rec.max_temp))
            item_max.setBackground(QColor(255, 180, 180))
            self.table.setItem(row, 1, item_max)

            # Минимальная температура — синий фон
            item_min = QTableWidgetItem(str(rec.min_temp))
            item_min.setBackground(QColor(180, 200, 255))
            self.table.setItem(row, 2, item_min)

            self.table.setItem(row, 3, QTableWidgetItem(str(rec.avg_temp)))
            self.table.setItem(row, 4, QTableWidgetItem(rec.description))

    def _show_stats(self):
        if not self.records:
            return
        deltas = [(rec.temp_delta, rec.date) for rec in self.records]
        max_delta = max(deltas, key=lambda x: x[0])
        min_delta = min(deltas, key=lambda x: x[0])
        self.lbl_stats.setText(
            f"📊 Наибольший перепад: {max_delta[0]}°C ({max_delta[1]})\n"
            f"📊 Наименьший перепад: {min_delta[0]}°C ({min_delta[1]})"
        )

    def _update_chart(self):
        if not self.records:
            return

        n = self.spin_window.value()
        steps = self.spin_steps.value()

        dates = [rec.date[5:] for rec in self.records]  # MM-DD
        max_temps = [rec.max_temp for rec in self.records]
        min_temps = [rec.min_temp for rec in self.records]
        avg_temps = [rec.avg_temp for rec in self.records]

        forecaster = MovingAverageForecaster(window=n)
        forecast_avg = forecaster.forecast(avg_temps, steps)

        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # Исторические данные
        x = list(range(len(dates)))
        ax.plot(x, max_temps, color="red", label="Макс °C", linewidth=1.5)
        ax.plot(x, min_temps, color="blue", label="Мин °C", linewidth=1.5)
        ax.plot(x, avg_temps, color="green", label="Средн °C", linewidth=2)

        # Прогноз
        x_forecast = list(range(len(dates), len(dates) + steps))
        ax.plot(x_forecast, forecast_avg, color="orange", linestyle="--",
                marker="o", markersize=4, label=f"Прогноз (n={n})")

        # Разделительная линия
        ax.axvline(x=len(dates) - 0.5, color="gray", linestyle=":", linewidth=1)

        # Подписи по оси X
        tick_positions = x[::3] + x_forecast[::3]
        tick_labels = dates[::3] + [f"+{i+1}д" for i in range(0, steps, 3)]
        ax.set_xticks(tick_positions[:len(tick_labels)])
        ax.set_xticklabels(tick_labels, rotation=45, fontsize=8)

        ax.set_title(f"Температура — {self.city}, {self.month}")
        ax.set_ylabel("Температура (°C)")
        ax.legend()
        ax.grid(True, alpha=0.3)
        self.figure.tight_layout()
        self.canvas.draw()

    def _export_chart(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить график", "weather_chart",
            "PNG (*.png);;PDF (*.pdf);;SVG (*.svg)"
        )
        if path:
            self.figure.savefig(path, dpi=150, bbox_inches="tight")
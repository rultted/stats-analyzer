from PyQt6.QtWidgets import QMainWindow, QTabWidget, QStatusBar
from PyQt6.QtGui import QIcon
from ui.weather_tab import WeatherTab
from ui.currency_tab import CurrencyTab


class MainWindow(QMainWindow):
    """
    Главное окно приложения.
    Содержит вкладки для каждого модуля (погода, валюты).
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Stats Analyzer")
        self.setMinimumSize(1000, 700)
        self._init_ui()

    def _init_ui(self):
        # Вкладки — общий интерфейс для всей команды
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)

        self.weather_tab = WeatherTab()
        self.currency_tab = CurrencyTab()

        self.tabs.addTab(self.weather_tab, "🌤 Погода")
        self.tabs.addTab(self.currency_tab, "💱 Курс валют")

        self.setCentralWidget(self.tabs)

        # Статус-бар внизу окна
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готово")
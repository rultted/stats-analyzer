from typing import List


class MovingAverageForecaster:
    """
    Прогнозирование методом экстраполяции по скользящей средней.
    Принцип инкапсуляции: логика прогноза скрыта внутри класса.
    """

    def __init__(self, window: int):
        if window < 1:
            raise ValueError("Размер окна должен быть >= 1")
        self.window = window

    def forecast(self, data: List[float], steps: int) -> List[float]:
        """
        Прогнозирует steps значений вперёд на основе исходного ряда data.
        Возвращает список из steps прогнозных значений.
        """
        if len(data) < self.window:
            raise ValueError(
                f"Данных ({len(data)}) меньше, чем размер окна ({self.window})"
            )

        series = list(data)
        predictions = []

        for _ in range(steps):
            window_values = series[-self.window:]
            next_val = sum(window_values) / self.window
            predictions.append(round(next_val, 2))
            series.append(next_val)

        return predictions

    def smooth(self, data: List[float]) -> List[float]:
        """
        Сглаживает исходный ряд скользящей средней.
        Возвращает сглаженный ряд той же длины (первые window-1 значений — None).
        """
        smoothed = [None] * (self.window - 1)
        for i in range(self.window - 1, len(data)):
            window_values = data[i - self.window + 1: i + 1]
            smoothed.append(round(sum(window_values) / self.window, 2))
        return smoothed
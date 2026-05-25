import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List


# Абстрактный базовый класс для загрузчиков данных (принцип абстракции ООП)
class BaseDataLoader(ABC):
    def __init__(self, filepath: str):
        self.filepath = filepath

    @abstractmethod
    def load(self):
        pass

    def _read_json(self) -> dict:
        with open(self.filepath, "r", encoding="utf-8") as f:
            return json.load(f)


@dataclass
class WeatherRecord:
    date: str
    max_temp: float
    min_temp: float
    avg_temp: float
    description: str

    @property
    def temp_delta(self) -> float:
        """Перепад температуры за день"""
        return self.max_temp - self.min_temp


@dataclass
class CurrencyRecord:
    date: str
    usd: float
    eur: float


# Загрузчик погодных данных (наследование от BaseDataLoader)
class WeatherDataLoader(BaseDataLoader):
    def load(self) -> tuple[str, str, List[WeatherRecord]]:
        raw = self._read_json()
        records = [
            WeatherRecord(
                date=entry["date"],
                max_temp=entry["max_temp"],
                min_temp=entry["min_temp"],
                avg_temp=entry["avg_temp"],
                description=entry["description"],
            )
            for entry in raw["data"]
        ]
        return raw["city"], raw["month"], records


# Загрузчик валютных данных (наследование от BaseDataLoader)
class CurrencyDataLoader(BaseDataLoader):
    def load(self) -> tuple[str, List[CurrencyRecord]]:
        raw = self._read_json()
        records = [
            CurrencyRecord(
                date=entry["date"],
                usd=entry["USD"],
                eur=entry["EUR"],
            )
            for entry in raw["data"]
        ]
        return raw["month"], records
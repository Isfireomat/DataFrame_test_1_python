from typing import Any, Callable
import re
import pandas as pd
from pandas import DataFrame
import numpy as np


class DFFile:
    def __init__(self, data: DataFrame) -> None:
        self.source_data: DataFrame = data
        self._dates_registration: DataFrame = self.source_data[["_id", "Дата регистрации"]]
        self._data: DataFrame = data.melt(id_vars=['_id'], var_name='year_field', value_name='value')
        self._data['year'] = self._data['year_field'].str.extract(r'(\d{4})')
        self._data['field'] = self._data['year_field'].str.replace(r'\d{4},\s', '', regex=True)
        self._data = self._data.set_index(['_id', 'year', 'field'])

    def get_value(self, df_id: int, year: int, field: str) -> Any:
        try:
            value: Any = self._data.loc[(df_id, str(year), field), 'value']
            if isinstance(value, str):
                if bool(re.search(r"[^0-9. ]", value)):
                    return value
                value = value.replace(" ", "")
            return np.float64(value)
        except KeyError:
            return np.nan

    def get_year(self, df_id: int) -> int:
        return self._dates_registration.loc[df_id, "Дата регистрации"].year


class DFProcessor:
    _instance: object | None = None
    _calculate_fields: dict[str, int] = {
            "Выручка, RUB": 1,
            "Себестоимость продаж, RUB": -1,
            "Управленческие расходы, RUB": -1,
            "Коммерческие расходы, RUB": -1,
        }
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    @staticmethod
    def _calculate_profit(
        file: DFFile, /, df_id: int, year: int, prev: int, last_available: int
    ) -> np.float64 | float:
        value: np.float64 = 0
        for field, sign in DFProcessor._calculate_fields.items():
            field_value: np.float64 = np.float64(
                    DFProcessor._get_value(file, 
                                           df_id, 
                                           year, 
                                           field, 
                                           prev, 
                                           last_available)
                )
            if field == list(DFProcessor._calculate_fields.keys())[0] \
                and pd.isna(field_value):
                return np.nan
            value += field_value * sign
        return value

    @staticmethod
    def _get_company_age(file: DFFile, /, df_id: int, year: int) -> int:
        return abs(file.get_year(df_id) - year)
        
    @staticmethod
    def _get_year_with_prev(year: int, prev: int) -> int:
        return year - prev

    @staticmethod
    def _get_value(
        file: DFFile, /, df_id: int, year: int, 
        field_name: str, prev: int, last_available: int
    ) -> np.float64 | float:
        for last_year in range(year - prev, year - last_available - prev - 1, -1):
            value = file.get_value(df_id, last_year, field_name)
            if not pd.isna(value):
                return value
        return np.nan

    @staticmethod
    def _get_values(file: DFFile, applications: DataFrame, /, 
                    field_name: str, prev: int, last_available: int) -> np.array:
        match field_name:
            case "Прибыль (убыток) от продажи, RUB": 
                values: np.array = np.array(
                    [
                        DFProcessor._calculate_profit(file, df_id, year, prev, last_available)
                        for df_id, year in zip(applications["_id"], applications["year"])
                    ]
                )
                return values
            case "Возраст компании, years": 
                values: np.array = np.array(
                    [
                        DFProcessor._get_company_age(file, df_id, year)
                        for df_id, year in zip(applications["_id"], applications["year"])
                    ]
                )
                return values
            case _ : 
                values: np.array = np.array(
                    [
                        DFProcessor._get_value(file, df_id, year, field_name, prev, last_available)
                        for df_id, year in zip(applications["_id"], applications["year"])
                    ]
                )
                return values

    def get_data(
        self,
        data: DataFrame,
        applications: DataFrame,
        query: list[dict[str, Any]],
    ) -> DataFrame:
        file: DFFile = DFFile(data)
        output = file.source_data[["_id"]].copy()
        
        for part_query in query:
            field_name: str = part_query.get('field_name')
            prev: int = part_query.get('prev', 0)
            last_available: int = part_query.get('last_available', 0)
            
            values: np.array = DFProcessor._get_values(file, 
                                                       applications, 
                                                       field_name, 
                                                       prev,
                                                       last_available)
            
            postfix: str = (
                f"{('Prev' if prev > 0 else 'Next') * abs(prev)} "
                f"{f'LA{last_available}' if last_available != 0 else ''}"
            ).strip()
            output[f"{field_name} {postfix}".strip()] = values
        
        return output

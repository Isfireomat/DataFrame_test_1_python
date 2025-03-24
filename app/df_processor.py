import pandas as pd
import numpy as np


class DFProcessor:
    _instance = None
    _calculate_fields = {
        "Выручка, RUB": 1,
        "Себестоимость продаж, RUB": -1,
        "Управленческие расходы, RUB": -1,
        "Коммерческие расходы, RUB": -1,
    }
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @staticmethod
    def _calculate_profit(
        data: pd.DataFrame, df_id: int, year: int, 
        prev: int, last_available: int) -> float:
        values = list(map(
            lambda field_sign: np.float64(
                DFProcessor._get_value(
                    data, df_id, year, 
                    field_sign[0], prev, last_available) * field_sign[1]
                ),
            DFProcessor._calculate_fields.items()
        ))
        return np.nan if pd.isna(values[0]) else sum(values)

    @staticmethod
    def _get_company_age(data: pd.DataFrame, df_id: int, year: int) -> int:
        company_age = year - pd.to_datetime(data.loc[df_id, 'Дата регистрации']).year
        return company_age if company_age>0 else np.nan

    @staticmethod
    def _get_value(
        data: pd.DataFrame, df_id: int, year: int, field_name: str, 
        prev: int, last_available: int) -> float:
        columns = list(
                    filter(
                        lambda col: col in data.columns, 
                        list(map(lambda y: f"{y}, {field_name}", 
                        range(year - prev, year - last_available - prev - 1, -1))
                    )
                )
            )        
        row_values = data.loc[df_id, columns]
        valid_value = row_values.first_valid_index()
        return row_values[valid_value] if valid_value is not None else np.nan


    def get_data(   
            self, data: pd.DataFrame, applications: pd.DataFrame, 
            queries: list[dict[str, any]]) -> pd.DataFrame:
        output = data[['_id']].copy()
        
        def process_query(query):
            field_name = query.get('field_name')
            prev, last_available = query.get('prev', 0), query.get('last_available', 0)
            methods = {
                "Прибыль (убыток) от продажи, RUB": 
                    lambda row: self._calculate_profit(data, row['_id'], 
                                                    row['year'], prev, last_available),
                "Возраст компании, years": 
                    lambda row: self._get_company_age(data, row['_id'], row['year']),
                "": 
                    lambda row: self._get_value(data, row['_id'], 
                                                row['year'], field_name, prev, last_available)
            }
            method = methods.get(field_name, methods[""])
            
            postfix = (f"{('Prev' if prev > 0 else 'Next') * abs(prev)}" 
                       f" {'LA' + str(last_available) if last_available else ''}").strip()
            column_name = f"{field_name} {postfix}".strip()
            
            output[column_name] = applications.apply(method, axis=1)

        list(map(process_query, queries))
        
        return output


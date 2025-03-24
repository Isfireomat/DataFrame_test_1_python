import base64
import pandas as pd # import for eval
from pandas import DataFrame 
import numpy as np # import for eval
from df_processor import DFProcessor
from binary_files import applications_64, data_64, output_64
from queries import query

def to_dataframe(binary_file: bytes) -> DataFrame:
    return DataFrame(eval(base64.b64decode(binary_file).decode().replace("np.NaN", "np.nan")))


applications: DataFrame = to_dataframe(applications_64)
data: DataFrame = to_dataframe(data_64)
output: DataFrame = to_dataframe(output_64)

processor: DFProcessor = DFProcessor()
new_output: DataFrame = processor.get_data(data.head(), applications.head(), query)

print(output.isna() == new_output.isna())
print(output)
print(new_output)
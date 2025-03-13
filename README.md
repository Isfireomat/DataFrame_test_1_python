### Тестовое задание по Pandas
Тестовое задание представлено в файле Middle Python Developer tech task.ipynb

### Запуск
Создание venv: 
```python
python -m venv venv
```
Активировать venv
```shell
source venv/bin/activate
```
Установить poetry:
```
pip install poetry
poetry install
```
Запустить main.py в директории /app
```shell
cd app
python main.py
```

### Примечание:
В тестовом задании по всей видимости ошибка в output:
```
Первый `Возраст компании, years` `NaN`, хотя он должен быть разницей между годом регистрации (`2019-05-21`) и годом, относительно которого считаются данные (`2018`), т.е. там должно быть число `1`
```
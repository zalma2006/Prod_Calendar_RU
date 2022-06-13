# создаём производственный календарь в виде таблицы, с меткой рабочий день (work_or_not = 1)
# или выходной (work_or_not = 0)
# версии
# requests==2.27.1, bs4==0.0.1, pandas==1.4.1, python==3.9


import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import datetime

url = r'https://www.consultant.ru/law/ref/calendar/proizvodstvennye/'
site = requests.get(url, params={'q': 'requests+language:python'}, timeout=1)
site = BeautifulSoup(site.text, 'html.parser')
# получаем количество лет по ведении производственного календаря
# который можно получить с сайта, теперь не зависим от списка лет.
years = []
a = '0'
for x in site.find_all('a'):
    b = x.getText()
    if a.startswith('Производственные календари') or \
    b.startswith('20'):
        years.append(x.getText())
    a = x.getText()
    if a.startswith('Скачать производственный календарь на'):
        break

# создаем словарь с сcылками по годам для производственного
# календаря
links_year = {}
for x in site.find_all('a'):
    if x.getText() in years:
        links_year[x.getText()] = 'https://www.consultant.ru'+''.join(re.findall(
            r'href="(/\w+/\w+/\w+/\w+/\d+\w?/)"',
            str(x.parent)))
links_year = dict(sorted(links_year.items()))


def prod_cal(year):
    # переходим на страницу обработки
    url = links_year[str(year)]
    site = requests.get(url, params={'q': 'requests+language:python'}, timeout=1)
    site = BeautifulSoup(site.text, 'html.parser')
    # достаём дни и принадлежность к рабочему или не рабочему дню
    df = pd.DataFrame(columns=['days', 'work_or_not'])
    for x in site.find_all('td'):
        days = {}
        if str(x.getText()) in list(map(str, list(range(1, 32)))) or \
                str(x.getText()) in list(map(lambda x: x + '*', list(map(str, list(range(1, 32)))))) or \
                list(map(lambda x: x + '**',
                         list(map(str, list(range(1, 32)))))) or \
                list(map(lambda x: x + '***',
                         list(map(str, list(range(1, 32)))))) or \
                list(map(lambda x: x + '****',
                         list(map(str, list(range(1, 32)))))):
            try:
                days[x.getText()] = re.findall(r'"(\w+\s*\w+?)"', str(x))[0]
                df1 = pd.DataFrame({'days': list(days.keys())[0],
                                    'work_or_not': list(days.values())[0]},
                                   index=[0])
                df = pd.concat([df, df1], ignore_index=True)
            except:
                days[x.getText()] = 'workday'
                df1 = pd.DataFrame({'days': list(days.keys())[0],
                                    'work_or_not': list(days.values())[0]},
                                   index=[0])
                df = pd.concat([df, df1], ignore_index=True)

    df['days'] = df['days'].str.extract(r'(\d+)')
    df.dropna(how='any', inplace=True)
    df = df[df['work_or_not'].isin(['holiday weekend', 'weekend',
                                    'workday', 'nowork', 'preholiday'])]
    df.reset_index(drop=True, inplace=True)
    # создаём таблицу с датами для указанного года
    df_date = pd.DataFrame(pd.date_range(start=datetime.datetime(year, 1, 1),
                                         end=datetime.datetime(year, 12, 31), freq='D'), columns=['date'])
    # соединяем таблицу с годом и принадлежностью к выходным дням
    df_date['index'] = df_date.index
    df['index'] = df.index
    df_date = df_date.merge(df, how='left', left_on=['index'], right_on=['index'])
    del df, df1, df_date['index'], df_date['days']
    # меняем принадлежность рабочих и не рабочих дней
    df_date.loc[df_date[~df_date[
        'work_or_not'].isin(['workday',
                             'preholiday'])].index,
                'work_or_not'] = 0
    df_date.loc[df_date[df_date[
        'work_or_not'].isin(['workday',
                             'preholiday'])].index,
                'work_or_not'] = 1
    df_date['work_or_not'] = df_date['work_or_not'].astype(int)
    return df_date

# наконец то создаём датасет с рабочими днями, 1 = рабочий день, 0 = не рабочий день
df = pd.DataFrame()
for key, value in links_year.items():
    url = value
    site = requests.get(url, params={'q': 'requests+language:python'}, timeout=1)
    site = BeautifulSoup(site.text, 'html.parser')
# забираем год из страницы на которой находимся
    year = int(''.join(re.findall(r'\d+', str(site.title.contents))))
    df1 = prod_cal(year=year)
    df = pd.concat([df, df1])
df.reset_index(inplace=True, drop=True)


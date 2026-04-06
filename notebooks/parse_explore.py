#!/usr/bin/env python
# coding: utf-8

# In[1]:


import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from datetime import datetime
from re import search
import json
from time import sleep
from random import uniform
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import matplotlib.dates as mdates
from itertools import chain


# # Парсинг ссылок
# Вдохновившись новостями по нобелевской неделе, для парсинга я выбрал сайт Naked Science, который содержит научнопопулярные статьи и новости из мира науки. Из раздела со всеми новостями будем парсить по страницам название каждой статьи, автора, аннотацию, индекс важности (оценка автором важности исследования/открытия для науки), дату публикации, хэштеги, количество просмотров в качестве целевой переменной, и наконец ссылки.

# In[2]:


# Так как дата публикации и число просмотров имеет разные форматы, сделаем функцию для их извлечения

def parse_date(date, form='%d.%m.%Y'):
    mapper = {
        'января': '01',
        'февраля': '02',
        'марта': '03',
        'апреля': '04',
        'мая': '05',
        'июня': '06',
        'июля': '07',
        'августа': '08',
        'сентября': '09',
        'октября': '10',
        'ноября': '11',
        'декабря': '12'
    }
    if search(r'\d{1,2}\.\d{2}\.\d{4}', date):
        return date
    else:
        date = date.split()
        day = '0' + date[0] if len(date[0]) < 2 else date[0]
        return '.'.join((day, mapper[date[1]], '2025'))

def parse_views(v):
    if v[-3:] == 'тыс':
        num = v.split()[0]
        num = num.replace(',', '.')
        v = float(num) * (10 ** 3)

    return int(v)


# In[3]:


def get_info(obj):
    header = obj.find('a', attrs={'class': 'animate-custom'})
    link = header.attrs['href'].strip()

    title = header.get_text().split()
    imp_ind = float(title[-1])
    title = ' '.join(title[:-1])

    author = obj.find(lambda tag: tag.name == 'div' and tag.get('class') == ['meta-item', 'meta-item_author'])
    author = author.string.strip()

    date = obj.find('span', attrs={'class': 'echo_date'}).string
    date = parse_date(date.split(', ')[0])

    views = obj.find('span', attrs={'class': 'fvc-count'}).string
    views = parse_views(views)

    annot = obj.find('p').string.strip()

    tags = obj.find(lambda tag: tag.name == 'div' and tag.get('class') == ['terms-items', 'grid'])
    tags = tags.find_all('div', attrs={'class': 'terms-item'})
    tags = [t.get_text().replace('#', '').strip() for t in tags]

    return {
        'title': title,
        'author': author,
        'date': date,
        'imp_ind': imp_ind,
        'views': views,
        'annot': annot,
        'tags': tags,
        'link': link
    }


# In[7]:


user_ag = UserAgent()
main_link = 'https://naked-science.ru/article/page/'
attemps = 0
success = []

start, pages = 10, 500
articles, links = [], []

for i in range(start, pages + start): # начнем пасрить с 10 страницы, чтобы количество просмотров и коммментов уже немного установилось
    if i % 5 == 0 and i != start:
        print(f'processing page {i - start}/{pages}')
        with open('articles_links.json', 'w', encoding='UTF-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=4)

    for j in range(3): # Пытаемся спарсить страницу три раза, если не удалось, увеличиваем счеткчик неудачных попыток
        sleep(uniform(1.1, 1.9))
        response = requests.get(main_link + f'{i}/', headers={'User-Agent': user_ag.random})
        if not response.ok:
            print(f'\n  WARNING: page {i - start} parsing failed\n')
            continue
        else:
            success.append(i)
            attemps = 0
            soup = BeautifulSoup(response.content, 'html.parser')
            news = soup.find('div', attrs={'class': 'news-items'})
            news = news.find_all(lambda tag: tag.name == 'div' and tag.get('class') == ['news-item-left', 'with-bookmark'])
            for x in news:
                try:
                    a = get_info(x)
                    if a['link'] not in links: # Некоторые статьи могут парситься дважды, поэтому проверяем
                        articles.append(a)
                        links.append(a['link'])
                except:
                    pass
            break
    else:
        attemps += 1

    if attemps > 3:
        # Если не удалось спарсить больше трех страниц подряд, будем прерывать процесс
        print(f'\n  WARNING: Parsing was stopped\n')
        break


print(f'\n --- {len(success)}/{pages} pages have been successfully parsed ---')


# # Парсинг статей

# In[10]:


with open('articles_links.json', 'r', encoding='UTF-8') as f:
    articles = json.load(f)
len(articles)


# In[11]:


def parse_page(responce, par_sep='\n'):
    soup = BeautifulSoup(response.content, 'html.parser')
    obj = soup.find('div', attrs={'class': 'body'}).find_all('p')
    text = par_sep.join([par.get_text().strip() for par in obj])

    comments = soup.find('div', attrs={'class': 'shesht-comments-list'})
    comments = comments.find_all('div', attrs={'class': 'shesht-comment-template__content-text'})
    comments = [co.get_text().strip() for co in comments]

    return {'text': text, 'comments': comments}


# In[15]:


user_ag = UserAgent()
attemps = 0
success = []

all_pages = len(articles)
pages, links = [], [x['link'] for x in articles]

for i, link in enumerate(links):
    if i % 5 == 0 and i != 0:
        print(f'processing page {i}/{all_pages}')
        with open('texts_comments.json', 'w', encoding='UTF-8') as f:
            json.dump(pages, f, ensure_ascii=False, indent=4)

    for j in range(3): # Пытаемся спарсить страницу три раза, если не удалось, увеличиваем счеткчик неудачных попыток
        sleep(uniform(1.1, 1.9))
        response = requests.get(link, headers={'User-Agent': user_ag.random})
        if not response.ok:
            print(f'\n  WARNING: page {i} parsing failed\n')
            continue
        else:
            success.append(i)
            attemps = 0
            try:
                a = parse_page(response)
                a['link'] = link
                pages.append(a)
            except:
                pass
            break
    else:
        attemps += 1

    if attemps > 3:
        # Если не удалось спарсить больше трех страниц подряд, будем прерывать процесс
        print(f'\n  WARNING: Parsing was stopped\n')
        break


print(f'\n --- {len(success)}/{all_pages} pages have been successfully parsed ---')
with open('texts_comments.json', 'w', encoding='UTF-8') as f:
            json.dump(pages, f, ensure_ascii=False, indent=4)


# In[16]:


with open('texts_comments.json', 'r', encoding='UTF-8') as f:
    pages = json.load(f)
len(pages)


# # EDA

# In[2]:


with open('articles_links.json', 'r', encoding='UTF-8') as f:
    articles = json.load(f)

with open('texts_comments.json', 'r', encoding='UTF-8') as f:
    pages = json.load(f)

original_df = pd.merge(pd.DataFrame(articles), pd.DataFrame(pages), on='link')


# In[3]:


original_df


# In[4]:


original_df.info()


# In[5]:


df = original_df.copy()
df['date'] = pd.to_datetime(df['date'], format='%d.%m.%Y')
df = df.set_index('date')
weekly_views = df['views'].resample('W').mean() # среднее по неделям количество просмторов на одну статью


# In[6]:


fig, axes = plt.subplots(figsize=(9, 5), layout='constrained')
axes.plot(weekly_views.index, weekly_views.values)

axes.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
axes.xaxis.set_major_formatter(mdates.DateFormatter('%m-%Y'))
axes.set_xlabel('publication period')
axes.set_ylabel('Weekly average views')
axes.tick_params(axis='x', labelrotation=45)
axes.grid(True, linestyle='--', alpha=0.3)

plt.show()


# Видно, что нет явного линейного тренда, то есть число просмотров со временем устанавливается, поэтому нет смысла нормировать его на время с момента публикации. Также отчетливо прослеживается сезонность, которая скорее всего связана с какими-то событиями. Так что на основе одного лишь текста предсказание числа просмотров врядли будет точным.

# In[7]:


y = original_df['views']
x1 = original_df['imp_ind']
x2 = original_df['text'].map(lambda x: len(x))

y_lim, x2_lim = y.quantile(0.95), x2.quantile(0.99)


# In[8]:


fig, axs = plt.subplot_mosaic([['hist_x1', 'hist_x2', '.'],
                               ['scatter_1', 'scatter_2', 'hist_y']],
                              figsize=(10, 6),
                              width_ratios=(2, 2, 1),
                              height_ratios=(1, 2),
                              layout='constrained')

axs['hist_x1'].hist(x1, bins=40, edgecolor='white')
axs['hist_x2'].hist(x2, bins=40, range=(0, x2_lim), edgecolor='white')
axs['hist_y'].hist(y, bins=40, range=(0, y_lim), orientation='horizontal', edgecolor='white')
axs['scatter_1'].scatter(x1, y, s=5)
axs['scatter_2'].scatter(x2, y, s=5)

axs['scatter_1'].sharey(axs['scatter_2'])
axs['scatter_2'].sharey(axs['hist_y'])
axs['scatter_1'].sharex(axs['hist_x1'])
axs['scatter_2'].sharex(axs['hist_x2'])

axs['scatter_1'].set_ylim(0, y_lim)
axs['scatter_2'].set_ylim(0, y_lim)
axs['scatter_2'].set_xlim(0, x2_lim)

axs['scatter_1'].set_xlabel('importance index')
axs['scatter_2'].set_xlabel('len of text')
axs['hist_y'].set_ylabel('views', rotation=270, labelpad=15)

for ax in axs.values():
    ax.grid(True, linestyle='--', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

plt.show()


# Видно, что нет явной зависимости числа просмотров от размера статьи и индекса важности

# In[9]:


def groupped_stat(data, to_group, min_freq=0):
    df_gr = data.groupby(to_group, as_index=False).agg({'views': 'mean', 'title': 'count'})
    df_gr.columns = [to_group, 'mean_views', 'all_publications']
    df_gr['mean_views'] = df_gr['mean_views'].astype(int)

    return df_gr[df_gr['all_publications'] > min_freq] # Установим минимальную частоту, чтобы исключить уникальные статьи с большим числом просмотров


# In[10]:


auth_popularity = groupped_stat(original_df, 'author', min_freq=5)
auth_popularity.sort_values(by='mean_views', inplace=True, ascending=False)
auth_popularity.head(10)


# In[11]:


auth_popularity.sort_values(by='all_publications', inplace=True, ascending=False)
auth_popularity.head(10)


# Невооруженным глазом видно, что количество публикаций не гарантирует популярность авторов, но есть явно читаемые авторы

# In[12]:


df = original_df.explode('tags')
df['tags'] = df['tags'].map(lambda x: x.lower())
tags_popularity = groupped_stat(df, 'tags', min_freq=5)

# Для некоторых статей первым тэгом стоит автор, например, НИУ ВШЭ, поэтому почистим тэги
all_authors = set(original_df['author'].str.lower())
tags_popularity = tags_popularity[~ tags_popularity['tags'].isin(all_authors)].copy()


# In[13]:


tags_popularity.sort_values(by='mean_views', inplace=True, ascending=False)
tags_popularity.head(10)


# In[14]:


tags_popularity.sort_values(by='all_publications', inplace=True, ascending=False)
tags_popularity.head(10)


# С тэгами ситуация похожая, есть явно популярный тэг "оружие и техника", остальные скорее всего относятся к сериям статей

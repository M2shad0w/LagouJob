# -*- coding: utf-8 -*-
# !/usr/bin/env python

import sys
import time
import os
import requests
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
from spider.jobdetail_spider import crawl_job_detail
import pandas as pd
from util import log
from config.config import *
from bs4 import BeautifulSoup

try:
    from urllib import parse as parse
except:
    import urllib as parse
    reload(sys)
    sys.setdefaultencoding('utf-8')

headers = {
    'Accept': 'application/json',
    'Accept-Encoding': 'gzip, deflate, sdch',
    'Host': 'm.lagou.com',
    'Referer': 'https://m.lagou.com/search.html',
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 8_0 like Mac OS X) AppleWebKit/600.1.3 (KHTML, like Gecko) '
                  'Version/8.0 Mobile/12A4345d Safari/600.1.4',
    'X-Requested-With': 'XMLHttpRequest',
    'Connection': 'keep-alive'
}


def crawl_jobs(positionName, detail=False):
    """crawl the job info from lagou H5 web pages"""
    # joblist = list()
    JOB_DATA = list()
    max_page_number = get_max_pageNo(positionName)
    log.info("%s, 共有 %s 页记录, 共约 %s 记录", positionName, max_page_number, max_page_number * 15)
    cookies = get_cookies()

    for i in range(1, max_page_number + 1):
        request_url = 'https://m.lagou.com/search.json?city=%E5%85%A8%E5%9B%BD&positionName=' + parse.quote(
            positionName) + '&pageNo=' + str(i) + '&pageSize=15'

        response = requests.get(request_url, headers=headers, cookies=cookies)
        if response.status_code == 200:
            for each_item in response.json()['content']['data']['page']['result']:
                # print each_item
                JOB_DATA.append([each_item.get('positionId', 0), each_item.get('positionName', None), each_item.get('city', None),
                          each_item.get('createTime', None), each_item.get('salary', None),
                          each_item.get('companyId', 0), each_item.get('companyName', None), each_item.get('companyFullName', None)])

                if detail:
                    for _ in range(LOOP_TIMES):
                        status = crawl_job_detail(each_item['positionId'], positionName)
                        if status or _ > LOOP_TIMES:
                            break

            print('crawling page %d done...' % i)
            time.sleep(TIME_SLEEP)
        elif response.status_code == 403:
            log.error('request is forbidden by the server...')
        else:
            log.error(response.status_code)

    return JOB_DATA


def get_cookies():
    """return the cookies after your first visit"""
    headers = {
        'Host': 'm.lagou.com',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 8_0 like Mac OS X) AppleWebKit/600.1.3 (KHTML, like Gecko) Version/8.0 Mobile/12A4345d Safari/600.1.4'
    }
    url = 'https://m.lagou.com/'
    response = requests.get(url, headers=headers, timeout=10)

    return response.cookies


def get_max_pageNo(positionName):
    """return the max page number of a specific job"""
    cookies = get_cookies()
    request_url = 'https://m.lagou.com/search.json?city=%E5%85%A8%E5%9B%BD&positionName=' + parse.quote(
        positionName) + '&pageNo=1&pageSize=15'

    response = requests.get(request_url, headers=headers, cookies=cookies, timeout=10)
    log.info("获取 %s 信息 路由: %s", positionName, request_url)
    if response.status_code == 200:
        max_page_no = int(int(response.json()['content']['data']['page']['totalCount']) / 15 + 1)

        return max_page_no
    elif response.status_code == 403:
        log.error('request is forbidden by the server...')

        return 0
    else:
        log.error(response.status_code)

        return 0


def get_job_list():
    """
    获取所有工作类目
    :return:
    """
    url = 'https://www.lagou.com/'
    headers = {
        "Host": "www.lagou.com",
        "Pragma": "no-cache",
        "Referer": "https://www.lagou.com/",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
    }
    response = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(response.text, "lxml")
    text = soup.find_all('div', class_='menu_box')[0].get_text().strip()
    path = BASE_PATH + "/data/"
    try:
        f = open(path + 'job_list.txt', mode='w', encoding='UTF-8')
    except Exception, e:
        import io
        f = io.open(path + 'job_list.txt', mode='w', encoding='UTF-8')
    finally:
        f.write(text)
        f.flush()
        f.close()


def load_job_list(flush=False):
    if flush:
        get_job_list()
    job_list = []
    path = BASE_PATH + "/data/"
    f = open(path + 'job_list.txt')
    while 1:
        lines = f.readlines(100000)
        if not lines:
            break
        for line in lines:
            line = line.strip()
            if len(line) == 0:
                continue
            else:
                job_list.append(line)
    return job_list


def main():
    craw_job_list = load_job_list()
    # craw_job_list = ["人工智能"]
    path = BASE_PATH + "/data/"
    if not os.path.exists(path) or not os.path.isdir(path):
        os.makedirs(path)
    for _ in craw_job_list:
        job = crawl_jobs(_)
        col = [
            u'职位编码',
            u'职位名称',
            u'所在城市',
            u'发布日期',
            u'薪资待遇',
            u'公司编码',
            u'公司名称',
            u'公司全称']
        df = pd.DataFrame(job, columns=col)
        df.to_csv(path + _ + ".csv")

if __name__ == '__main__':
    main()

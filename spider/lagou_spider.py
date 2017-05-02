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

try:
    from urllib import parse as parse
except:
    import urllib as parse
    reload(sys)
    sys.setdefaultencoding('utf-8')


def crawl_jobs(positionName):
    """crawl the job info from lagou H5 web pages"""
    # joblist = list()
    JOB_DATA = list()
    max_page_number = get_max_pageNo(positionName)
    log.info("%s, 共有 %s 页记录, 共约 %s 记录", positionName, max_page_number, max_page_number * 15)
    cookies = get_cookies()

    for i in range(1, max_page_number + 1):
        request_url = 'https://m.lagou.com/search.json?city=%E5%85%A8%E5%9B%BD&positionName=' + parse.quote(
            positionName) + '&pageNo=' + str(i) + '&pageSize=15'
        headers = {
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Host': 'm.lagou.com',
            'Referer': 'https://m.lagou.com/search.html',
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 8_0 like Mac OS X) AppleWebKit/600.1.3 (KHTML, '
                          'like Gecko) Version/8.0 Mobile/12A4345d Safari/600.1.4',
            'X-Requested-With': 'XMLHttpRequest',
            'Connection': 'keep-alive'
        }
        response = requests.get(request_url, headers=headers, cookies=cookies)
        if response.status_code == 200:
            for each_item in response.json()['content']['data']['page']['result']:
                # job = Job(each_item['positionId'], each_item['positionName'], each_item['city'],
                #           each_item['createTime'], each_item['salary'],
                #           each_item['companyId'], each_item['companyName'], each_item['companyFullName'])
                # joblist.append(job)
                JOB_DATA.append([each_item['positionId'], each_item['positionName'], each_item['city'],
                          each_item['createTime'], each_item['salary'],
                          each_item['companyId'], each_item['companyName'], each_item['companyFullName']])
                crawl_job_detail(each_item['positionId'], positionName)
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
    response = requests.get(request_url, headers=headers, cookies=cookies, timeout=10)
    print("获取 %s 信息路由:" % positionName + request_url)
    if response.status_code == 200:
        max_page_no = int(int(response.json()['content']['data']['page']['totalCount']) / 15 + 1)

        return max_page_no
    elif response.status_code == 403:
        log.error('request is forbidden by the server...')

        return 0
    else:
        log.error(response.status_code)

        return 0


if __name__ == '__main__':
    # jobname = '人工智能'
    craw_job_list = ["数据挖掘", "ios", "后端", "架构师", "前端", "Android", "大数据", "人工智能", "java", "php", "python"]
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)) + "/data/"
    if not os.path.exists(path) or not os.path.isdir(path):
        os.makedirs(path)
    for _ in craw_job_list:
        joblist = crawl_jobs(_)
        col = [
                u'职位编码',
                u'职位名称',
                u'所在城市',
                u'发布日期',
                u'薪资待遇',
                u'公司编码',
                u'公司名称',
                u'公司全称']
        # jl = [json.dumps(_) for _ in joblist]
        df = pd.DataFrame(joblist, columns=col)
        df.to_csv(path + _ + ".csv")
        # write_excel(joblist, jobname)

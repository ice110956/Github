#!usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'Patrick'

import urllib2
from bs4 import BeautifulSoup
import re


class HtmlModel(object):
    """下载 url = http://www.ncbi.nlm.nih.gov/sites/GDSbrowser
    中指定的描述，放入同名_description.txt中"""

    def __init__(self):
        self.page = ""

    def get_page(self, page):
        """主方法"""
        self.page = page
        my_url = "http://www.ncbi.nlm.nih.gov/sites/GDSbrowser?acc=" + self.page
        try:
            my_response = urllib2.urlopen(my_url)
        except:
            print("wrong name!")
            return
        my_page = my_response.read()
        soup = BeautifulSoup(my_page)
        self.get_description(soup)

    def get_description(self, soup):
        """解析HTML页面，获取描述，写入txt"""

        des_name = []
        des_value = []
        table = soup.find('table', id='gds_details', class_='gds_panel')
        res = re.compile('(\s{2,})|(:)')
        for item in table.findAll('th', class_='not_caption'):
            des_name.append(res.sub(' ', item.text.encode('utf-8').replace('\n', '').strip()))
            item = item.find_next_sibling('td')
            des_value.append(res.sub(' ', item.text.encode('utf-8').replace('\n', '').strip()))
        f = file(self.page + '_description' + '.txt', 'w+')
        print('down description')
        for i in range(0, len(des_name)):
            text_name = des_name[i]
            text_value = des_value[i]
            text = "<"+text_name + ':' + text_value+">" + "\n\r"
            f.write(text)
        f.close()


if __name__ == '__main__':
    Model = HtmlModel()
    page = "GDS4359"
    #根据具体使用方法改变page的传入方法
    Model.get_page( page)
# -*- coding: utf-8 -*-
"""调用EpubCreater生成电子书的示例
主要演示了各种生成器的使用
"""

from Iterators import iter_page, iter_url, iter_txt
from EpubCreater import createepub


bookname = '风暴法神'
args = {}
if bookname == '北宋大表哥':
    # iter_page:通过目录页得到列表
    args = {'url': 'https://www.xxbiquge.com/26_26345/',
            'hrefre': '<a +href="/[\d_]+?/([\d_]+?\.html)" *>(第.+?)</a>',
            'titlere': '<h1>(.+?)</h1>',
            'encode': 'utf-8'}
    it = iter_page(**args)
elif bookname == '穿越原始成为巫':
    args = {'url': 'https://www.ifzxs.cc/244/244343/',
            'hrefre': '<a .* href="([\w_]+?\.html)"',
            'titlere': '<h1>(.+?)</h1>',
            'encode': 'gbk'}
    it = iter_page(**args)
elif bookname == '进化的四十六亿重奏':
    args = {'url': 'https://www.xxbiquge.com/4_4146/',
            'hrefre': '<a href="/4_4146/(\w+.html)">',
            'titlere': '<h1>(.+?)</h1>',
            'encode': 'utf-8'}
    it = iter_page(**args)
elif bookname == '异界生活助理神':
    args = {'url': 'http://www.biquge.com.tw/4_4363/',
            'hrefre': '<a href="/4_4363/(\w+.html)">',
            'encode': 'gbk'}
    it = iter_page(**args)
elif bookname == '都市奇门医圣':
    # iter_url:通过第一页得到后续列表
    args = {'url_fmt': 'http://m.wukongks.com/book/read' +
                       '?fr=shenma&bkid=56983105&crid={}',
            'url_params': (188023,),
            'paramre': 'location.href = ".*&crid=(.*)&',
            'titlere': '<div class="title">(.+?)</div>',
            'linere': '<p>(.+?)</p>',
            'encode': 'gbk'}
    it = iter_url(**args)
elif bookname == '风暴法神':
    # iter_txt:从单一txt载入全部章节
    args = {'file': 'C:/Users/hunte/Documents/baiduyun/风暴法神.TXT'}
    it = iter_txt(**args)
else:
    it = None

if it:
    destfile = 'C:/Users/hunte/Documents/epub/{}.txt'.format(bookname)
    args['_generator'] = it.__name__
    # createepub(destfile, it, meta=args)

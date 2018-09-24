# -*- coding: utf-8 -*-
"""调用EpubCreater生成电子书的示例
主要演示了各种生成器的使用
"""

from EpubCreater import createepub, getgenerator


bookname = '克拉克科幻作品集'
if bookname == '北宋大表哥':
    # iter_page:通过目录页得到列表
    args = {'_generator': 'Iterators.iter_page',
            'url': 'https://www.xxbiquge.com/26_26345/',
            'hrefre': '<a +href="/[\d_]+?/([\d_]+?\.html)" *>(第.+?)</a>',
            'titlere': '<h1>(.+?)</h1>',
            'encode': 'utf-8'}
elif bookname == '穿越原始成为巫':
    args = {'_generator': 'Iterators.iter_page',
            'url': 'https://www.ifzxs.cc/244/244343/',
            'hrefre': '<a .* href="([\w_]+?\.html)"',
            'titlere': '<h1>(.+?)</h1>',
            'encode': 'gbk'}
elif bookname == '进化的四十六亿重奏':
    args = {'_generator': 'Iterators.iter_page',
            'url': 'https://www.xxbiquge.com/4_4146/',
            'hrefre': '<a href="/4_4146/(\w+.html)">',
            'titlere': '<h1>(.+?)</h1>',
            'encode': 'utf-8'}
elif bookname == '异界生活助理神':
    args = {'_generator': 'Iterators.iter_page',
            'url': 'http://www.biquge.com.tw/4_4363/',
            'hrefre': '<a href="/4_4363/(\w+.html)">',
            'encode': 'gbk'}
elif bookname == '都市奇门医圣':
    # iter_url:通过第一页得到后续列表
    args = {'_generator': 'Iterators.iter_url',
            'url_fmt': 'http://m.wukongks.com/book/read' +
                       '?fr=shenma&bkid=56983105&crid={}',
            'url_params': (188023,),
            'paramre': 'location.href = ".*&crid=(.*)&',
            'titlere': '<div class="title">(.+?)</div>',
            'linere': '<p>(.+?)</p>',
            'encode': 'gbk'}
elif bookname == '风暴法神':
    # iter_txt:从单一txt载入全部章节
    args = {'_generator': 'Iterators.iter_txt',
            'file': 'C:/Users/hunte/Documents/baiduyun/风暴法神.TXT'}
elif bookname == '克拉克科幻作品集':
    # iter_dir:从一个目录中的所有文件载入全部章节
    args = {'_generator': 'Iterators.iter_dir',
            'homedir': 'C:/Users/hunte/Documents/baiduyun/阿瑟·C·克拉克',
            'exts': 'txt',
            'includesubdir': True}
else:
    args = None

if args:
    destfile = 'C:/Users/hunte/Documents/epub/{}.txt'.format(bookname)
    createepub(destfile, getgenerator(**args), meta=args, showlog=False)

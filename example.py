# -*- coding: utf-8 -*-
"""调用EpubCreater生成电子书的示例
主要演示了各种生成器的使用
"""

from EpubCreater import createepub, getgenerator, recreate


def _get_kwgs(bookname):
    if bookname == '北宋大表哥':
        # iter_page:通过目录页得到列表
        kwgs = {'_generator': 'Iterators.iter_page',
                'url': 'https://www.xxbiquge.com/26_26345/',
                'hrefre': '<a +href="/[\d_]+?/([\d_]+?\.html)" *>(第.+?)</a>',
                'titlere': '<h1>(.+?)</h1>',
                'encode': 'utf-8'}
    elif bookname == '穿越原始成为巫':
        kwgs = {'_generator': 'Iterators.iter_page',
                'url': 'https://www.ifzxs.cc/244/244343/',
                'hrefre': '<a .* href="([\w_]+?\.html)"',
                'titlere': '<h1>(.+?)</h1>',
                'encode': 'gbk'}
    elif bookname == '进化的四十六亿重奏':
        kwgs = {'_generator': 'Iterators.iter_page',
                'url': 'https://www.xxbiquge.com/4_4146/',
                'hrefre': '<a href="/4_4146/(\w+.html)">',
                'titlere': '<h1>(.+?)</h1>',
                'encode': 'utf-8'}
    elif bookname == '异界生活助理神':
        kwgs = {'_generator': 'Iterators.iter_page',
                'url': 'http://www.biquge.com.tw/4_4363/',
                'hrefre': '<a href="/4_4363/(\w+.html)">',
                'encode': 'gbk'}
    elif bookname == '都市奇门医圣':
        # iter_url:通过第一页得到后续列表
        kwgs = {'_generator': 'Iterators.iter_url',
                'url_fmt': 'http://m.wukongks.com/book/read' +
                           '?fr=shenma&bkid=56983105&crid={}',
                'url_params': (188023,),
                'paramre': 'location.href = ".*&crid=(.*)&',
                'titlere': '<div class="title">(.+?)</div>',
                'linere': '<p>(.+?)</p>',
                'encode': 'gbk'}
    elif bookname == '风暴法神':
        # iter_txt:从单一txt载入全部章节
        kwgs = {'_generator': 'Iterators.iter_txt',
                'file': 'C:/Users/hunte/Documents/baiduyun/风暴法神.TXT'}
    elif bookname == '克拉克科幻作品集':
        # iter_dir:从一个目录中的所有文件载入全部章节
        kwgs = {'_generator': 'Iterators.iter_dir',
                'homedir': 'C:/Users/hunte/Documents/baiduyun/阿瑟·C·克拉克',
                'exts': 'txt',
                'includesubdir': True}
    else:
        # 未曾预定义的epub
        #   可以给bookname一个epub文件名:
        #   如果它是EpubCreater.createepub生成的,将会重新生成它
        #   这在文章源的内容发生变化时很有用
        kwgs = None
    return kwgs


if __name__ == '__main__':
    import sys
    import os
    fmt_destfile = 'C:/Users/hunte/Documents/epub/{}.epub'
    # 捡出控制项
    showlog = '-nolog' not in sys.argv[1:]
    for bookname in filter(lambda s: s[0] != '-', sys.argv[1:]):
        kwgs = _get_kwgs(bookname)
        if kwgs:
            # 使用各种迭代器得到章节来生成epub
            destfile = fmt_destfile.format(bookname)
            createepub(filename=destfile,
                       source=getgenerator(**kwgs),
                       meta=kwgs,
                       showlog=showlog)
            print('{} is done.'.format(destfile))
        elif bookname[-5:] == '.epub':
            # 从epub中提取生成器信息来重生成epub
            if os.path.isfile(bookname):
                recreate(epub_file=bookname,
                         showlog=showlog)
                print('{} is done.'.format(bookname))
            else:
                raise FileNotFoundError(bookname)

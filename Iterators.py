# -*- coding: utf-8 -*-
"""EpubCreater.source常用的迭代器"""

from urllib.request import urlopen
import re
from OPF import XhtmlDoc


def default_textengile(line):
    """基本的行处理器"""
    return '  <p>　　{}</p>'.format(line.lstrip())


def autoinc(start=1, step=1):
    """
    >>> i = autoinc()
    >>> next(i)
    1
    >>> next(i)
    2
    >>> next(i)
    3
    """
    while True:
        yield start
        start += step


def htmlreader(html, filename, titlere, linere,
               textengile=default_textengile):
    """根据html流中的内容生成XhtmlDoc的title与data
    html: 一段html内容.
    titlere: 用于从html中提取文档标题的SRE_Pattern.
    linere: 用于从html中提取每一行文档的SRE_Pattern.
    textengile: 可选的行处理器,它用于对提取的每一行文档进行预处理.
        它应当是一个函数/方法,接受一段文本,返回处理后的文本.
        默认的行处理器default_textengile已经完成简单的处理
    """
    try:
        title = titlere.findall(html)[0]
    except (Exception,):
        title = ''
    try:
        lines = [textengile(line) for
                 line in linere.findall(html)]
    except (Exception,):
        lines = []
    data = ''.join(lines)
    doc = XhtmlDoc(filename, title, data)
    return doc


def iter_url(url_fmt, *url_params,
             paramre='nextpage="/(\\w+)/(\\w+).html',
             titlere='<title>(\.+)</title>',
             linere='&nbsp;&nbsp;&nbsp;&nbsp;(.+?)<',
             textengile=default_textengile,
             encode='utf-8',
             maxget=-1):
    """从指定网络页面开始循环抓取内容生成xhtml
    url_fmt/url_params: 使用它来生成每个页面的url
        在url_fmt中每个{}将被url_params中的内容替换
        可以使用{n}来指定使用第n个url_params值,n从0开始
    paramre: 一个正则表达式,它从当前页面获取下一页使用的url_params列表
        当获取到的列表不能满足url_fmt使用需要则结果迭代
        如果有多个匹配结果,使用第一组匹配的结果
    titlere: 正则表达式,用于从当前页面提取页面的标题,只使用第一个匹配的结果
    linere: 正则表达式,用于从页面内容中获取每一段内容
    textengile: 行处理器,只用于内容行
    decode: 页面的编码格式,默认按utf-8处理
    maxget: 最大迭代次数,指定小于0的值则不做限制
        当只准备获取页面序列中前面一部分时,它很有用
    >>> it = iter_url('https://www.xxbiquge.com/{}/{}.html',
    ...               '26_26345', 1466511,
    ...               titlere='<h1>(.+?)</h1>',
    ...               maxget=3)
    >>> for e in it:
    ...     print('{}({})'.format(e.title,len(e.html)))
    第一章 北宋“神鸟”(3821)
    第二章 义庄(3847)
    第三章 泔水与饥饿(3931)
    """
    params = list(url_params)
    idx = autoinc()
    param_re = re.compile(paramre)
    title_re = re.compile(titlere)
    line_re = re.compile(linere)
    while params[-1] is not None and maxget != 0:
        try:
            url = url_fmt.format(*params)
            html = urlopen(url).read().decode(encode)
            doc = htmlreader(html,
                             filename='{}.xhtml'.format(next(idx)),
                             titlere=title_re,
                             linere=line_re,
                             textengile=textengile)
            yield doc
            params = param_re.findall(html)[0]
            maxget -= 1
        except (Exception,) as err:
            print(err)
            raise StopIteration


def iter_page(url, hrefre,
              titlere='<title>(\.+?)</title>',
              linere='&nbsp;&nbsp;&nbsp;&nbsp;(.+?)<',
              textengile=default_textengile,
              encode='utf-8',
              maxget=-1):
    """从指定url中的子页面的列表来枚举每个子页面
    >>> it = iter_page('https://www.xxbiquge.com/26_26345/',
    ...                '<a +href="/[\d_]+?/([\d_]+?\.html)" *>(第.+?)</a>',
    ...                titlere='<h1>(.+?)</h1>',
    ...                maxget=3)
    >>> for e in it:
    ...     print('{}({})'.format(e.title,len(e.html)))
    第一章 北宋“神鸟”(3821)
    第二章 义庄(3847)
    第三章 泔水与饥饿(3931)
    """
    title_re = re.compile(titlere)
    line_re = re.compile(linere)
    html = urlopen(url).read().decode(encode)
    idx = autoinc()
    for href in re.compile(hrefre).findall(html):
        html = urlopen(url + href[0]).read().decode(encode)
        doc = htmlreader(html,
                         filename='{}.xhtml'.format(next(idx)),
                         titlere=title_re,
                         linere=line_re,
                         textengile=textengile)
        yield doc
        maxget -= 1
        if maxget == 0:
            break


def iter_txt(file,
             titlere='^[^ ^　].*',
             ignorebkline=True,
             textengile=default_textengile,
             encode='utf-8',
             startline=1):
    """从一个文本文件中枚举所有章节
    titlere: 用于识别章节名的正则表达式,匹配的行作为章节名,后续的行作为章节内容
    ignorebkline: 是否跳过空行,默认是不处理空行的
    textengile: 内容行处理器,它负责将每行文字进行处理以得到符合输出要求的样式
        默认的处理器是在<p>标记中以两个中文空格开始去掉左边全部空格的一行
    encode: 指出文件的编码格式
    startline: 文件开始若干行不参与处理,这个行数包括空行
    >>> file = 'C:/Users/hunte/Documents/baiduyun/阿瑟·C·克拉克/复原.TXT'
    >>> it = iter_txt(file, encode='gbk', startline=3)
    >>> for e in it:
    ...     print(e.name)
    ...     print('    title="{}"({}bytes)'.format(e.title,len(e.html)))
    1.xhtml
        title="正文 复原"(2846bytes)
    >>> file = 'C:/Users/hunte/Documents/baiduyun/风暴法神.TXT'
    >>> it = iter_txt(file)
    """
    idx = autoinc()
    title_re = re.compile(titlere)
    with open(file, 'r', encoding=encode) as f:
        doc = XhtmlDoc('{}.xhtml'.format(next(idx)))
        for line in f:
            line = line.replace('\n', '')
            if startline > 1:
                startline -= 1
            elif ignorebkline and len(line) == 0:
                pass
            elif title_re.fullmatch(line):
                if doc.title != '':
                    yield doc
                    doc = XhtmlDoc('{}.xhtml'.format(next(idx)))
                doc.title = line
            else:
                doc.data += textengile(line) + '\r\n'
    if doc.title != '':
        yield doc


if __name__ == '__main__':
    import doctest
    name = ['iter_txt',
            'autoinc',
            ]
    if len(name) == 0:
        doctest.testmod()
    else:
        for item in name:
            if item in globals():
                obj = globals()[item]
                doctest.run_docstring_examples(obj, globals(), name=item)

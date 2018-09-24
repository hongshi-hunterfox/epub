# -*- coding: utf-8 -*-
"""EpubCreater.source常用的迭代器"""

from urllib.request import urlopen
import re
import os
from OPF import XhtmlDoc


def default_textengine(line):
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


def autoname(fmt: str = '{}.xhtml'):
    """自增的名称
    >>> it_name = autoname('dir{}.xhtml')
    >>> next(it_name)
    'dir1.xhtml'
    >>> next(it_name)
    'dir2.xhtml'
    """
    idx = autoinc()
    while True:
        yield fmt.format(next(idx))


def htmltodoc(html, filename, titlere, linere,
              textengine=default_textengine):
    """根据html流中的内容生成XhtmlDoc的title与data
    html: 一段html内容.
    titlere: 用于从html中提取文档标题的SRE_Pattern.
    linere: 用于从html中提取每一行文档的SRE_Pattern.
    textengine: 可选的行处理器,它用于对提取的每一行文档进行预处理.
        它应当是一个函数/方法,接受一段文本,返回处理后的文本.
        默认的行处理器default_textengine已经完成简单的处理
    """
    try:
        title = titlere.findall(html)[0]
    except (Exception,):
        title = ''
    try:
        lines = [textengine(line) for
                 line in linere.findall(html)]
    except (Exception,):
        lines = []
    data = '\r\n'.join(lines)
    return XhtmlDoc(filename, title, data)


def filetodoc(filename: str, encode: str = 'utf-8',
              textengine=default_textengine):
    lines = []
    with open(filename, 'r', encoding=encode) as f:
        for line in f:
            lines.append(textengine(line))
    return XhtmlDoc(filename,
                    os.path.basename(filename),
                    '\r\n'.join(lines))


def dirtodoc(path: str, dirnames):
    """为一个目录生成一个文档，它的内容是一个列表,列出其中的文件（及目录)
    path: 要列表的目录,以"/"为分隔符,不以"/"结束
    dirnames: 已经注册的目录字典
        {'path1':'src1',...}
    >>> doc = dirtodoc('c:/windows/IdentityCRL',
    ...                {'c:': 'dir1.xhtml',
    ...                 'c:/windows': 'dir2.xhtml',
    ...                 'c:/windows/CSC': 'dir3.xhtml',
    ...                 'c:/windows/IdentityCRL': 'dir4.xhtml'})
    >>> doc.name
    'dir4.xhtml'
    >>> doc.title
    'IdentityCRL'
    >>> len(doc.html) > 370
    True
    """
    t_path = os.path.split(path)
    data = '  <h3>目录中的文件列表:</h3>\r\n  <ui>\r\n'
    for file in os.scandir(path):
        if file.is_file():
            data += '    <li>{}</li>\r\n'.format(file.name)
        else:
            data += '    <li>[目录]:{}</li>\r\n'.format(file.name)
    data += '  </ui>'
    return XhtmlDoc(filename=dirnames[path],
                    title=t_path[1],
                    data=data,
                    parentsrc=dirnames[t_path[0]])


def eachfiles(home, exts='*', includesubdir=True):
    """遍历目录中每一个文件名
    * 注意,文件的路径分隔符将始终强制为os.altsep
    >>> for filename in eachfiles('D:/Python/baseweb'):
    ...    filename
    'D:/Python/baseweb/app.py'
    'D:/Python/baseweb/server.py'
    'D:/Python/baseweb/__pycache__/app.cpython-36.pyc'
    """
    exts = re.compile('^{}$'.format(exts.replace('*', '.*')
                                    .replace('?', '.')
                                    .replace(',', '$|^')
                                    .replace(';', '$|^')),
                      re.I)
    home = [home]
    for path in home:
        for file in os.listdir(path):
            if file.startswith('.'):
                pass
            file = os.path.join(path, file).replace(os.sep, os.altsep)
            if os.path.isdir(file):
                if includesubdir:
                    home.append(file)
            elif exts.match(file.split('.')[-1]):
                yield file


def getfileencode(file):
    """测试得到文本类型文件可能使用的编码格式
    它不一定就是正确的
    >>> getfileencode('C:/Users/hunte/Documents/baiduyun/风暴法神.txt')
    'utf_8_sig'
    >>> getfileencode('C:/Users/hunte/Documents/baiduyun/阿瑟·C·克拉克/星.txt')
    'gb18030'
    >>> getfileencode(r'D:/Python/baseweb\\app.py')
    'utf_8'
    """
    codes = ['utf_8', 'utf_16', 'gb18030', 'big5']
    with open(file, 'rb') as f:
        b = f.read()
        for code in codes:
            try:
                b.decode(code)
                if code == 'utf_8' and b.startswith(b'\xef\xbb\xbf'):
                    code = 'utf_8_sig'
                break
            except (Exception,):
                continue
    return code


def iter_url(url_fmt, *url_params,
             paramre='nextpage="/(\\w+)/(\\w+).html',
             titlere='<title>(\.+)</title>',
             linere='&nbsp;&nbsp;&nbsp;&nbsp;(.+?)<',
             textengine=default_textengine,
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
    textengine: 行处理器,只用于内容行
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
    docname = autoname()
    param_re = re.compile(paramre)
    title_re = re.compile(titlere)
    line_re = re.compile(linere)
    while params[-1] is not None and maxget != 0:
        try:
            url = url_fmt.format(*params)
            html = urlopen(url).read().decode(encode)
            yield htmltodoc(html,
                            filename=next(docname),
                            titlere=title_re,
                            linere=line_re,
                            textengine=textengine)
            params = param_re.findall(html)[0]
            maxget -= 1
        except (Exception,):
            # 可能没有下一页，param_re.findall()[0]产生错误
            raise StopIteration


def iter_page(url, hrefre,
              titlere='<title>(\.+?)</title>',
              linere='&nbsp;&nbsp;&nbsp;&nbsp;(.+?)<',
              textengine=default_textengine,
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
    it_name = autoname()
    for href in re.compile(hrefre).findall(html):
        html = urlopen(url + href[0]).read().decode(encode)
        yield htmltodoc(html,
                        filename=next(it_name),
                        titlere=title_re,
                        linere=line_re,
                        textengine=textengine)
        maxget -= 1
        if maxget == 0:
            break


def iter_txt(file,
             titlere='^[^ ^　].*',
             ignorebkline=True,
             textengine=default_textengine,
             encode='utf-8',
             startline=1):
    """从一个文本文件中枚举所有章节
    titlere: 用于识别章节名的正则表达式,匹配的行作为章节名,后续的行作为章节内容
    ignorebkline: 是否跳过空行,默认是不处理空行的
    textengine: 内容行处理器,它负责将每行文字进行处理以得到符合输出要求的样式
        默认的处理器是在<p>标记中以两个中文空格开始去掉左边全部空格的一行
    encode: 指出文件的编码格式
    startline: 文件开始若干行不参与处理,这个行数包括空行
    >>> file = 'C:/Users/hunte/Documents/baiduyun/阿瑟·C·克拉克/复原.TXT'
    >>> it = iter_txt(file, encode='gbk', startline=3)
    >>> for e in it:
    ...     print(e.name)
    ...     print('    title="{}"({}bytes)'.format(e.title,len(e.html)))
    1.xhtml
        title="复原"(2840bytes)
    >>> file = 'C:/Users/hunte/Documents/baiduyun/风暴法神.TXT'
    >>> it = iter_txt(file)
    >>> type(it)
    <class 'generator'>
    """
    docname = autoname()
    title_re = re.compile(titlere)
    new_doc = XhtmlDoc(next(docname))
    with open(file, 'r', encoding=encode) as f:
        for line in f:
            line = line.replace('\n', '')
            if startline > 1:
                startline -= 1  # 此行被要求忽略
            elif ignorebkline and len(line) == 0:
                pass  # 空行被忽略
            elif title_re.fullmatch(line):
                # 一个新的标题行
                if new_doc.title != '':
                    yield new_doc  # 迭代出上一个文档
                    new_doc = XhtmlDoc(next(docname))
                new_doc.title = line
            else:
                new_doc.data += textengine(line) + '\r\n'
    if new_doc.data != '':
        if new_doc.title == '':
            new_doc.title = os.path.basename(file)
        if '.' in new_doc.title:
            new_doc.title = new_doc.title[0: new_doc.title.rindex('.')]
        yield new_doc  # 迭代出最后一个文档


def iter_dir(homedir, exts='*', includesubdir=False, monoinfile=False,
             titlere='^[^ ^　].*', textengine=default_textengine,
             encode=None):
    """遍历目录中的文件来迭代每个文档
    对于符合exts的每个文件,它至少迭代出一个文档
    homedir: 要遍历的目录
    exts: 只处理指定类型扩展名的文件,多个扩展名使用";"分隔,可以使用*和?通配符
    includesubdir: 是否包含子目录
        如果包含子目录,那么,每个子目录也会迭代出一个文档,其内容是该目录结构
    monoinfile: 是否为单一文件产生多层导航结构
        如果此项为True,那么将会使用titlere来产生章节,每个章节将迭代出一个文档
    textengine: 行处理器
    encode: 文件编码
        如果明确知道这些文件的编码,请指定它,这会节省很多时间
        如果包含的文件有多种编码,则不用指定,它会根据内容来判断文件编码
    """
    homedir = homedir.replace(os.sep, os.altsep)
    dirnames = {homedir: ''}
    docsrc = autoname('Text/{}.xhtml')
    dirsrc = autoname('Text/dir{}.xhtml')

    for file in eachfiles(homedir, exts, includesubdir):
        dirname = os.path.dirname(file)
        # 新目录的父节点可能也没有...直到homedir才确定有
        # a已注册,a/b/c需要先注册a/b,才可以注册a/b/c
        # 因此,可能需要迭代出多个dir_doc
        new_dirs = []
        parentname = dirname
        while parentname not in dirnames:  # 列出所有未注册的上级目录
            new_dirs.append(parentname)
            parentname = os.path.dirname(parentname)
        if len(new_dirs) > 0:  # 存在未注册的上级目录
            new_dirs.reverse()
            for each_dir in new_dirs:
                dirnames[each_dir] = next(dirsrc)
                yield dirtodoc(each_dir, dirnames)
        # 文件编码,必要时通过内容识别
        file_encode = encode
        if file_encode is None:
            file_encode = getfileencode(file)
        if monoinfile:
            # 文件内不分章节
            txt_doc = filetodoc(next(docsrc),
                                encode=file_encode,
                                textengine=textengine)
            txt_doc.name = txt_doc.name[len(homedir):]
            txt_doc.parentsrc = dirnames[dirname]
            yield txt_doc
        else:
            # 文件内分章节
            file_src = next(dirsrc)
            file_stem = os.path.basename(file)
            if '.' in file_stem:
                file_stem = file_stem[0: file_stem.rindex('.')]
            yield XhtmlDoc(filename=file_src,
                           title=file_stem,
                           data='',
                           parentsrc=dirnames[dirname])
            for each_doc in iter_txt(file=file,
                                     titlere=titlere,
                                     textengine=textengine,
                                     encode=file_encode):
                each_doc.name = next(docsrc)
                each_doc.parentsrc = file_src
                yield each_doc


if __name__ == '__main__':
    import doctest
    name = ['autoinc', 'autoname',
            'htmltodoc', 'filetodoc', 'dirtodoc',
            'eachfiles', 'getfileencode',
            'iter_txt',
            ]
    if len(name) == 0:
        doctest.testmod()
    else:
        for item in name:
            if item in globals():
                obj = globals()[item]
                doctest.run_docstring_examples(obj,
                                               globals(),
                                               name=item)

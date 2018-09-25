# -*- coding: utf-8 -*-
"""读取epub文件到一个对象(EpubObject类型)"""
import re
import zipfile


def _get_iterinfo(metas: list) -> dict:
    """分析来自文件content.opf的内容,从中得到生成器信息
    它返回一个dict
    metadict:一个meta字典"""
    iterinfo = {}
    re_source = re.compile('<meta name="source:(.+?)" content="(.*?)"')
    for item in metas:
        for k, v in re_source.findall(item):
            if v in ['True', 'False']:
                iterinfo[k] = v == 'True'
            elif v.isdigit():
                iterinfo[k] = int(v)
            elif v.isnumeric():
                iterinfo[k] = float(v)
            else:
                iterinfo[k] = v
    return iterinfo


def _get_metadata(contentdata: str) -> list:
    """分析来自文件content.opf的内容,从中得到全部的metadata数据"""
    metas = []
    contentdata = contentdata.replace('\r\n', '')
    s = re.compile(r'<metadata.*?>(.*?)</metadata>').findall(contentdata)[0]
    for e in re.compile('(<.+?>.+?</.+?>|<.+?/>)').findall(s):
        metas.append(e)
    return metas


def _readstrfile(z: zipfile.ZipFile, filename: str) -> str:
    """从一个zip文档中读出一个文件"""
    try:
        data = z.read(filename).decode(encoding='utf-8')
    except (Exception,):
        data = ''
    return data


def getsource(epub_file: str) -> dict:
    """获取epub包中content.opf文件记录的章节源信息
    它们在metadata节中以meta元素存储,name以source:xxx构成
    """
    with zipfile.ZipFile(epub_file, 'r') as z:
        metadata = _get_metadata(_readstrfile(z, 'OEBPS/content.opf'))
        args = _get_iterinfo(metadata)
    if args is None or len(args.keys()) == 0:
        args = None
    return args

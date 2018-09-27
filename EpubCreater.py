# -*- coding: utf-8 -*-
"""生成epub文件的主要模块"""

import zipfile
import pathlib
import uuid
import datetime
from OPF import Metadata, Mainfest, Spine, NavMap, ManifestItem, NavPoint
from OPF import CoreMediaType
from OPF import lineidentity as indent
from EpubReader import getsource

_F_MIMETYPE = 'application/epub+zip'
_F_CONTAINER_XML = '''\
<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" \
xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="OEBPS/content.opf" \
media-type="application/oebps-package+xml"/>
   </rootfiles>
</container>'''
_F_CONTENT_OPF = '''\
<?xml version="1.0" encoding="utf-8" ?>
<package unique-identifier="BookId" version="2.0" \
xmlns="http://www.idpf.org/2007/opf">
{metadata}
{manifest}
{spine}
  <guide>
  </guide>
</package>'''
_F_TOC_NCX = '''\
<?xml version="1.0" encoding="utf-8" ?>
<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN"
 "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">
  <ncx version="2005-1" xmlns="http://www.daisy.org/z3986/2005/ncx/">
  <head>
    <meta content="{identifier}" name="dtb:uid"/>
    <meta content="{depth}" name="dtb:depth"/>
    <meta content="0" name="dtb:totalPageCount"/>
    <meta content="0" name="dtb:maxPageNumber"/>
  </head>
  <docTitle>
    <text>{title}</text>
  </docTitle>
{navmap}
</ncx>'''


def guid(s='') -> str:
    """根据字符串计算一个相应的uuid,对于非字符串,将先进行str()处理"""
    return str(uuid.uuid3(uuid.NAMESPACE_OID, str(s)))


class EpubCreater(object):
    """epub文件生成器
    它完成对OPF.OPFObject的填充与epub文件的写入功能
    """
    __file = ''  # epub文件名
    showlog = True  # 是否在文件生成过程中显示正在生成哪个文件
    source = []  # 文档源,单个Doc以及可迭代Doc的对象
    metadata = Metadata()
    mainfest = Mainfest()
    spine = Spine()
    nav = NavMap()

    def __init__(self, **args):
        """可以通过参数来设置必要的信息以及触发文件生成动作以简化初始化工作
        可用的参数:file(self.__file),showlog
        """
        for k, v in args.items():
            if hasattr(self, k):
                self.__setattr__(k, v)
        m_item = ManifestItem('toc.ncx', CoreMediaType.dtbncx, id='ncx')
        self.mainfest.append(m_item)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        if exc_type is None:
            self.write()

    def __getcontentstr(self):
        """生成OPF文件content.opf的内容"""
        metadata = indent(self.metadata.xml)
        manifest = indent(self.mainfest.xml)
        spine = indent(self.spine.xml)
        return _F_CONTENT_OPF.format(metadata=metadata,
                                     manifest=manifest,
                                     spine=spine)

    def __gettocstr(self):
        """生成文件toc.ncx的内容"""
        return _F_TOC_NCX.format(identifier=self.metadata.identifier,
                                 depth=self.nav.depth,
                                 title=self.metadata.title,
                                 navmap=indent(self.nav.xml))

    @property
    def file(self):
        return self.__file

    @file.setter
    def file(self, file: str):
        file = self.__forceext(file, 'epub')
        self.__file = file

    @property
    def stem(self):
        return pathlib.PureWindowsPath(self.__file).stem

    @staticmethod
    def __forceext(file: str, ext: str = 'epub') -> str:
        """修改文件的扩展名"""
        if ext[0] != '.':
            ext = '.' + ext
        return pathlib.PureWindowsPath(file).with_suffix(ext).as_posix()

    def addmetagroup(self, tag, data):
        """在metadata中添加一组meta
        这组meta元素name属性的格式为"{tag}:{key}",值为str(data[key])
        可以通过这种方式保存epub文件生成使用的迭代器的相关信息,以供之后重做
        """
        for key, val in data.items():
            self.metadata.append('{}:{}'.format(tag, key),
                                 str(data[key]))

    def write(self):
        """写入epub文件
        如果有一些文件是未决的(它们先提交了doc,然后才完成内容的构建),它们不能在
        提交doc时就写入,需要建立一个列表记录这些未决doc,在适当的时候进行写入。
        简单的做法是在迭代完毕后去写入
        """
        print('Create epub file:', self.__file)
        with zipfile.ZipFile(self.__file, 'w') as z:
            def wt(name, data):
                if self.showlog:
                    print('file "{}" to zip...'.format(name))
                z.writestr(name, data, zipfile.ZIP_DEFLATED)
            for source in self.source:
                uncompleted = []
                for doc in source:
                    # doc有属性:name,title,html,parentsrc,complete
                    if doc.complete:
                        wt('OEBPS/' + doc.name, doc.html)
                    else:
                        uncompleted.append(doc)
                    m_item = ManifestItem(doc.name, CoreMediaType.xhtml)
                    self.mainfest.append(m_item)
                    self.spine.append(doc.name)
                    try:
                        path = tuple(self.nav.getpath(doc.parentsrc))
                    except (Exception,):
                        path = ()
                    self.nav.append(NavPoint(doc.title, doc.name), *path)
                for doc in uncompleted:
                    if not doc.complete:
                        pass  # 这是一个未完成的文档,还是写了吧
                    wt('OEBPS/' + doc.name, doc.html)
            wt('mimetype', _F_MIMETYPE)
            wt('META-INF/container.xml', _F_CONTAINER_XML)
            wt('OEBPS/content.opf', self.__getcontentstr())
            wt('OEBPS/toc.ncx', self.__gettocstr())


def getgenerator(_generator: str, **kwgs):
    """使用指定的参数建立相应的迭代器实例
    _generator是迭代器的名字
        格式:[package_name.][module_name]generator_name:
            Graps.LocalFile.GrapForPath
        这里BookGraps是一个外部包的名字,BookGraps则是一个迭代器,它可以是任何
        一种可以被for ... in ....调用的对象,只要迭代得到的是一个OPF.XhtmlDoc对象
    args:如果初始化迭代器需要参数,在这里给出它们
    """
    if '.' in _generator:
        path = _generator.split('.')
        module_name = path[0]
        print('module_name:', module_name)
        if module_name not in locals().keys():
            # 这是一个未导入的模块/包
            module = __import__(module_name)
            _generator = '.'.join(['module'] + path[1:])
    generator = eval(_generator)
    return generator(**kwgs)


def createepub(filename, source, showlog=True, meta=None):
    """简化的调用方式
    filename: 要生成的epub文件,带扩展名,绝对路径或相对路径
    source: 文档源迭代器实例
    showlog: 是否在生成过程中显示日志
    meta: 文档迭代器的初始化参数,这是一个dict,
        它的值应当都是字符类型或可以字符化的类型如数值
        它们的顺序有时很重要
    """
    stname = pathlib.PureWindowsPath(filename).stem
    with EpubCreater(file=filename, showlog=showlog) as f:
        f.metadata.append('title', stname)
        f.metadata.append('identifier',
                          'urn:uuid:' + guid(stname),
                          id='BookId', opf_x3ascheme='UUID')
        f.metadata.append('language', '中文')
        f.metadata.append('date', str(datetime.date.today()))
        if meta:
            f.addmetagroup('source', meta)
        f.source.append(source)


def recreate(epub_file: str, showlog=True):
    """重新生成一个epub文件"""
    kwgs = getsource(epub_file)
    if kwgs:
        createepub(filename=epub_file,
                   source=getgenerator(**kwgs),
                   showlog=showlog,
                   meta=kwgs)


if __name__ == '__main__':
    import doctest
    doctest.testmod()

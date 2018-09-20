# -*- coding: utf-8 -*-
""""""

import zipfile
import pathlib
import uuid
import datetime
from OPF import Metadata, Mainfest, Spine, NavMap, ManifestItem, NavPoint
from OPF import CoreMediaType
from OPF import lineidentity as indent

_F_MIMETYPE = 'application/epub+zip'
_F_CONTAINER_XML = '''\
<?xml version="1.0" encoding="UTF-8"?>\r
<container version="1.0" \
xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\r
    <rootfiles>\r
        <rootfile full-path="OEBPS/content.opf" \
media-type="application/oebps-package+xml"/>\r
   </rootfiles>\r
</container>'''
_F_CONTENT_OPF = '''\
<?xml version="1.0" encoding="utf-8" ?>\r
<package unique-identifier="BookId" version="2.0" \
xmlns="http://www.idpf.org/2007/opf">\r
{metadata}\r
{manifest}\r
{spine}\r
  <guide>\r
  </guide>\r
</package>'''
_F_TOC_NCX = '''\
<?xml version="1.0" encoding="utf-8" ?>\r
<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN"\r
 "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">\r
  <ncx version="2005-1" xmlns="http://www.daisy.org/z3986/2005/ncx/">\r
  <head>\r
    <meta content="{identifier}" name="dtb:uid"/>\r
    <meta content="{depth}" name="dtb:depth"/>\r
    <meta content="0" name="dtb:totalPageCount"/>\r
    <meta content="0" name="dtb:maxPageNumber"/>\r
  </head>\r
  <docTitle>\r
    <text>{title}</text>\r
  </docTitle>\r
{navmap}\r
</ncx>'''


def guid(s='') -> str:
    """
    >>> guid('a')
    'a20740b4-71b5-3b90-852e-bdb859da9fdd'
    >>> guid('')
    '596b79dc-00dd-3991-a72f-d3696c38c64f'
    >>> guid()
    '596b79dc-00dd-3991-a72f-d3696c38c64f'
    >>> guid(3) == guid('3')
    True
    """
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
        """可以通过参数来设置必要的信息以及触发文件生成动作
        这就可以简化整个生成epub文件的过程为一条语句
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
        """写入epub文件"""
        print(self.__file)
        with zipfile.ZipFile(self.__file, 'w') as z:
            def wt(name, data):
                if self.showlog:
                    print('file "{}" to zip...'.format(name))
                z.writestr(name, data, zipfile.ZIP_DEFLATED)
            wt('mimetype', _F_MIMETYPE)
            wt('META-INF/container.xml', _F_CONTAINER_XML)
            for source in self.source:
                for doc in source:
                    # doc有name,title,html三项属性
                    if doc.name is None:
                        doc.name = '{}.xhtml'.format(len(self.metadata))
                    wt('OEBPS/' + doc.name, doc.html)
                    m_item = ManifestItem(doc.name, CoreMediaType.xhtml)
                    self.mainfest.append(m_item)
                    self.spine.append(doc.name)
                    try:
                        path = tuple(self.nav.getpath(doc.name))
                    except (Exception,):
                        path = ()
                    self.nav.append(NavPoint(doc.title, doc.name), *path)
            wt('OEBPS/content.opf', self.__getcontentstr())
            wt('OEBPS/toc.ncx', self.__gettocstr())


def getgenerator(_generator: str, **args):
    """使用指定的参数建立相应的迭代器实例
    _generator是迭代器的名字
        格式:[package_name.][module_name]generator_name:
            Graps.LocalFile.GrapForPath
        这里BookGraps是一个外部包的名字,BookGraps则是一个迭代器,它可以是任何
        一种可以被for ... in ....调用的对象,只要迭代得到的是一个OPF.XhtmlDoc对象
    args:如果初始化迭代器需要参数,在这里给出它们
    """
    if '.' in _generator:
        # 未导入的
        module_name = _generator[0:_generator.rindex('.')]
        generator_name = _generator[_generator.rindex('.') + 1:]
        import importlib
        package = importlib.import_module(module_name)
        generator = getattr(package, generator_name)
    else:
        # 已经导入的
        generator = eval(_generator)
    return generator(**args)


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


if __name__ == '__main__':
    import doctest
    doctest.testmod()

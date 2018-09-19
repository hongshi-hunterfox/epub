# -*- coding: utf-8 -*-
"""OPFObject相关结构
对于一本电子出版物,
必有的:Metadata/Mainfest/Spine
可选的:NavMap(NCX)/guide
弃用的:tours
其中,guide与tours没有在此定义

CoreMediaType:
    这个枚举包含了OPF2.0所规定的核心媒体类型
    媒体类型对ManifestItem/SpineItem
Metadata/Mainfest,Spine,NavMap
    这些对象都具备方法append()
        可以使用它添加一个元素项
    都具备属性xml
        它一个xml片段,包含该对象在xml文档中的相应部分,没有前置空格与后续换行
        因此,它们没有针对xml文档的缩进,但xml片段内部有相对缩进
        为保持xml文档缩进一致,可以使用lineidentity()来为xml片段增加缩进

lineidentity()
    这个函数为字符串的每一行增加前置空格,默认是增加两个空格
"""

from collections import Iterable
import re
from enum import Enum
from errors import *

_F_XHTML = '''\
<?xml version="1.0" encoding="utf-8"?>\r
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"\r
  "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">\r
<html xmlns="http://www.w3.org/1999/xhtml">\r
<head>\r
  <title>{title}</title>\r
</head>\r
<body>\r
  <h2>{title}</h2>\r
{data}\r
</body>\r
</html>'''
_DublinCoreNames = ('title',
                    'creator',
                    'subject',
                    'description',
                    'publisher',
                    'contributor',
                    'date',
                    'type',
                    'format',
                    'identifier',
                    'source',
                    'language',
                    'relation',
                    'coverage',
                    'rights')


def hrefid(href):
    return ''.join(re.compile(r'[\w\d\-._:]+').findall(href.split('#')[0]))


def displayedname(name):
    """对名称做解码(_x??转化为相应字符)
    name: 需要做解码的名称
    >>> displayedname('dc_x3atitle')
    'dc:title'
    """
    for s_16 in set(re.compile('_x([\da-fA-F]{2})').findall(name)):
        name = name.replace('_x' + s_16, chr(int(s_16, 16)))
    return name


def lineidentity(s: str, step: int = 2) -> str:
    """将一个字符串每一行缩进指定空格"""
    fmt = ' ' * abs(step) + '{}'
    return '\n'.join(fmt.format(e) for e in s.split('\n'))


class CoreMediaType(Enum):
    """OPF核心媒体类型
    在必要的时候(如建立spine(导航/目录)前应当确认它们的实际类型
    """
    gif = 'image/gif'
    jpeg = 'image/jpeg'
    png = 'image/png'
    svg = 'image/svg+xml'
    xhtml = 'application/xhtml+xml'
    dtbook = 'application/x-dtbook+xml'
    text = 'text/css'
    xml = 'application/xml'
    oeb1doc = 'text/x-oeb1-document'
    oeb1css = 'text/x-oeb1-css'
    dtbncx = 'application/x-dtbncx+xml'


class XhtmlDoc(object):
    """一个xhtml文档
    给出title与<body>中的内容即可通过html属性得到相应的xhtml文档内容"""
    name = title = data = ''

    def __init__(self, filename: str = None, title: str = '', data: str = ''):
        self.name = filename
        self.title = title
        self.data = data

    @property
    def html(self):
        return _F_XHTML.format(title=self.title, data=self.data)


class _XML(list):
    """提供xml序列输出
    元素属性名使用_0xnn来表示一些特殊的字符"-",":"等,其中nn为该字符的hex值
    它们在访问时使用这些规则,在输出为xml时则被转义:
    >>> _XML('item', opf_x3ascheme='UUID').xml
    '<item opf:scheme="UUID" />'
    >>> _XML('dc:identifier', '978-7-5399-6291-7', id='Bookid').xml
    '<dc:identifier id="Bookid">978-7-5399-6291-7</dc:identifier>'
    >>> _XML('meta', name='mdate', content='2018-09-14').xml
    '<meta name="mdate" content="2018-09-14" />'
    >>> s = _XML('metadata')
    >>> s.append(_XML('dc:identifier', '978-7-5399-6291-7', id='Bookid'))
    >>> s.append(_XML('meta', name='Sigil version', content='0.9.7'))
    >>> s.append(_XML('meta', name='moditydate', content='2018-09-17'))
    >>> print(s.xml)
    <metadata>\r
      <dc:identifier id="Bookid">978-7-5399-6291-7</dc:identifier>\r
      <meta name="Sigil version" content="0.9.7" />\r
      <meta name="moditydate" content="2018-09-17" />\r
    </metadata>
    """
    name = ''
    _value = None
    args = {}

    def __init__(self, node_name: str, node_value=None, **args):
        super().__init__()
        self.name = node_name
        self._value = node_value
        self.args = args

    def __getattr__(self, attr):
        """
        value:保存在_value,它是xml元素对中间包含的值,只能通过初始化时指定
            扩展属性value可以在初始化时使用命名参数指定:value='aaa'
        """
        if attr == 'value':
            return self._value
        else:
            try:
                return self.args[attr]
            except (KeyError, ):
                return None

    def __setattr__(self, attr, value):
        if hasattr(self, attr):
            super().__setattr__(attr, value)
        elif attr == 'value':
            self._value = value
        else:
            self.args[attr] = value

    @property
    def propertyxml(self):
        """返回xml的属性描述段
        未对属性名与值做合法性验证及处理
        """
        xml = ''
        for k, v in self.args.items():
            if k is not None:
                k = displayedname(k)
                if hasattr(v, '__call__'):
                    v = v()  # 后期计算的值
                if v is None:
                    v = ''
                xml += ' {}="{}"'.format(k, v)
        return xml

    @property
    def xml(self):
        """返回对象的xml
        属性串先于元素生成
        """
        xml_attr = self.propertyxml
        if len(self) > 0:
            element = lineidentity('\r\n'.join(e.xml for e in self))
            text = '\r\n{}\r\n'.format(element)
        else:
            text = self._value
        if text is None:
            fmt = '<{name}{attr} />'
        else:
            fmt = '<{name}{attr}>{text}</{name}>'
        return fmt.format(name=self.name, attr=xml_attr, text=text)


class MetaItem(_XML):
    """metadata数据项(dc-metadata/x-metadata)
    dc-metadata可以不指定value,可以添加属性
    x-metadata必须指定value,且忽略添加的属性
    属性名中的':'使用"__"代替
    **如果属性名与值包含<>"等符号有可能使str()得到的xml的错误的
    >>> MetaItem('source').xml  # 核心元素可以不指定值
    '<dc:source></dc:source>'
    >>> MetaItem('identifier','978-7-5399-6291-7').xml
    '<dc:identifier>978-7-5399-6291-7</dc:identifier>'
    >>> MetaItem('identifier','123',id='BookId',opf_x3ascheme='aa').xml
    '<dc:identifier id="BookId" opf:scheme="aa">123</dc:identifier>'
    >>> MetaItem('modifydate').xml
    '<meta name="modifydate" content="" />'
    >>> MetaItem('modifydate', '2018-09-14').xml
    '<meta name="modifydate" content="2018-09-14" />'
    >>> MetaItem('modifydate', '2018-09-14', id='1234').xml
    '<meta name="modifydate" content="2018-09-14" />'
    """

    def __init__(self, node_name, node_value=None, **args):
        if node_name in _DublinCoreNames:
            # 核心元素符加"dc:"前缀
            node_name = 'dc:' + node_name
            if node_value is None:
                node_value = ''
            super().__init__(node_name, node_value, **args)
        else:
            # 非核心元素只有固定属性name/content
            super().__init__('meta',
                             name=node_name,
                             content=node_value)


class Metadata(_XML):
    """出版物元数据
    可以使用一个包含多个MetaItem实例的列表来初始化Metadata实例
    可以向Metadata实例添加一个MetaItem实例
    可以通过指定MetaItem名/值及基属性名/值向Metadata实例添加一个MetaItem实例
    >>> lmd = list()
    >>> lmd.append(MetaItem('title','bookname'))
    >>> lmd.append(MetaItem('identifier','978-7-5399-6291-7',id='ISBN'))
    >>> lmd.append(MetaItem('Sigil version','0.4.0'))
    >>> lmd.append(MetaItem('modifydate','2018-09-14'))
    >>> lmd.append(MetaItem('newtime',))
    >>> md = Metadata(lmd)  # 以列表来初始化Metadata实例
    >>> md.append(MetaItem('Sigil version','0.4.1'))  # 追加一个MetaItem实例
    >>> md.append('mdate','2018-09-14')  # 追加扩展元素
    >>> md.append('language','中文',code='gb2312')  # 追加核心元素
    >>> print(md.xml)
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" \
xmlns:opf="http://www.idpf.org/2007/opf">\r
      <dc:title>bookname</dc:title>\r
      <dc:identifier id="ISBN">978-7-5399-6291-7</dc:identifier>\r
      <meta name="Sigil version" content="0.4.0" />\r
      <meta name="modifydate" content="2018-09-14" />\r
      <meta name="newtime" content="" />\r
      <meta name="Sigil version" content="0.4.1" />\r
      <meta name="mdate" content="2018-09-14" />\r
      <dc:language code="gb2312">中文</dc:language>\r
    </metadata>
    """

    def __init__(self, datas: Iterable = None):
        """可以在实例化时添加元素:self
        datas: 一个可迭代对象或一个MetaItem实例
            如果不指定则建立一个空的Metadata实例
        """
        super().__init__('metadata',
                         xmlns_x3adc='http://purl.org/dc/elements/1.1/',
                         xmlns_x3aopf='http://www.idpf.org/2007/opf')
        if datas:
            self.append(datas)

    def append(self, key, value: str = None, **args):
        """有三种方式来向Metadata添加元素.
        1.添加一个列表:
            Metadata.append([MetaItem(...),...])
            这会将列表中所有元素逐个添加到Metadata中,
            这将是一个递归调用,只有MetaItem类型的元素才被真正的添加.
            你甚至可以在这个列表中包含另一个列表,但是:
                它们在Metadata中并不会保留原有的层次关系
        2.添加一个MetaItem元素:
            Metadata.append(MetaItem(...))
        3.添加一个未建立的MetaItem元素:
            Metadata.append(item_name,item_value,...)
            这不需要预选建立一个有效的MetaItem实例,它们将被自动建立.
        >>> t = Metadata()
        >>> t.append([MetaItem('type'),MetaItem('source')])
        >>> print(len(t))
        2
        >>> t.append(MetaItem('identifier','223355',id='BookId'))
        >>> print(len(t))
        3
        >>> t.append(MetaItem('mdate','2018-09-14'))
        >>> print(len(t))
        4
        """
        if isinstance(key, str):
            super().append(MetaItem(key, value, **args))
        elif isinstance(key, MetaItem):
            super().append(key)
        elif isinstance(key, Iterable):
            for metaitem in key:
                self.append(metaitem)


class ManifestItem(_XML):
    """manifest元素项
    它不要求属性的内容满足OPF规范的要求
    href不允许包含片断标示符,因此"#"及其后续部分将被丢弃(如果有的话)
    str()得到的将是相应的xml,无论它是否满足OPF规范的要求
    >>> ManifestItem('0.xhtml', CoreMediaType.xhtml).xml
    '<item id="0.xhtml" href="0.xhtml" media-type="application/xhtml+xml" />'
    >>> ManifestItem('1.xhtml#2233').xml
    '<item id="1.xhtml" href="1.xhtml" media-type="" />'
    >>> ManifestItem('2.xhtml',fallback='x1').xml
    '<item fallback="x1" id="2.xhtml" href="2.xhtml" media-type="" />'
    """

    def __init__(self, href: str, media_x2dtype: CoreMediaType = None, **args):
        if '#' in href:
            href = href.split('#')[0]
        if isinstance(media_x2dtype, CoreMediaType):
            media_x2dtype = media_x2dtype.value
        if 'id' not in args.keys():
            args['id'] = hrefid(href)
        args['href'] = href
        args['media_x2dtype'] = media_x2dtype
        super().__init__('item', **args)


class Mainfest(_XML):
    """文件清单
    每个项均为一个ManifestItem实例
    >>> mainfest = Mainfest()
    >>> mainfest.append(ManifestItem('1.xhtml', CoreMediaType.xhtml))
    >>> mainfest.append(ManifestItem('2.xhtml', CoreMediaType.xhtml))
    >>> mainfest.append(ManifestItem('3.xhtml', CoreMediaType.xhtml))
    >>> print(mainfest.xml)
    <manifest>\r
      <item id="1.xhtml" href="1.xhtml" media-type="application/xhtml+xml" />\r
      <item id="2.xhtml" href="2.xhtml" media-type="application/xhtml+xml" />\r
      <item id="3.xhtml" href="3.xhtml" media-type="application/xhtml+xml" />\r
    </manifest>
    """

    def __init__(self):
        super().__init__('manifest')

    def append(self, maniitem: ManifestItem):
        if isinstance(maniitem, ManifestItem):
            self.checkfillback(maniitem)
            super().append(maniitem)
        else:
            raise TypeError('\'maniitem\' object is not ManifestItem')

    def lookupid(self, findid: str) -> ManifestItem:
        """寻找指定id的元素"""
        for maniitem in self:
            if maniitem.id == findid:
                return maniitem

    def lookuphref(self, href: str) -> ManifestItem:
        """寻找指定href的元素"""
        for maniitem in self:
            if maniitem.href == href:
                return maniitem

    def checkfillback(self,
                      maniitem: ManifestItem,
                      checklist: list = None):
        """检查一个ManifestItem的候选链是否合法
            候选链不能形成循环引用,并且必需终止于一个OPF核心媒体类型.
            当item的候选链不合法时,将抛出相应的错误.
            如果没有错误抛出,那么,恭喜你,它是好的.
        item: 一个包含于此对象中的ManifestItem实例的引用
        checklist: 列出合法的媒体类型.
            默认为所有核心媒体类型均为合法的,如果要限定此候选链只能是某一部分,
            比如Spine中只能包含特定的一部分媒体类型,可以使用一个列表来指出它们:
                [CoreMediaType.xhtml,  ...]
        """
        if checklist is None or len(checklist) == 0:
            checklist = [e.value for e in CoreMediaType]
        hrefs = [maniitem.href]
        if maniitem.fallback:
            backer = self.lookupid(maniitem.fallback)
            while backer.media_type not in checklist:
                hrefs.append(backer.href)
                if backer.href in hrefs[:-1]:
                    raise CircularReference(hrefs)
                if not hasattr(backer, 'fallback'):
                    raise EndNotCMT(hrefs)
                backer = self.lookupid(backer.fallback)
                if backer is None:
                    raise EndToEmpty(hrefs)
        elif maniitem.media_x2dtype not in checklist:
            hrefs.append(maniitem.media_x2dtype)
            raise EndNotCMT(hrefs + checklist)


class SpineItem(_XML):
    """书脊项
    linear默认为yes,不指定或指定为yes/no之外的内容时将处理为yes
    >>> SpineItem('page1').xml
    '<itemref idref="page1" linear="yes" />'
    >>> SpineItem('page1','no').xml
    '<itemref idref="page1" linear="no" />'
    >>> SpineItem('page1','wtf?').xml
    '<itemref idref="page1" linear="yes" />'
    """

    def __init__(self, idref: str, linear: str = 'yes'):
        if linear not in ('yes', 'no'):
            linear = 'yes'
        super().__init__('itemref', idref=idref, linear=linear)


class Spine(_XML):
    """书脊
    书脊决定了文档的阅读顺序,它包含的每一项的顺序很重要
    它通过idref引用ManifestItem.id,书脊中每一个项的idref不能重复
    对应的ManifestItem应当满足下列条件之一:
        media_type是xhtml/dtbook/oeb1doc之一
        fillback链结束于xhtml/dtbook/oeb1doc之一
    >>> spine = Spine()
    >>> spine.append('Text/1.xhtml')
    >>> print(spine.xml)
    <spine toc="ncx">\r
      <itemref idref="Text1.xhtml" linear="yes" />\r
    </spine>
    >>> spine = Spine(Mainfest())
    >>> spine.mainfest.append(ManifestItem('1.xhtml',CoreMediaType.xhtml))
    >>> spine.mainfest.append(ManifestItem('2.xhtml',CoreMediaType.xhtml))
    >>> spine.mainfest.append(ManifestItem('3.xhtml',CoreMediaType.xhtml))
    >>> spine.append('3.xhtml')
    >>> spine.append('1.xhtml')
    >>> spine.append('2.xhtml')
    >>> print(spine.xml)
    <spine toc="ncx">\r
      <itemref idref="3.xhtml" linear="yes" />\r
      <itemref idref="1.xhtml" linear="yes" />\r
      <itemref idref="2.xhtml" linear="yes" />\r
    </spine>
    >>> spine = Spine(Mainfest())
    >>> spine.mainfest.append(ManifestItem('1.xhtml',CoreMediaType.xhtml))
    >>> spine.mainfest.append(ManifestItem('2.xhtml',CoreMediaType.xhtml))
    >>> spine.mainfest.append(ManifestItem('3.xhtml',CoreMediaType.xhtml))
    >>> spine.append('Text/1.xhtml') # 引用不存在的项产生错误
    Traceback (most recent call last):
    errors.QuotedNothing: Text/1.xhtml
    >>> spine = Spine(Mainfest())
    >>> spine.mainfest.append(ManifestItem('1.xhtml',CoreMediaType.xhtml))
    >>> spine.mainfest.append(ManifestItem('2.xhtml',CoreMediaType.xhtml))
    >>> spine.mainfest.append(ManifestItem('3.xhtml',CoreMediaType.xhtml))
    >>> spine.append('1.xhtml')
    >>> spine.append('1.xhtml')  #重复引用产生错误
    Traceback (most recent call last):
    errors.QuotedRepeat: 1.xhtml
    """
    mainfest = None

    def __init__(self, mainfest: Mainfest = None):
        super().__init__('spine', toc='ncx')
        if isinstance(mainfest, Mainfest):
            self.mainfest = mainfest

    def append(self, href: str):
        if self.mainfest:
            maniitem = self.mainfest.lookuphref(href)
            if maniitem is None:
                raise QuotedNothing(href)
            types = [CoreMediaType.xhtml.value,
                     CoreMediaType.dtbook.value,
                     CoreMediaType.oeb1doc.value]
            self.mainfest.checkfillback(maniitem, types)
            idref = maniitem.id
        else:
            idref = hrefid(href)
        for e in self:
            if e.idref == idref:
                raise QuotedRepeat(idref)
        super().append(SpineItem(idref))


class NavPoint(_XML):
    """Navigation Center eXtended,即目录
    ncx具备多层结构,顺序(order)是重要的
    src允许使用片断标示符#...来指向某个文档中特定位置
    >>> ncx = NavPoint('第一章 突如其来的就这行发生了','p1')
    >>> ncx.append(NavPoint('第一节 谁都不要拦着我','p2'))
    >>> ncx.reorder()
    >>> print(ncx.xml) #doctest: +ELLIPSIS
    <navPoint id="p1" playOrder="1">\r
      <navLabel>\r
        <text>第一章 突如其来的就这行发生了</text>\r
      </navLabel>\r
      <content src="p1" />\r
      <navPoint id="p2" playOrder="2">\r
        <navLabel>\r
          <text>第一节 谁都不要拦着我</text>\r
        </navLabel>\r
        <content src="p2" />\r
      </navPoint>\r
    </navPoint>
    >>> print(ncx.depth)
    2
    """
    __order = 0
    _src = ''

    def __init__(self, label='', src=''):
        super().__init__('navPoint',
                         id=hrefid(src),
                         playOrder=lambda: NavPoint.nextorder())
        self._src = src
        node = _XML('navLabel')
        node.append(_XML('text', label))
        super().append(node)
        super().append(_XML('content', src=src))

    def append(self, navpoint: object, *path):
        if not isinstance(navpoint, NavPoint):
            raise TypeError('\'navpoint\' object is not NavPoint')
        if len(path) == 0:
            super().append(navpoint)
        else:
            node = self.getnode(*path)
            node.append(navpoint)

    def getnode(self, *path):
        """在多层中按指定路径找到特定的节点
        path: 一个列表,按顺序列出每一层的src
            如果不指定path,则返回自己
        """
        nodes = [self]
        for src in path:
            for e in nodes[-1]:
                if isinstance(e, NavPoint):
                    if e._src == src:
                        nodes.append(e)
                        break
        return nodes[-1]

    @property
    def depth(self):
        """这个多层结构的最大深度"""
        try:
            element = filter(lambda x: isinstance(x, NavPoint), self)
            depth = max(e.depth for e in element) + 1
        except (ValueError,):
            depth = 1
        return depth

    @classmethod
    def reorder(cls):
        """使所有节点order从1开始自增(应当在调用顶层xml之前调用它)"""
        cls.__order = 0

    @classmethod
    def nextorder(cls):
        cls.__order += 1
        return cls.__order


class NavMap(NavPoint):
    """NavMap是NcxItem的顶层封装,额外实现xml方法
    >>> nav = NavMap()
    >>> nav.append(NavPoint('第一部 突如其来','p1'))
    >>> nav.append(NavPoint('第二部 今天没吃药','p5'))
    >>> nav.append(NavPoint('第一章 谁都不要拦着我','p2'),'p1')
    >>> nav.append(NavPoint('第二章 万万没有想到','p4'),'p1')
    >>> nav.append(NavPoint('第一节 狂燥的布莱尔','p3'),'p1','p2')
    >>> print(nav.xml)
    <navMap>\r
      <navPoint id="p1" playOrder="1">\r
        <navLabel>\r
          <text>第一部 突如其来</text>\r
        </navLabel>\r
        <content src="p1" />\r
        <navPoint id="p2" playOrder="2">\r
          <navLabel>\r
            <text>第一章 谁都不要拦着我</text>\r
          </navLabel>\r
          <content src="p2" />\r
          <navPoint id="p3" playOrder="3">\r
            <navLabel>\r
              <text>第一节 狂燥的布莱尔</text>\r
            </navLabel>\r
            <content src="p3" />\r
          </navPoint>\r
        </navPoint>\r
        <navPoint id="p4" playOrder="4">\r
          <navLabel>\r
            <text>第二章 万万没有想到</text>\r
          </navLabel>\r
          <content src="p4" />\r
        </navPoint>\r
      </navPoint>\r
      <navPoint id="p5" playOrder="5">\r
        <navLabel>\r
          <text>第二部 今天没吃药</text>\r
        </navLabel>\r
        <content src="p5" />\r
      </navPoint>\r
    </navMap>
    >>> print(nav.depth)
    3
    """

    def __init__(self):
        super().__init__()
        self.name = 'navMap'
        self.args = {}
        self.clear()

    @property
    def depth(self):
        return super().depth - 1

    @property
    def xml(self):
        self.reorder()
        xml = super().xml
        self.reorder()
        return xml


if __name__ == '__main__':
    import doctest
    doctest.testmod()

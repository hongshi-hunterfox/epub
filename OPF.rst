================================
OPF.py
================================
中定义了各种OPF object的主要结构。

displayedname(name: str) -> str
--------------------------------
在xml标签中,一些Tag/Property是可以包含一些特殊字符如":","-"等，这些名称映射到对
象中时,需要进行转码,在本项目中,使用"_xhh"来表示一些不可出现在对象属性名中的字符,
如使用"_x3a"代替":",而函数 ``displayedname`` 可以将这种被替代的部分还原为相应的
特殊字符.

::

    >>> displayedname('dc_x3atitle')
    'dc:title'

lineidentity(s: str, step: int = 2) -> str:
--------------------------------------------
函数 ``lineidentity`` 用于次一个多行文本的每一行添加一段前置的空格以形成缩进,这
在美化xml文档时相当有用.

::

    >>> lineidentity('a\\nb')
    '  a\n  b'

    >>> lineidentity('a\\nb', 3)
    '   a\n   b'

class CoreMediaType
---------------------
它是一个枚举类,列出了所有在OPF 2.0中定义的核心媒体类型.使用它的主要理由是可以避
免输入时因为手滑而引发的错误.

class XhtmlDoc
-----------------
这是 ``application/xhtml+xml`` 类型文档的处理对象,它封装了xhtml文档中与内容无关
的部分,因此,只需要填充它的 ``title(str)`` 与 ``data(html块)`` 即可通过html属性
得到一个符合要求的xhtml文档.

为了它能写入到epub中,还需要为它指定 ``name`` ,必要时还需要指定 ``parentsrc`` .

为了能使文档延后完成内容的构建,可以指定``complete``为``Flase``,并在完成后内容后
指定``complete``为``True``.

这些属性都可以在建立实例时通过参数传递给这个类的``__init__``,其中,``name``属性对
应的是命名参数``filename``.

class _XML
------------
这是所有xml节点对应的对象共有的基类,基于xml节点的特性,它有``name``/``value``属性,
也可以增加各种自定义属性.一个xml节点可以包含另一个(或多个)xml节点,因此,它是基于
``list``派生的类.

一个经典的xml节点格式形如``<tag>value</tag>``,这个类的``__init__``使用接受命名参
数``node_name``与``node_value``与``tag``和``value``对应.

在__init__中还可以自由传递其它的属性,以形成
``<tag property_name="property_value"...>value</tag>``这样的形式,如果xml属性名包
含特殊字符,则需要转码为_xhh的形式,同时,属性名中本身就含有"_x"也应当对"x"做转码为
"_x78",如xml节点属性``range_xsize``需要转码为``range__x78size``.

通过访问xml属性可以得到这个节点及其可能内部包含的节点对应的xml串.

::

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


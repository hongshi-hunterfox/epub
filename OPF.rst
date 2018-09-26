================================
OPF.py
================================
中定义了各种OPF object的主要结构。

displayedname(name: str) -> str
--------------------------------
在xml标签中,一些Tag/Property是可以包含一些特殊字符如":","-"等，这些名称映射到对
象中时,需要进行转码,在本项目中,使用"_xhh"来表示一些不可出现在对象属性名中的字符,
如使用"_x3a"代替":",而函数 ``displayedname()`` 可以将这种被替代的部分还原为相应的
特殊字符.

::

    >>> displayedname('dc_x3atitle')
    'dc:title'

lineidentity(s: str, step: int = 2) -> str:
--------------------------------------------
函数 ``lineidentity()`` 用于次一个多行文本的每一行添加一段前置的空格以形成缩进,这
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

为了能使文档延后完成内容的构建,可以指定 ``complete`` 为 ``Flase`` ,并在完成后内
容后指定 ``complete`` 为 ``True`` .

这些属性都可以在建立实例时通过参数传递给这个类的 ``__init__`` ,其中, ``name`` 属
性对应的是命名参数 ``filename`` .

class _XML
------------
这是所有xml节点对应的对象共有的基类,基于xml节点的特性,它有 ``name`` / ``value``
属性,也可以增加各种自定义属性.一个xml节点可以包含另一个(或多个)xml节点,因此,它是
基于 ``list`` 派生的类.

一个经典的xml节点格式形如 ``<tag>value</tag>`` ,这个类的 ``__init__`` 使用接受命
名参数 ``node_name`` 与 ``node_value`` 来和xml节点的 ``tag`` 与 ``value`` 对应.

    如果一个xml节点没有value也没有子项,那么,它可能简化为 ``<tag />`` 这样的形式.

在__init__中还可以自由传递其它的属性,以形成
``<tag property_name="property_value"...>value</tag>`` 这样的形式,如果xml属性名包
含特殊字符,则需要转码为_xhh的形式,同时,属性名中本身就含有"_x"也应当对"x"做转码为
"_x78",如xml节点属性 ``range_xsize`` 需要转码为 ``range__x78size`` .

需要注意,如果属性的名/值含有"<"或">"这样的符号,为了不影响xml格式,它们需要转码.

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


class MetaItem
----------------------
它派生自 ``_XML`` .在OPF中,它对应于opf文件(一般名为 ``content.opf`` )中
``metadata`` 元素下的两类元素:核心元数据( ``dc-metadata`` )与扩展元数据(
``x-metadata`` ).

对于核心元数据,指定node_name(tag)时不需要添加'dc:'前缀,当识别出节点是核心元数据
项时,会自动添加'dc:'前缀.

::

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


class Metadata
--------------------
出版物元数据对象,它派生自 ``_XML`` .它对应opf文件中 ``metadata`` 元素.

它提供了 ``append()`` 方法用于向其中添加 ``MetaItem`` 实例.

``append`` 方法有三种使用方式:

1.添加一个列表
  ``Metadata.append([MetaItem(...),...])``
  这会将列表中所有元素逐个添加到Metadata中,
  这将是一个递归调用,只有MetaItem类型的元素才被真正的添加.
  你甚至可以在这个列表中包含另一个列表,但是:
    它们在Metadata中并不会保留原有的层次关系

2.添加一个MetaItem元素:
  ``Metadata.append(MetaItem(...))``
3.添加一个未建立的MetaItem元素:
  ``Metadata.append(item_name,item_value,...)``
  这不需要预选建立一个有效的MetaItem实例,它们将被自动建立.

::

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


class ManifestItem
----------------------
manifest元素项对应的对象,派生自 ``_XML`` .对应于OPF中opf文件内manifest元素中的每
item元素.

在OPF 2.0规范中要求此元素应当具备 ``id/href/media-type`` 三个必备属性,以及一些可
选属性,但在这个类中并没有做太多的限制.例外的属性会被接受并在xml中做相应的输出.

id属性如果缺失,会使用href值进行计算来得到一个可用的值.

media-type属性(在 ``__init__`` 中命名参数名为 ``media_x2dtype`` ) 如果缺失,则会
使用输出 ''.

::

    >>> ManifestItem('0.xhtml', CoreMediaType.xhtml).xml
    '<item id="0.xhtml" href="0.xhtml" media-type="application/xhtml+xml" />'

    >>> ManifestItem('1.xhtml#2233').xml
    '<item id="1.xhtml" href="1.xhtml" media-type="" />'

    >>> ManifestItem('2.xhtml',fallback='x1').xml
    '<item fallback="x1" id="2.xhtml" href="2.xhtml" media-type="" />'


class Mainfest
------------------
派生自 ``_XML`` .文件清单中包含可能被阅读的每一个文件的的列表( ``ManifestItem`` )
实例.

它提供了 ``append()`` 方法来向其它添加文件项.此方法只接受单个 ``ManifestItem``
实例为参数.

::

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


它提供了在其中寻找一个文件项的两个方法:

- ``lookupid()`` 寻找id属性与指定值一致的item

- ``lookuphref()`` 寻找href属性与指定值一致的item


class Spine
-----------------
书脊项,派生自 ``_XML`` .

书脊在OPF 2.0中并不是必需的,但它是很常用的,一般的作用是形成目录索引.

书脊决定了文档的阅读顺序,它包含的每一项的顺序很重要.同时它也是一个多层结构.

只有存在于 ``Mainfest`` 中的 ``ManifestItem`` 实例才可以有对应的 ``Spine`` 实例.
它们之间的关系为 ``ManifestItem.id ==  Spine.idref``.

同时,相应的 ``ManifestItem.media_type`` 要么是xhtml/dtbook/oeb1doc类型之一,要么
它的fillback链结束于这些类型之一.

为了完成这个验证,它持有 ``Mainfest`` 实例的一个引用.这通过向 ``__init__`` 向它
传递 ::

    >>> spine = Spine(Mainfest())

如果没有给它这个副本,那么,它将在添加子项不会做相应的验证.







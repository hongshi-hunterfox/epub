# 生成与维护epub文档的工具

## createepub()
使用`createepub`来生成一个epub文档.
### 语法
`createepub(filename, source[, showlog=True][, meta=None])`<br>
**必需参数:**<br>
- `filename`<br>
一个字符串,它是将要生成的epub文档名,如果它已经存在,新的文档将履盖它.
- `source`<br>
是一个可以被for迭代的对象,它的每一项是一个OPF.XhtmlDoc对象.<br>
**可选参数:**<br>
- `showlog`<br>
是一个逻辑值,它指出是否在控制台上输出生成过程的简要信息,默认为True.
- `meta`<br>
是一个字典,它包含了创建生成器的所有参数,默认为`None`.
这个字典中的信息将被记录到epub文档中,它们将在重新生成这个epub文档时被使用.
### 示例:
```
    from Iterators import iter_txt
    createepub(filename=bookname,
               source=iter_txt(file='mybook.txt'),
               showlog=False)
```
我们可以使用`getgenerator()`来完成建立生成器实例的工作,
它使我们可以重用meta这个字典:
```
    bookname='mybook.epub'
    # 生成器iter_txt最少只需要指定参数file
    kwgs = {'_generator': 'Iterators.iter_txt',
            'file': 'mybook.txt'}
    iter = getgenerator(**kwgs)
    createepub(filename=bookname,
               source=iter,
               showlog=False,
               meta=kwgs)
```
这样做的好处是,将我们修改了mybook.txt中的内容时,
可以使用`recreate()`来更简单的重新生成这个epub文档，
因为它会使用记录到epub文档中的meta字典重新建立相应的生成器.

## getgenerator()
以指定参数创建一个生成器实例
### 语法
`recreate(_generator, **kwgs)`
**必需参数:**<br>
`_generator`<br>
一个字符串,迭代器的名字,格式为`[package_name.][module_name.]generator_name`
**可选参数:**<br>
`args`<br>
如果初始化迭代器需要参数以指名参数的形式传递它们
### 示例
```
    iter = getgenerator(_generator='Iterators.iter_txt',
                        file='mybook.txt')
```
或者如`createepub`中示例那样:
```
    kwgs = {'_generator': 'Iterators.iter_txt',
            'file': 'mybook.txt'}
    iter = getgenerator(**kwgs)
```

## recreate()
可以使用`recreate`来重新生成之前使用`createepub`生成的epub文档.
这种方式比`createepub`需要的参数更少.
### 语法
`recreate(epub_file: str, showlog=True)`<br>
**必需参数:**<br>
- `epub_file`<br>
指出要重新生成的epub文件.<br>
**可选参数:**<br>
- `showlog`<br>
的用法与`createepub`中一样.
### 示例
```
    recreate('mybook.epub')
```
当mybook.epub是使用`createepub`生成的,
并且通过参数`meta`传递了完整有效的生成器信息时,
它就可以再次重新生成这个文档了.



## 生成器
`createepub`第二个参数需要指定一个生成器,
这个生成器应当是可以被`for`枚举/迭代的,
每次迭代得到的应当是一个有效的XhtmlDoc实例(它在OPF模块中定义).

在Iterators模块中，提供了
- iter_page
- iter_url
- iter_txt
- iter_dir
- iter_files

这些比较常用的生成器,如果这些不能满足使用需要,
可以自定义一个生成器,它的基本写法如下：
```
    def my_iter():
        for ...:
          yield XhtmlDoc(...)
```
*必要时，我们可以使用一些爬虫框架来进行迭代.*

## XhtmlDoc
它用于传递一个xhtml文档的内容.<br>
**核心属性:**<br>
- `filename`<br>
是它在epub包中的文件名,
需要在生成器中使用一些方法来确保每个生成的XhtmlDoc实例都使用不同的filename.  
- `title`<br>
文档的title，它会使用在xhml文档的head.title与body.h1中  
- `data`<br>
是文档的内容,它应当是一段html标记文本,它将插入到body.h1之后.<br>
**扩展属性:**<br>
- `parentsrc`默认值为`''`<br>
为了在epub中实现多层的导航,可以将parentsrc指定为相应的上级文档的filename.
- `complete`默认值为`True`<br>
用于先迭代出文档,之后再完成它的内容.因为一些情况下,
我们可能需要先生成一个文档供其它文档去引用为上级文档,
但出于效率考虑,它的内容我们可能需要在完成这些下级文档的过程中逐步完成，
我们可以先产生这个文档,但指定它的complete=False,迭代出它,
在完成它的全部内容后,再设置complete=True.<br>
需要注意,如果没有将complete设置为True,这些未完成的文档有可能不会被写入到epub中,
那么epub文档阅读器有可能提示这是一个无效的epub文档.
- `translator`默认为`None`<br>
html翻译器.<br>
如果要生产复杂的页面内容,比如对代码进行语法着色等,可以指定一个翻译器,
它应当能接受一个参数(`XhtmlDoc.data`),并返回等价的html代码.<br>
一般情况下,我们可以直接生产html代码块作为`XhtmlDoc.data`的值,
此时我们无须关注这个属性.

## default_textengine()
基本的行处理器,它只是简单的将每一行作为一个段落,前置两个全角空格后放入到`<p>`标记对中.

## autoname()
它可以迭代出不重复的xhtml文档名.可以在生成器中使用它为每个XhtmlDoc实例生成一个不重复的名称.<br>
如果有多个生成器共同工作,这将是很有必要的.
### 语法
`autoname([fmt])`<br>
fmt默认值为`'{}.xhtml'`.其中的{}部分将在每次迭代时替换为一个自增的数.

## htmltodoc()
根据html流中的内容生成XhtmlDoc的title与data.
### 语法
`htmltodoc(html, filename, titlere, linere[, textengine])`<br>
**参数说明**<br>
- html<br>
    一段html内容
- filename<br>
    用于从html中提取文档标题的正则表达式(SRE_Pattern).
- titlere<br>
    用于从html中提取每一行文档的(SRE_Pattern).
- linere(可选的)<br>
    行处理器,它用于对提取的每一行文档进行预处理.它应当是一个函数/方法,
    接受一段文本,返回处理后的文本.<br>
    默认的行处理器default_textengine已经完成简单的处理

## filetodoc()
以一个txt文档的内容生成一个XhtmlDoc文档
### 语法
`filetodoc(filename[, encode][, textengine])`

## dirtodoc()
将指定目录中的文件做成一个列表,以此生成一个XhtmlDoc对象
### 语法
`dirtodoc(path,dirnames)`
**参数说明**<br>
- path<br>
    指出要列表的目录,要求使用`/`作为路径分隔符.<br>
- dirnames<br>
    一个已经注册的目录字典,注册目录为key，对应的文件名为value
### 示例
```
    doc = dirtodoc('c:/windows/IdentityCRL',
                   {'c:': 'dir1.xhtml',
                    'c:/windows': 'dir2.xhtml',
                    'c:/windows/CSC': 'dir3.xhtml',
                    'c:/windows/IdentityCRL': 'dir4.xhtml'})
```

## getfileencode()
测试得到文本类型文件可能使用的编码格式(仅限中文).
它并不是总是正确的,而且也比较浪费时间.
因此不是必要的时候不要使用它.
### 语法
`getfileencode(file)`
### 示例
```
    ?getfileencode('C:/Documents/nodes/2006_03_17.txt')
    ?getfileencode(''D:/Python/baseweb\\core\\logon.py')
```

# 生成与维护epub文档的工具

## createepub()
使用createepub来生成一个epub文档.

createepub(filename, source, ...)

必需参数:
- filename
是一个字符串,它是将要生成的epub文档名,如果它已经存在,新的文档新履盖它.
- source是一个可以被for的对象,它的每一项是一个OPF.XhtmlDoc对象
可选参数:
- showlog是一个逻辑值,它指出是否在控制台上输出生成过程的简要信息,默认为True
- meta是一个字典,它包含了创建生成器的所有参数,默认为None.
这个字典中的信息将被记录到epub文档中,它们将在重新生成这个epub文档时被使用

示例:
from Iterators import iter_txt
createepub(filename=bookname,
           source=iter_txt(file='mybook.txt'),
           showlog=False)
我们可以使用getgenerator()来完成建立生成器实例的工作,它使我们可以重复使用meta这个字典.
bookname='mybook.epub'
kwgs = {'_generator': 'Iterators.iter_txt',
        'file': 'mybook.txt'}
iter = getgenerator(**kwgs)
createepub(filename=bookname,
           source=iter,
           showlog=False,
           meta=kwgs)
这样做的好处是,将我们修改了mybook.txt中的内容时,可以使用recreate()来更简单的重新生成这个epub文档:
recreate('mybook.epub')

在Iterators模块中，已经提供了iter_page, iter_url, iter_txt, iter_dir, iter_files这些比较常用的生成器,如果这些不能满足使用需要,可以自定义一个生成器,它最简单的形式是：
def my_iter():
    for ...:
      yield XhtmlDoc(...)
这里有一个XhtmlDoc类,它在OPF模块中定义.
它的核心属性有:
filename是它在epub包中的文件名,需要在生成器中使用一些方法来确保每个生成的XhtmlDoc实例都使用不同的filename.
title是文档的title，它会使用在xhml文档的head.title与body.h1中
data:是文档的内容,它应当是一段html标记文本,它将插入到body.h1之后
为了在epub中实现多层的导航,可以通过parentsrc为XhtmlDoc实例指定相应的上级文档的filename.
而有些文档可能
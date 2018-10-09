# -*- coding: utf-8 -*-
"""主测试文件
使用doctest为核心,使用rst文档中的测试用例进行测试
"""

from os import listdir
from os.path import splitext, isfile
import sys
import doctest


def getstem(filename: str) ->str:
    """得到文件根名"""
    return splitext(filename)[0]


def getext(filename: str) ->str:
    """得到文件扩展名"""
    return splitext(filename)[1]


def forceext(filename: str, ext: str) ->str:
    """替换文件的扩展名"""
    return '{}.{}'.format(getstem(filename), ext)


def get_rsts() -> list:
    """得到此目录下所有rst文件的列表"""
    rsts = []
    for file in listdir('.'):
        if getext(file) == '.rst':
            rsts.append(file)
    return rsts


def non_private(name):
    """过滤器,判断属性/方法是否是私有的"""
    return name[0] != '_'


def get_moduledict(module_name: str) ->dict:
    """将一个模块对象中公有的元素组装为一个字典"""
    moduledict = {}
    module = __import__(module_name)
    for name in filter(non_private, dir(module)):
        moduledict[name] = getattr(module, name)
    return moduledict


if __name__ == '__main__':
    # 如果给出了测试用例文件列表则使用它们
    rsts = []
    for filename in sys.argv:
        if getext(filename) != '.rst':
            filename = forceext(filename, 'rst')
        if isfile(filename):
            rsts.append(filename)
else:
    # 如果没有给出测试用例文件,则在当前目录下寻找所有的rst文件
    rsts = get_rsts()

# 每个rst文件对应一组测试
for rst_file in rsts:
    # 得到rst对应的目标模块/文件,建立相应的待测对象
    try:
        module_dict = get_moduledict(getstem(rst_file))
    except (Exception,):
        module_dict = {}
    print(getstem(rst_file), '...')
    # 待测对象通过extraglobs参数传递给testfile方法
    doctest.testfile(rst_file,
                     extraglobs=module_dict)

# -*- coding: utf-8 -*-
"""主测试文件
使用doctest为核心进行测试
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
    rsts = []
    for filename in sys.argv:
        if getext(filename) != '.rst':
            filename = forceext(filename, 'rst')
        if isfile(filename):
            rsts.append(filename)
else:
    rsts = get_rsts()
for rst_file in rsts:
    try:
        module_dict = get_moduledict(getstem(rst_file))
    except (Exception,):
        module_dict = {}
    doctest.testfile(rst_file,
                     extraglobs=module_dict)

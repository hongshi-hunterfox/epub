# -*- coding: utf-8 -*-


class EpubError(Exception):
    """epub项目中的异常"""


class FillbackError(EpubError):
    """候选链错误
    参数是一个列表:
        自当前src至出错的那个src
    """


class CircularReference(FillbackError):
    """候选链错误(循环引用文档)
    最后一个src在列表中第二次出现
    """


class EndNotCMT(FillbackError):
    """候选链错误(结束于非核心媒体类型)
    最后一个src的media-type不是限
    """


class EndToEmpty(FillbackError):
    """候选链错误(非正常结束)"""


class QuoteError(Exception):
    """引用异常"""


class QuotedNothing(QuoteError):
    """引用了不存在的源"""


class QuotedRepeat(QuoteError):
    """重复引用同一个源"""


class NotFoundSource(Exception):
    """在EPUB的content.opf中找不到源的定义(meta name="source:...")"""

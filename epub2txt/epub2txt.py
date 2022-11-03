# Copyright (c) 2019 The Python Packaging Authority

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Convert epub to text."""
# pylint:

from typing import Any, Callable, List, Union

from pathlib import Path

# for with_func_attrs
# from typing import Iterable
from collections import Iterable  # < py38

# the rest
from itertools import zip_longest
import httpx
import io
from lxml import etree
from ebooklib import epub

import logzero
from logzero import logger


def with_func_attrs(**attrs: Any) -> Callable:
    '''Deco with_func_attrs.'''
    def with_attrs(fct: Callable) -> Callable:
        for key, val in attrs.items():
            setattr(fct, key, val)
        return fct
    return with_attrs


def flatten_iter(items):
    """Yield items from any nested iterable; see Reference."""
    for x in items:
        if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
            for sub_x in flatten_iter(x):
                yield sub_x
        else:
            yield x


# fmt: off
@with_func_attrs(title="", toc="", toc_titles="", toc_hrefs="", toc_uids="", spine="", metadata="")
def epub2txt(
        filepath: Union[str, Path],
        clean: bool = True,
        outputlist: bool = False,
        debug: bool = False,
        do_formatting: bool = False,
) -> Union[str, List[str]]:
    # fmt: on
    """Convert epub to text.

    outputlist: if set to True, output List[str] according to book.spine
    clean: remove blank lines if set to True

    list of ebooklib.epub.EpuNav/ebooklib.epub.EpubHtml
    [book.get_item_with_id(elm) for elm in book.spine]
    """
    if debug:
        logzero.loglevel(10)
    else:
        logzero.loglevel(20)

    # process possible url
    if filepath.__str__().startswith("http"):
        try:
            resp = httpx.get(filepath, timeout=30)
            resp.raise_for_status()
        except Exception as exc:
            logger.error("httpx.get(%s) exc: %s", filepath, exc)
            raise
        cont = io.BytesIO(resp.content)

        try:
            book = epub.read_epub(cont)
        except Exception as exc:
            logger.error("epub.read_epub(cont) exc: %s", exc)
            raise
    else:
        filepath = Path(filepath)
        try:
            book = epub.read_epub(filepath)
        except Exception as exc:
            logger.error("epub.read_epub(%s) exc: %s", filepath, exc)
            raise

    _ = [*flatten_iter(book.toc)]
    try:
        epub2txt.toc_titles = [elm.title for elm in _]
        # xhtml files associated with toc titles
        epub2txt.toc_hrefs = [elm.href for elm in _]
    except Exception as exc:
        logger.warning(" toc_title/toc_hrefs exc: %s", exc)

    try:
        epub2txt.toc_uids = [elm.uid for elm in _]
    except Exception as exc:
        logger.warning(" toc_uids exc: %s", exc)

    epub2txt.title = book.title
    epub2txt.toc = [*zip_longest(epub2txt.toc_titles, epub2txt.toc_hrefs, fillvalue="")]

    # list of things packed into epub
    epub2txt.spine = [elm[0] for elm in book.spine]

    # list of ebooklib.epub.EpuNav/ebooklib.epub.EpubHtml
    # [book.get_item_with_id(elm) for elm in epub2txt.spine]

    epub2txt.metadata = [*book.metadata.values()]

    contents = [book.get_item_with_id(item[0]).content for item in book.spine]
    # texts = [pq(content).text() for content in contents]

    # Using XPath to find text
    # root = etree.XML(content)
    # tree = etree.ElementTree(root)
    # text = tree.xpath("string()")   # pq(content).text()

    texts = []
    for content in contents:
        content_string = content.decode('utf-8')
        if do_formatting:
            content_string = content_string.replace(u'<em>', u'___SHIFT_IN_CHARACTER___')
            content_string = content_string.replace(u'</em>', u'___SHIFT_OUT_CHARACTER___')
            content_string = content_string.replace(u'<i>', u'___SHIFT_IN_CHARACTER___')
            content_string = content_string.replace(u'</i>', u'___SHIFT_OUT_CHARACTER___')
            content_string = content_string.replace(u'<strong>', u'___SHIFT_IN_CHARACTER______SHIFT_IN_CHARACTER___')
            content_string = content_string.replace(u'</strong>', u'___SHIFT_OUT_CHARACTER______SHIFT_OUT_CHARACTER___')
            content_string = content_string.replace(u'<b>', u'___SHIFT_OUT_CHARACTER______SHIFT_OUT_CHARACTER___')
            content_string = content_string.replace(u'</b>', u'___SHIFT_OUT_CHARACTER______SHIFT_OUT_CHARACTER___')
        content = bytes(content_string, 'utf-8')
        root = etree.XML(content)
        tree = etree.ElementTree(root)
        text = tree.xpath("string()")
        if do_formatting:
            text = text.replace(u'___SHIFT_IN_CHARACTER___', u'\u000f')
            text = text.replace(u'___SHIFT_OUT_CHARACTER___', u'\u000e')
        texts.append(text)

    if clean:
        temp = []
        for text in texts:
            _ = [elm.strip() for elm in text.splitlines() if elm.strip()]
            temp.append("\n".join(_))
        texts = temp

    if outputlist:
        return texts

    return "\n".join(texts)

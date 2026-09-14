#!/usr/bin/env python3
"""Пересобирает .pptx со сжатием deflate (pptxgenjs пишет zip без сжатия)."""
import os
import sys
import zipfile


def recompress(path):
    with zipfile.ZipFile(path) as zin:
        items = [(i.filename, i.date_time, zin.read(i.filename)) for i in zin.infolist()]

    tmp = path + '.tmp'
    with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zout:
        for name, date_time, data in items:
            info = zipfile.ZipInfo(name, date_time)
            info.compress_type = zipfile.ZIP_DEFLATED
            zout.writestr(info, data)

    before = os.path.getsize(path)
    os.replace(tmp, path)
    print('%s: %d -> %d байт' % (path, before, os.path.getsize(path)))


if __name__ == '__main__':
    for arg in sys.argv[1:]:
        recompress(arg)

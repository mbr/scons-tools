#!/usr/bin/env python
# coding=utf8

from SCons.Script import *

# 150 dpi, a4 (210mm x 297mm)
a4_dim_px = (1240, 1754)

def generate(env):
    # converts a JPEG with the right aspect ration to an A4 PDF page
    img_to_pdf = Builder(action = ' '.join(
                        ['convert', '$SOURCE',
                         '-units', 'PixelsPerInch',
                         '-density', '150',
                         '-quality', '80',
                         '-resize', '%dx%d' % a4_dim_px,
                         '$TARGET']))

    # converts an SVG to PDF using inkscape
    svg_to_pdf = Builder(action = ' '.join(
                        ['inkscape',
                         '--export-area-page',
                         '--export-pdf=$TARGET',
                         '$SOURCE']))

    # concatenates PDF files using pdftk
    pdf_merge = Builder(action = 'pdftk $SOURCES cat output $TARGET')

    rst_to_html = Builder(action = ' '.join(
                          ['rst2html',
                           '--strict',
                           '--math-output=MathJax',
                           '$SOURCE',
                           '$TARGET']),
                          suffix = '.html',
                          src_suffix = '.rst')

    env.Append(BUILDERS={
        'PDFMerge': pdf_merge,
        'ImgToPDF': img_to_pdf,
        'SVGToPDF': svg_to_pdf,
        'RSTToHTML': rst_to_html,
    })


def exists(env):
    # we could detect if all tools are installed, however a user might want
    # to use only some of them
    return True

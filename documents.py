#!/usr/bin/env python
# coding=utf8

from SCons.Script import Builder

# 150 dpi, a4 (210mm x 297mm)
a4_dim_px = (1240, 1754)


def generate(env):
    # converts a JPEG with the right aspect ration to an A4 PDF page
    img_to_pdf = Builder(action=' '.join(
                        ['convert', '$SOURCE',
                         '-units', 'PixelsPerInch',
                         '-density', '150',
                         '-quality', '80',
                         '-resize', '%dx%d' % a4_dim_px,
                         '$TARGET']))

    # converts an SVG to PDF using inkscape
    svg_to_pdf = Builder(action=' '.join(
                        ['inkscape',
                         '--export-area-page',
                         '--export-pdf=$TARGET',
                         '$SOURCE']))

    # concatenates PDF files using pdftk
    pdf_merge = Builder(action='pdftk $SOURCES cat output $TARGET')

    rst_to_html = Builder(action=' '.join(
                          ['rst2html',
                           '--strict',
                           '--math-output=MathJax',
                           '$SOURCE',
                           '$TARGET']),
                          suffix='.html',
                          src_suffix='.rst')

    rst_to_latex = Builder(action=' '.join(
                           ['rst2latex',
                            '--strict',
                            '--stylesheet=amsfonts,amssymb',
                            '$RST2LATEXFLAGS',
                            '$SOURCE',
                            '$TARGET',
                            ]),
                           suffix='.latex',
                           src_suffix='.rst')

    rst_to_pdf = Builder(action=' '.join(
                         ['rst2pdf',
                          '--compressed',
                          # FIXME: should support language options
                          '--smart-quotes=1',
                          '>', '$TARGET',
                          '<', '$SOURCE',
                          ]),
                         suffix='.pdf',
                         src_suffix='.rst')

    dot_to_pdf = Builder(action=' '.join([
                         'dot',
                         '-Tpdf',            # output pdf
                         '-o$TARGET',
                         '$SOURCE',
                         ]),
                         suffix='.pdf',
                         src_suffix='.dot',
                         )

    env.Append(BUILDERS={
        'PDFMerge': pdf_merge,
        'ImgToPDF': img_to_pdf,
        'SVGToPDF': svg_to_pdf,
        'RST2HTML': rst_to_html,
        'RST2Latex': rst_to_latex,
        'RST2PDF': rst_to_pdf,
        'DotPdf': dot_to_pdf,
    })


def exists(env):
    # we could detect if all tools are installed, however a user might want
    # to use only some of them
    return True

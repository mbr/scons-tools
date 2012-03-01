#!/usr/bin/env python
# coding=utf8

"""Builders for common generated web files"""

import re

from SCons.Script import *

# note: this is far from accurate or correct,
#       but should handle 99% of the common cases
import_re = re.compile('@import\s+' +
                       '(?:url\()?' +
                       """["']([^'"]*)["']""" +
                       '\s*;')


def less_scan(node, env, path):
    imports = import_re.findall(node.get_text_contents())
    return env.File([node.get_dir().File(fn) for fn in imports])


def generate(env):
    bld = Builder(action='lessc $SOURCE $TARGET',
                  suffix='.css',
                  src_suffix='.less')

    s = Scanner(function=less_scan, skeys=['.less'])
    env.Append(BUILDERS={'less': bld}, SCANNERS=s)


def exists(env):
    return env.Detect('lessc')

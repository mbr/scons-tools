#!/usr/bin/env python
# coding=utf8

"""Builders for common generated web files"""

import os
import re
from urlparse import urlparse

from SCons.Script import *
import SCons.Warnings


class UnknownDependencyWarning(SCons.Warnings.Warning):
    pass


SCons.Warnings.enableWarningClass(UnknownDependencyWarning)


# note: this is far from accurate or correct,
#       but should handle 99% of the common cases
import_re = re.compile('@import\s+' +
                       '(?:url\()?' +
                       """["']([^'"]*)["']""" +
                       '\s*;')


def less_scan(node, env, path):
    imports = import_re.findall(node.get_text_contents())
    return env.File([node.get_dir().File(fn) for fn in imports])


def dart2js_scan(node, env, path):
    deps_fn = str(node) + '.js.deps'
    if os.path.exists(deps_fn):
        dependencies = []
        with open(deps_fn) as deps_file:
            for line in deps_file:
                o = urlparse(line.strip())
                if not o.scheme == 'file':
                    SCons.Warnings.warn(UnknownDependencyWarning,
                                        'Cannot handle dependency "%s"' % line)
                    continue

                dependencies.append(env.File(o.path))
        return dependencies
    return []


def dart_emitter(target, source, env):
    target.append(str(target[0]) + '.deps')
    target.append(str(target[0]) + '.map')
    return target, source


dart2js_builder = Builder(action='dart2js -c $SOURCE -o$TARGET',
                          suffix='.dart.js',
                          src_suffix='.dart',
                          emitter=dart_emitter)

dart2js_scanner = Scanner(function=dart2js_scan,
                          skeys=['.dart'])


less_builder = Builder(action='lessc $SOURCE $TARGET',
                       suffix='.css',
                       src_suffix='.less')


less_scanner = Scanner(function=less_scan, skeys=['.less'])


def generate(env):
    env.Append(BUILDERS={'less': less_builder,
                         'Dart2Js': dart2js_builder},
               SCANNERS=[less_scanner, dart2js_scanner])


def exists(env):
    return True

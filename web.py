#!/usr/bin/env python
# coding=utf8

"""Builders for common generated web files.

Supports building of LESS, Dart and CoffeeScript files.
"""

import os
import re
from urlparse import urlparse

from SCons.Script import *
import SCons.Warnings


class UnknownDependencyWarning(SCons.Warnings.Warning):
    pass


SCons.Warnings.enableWarningClass(UnknownDependencyWarning)


#################################################
# SCANNERS
#################################################
SCANNERS = []

# note: this is far from accurate or correct,
#       but should handle 99% of the common cases
LESS_IMPORT_RE = re.compile('@import\s+' +
                            '(?:url\()?' +
                            """["']([^'"]*)["']""" +
                            '\s*;')


def less_scan(node, env, path):
    include_path = (node.get_dir(),) + tuple(path)
    result = []
    for fn in LESS_IMPORT_RE.findall(node.get_text_contents()):
        n = SCons.Node.FS.find_file(fn, include_path)
        if n == None:
            result.append(env.File(fn))
            # should trigger a 'not found'
        else:
            result.append(n)

    return result

SCANNERS.append(Scanner(function=less_scan, skeys=['.less'],
                        path_function=FindPathDirs('LESS_INCLUDE_PATH'),
                        recursive=True))


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

SCANNERS.append(Scanner(function=dart2js_scan,
                        skeys=['.dart']))


#################################################
# BUILDERS
#################################################
BUILDERS = {}
DEFAULTS = {}

def dart_emitter(target, source, env):
    target.append(str(target[0]) + '.deps')
    target.append(str(target[0]) + '.map')
    return target, source

BUILDERS['Dart2Js'] = Builder(action='dart2js -c $SOURCE -o$TARGET',
                              suffix='.dart.js',
                              src_suffix='.dart',
                              emitter=dart_emitter)


def lessc_generator(source, target, env, for_signature):
    if not env['LESS_COMPILER'] in ('lessc', 'recess'):
        raise Error('Less compiler %s not known' % env['LESS_COMPILER'])

    cmd = [env['LESS_COMPILER']]

    if env['LESS_INCLUDE_PATH']:
        if env['LESS_COMPILER'] not in ('lessc',):
            raise Error('Compiler %s does not support include paths.' %
                        env['LESS_COMPILER'])
        cmd.append('--include-path="%s"' %
                   os.pathsep.join(env['LESS_INCLUDE_PATH']))

    if env['LESS_COMPRESS']:
        if env['LESS_YUI_COMPRESS']:
            if env['LESS_COMPILER'] not in ('lessc',):
                raise Error('Compiler %s does not support YUI-compress.' %
                            env['LESS_COMPILER'])
            cmd.append('--yui-compress')
        else:
            cmd.append('--compress')

    if env['LESS_STRICT_IMPORTS']:
        if env['LESS_COMPILER'] not in ('lessc',):
            raise Error('Compiler %s does not support strict imports.' %
                        env['LESS_COMPILER'])
        cmd.append('--strict-imports')

    cmd.append('"%s"' % source[0])
    cmd.append('"%s"' % target[0])

    return ' '.join(cmd)

BUILDERS['Less'] = Builder(generator=lessc_generator,
                           suffix='.css',
                           src_suffix='.less')
DEFAULTS['LESS_COMPILER'] = 'lessc'
DEFAULTS['LESS_INCLUDE_PATH'] = []
DEFAULTS['LESS_COMPRESS'] = True
DEFAULTS['LESS_YUI_COMPRESS'] = False
DEFAULTS['LESS_STRICT_IMPORTS'] = True


def generate(env):
    env.Append(BUILDERS=BUILDERS, SCANNERS=SCANNERS)
    env.SetDefault(**DEFAULTS)


def exists(env):
    return True

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
    for fn in LESS_IMPORT_RE.findall(node.get_text_contents()):
        n = SCons.Node.FS.find_file(fn, include_path)
        if n == None:
            yield env.File(fn)
            # should trigger a 'not found'
        else:
            yield n

SCANNERS.append(Scanner(function=less_scan, skeys=['.less'],
                        path_function=FindPathDirs('LESS_INCLUDE_PATH'),
                        recursive=True))


def dart2js_scan(node, env, path):
    deps_fn = str(node) + '.js.deps'
    if os.path.exists(deps_fn):
        with open(deps_fn) as deps_file:
            for line in deps_file:
                o = urlparse(line.strip())
                if not o.scheme == 'file':
                    SCons.Warnings.warn(UnknownDependencyWarning,
                                        'Cannot handle dependency "%s"' % line)
                    continue

                yield env.File(o.path)

SCANNERS.append(Scanner(function=dart2js_scan,
                        skeys=['.dart']))


# coffee-script code MIT-licensed, originally written by Joe Koberg
# altered by Marc Brinkmann
COFFEE_REQUIRE_PATTERNS = [
    re.compile(pattern, re.MULTILINE)
    for pattern in [
        r"""require\s*\(*\s*['"]([^.].*?)['"]\)*""",
        r"""require\s*\(*\s*['"](\./.*?)['"]\)*""",
        r"""require\s*\(*\s*['"](\.\./.*?)['"]\)*""",
        ]
    ]

COFFEE_DEFINE_PATTERNS = [
    re.compile(pattern, re.MULTILINE)
    for pattern in [
        r"""define\s*\(*\s*\[(.+?)\]""",
        r"""require\s*\(*\s*\[(.+?)\]""",
        ]
    ]

def coffee_glob_requirement_name(env, node, name):
    if not name.startswith('_'):
        if name.endswith('.js'):
            # suffixed files are located relative to the script calling require()
            # that seems wrong. Suffixed files are located relative to root???
            #req = node.File(name)
            yield env['COFFEEROOT'].File(name)
        else:
            # non-suffixed files are located relative to html containing data-main
            # Also seems wrong. They are located relative to the SCRIPT mentioned in data-main
            coffee_file = node.File(name+'.coffee')
            if coffee_file.exists():
                # build the required JS file from the coffescript source
                reqs = env.Coffeescript(source=coffee_file)
                for req in reqs:
                    yield req
            else:
                # if no .coffee to compile, depend on a raw .js
                yield node.File(name+'.js')


def coffee_scan(node, env, path):
    contents = node.get_text_contents()
    requirements = []

    for pattern in COFFEE_REQUIRE_PATTERNS:
        for match in pattern.finditer(contents):
            requirement = match.group(1)
            for found in coffee_glob_requirement_name(env, node, requirement):
                yield found

    for pattern in COFFEE_DEFINE_PATTERNS:
        for match in pattern.finditer(contents):
            define_strings = [s.strip().strip('"\'') for s in match.group(1).split(',')]
            for requirement in define_strings:
                for found in coffee_glob_requirement_name(env, node, requirement):
                    yield found
SCANNERS.append(env.Scanner(function = coffee_scan_func,
                            skeys = ['.coffee', '.js']))



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
                              emitter=dart_emitter,
                              single_source=True)


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
                           src_suffix='.less',
                           single_source=True)
DEFAULTS['LESS_COMPILER'] = 'lessc'
DEFAULTS['LESS_INCLUDE_PATH'] = []
DEFAULTS['LESS_COMPRESS'] = True
DEFAULTS['LESS_YUI_COMPRESS'] = False
DEFAULTS['LESS_STRICT_IMPORTS'] = True
# note: could use lessc for compiling and recess for compression to support
#       build a "real" bootstrap
# note: could support .min.css using emitters?
# note: could support a path for the compiler binary (to allow non-standard
#       compiler forks)
# note: could do away with LESS_YUI_COMPRESS and add a generic LESS_COMPRESSOR
#       option, see first note


# coffee-script code MIT-licensed, originally written by Joe Koberg
# altered by Marc Brinkmann
BUILDERS['Coffee'] = Builder(action='coffee -c $SOURCE > $TARGET',
                             suffix='.js', src_suffix='.coffee',
                             single_source=True)
DEFAULTS['COFFEEROOT'] = Dir('.')


def generate(env):
    env.Append(BUILDERS=BUILDERS, SCANNERS=SCANNERS)
    env.SetDefault(**DEFAULTS)


def exists(env):
    return True

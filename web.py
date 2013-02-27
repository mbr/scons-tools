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


def get_jar(env, jarname):
    if jarname in env:
        return env.get(jarname)

    if jarname in env['ENV']:
        return env['ENV'][jarname]

    raise KeyError('Please set %s on the environment' % jarname)


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
            yield env['COFFEE_ROOT'].File(name)
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
SCANNERS.append(Scanner(function = coffee_scan,
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


def coffee_generator(source, target, env, for_signature):
    cmd = ['coffee']
    cmd.append('-c')
    cmd.append('-p')

    if env['COFFEE_BARE']:
        cmd.append('-b')

    cmd.extend('"%s"' % src for src in source)
    cmd.append('> "%s"' % target[0])
    return ' '.join(cmd)

BUILDERS['Coffee'] = Builder(generator=coffee_generator,
                             suffix='.js', src_suffix='.coffee')
DEFAULTS['COFFEE_ROOT'] = Dir('.')
DEFAULTS['COFFEE_BARE'] = False


def uglifyjs_generator(source, target, env, for_signature):
    cmd = ['uglifyjs']

    # input needs to go in front
    cmd.extend('"%s"' % src for src in source)

    if env['UGLIFY_COMMENTS']:
        cmd.append('--comments')
        cmd.append(env['UGLIFY_COMMENTS'])

    if env['UGLIFY_COMPRESS']:
        cmd.append('--compress')

    if env['UGLIFY_COMPRESS']:
        cmd.append('--mangle')

    if env['UGLIFY_BEAUTIFY']:
        cmd.append('--beautify')

    if env['UGLIFY_LINT']:
        cmd.append('--lint')

    cmd.append('-o "%s"' % target[0])

    return ' '.join(cmd)

BUILDERS['UglifyJs'] = Builder(generator=uglifyjs_generator,
                               suffix='.min.js', src_suffic='.js')
DEFAULTS['UGLIFY_COMMENTS'] = None
DEFAULTS['UGLIFY_COMPRESS'] = True
DEFAULTS['UGLIFY_MANGLE'] = True
DEFAULTS['UGLIFY_BEAUTIFY'] = False
DEFAULTS['UGLIFY_LINT'] = False


def closure_generator(source, target, env, for_signature):
    cmd = [env['JAVA'], '-jar', get_jar(env, 'CLOSURE_COMPILER_JAR')]

    if env['CLOSURE_COMPILATION_LEVEL']:
        cmd.append('--compilation_level')
        cmd.append(env['CLOSURE_COMPILATION_LEVEL'])

    cmd.extend(env['CLOSURE_FLAGS'])

    cmd.append('--js_output_file "%s"' % target[0])
    cmd.extend('--js "%s"' % src for src in source)

    return ' '.join(cmd)

BUILDERS['Closure'] = Builder(generator=closure_generator,
                                suffix='.min.js', src_suffic='.js')

DEFAULTS['CLOSURE_COMPILATION_LEVEL'] = 'ADVANCED_OPTIMIZATIONS'
DEFAULTS['CLOSURE_FLAGS'] = []


def htmlcomp_generator(source, target, env, for_signature):
    cmd = [env['JAVA'], '-jar', get_jar(env, 'HTMLCOMP_COMPRESSOR_JAR')]

    opt_level_trans = {
        'WHITESPACE_ONLY': 'whitespace',
        'SIMPLE_OPTIMIZATIONS': 'simple',
        'ADVANCED_OPTIMIZATIONS': 'advanced',
    }

    is_xml = str(target[0]).endswith('.xml')

    def_opt_set = env['HTMLCOMP_AGGRESSIVE_OPTIONS']\
                  if env['HTMLCOMP_AGGRESSIVE'] else\
                  env['HTMLCOMP_SAFE_OPTIONS']

    def get_opt(name):
        val = env[name]

        if val == None:
            return def_opt_set[name]

    if env['HTMLCOMP_CHARSET']:
        cmd.append('--charset')
        cmd.append(env['HTML_CHARSET'])

    if get_opt('HTMLCOMP_PRESERVE_COMMENTS'):
        cmd.append('--preserve-comments')

    if is_xml and get_opt('HTMLCOMP_PRESERVE_INTERTAG_SPACES'):
        cmd.append('--preserve-intertag-spaces')
    elif not is_xml and not get_opt('HTMLCOMP_PRESERVE_INTERTAG_SPACES'):
        cmd.append('--remove-intertag-spaces')

    if not is_xml:
        if get_opt('HTMLCOMP_PRESERVE_MULTI_SPACES'):
            cmd.append('--preserve-multi-spaces')

        if get_opt('HTMLCOMP_PRESERVE_LINE_BREAKS'):
            cmd.append('--preserve-line-breaks')

        if not get_opt('HTMLCOMP_PRESERVE_QUOTES'):
            cmd.append('--remove-quotes')

        if not get_opt('HTMLCOMP_PRESERVE_DOCTYPE'):
            cmd.append('--simple-doctype')

        if not get_opt('HTMLCOMP_PRESERVE_TYPE_ATTRS'):
            cmd.extend(('--remove-style-attr',
                        '--remove-link-attr',
                        '--remove-script-attr',
                        '--remove-form-attr',
                        '--remove-input-attr'))

        if not get_opt('HTMLCOMP_PRESERVE_BOOL_ATTRS'):
            cmd.append('--simple-bool-attr')

        if not get_opt('HTMLCOMP_PRESERVE_JS_PROTOCOL'):
            cmd.append('--remove-js-protocol')

        if get_opt('HTMLCOMP_COMPRESS_JS') == 'yui':
            cmd.extend(('--compress-js', '--js-compressor', 'yui'))
        elif get_opt('HTMLCOMP_COMPRESS_JS') == 'closure':
            cmd.extend(('--compress-js', '--js-compressor', 'closure'))
            cmd.append('--closure-opt-level')
            cmd.append(opt_level_trans.get(env['CLOSURE_COMPILATION_LEVEL'],
                       'simple'))

        if get_opt('HTMLCOMP_COMPRESS_CSS') == 'yui':
            cmd.append('--compress-css')

    cmd.append('"%s"' % source[0])
    cmd.append('-o "%s"' % target[0])

    return ' '.join(cmd)

BUILDERS['HtmlComp'] = Builder(generator=htmlcomp_generator,
                               suffix='.min.html', src_suffix='.html',
                               single_source=True)

DEFAULTS['JAVA'] = 'java'
DEFAULTS['HTMLCOMP_AGGRESSIVE'] = True

DEFAULTS['HTMLCOMP_AGGRESSIVE_OPTIONS'] = {
    'HTMLCOMP_PRESERVE_INTERTAG_SPACES': False,
    'HTMLCOMP_PRESERVE_QUOTES': False,
    'HTMLCOMP_PRESERVE_DOCTYPE': False,
    'HTMLCOMP_PRESERVE_TYPE_ATTRS': False,
    'HTMLCOMP_PRESERVE_BOOL_ATTRS': False,
    'HTMLCOMP_PRESERVE_JS_PROTOCOL': False,
    'HTMLCOMP_COMPRESS_JS': 'closure',
    'HTMLCOMP_COMPRESS_CSS': 'yui',
}

DEFAULTS['HTMLCOMP_SAFE_OPTIONS'] = {
    'HTMLCOMP_PRESERVE_INTERTAG_SPACES': True,
    'HTMLCOMP_PRESERVE_QUOTES': True,
    'HTMLCOMP_PRESERVE_DOCTYPE': True,
    'HTMLCOMP_PRESERVE_TYPE_ATTRS': True,
    'HTMLCOMP_PRESERVE_BOOL_ATTRS': True,
    'HTMLCOMP_PRESERVE_JS_PROTOCOL': True,
    'HTMLCOMP_COMPRESS_JS': False,
    'HTMLCOMP_COMPRESS_CSS': False,
}

DEFAULTS['HTMLCOMP_CHARSET'] = None
DEFAULTS['HTMLCOMP_PRESERVE_COMMENTS'] = False
DEFAULTS['HTMLCOMP_PRESERVE_MULTI_SPACES'] = False
DEFAULTS['HTMLCOMP_PRESERVE_LINE_BREAKS'] = False

DEFAULTS['HTMLCOMP_PRESERVE_INTERTAG_SPACES'] = None
DEFAULTS['HTMLCOMP_PRESERVE_QUOTES'] = None
DEFAULTS['HTMLCOMP_PRESERVE_DOCTYPE'] = None
DEFAULTS['HTMLCOMP_PRESERVE_TYPE_ATTRS'] = None
DEFAULTS['HTMLCOMP_PRESERVE_BOOL_ATTRS'] = None
DEFAULTS['HTMLCOMP_PRESERVE_JS_PROTOCOL'] = None
DEFAULTS['HTMLCOMP_COMPRESS_JS'] = None
DEFAULTS['HTMLCOMP_COMPRESS_CSS'] = None

def generate(env):
    env.Append(BUILDERS=BUILDERS, SCANNERS=SCANNERS)
    env.SetDefault(**DEFAULTS)


def exists(env):
    return True

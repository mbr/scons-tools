Custom tools/builders for SCons. Each is in a self-contained file, put it into
your `~/.scons/site_scons/site_tools` directory, or use code like this::

  env = Environment(tools = ['default', 'archive'], toolpath = ['scons-tools'])

You should put the tools file (in this case, `archive.py`) into a subfolder of
the directory `SConstruct` resides in called `scons-tools`.

Note: Depending on your distro and scons version, the site_tools directory may
reside elsewhere. Check the scons manpage for details.

The documentation is a bit lacking at this moment, you are encouraged to have a
look at the source files to find out what builders are available.

All of these SCons tools play along nicely with `hitnrun
<http://github.com/mbr/hitnrun>`_.

Web development
===============

A lot of tools are available for web development, here is an example
``SConstruct`` file to showcase some of them::

  import os

  env = Environment(tools=['default', 'web'], ENV=os.environ,
                    CLOSURE_COMPILER_JAR='~/compiler.jar')

  # compile our scripts
  js_files = env.Coffee(Glob('src/coffee/*.coffee'))

  # build assets
  env.Closure('static/js/app.js', js_files)
  env.Less('static/css/main.css', Glob('src/less/*.less'))


This will build a bunch of `LESS <http://lesscss.org>`_ stylesheets to CSS, and
convert `CoffeeScript <http://coffeescript.org>`_ files to minified Javascript
using the `Google Closure <https://developers.google.com/closure/compiler/>`_
compiler.

Working on this is nice if you use `hitnrun <http://github.com/mbr/hitnrun>`_,
simply type::

  hitnrun

Now saving any of the ``.less`` or ``.coffee`` files will trigger a rebuild of
the parts that need to be rebuilt.


License
=======
Copyright (c) 2010 Marc Brinkmann

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

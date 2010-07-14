#!/usr/bin/env python
# coding=utf8

from SCons.Script import *
from SCons.Errors import BuildError
from SCons import Action

"""
Scons zip/tar/tar.bz2/tar.gz Builder

This aims at allowing the user to easily create an archive of a few files. It is not meant to replace the
packaging capabilities of the bundled package builders, but is rather intended to be used in situations where
you do not want to create a full-fledged package just yet.

A simple example:
-----------------
# assuming you have this file in ./scons-tools:
env = Environment(tools = ['default', 'archive'], toolpath = ['scons-tools'])

  # more stuff declared here ...

# zip up file_1, file_2 and all files named '*.foo' in the subdir 'some_sub_dir' to the
# archive:
Alias('release', env.Archive('dist/release-binary.tar.gz',
                             ['file_1','file_2'] + env.Glob('some_sub_dir/*.foo'))
     )

Other options:
--------------
You can set the following Environment options to affect the behavior of this Tool:

	# example settings, set to defaults here:
	env['ARCHIVE_ZIP_METHOD'] = 'ZIP_DEFLATED'  # zip method, ZIP_STORED for no compression when
	                                              using .zip files
	env.SetDefault(ARCHIVE_PREFIX = None)       # a directory prefix. set to 'foo' and a file
	                                            # 'some_sub_dir/bar.xy' will be added to the archive
	                                            # as 'foo/some_sub_dir/bar.xy'
	env.SetDefault(ARCHIVE_VERBOSE = True)      # print all filenames as they are added
"""

try:
	import os
	import os.path
	import zipfile
	import tarfile
except ImportError:
	def exists(env): return False
else:
	def exists(env): return True

def generate(env):
	assert(exists(env))
	bld = Builder(action = Action.Action(archive, archive_string))
	env.Append(BUILDERS = {'Archive': bld})
	env.SetDefault(ARCHIVE_ZIP_METHOD = 'ZIP_DEFLATED')
	env.SetDefault(ARCHIVE_PREFIX = None)
	env.SetDefault(ARCHIVE_VERBOSE = True)

class ZipWriter(object):
	def __init__(self, env, output_filename):
		try:
			self.ziparchive = zipfile.ZipFile(output_filename, 'w', getattr(zipfile, env['ARCHIVE_ZIP_METHOD']))
		except AttributeError:
			raise BuildError(errstr = 'Not a valid zip method: %s' % env['ARCHIVE_ZIP_METHOD'])

	def add(self, filename, archive_filename):
		self.ziparchive.write(filename, archive_filename)

	def finish(self):
		self.ziparchive.close()

class TarWriter(object):
	def __init__(self, env, output_filename, compression_mode = ''):
		self.tararchive = tarfile.open(output_filename, 'w:%s' % compression_mode)

	def add(self, filename, archive_filename):
		self.tararchive.add(filename, archive_filename)

	def finish(self):
		self.tararchive.close()

def archive_string(target, source, env):
	return "Building %s from %d source files." % (target[0].get_path(), len(source))

def archive(target, source, env):
	assert(len(target) == 1)
	target_name = target[0].get_abspath()

	if target_name.endswith('.zip'):
		writer = ZipWriter(env, target_name)
	elif target_name.endswith('.tar'):
		writer = TarWriter(env, target_name)
	elif target_name.endswith('.tar.bz2'):
		writer = TarWriter(env, target_name, 'bz2')
	elif target_name.endswith('.tar.gz'):
		writer = TarWriter(env, target_name, 'gz')
	else:
		raise BuildError(errstr = "Unknown file extension: %s" % target_name)

	target_relname = target[0].get_path()
	for sourcefile in source:
		archive_prefix = env['ARCHIVE_PREFIX'] or ''
		archive_filename = os.path.join(archive_prefix, sourcefile.get_path())
		source_filename = sourcefile.get_abspath()
		if env['ARCHIVE_VERBOSE']: print "%s => %s:%s" % (source_filename, target_relname, archive_filename)
		writer.add(source_filename, archive_filename)

	writer.finish()

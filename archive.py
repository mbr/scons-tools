#!/usr/bin/env python
# coding=utf8

from SCons.Script import *
from SCons.Errors import BuildError

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
	bld = Builder(action = archive)
	env.Append(BUILDERS = {'Archive': bld})
	env.SetDefault(ARCHIVE_ZIP_METHOD = 'ZIP_DEFLATED')

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

def archive(target, source, env):
	assert(len(target) == 1)
	archive_name = target[0].get_abspath()

	if archive_name.endswith('.zip'):
		writer = ZipWriter(env, archive_name)
	elif archive_name.endswith('.tar'):
		writer = TarWriter(env, archive_name)
	elif archive_name.endswith('.tar.bz2'):
		writer = TarWriter(env, archive_name, 'bz2')
	elif archive_name.endswith('.tar.gz'):
		writer = TarWriter(env, archive_name, 'gz')
	else:
		raise BuildError(errstr = "Unknown file extension: %s" % archive_name)

	for sourcefile in source:
		writer.add(sourcefile.get_abspath(), sourcefile.get_path())

	writer.finish()

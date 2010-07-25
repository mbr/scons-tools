#!/usr/bin/env python
# coding=utf8

from SCons.Script import *

cpu_freq_table = {
	'atmega128': 7372800,
	'atmega328p': 16*10**6,
}

def generate(env):
	bld = Builder(action = 'avr-objcopy -O ihex -R .eeprom $SOURCE $TARGET',
					 suffix = '.hex',
					 src_suffix = '.elf')
	env.Append(BUILDERS = {'AVRHex': bld})

	archflags = Split('-mmcu=$AVR_MMCU -DF_CPU=$AVR_F_CPU' % env)
	env.Replace(CC = 'avr-gcc',
	            CXX = 'avr-g++',
	            AR = 'avr-ar',
	            RANLIB = 'avr-ranlib')
	env.SetDefault(AVR_MMCU = 'atmega328p')

	# freq table fillin
	if env['AVR_MMCU'] not in cpu_freq_table and not 'F_CPU' in env:
		print 'Warning: Unknown AVR_MMCU "%s" and AVR_F_CPU not set.' % env['AVR_MMCU']
	env.SetDefault(AVR_F_CPU = cpu_freq_table.get(env['AVR_MMCU'], ''))

	env.Append(CFLAGS = archflags,
			   CXXFLAGS = archflags,
			   LINKFLAGS = archflags + Split('--gc-sections'))

	# create data and function sections, allowing for later removal of unused functions/data
	# with --gc-sections
	env.Append(CFLAGS = Split('-fdata-sections -ffunction-sections -s'))
	env.Append(CXXFLAGS = '-fno-exceptions')
	env.Append(CFLAGS = '-Os')
	env.Append(CFLAGS = '-std=c99')

def exists():
	return True

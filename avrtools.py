#!/usr/bin/env python
# coding=utf8

from SCons.Script import *

def generate(env):
	bld = Builder(action = 'avr-objcopy -O ihex -R .eeprom $SOURCE $TARGET',
					 suffix = '.hex',
					 src_suffix = '.elf')
	env.Append(BUILDERS = {'AVRHex': bld})

	archflags = Split('-mmcu=atmega328p -DF_CPU=16000000L')
	env.Replace(CC = 'avr-gcc',
	            CXX = 'avr-g++',
	            AR = 'avr-ar',
	            RANLIB = 'avr-ranlib')
	env.Append(CFLAGS = archflags,
			   CXXFLAGS = archflags,
			   LINKFLAGS = archflags + Split('--gc-sections'))
	env.Append(CXXFLAGS = '-fno-exceptions')
	env.Append(CFLAGS = '-Os')
	env.Append(CFLAGS = '-std=c99')

def exists():
	return True

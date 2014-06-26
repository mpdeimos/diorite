#!/usr/bin/env python
# encoding: utf-8
#
# Copyright 2014 Jiří Janoušek <janousek.jiri@gmail.com>
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met: 
# 
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer. 
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution. 
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# Top of source tree
top = '.'
# Build directory
out = 'build'

# Application name and version
APPNAME = "diorite"
VERSION = "0.1.0"
API_VERSION = "0.1"

import sys
from waflib.Configure import conf
from waflib.Errors import ConfigurationError
from waflib.Context import WAFVERSION

WAF_VERSION = map(int, WAFVERSION.split("."))
REQUIRED_VERSION = [1, 7, 14] 
if WAF_VERSION < REQUIRED_VERSION:
	print("Too old waflib %s < %s. Use waf binary distributed with the source code!" % (WAF_VERSION, REQUIRED_VERSION))
	sys.exit(1)

LINUX = "LINUX"
WIN = "WIN"

if sys.platform.startswith("linux"):
	_PLATFORM = LINUX
elif sys.platform.startswith("win"):
	_PLATFORM = WIN
else:
	_PLATFORM = sys.platform.upper()

@conf
def vala_def(ctx, vala_definition):
	"""Appends a Vala definition"""
	if not hasattr(ctx.env, "VALA_DEFINES"):
		ctx.env.VALA_DEFINES = []
	if isinstance(vala_def, tuple) or isinstance(vala_def, list):
		for d in vala_definition:
			ctx.env.VALA_DEFINES.append(d)
	else:
		ctx.env.VALA_DEFINES.append(vala_definition)

@conf
def check_dep(ctx, pkg, uselib, version, mandatory=True, store=None, vala_def=None, define=None):
	"""Wrapper for ctx.check_cfg."""
	result = True
	try:
		res = ctx.check_cfg(package=pkg, uselib_store=uselib, atleast_version=version, mandatory=True, args = '--cflags --libs')
		if vala_def:
			ctx.vala_def(vala_def)
		if define:
			for key, value in define.iteritems():
				ctx.define(key, value)
	except ConfigurationError, e:
		result = False
		if mandatory:
			raise e
	finally:
		if store is not None:
			ctx.env[store] = result
	return res

# Add extra options to ./waf command
def options(ctx):
	ctx.load('compiler_c vala')
	ctx.add_option('--noopt', action='store_true', default=False, dest='noopt', help="Turn off compiler optimizations")
	ctx.add_option('--debug', action='store_true', default=True, dest='debug', help="Turn on debugging symbols")
	ctx.add_option('--no-debug', action='store_false', dest='debug', help="Turn off debugging symbols")
	ctx.add_option('--no-ldconfig', action='store_false', default=True, dest='ldconfig', help="Don't run ldconfig after installation")
	ctx.add_option('--platform', default=_PLATFORM, help="Target platform")

# Configure build process
def configure(ctx):
	
	ctx.env.PLATFORM = PLATFORM = ctx.options.platform.upper()
	if PLATFORM not in (WIN, LINUX):
		print("Unsupported platform %s. Please try to talk to devs to consider support of your platform." % sys.platform)
		sys.exit(1)
	
	ctx.define(PLATFORM, 1)
	ctx.env.VALA_DEFINES = [PLATFORM]
	ctx.msg('Target platform', PLATFORM, "GREEN")
	ctx.msg('Install prefix', ctx.options.prefix, "GREEN")
	
	ctx.load('compiler_c vala')
	ctx.check_vala(min_version=(0,16,1))
	
	# Don't be quiet
	ctx.env.VALAFLAGS.remove("--quiet")
	ctx.env.append_value("VALAFLAGS", "-v")
	
	# enable threading
	ctx.env.append_value("VALAFLAGS", "--thread")
	
	# Turn compiler optimizations on/off
	if ctx.options.noopt:
		ctx.msg('Compiler optimizations', "OFF?!", "RED")
		ctx.env.append_unique('CFLAGS', '-O0')
	else:
		ctx.env.append_unique('CFLAGS', '-O2')
		ctx.msg('Compiler optimizations', "ON", "GREEN")
	
	# Include debugging symbols
	if ctx.options.debug:
		#~ ctx.env.append_unique('VALAFLAGS', '-g')
		if PLATFORM == LINUX:
			ctx.env.append_unique('CFLAGS', '-g3')
		elif PLATFORM == WIN:
			ctx.env.append_unique('CFLAGS', ['-g', '-gdwarf-2'])
	
	# Anti-underlinking and anti-overlinking linker flags.
	ctx.env.append_unique("LINKFLAGS", ["-Wl,--no-undefined", "-Wl,--as-needed"])
	
	# Check dependencies
	ctx.check_dep('glib-2.0', 'GLIB', '2.34') # <= 2.40.0 (Ubuntu 14.04)
	ctx.check_dep('gthread-2.0', 'GTHREAD', '2.34') # <= 2.40.0 (Ubuntu 14.04)
	ctx.check_dep('gio-2.0', 'GIO', '2.38') # <= 2.40.0 (Ubuntu 14.04)
	ctx.check_dep('gtk+-3.0', 'GTK+', '3.4') # <= 3.10.8 (Ubuntu 14.04)
	ctx.check_dep('gdk-3.0', 'GDK', '3.4')  # <= 3.10.8 (Ubuntu 14.04)
	
	if PLATFORM == LINUX:
		ctx.check_dep('gio-unix-2.0', 'UNIXGIO', '2.32')
	elif PLATFORM == WIN:
		ctx.check_dep('gio-windows-2.0', 'WINGIO', '2.32')

def build(ctx):
	#~ print ctx.env
	PLATFORM = ctx.env.PLATFORM
	DIORITE_GLIB = "dioriteglib"
	DIORITE_GTK = "dioritegtk"
	packages = 'posix glib-2.0 gio-2.0'
	uselib = 'GLIB GTHREAD'
	vala_defines = ctx.env.VALA_DEFINES
	
	if PLATFORM == WIN:
		DIORITE_GLIB_LIBNAME = "dioriteglib-" + API_VERSION.split(".")[0]
		DIORITE_GTK_LIBNAME = "dioritegtk-" + API_VERSION.split(".")[0]
		CFLAGS="-mms-bitfields"
		uselib += " WINGIO"
		packages += " gio-windows-2.0 win32"
	else:
		DIORITE_GLIB_LIBNAME = "dioriteglib"
		DIORITE_GTK_LIBNAME = "dioritegtk"
		CFLAGS=""
		uselib += " UNIXGIO"
		packages += " gio-unix-2.0"
	
	ctx(features = "c cshlib",
		target = DIORITE_GLIB,
		name = DIORITE_GLIB,
		vnum = "0.1.0",
		source = ctx.path.ant_glob('src/glib/*.vala') + ctx.path.ant_glob('src/glib/*.c'),
		packages = packages,
		uselib = uselib,
		includes = ["src/glib"],
		vala_defines = vala_defines,
		cflags = ['-DG_LOG_DOMAIN="DioriteGlib"'],
		vapi_dirs = ['vapi'],
		vala_target_glib = "2.32",
	)
	
	ctx(features = "c cshlib",
		target = DIORITE_GTK,
		name = DIORITE_GTK,
		vnum = "0.1.0",
		source = ctx.path.ant_glob('src/gtk/*.vala') + ctx.path.ant_glob('src/gtk/*.c'),
		packages = " gtk+-3.0 gdk-3.0 gio-2.0 glib-2.0",
		uselib = "GTK+ GDK GIO GLIB",
		use = [DIORITE_GLIB],
		includes = ["src/gtk"],
		vala_defines = vala_defines,
		cflags = ['-DG_LOG_DOMAIN="DioriteGtk"'],
		vapi_dirs = ['vapi'],
		vala_target_glib = "2.32",
	)
	
	ctx(features = 'subst',
		source='src/dioriteglib.pc.in',
		target='dioriteglib.pc',
		install_path='${LIBDIR}/pkgconfig',
		VERSION=VERSION,
		PREFIX=ctx.env.PREFIX,
		INCLUDEDIR = ctx.env.INCLUDEDIR,
		LIBDIR = ctx.env.LIBDIR,
		APPNAME=APPNAME,
		API_VERSION=API_VERSION,
		CFLAGS=CFLAGS,
		LIBNAME=DIORITE_GLIB_LIBNAME
		)
	
	ctx(features = 'subst',
		source='src/dioritegtk.pc.in',
		target='dioritegtk.pc',
		install_path='${LIBDIR}/pkgconfig',
		VERSION=VERSION,
		PREFIX=ctx.env.PREFIX,
		INCLUDEDIR = ctx.env.INCLUDEDIR,
		LIBDIR = ctx.env.LIBDIR,
		APPNAME=APPNAME,
		API_VERSION=API_VERSION,
		CFLAGS=CFLAGS,
		LIBNAME=DIORITE_GTK_LIBNAME
		)
	
	if PLATFORM == WIN :
		ctx.program(
		target = "dioriteinterrupthelper",
		source = ['src/helpers/interrupthelper.vala'],
		use = [DIORITE_GLIB],
		packages = 'glib-2.0 win32',
		uselib = 'GLIB',
		vapi_dirs = ['vapi'],
		vala_target_glib = "2.32",
		)
	
	ctx.add_post_fun(post)

def dist(ctx):
	ctx.algo = "tar.gz"
	ctx.excl = '.bzr .bzrignore build/* **/.waf* **/*~ **/*.swp **/.lock* bzrcommit.txt **/*.pyc'

def post(ctx):
	if ctx.cmd in ('install', 'uninstall'):
		if ctx.env.PLATFORM == LINUX and ctx.options.ldconfig:
			ctx.exec_command('/sbin/ldconfig') 

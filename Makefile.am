AUTOMAKE_OPTIONS = foreign
ACLOCAL_AMFLAGS = -I m4

bin_PROGRAMS =
bin_SCRIPTS =
noinst_PROGRAMS =
noinst_HEADERS =
TESTS =
XFAIL_TESTS = 
check_PROGRAMS =
EXTRA_PROGRAMS =
CLEANFILES = $(bin_SCRIPTS)
MAINTAINERCLEANFILES =
EXTRA_DIST =
BUILT_SOURCES =

EXTRA_DIST += \
			   prepare.sh 

AM_CPPFLAGS = -I$(top_srcdir)/src \
    $(BOOST_CPPFLAGS) ${CONCEPTUAL_CFLAGS}

AM_LDFLAGS = $(BOOST_LDFLAGS) 

AM_CFLAGS = 

AM_LIBS =

LDADD = ${CONCEPTUAL_LIBS}

AM_CXXFLAGS = $(AM_CFLAGS)

lib_LTLIBRARIES = src/libunion.la

pkgconfigdir = $(libdir)/pkgconfig
pkgconfig_DATA = maint/union.pc

include Make.rules

include $(top_srcdir)/src/Makefile.subdir


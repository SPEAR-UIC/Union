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
    ${CONCEPTUAL_CFLAGS}

AM_LDFLAGS = 

AM_CFLAGS = 

AM_LIBS =

LDADD = ${CONCEPTUAL_LIBS}

AM_CXXFLAGS = $(AM_CFLAGS)

lib_LTLIBRARIES = src/libunion.la

pkgconfigdir = $(libdir)/pkgconfig
pkgconfig_DATA = maint/union.pc

include Make.rules

# Generate union_util.c and Makefile.subdir before compiling
src/generated.stamp:
	$(AM_V_GEN) $(PYTHON) $(top_srcdir)/src/translator/gen_benchmark.py \
		--conceptual-dir=$(CONCEPTUAL_SRC_DIR) \
		--union-srcdir=$(top_srcdir)/src && \
	touch $@

# Declare the outputs
BUILT_SOURCES += \
	src/generated.stamp \
	src/union_util.c \
	src/Makefile.subdir

# Rebuild if Makefile.subdir changes
$(srcdir)/src/Makefile.subdir: src/generated.stamp

include $(top_srcdir)/src/Makefile.subdir

PYTHON = @PYTHON@
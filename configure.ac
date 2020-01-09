#                                               -*- Autoconf -*-
# Process this file with autoconf to produce a configure script.

AC_PREREQ([2.67])
AC_INIT([union], [0.1], [],[],[]) 
AC_CONFIG_MACRO_DIRS([m4])
LT_INIT

AX_BOOST_BASE([1.66])

AC_CANONICAL_TARGET
AC_CANONICAL_SYSTEM
AC_CANONICAL_HOST

AM_INIT_AUTOMAKE([foreign subdir-objects -Wall])

# we should remove this soon, only needed for automake 1.10 and older
m4_ifdef([AM_SILENT_RULES], [AM_SILENT_RULES([yes])])


AC_CONFIG_SRCDIR([README.md])

# Checks for programs.
AC_PROG_CC
AM_PROG_CC_C_O
AC_PROG_CXX
AC_PROG_CXXCPP

AX_CXX_COMPILE_STDCXX(11, noext, mandatory)
AC_PROG_MKDIR_P

AC_REQUIRE_CPP

AC_CHECK_SIZEOF([long int])

#check for Conceptual
AC_ARG_WITH([conceptual],[AS_HELP_STRING([--with-conceptual@<:@=DIR@:>@],
                        [location of Conceptual installation])])
if test "x${with_conceptual}" != "x" ; then
  AC_CHECK_FILES([${with_conceptual}/lib/libncptl.a],
    AM_CONDITIONAL(USE_CONC, true),
    AC_MSG_ERROR(Could not find Conceptual libraries libncptl.a))
  CONCEPTUAL_CFLAGS="-I${with_conceptual}/include"
  CONCEPTUAL_LIBS="-L${with_conceptual}/lib/ -lncptl"
  AC_SUBST(CONCEPTUAL_LIBS)
  AC_SUBST(CONCEPTUAL_CFLAGS)
else
  AM_CONDITIONAL(USE_CONC, false)
fi


dnl
dnl Verify pkg-config
dnl
PKG_PROG_PKG_CONFIG
if test "x$PKG_CONFIG" == "x"; then
       AC_MSG_ERROR([Could not find pkg-config utility!])
fi



AC_CONFIG_FILES([Makefile maint/union.pc])
AC_OUTPUT



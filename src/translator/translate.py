#! /usr/bin/env python

import sys
import os
import getopt
import re
import string
import random


def usage(exitcode=0):
    "Provide a usage message."
    if exitcode == 0:
        dev = sys.stdout
    else:
        dev = sys.stderr
    dev.write("""Usage: ncptl [--concpath=<string>] [--backend=<string>]
         [--output=<file>] <file.ncptl> | --program=<program>

       ncptl --help
""")
    raise SystemExit, exitcode

###########################################################################

# The program starts here.
if __name__ == "__main__":

    # Set default values for our command-line parameters.
    outfilename = "-"
    progname = ""
    backend = "c_union"
    entirefile = None
    backend_options = []
    filter_list = []
    keep_ints = 0
    lenient = 0
    be_verbose = 1

    # Parse the command line.
    end_of_options = "--~!@#$%^&*"
    argumentlist = map(lambda a: re.sub(r'^--$', end_of_options, a), sys.argv[1:])
    success = 0
    filelist = []
    options = []
    shortlongopts = [("h",  "help"),
                     ("c:", "concpath="),    
                     ("o:", "output="),
                     ("b:", "backend="),
                     ("p:", "program=")]
    shortopts = string.join(map(lambda sl: sl[0], shortlongopts), "")
    longopts = map(lambda sl: sl[1], shortlongopts)
    while not success:
        try:
            opts, args = getopt.getopt(argumentlist, shortopts, longopts)
            options.extend(opts)
            if len(args) == 0:
                success = 1
            else:
                filelist.append(args[0])
                argumentlist = args[1:]
        except getopt.error, errormsg:
            unrecognized = re.match(r'option (\S+) not recognized', str(errormsg))
            if unrecognized:
                # Move the unrecognized parameter and everything that
                # follows it from the argumentlist list to the
                # backend_options list.
                unrec = unrecognized.group(1)
                removed  = 0
                for arg in xrange(0, len(argumentlist)):
                    badarg = argumentlist[arg]
                    if unrec == badarg \
                           or unrec+"=" == badarg[0:len(unrec)+1] \
                           or (unrec[1] != '-' and unrec == badarg[0:2]):
                        if unrec == end_of_options:
                            backend_options.extend(argumentlist[arg+1:])
                        else:
                            backend_options.extend(argumentlist[arg:])
                        backend_options = map(lambda s:
                                                  re.sub(r'^(-H|--help-backend)$',
                                                         "--help", s),
                                              backend_options)
                        argumentlist = argumentlist[0:arg]
                        removed = 1
                        break
                if not removed:
                    sys.stderr.write('failed to find "%s" in %s' % (unrec, repr(argumentlist)))
            else:
                sys.stderr.write("%s\n\n" % errormsg)
                usage(1)
    for opt, optarg in options:
        if opt in ("-h", "--help"):
            usage()
        elif opt in ("-c", "--concpath"):
            concpath = optarg
        elif opt in ("-o", "--output"):
            outfilename = optarg
            progname = outfilename.replace(".c","")
        elif opt in ("-b", "--backend"):
            backend = optarg
        elif opt in ("-p", "--program"):
            entirefile = optarg
            infilename = "<command line>"
        else:
            usage(1)
    if len(filelist) > 1 or (len(filelist) > 0 and entirefile != None):
        # We currently allow only one program to be compiled per invocation.
        usage(1)

    # Load Conceptual modules
    try:
        if concpath:
            if be_verbose:
                sys.stderr.write("# Loading Conceptual modules from %s ...\n" %
                                (concpath))
            orig_path = sys.path
            sys.path.insert(0, concpath)
            if os.environ.has_key("NCPTL_PATH"):
                sys.path[:0] = string.split(os.environ["NCPTL_PATH"], ":")
            exec("from ncptl_lexer import NCPTL_Lexer")
            exec("from ncptl_parser import NCPTL_Parser")
            exec("from ncptl_semantic import NCPTL_Semantic")
            exec("from ncptl_config import ncptl_config, expanded_ncptl_config")
            exec("from ncptl_backends import backend_list")
            sys.path = orig_path
    except ImportError, reason:
        sys.stderr.write('unable to load Conceptual modules (reason: %s)' %
                           (str(reason)))


    full_path = os.path.realpath(__file__)
    curpath, filename = os.path.split(full_path)

    # Look for additional backends.
    backend2path = {}
    backend_path = []

    backend_path.append(curpath)
    if os.environ.has_key("NCPTL_PATH"):
        backend_path.extend(string.split(os.environ["NCPTL_PATH"], ":"))
    if concpath:
        backend_path.append(concpath)
    backend_path.extend(sys.path)
    backend_path = map(os.path.normpath, backend_path)
    for bdir in backend_path:
        try:
            for somefile in os.listdir(bdir):
                re_matches = re.search(r'^codegen_(.+)\.py[co]?$', somefile)
                if re_matches:
                    new_backend = re_matches.group(1)
                    if not backend2path.has_key(new_backend):
                        backend2path[new_backend] = os.path.normpath(os.path.join(bdir, somefile))
        except:
            # Ignore non-directories and directories we don't have access to.
            pass


    # Load the named backend.
    try:
        if backend != None:
            if be_verbose:
                sys.stderr.write("# Loading the %s backend from %s ...\n" %
                                 (backend, os.path.abspath(backend2path[backend])))
            orig_path = sys.path
            if concpath:
                sys.path.insert(0, concpath)
            if os.environ.has_key("NCPTL_PATH"):
                sys.path[:0] = string.split(os.environ["NCPTL_PATH"], ":")
            exec("from codegen_%s import NCPTL_CodeGen" % backend)
            sys.path = orig_path
    except ImportError, reason:
        sys.stderr.write('unable to load backend "%s" (reason: %s)' %
                           (backend, str(reason)))

    # Prepare to announce what we're going to compile.  This is useful
    # in case the user mistakenly omitted a filename and doesn't
    # realize that ncptl expects input from stdin.
    if entirefile == None:
        if filelist==[] or filelist[0]=="-":
            infilename = "<stdin>"

            # As a special case, if --help appears on the command
            # line, and we would normally read from standard input,
            # specify a dummy, empty program so the backend will
            # output a help message and exit.  Note that --help *must*
            # be a backend option at this point because we've already
            # processed the frontend's command line and therefore
            # would have already seen a frontend --help.
            if "--help" in sys.argv or "--help-backend" in sys.argv or "-H" in sys.argv:
                if backend == None:
                    sys.stderr.write('backend help cannot be provided unless a backend is specified')
                    sys.stderr.write("\n")
                    usage(1)
                entirefile = ""
        else:
            infilename = filelist[0]


    # Read the entire input file unless a complete program was
    # provided on the command line.
    if entirefile == None:
        try:
            if be_verbose:
                if infilename == "<stdin>":
                    input_program_source = "the standard input device"
                else:
                    input_program_source = infilename
                sys.stderr.write("# Reading a coNCePTuaL program from %s ...\n" % input_program_source)
            if infilename == "<stdin>":
                entirefile = sys.stdin.read()
            else:
                infile = open(infilename)
                entirefile = infile.read()
                infile.close()
        except IOError, (errno, strerror):
            sys.stderr.write("unable to read from %s (%s)" % (infilename, strerror))

    # Instantiate a lexer, parser, and code generator.
    lexer = NCPTL_Lexer()
    parser = NCPTL_Parser(lexer)
    semantic = NCPTL_Semantic()
    if backend != None:
        codegen = NCPTL_CodeGen(backend_options)

    # Compile the program into backend-specific source code.
    try:
        sys.setcheckinterval(100000)
    except AttributeError:
        # Jython 2.2a1 doesn't support sys.setcheckinterval.
        pass
    if be_verbose:
        sys.stderr.write("# Lexing ...\n")
    tokenlist = lexer.tokenize(entirefile, filesource=infilename)
    del lexer
    if be_verbose:
        sys.stderr.write("# Parsing ...\n")
    syntree = parser.parsetokens(tokenlist, filesource=infilename)
    del parser
    if be_verbose:
        sys.stderr.write("# Analyzing program semantics ...\n")
    syntree = semantic.analyze(syntree, filesource=infilename, lenient=lenient)
    del semantic
    if backend == None:
        # If a backend wasn't specified we have nothing left to do.
        if be_verbose:
            sys.stderr.write("# Not compiling %s -- no backend was specified.\n" % infilename)
        sys.exit(0)
    if be_verbose:
        if backend_options == []:
            sys.stderr.write("# Compiling %s using the %s backend ...\n" %
                             (infilename, backend))
        else:
            if len(backend_options) == 1:
                option_word = "option"
            else:
                option_word = "options"
            sys.stderr.write('# Compiling %s using the %s backend with the %s "%s"\n' %
                             (infilename, backend, option_word,
                              string.join(backend_options, " ")))
    codelist = codegen.generate(syntree, filesource=infilename, filetarget=outfilename, sourcecode=entirefile)

    # Write the output file.  Optionally compile it in a
    # backend-specific manner.  Optionally link it in a
    # backend-specific manner.
    if infilename != "<command line>":
        # Put generated files in the current directory.
        infilename = os.path.basename(infilename)

    try:
        if outfilename == "-":
            if be_verbose:
                sys.stderr.write("# Writing to standard output ...\n")
            outfile = sys.stdout
        else:
            if be_verbose:
                sys.stderr.write("# Writing %s ...\n" % outfilename)
            outfile = open(outfilename, "w")
        for oneline in codelist:
            outfile.write("%s\n" % oneline)
        outfile.close()
    except IOError, (errno, strerror):
        sys.stderr.write("unable to produce %s (%s)" % (outfilename, strerror))
    if be_verbose:
        if outfilename == "-":
            sys.stderr.write("# Files generated: <standard output>\n")
        else:
            sys.stderr.write("# Files generated: %s\n" % outfilename)

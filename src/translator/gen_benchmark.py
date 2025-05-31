#!/usr/bin/env python

from __future__ import print_function  # for Python 2 print compatibility
import os
import os
import subprocess
import re
import sys
import argparse
from glob import glob

def insert_if_not_exist(content, idx, hls):
    exist = False
    for i in range(idx[0], idx[1]):
        if hls[i] in content:
            exist = True
            break

    if not exist:
        hls.insert(idx[0], content)

def translate_conc_to_codes(filepath, codespath):
    # get program name
    program_name = filepath.split("/")[-1].replace(".c","")

    with open(filepath, 'r') as infile:
        content = infile.read()
    inLines = content.split('\n')

    eliminate_logging(inLines)
    eliminate_conc_init(inLines)
    make_static_var(inLines)
    manipulate_mpi_ops(inLines, program_name)
    adding_struct(inLines, program_name)

    # output program file
    with open("./conc-"+program_name+".c","w+") as outFile:
        outFile.writelines(["%s\n" % item for item in inLines])

    # modify interface file
    program_struct = "extern struct codes_conceptual_bench "+program_name+"_bench;\n"
    program_struct_idx=[]
    program_definition = "    &"+program_name+"_bench,\n"
    program_definition_idx=[]
    with open(codespath+"src/workload/codes-conc-addon.c","r+") as header:
        hls = header.readlines()
        for idx, line in enumerate(hls):
            if '/* list of available benchmarks begin */' in line:
                program_struct_idx.append(idx+1)
            elif '/* list of available benchmarks end */' in line:
                program_struct_idx.append(idx)
        insert_if_not_exist(program_struct, program_struct_idx, hls)

        for idx, line in enumerate(hls):
            if '/* default benchmarks begin */' in line:
                program_definition_idx.append(idx+1)
            elif '/* default benchmarks end */' in line:
                program_definition_idx.append(idx)
        insert_if_not_exist(program_definition, program_definition_idx, hls)

        header.seek(0)
        header.writelines(hls)

    # modify makefile
    program_compile = "src_libcodes_la_SOURCES += src/workload/conceputal-skeleton-apps/conc-"+program_name+".c\n"
    program_compile_idx = []
    with open(codespath+"Makefile.am","r+") as makefile:
        mfls = makefile.readlines()
        for idx, line in enumerate(mfls):
            if "CONCEPTUAL_LIBS" in line:
                program_compile_idx.append(idx+1)
                break
        for i in range(program_compile_idx[0], len(mfls)):
            if 'endif' in mfls[i]:
                program_compile_idx.append(i)
                break
        insert_if_not_exist(program_compile, program_compile_idx, mfls)        
        makefile.seek(0)
        makefile.writelines(mfls)        


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--conceptual-dir", required=True, help="Path to Conceptual source")
    parser.add_argument("-u", "--union-srcdir", required=True, help="Path to Union source")
    args = parser.parse_args()

    conceptual_dir = os.path.abspath(args.conceptual_dir)
    SRC_DIR = os.path.abspath(args.union_srcdir)
    NCPTL_DIR = os.path.join(SRC_DIR, 'translator')
    BENCH_DIR = os.path.join(SRC_DIR, 'benchmarks')
    REGISTRY_FILE = os.path.join(SRC_DIR, 'union_util.c')
    MAKEFILE_SUBDIR = os.path.join(SRC_DIR, "Makefile.subdir")
    TRANSLATOR = os.path.join(NCPTL_DIR, 'translate.py')
    
    # Translate all .ntpl files to .c
    for fname in os.listdir(NCPTL_DIR):
        if fname.endswith('.ncptl'):
            base = os.path.splitext(fname)[0]
            ncptl_path = os.path.join(NCPTL_DIR, fname)
            c_path = os.path.join(BENCH_DIR, base + '.c')
            retcode = subprocess.call([TRANSLATOR, "-o", c_path, "-c", conceptual_dir, ncptl_path])
            if retcode != 0:
                sys.stderr.write("Error: translation failed\n")
                sys.exit(retcode)

    # Collect all benchmark names
    benchmarks = sorted([
        os.path.splitext(f)[0]
        for f in os.listdir(BENCH_DIR)
        if f.endswith('.c') or f.endswith('.C')
    ])

    # Update benchmark registry in union_util.c
    def extern_block():
        lines = ["/* list of available benchmarks begin */"]
        for b in benchmarks:
            lines.append("extern struct union_conceptual_bench {}_bench;".format(b))
        lines.append("/* list of available benchmarks end */")
        return "\n".join(lines)

    def default_array_block():
        indent = "    "  # Exactly four spaces
        lines = [indent + "/* default benchmarks begin */"]
        for b in benchmarks:
            lines.append(indent + "&{}_bench,".format(b))
        lines.append(indent + "/* default benchmarks end */")
        return "\n".join(lines)

    with open(REGISTRY_FILE, 'r') as f:
        content = f.read()

    content = re.sub(
        r'/\* list of available benchmarks begin \*/.*?/\* list of available benchmarks end \*/',
        extern_block(),
        content,
        flags=re.DOTALL
    )

    content = re.sub(
        r'[ \t]*/\* default benchmarks begin \*/.*?/\* default benchmarks end \*/',
        default_array_block(),
        content,
        flags=re.DOTALL
    )

    with open(REGISTRY_FILE, 'w') as f:
        f.write(content)

    # Update benchmarks in Makefile.subdir
    headers_line = "include_HEADERS = src/union_util.h\n"
    dist_data_line = "dist_data_DATA = src/benchmarks/conceptual.json\n"

    # Collect all .c and .C files
    bench_paths = [f for f in sorted(os.listdir(BENCH_DIR))
                  if f.endswith(".c") or f.endswith(".C")]

    benchmark_sources = ["\tsrc/benchmarks/%s \\" % name for name in bench_paths]

    if benchmark_sources:
        benchmark_sources[-1] = benchmark_sources[-1].rstrip(" \\")

    # Compose the Makefile.subdir content
    with open(MAKEFILE_SUBDIR, "w") as mf:
        mf.write(headers_line + "\n")
        mf.write("src_libunion_la_SOURCES = src/union_util.c \\\n")
        mf.write("\n".join(benchmark_sources))
        mf.write("\n\n" + dist_data_line)


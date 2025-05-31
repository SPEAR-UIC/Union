########################################################################
#
# Code generation module for the coNCePTuaL language:
# C + Union
#
# By Scott Pakin <pakin@lanl.gov>
#
# ----------------------------------------------------------------------
#
# 
# Copyright (C) 2015, Los Alamos National Security, LLC
# All rights reserved.
# 
# Copyright (2015).  Los Alamos National Security, LLC.  This software
# was produced under U.S. Government contract DE-AC52-06NA25396
# for Los Alamos National Laboratory (LANL), which is operated by
# Los Alamos National Security, LLC (LANS) for the U.S. Department
# of Energy. The U.S. Government has rights to use, reproduce,
# and distribute this software.  NEITHER THE GOVERNMENT NOR LANS
# MAKES ANY WARRANTY, EXPRESS OR IMPLIED, OR ASSUMES ANY LIABILITY
# FOR THE USE OF THIS SOFTWARE. If software is modified to produce
# derivative works, such modified software should be clearly marked,
# so as not to confuse it with the version available from LANL.
# 
# Additionally, redistribution and use in source and binary forms,
# with or without modification, are permitted provided that the
# following conditions are met:
# 
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
# 
#   * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer
#     in the documentation and/or other materials provided with the
#     distribution.
# 
#   * Neither the name of Los Alamos National Security, LLC, Los Alamos
#     National Laboratory, the U.S. Government, nor the names of its
#     contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY LANS AND CONTRIBUTORS "AS IS" AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL LANS OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# 
#
########################################################################

import string
import codegen_c_generic

class NCPTL_CodeGen(codegen_c_generic.NCPTL_CodeGen):

    def __init__(self, options=None):
        "Initialize the C + Union code generation module."
        codegen_c_generic.NCPTL_CodeGen.__init__(self, options)
        self.backend_name = "c_union"
        self.backend_desc = "C + Union"

        # Determine the set of build parameters to use.
        self.set_param("CC", "replace",
                       self.get_param("MPICC", self.get_param("CC", "cc")))
        self.set_param("CPPFLAGS", "append",
                       self.get_param("MPICPPFLAGS", ""))
        self.set_param("CFLAGS", "replace",
                       self.get_param("MPICFLAGS",
                                      self.get_param("CFLAGS", "")))
        self.set_param("LDFLAGS", "prepend",
                       self.get_param("MPILDFLAGS", ""))
        self.set_param("LIBS", "prepend",
                       self.get_param("MPILIBS", ""))

        # Process any command-line options targeting the backend itself.
        self.send_function = "UNION_MPI_Send"
        self.isend_function = "UNION_MPI_Isend"
        self.reduce_operation = "UNION_Op_Sum"
        for arg in range(0, len(options)):
            if options[arg] == "--ssend":
                # Use MPI_Send() unless the --ssend option is given,
                # in which case we use MPI_Ssend().
                self.send_function = "UNION_MPI_Ssend"
                self.isend_function = "UNION_MPI_Issend"
            elif options[arg][:9] == "--reduce=":
                # Reduce using UNION_Op_Sum unless an alternative is named.
                self.reduce_operation = options[arg][9:]
            elif options[arg] == "--help":
                # Output a help message.
                self.cmdline_options.extend([
                    ("--ssend",
                     """Use UNION_MPI_Ssend() for point-to-point
                                  communication instead of UNION_MPI_Send()"""),
                    ("--reduce=<string>",
                     """Specify an MPI reduce operator to use for
                                  UNION_MPI_Reduce() and UNION_MPI_Allreduce()
                                  [default: UNION_Op_Sum]""")])
                self.show_help()
                raise SystemExit, 0


    # ----------- #
    # Header code #
    # ----------- #

    def code_specify_include_files_POST(self, localvars):
        "Specify extra header files needed by the c_union backend."
        return [
            "#include \"union_util.h\"",
            "#include <mpi.h>",
            "#include <stdarg.h>"]

    def code_define_macros_POST(self, localvars):
        "Define some macros to simplify the generated C code."
        newmacros = []
        newmacros.extend([
            "/* Define a macro that increments REDUCE's alternate buffer pointer by a byte offset. */",
            "#define CONC_GETALTBUFPTR(S) ((void *)((char *)thisev->s.S.altbuffer + thisev->s.S.bufferofs))",
            "",
            "/* Estimate the number of unique communicators that this program will need.",
            " * (The tradeoff is one of initialization time versus memory consumption.) */",
            "#define ESTIMATED_COMMUNICATORS 128",
            "",
            "/* Specify an operation to use for all reduction operations. */",
            "#define REDUCE_OPERATION %s" % self.reduce_operation,
            '#define REDUCE_OPERATION_NAME "%s"' % self.reduce_operation,
            ""])
        return newmacros

    def code_declare_globals_EXTRA(self, localvars):
        "Declare additional C global variables needed by the c_mpi backend."
        newvars = []
        self.code_declare_var(name="mpi_is_running", rhs="0",
                              comment="1=MPI has been initialized",
                              stack=newvars)
        self.code_declare_var(type="NCPTL_QUEUE *", name="recvreqQ",
                              comment="List of MPI receive requests",
                              stack=newvars)
        self.code_declare_var(type="UNION_Request *", name="recvrequests",
                              comment="List version of recvreqQ",
                              stack=newvars)
        self.code_declare_var(type="NCPTL_QUEUE *", name="recvstatQ",
                              comment="List of MPI receive statuses",
                              stack=newvars)
        self.code_declare_var("UNION_Status *", name="recvstatuses",
                              comment="List version of recvstatQ",
                              stack=newvars)
        self.code_declare_var(type="NCPTL_QUEUE *", name="sendreqQ",
                              comment="List of MPI send requests",
                              stack=newvars)
        self.code_declare_var(type="UNION_Request *", name="sendrequests",
                              comment="List version of sendreqQ",
                              stack=newvars)
        self.code_declare_var(type="NCPTL_QUEUE *", name="sendstatQ",
                              comment="List of MPI send statuses",
                              stack=newvars)
        self.code_declare_var(type="UNION_Status *", name="sendstatuses",
                              comment="List version of sendstatQ",
                              stack=newvars)
        self.code_declare_var(type="NCPTL_SET *", name="communicators",
                              comment="Map from an array of processor flags to an MPI communicator",
                              stack=newvars)
        # self.code_declare_var(type="MPI_Errhandler", name="mpi_error_handler",
        #                       comment="Handle to handle_MPI_error()",
        #                       stack=newvars)
        self.code_declare_var(name="union_tag_ub",
                              comment="Upper bound on an UNION tag value",
                              stack=newvars)
        self.code_declare_var(type="ncptl_int", name="conc_mcast_tallies",
                              arraysize="CONC_MCAST_MPI_NUM_FUNCS", rhs="{0}",
                              comment="Tallies of (static) multicast implementation functions",
                              stack=newvars)


        # Make all declarations static.
        static_newvars = []
        for var in newvars:
            static_newvars.append("static " + var)
        return static_newvars


    # -------------- #
    # Initialization #
    # -------------- #

    def code_def_init_decls_POST(self, localvars):
        "Declare variables needed by code_define_functions_INIT_COMM_1."
        newvars = []
        self.code_declare_var(type="int", name="num_tasks",
                              comment="int version of var_num_tasks needed by UNION_MPI_Comm_size()",
                              stack=newvars)
        self.code_declare_var(type="char *", name="procflags",
                              comment="Array of 1s representing an all-task MPI communicator",
                              stack=newvars)
        self.code_declare_var(type="UNION_Comm", name="comm_world", rhs="UNION_Comm_World",
                              comment="Copy of UNION_Comm_World that we can take the address of",
                              stack=newvars)
        self.code_declare_var(type="void *", name="attr_val",
                              comment="Pointed to the value of UNION_TAG_UB",
                              stack=newvars)
        self.code_declare_var(type="int", name="attr_flag", rhs="0",
                              comment="true=UNION_TAG_UB was extracted; false=not extracted",
                              stack=newvars)
        if self.program_uses_log_file:
            self.code_declare_var(type="char", name="log_key_str", arraysize="128",
                                  comment="String representing the range of valid MPI tags",
                                  stack=newvars)
        return newvars

    def code_def_init_init_PRE(self, localvars):
        "Define extra initialization to be performed before ncptl_init()."
        return [
            " /* Initialize MPI. */",
            # "//(void) MPI_Init(&argc, &argv);",
            "mpi_is_running = 1;"]

    def code_define_functions_INIT_COMM_1(self, localvars):
        "Define extra initialization to be performed after ncptl_init()."
        return [
            # "(void) MPI_Errhandler_create ((MPI_Handler_function *)handle_MPI_error, &mpi_error_handler);",
            # "(void) MPI_Errhandler_set (UNION_Comm_World, mpi_error_handler);",
            "(void) UNION_MPI_Comm_rank(UNION_Comm_World, &physrank);",
            "(void) UNION_MPI_Comm_size(UNION_Comm_World, &num_tasks);",
            "var_num_tasks = (ncptl_int) num_tasks;",
            # "(void) MPI_Comm_get_attr(UNION_Comm_World, UNION_TAG_UB, &attr_val, &attr_flag);",
            "union_tag_ub = (ncptl_int) (attr_flag ? *(int *)attr_val : 32767);"]

    def code_define_functions_PRE(self, localvars):
        "Define some additional functions we need at run time."
        return [
            # "/* Capture MPI errors. */",
            # "static void handle_MPI_error (MPI_Comm *comm, int *errcode, ...)",
            # "{",
            # "va_list args;",
            # "char errstring[MPI_MAX_ERROR_STRING];",
            # "int errstrlen;",
            # "",
            # "va_start (args, errcode);",
            # "if (MPI_Error_string (*errcode, errstring, &errstrlen) == MPI_SUCCESS)",
            # 'fprintf(stderr, "MPI run-time error: %s", errstring);',
            # "else",
            # 'fprintf(stderr, "MPI aborted with unrecognized error code %d", *errcode);',
            # "conc_dummy_var.vp = (void *) comm;   /* Prevent the compiler from complaining that comm is unused. */",
            # "va_end (args);",
            # "}",
            # "",
            "/* Perform the equivalent of MPI_Comm_rank() for an arbitrary process. Not support subgroups */",
            "static int rank_in_MPI_communicator (UNION_Comm subcomm, int global_rank)",
            "{",
            # "  UNION_Group world_group;   /* Group associated with UNION_Comm_World */",
            # "  UNION_Group subgroup;      /* Group associate with subcomm */",
            # "  int subrank;             /* global_rank's rank within subcomm */",
            # "",
            # "  MPI_Comm_group (UNION_Comm_World, &world_group);",
            # "  MPI_Comm_group (subcomm, &subgroup);",
            # "  MPI_Group_translate_ranks (world_group, 1, &global_rank, subgroup, &subrank);",
            # "  return subrank;",
            "  return global_rank;",
            "}",
            "",
            "/* Map an arbitrary tag to within MPI's valid range of [0, union_tag_ub]. */",
            "static ncptl_int map_tag_into_MPI_range (ncptl_int tag)",
            "{",
            "if (tag == NCPTL_INT_MIN)",
            " /* Avoid taking the absolute value of NCPTL_INT_MIN. */",
            "tag = 555666773%s;   /* Arbitrary value */" % self.ncptl_int_suffix,
            "tag = ncptl_func_abs (tag);   /* Only nonnegatives values are allowed. */",
            "if (union_tag_ub < NCPTL_INT_MAX)",
            "tag %= union_tag_ub + 1;",
            "return tag;",
            "}",
            "",
            "/* Given an array of task in/out booleans return an MPI",
            ' * communicator that represents the "in" tasks. */',
            "static UNION_Comm define_MPI_communicator (char *procflags)",
            "{",
            "UNION_Comm *existing_comm;    /* Previously defined MPI communicator */",
            "UNION_Comm new_comm;          /* Newly defined MPI communicator */",
            "",
            "existing_comm = (UNION_Comm *) ncptl_set_find (communicators, (void *)procflags);",
            "if (existing_comm)",
            "return *existing_comm;",
            "/* Do NOT split communicator; just assign existing communicator directly */",
            "new_comm = UNION_Comm_World;",          
            # "(void) MPI_Comm_split (UNION_Comm_World, (int)procflags[physrank], physrank, &new_comm);",
            # "(void) MPI_Errhandler_set (new_comm, mpi_error_handler);",
            "ncptl_set_insert (communicators, (void *)procflags, (void *)&new_comm);",
            "return define_MPI_communicator (procflags);",
            "}"]

    def code_def_init_cmd_line_PRE_PARSE(self, localvars):
        "Prevent MPI_Abort() from being called by --help."
        return ["mpi_is_running = 0;   /* Don't invoke MPI_Abort() after --help. */"]

    def code_def_init_cmd_line_POST_PARSE(self, localvars):
        "Re-enable MPI_Abort()."
        return ["mpi_is_running = 1;"]

    def code_def_init_misc_PRE_LOG_OPEN(self, localvars):
        "Add an extra line to the log file."
        extraloglines = []
        if self.program_uses_log_file:
            extraloglines.extend([
                    'ncptl_log_add_comment ("MPI send routines", "%s() and %s()");' %
                    (self.send_function, self.isend_function),
                    'ncptl_log_add_comment ("MPI reduction operation", REDUCE_OPERATION_NAME);',
                    'sprintf (log_key_str, "[0, %" NICS "]", union_tag_ub);',
                    'ncptl_log_add_comment ("MPI tag range", log_key_str);'])
        return extraloglines

    def code_def_init_misc_EXTRA(self, localvars):
        "Initialize everything else that needs to be initialized."
        return [
            "sendreqQ = ncptl_queue_init (sizeof (UNION_Request));",
            "sendstatQ = ncptl_queue_init (sizeof (UNION_Status));",
            "recvreqQ = ncptl_queue_init (sizeof (UNION_Request));",
            "recvstatQ = ncptl_queue_init (sizeof (UNION_Status));",
            "communicators = ncptl_set_init (ESTIMATED_COMMUNICATORS, var_num_tasks*sizeof(char), sizeof(UNION_Comm));",
            "procflags = (char *) ncptl_malloc (var_num_tasks*sizeof(char), 0);",
            "for (i=0; i<var_num_tasks; i++)",
            "procflags[i] = 1;",
            "ncptl_set_insert (communicators, (void *)procflags, (void *)&comm_world);",
            "ncptl_free (procflags);"]

    def code_define_main_POST_INIT(self, localvars):
        "Finalize the various asynchronous-data queues into lists."
        return [
            "sendrequests = (UNION_Request *) ncptl_queue_contents (sendreqQ, 0);",
            "sendstatuses = (UNION_Status *) ncptl_queue_contents (sendstatQ, 0);",
            "recvrequests = (UNION_Request *) ncptl_queue_contents (recvreqQ, 0);",
            "recvstatuses = (UNION_Status *) ncptl_queue_contents (recvstatQ, 0);"]

    def code_def_init_reseed_BCAST(self, localvars):
        "Broadcast a random-number seed to all tasks."
        bcastcode = []
        self.push("{", bcastcode)
        self.code_declare_var(type="int", name="rndseed_int",
                              rhs="(int) random_seed",
                              comment="Version of random_seed with int type",
                              stack=bcastcode)
        self.pushmany([
            "(void) UNION_MPI_Bcast ((void *)&rndseed_int, 1, UNION_Int, 0, UNION_Comm_World);",
            "random_seed = (ncptl_int) rndseed_int;",
            "}"],
                      stack=bcastcode)
        return bcastcode

    def code_def_init_uuid_BCAST(self, locals):
        "Broadcast logfile_uuid to all tasks."
        return ["(void) UNION_MPI_Bcast ((void *)logfile_uuid, 37, UNION_Char, 0, UNION_Comm_World);"]

    def code_def_mark_used_POST(self, locals):
        "Indicate that rank_in_MPI_communicator() is not an unused function."
        return ["rank_in_MPI_communicator (UNION_Comm_World, 0);"]

    # ------------ #
    # Finalization #
    # ------------ #

    def code_def_finalize_DECL(self, localvars):
        "Store the return value of MPI_Finalize()."
        newvars = []
        self.code_declare_var(type="int", name="mpiresult",
                              comment="Return code from MPI_Finalize()",
                              stack=newvars)
        if self.program_uses_log_file:
            self.code_declare_var(type="char", name="log_key_str", arraysize="128",
                                  comment="String representing the range of valid MPI tags",
                                  stack=newvars)
        return newvars

    def code_def_finalize_PRE(self, localvars):
        "Write some additional data to the log file."
        finalcode = []
        if self.program_uses_log_file:
            self.push("log_key_str[0] = '\\0';", finalcode)
            for mpi_func in ["Bcast", "Alltoall", "Alltoallv"]:
                self.pushmany([
                        "if (conc_mcast_tallies[CONC_MCAST_MPI_%s] > 0) {" % string.upper(mpi_func),
                        "char onefuncstr[50];",
                        'sprintf (onefuncstr, "%%sMPI_%s()*%%" NICS,' % mpi_func,
                        'log_key_str[0] == \'\\0\' ? "" : " ", conc_mcast_tallies[CONC_MCAST_MPI_%s]);' % string.upper(mpi_func),
                        "strcat (log_key_str, onefuncstr);",
                        "}"],
                              stack=finalcode)
            self.pushmany([
                    "if (log_key_str[0] != '\\0')",
                    'ncptl_log_add_comment ("Multicast functions used (statically)", log_key_str);'],
                          stack=finalcode)
        return finalcode

    def code_def_finalize_POST(self, localvars):
        "Finish up cleanly."
        return [
            "mpiresult = 0;",
            "UNION_MPI_Finalize();",
            "mpi_is_running = 0;",
            "exitcode = mpiresult;"]

    def code_def_exit_handler_BODY(self, localvars):
        """
             Terminate all processes in the program if we exited
             without calling conc_finalize().
        """
        return [
            "if (mpi_is_running)",
            "MPI_Abort (UNION_Comm_World, 1);"]


    # ---------------------------- #
    # Point-to-point communication #
    # ---------------------------- #

    def code_declare_datatypes_SEND_STATE(self, localvars):
        "Declare fields in the CONC_SEND_EVENT structure for send events."
        newfields = []
        self.code_declare_var(type="UNION_Request *", name="handle",
                              comment="MPI handle representing an asynchronous send",
                              stack=newfields)
        return newfields

    def code_declare_datatypes_RECV_STATE(self, localvars):
        "Declare fields in the CONC_RECV_EVENT structure for receive events."
        newfields = []
        self.code_declare_var(type="UNION_Request *", name="handle",
                              comment="MPI handle representing an asynchronous receive",
                              stack=newfields)
        return newfields

    def code_def_init_msg_mem_PRE(self, localvars):
        "Flatten sendreqQ and recvreqQ into lists for use by code_def_init_msg_mem_EACH_TAG."
        return [
            "sendrequests = (UNION_Request *) ncptl_queue_contents (sendreqQ, 0);",
            "recvrequests = (UNION_Request *) ncptl_queue_contents (recvreqQ, 0);"]

    def code_def_init_msg_mem_EACH_TAG(self, localvars):
        "Store pointers into sendrequests and recvrequests."
        handlecode = []
        tag = localvars["tag"]
        struct = localvars["struct"]
        if tag == "EV_ASEND":
            self.push("%s.handle = &sendrequests[%s.pendingsends-1];" %
                      (struct, struct),
                      handlecode)
        elif tag == "EV_ARECV":
            self.push("%s.handle = &recvrequests[%s.pendingrecvs-1];" %
                      (struct, struct),
                      handlecode)
        elif tag == "EV_MCAST":
            self.pushmany([
                    "if (%s.mpi_func == CONC_MCAST_MPI_ALLTOALL || %s.mpi_func == CONC_MCAST_MPI_ALLTOALLV)" % (struct, struct),
                    "%s.buffer2 = NULL;" % struct],
                          stack=handlecode)
        elif tag == "EV_REDUCE":
            self.pushmany([
                "if (!%s.altbuffer && %s.receiving)" % (struct, struct),
                "%s.altbuffer = NULL;" % struct],
                          stack=handlecode)
        return handlecode

    def n_send_stmt_BODY(self, localvars):
        "Allocate memory for additional pending sends."
        hookcode = []
        self.push("%s.tag = map_tag_into_MPI_range (%s.tag);" %
                  (localvars["struct"], localvars["struct"]),
                  hookcode)
        if "asynchronously" in localvars["attributes"]:
            self.pushmany([
                    "(void *) ncptl_queue_allocate (sendreqQ);",
                    "(void *) ncptl_queue_allocate (sendstatQ);"],
                          stack=hookcode)
        return hookcode

    def n_recv_stmt_BODY(self, localvars):
        "Allocate memory for additional pending receives."
        hookcode = []
        self.push("%s.tag = map_tag_into_MPI_range (%s.tag);" %
                  (localvars["struct"], localvars["struct"]),
                  hookcode)
        if "asynchronously" in localvars["attributes"]:
            self.pushmany([
                "(void *) ncptl_queue_allocate (recvreqQ);",
                "(void *) ncptl_queue_allocate (recvstatQ);"],
                          stack=hookcode)
        return hookcode

    def code_def_procev_DECL(self, localvars):
        "Declare a status variable for MPI_Recv()."
        newdecls = []
        if self.events_used.has_key("EV_RECV"):
            self.code_declare_var(type="UNION_Status", name="status",
                                  comment="Not needed but required by MPI_Recv()",
                                  stack=newdecls)
        return newdecls

    def code_def_procev_send_BODY(self, localvars):
        "Send a message down a given channel (blocking)."
        return [
            "(void) %s (NULL," % self.send_function,
            "(int)thisev->s.send.size, UNION_Byte,",
            "(int)thisev->s.send.dest, (int)thisev->s.send.tag, UNION_Comm_World);"]

    def code_def_procev_recv_BODY(self, localvars):
        "Receive a message from a given channel (blocking)."
        return [
            "(void) UNION_MPI_Recv (NULL,",
            "(int)thisev->s.recv.size, UNION_Byte,",
            "(int)thisev->s.recv.source, (int)thisev->s.recv.tag,",
            "UNION_Comm_World, &status);"]

    def code_def_procev_asend_BODY(self, localvars):
        "Perform an asynchronous send."
        return [
            "(void) %s (NULL," % self.isend_function,
            "(int)thisev->s.send.size, UNION_Byte,",
            "(int)thisev->s.send.dest, (int)thisev->s.send.tag,",
            "UNION_Comm_World, thisev->s.send.handle);"]

    def code_def_procev_arecv_BODY(self, localvars):
        "Perform an asynchronous receive."
        return [
            "(void) UNION_MPI_Irecv (NULL,",
            "(int)thisev->s.recv.size, UNION_Byte,",
            "(int)thisev->s.recv.source, (int)thisev->s.recv.tag,",
            "UNION_Comm_World, thisev->s.recv.handle);"]

    def code_def_procev_wait_BODY_SENDS(self, localvars):
        "Retry all of the sends that blocked."
        return [
            "(void) UNION_MPI_Waitall ((int)thisev->s.wait.numsends, sendrequests, sendstatuses);"]

    def code_def_procev_wait_BODY_RECVS(self, localvars):
        "Retry all of the receives that blocked."
        return [
            "(void) UNION_MPI_Waitall ((int)thisev->s.wait.numrecvs, recvrequests, recvstatuses);"]


    # ------------------------ #
    # Collective communication #
    # ------------------------ #

    def code_declare_datatypes_SYNC_STATE(self, localvars):
        "Declare fields in the CONC_SYNC_EVENT structure for synchronization events."
        newfields = []
        self.code_declare_var(type="UNION_Comm", name="communicator",
                              comment="Set of tasks to synchronize",
                              stack=newfields)
        return newfields

    def code_declare_communicator(self, source_task, stack):
        """
             Return an MPI communicator representing a set of tasks.
             Note that the source_task argument is allowed to be of
             target_tasks type.
        """
        # Convert source task groups to ordinary tasks.
        if source_task[0] == "let_task":
            source_task, srenamefrom, srenameto = self.task_group_to_task(source_task)
            if srenamefrom != None:
                self.code_declare_var(name=srenameto, rhs=srenamefrom, stack=mcastcode)

        # Declare a communicator representing source_task.
        base_comm = "UNION_Comm_World"
        if source_task[0]=="task_all" or source_task[0]=="all_others":
            return base_comm
        elif source_task[0] in ["task_restricted", "task_expr"]:
            if source_task[0] == "task_expr":
                expression_name = "task %s" % source_task[1]
            else:
                expression_name = "tasks %s such that %s" % source_task[1:3]
            self.pushmany([
                " /* Define a communicator representing %s. */" % expression_name],
                          stack)
            self.code_declare_var(type="char *", name="procflags", rhs="NULL",
                                  comment="Flags indicating whether each task is in or out",
                                  stack=stack)
            self.code_declare_var(type="UNION_Comm", name="subcomm",
                                  comment="MPI subcommunicator to use",
                                  stack=stack)
            if source_task[0] == "task_expr":
                loopvar = self.code_declare_var(suffix="loop", stack=stack)
                expression = "(%s == (%s))" % (loopvar, source_task[1])
            else:
                loopvar = source_task[1]
                expression = source_task[2]
                self.code_declare_var(name=loopvar, stack=stack)
            self.pushmany([
                "",
                " /* Determine the set of participating tasks. */",
                "procflags = (char *) ncptl_malloc (var_num_tasks*sizeof(char), 0);",
                "for (%s=0; %s<var_num_tasks; %s++)" % (loopvar, loopvar, loopvar),
                "procflags[ncptl_virtual_to_physical(procmap, %s)] = %s;" % (loopvar, expression),
                "",
                "subcomm = define_MPI_communicator (procflags);",
                "ncptl_free (procflags);"],
                          stack)
            return "subcomm"
        else:
            self.errmsg.error_internal('unable to declare an MPI communicator for source task "%s"' % source_task[0])

    def n_sync_stmt_DECL(self, localvars):
        "Declare a communicator representing the tasks to synchronize."
        synccode = []
        self.communicator = self.code_declare_communicator(localvars["source_task"],
                                                           synccode)
        return synccode

    def n_sync_stmt_INIT(self, localvars):
        "Return the communicator selected by n_sync_stmt_DECL."
        return ["thisev->s.sync.communicator = %s;" % self.communicator]

    def code_def_procev_sync_BODY(self, localvars):
        "Synchronize a set of tasks."
        return ["(void) UNION_MPI_Barrier (thisev->s.sync.communicator);"]

    def n_for_count_SYNC_ALL(self, localvars):
        "Prepare to synchronize all of the tasks in the job."
        return ["thisev_sync->s.sync.communicator = UNION_Comm_World;"]

    def code_synchronize_all_BODY(self, localvars):
        "Immediately synchronize all of the tasks in the job."
        return ["(void) UNION_MPI_Barrier (UNION_Comm_World);"]

    def code_def_procev_etime_REDUCE_MIN(self, localvars):
        "Find the global minimum of the elapsedtime variable."
        return [
            "(void) UNION_MPI_Allreduce (&elapsedtime, &minelapsedtime,",
            "1, UNION_Double, UNION_Op_Min, UNION_Comm_World);"]

    def code_declare_datatypes_PRE(self, localvars):
        "Declare extra datatypes needed by the C+MPI backend."
        return ["/* Enumerate the various mechanisms used to implement MULTICAST statements. */",
                "typedef enum {",
                "CONC_MCAST_MPI_BCAST,       /* One to many */",
                "CONC_MCAST_MPI_ALLTOALL,    /* Many to many, same data to all */ ",
                "CONC_MCAST_MPI_ALLTOALLV,   /* General many to many */",
                "CONC_MCAST_MPI_NUM_FUNCS    /* Number of the above */",
                "} CONC_MCAST_MPI_FUNC;"]

    def code_declare_datatypes_MCAST_STATE(self, localvars):
        "Declare fields in the CONC_MCAST_EVENT structure for multicast events."
        newfields = []
        self.code_declare_var(name="size2",
                              comment="Number of bytes to receive in the many-to-many case",
                              stack=newfields)
        self.code_declare_var(name="bufferofs2",
                              comment="Byte offset into the message buffer in the many-to-many case",
                              stack=newfields)
        self.code_declare_var(type="void *", name="buffer2",
                              comment="Pointer to receive-message memory in the many-to-many case",
                              stack=newfields)
        self.code_declare_var(type="UNION_Comm", name="communicator",
                              comment="Set of tasks to multicast to/from",
                              stack=newfields)
        self.code_declare_var(type="int", name="root",
                              comment="source's rank within communicator",
                              stack=newfields)
        self.code_declare_var(type="int *", name="sndvol",
                              comment="Volume of data to send to each rank in the communicator",
                              stack=newfields)
        self.code_declare_var(type="int *", name="snddisp",
                              comment="Offset from buffer of each message to send",
                              stack=newfields)
        self.code_declare_var(type="int *", name="rcvvol",
                              comment="Volume of data to receive from each rank in the communicator",
                              stack=newfields)
        self.code_declare_var(type="int *", name="rcvdisp",
                              comment="Offset from buffer2 of each message to receive",
                              stack=newfields)
        self.code_declare_var(type="CONC_MCAST_MPI_FUNC", name="mpi_func",
                              comment="MPI function to use to perform the multicast",
                              stack=newfields)
        return newfields

    def n_mcast_stmt_MANY_MANY(self, localvars):
        "Take over the handling of n_mcast_stmt for many-to-many multicasts."
        mcastcode = []

        # Copy values from n_mcast_stmt's scope.
        node = localvars["node"]
        attributes = localvars["attributes"]
        target_tasks = localvars["target_tasks"]
        message_spec = localvars["message_spec"]
        source_task = localvars["source_task"]
        num_messages = localvars["num_messages"]
        if message_spec[3] != "0LL":
            self.errmsg.error_fatal("aligned/misaligned many-to-one and many-to-many multicast messages are not yet implemented by the %s backend" % self.backend_name,
                                    lineno0=node.lineno0, lineno1=node.lineno1)
        if message_spec[5] != "no_touching":
            self.errmsg.error_fatal("touched/verified many-to-one and many-to-many multicast messages are not yet implemented by the %s backend" % self.backend_name,
                                    lineno0=node.lineno0, lineno1=node.lineno1)
        self.push_marker(mcastcode)
        self.push(" /* %s MULTICAST...TO %s */" % (self.tasks_to_text(source_task), self.tasks_to_text(target_tasks)),
                  mcastcode)

        # Declare some of the variables we'll need for MPI_Alltoallv().
        self.push("{", mcastcode)
        self.code_declare_var(name="numsenders", rhs="0"+self.ncptl_int_suffix,
                              comment="Number of sending tasks",
                              stack=mcastcode)
        self.code_declare_var(type="int *", name="sndvol",
                              comment="Number of bytes we send to each other task",
                              stack=mcastcode)
        self.code_declare_var(type="int *", name="snddisp",
                              comment="Buffer offset of each send",
                              stack=mcastcode)
        self.code_declare_var(type="int", name="sndnum", rhs="0",
                              comment="Total number of sends from us",
                              stack=mcastcode)
        self.code_declare_var(type="int *", name="rcvvol",
                              comment="Number of bytes sent to us from each other task",
                              stack=mcastcode)
        self.code_declare_var(type="int *", name="rcvdisp",
                              comment="Buffer offset of each receive",
                              stack=mcastcode)
        self.code_declare_var(type="int", name="rcvnum", rhs="0",
                              comment="Total number of sends to us",
                              stack=mcastcode)
        self.code_declare_var(type="int", name="peervar",
                              comment="Physical rank of one of our peer tasks",
                              stack=mcastcode)
        self.code_declare_var(type="char *", name="procflags",
                              rhs="(char *) ncptl_malloc (var_num_tasks*sizeof(char), 0)",
                              comment="Flags indicating whether each task is in or out",
                              stack=mcastcode)
        self.code_declare_var(type="ncptl_int *", name="sendsfrom",
                              rhs="(ncptl_int *) ncptl_malloc (var_num_tasks*sizeof(ncptl_int), 0)",
                              comment="Tally of sends from each rank",
                              stack=mcastcode)
        self.code_declare_var(type="ncptl_int *", name="recvsby",
                              rhs="(ncptl_int *) ncptl_malloc (var_num_tasks*sizeof(ncptl_int), 0)",
                              comment="Tally of receives by each rank",
                              stack=mcastcode)
        self.code_declare_var(type="int", name="stasknum",
                              comment="A single source task mapped by ncptl_virtual_to_physical()",
                              stack=mcastcode)
        self.code_declare_var(type="int", name="ttasknum",
                              comment="A single target task mapped by ncptl_virtual_to_physical()",
                              stack=mcastcode)
        self.code_declare_var(type="CONC_MCAST_MPI_FUNC", name="mpi_func",
                              comment="The MPI function that will implement the multicast",
                              stack=mcastcode)
        self.communicator = self.code_declare_var(type="UNION_Comm", name="subcomm",
                                                  comment="MPI subcommunicator to use",
                                                  stack=mcastcode)

        # Convert source task groups to ordinary tasks.
        if source_task[0] == "let_task":
            source_task, srenamefrom, srenameto = self.task_group_to_task(source_task)
            if srenamefrom != None:
                self.code_declare_var(name=srenameto, rhs=srenamefrom, stack=mcastcode)
        self.push("", mcastcode)

        # Create a communicator holding all sources and all targets.
        self.pushmany([
                " /* Determine all participants in the many-to-many multicast. */",
                "memset(procflags, 0, var_num_tasks);",
                "memset(sendsfrom, 0, var_num_tasks*sizeof(ncptl_int));",
                "memset(recvsby, 0, var_num_tasks*sizeof(ncptl_int));"],
                      stack=mcastcode)
        if source_task[0] == "task_expr":
            sloopvar = None
            self.pushmany([
                    "if ((%s) >= 0 && (%s) < var_num_tasks) {" % (source_task[1], source_task[1]),
                    "stasknum = (int) ncptl_virtual_to_physical(procmap, %s);" % source_task[1],
                    "procflags[stasknum] = 1;",
                    "numsenders = 1;"],
                          stack=mcastcode)
        else:
            self.push("{", mcastcode)
            sloopvar = self.code_declare_var(name=source_task[1], stack=mcastcode)
            sexpression = source_task[2]
            if sexpression == None:
                # ALL TASKS
                sexpression = "1"
            self.pushmany([
                    "",
                    "for (%s=0; %s<var_num_tasks; %s++)" % (sloopvar, sloopvar, sloopvar),
                    "if (%s) {" % sexpression,
                    "stasknum = (int) ncptl_virtual_to_physical(procmap, %s);" % sloopvar,
                    "procflags[stasknum] = 1;",
                    "numsenders++;"],
                          stack=mcastcode)
        if target_tasks[0] == "task_expr":
            self.pushmany(["ttasknum = (int) ncptl_virtual_to_physical(procmap, %s);" % target_tasks[1],
                           "sendsfrom[stasknum] = 1;",
                           "recvsby[ttasknum] = 1;",
                           "procflags[ttasknum] = 1;"],
                      mcastcode)
        else:
            # Convert target task groups to ordinary tasks.
            if target_tasks[0] == "let_task":
                target_tasks, trenamefrom, trenameto = self.task_group_to_task(target_tasks)
                if trenamefrom != None:
                    self.code_declare_var(name=trenameto, rhs=trenamefrom, stack=stack)

            # Identify the tasks that will receive a message.
            tloopvar = target_tasks[1]
            texpression = target_tasks[2]
            self.push("{", mcastcode)
            tloopvar = self.code_declare_var(name=tloopvar, stack=mcastcode)
            if texpression == None:
                # ALL OTHER TASKS
                if sloopvar == None:
                    # From a single task
                    texpression = "%s != %s" % (tloopvar, source_task[1])
                else:
                    # From potentially more than one task
                    texpression = "%s != %s" % (tloopvar, sloopvar)
            self.pushmany([
                    "",
                    "for (%s=0; %s<var_num_tasks; %s++)" % (tloopvar, tloopvar, tloopvar),
                    "if (%s) {" % texpression,
                    "ttasknum = (int) ncptl_virtual_to_physical(procmap, %s);" % tloopvar,
                    "sendsfrom[stasknum]++;",
                    "recvsby[ttasknum]++;",
                    "procflags[ttasknum] = 1;",
                    "}",
                    "}"],
                          stack=mcastcode)
        self.push("}", mcastcode)
        if source_task[0] != "task_expr":
            self.push("}", mcastcode)
        self.push("subcomm = define_MPI_communicator(procflags);", mcastcode)

        # See if it's safe to use MPI_Alltoall() instead of MPI_Alltoallv().
        self.pushmany([
                "",
                " /* Determine if all participants are sending and receiving the same number",
                "  * and volume of messages.  If so, then we can use the faster MPI_Alltoall()",
                "  * function for the multicast instead of the slower MPI_Alltoallv(). */",
                "{",
                "ncptl_int msgtally = -1;   /* Messages sent or received by any participant */",
                "ncptl_int i;",
                "mpi_func = CONC_MCAST_MPI_ALLTOALL;  /* Use MPI_Alltoall() unless we require MPI_Alltoallv(). */",
                "for (i=0; i<var_num_tasks; i++) {",
                "stasknum = (int) ncptl_virtual_to_physical(procmap, i);",
                "if (procflags[stasknum]) {",
                "if (msgtally == -1)",
                "msgtally = sendsfrom[stasknum];",
                "if (sendsfrom[stasknum] != msgtally || recvsby[stasknum] != msgtally) {",
                "mpi_func = CONC_MCAST_MPI_ALLTOALLV;",
                "break;",
                "}",
                "}",
                "}",
                "}"],
                      stack=mcastcode)

        # As a special case, use MPI_Bcast() for one-to-one and
        # one-to-many multicasts.
        self.pushmany([
                "",
                " /* The following steps are performed only by those tasks who are",
                "  * involved in the communication (as senders and/or receivers). */",
                "if (numsenders > 0 && procflags[physrank]) {"],
                      stack=mcastcode)
        self.code_declare_var(type="int", name="groupsize", rhs="0",
                              comment="Number of MPI ranks represented by subcomm",
                              stack=mcastcode)
        loopvar = self.code_declare_var(suffix="loop", stack=mcastcode)
        self.pushmany([
                "",
                "if (numsenders == 1) {",
                " /* As a special case, use MPI_Bcast() if there's a single sender. */"],
                      stack=mcastcode)
        if sloopvar != None:
            self.code_declare_var(name=sloopvar, rhs="virtrank", stack=mcastcode)
        self.push("conc_mcast_tallies[CONC_MCAST_MPI_BCAST]++;", mcastcode)
        one = "1" + self.ncptl_int_suffix
        if num_messages == "1":
            num_messages = one
        if num_messages != one:
            self.push("for (%s=0; %s<%s; %s++) {" %
                      (loopvar, loopvar, num_messages, loopvar),
                      mcastcode)
        self.code_allocate_event("EV_MCAST", mcastcode)
        struct = "thisev->s.mcast"
        self.code_fill_in_comm_struct(struct, message_spec, attributes,
                                      source_task[1], "source", mcastcode)
        self.pushmany([
                "if (var_num_tasks == 1)",
                "%s.source = 0%s;" % (struct, self.ncptl_int_suffix),
                "%s.mpi_func = CONC_MCAST_MPI_BCAST;  /* One-to-many communication */" % struct],
                      stack=mcastcode)
        self.pushmany(self.invoke_hook("n_mcast_stmt_INIT", locals(),
                                       before=[""]),
                      stack=mcastcode)
        if num_messages != one:
            self.push("}", mcastcode)
        self.push("}", mcastcode)

        # Allocate memory for MPI_Alltoallv()'s use.
        self.pushmany([
                "else {",
                " /* We have more than one sender.",
                "  * Allocate memory for MPI_Alltoallv() to use. */",
                "for (%s=0; %s<var_num_tasks; %s++)" % (loopvar, loopvar, loopvar),
                "groupsize += procflags[%s];" % loopvar,
                "sndvol = (int *) ncptl_malloc(groupsize*sizeof(int), 0);",
                "memset(sndvol, 0, groupsize*sizeof(int));",
                "snddisp = (int *) ncptl_malloc(groupsize*sizeof(int), 0);",
                "memset(snddisp, 0, groupsize*sizeof(int));",
                "rcvvol = (int *) ncptl_malloc(groupsize*sizeof(int), 0);",
                "memset(rcvvol, 0, groupsize*sizeof(int));",
                "rcvdisp = (int *) ncptl_malloc(groupsize*sizeof(int), 0);",
                "memset(rcvdisp, 0, groupsize*sizeof(int));",
                ""],
                      stack=mcastcode)

        # Determine all of the tasks the caller will send to.
        self.push(" /* Determine each task to which I will send data. */", mcastcode)
        self.code_begin_source_scope(source_task, mcastcode)
        if target_tasks[0] == "let_task":
            target_tasks, trenamefrom, trenameto = self.task_group_to_task(target_tasks)
            if trenamefrom != None:
                self.code_declare_var(name=trenameto, rhs=trenamefrom, stack=mcastcode)
        if target_tasks[0] == "all_others":
            targetvar = self.code_declare_var(suffix="loop", stack=mcastcode)
            self.pushmany([
                "for (%s=0; %s<var_num_tasks; %s++)" % (targetvar, targetvar, targetvar),
                "if (%s != virtrank) {" % targetvar],
                          mcastcode)
        elif target_tasks[0] == "task_expr":
            targetvar = target_tasks[1]
            self.code_declare_var(name="virtdest", rhs=targetvar, stack=mcastcode)
            self.push("if (virtdest>=0 && virtdest<var_num_tasks) {",
                      stack=mcastcode)
        elif target_tasks[0] == "task_restricted":
            targetvar = self.code_declare_var(name=target_tasks[1], stack=mcastcode)
            self.pushmany([
                "for (%s=0; %s<var_num_tasks; %s++)" % (targetvar, targetvar, targetvar),
                "if (%s) {" % target_tasks[2]],
                          mcastcode)
        else:
            self.errmsg.error_internal('unknown target task type "%s"' % target_tasks[0])
        self.pushmany([
                " /* In this scope, %s represents a single receiver. */" % targetvar,
                "peervar = rank_in_MPI_communicator (subcomm, ncptl_virtual_to_physical(procmap, %s));" % targetvar,
                "sndvol[peervar] = (int) (%s);" % message_spec[2],
                "snddisp[peervar] = (int) (sndnum * (%s));" % message_spec[2],
                "sndnum++;",
                "}"],
                      stack=mcastcode)
        self.code_end_source_scope(source_task, mcastcode)

        # Determine all of the tasks who will send to the caller.
        self.push("", mcastcode)
        self.push(" /* Determine each task who will send data to me. */", mcastcode)
        sourcevar = self.code_begin_target_loop(source_task, target_tasks, mcastcode)
        self.pushmany([
                " /* Register that task %s will send us data. */" % sourcevar,
                "peervar = rank_in_MPI_communicator (subcomm, ncptl_virtual_to_physical(procmap, %s));" % sourcevar,
                "rcvvol[peervar] = (int) (%s);" % message_spec[2],
                "rcvdisp[peervar] = (int) (rcvnum * (%s));" % message_spec[2],
                "rcvnum++;"],
                      stack=mcastcode)
        self.code_end_target_loop(source_task, target_tasks, mcastcode)
        self.push("", mcastcode)

        # Adjust sndnum and rcvnum if we're using MPI_Alltoall().
        self.pushmany([
                " /* MPI_Alltoall() includes sends to self.  Adjust sndnum and rcvnum appropriately. */",
                "if (mpi_func == CONC_MCAST_MPI_ALLTOALL) {",
                "UNION_MPI_Comm_size (subcomm, &sndnum);",
                "rcvnum = sndnum;",
                "}",
                ""],
                      stack=mcastcode)

        # Perform the correct number of multicasts.
        one = "1" + self.ncptl_int_suffix
        if num_messages == "1":
            num_messages = one
        if num_messages == one:
            self.pushmany([
                    " /* Prepare to multicast a message. */",
                    "conc_mcast_tallies[mpi_func]++;",
                    "if (1) {"],
                          stack=mcastcode)
        else:
            self.pushmany([
                    " /* Prepare to multicast %s messages. */" % num_messages,
                    "conc_mcast_tallies[mpi_func]++;",
                    "if (1) {"],
                          stack=mcastcode)
            loopvar = self.code_declare_var(suffix="loop", stack=mcastcode)
            self.push("for (%s=0; %s<%s; %s++) {" %
                      (loopvar, loopvar, num_messages, loopvar),
                      mcastcode)
        self.code_allocate_event("EV_MCAST", mcastcode)
        struct = "thisev->s.mcast"
        alt_message_spec = list(message_spec)
        alt_message_spec[2] = "sndnum * (%s)" % message_spec[2]
        self.code_fill_in_comm_struct(struct, alt_message_spec, attributes, None, None, mcastcode)
        self.pushmany([
                "%s.bufferofs2 = %s;" % (struct, alt_message_spec[7]),
                "%s.size2 = rcvnum * (%s);" % (struct, message_spec[2]),
                "//(void) ncptl_malloc_message (%s.size2 + %s.bufferofs2, %s.alignment, %s.buffernum+1, %s.misaligned);" % (struct, struct, struct, struct, struct),
                "%s.buffer2 = NULL;" % struct,
                "%s.communicator = subcomm;" % struct,
                "if (%s.tag != 0%s)" % (struct, self.ncptl_int_suffix),
                'ncptl_fatal ("The %s backend does not support nonzero tags in MULTICAST statements");' % self.backend_name],
                      stack=mcastcode)
        for a2av_var in ["sndvol", "snddisp", "rcvvol", "rcvdisp"]:
            self.push("%s.%s = %s;" % (struct, a2av_var, a2av_var), mcastcode)
        self.pushmany([
                "%s.source = -1;" % struct,
                "%s.mpi_func = mpi_func;" % struct,
                "if (mpi_func == CONC_MCAST_MPI_ALLTOALL)",
                "%s.sndvol[0] = %s.rcvvol[0] = %s;" % (struct, struct, message_spec[2])],
                      stack=mcastcode)
        if num_messages != one:
            self.push("}", mcastcode)
        self.push("}", mcastcode)

        # Close all open scopes.
        self.pushmany([
                "}",
                "}",
                "ncptl_free(procflags);",
                "ncptl_free(sendsfrom);",
                "ncptl_free(recvsby);",
                "}"],
                      stack=mcastcode)
        self.combine_to_marker(mcastcode)
        return mcastcode

    def n_mcast_stmt_DECL(self, localvars):
        "Declare a communicator representing the tasks to multicast to/from."
        mcastcode = []
        self.communicator = self.code_declare_communicator(localvars["target_or_source"],
                                                           mcastcode)
        return mcastcode

    def n_mcast_stmt_INIT(self, localvars):
        "Return the communicator selected by n_mcast_stmt_DECL."
        struct = localvars["struct"]
        return [
            "%s.communicator = %s;" % (struct, self.communicator),
            "%s.root = rank_in_MPI_communicator (%s.communicator, %s.source);" %
            (struct, struct, struct),
            "if (%s.tag != 0%s)" % (struct, self.ncptl_int_suffix),
            'ncptl_fatal ("The %s backend does not support nonzero tags in MULTICAST statements");' % self.backend_name]

    def code_def_procev_mcast_BODY(self, localvars):
        "Multicast a message to a set of tasks."
        struct = "thisev->s.mcast"
        return [
            "switch (%s.mpi_func) {" % struct,
            "case CONC_MCAST_MPI_BCAST:",
            " /* One to many */",
            "(void) UNION_MPI_Bcast (NULL, %s.size, UNION_Byte," % struct,
            "%s.root, %s.communicator);" % (struct, struct),
            "break;",
            "case CONC_MCAST_MPI_ALLTOALL:",
            " /* Many to many, same to each */",
            "(void) UNION_MPI_Alltoall (NULL, %s.sndvol[0], UNION_Byte," % struct,
            "NULL, %s.rcvvol[0], UNION_Byte, %s.communicator);" % (struct, struct),
            "break;",
            "case CONC_MCAST_MPI_ALLTOALLV:",
            " /* Many to many, different to each */",
            "(void) UNION_MPI_Alltoallv (NULL, %s.sndvol, %s.snddisp, UNION_Byte," % (struct, struct),
            "NULL, %s.rcvvol, %s.rcvdisp, UNION_Byte, %s.communicator);" % (struct, struct, struct),
            "break;",
            "default:",
            " /* We should never get here. */",
            'ncptl_fatal ("Internal error: Unrecognized multicast function");',
            "break;",
            "}"]

    def code_declare_datatypes_REDUCE_STATE(self, localvars):
        "Declare fields in the CONC_REDUCE_EVENT structure for reduction events."
        newfields = []
        self.code_declare_var(type="void *", name="altbuffer",
                              comment="Pointer to additional message memory",
                              stack=newfields)
        self.code_declare_var(type="UNION_Comm", name="sendcomm",
                              comment="Set of tasks to reduce from",
                              stack=newfields)
        self.code_declare_var(type="UNION_Comm", name="recvcomm",
                              comment="Set of tasks to reduce to",
                              stack=newfields)
        self.code_declare_var(type="UNION_Datatype", name="datatype",
                              comment="MPI datatype to reduce",
                              stack=newfields)
        self.code_declare_var(type="int", name="reducetype",
                              comment="0=reduce; 1=allreduce; 2=reduce+bcast",
                              stack=newfields)
        self.code_declare_var(name="reduceroot",
                              comment="Root task of the reduction if reducetype is 0 or 2",
                              stack=newfields)
        self.code_declare_var(name="bcastroot",
                              comment="Root task of the multicast if reducetype is 2",
                              stack=newfields)
        return newfields

    def n_reduce_stmt_DECL(self, localvars):
        "Declare variables needed to characterize the reduction."
        reducecode = []
        allreduce = localvars["allreduce"]
        if not allreduce:
            self.code_declare_var(type="int", name="allreduce",
                                  comment="1=senders are the same as receivers",
                                  stack=reducecode)
            self.code_declare_var(type="int", name="disjoint",
                                  comment="1=no sender is also a receiver",
                                  stack=reducecode)
            self.code_declare_var(name="first_shared",
                                  rhs="-1%s" % self.ncptl_int_suffix,
                                  comment="Task ID of the first task that's both a sender and a receiver",
                                  stack=reducecode)
        self.code_declare_var(type="UNION_Comm", name="sendcomm",
                              comment="Set of tasks to reduce from",
                              stack=reducecode)
        self.code_declare_var(type="UNION_Comm", name="recvcomm",
                              comment="Set of tasks to reduce to",
                              stack=reducecode)
        return reducecode

    def n_reduce_stmt_HAVE_PEERS(self, localvars):
        "Determine the type of reduction operation we're about to perform"
        reducecode = []
        allreduce = localvars["allreduce"]

        # Determine at run time if we have an all-reduce situation.
        if not allreduce:
            self.pushmany([
                " /* Determine if the set of senders matches",
                "  * exactly the set of receivers. */",
                "allreduce = 1;",
                "for (i=0; i<var_num_tasks; i++)",
                "if (reduce_receivers[i] != reduce_senders[i]) {",
                "allreduce = 0;",
                "break;",
                "}",
                "",
                " /* Store the task ID of the first task that's both a sender and a receiver. */",
                "if (!allreduce)",
                "for (i=0; i<var_num_tasks; i++)",
                "if (reduce_senders[i] && reduce_receivers[i]) {",
                "first_shared = i;",
                "break;",
                "}",
                "",
                " /* Bridge a disjoint reduce/broadcast by ensuring",
                "  * that the first sender is also a receiver. */",
                "disjoint = first_shared == -1%s;" % self.ncptl_int_suffix,
                "if (disjoint)",
                "for (i=0; i<var_num_tasks; i++)",
                "if (reduce_senders[i]) {",
                "reduce_receivers[i] = 1;",
                "first_shared = i;",
                "break;"
                "}"],
                          stack=reducecode)

        # Create a send communicator by faking a source_task tuple.
        self.pushmany([
            "",
            " /* Store a communicator that represents the physical ranks of reduce_senders[]. */",
            "{"],
                      stack=reducecode)
        loopvar = self.newvar(suffix="loop")
        sender_tasks = ("task_restricted", loopvar, "reduce_senders[%s]" % loopvar)
        sendcomm = self.code_declare_communicator(sender_tasks, reducecode)
        self.push("sendcomm = %s;" % sendcomm, reducecode)
        if allreduce:
            self.push("recvcomm = %s;" % sendcomm, reducecode)
        self.push("}", reducecode)

        # Create a receive communicator by faking a source_task tuple.
        if not allreduce:
            self.pushmany([
                "",
                " /* Store a communicator that represents the physical ranks of reduce_receivers[]. */",
                "{"],
                          stack=reducecode)
            loopvar = self.newvar(suffix="loop")
            receiver_tasks = ("task_restricted", loopvar, "reduce_receivers[%s]" % loopvar)
            recvcomm = self.code_declare_communicator(receiver_tasks, reducecode)
            self.push("recvcomm = %s;" % recvcomm, reducecode)
            self.push("}", reducecode)
        return reducecode

    def n_reduce_stmt_INIT(self, localvars):
        "Define communicators and store both the communicators and the reduction type."
        initcode = []
        struct = localvars["struct"]
        allreduce = localvars["allreduce"]

        # Determine whether to use MPI_Reduce(), MPI_Allreduce(), or
        # MPI_Reduce()+MPI_Bcast().
        if allreduce:
            # We know at compile time that we have an allreduce.
            self.push("%s.reducetype = 1;" % struct, initcode)
        else:
            # We have to check at run time for the type of reduction.
            self.pushmany([
                "",
                " /* Store the type of reduction we intend to perform. */",
                "if (numreceivers == 1 && !disjoint)",
                "%s.reducetype = 0;" % struct,
                "else",
                "if (allreduce)",
                "%s.reducetype = 1;" % struct,
                "else",
                "%s.reducetype = 2;" % struct,
                "",
                " /* Fill in the remainder of the reduce structure. */",
                "%s.reduceroot = rank_in_MPI_communicator (sendcomm, ncptl_virtual_to_physical(procmap, first_shared));" % struct,
                "%s.bcastroot = rank_in_MPI_communicator (recvcomm, ncptl_virtual_to_physical(procmap, first_shared));" % struct],
                      stack=initcode)
        return initcode

    def n_reduce_stmt_INIT2(self, localvars):
        "Assign a value to the altbuffer member of the reduce structure."
        initcode = []
        struct = localvars["struct"]

        # Handle the alternate buffer field differently based on whether the
        # message buffer is supposed to be unique.
        self.pushmany([
                " /* Perform some c_mpi-specific structure initialization. */",
                "if (%s.tag != 0%s)" % (struct, self.ncptl_int_suffix),
                'ncptl_fatal ("The %s backend does not support nonzero tags in REDUCE statements");' % self.backend_name],
                      stack=initcode)
        if string.upper(localvars["uniqueness"]) == "UNIQUE":
            alignment = localvars["alignment"]
            self.push("if (%s.receiving)" % struct, initcode)
            if localvars["misaligned"]:
                self.push("%s.altbuffer = ncptl_malloc_misaligned (message_size + %s.bufferofs, %s);" %
                          (struct, struct, alignment),
                          initcode)
            else:
                self.push("%s.altbuffer = ncptl_malloc (message_size + %s.bufferofs, %s);" %
                          (struct, struct, alignment),
                          initcode)
            self.push("else", initcode)
            self.push("%s.altbuffer = NULL;" % struct, initcode)
        else:
            # We don't have to invoke ncptl_malloc_message here
            # because the parameters are the same as for the BUFFER
            # structure member.
            self.push("%s.altbuffer = NULL;" % struct, initcode)
        self.pushmany([
            "switch (%s.itemsize) {" % struct,
            "case 4%s:" % self.ncptl_int_suffix,
            "%s.datatype = UNION_Int;" % struct,
            "break;",
            "",
            "case 8%s:" % self.ncptl_int_suffix,
            "%s.datatype = UNION_Double;" % struct,
            "break;",
            "",
            "default:",
            'ncptl_fatal ("Internal error -- unable to reduce data of size %%" NICS " byte(s)", %s.itemsize);' % struct,
            "break;",
            "}",
            "%s.sendcomm = sendcomm;" % struct,
            "%s.recvcomm = recvcomm;" % struct,
            "//(void) ncptl_malloc_message (message_size + %s.bufferofs, %s.alignment, %s.buffernum+1, %s.misaligned);   /* altbuffer uses buffernum+1. */" %
            (struct, struct, struct, struct)],
                      stack=initcode)
        return initcode

    def code_def_procev_reduce_BODY(self, localvars):
        "Reduce one or more values and distribute the result."
        struct = "thisev->s.reduce"
        reducecode = []
        self.pushmany([
            "switch (%s.reducetype) {" % struct,
            "case 0:",
            " /* Reduce to a single task. */",
            "(void) UNION_MPI_Reduce (NULL, NULL, %s.numitems," % struct,
            "%s.datatype, REDUCE_OPERATION, %s.reduceroot, %s.sendcomm);" %
            (struct, struct, struct),
            "break;",
            "",
            "case 1:",
            " /* Reduce from a set of tasks to the same set of tasks. */",
            "(void) UNION_MPI_Allreduce (NULL, NULL, %s.numitems," % struct,
            "%s.datatype, REDUCE_OPERATION, %s.sendcomm);" % (struct, struct),
            "break;",
            "",
            "case 2:",
            " /* Reduce from one set of tasks to a different set. */",
            "if (%s.sending)" % struct,
            "(void) UNION_MPI_Reduce (NULL, NULL, %s.numitems," % struct,
            "%s.datatype, REDUCE_OPERATION, %s.reduceroot, %s.sendcomm);" %
            (struct, struct, struct),
            "if (%s.receiving)" % struct,
            "(void) UNION_MPI_Bcast (NULL, %s.numitems," % struct,
            "%s.datatype, %s.bcastroot, %s.recvcomm);" % ((struct,)*3),
            "break;",
            "",
            "default:",
            'ncptl_fatal ("Internal error -- unknown reduction type");',
            "}"],
                      stack=reducecode)
        if self.program_uses_touching:
            localvars["msgbuffer"] = "%s.altbuffer" % struct
        return reducecode

    def n_log_stmt(self, node):
        "Log an expression to a particular row+column of a log file."
        self.program_uses_log_file = 0
        entrylist = self.pop()
        source_task = self.pop()
        istack = self.init_elements
        self.push_marker(istack)

        # Write a comment string.
        comment = " /* %s LOGS " % self.tasks_to_text(source_task)
        for logentry in range(len(entrylist)):
            description = self.clean_comments(entrylist[logentry][0])
            if logentry == 0:
                comment = comment + "%s " % description
            else:
                comment = comment + "AND %s " % description
        comment = comment + "*/"
        self.push(comment, istack)
        self.code_allocate_code_event(source_task,
                                      string.join(map(lambda e: e[1], entrylist)),
                                      node.sem.has_key("needs_procmap"),
                                      istack)
        self.combine_to_marker(istack)

        # Generate the corresponding code.
        astack = self.arbitrary_code
        self.push_marker(astack)
        self.pushmany([
            comment,
            "if (!suppress_output) {"],
                      astack)

        self.code_clock_control("DECLARE", astack)
        self.code_clock_control("STOP", astack)
        for description, expression, aggregate, agg_arg in entrylist:
            clean_desc = string.replace(description, "\\n", " ")
            if aggregate:
                aggregate_enum = "NCPTL_FUNC_" + string.upper(aggregate)
            else:
                aggregate_enum = "NCPTL_FUNC_NO_AGGREGATE"
            self.push('ncptl_log_write (logstate, %s, %s, %s, %s, %s);' %
                       (self.logcolumn, clean_desc, aggregate_enum, agg_arg,
                        self.code_make_expression_fp(expression)),
                      astack)
            self.logcolumn = self.logcolumn + 1
        self.code_clock_control("RESTART", astack)
        self.push("}", astack)
        self.combine_to_marker(astack)

    def n_log_flush_stmt(self, node):
        """Compute the previously specified aggregate functions and
        write the results to the log file."""
        self.program_uses_log_file = 0
        source_task = self.pop()
        istack = self.init_elements
        self.push_marker(istack)
        self.push(" /* %s COMPUTES AGGREGATES */" % self.tasks_to_text(source_task), istack)
        self.code_begin_source_scope(source_task, istack)
        self.code_allocate_event("EV_FLUSH", declare="(void)", stack=istack)
        self.code_end_source_scope(source_task, istack)
        self.combine_to_marker(istack)


    def code_declare_globals(self, node):
        "Declare all of the C global variables the generated code may need."

        # Output a section comment.
        self.pushmany([
            "/********************",
            " * Global variables *",
            " ********************/",
            ""])

        # Declare all of the exported variables, which are maintained
        # automatically by the code generator.
        self.push("/* Variables exported to coNCePTuaL programs */")
        for variable, meaning in self.exported_vars.items():
            self.push("static %s %s = %d;   /* %s */" %
                      (meaning[0], variable, int(variable=="var_num_tasks"), meaning[1]))
        self.push("")

        # Create a dummy variable to help silence whiny compilers.
        self.push("/* Dummy variable to help mark other variables as used */")
        self.pushmany([
            "static union {",
            "ncptl_int ni;",
            "int i;",
            "void *vp;"])
        self.pushmany(self.invoke_hook("code_declare_globals_DUMMY_VAR", locals()))
        self.pushmany([
            "} conc_dummy_var;",
            ""])

        # Declare all of the boilerplate variables, both generic C and
        # backend-specific.
        self.pushmany([
            "/* Variables used internally by boilerplate code */",
            "static uint64_t starttime;   /* Time the clock was last reset (microseconds) */",
            "static ncptl_int pendingrecvs = 0;   /* Current # of outstanding receives */",
            "static ncptl_int pendingrecvbytes = 0; /* Current # of bytes in outstanding receives */",
            "static NCPTL_QUEUE *touchedqueue;      /* Queue of asynchronous receives to touch */",
            "static ncptl_int pendingsends = 0;   /* Current # of outstanding sends */",
            "static NCPTL_QUEUE *eventqueue;   /* List of coNCePTuaL events to perform */",
            "static int within_time_loop = 0;   /* 1=we're within a FOR <time> loop */",
            "static int suppress_output = 1;    /* 1=suppress output to stdout and the log file */",
            "static void *touch_region = NULL;   /* Memory region to touch */",
            "static ncptl_int touch_region_size = 0;   /* # of bytes in the above */",
            "static int virtrank;    /* This task's virtual rank in the computation */",
            "static int physrank;    /* This task's physical rank in the computation */",
            "static NCPTL_VIRT_PHYS_MAP *procmap;  /* Virtual to physical rank mapping */"])
        if self.program_uses_randomness >= 1:
            self.push("static ncptl_int random_seed;   /* Seed for the random-number generator */")
        self.push("static NCPTL_LOG_FILE_STATE *logstate;   /* Opaque object representing all log-file state */")
        if self.program_uses_log_file:
            self.pushmany([
                "static char *logfile_uuid;   /* Execution UUID to write to every log file */"])
        if self.stores_restores_vars:
            self.push("static NCPTL_QUEUE *expvarstack;   /* Stack of exported-variable values */")
        self.pushmany([
            "static char *logfiletmpl;   /* Template for the log file's name */"])
        if self.define_eventnames:
            self.push("static char *eventnames[NUM_EVS];   /* Name of each event */")
        self.pushmany(self.invoke_hook("code_declare_globals_EXTRA", locals(),
                                       before=[
            "",
            "/* Global variables specific to the %s backend */" % self.backend_name]))

        # Declare variables corresponding to those in the user's code.
        if self.global_declarations:
            self.push("")
            self.push("/* Program-specific variables */")
            for decl in self.global_declarations:
                self.push("static %s" % decl)

        # Declare variables and functions provided as literal code by one
        # or more BACKEND DECLARES statements.
        if self.backend_declarations:
            self.pushmany(["",
                           "/************************************",
                           " * Variables and functions declared *",
                           " * using BACKEND DECLARES           *",
                           " ************************************/",
                           ""])
            for decl in self.backend_declarations:
                self.push(decl)


    def code_def_init_cmd_line(self, node):
        "Parse the command line."

        # Prepare to parse the command line.
        self.push(" /* Plug variables and default values into the NCPTL_CMDLINE structure. */")
        self.pushmany(self.invoke_hook("code_def_init_cmd_line_PRE_ARGS", locals()))
        short2index = {}
        for paramnum in range(0, len(self.global_parameters)):
            vartype, ident, longform, shortform, description, defvalue = \
                     self.global_parameters[paramnum]
            short2index[shortform] = paramnum
            self.push("arguments[%d].variable = (CMDLINE_VALUE *) &%s;" %
                       (paramnum, ident))
            if vartype == "NCPTL_TYPE_INT":
                self.push('arguments[%d].defaultvalue.intval = %s;' %
                           (paramnum, defvalue))
            elif vartype == "NCPTL_TYPE_STRING":
                if defvalue != "OVERWRITTEN":
                    self.push('arguments[%d].defaultvalue.stringval = "%s";' %
                              (paramnum, defvalue))
            else:
                self.errmsg.error_internal('command-line parameter is "%s"' %
                                           (self.thisfile, str(defvalue)))
        self.pushmany(self.invoke_hook("code_def_init_cmd_line_POST_ARGS", locals()))
        self.push("")

        # Parse the command line.
        self.push(" /* Parse the command line. */")
        self.pushmany(self.invoke_hook("code_def_init_cmd_line_PRE_PARSE", locals()))
        self.pushmany([
            "ncptl_parse_command_line (argc, argv, arguments, sizeof(arguments)/sizeof(NCPTL_CMDLINE));",
            "if (help_only)",
            'ncptl_fatal ("Internal error in the c_generic backend: failed to exit after giving help");'])
        self.pushmany(self.invoke_hook("code_def_init_cmd_line_POST_PARSE", locals()))

    def code_fill_in_comm_struct(self, struct, message_spec, attributes,
                                 targetvar, rankvar, stack=None,
                                 verification=1):
        "Fill in common fields of various communication-state structures."
        num_messages, uniqueness, message_size, alignment, misaligned, touching, tag, buffer_ofs, buffer_num = message_spec

        # Fill in most of the fields.
        if rankvar != None and targetvar != None:
            self.push("%s.%s = ncptl_virtual_to_physical (procmap, %s);" % (struct, rankvar, targetvar), stack)
        if message_size != None:
            self.push("%s.size = %s;" % (struct, message_size), stack)
        if alignment != None:
            self.push("%s.alignment = %s;" % (struct, alignment), stack)
        if misaligned != None:
            self.push("%s.misaligned = %s;" % (struct, misaligned), stack)
        if touching != None:
            self.push("%s.touching = %d;" % (struct, int(touching=="touching")), stack)
            if verification:
                self.push("%s.verification = %d;" % (struct, int(touching=="verification")), stack)
        self.push("%s.tag = %s;" % (struct, tag), stack)
        self.push("%s.pendingsends = pendingsends;" % struct, stack)
        self.push("%s.pendingrecvs = pendingrecvs;" % struct, stack)
        if buffer_ofs != None:
            self.push("%s.bufferofs = %s;" % (struct, buffer_ofs), stack)

        # The buffer_num field is assigned in one of many different ways.
        if buffer_num != None:
            if buffer_num != "default":
                self.push("if (%s < 0%s)" % (buffer_num, self.ncptl_int_suffix), stack)
            if "asynchronously" in attributes:
                self.push("%s.buffernum = pendingsends+pendingrecvs;" % struct, stack)
            elif verification:
                self.push("%s.buffernum = %s.verification ? pendingsends+pendingrecvs : 0;" %
                          (struct, struct),
                          stack)
            else:
                self.push("%s.buffernum = 0%s;" % (struct, self.ncptl_int_suffix), stack)
            if buffer_num != "default":
                self.pushmany([
                    "else",
                    "%s.buffernum = %s;" % (struct, buffer_num)],
                              stack)

        # Handle the buffer field differently based on whether the
        # message buffer is supposed to be unique.
        if None not in [uniqueness, message_size, alignment]:
            if uniqueness == "unique":
                if misaligned == 1:
                    self.push("%s.buffer = NULL;" %
                              (struct),
                              stack)
                else:
                    self.push("%s.buffer = NULL;" %
                              (struct),
                              stack)
            else:
                self.pushmany([
                    "//(void) ncptl_malloc_message (%s.size+%s.bufferofs, %s.alignment, %s.buffernum, %s.misaligned);" %
                    (struct, struct, struct, struct, struct),
                    "%s.buffer = NULL;" % struct],
                              stack)


    def code_def_init_msg_mem(self, node):
        "Allocate memory for message buffers."

        # Allocate message memory.
        msg_events = {"EV_SEND":   "send",
                      "EV_ASEND":  "send",
                      "EV_RECV":   "recv",
                      "EV_ARECV":  "recv",
                      "EV_MCAST":  "mcast",
                      "EV_REDUCE": "reduce"}
        self.pushmany([
            " /* Allocate memory for non-unique messages and asynchronous",
            "  * message handles now that we know how much memory we need",
            "  * to allocate. */",
            "eventlist = (CONC_EVENT *) ncptl_queue_contents (eventqueue, 0);",
            "numevents = ncptl_queue_length (eventqueue);"])
        self.pushmany(self.invoke_hook("code_def_init_msg_mem_PRE", locals()))
        self.pushmany([
            "for (i=0; i<numevents; i++) {",
            "CONC_EVENT *thisev = &eventlist[i];   /* Cache of the current event */",
            "switch (thisev->type) {"])
        for tag, field in msg_events.items():
            if self.events_used.has_key(tag):
                struct = "thisev->s.%s" % field
                sizefield = "%s.bufferofs + " % struct
                if tag == "EV_REDUCE":
                    sizefield += "%s.numitems * %s.itemsize" % (struct, struct)
                else:
                    sizefield += "%s.size" % struct
                self.pushmany([
                    "case %s:" % tag,
                    "if (!%s.buffer)" % struct,
                    "%s.buffer = NULL;" % struct])
                if tag != "EV_REDUCE":
                    self.pushmany([
                        "if (%s.verification)" % struct,
                        "//ncptl_fill_buffer (CONC_GETBUFPTR(%s), %s, -1);" % (field, sizefield)])
                self.pushmany(self.invoke_hook("code_def_init_msg_mem_EACH_TAG", locals()))
                self.push("break;")
                self.push("")
        self.pushmany([
            "default:",
            "break;",
            "}",
            "}"])
        self.pushmany(self.invoke_hook("code_def_init_msg_mem_POST", locals(),
                                       before=[""]))
        self.push("}")

    # For the following, all backends will need to define
    # n_reduce_stmt_DECL and n_reduce_stmt_INIT to initialize
    # thisev->s.reduce.
    def n_reduce_stmt(self, node):
        "Reduce a set of values and multicast the result."
        # Gather all information about the communication.
        allreduce = "allreduce" in node.attr
        if not allreduce:
            target_tasks = self.pop()
        target_message_spec = self.pop()
        source_message_spec = self.pop()
        source_tasks = self.pop()
        if allreduce:
            target_tasks = source_tasks
        istack = self.init_elements
        self.push_marker(istack)
        self.push(" /* %s REDUCE...TO %s */" %
                  (self.tasks_to_text(source_tasks),
                   self.tasks_to_text(target_tasks)),
                  istack)
        if not allreduce and source_tasks == target_tasks:
            # If we know at compile time that the senders must match
            # the receivers then we can consider this an allreduce
            # operation.
            allreduce = 1

        # We haven't yet implemented target message specifications.
        if source_message_spec != target_message_spec:
            self.errmsg.error_fatal('WHO RECEIVES THE RESULT with a different specification is not yet implemented by the %s backend' % self.backend_name,
                                    lineno0=node.lineno0, lineno1=node.lineno1)

        # Determine if we're a sender.
        self.push("{", istack)
        num_open_scopes = 1
        self.code_declare_var(name="reduce_senders", type="char *",
                              comment="1=rank represents a sender; 0=it doesn't",
                              stack=istack)
        self.code_declare_var(name="reduce_receivers", type="char *",
                              comment="1=rank represents a receiver; 0=it doesn't",
                              stack=istack)
        self.code_declare_var(name="numsenders", rhs="0"+self.ncptl_int_suffix,
                              comment="Number of tasks who will compute the reduced values",
                              stack=istack)
        self.code_declare_var(name="numreceivers", rhs="0"+self.ncptl_int_suffix,
                              comment="Number of tasks who will receive the reduced values",
                              stack=istack)
        self.code_declare_var(name="i", stack=istack)
        self.pushmany(self.invoke_hook("n_reduce_stmt_DECL", locals()), stack=istack)
        self.pushmany(self.invoke_hook("n_reduce_stmt_PRE", locals(),
                                       after=[""], before=[
            "",
            " /* Perform initializations specific to the %s backend. */" %
            self.backend_name]),
                      stack=istack)
        self.pushmany([
            " /* Determine the set of senders. */",
            "reduce_senders = (char *) ncptl_malloc (var_num_tasks*sizeof(char), 0);"],
                      stack=istack)
        source_task_var = None
        if source_tasks[0] == "task_all":
            source_task_var = source_tasks[1]
            self.pushmany([
                "for (i=0; i<var_num_tasks; i++)",
                "reduce_senders[i] = 1;",
                "numsenders = var_num_tasks;"],
                          stack=istack)
        else:
            self.pushmany([
                "for (i=0; i<var_num_tasks; i++)",
                "reduce_senders[i] = 0;"],
                          stack=istack)
            if source_tasks[0] == "task_expr":
                self.pushmany([
                    "if ((%s)>=0 && (%s)<var_num_tasks) {" %
                    (source_tasks[1], source_tasks[1]),
                    "reduce_senders[%s] = 1;" % source_tasks[1],
                    "numsenders = 1%s;" % self.ncptl_int_suffix,
                    "}"],
                              stack=istack)
            elif source_tasks[0] == "task_restricted":
                source_task_var = source_tasks[1]
                self.pushmany([
                    "for (i=0; i<var_num_tasks; i++) {",
                    "ncptl_int %s = i;" % source_tasks[1],
                    "if (%s) {" % source_tasks[2],
                    "reduce_senders[i] = 1;",
                    "numsenders++;",
                    "}",
                    "}"],
                              stack=istack)
            else:
                self.errmsg.error_internal('unknown source task type "%s"' % source_tasks[0])

        # Determine if we're a receiver.
        must_close_receiver_scope = 0
        self.pushmany([
            "",
            " /* Determine the set of receivers. */",
            "reduce_receivers = (char *) ncptl_malloc (var_num_tasks*sizeof(char), 0);"],
                      stack=istack)
        if target_tasks[0] == "task_all":
            self.pushmany([
                "for (i=0; i<var_num_tasks; i++)",
                "reduce_receivers[i] = 1;",
                "numreceivers = var_num_tasks;"],
                          stack=istack)
        else:
            self.pushmany([
                "for (i=0; i<var_num_tasks; i++)",
                "reduce_receivers[i] = 0;"],
                          stack=istack)
            if (source_task_var != None
                and re.search(r'\b%s\b' % source_task_var, target_tasks[1])
                and (target_tasks[0] == "task_expr" or target_tasks[1] != source_task_var)):
                self.push("{", istack)
                must_close_receiver_scope = 1
                self.code_declare_var(name=source_task_var,
                                      comment="Source task number",
                                      stack=istack)
                self.pushmany([
                    "for (%s=0; %s<var_num_tasks; %s++)" %
                    (source_task_var, source_task_var, source_task_var),
                    "if (reduce_senders[%s])" % source_task_var],
                              stack=istack)
            if target_tasks[0] == "task_expr":
                self.pushmany([
                    "if ((%s)>=0 && (%s)<var_num_tasks) {" %
                    (target_tasks[1], target_tasks[1]),
                    "reduce_receivers[%s] = 1;" % target_tasks[1],
                    "numreceivers++;",
                    "}"],
                              stack=istack)
            elif target_tasks[0] == "task_restricted":
                self.pushmany([
                    "for (i=0; i<var_num_tasks; i++) {",
                    "ncptl_int %s = i;" % target_tasks[1],
                    "if (%s) {" % target_tasks[2],
                    "reduce_receivers[i] = 1;",
                    "numreceivers++;",
                    "}",
                    "}"],
                              stack=istack)
            else:
                self.errmsg.error_internal('unknown target task type "%s"' % target_tasks[0])
        if must_close_receiver_scope:
            self.push("}", istack)
        self.pushmany(self.invoke_hook("n_reduce_stmt_HAVE_PEERS", locals(),
                                       before=[""]),
                      stack=istack)

        # Enqueue a REDUCE event for every task that is either a
        # sender or a receiver.
        self.pushmany([
            "",
            " /* Enqueue a REDUCE event for each task involved in the reduction. */",
            "if (numsenders && numreceivers && (reduce_senders[virtrank] || reduce_receivers[virtrank])) {"],
                      stack=istack)
        self.code_allocate_event("EV_REDUCE", istack)
        self.code_declare_var(name="message_size",
                              comment="Message size as the product of the number of items and the item size",
                              stack=istack)
        struct = "thisev->s.reduce"
        item_count, uniqueness, data_type, alignment, misaligned, touching, tag, buffer_ofs, buffer_num = source_message_spec
        self.pushmany(self.invoke_hook("n_reduce_stmt_INIT", locals(),
                                       before=[""]),
                      stack=istack)
        self.pushmany([
            "%s.numitems = %s;" % (struct, item_count),
            "%s.itemsize = %s;" % (struct, data_type),
            "%s.sending = reduce_senders[virtrank];" % struct,
            "%s.receiving = reduce_receivers[virtrank];" % struct,
            "message_size = %s.numitems * %s.itemsize;" % (struct, struct)],
                      stack=istack)
        faked_message_spec = (1, uniqueness, None, alignment, misaligned, touching, tag, buffer_ofs, buffer_num)
        self.code_fill_in_comm_struct(struct, faked_message_spec, [], None, None, stack=istack, verification=0)

        # Handle the buffer field differently based on whether the
        # message buffer is supposed to be unique.
        if uniqueness == "unique":
            if misaligned == 1:
                self.push("%s.buffer = NULL;" %
                          (struct),
                          istack)
            else:
                self.push("%s.buffer = NULL;" %
                          (struct),
                          istack)
        else:
            self.push("%s.buffer = NULL;" %
                      (struct),
                      istack)
        self.pushmany(self.invoke_hook("n_reduce_stmt_INIT2", locals(),
                                       before=[""]),
                      stack=istack)
        self.push("}", istack)
        self.pushmany(self.invoke_hook("n_reduce_stmt_POST", locals(),
                                       before=[""]),
                      stack=istack)

        # Free allocated memory.
        self.push("ncptl_free (reduce_receivers);", istack)
        self.push("ncptl_free (reduce_senders);", istack)

        # Close all of our open scopes.
        for i in range(0, num_open_scopes):
            self.push("}", istack)
        self.combine_to_marker(istack)

    def code_def_procev_mcast(self, node):
        "Process an EV_MCAST event."
        if self.events_used.has_key("EV_MCAST"):
            self.pushmany([
                "case EV_MCAST:",
                " /* Synchronous multicast */"])
            if self.program_uses_touching:
                self.pushmany([
                    "if (thisev->s.mcast.source == physrank) {",
                    " /* We're the sender */",
                    "if (thisev->s.mcast.touching)",
                    "//ncptl_touch_data (CONC_GETBUFPTR(mcast), thisev->s.mcast.size);",
                    "else",
                    "if (thisev->s.mcast.verification)",
                    "//ncptl_fill_buffer (CONC_GETBUFPTR(mcast), thisev->s.mcast.size, 1);",
                    "}"])
            self.pushmany(self.invoke_hook("code_def_procev_mcast_BODY", locals(),
                                           alternatepy=lambda loc:
                                           loc["self"].errmsg.error_fatal("the %s backend does not support MULTICASTS" %
                                                                          loc["self"].backend_name)))
            if self.program_uses_touching:
                self.pushmany([
                    "if (thisev->s.mcast.source != physrank) {",
                    " /* We're a receiver */",
                    "if (thisev->s.mcast.touching)",
                    "//ncptl_touch_data (CONC_GETBUFPTR(mcast), thisev->s.mcast.size);",
                    "else",
                    "if (thisev->s.mcast.verification)",
                    "var_bit_errors += ncptl_verify (CONC_GETBUFPTR(mcast), thisev->s.mcast.size);",
                    "}"])
            self.push("break;")
            self.push("")

    def code_def_procev_send(self, node):
        "Process an EV_SEND event."
        if self.events_used.has_key("EV_SEND"):
            self.pushmany([
                "case EV_SEND:",
                " /* Synchronous send */"])
            if self.program_uses_touching:
                self.pushmany([
                    "if (thisev->s.send.touching)",
                    "//ncptl_touch_data (CONC_GETBUFPTR(send), thisev->s.send.size);",
                    "else",
                    "if (thisev->s.send.verification)",
                    "//ncptl_fill_buffer (CONC_GETBUFPTR(send), thisev->s.send.size, 1);"])
            self.pushmany(self.invoke_hook("code_def_procev_send_BODY", locals(),
                                           alternatepy=lambda loc:
                                           loc["self"].errmsg.error_fatal("the %s backend does not support SENDS" %
                                                                          loc["self"].backend_name)))
            self.code_update_exported_vars(["var_bytes_sent",
                                            "var_total_bytes",
                                            "var_msgs_sent",
                                            "var_total_msgs"],
                                           "send")
            self.pushmany(["break;", ""])


    def code_def_procev_asend(self, node):
        "Process an EV_ASEND event."
        if self.events_used.has_key("EV_ASEND"):
            self.pushmany([
                "case EV_ASEND:",
                " /* Asynchronous send */"])
            if self.program_uses_touching:
                self.pushmany([
                    "if (thisev->s.send.touching)",
                    "//ncptl_touch_data (CONC_GETBUFPTR(send), thisev->s.send.size);",
                    "else",
                    "if (thisev->s.send.verification)",
                    "//ncptl_fill_buffer (CONC_GETBUFPTR(send), thisev->s.send.size, 1);"])
            self.pushmany(self.invoke_hook("code_def_procev_asend_BODY", locals(),
                                           alternatepy=lambda loc:
                                           loc["self"].errmsg.error_fatal("the %s backend does not support ASYNCHRONOUSLY SENDS" %
                                                                          loc["self"].backend_name)))
            self.code_update_exported_vars(["var_bytes_sent",
                                            "var_total_bytes",
                                            "var_msgs_sent",
                                            "var_total_msgs"],
                                           "send")
            self.pushmany(["break;", ""])

    def code_def_mark_used(self, node):
        "Declare a function to mark various variables as used."
        self.pushmany([
            "/* Inhibit the compiler from complaining that",
            " * certain variables are defined but not used.",
            " * This function should never be called. */",
            "static void conc_mark_variables_used (void)",
            "{"])
        self.pushmany(self.invoke_hook("code_def_mark_used_PRE", locals()))
        for ni_var in self.exported_vars.keys() + ["pendingrecvbytes", "touch_region_size"]:
            self.push("conc_dummy_var.ni = %s;" % ni_var)
        self.pushmany([
            "conc_dummy_var.vp = touch_region;",
            "conc_dummy_var.i  = within_time_loop;",
            "conc_dummy_var.i  = suppress_output;"])
        self.pushmany(self.invoke_hook("code_def_mark_used_POST", locals()))
        self.push("}")


    def code_define_main(self, node):
        "Declare a main() function for the generated code."

        filename = self.filesource.split("/")[-1]
        progname = ".".join(filename.split(".")[:-1])


        # Output a section comment up to the opening curly brace.
        self.pushmany([
            "/" + "*"*73 + "/",
            "/" + "*"*29 + " MAIN ROUTINE " + "*"*30 + "/",
            "/" + "*"*73 + "/",
            "",
            "/* Program execution starts here. */",
            "static int %s_main (int argc, char *argv[])" % progname,
            "{"])

        # Declare all of the variables we might need within main().
        self.push(" /* Declare variables needed by all C-based backends. */")
        self.code_declare_var(type="CONC_EVENT *", name="eventlist",
                              comment="List of events to execute")
        self.code_declare_var(name="numevents", comment="Number of entries in eventlist[]")
        self.pushmany(self.invoke_hook("code_define_main_DECL", locals(),
                                       before=[
            "",
            " /* Declare variables that are specific to the %s backend. */" %
            self.backend_name]))
        self.push("")

        # Initialize the program.
        self.push(" /* ----- Initialization ----- */")
        self.pushmany(self.invoke_hook("code_define_main_PRE_INIT", locals()))
        self.push("conc_initialize (argc, argv);")
        self.push("eventlist = (CONC_EVENT *) ncptl_queue_contents (eventqueue, 0);")
        self.push("numevents = ncptl_queue_length (eventqueue);")
        self.pushmany(self.invoke_hook("code_define_main_POST_INIT", locals()))
        self.push("starttime = ncptl_time();")
        self.push("")

        # Process every event in the event list but include only the
        # cases we actually require.  All backends will need to define
        # the various code_def_*_BODY functions.
        self.push(" /* ----- Event-list processing ----- */")
        self.pushmany(self.invoke_hook("code_define_main_PRE_EVENTS", locals()))
        self.push("conc_process_events (eventlist, 0, numevents-1, 1);")
        self.pushmany(self.invoke_hook("code_define_main_POST_EVENTS", locals(),
                                       before=[""]))
        self.push("")

        # Finish up cleanly.
        self.pushmany([
            " /* ----- Finalization ----- */",
            "return conc_finalize();",
            "}"])

        # Fill UNION structure
        self.pushmany([
            "/* fill in function pointers for this method */",
            "struct union_conceptual_bench %s_bench = " % progname,
            "{",
            ".program_name = \"%s\"," % progname,
            ".conceptual_main = %s_main," % progname,
            "};"])









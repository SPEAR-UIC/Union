/*
 *
 * See COPYRIGHT notice in top-level directory.
 *
 */

#ifndef UNION_INCLUDE_H
#define UNION_INCLUDE_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ncptl/ncptl.h>

#define MAX_CONC_ARGV 128

typedef int UNION_TAG;
typedef int UNION_Comm;
typedef int UNION_Comm_World;
typedef int UNION_Datatype;
typedef int UNION_Request;
typedef int UNION_Status;
typedef int UNION_Op;
#define UNION_STATUSES_IGNORE (UNION_Status *)1

#define UNION_Comm_World 1
#define UNION_Op_Max 1
#define UNION_Byte 1
#define UNION_Int 4
#define UNION_Double 8

typedef struct union_bench_param union_bench_param;

struct union_bench_param {
    char conc_program[MAX_CONC_ARGV];
    int conc_argc;
    char config_in[MAX_CONC_ARGV][MAX_CONC_ARGV];
    char *conc_argv[MAX_CONC_ARGV];
};

/* object structure */
struct union_conceptual_bench {
    char *program_name; /* name of the conceptual program */
    int (*conceptual_main)(int argc, char *argv[]);
};


void union_conc_add_bench(
        struct union_conceptual_bench const * method);


int union_conc_bench_load(
        const char* program,
        int argc,
        char *argv[]);

void UNION_MPI_Comm_size (UNION_Comm comm, int *size);
void UNION_MPI_Comm_rank( UNION_Comm comm, int *rank );
void UNION_MPI_Finalize();
void UNION_Compute(long ns);
void UNION_MPI_Send(const void *buf,
            int count,
            UNION_Datatype datatype,
            int dest,
            int tag,
            UNION_Comm comm);
void UNION_MPI_Recv(void *buf,
            int count,
            UNION_Datatype datatype,
            int source,
            int tag,
            UNION_Comm comm,
            UNION_Status *status);
void UNION_MPI_Sendrecv(const void *sendbuf,
            int sendcount,
            UNION_Datatype sendtype,
            int dest,
            int sendtag,
            void *recvbuf,
            int recvcount,
            UNION_Datatype recvtype,
            int source,
            int recvtag,
            UNION_Comm comm,
            UNION_Status *status);
void UNION_MPI_Barrier(UNION_Comm comm);
void UNION_MPI_Isend(const void *buf,
            int count,
            UNION_Datatype datatype,
            int dest,
            int tag,
            UNION_Comm comm,
            UNION_Request *request);
void UNION_MPI_Irecv(void *buf,
            int count,
            UNION_Datatype datatype,
            int source,
            int tag,
            UNION_Comm comm,
            UNION_Request *request);
void UNION_MPI_Wait(UNION_Request *request,
            UNION_Status *status);
void UNION_MPI_Waitall(int count,
            UNION_Request array_of_requests[],
            UNION_Status array_of_statuses[]);
void UNION_MPI_Reduce(const void *sendbuf,
            void *recvbuf,
            int count,
            UNION_Datatype datatype,
            UNION_Op op,
            int root,
            UNION_Comm comm);
void UNION_MPI_Allreduce(const void *sendbuf,
            void *recvbuf,
            int count,
            UNION_Datatype datatype,
            UNION_Op op,
            UNION_Comm comm);
void UNION_MPI_Bcast(void *buffer,
            int count,
            UNION_Datatype datatype,
            int root,
            UNION_Comm comm);
void UNION_MPI_Alltoall(const void *sendbuf,
            int sendcount,
            UNION_Datatype sendtype,
            void *recvbuf,
            int recvcount,
            UNION_Datatype recvtype,
            UNION_Comm comm);
void UNION_MPI_Alltoallv(const void *sendbuf,
            const int *sendcounts,
            const int *sdispls,
            UNION_Datatype sendtype,
            void *recvbuf,
            const int *recvcounts,
            const int *rdispls,
            UNION_Datatype recvtype,
            UNION_Comm comm);

void UNION_Mark_Iteration(UNION_TAG iter_tag);

inline void UNION_Type_size(UNION_Datatype type, int* size) {
    *size = type;
}

#ifdef __cplusplus
}
#endif

#endif /* UNION_INCLUDE_H */

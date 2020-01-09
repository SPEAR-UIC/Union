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
#include <mpi.h> 

#define MAX_CONC_ARGV 128

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

void UNION_MPI_Comm_size (MPI_Comm comm, int *size);
void UNION_MPI_Comm_rank( MPI_Comm comm, int *rank );
void UNION_MPI_Finalize();
void UNION_Compute(long ns);
void UNION_MPI_Send(const void *buf, 
            int count, 
            MPI_Datatype datatype, 
            int dest, 
            int tag,
            MPI_Comm comm);
void UNION_MPI_Recv(void *buf, 
            int count, 
            MPI_Datatype datatype, 
            int source, 
            int tag,
            MPI_Comm comm, 
            MPI_Status *status);
void UNION_MPI_Sendrecv(const void *sendbuf, 
            int sendcount, 
            MPI_Datatype sendtype,
            int dest, 
            int sendtag,
            void *recvbuf, 
            int recvcount, 
            MPI_Datatype recvtype,
            int source, 
            int recvtag,
            MPI_Comm comm, 
            MPI_Status *status);
void UNION_MPI_Barrier(MPI_Comm comm);
void UNION_MPI_Isend(const void *buf, 
            int count, 
            MPI_Datatype datatype, 
            int dest, 
            int tag,
            MPI_Comm comm, 
            MPI_Request *request);
void UNION_MPI_Irecv(void *buf, 
            int count, 
            MPI_Datatype datatype, 
            int source, 
            int tag,
            MPI_Comm comm, 
            MPI_Request *request);
void UNION_MPI_Wait(MPI_Request *request,
            MPI_Status *status);
void UNION_MPI_Waitall(int count, 
            MPI_Request array_of_requests[], 
            MPI_Status array_of_statuses[]);
void UNION_MPI_Reduce(const void *sendbuf, 
            void *recvbuf, 
            int count, 
            MPI_Datatype datatype,
            MPI_Op op, 
            int root, 
            MPI_Comm comm);
void UNION_MPI_Allreduce(const void *sendbuf, 
            void *recvbuf, 
            int count, 
            MPI_Datatype datatype,
            MPI_Op op, 
            MPI_Comm comm);
void UNION_MPI_Bcast(void *buffer, 
            int count, 
            MPI_Datatype datatype, 
            int root, 
            MPI_Comm comm);
void UNION_MPI_Alltoall(const void *sendbuf, 
            int sendcount, 
            MPI_Datatype sendtype, 
            void *recvbuf,
            int recvcount, 
            MPI_Datatype recvtype, 
            MPI_Comm comm);
void UNION_MPI_Alltoallv(const void *sendbuf, 
            const int *sendcounts, 
            const int *sdispls,
            MPI_Datatype sendtype, 
            void *recvbuf, 
            const int *recvcounts,
            const int *rdispls, 
            MPI_Datatype recvtype, 
            MPI_Comm comm);

#ifdef __cplusplus
}
#endif

#endif /* UNION_INCLUDE_H */

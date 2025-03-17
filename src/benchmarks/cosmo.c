#include "mpi.h"
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include "union_util.h"

static int cosmo_main(int argc, char *argv[])
{

    int max_iter = atoi(argv[1]);
    int count = atoi(argv[2]);
    long interval_nsec = atol(argv[3]);

    // int *in, *out, *sol;
    int i;
    double startTime, stopTime;
    int rank, size;
    struct timespec tim;
    tim.tv_sec = 0;
    tim.tv_nsec = interval_nsec;

    // MPI_Init(&argc, &argv);
    UNION_MPI_Comm_size(UNION_Comm_World, &size);
    UNION_MPI_Comm_rank(UNION_Comm_World, &rank);
    // in = (int *)malloc( count * sizeof(int) );
    // out = (int *)malloc( count * sizeof(int) );
    // sol = (int *)malloc( count * sizeof(int) );
    // for (i=0; i<count; i++)
    // {
    //     *(in + i) = i;
    //     *(sol + i) = i*size;
    //     *(out + i) = 0;
    // }

    // startTime = MPI_Wtime();
    int fid;
    long sample_size = 8 * 1024 * 1024; /* 8MB */
    for (i=0; i<max_iter; i++) {
        fid = rank*1000+i;
        UNION_IO_OPEN_FILE(fid);
        UNION_IO_WRITE(fid,sample_size);
        UNION_IO_CLOSE_FILE(fid);
        UNION_Compute(interval_nsec);
        nanosleep(&tim, NULL);
        UNION_MPI_Allreduce(NULL, NULL, count, UNION_Int, UNION_Op_Sum, UNION_Comm_World);
        UNION_ANNO_Iteration_End(i);
    }

    // stopTime = MPI_Wtime();

    if (rank==0)
    {
        printf("\nCosmo: Completed %d iterations for comm size %d, Msg Size %d\n", i, size, count);
        // printf("Time elapsed: %f ns\n", (stopTime - startTime)*1000000000);
    }
    // free( in );
    // free( out );
    // free( sol );
    UNION_MPI_Finalize();
    return 0;
}

/* fill in function pointers for this method */
struct union_conceptual_bench cosmo_bench = 
{
.program_name = "cosmo",
.conceptual_main = cosmo_main,
};


#include "mpi.h"
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include "union_util.h"

static int checkpoint_main(int argc, char *argv[])
{

    int max_iter = atoi(argv[1]);
    long checkpoint_size = atol(argv[2]); /* size in byte */
    long interval_nsec = atol(argv[3]);   /* in nanosec */


    // int *in, *out, *sol;
    int i;
    double startTime, stopTime, checkpoint_wr_time;
    int rank, size;
    struct timespec tim;
    tim.tv_sec = 0;
    tim.tv_nsec = interval_nsec;

    // MPI_Init(&argc, &argv);
    UNION_MPI_Comm_size(UNION_Comm_World, &size);
    UNION_MPI_Comm_rank(UNION_Comm_World, &rank);
    long checkpoint_size_per_rank = checkpoint_size/size;

    // startTime = MPI_Wtime();

    for (i=0; i<max_iter; i++) {
        UNION_Compute(interval_nsec);
        nanosleep(&tim, NULL);
        if(rank==0)
          UNION_IO_OPEN_FILE(i);
        UNION_IO_WRITE(i,checkpoint_size_per_rank);
        // UNION_MPI_Barrier(UNION_Comm_World);
        if(rank==0)
          UNION_IO_CLOSE_FILE(i);
    }

    // stopTime = MPI_Wtime();

    if (rank==0)
    {
        printf("\nCheckpoint: Completed %d iterations for size %d, interval %lu ns\n", i, checkpoint_size_per_rank, interval_nsec);
        // printf("Time elapsed: %f ns\n", (stopTime - startTime)*1000000000);
    }
    UNION_MPI_Finalize();
    return 0;
}

/* fill in function pointers for this method */
struct union_conceptual_bench checkpoint_bench = 
{
.program_name = "checkpoint",
.conceptual_main = checkpoint_main,
};


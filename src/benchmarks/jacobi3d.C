/** \file jacobi3d.C
 *  Author: Abhinav S Bhatele
 *  Date Created: December 19th, 2010
 *
 *        ***********  ^
 *      *         * *  |
 *    ***********   *  |
 *    *		*   *  Y
 *    *		*   *  |
 *    *		*   *  |
 *    *		*   *  ~
 *    *		* *
 *    ***********   Z
 *    <--- X --->
 *
 *    X: left, right --> wrap_x
 *    Y: top, bottom --> wrap_y
 *    Z: front, back --> wrap_z
 *
 *  Three dimensional decomposition of a 3D stencil
 */

#include "mpi.h"
#include <stdio.h>
#include <stdlib.h>
#include <strings.h>
#include <math.h>
#include <time.h>
#include "union_util.h"

/* We want to wrap entries around, and because mod operator % sometimes
 * misbehaves on negative values. -1 maps to the highest value.
 */
#define wrap_x(a)	(((a)+num_blocks_x)%num_blocks_x)
#define wrap_y(a)	(((a)+num_blocks_y)%num_blocks_y)
#define wrap_z(a)	(((a)+num_blocks_z)%num_blocks_z)

#define index(a,b,c)	((a)+(b)*(blockDimX+2)+(c)*(blockDimX+2)*(blockDimY+2))
#define calc_pe(a,b,c)	((a)+(b)*num_blocks_x+(c)*num_blocks_x*num_blocks_y)

#define MAX_ITER	10
#define LEFT		1
#define RIGHT		2
#define TOP		3
#define BOTTOM		4
#define FRONT		5
#define BACK		6
#define DIVIDEBY7	0.14285714285714285714

double startTime;
double endTime;

static int jacobi3d_main(int argc, char **argv) {
  int myRank, numPes, maxiter, messageSize;
  long compute_time;

  // MPI_Init(&argc, &argv);
  UNION_MPI_Comm_size(UNION_Comm_World, &numPes);
  UNION_MPI_Comm_rank(UNION_Comm_World, &myRank);
  UNION_Request sreq[6], rreq[6];

  int blockDimX, blockDimY, blockDimZ;
  int arrayDimX, arrayDimY, arrayDimZ;
  int noBarrier = 0;

  if (argc != 7 && argc != 11) {
    printf("%s [array_size] [block_size] [message_size] [iter] [compute_time]+[no]barrier\n", argv[0]);
    printf("%s [array_size_X] [array_size_Y] [array_size_Z] [block_size_X] [block_size_Y] [block_size_Z] [message_size] [iter] [compute_time]+[no]barrier\n", argv[0]);
    //MPI_Abort(UNION_Comm_World, -1);
  }

  if(argc == 7) {
    arrayDimZ = arrayDimY = arrayDimX = atoi(argv[1]);
    blockDimZ = blockDimY = blockDimX = atoi(argv[2]);
    messageSize = atoi(argv[3]);
    maxiter = atoi(argv[4]);
    compute_time = atol(argv[5]);
    if(strcasecmp(argv[6], "+nobarrier") == 0)
      noBarrier = 1;
    else
      noBarrier = 0;
    if(noBarrier && myRank==0) printf("\nSTENCIL COMPUTATION WITH NO BARRIERS\n");
  }
  else {
    arrayDimX = atoi(argv[1]);
    arrayDimY = atoi(argv[2]);
    arrayDimZ = atoi(argv[3]);
    blockDimX = atoi(argv[4]);
    blockDimY = atoi(argv[5]);
    blockDimZ = atoi(argv[6]);
    messageSize = atoi(argv[7]);
    maxiter = atoi(argv[8]);
    compute_time = atol(argv[9]);
    if(strcasecmp(argv[10], "+nobarrier") == 0)
      noBarrier = 1;
    else
      noBarrier = 0;
    if(noBarrier && myRank==0) printf("\nSTENCIL COMPUTATION WITH NO BARRIERS\n");
  }

  if (arrayDimX < blockDimX || arrayDimX % blockDimX != 0) {
    printf("array_size_X % block_size_X != 0!\n");
    //MPI_Abort(UNION_Comm_World, -1);
  }
  if (arrayDimY < blockDimY || arrayDimY % blockDimY != 0) {
    printf("array_size_Y % block_size_Y != 0!\n");
    //MPI_Abort(UNION_Comm_World, -1);
  }
  if (arrayDimZ < blockDimZ || arrayDimZ % blockDimZ != 0) {
    printf("array_size_Z % block_size_Z != 0!\n");
    //MPI_Abort(UNION_Comm_World, -1);
  }

  struct union_app_data app_data = {
    .final_iteration = maxiter - 1,
  };
  UNION_Pass_app_data(&app_data);

  struct timespec tim;
  tim.tv_sec = 0;
  tim.tv_nsec = compute_time;

  int num_blocks_x = arrayDimX / blockDimX;
  int num_blocks_y = arrayDimY / blockDimY;
  int num_blocks_z = arrayDimZ / blockDimZ;

  int myXcoord = myRank % num_blocks_x;
  int myYcoord = (myRank % (num_blocks_x * num_blocks_y)) / num_blocks_x;
  int myZcoord = myRank / (num_blocks_x * num_blocks_y);

  int i, j, k;
  double error = 1.0, max_error = 0.0;

  if(myRank == 0) {
    printf("Jacobi3D: Running Jacobi on %d processors with (%d, %d, %d) elements\n", numPes, num_blocks_x, num_blocks_y, num_blocks_z);
    printf("Jacobi3D: Array Dimensions: %d %d %d\n", arrayDimX, arrayDimY, arrayDimZ);
    printf("Jacobi3D: Block Dimensions: %d %d %d\n", blockDimX, blockDimY, blockDimZ);
  }

  // double *temperature;
  // double *new_temperature;

  /* allocate one dimensional arrays */
 //  temperature = new double[(blockDimX+2) * (blockDimY+2) * (blockDimZ+2)];
 //  new_temperature = new double[(blockDimX+2) * (blockDimY+2) * (blockDimZ+2)];

 //  for(k=0; k<blockDimZ+2; k++)
 //    for(j=0; j<blockDimY+2; j++)
 //      for(i=0; i<blockDimX+2; i++) {
	// temperature[index(i, j, k)] = 0.0;
 //      }

 //  /* boundary conditions */
 //  if(myZcoord == 0 && myYcoord < num_blocks_y/2 && myXcoord < num_blocks_x/2) {
 //    for(j=1; j<=blockDimY; j++)
 //      for(i=1; i<=blockDimX; i++)
	// temperature[index(i, j, 1)] = 1.0;
 //  }

 //  if(myZcoord == num_blocks_z-1 && myYcoord >= num_blocks_y/2 && myXcoord >= num_blocks_x/2) {
 //    for(j=1; j<=blockDimY; j++)
 //      for(i=1; i<=blockDimX; i++)
 //      temperature[index(i, j, blockDimZ)] = 0.0;
 //  }

  /* Copy left, right, bottom, top, front and back  planes into temporary arrays. */

  // double *left_plane_out   = new double[messageSize];
  // double *right_plane_out  = new double[messageSize];
  // double *left_plane_in    = new double[messageSize];
  // double *right_plane_in   = new double[messageSize];

  // double *bottom_plane_out = new double[messageSize];
  // double *top_plane_out	   = new double[messageSize];
  // double *bottom_plane_in  = new double[messageSize];
  // double *top_plane_in     = new double[messageSize];

  // double *back_plane_out    = new double[messageSize];
  // double *front_plane_out   = new double[messageSize];
  // double *back_plane_in     = new double[messageSize];
  // double *front_plane_in    = new double[messageSize];

  UNION_MPI_Barrier(UNION_Comm_World);
  // MPI_Pcontrol(1);
  // startTime = MPI_Wtime();

  int iterations;
  for(iterations = 0; iterations < maxiter; iterations++) {
    UNION_Compute(compute_time);
    nanosleep(&tim, NULL);
    // if(myRank == 0) printf("iteration %d\n", iterations);
    /* Copy different planes into buffers */
    // for(k=0; k<blockDimZ; ++k)
    //   for(j=0; j<blockDimY; ++j) {
    //     left_plane_out[k*blockDimY+j] = temperature[index(1, j+1, k+1)];
    //     right_plane_out[k*blockDimY+j] = temperature[index(blockDimX, j+1, k+1)];
    //   }

    // for(k=0; k<blockDimZ; ++k)
    //   for(i=0; i<blockDimX; ++i) {
    //     top_plane_out[k*blockDimX+i] = temperature[index(i+1, 1, k+1)];
    //     bottom_plane_out[k*blockDimX+i] = temperature[index(i+1, blockDimY, k+1)];
    //   }

    // for(j=0; j<blockDimY; ++j)
    //   for(i=0; i<blockDimX; ++i) {
    //     back_plane_out[j*blockDimX+i] = temperature[index(i+1, j+1, 1)];
    //     front_plane_out[j*blockDimX+i] = temperature[index(i+1, j+1, blockDimZ)];
    //   }

    /* Receive my right, left, top, bottom, back and front planes */
    UNION_MPI_Irecv(NULL, messageSize, UNION_Double, calc_pe(wrap_x(myXcoord+1), myYcoord, myZcoord), RIGHT, UNION_Comm_World, &rreq[RIGHT-1]);
    UNION_MPI_Irecv(NULL, messageSize, UNION_Double, calc_pe(wrap_x(myXcoord-1), myYcoord, myZcoord), LEFT, UNION_Comm_World, &rreq[LEFT-1]);
    UNION_MPI_Irecv(NULL, messageSize, UNION_Double, calc_pe(myXcoord, wrap_y(myYcoord+1), myZcoord), TOP, UNION_Comm_World, &rreq[TOP-1]);
    UNION_MPI_Irecv(NULL, messageSize, UNION_Double, calc_pe(myXcoord, wrap_y(myYcoord-1), myZcoord), BOTTOM, UNION_Comm_World, &rreq[BOTTOM-1]);
    UNION_MPI_Irecv(NULL, messageSize, UNION_Double, calc_pe(myXcoord, myYcoord, wrap_z(myZcoord+1)), FRONT, UNION_Comm_World, &rreq[FRONT-1]);
    UNION_MPI_Irecv(NULL, messageSize, UNION_Double, calc_pe(myXcoord, myYcoord, wrap_z(myZcoord-1)), BACK, UNION_Comm_World, &rreq[BACK-1]);


    /* Send my left, right, bottom, top, front and back planes */
    UNION_MPI_Isend(NULL, messageSize, UNION_Double, calc_pe(wrap_x(myXcoord-1), myYcoord, myZcoord), RIGHT, UNION_Comm_World, &sreq[RIGHT-1]);
    UNION_MPI_Isend(NULL, messageSize, UNION_Double, calc_pe(wrap_x(myXcoord+1), myYcoord, myZcoord), LEFT, UNION_Comm_World, &sreq[LEFT-1]);
    UNION_MPI_Isend(NULL, messageSize, UNION_Double, calc_pe(myXcoord, wrap_y(myYcoord-1), myZcoord), TOP, UNION_Comm_World, &sreq[TOP-1]);
    UNION_MPI_Isend(NULL, messageSize, UNION_Double, calc_pe(myXcoord, wrap_y(myYcoord+1), myZcoord), BOTTOM, UNION_Comm_World, &sreq[BOTTOM-1]);
    UNION_MPI_Isend(NULL, messageSize, UNION_Double, calc_pe(myXcoord, myYcoord, wrap_z(myZcoord-1)), FRONT, UNION_Comm_World, &sreq[FRONT-1]);
    UNION_MPI_Isend(NULL, messageSize, UNION_Double, calc_pe(myXcoord, myYcoord, wrap_z(myZcoord+1)), BACK, UNION_Comm_World, &sreq[BACK-1]);

    UNION_MPI_Waitall(6, rreq, UNION_STATUSES_IGNORE);
    UNION_MPI_Waitall(6, sreq, UNION_STATUSES_IGNORE);

    // for (i=0; i<6; i++) {
    //   UNION_MPI_Wait(&rreq[i],MPI_STATUS_IGNORE);
    //   UNION_MPI_Wait(&sreq[i],MPI_STATUS_IGNORE);
    // }

    /* Copy buffers into ghost layers */
 //    for(k=0; k<blockDimZ; ++k)
 //      for(j=0; j<blockDimY; ++j) {
	// temperature[index(0, j+1, k+1)] = left_plane_in[k*blockDimY+j];
 //      }
 //    for(k=0; k<blockDimZ; ++k)
 //      for(j=0; j<blockDimY; ++j) {
	// temperature[index(blockDimX+1, j+1, k+1)] = right_plane_in[k*blockDimY+j];
 //      }
 //    for(k=0; k<blockDimZ; ++k)
 //      for(i=0; i<blockDimX; ++i) {
	// temperature[index(i+1, 0, k+1)] = bottom_plane_in[k*blockDimX+i];
 //      }
 //    for(k=0; k<blockDimZ; ++k)
 //      for(i=0; i<blockDimX; ++i) {
	// temperature[index(i+1, blockDimY+1, k+1)] = top_plane_in[k*blockDimX+i];
 //      }
 //    for(j=0; j<blockDimY; ++j)
 //      for(i=0; i<blockDimX; ++i) {
	// temperature[index(i+1, j+1, 0)] = back_plane_in[j*blockDimX+i];
 //      }
 //    for(j=0; j<blockDimY; ++j)
 //      for(i=0; i<blockDimX; ++i) {
	// temperature[index(i+1, j+1, blockDimY+1)] = top_plane_in[j*blockDimX+i];
 //      }

 //    /* update my value based on the surrounding values */
 //    for(k=1; k<blockDimZ+1; k++)
 //      for(j=1; j<blockDimY+1; j++)
	// for(i=1; i<blockDimX+1; i++) {
	//   new_temperature[index(i, j, k)] = (temperature[index(i-1, j, k)]
 //                                          +  temperature[index(i+1, j, k)]
 //                                          +  temperature[index(i, j-1, k)]
 //                                          +  temperature[index(i, j+1, k)]
 //                                          +  temperature[index(i, j, k-1)]
 //                                          +  temperature[index(i, j, k+1)]
 //                                          +  temperature[index(i, j, k)] ) * DIVIDEBY7;
	// }

 //    max_error = error = 0.0;
 //    for(k=1; k<blockDimZ+1; k++)
 //      for(j=1; j<blockDimY+1; j++)
	// for(i=1; i<blockDimX+1; i++) {
	//   error = fabs(new_temperature[index(i, j, k)] - temperature[index(i, j, k)]);
	//   if(error > max_error)
	//     max_error = error;
	// }
 
 //    double *tmp;
 //    tmp = temperature;
 //    temperature = new_temperature;
 //    new_temperature = tmp;

 //    /* boundary conditions */
 //    if(myZcoord == 0 && myYcoord < num_blocks_y/2 && myXcoord < num_blocks_x/2) {
 //      for(j=1; j<=blockDimY; j++)
	// for(i=1; i<=blockDimX; i++)
	//   temperature[index(i, j, 1)] = 1.0;
 //    }

 //    if(myZcoord == num_blocks_z-1 && myYcoord >= num_blocks_y/2 && myXcoord >= num_blocks_x/2) {
 //      for(j=1; j<=blockDimY; j++)
	// for(i=1; i<=blockDimX; i++)
	// temperature[index(i, j, blockDimZ)] = 0.0;
 //    }

    // if(myRank == 0) printf("Iteration %d %f\n", iterations, max_error);
    if(noBarrier == 0) UNION_MPI_Allreduce(&max_error, &error, 1, UNION_Double, UNION_Op_Max, UNION_Comm_World);

    UNION_Mark_Iteration(iterations);
  } /* end of while loop */

  UNION_MPI_Barrier(UNION_Comm_World);
  // MPI_Pcontrol(0);

  if(myRank == 0) {
    // endTime = MPI_Wtime();
    printf("Jacobi3D: Completed %d iterations\n", iterations + 1);
    // printf("Time elapsed per iteration: %f\n", (endTime - startTime)/(MAX_ITER-5));
  }

  UNION_MPI_Finalize();
  return 0;
} /* end function main */

extern "C" {
/* fill in function pointers for this method */
struct union_conceptual_bench jacobi3d_bench = 
{
.program_name = (char *) "jacobi3d",
.conceptual_main = jacobi3d_main,
};
}

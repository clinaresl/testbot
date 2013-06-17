/* This program performs iterative-deepening A* on the sliding tile
puzzles, using the Manhattan distance evaluation function. It was
written by Richard E.  Korf, Computer Science Department, University
of California, Los Angeles, Ca.  90024.  */

#include <stdio.h>                                   /* standard I/O library */
#include <string.h>                                                /* memcpy */
#include <sys/time.h>                                       /* time handling */
#include <unistd.h>                                         /* time handling */

#define NUMBER  30               /* number of problem instances to be solved */
#define X 4                                    /* squares in the x dimension */
#define SIZE 16                                   /* total number of squares */

int s[SIZE];                       /* state of puzzle: tile in each position */

struct operators                  
{int num;                                 /* number of applicable oprs: 2..4 */
 int pos[4];} oprs[SIZE];    /* position of adjacent tiles for each position */

int increment [SIZE] [SIZE] [SIZE];    /* incr eval func: tile, source, dest */

int thresh;                                       /* search cutoff threshold */
double generated;                /* number of states generated per iteration */
double total;                            /* total number of states generated */

/* INITOPS initializes the operator table. */

initops ()

{int blank;                                   /* possible positions of blank */

 for (blank = 0; blank < SIZE; blank++)  /* for each possible blank position */
   {oprs[blank].num = 0;                               /* no moves initially */
    if (blank > X - 1)                                       /* not top edge */
      oprs[blank].pos[oprs[blank].num++] = blank - X;       /* add a move up */
    if (blank % X > 0)                                      /* not left edge */
      oprs[blank].pos[oprs[blank].num++] = blank - 1;     /* add a move left */
    if (blank % X < X - 1)                                 /* not right edge */
      oprs[blank].pos[oprs[blank].num++] = blank + 1;    /* add a move right */
    if (blank < SIZE - X)                                 /* not bottom edge */
      oprs[blank].pos[oprs[blank].num++] = blank + X;}}   /* add a move down */

/* INIT pre-computes the incremental evaluation function table. For a
given tile moving from a given source position to a given destination
position, it returns the net change in the value of the Manhattan
distance, which is either +1 or -1.  */

init (increment)

int increment [SIZE] [SIZE] [SIZE];/* incr eval function: tile, source, dest */

{int tile;                                               /* tile to be moved */
 int source, dest;                       /* source and destination positions */
 int destindex;                       /* destination index in operator table */

 for (tile = 1; tile < SIZE; tile++)                   /* all physical tiles */
   for (source = 0; source < SIZE; source++)   /* all legal source positions */
     for (destindex = 0; destindex < oprs[source].num; destindex++) 
                                             /* legal destinations of source */
       {dest = oprs[source].pos[destindex];    /* dest is new blank position */
	increment[tile][source][dest]  = abs((tile % X) - (dest % X))   
                                       - abs((tile % X) - (source % X)) 
                                       + abs((tile / X) - (dest / X))
                                       - abs((tile / X) - (source / X));}}

/* INPUT accepts an initial state from the terminal, assuming it is
preceded by a problem number. It stores it in the state vector and
returns the position of the blank tile. */

input (s)

int s[SIZE];                                                 /* state vector */

{int index;                                       /* index to tile positions */
 int blank;                                        /* position of blank tile */

 scanf ("%*d");                                  /* skip over problem number */
 for (index = 0; index < SIZE; index++)                 /* for each position */
   {scanf ("%d", &s[index]);                  /* input tile in that position */
    if (s[index] == 0) blank = index;}     /* note blank position in passing */
 return (blank);}

/* MANHATTAN returns the sum of the Manhattan distances of each tile,
 except the blank, from its goal position. */

manhattan (s)

int s[SIZE];                                                        /* state */

{int value;                                                   /* accumulator */
 int pos;                                                   /* tile position */

  value = 0;
  for (pos = 0; pos < SIZE; pos++)
    if (s[pos] != 0)            /* blank isn't counted in Manhattan distance */
      value = value + abs((pos % X) - (s[pos] % X))            /* X distance */
                    + abs((pos / X) - (s[pos] / X));           /* Y distance */
  return(value);}

/* SEARCH performs one depth-first iteration of the search, cutting
 off when the depth plus the heuristic evaluation exceeds THRESH. If
 it succeeds, it returns 1 and records the sequence of tiles moved in
 the solution.  Otherwise, it returns 0 */

search (blank, oldblank, g, h)

int blank;			                /* current position of blank */
int oldblank;			               /* previous position of blank */
int g;                                            /* current depth of search */
int h;	                           /* value of heuristic evaluation function */

{ int index;                                    /* index into operator array */
  int newblank;                               /* blank position in new state */
  int tile;                                              /* tile being moved */
  int newh;                             /* heuristic evaluation of new state */
  
  for (index = 0; index < oprs[blank].num; index++)     /* for each appl opr */
    if ((newblank = oprs[blank].pos[index]) != oldblank) /*not inv last move */
      {tile = s[newblank];            /* tile moved is in new blank position */
      newh = h + increment[tile][newblank][blank];   /* new heuristic est */
       generated++;                                 /* count nodes generated */
       if (newh+g+1 <= thresh)                    /* less than search cutoff */
	 {s[blank] = tile;                               /* make actual move */
	  if ((newh == 0) ||                     /* goal state is reached or */
	      (search(newblank, blank, g+1, newh)))       /* search succeeds */
	    return (1);                                 /* exit with success */
	  s[newblank] = tile;}}       /* undo current move before doing next */
  return (0);}                                          /* exit with failure */

/* Main program does the initialization, inputs an initial state, solves it,
   and prints the solution. */

main ()

{
  int success;                         /* boolean flag for success of search */
  int blank;                                    /* initial position of blank */
  int initeval;                       /* manhattan distance of initial state */
  int problem;                                           /* problem instance */
  int index;                                      /* index to tile positions */
  long totalTime = 0;       /* time elapsed for solving the whole test suite */
  
  struct timeval stv,etv;
  struct timezone stz,etz;
  float thistime;
  float totaltime=0.0;
  
  initops ();                                   /* initialize operator table */
  init (increment);                        /* initialize evaluation function */
  
  for (problem = 1; problem <= NUMBER; problem++){ /* for each initial state */
    blank = input(s);                                 /* input initial state */
    gettimeofday (&stv,&stz);
    thresh = initeval = manhattan(s);      /* initial threshold is initial h */
    total = 0;                           /* initialize total nodes generated */
    
    do{                    /* depth-first iterations until solution is found */
      generated = 0;            /* initialize number generated per iteration */
      success = search (blank, -1, 0, initeval);           /* perform search */
      fflush(stdout);       /* flush output buffer to see progress of search */
      total = total + generated;    /* keep track of total nodes per problem */
      thresh += 2;}                     /* threshold always increases by two */
    while (!success);                             /* until solution is found */
    
    gettimeofday (&etv,&etz);
    if (etv.tv_usec>stv.tv_usec){
      thistime=(etv.tv_sec-stv.tv_sec)+(etv.tv_usec-stv.tv_usec)/1000000.0;}
    else{
      thistime=(etv.tv_sec-stv.tv_sec)+(1000000.0+etv.tv_usec-stv.tv_usec)/1000000.0;}
    
    totaltime+=thistime;
    
    printf ("%d %d %10.f %2.2f/%2.2f (%2.2f)\n", problem, thresh-2, total,
	    thistime,totaltime,totaltime/(problem*1.0));}}


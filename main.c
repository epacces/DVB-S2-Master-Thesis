#include <stdlib.h>
#include <conio.h>
#include <iostream.h>
#include <time.h>
#include <dos.h>
#include <stdio.h>
#include <string.h>
#include <fstream.h>
#include <math.h>


#define MAXR 192 // max r bits
#define P 8      // degree of parallelism
#define MAXN ((1<<16)-1)  // primitive code length
#define MAXT 12         // Max corrective capacity
#define DRIFT 0 // adding extra errors


#ifndef TESTENC
#define TESTDEC
#define SERIAL
#endif




//////////////////////////// MACRO //////////////////////////////
// It returns corrective capacity of the code with (n,k) given //
/////////////////////////////////////////////////////////////////

#define t(n,k)  ( ((n)-(k)) / (16) )


/****************************************************************************/
/*********************** Global Variable  **********************************/
/***************************************************************************/

int codeword[MAXN],
	message[MAXN]; // information bits

int Ap_n[MAXR][MAXR];	// (n-k) rows, (n-k) col
int Ap_k[MAXR][MAXR];	// 192 rows, 192 col
int C[MAXR][P];			// 192 rows, 8 col
int S[(MAXT + DRIFT)*2];          // Syndrome vector
int err[MAXT+DRIFT];          // array of random error location
FILE *o3;

/****************************************************************************/
/*********************** PN bit source **************************************/
/***************************************************************************/

int lfsr(unsigned long int *seed)
{
	int b,c;

	b = ( ((*seed) & (1 << 31) ) >> 31 ) ;

	c =   ((*seed) & 1) ^ ( ((*seed) & (1 << 1)) >> 1 ) ^ ( ((*seed) & (1 << 21)) >> 21 ) ^ b ;

	(*seed) = ((*seed) << 1) | c;

	return(b);
}

/****************************************************************************/
/*********************** Message generator **********************************/
/***************************************************************************/

void message_gen(int n,int k, unsigned long int  *seed)
{
	int i;
    // Message bits pseudo random generation
	for (i=n-1;i>=n-k;i--)
		message[i] = lfsr(seed);
	// Zero padding
	for(i = 0; i < n-k; i++)
		message[i] = 0;
}

/****************************************************************************/
/*********************** Polynomial Generators *****************************/
/***************************************************************************/
// Note: only used by algorithm emulating the serial architecture (n-clock cycles)

const unsigned int gen12[] =
{1,1,1,0,0,1,1,1,1,0,1,0,1,0,1,0,0,1,0,0,0,0,0,0,0,1,1,0,0,1,1,0,
 1,1,1,0,1,1,1,1,1,0,1,0,0,0,0,1,1,1,1,0,0,0,1,0,1,1,0,0,0,0,0,0,
 1,0,0,1,0,0,0,1,0,0,0,1,0,0,0,0,1,0,1,0,1,1,0,0,0,0,1,1,1,0,1,1,
 0,0,0,1,1,0,1,1,0,0,1,1,0,1,0,0,1,1,1,1,0,0,1,1,0,0,0,0,1,0,1,0,
 0,0,1,1,1,0,0,0,1,0,0,0,1,0,1,0,0,0,1,1,1,0,1,0,0,0,1,0,0,0,0,1,
 1,1,0,0,0,0,0,1,0,1,1,1,0,0,0,0,0,1,1,0,0,1,0,0,0,1,1,1,0,0,1,0,
 1};
// i.e. gen(x) = a_0*x^0 + a_1*x^1 + ... + a_(r-1)*x^(r-1) + a_r*x^r

const unsigned int gen10[] =
{1,0,0,0,1,0,0,1,1,0,1,0,0,1,1,0,1,1,0,1,1,1,0,1,0,0,0,1,1,1,0,1,
 1,0,0,0,0,0,0,0,1,1,0,0,0,1,0,0,1,0,0,0,1,0,1,1,1,1,1,1,0,1,1,1,
 1,1,0,0,0,0,0,0,1,1,1,0,1,0,1,0,0,0,0,1,1,1,1,0,0,1,0,1,0,1,1,0,
 1,1,1,1,1,0,0,0,1,1,0,0,1,1,0,0,0,1,0,1,0,1,0,0,0,0,1,1,1,1,1,1,
 1,0,1,1,0,1,1,1,0,0,1,1,0,0,0,0,1,0,1,0,1,0,0,0,0,0,0,0,0,1,1,0,
 1};

const unsigned int gen8[] =
{1,1,0,1,0,1,0,0,0,1,1,0,0,1,1,0,1,0,0,1,1,1,1,1,0,0,1,0,0,0,0,0,
 1,0,1,0,1,1,1,0,1,0,1,1,0,1,1,0,0,0,1,1,1,1,1,1,1,0,0,1,1,0,0,0,
 1,0,1,1,1,1,0,1,1,1,1,0,1,0,0,1,1,1,1,0,0,1,0,0,1,0,0,0,1,1,1,0,
 1,1,1,1,1,0,1,0,1,0,1,0,0,1,0,0,1,1,1,0,0,0,0,0,0,0,1,1,1,0,0,0,
 1};

/****************************************************************************/
/*********************** Serial BCH encoder ********************************/
/***************************************************************************/

void BCH_s_enc(int n, int k)
{

	const unsigned int *g;
	int *reg;
	int mem,app,i,j;

/***************  Mode Selection (t-error-correction) ***********************/

	switch(n-k) {
	case 192:
		g = gen12;
		reg = (int*)calloc(n-k,sizeof(int));
		break;
	case 160:
		g = gen10;
		reg = (int*)calloc(n-k,sizeof(int));
		break;
	case 128:
		g = gen8;
		reg = (int*)calloc(n-k,sizeof(int));
		break;
	default:
		fprintf(stdout,"Error:simulation aborted!\n");
		fprintf(stdout,"Please insert a n-k couple provided by DVB-S2 FEC\n");
		exit(0);
	}

/*********************** Encoding serial algorithm ********************************/
/**************************   n clock ticks **************************************/

/************************* Computing remainder **********************************/

	for (i=n-1; i>=0; i--)
	{
		mem=reg [n-k-1];
		for (j=n-k-2; j>=0; j--)
		{
			app=mem & g[j+1];
			reg[j+1]=reg[j]^app;
		}

		reg[0]= message[i]^(mem & g[0]);

	}

/*********************** Codeword in systematic form ********************************/

	for (i=n-1;i>=n-k;i--)
		codeword[i] = message[i];
	for (i=n-k-1; i >=0; i--)
		codeword[i] = reg[i];

	free(reg);
}

/****************************************************************************/
/*********************** Loading matrices routine ***************************/
/***************************************************************************/

void load_matrices(int n, int k)
{
	FILE *input_Ap_k, *input_C, *input_Ap_n;
	int i,j;

/***********************  Mode Selection (t-error-correction) ***********************/

	switch(n-k) {
	case 192:
		input_Ap_k = fopen ("Matrices/ADVBS2_nclk_t12.txt","r");
		input_Ap_n = fopen ("Matrices/ADVBS2_nclk_t12.txt","r");
		input_C = fopen("Matrices/CDVBS2_kclk_t12.txt","r");
		break;
	case 160:
		input_Ap_k = fopen ("Matrices/ADVBS2_kclk_t10.txt","r");
		input_Ap_n = fopen ("Matrices/ADVBS2_nclk_t10.txt","r");
		input_C = fopen("Matrices/CDVBS2_kclk_t10.txt","r");
		break;
	case 128:
		input_Ap_k = fopen ("Matrices/ADVBS2_kclk_t8.txt","r");
		input_Ap_n = fopen ("Matrices/ADVBS2_nclk_t8.txt","r");
		input_C = fopen("Matrices/CDVBS2_kclk_t8.txt","r");
		break;
	default:
		fprintf(stdout,"Error: loading of matrices failed!\n");
		fprintf(stdout,"Please insert a n-k couple provided by DVB-S2 FEC\n");
		exit(0);
	}



/********************* Loading matrix Ap_n ***********************************/
/////////// Note: ONLY this matrix size is variable //////////////////////////


	for ( i=0;i<n-k;i++){
		for ( j=0;j<n-k;j++){
			//fscanf(input_Ap_k,"%d\t",&(Ap_k[i][j]));
			fscanf(input_Ap_n,"%d\t",&(Ap_n[i][j]));
			//power_A[i][j] = load_i;
		}
		//fscanf(input_Ap_k,"\n");
		fscanf(input_Ap_n,"\n");
	}

/********************* Loading matrix Ap_k ***********************************/

	for ( i=0;i<MAXR;i++)
		for ( j=0;j<MAXR;j++)
			fscanf(input_Ap_k,"%d\t", &(Ap_k[i][j]));
		fscanf(input_Ap_k,"\n");




/********************* Loading matrix C ***********************************/
	for (i=0;i<MAXR;i++)
	{
		for (j=0;j<P;j++)
		{
			fscanf(input_C,"%d\t",&(C[i][j]));
			//comb_C[i][j] = load_c;
		}

		fscanf (input_C,"\n");
	}


	fclose(input_C);
	fclose(input_Ap_n);
	fclose(input_Ap_k);

}

/************************************************************************/
/***********  Combinatorial blocks emulation ****************************/
/***********************************************************************/

/************************************************************************/
/******************  Input comb network  ********************************/
/***********************************************************************/

int comb_c(int index, int *input)
{
	int out,f,ind;

	out=0;

	ind=P-1;

	for (f=0; f<P; f++)
	{
		out= out ^ ((C[index][f]) & (input[f]));
		ind--;
	}

	return(out);
}

/************************************************************************/
/******************  State comb network  ********************************/
/***********************************************************************/

int comb_n(int index,int r, int *reg_old)
{
	int out,f;

	out=0;

	for (f=0; f<P; f++)

	{
		out=out^(Ap_n[index][r-f-1] & reg_old[r-f-1]);
	}

	return(out);
}

int comb_k(int index, int *reg_old)
{
	int out,f;

	out=0;

	for (f=0; f<P; f++)

	{
		out=out^(Ap_k[index][MAXR-f-1] & reg_old[MAXR-f-1]);
	}

	return(out);
}



/****************************************************************************/
/*********************** BCH parellel encoder *******************************/
/*********************** n clock ticks        *******************************/
/***************************************************************************/

void BCHnclk_par(int n,int k)
{
	int clock_ticks;
	int *reg, *reg_old;

	int input[P]; // parallel input bits

/***************  Mode Selection (t-error-correction) ***********************/

	switch(n-k) {
	case 192:
		reg = (int*)calloc(n-k,sizeof(int));
		reg_old = (int*)calloc(n-k,sizeof(int));
		break;
	case 160:
		reg = (int*)calloc(n-k,sizeof(int));
		reg_old = (int*)calloc(n-k,sizeof(int));
		break;
	case 128:
		reg = (int*)calloc(n-k,sizeof(int));
		reg_old = (int*)calloc(n-k,sizeof(int));
		break;
	default:
		fprintf(stdout,"Error:simulation aborted!\n");
		fprintf(stdout,"Please insert a n-k couple provided by DVB-S2 FEC\n");
		exit(0);
	}
	/// Computation of clock ticks required to compute the remainder after division////
	clock_ticks = n/P;



/************************* Computing remainder **********************************/
	int z=0;

	for (int i=0; i<clock_ticks; i++)
	{
		///// refresh of state  /////// ///////
		for (int m=0; m<n-k; m++)
			reg_old[m]=reg[m];
		///////////////////////////////////////
		/////// loading of parallel input //////
		for (int count=P-1; count>=0; count--)
		{
			z++;
			input[count] = message[n-z];
		}
		///////////////////////////////////////////
		/// Computing of next values of state /////
		if (clock_ticks >0)
		{

			for (m=0; m<n-k; m++)
			{
				if (m<P)

					reg[m] = input[m]^comb_n(m,n-k,reg_old);

				else

					reg[m] = comb_n(m,n-k,reg_old)^reg_old[m-P];

			}
		}
		/////////////////////////////////////////////
	}
/************************************************************************************/

/*********************** Codeword in systematic form ********************************/

	for (i=n-1; i>n-k-1; i--)
		codeword[i] = message[i];

	for (i=n-k-1; i>=0; i--)
		codeword[i] =  reg[i];

}

/****************************************************************************/
/*********************** BCH parellel encoder *******************************/
/*********************** k clock ticks        *******************************/
/***************************************************************************/

void BCHkclk_par(int n,int k)
{
	int clock_ticks;
	int *reg, *reg_old;
	int offset,m;

	int input[P]; // parallel input bits

/***************  Mode Selection (t-error-correction) ***********************/

	switch(n-k) {
	case 192:
		reg = (int*)calloc(MAXR,sizeof(int));
		reg_old = (int*)calloc(MAXR,sizeof(int));
		offset = MAXR-192;
		break;
	case 160:
		reg = (int*)calloc(MAXR,sizeof(int));
		reg_old = (int*)calloc(MAXR,sizeof(int));
		offset = MAXR - 160;
		break;
	case 128:
		reg = (int*)calloc(MAXR,sizeof(int));
		reg_old = (int*)calloc(MAXR,sizeof(int));
		offset = MAXR-128;
		break;
	default:
		fprintf(stdout,"Error:encoding aborted!\n");
		fprintf(stdout,"Please insert a n-k couple provided by DVB-S2 FEC\n");
		exit(0);
	}
	/// Computation of clock ticks required to compute the remainder after division////
	clock_ticks = k/P;

/************************* Computing remainder **********************************/

	int z=0;
	for (int i=0; i<clock_ticks; i++)
	{
		for (m=0; m < MAXR; m++)
			reg_old[m]=reg[m];

		for (int count=P-1; count>=0; count--)
		{
			z++;
			input[count] = message[n-z];
		}


		if (clock_ticks>0)
		{

			for (m=0; m< MAXR; m++)
			{
				if (m<P)

					reg[m] = (comb_c(m,input))^(comb_k(m,reg_old));
				else
					reg[m] = (comb_c(m,input))^(comb_k(m,reg_old))^(reg_old[m-(P)]);
			}
		}
	}
/*********************** Codeword in systematic form ********************************/

	for (i=n-1; i>n-k-1; i--)
		codeword[i] = message[i];

	for (i=n-k-1; i>=0 ; i--)
		codeword[i] =  reg[i+offset];

	/*  Check values of register
	FILE *de;
	de = fopen("debugkclk.txt","w");
	for(i = MAXR-1; i >=0; i--)
		fprintf(de,"%d\n",reg[i]);
	*/

}

/****************************************************************************/
/*********************** Creation of GF(2^m)  *******************************/
/*********************** useful tables        *******************************/
/***************************************************************************/

void gfField(int m, // Base 2 logarithm of cardinality of the Field
			 int poly, // primitive polynomial of the Field in decimal form
			 int ** powOfAlpha, int ** indexAlpha)
{
	int reg,	// this integer of 32 bits, masked by a sequence of m ones,
				// contains the elements of Galois Field
		tmp,i;
	// sequence of m ones
	int mask = (1<<m) -1;  // 1(m) Bit Masking

	// Allocation and initialization of the tables of the Galois Field
	*powOfAlpha = (int *)calloc((1<<m)-2, sizeof(int));
	*indexAlpha = (int *)calloc((1<<m)-1, sizeof(int));

	(*powOfAlpha)[0] = 1;
	(*indexAlpha)[0] = - 1; // we set -1
	(*indexAlpha)[1] = 0;

	for (i = 0, reg = 1; i < (1<<m)-2; i++)
	{
			tmp = (int)(reg & (1<<(m-1))); // Get the MSB
            reg <<= 1;   // Register shifted
            if( tmp) { //
				reg ^= poly;
				//
				reg &= mask;
			}
			// Step-by-step writing of the tables
			(*powOfAlpha)[i+1] = (int) reg;
			(*indexAlpha)[(int)reg] = i+1;
    }


}


/****************************************************************************/
/*********************** Error detection   *******************************/
/***************************************************************************/

bool error_detection(int *pow, int *index, int t)
{

	bool syn = false;
	for(int i = 0; i < t*2; i++)
	{
		S[i] = 0;
		for(int j = 0; j < MAXN; j++){
			if(codeword[j])
				S[i] ^= pow[((i+1)*j)%MAXN];
		}
		if((S[i] = index[S[i]]) != -1)
			syn = true;

	}

	return syn;

}


/****************************************************************************/
/*********************** Error correction   *******************************/
/***************************************************************************/

void BerlMass(//int *S, // array of syndrome in exponential notation
			  int t2, // length of array S
			  int *pow,
			  int *index)

{
	int k,L,l,i;
	int d, dm, tmp;
	int *T, *c, *p, *lambda,*el;
	// Allocation and initialization
	// Auto-Regressive-Filter coefficients computed at the previous step
	p = (int*) calloc(t2,sizeof(int));
	// Auto-Regressive-Filter coefficients computed at the current step
	c = (int*) calloc(t2,sizeof(int));
	// Temporary array
	T = (int*) calloc(t2,sizeof(int));
	// error location array (found by Chien Search)
	el = (int*) calloc(t2,sizeof(int));
	// Error polynomial locator
	lambda = (int*) calloc(t2,sizeof(int));


	// Inizialization step
	c[0] = 1;
	p[0] = 1;
	L = 0;
	l = 1;
	dm = 1;

/*********** Berlekamp-Massey Algorithm *******************/
	for (k = 0; k < t2; k++)
	{
		// Discrepancy computation
		if(S[k] == -1)
			d = 0;
		else
			d = pow[S[k]];
		for(i = 1; i <= L;i++)
			if(S[k-i] >= 0 && c[i] > 0)
			d ^= pow[(index[c[i]]+ S[k-i])%MAXN];
			// exponential rule

		if( d == 0)
		{
			l++;
		}
		else
		{
			if(2*L > k)
			{
				for( i = l; i <t2; i++)
				{
					if(p[i-l] != 0)
						c[i] ^= pow[(index[d]-index[dm]+index[p[i-l]]+MAXN)%MAXN];
				}
				l++;
			}
			else
			{
				for( i = 0; i < t2; i++)
					T[i] = c[i];
				for( i = l; i <t2; i++)
				{
					if(p[i-l] != 0)
						c[i] ^= pow[(index[d]-index[dm]+index[p[i-l]]+MAXN)%MAXN];
				}
				L = k-L+1;
				for( i = 0; i < t2; i++)
					p[i] = T[i];
				dm = d;
				l = 1;
			}

		}
	}



/********** Storing of error locator polynomial coefficient **********/
	for(i = 0; i <=L; i++)
	{
		// Error storing
		lambda[i] = index[c[i]];

	}

/**************    Chien search   **************************/
/*******************   Roots searching  ***********************/

	int j;
	k = 0;
	for(i = 0; i < MAXN; i++)
	{
		for(j = 1, tmp = 0; j <=L; j++)
			tmp ^= pow[(lambda[j]+i*j)%MAXN];
		if (tmp == 1)
			// roots inversion give the error locations
			el[k++] = (MAXN-i)%MAXN;

	}
	bool success = true;
	fprintf(o3,"\nPosition of errors detected:\n");
	for(i = 0; i <k; i++) {
		if(el[i] != err[i]) {success=false;}
		fprintf(o3,"%d\t",el[i]);
	}
	if(success) {fprintf(o3,"\nSuccessful decoding!");
	fprintf(stdout,"\nSuccessful decoding!\n----------------------\n");};
	fprintf(o3,"\n\n-------------------------------------");



}



// Random variable uniformly distributed between 0.0 and 1.0
extern double uniform01(long * );

/****************************************************************************/
/*********************** Insertion sort  *******************************/
/***************************************************************************/

void elSort(int dim)
{
	int i, j;
	int key;

	for ( i = 1; i < dim; i++)
     {
         key = err[i];
         j = i - 1;
         while (err[j] < key && j >=0) {
			 err[j+1] = err[j];
			 j--;
		}
		err[j+1] = key;
	}

}

/*************************************************************************/
/*******************        MAIN FUNCTION       **************************/
/*************************************************************************/

int main()
{
	FILE *o1, *o2;
	int *pow, *index;
	int n,k,i,s;
	unsigned long int seed;
	long seed2;
	char *outfile = new char[120];


	//o1 = fopen("outserial.txt","w");
	//o2 = fopen("outpnclk.txt","w");

	n = 57600;  k = 57472;  //
	n = 16200; k=16008; // n = 21600; k = 21408; // n = 43200; k = 43040;

#ifndef SERIAL
	load_matrices(n,k);
#endif
#if defined (TESTDEC)
	sprintf(outfile,"DecTest/outdec_%d_%d.txt",n,k);
	o3 = fopen(outfile,"w");
#endif
	// Galois Field Creation
	gfField(16,
		32+8+4+1,
		&pow,
		&index
		);

#if defined (TESTDEC)
	sprintf(outfile,"DecTest/outdec_%d_%d.txt",n,k);
	o3 = fopen(outfile,"w");
#endif

	/** Simulation Loop **/
	for(s = 0; s <100; s++)
	{

	message_gen(n,k,&seed);
#ifdef SERIAL
	BCH_s_enc(n,k);
#endif


#ifdef NPARALLEL
	BCHnclk_par(n,k);
#endif

#ifdef KPARALLEL
	BCHkclk_par(n,k);
#endif


	fprintf(stdout,"SIM #%d\n",s+1);

#if defined (TESTDEC)
	fprintf(o3,"\nSimulation #%d\nLocation of the pseudo-random errors:\n ",s+1);

	// Random error pattern generator
	for(i = 0; i < t(n,k)+DRIFT; i++){
		// bit flipping
		codeword[err[i] = (int)floor(n*uniform01(&seed2))] ^= 1;
		fprintf(o3,"%d\t",err[i]);
	}
	// Sort of the error locations in decreasing order:
	// it will be useful to check the corrispondence with errors detected
	elSort(t(n,k)+DRIFT);
#endif

	if(error_detection(pow,index,t(n,k)+DRIFT) ) {
		fprintf(stdout,"Errors detected!\nDecoding by Berlekamp-Massey algorithm.....\n");
		fprintf(o3,"\n\nErrors detected!\nDecoding by Berlekamp-Massey algorithm.....\n");
		BerlMass((t(n,k)+DRIFT)*2,pow,index);

	}
	else
		fprintf(stdout,"\n\nNo errors detected!\n------------------------------\n");
	}

	return 0;
}
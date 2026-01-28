# Software Package for VHDL Validation

## Software Implementation of Serial Encoder

This section describes the software implementations of the architecture illustrated in . Recall that only this architecture is actually serial since the other one (depicted in ), which computes parity bits in $`n\ped{bch}`$ clock ticks, needs a parallel fetching of the encoding result and a reset of the register at the end of each computation cycle[^1].

The software implementation shown below simulates the serial architecture depicted in . For the first $`k`$ clock ticks, the informative bits exits while the feedback loop is enabled. From $`k`$ to $`n`$ instead, the feedback loop is disabled and then all the parity bits ready to be fetched are carried (serially) to the output while zeros are going to be stored into each stage of the shift register, thus resetting the register. This is certainly an advantage with respect to architecture depicted in , which requires a parallel fetching of the parity bits together with, in turn, a reset of the shift register.

To simulate the two different behaviors of the serial encoder, which for $`k`$ clock cycles yields the bits of message while for the next one produces the parity bits, a integer `encStep` counter has been employed. It follows a useful description of the used variable:

- `ticks` is a function parameter and refers to the numbers of iteration/clock-ticks which have to be simulated; `m[], out[]`, other ones function parameters, are vector relevant to input and output. The function `Run` reads from `m[]` and write in turn the result of `ticks` computation cycles.

- Vector of integer `state[]` represent the values contained in each register of the encoder.

- `g[]` represent in vectorial form polynomial generator of the BCH code.

- `r` is the length of the shift register.

``` c

void BCHenc::Run(int ticks,int *m,int *out)
{
    int i,s, j,k;
    if(encStep == n) {encStep = 0;}
    if(encStep < k){
        for(i = 0; i < ticks; i++, encStep++){
        // If condition is true enable feedback 
            if(state[r-1]^m[i]){
			for(j = r-1; j >=1; j--)
				state[j] = state[j-1]^g[j];
			state[0] = 1;
		    }
			else{
			// Shifting of bits
			for(j = r-1; j >= 1; j--)
				state[j] = state[j-1];
			state[0] = 0;
			}
		out[i] = m[i];
		}
	}
	else if(encStep >=k && encStep < n){
        for(i = 0; i < ticks; i++, encStep++){
            out[i] = state[r-1];
            for(j = r-1; j >= 1; j--)
                state[j] = state[j-1];
            state[0] = 0;
		}
	}
}
```

This piece of software works serially, but the user may define the number of iterations that emulator machine has to perform. Anyway this software emulator, as its more physical version, takes $`n`$ clock ticks to encode a single codeword.

## Software Implementations of Parallel Encoder

Matrices $`\vet A^8`$ and $`\vet B_8`$ defined in have been pre-computed via software by a Matlab routine. Useful coefficients of these matrices can be stored in local variables (software) or in LUT (hardware). Note that, concerning the $`\vet A^8`$ matrix, the sub-matrices $`\vet C_1`$ and $`\vet C_2`$ should be stored in a dedicated memory for each t-error correction level to make the architecture flexible.

The first software implementation refers to the slower parallel architecture which spends $`n`$ clock ticks to provide codewords associated to messages. Pre-computed parts of the matrix $`\vet A^8`$ relevant to each operating modes are loaded and saved in memory on $`(n \virgola k)`$ (only those provided by the standard) basis. Matrix $`\vet B_p`$, already defined in <a href="#eq:Btrivial" data-reference-type="eqref" data-reference="eq:Btrivial">[eq:Btrivial]</a> (see also the example in ), is trivial and its save in memory can be avoided since that form corresponds to connect the eight inputs to the first XOR stage of the architecture. In other words, the 192 combinatorial networks on the input side (depicted in ) in this kind of architecture are not necessary.
The following function is dedicated to simulate the functioning of combinatorial networks on the output side:

- Feedback combinatorial network acting on the last eight values of the state register. Function `combn(index, n, regold)` implements the product row by column between $`\vet C_1 \virgola \vet C_2`$ and $`x_{184}\virgola \ldots \virgola x_{191}`$.

``` c

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
```

The first part of function `BCHnclkpar(int n,int k)` is relevant to the error protection level and consequently due to the state vector allocation (recall that register length can be 128, 160, 192 with respect to $`t = 8 \virgola 10 \virgola 12`$ possible values). In case of mismatch with the couples $`n \virgola k`$, provided by the standard DVB-S2 for the normal FECFRAME, simulation is aborted.
The `for` cycle in the middle part of the program updates cyclically the register of the encoder, using the above function implementing each combinatorial networks.
Eventually, output is formatted in the systematic form complyant with the DVB-S2 standard requirements.

``` c

void BCHnclk_par(int n,int k)
{
	int clock_ticks;
	int *reg, *reg_old;
	
	int input[P]; // parallel input bits 

/*  Mode Selection (t-error-correction) */

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
		fprintf(stdout,"Please insert a n-k couple 
                           provided by DVB-S2 FEC\n");
		exit(0);
	}
	/* Computation of clock ticks required 
        to compute the remainder after division */
	clock_ticks = n/P; 

	

    /* Computing remainder */
	int z=0;
	
	for (int i=0; i<clock_ticks; i++)
	{
		/* refresh of state  */
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

    /* Codeword in systematic form */

	for (i=n-1; i>n-k-1; i--)
		codeword[i] = message[i];
    
	for (i=n-k-1; i>=0; i--)
		codeword[i] =  reg[i];

}
```

The second implementation is connected to the faster architecture (its correspondent serial version is depicted in ) which spends $`k`$ clock ticks to compute parity bits, saving, compared to the first, $`r`$ clock cycles for each computation cycle or, i.e., for each encoding cycle. The function `combn(index, n, regold)` implementing the combinatorial networks on the output side is the same of the slower architecture according to what we said in Chapter <a href="#ch:BCHAlg&amp;Arch" data-reference-type="ref" data-reference="ch:BCHAlg&amp;Arch">[ch:BCHAlg&amp;Arch]</a> (i.e. matrix $`\vet A_8`$ cannot change).
Therefore here we have two functions:

- Function `combc(index, input)` provides the result of row by column product between matrix $`\vet B_8`$ and the inputs.

- Function `combn(index, n, regold)` implements the product row by column between $`\vet C_1 \virgola \vet C_2`$ and $`x_{184}\virgola \ldots \virgola x_{191}`$.

``` c

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
```

``` c

void BCHkclk_par(int n,int k)
{
	int clock_ticks;
	int *reg, *reg_old;
	int offset,m;
	
	int input[P]; // parallel input bits

    /* Mode Selection (t-error-correction) */

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
		fprintf(stdout,"Please insert a n-k 
                       couple provided by DVB-S2 FEC\n");
		exit(0);
	}
	/* Computation of clock ticks required
        to compute the remainder after division */
	clock_ticks = k/P;

    /* Computing remainder */
	
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
					reg[m] = (comb_c(m,input))^(comb_k(m,reg_old))^
                             (reg_old[m-(P)]);
			}
		}
	}
    /* Codeword in systematic form */

	for (i=n-1; i>n-k-1; i--)
		codeword[i] = message[i];

	for (i=n-k-1; i>=0 ; i--)
		codeword[i] =  reg[i+offset];
	
}
```

## Galois Fields Tables

As said in , the knowledge of the big field $`GF(2^{16})`$ where the roots of polynomial generators are is necessary to make error detection and decoding (e.g. by Berlekamp-Massey Algorithm). Galois field associated to this BCH code can be built by using $`g_1(x)`$ in , which is also the primitive polynomial of $`GF(2^{16})`$ for the reasons already expressed in .

All the $`2^{16}-1`$ elements of this field can be obtained by a LFSR structure (implementing the division algorithm as that depicted in ) where each connection/disconnection (since we are over GF(2)) corresponds to coefficients of $`g_1(x)`$. This LFSR architecture, however, performs all their operations in absence of external stimulus (i.e, the single input $`u(i)`$ is forced to zero $`u(i) = 0`$).
The state evolution repeats for each multiple of $`2^{16}-1`$: if the shift register is initialized by a unitary seed ($`0\virgola \ldots \virgola 0 \virgola 1`$), then we will find the same seed after $`2^{16}-1`$ clock ticks. This means that the initialization seed is a primitive element of GF($`2^{16}`$).
Each primitive element can be found by trial end errors:according to Definition A.3.2, when an initialization seed leads to have a 1 at $`2^{16}-1`$ clock tick, then a primitive element has been found, otherwise it does not. In our simulation, for the sake of simplicity, $`\alpha = 1`$ has been used as primitive element.

``` c

void gfField(int m, // Base 2 logarithm of cardinality of the Field
			 int poly, // primitive polynomial of the Field in decimal form
			 int ** powOfAlpha, int ** indexAlpha)
{
	int reg,	// this integer of 32 bits, masked by a sequence of m ones,
				// contains the elements of Galois Field	 		
		tmp,i;
	// sequence of m ones
	int mask = (1<<m) -1;  // 1(m) sequence of m ones
	
	// Allocation and initialization of the tables of the Galois Field
	*powOfAlpha = (int *)calloc((1<<m)-2, sizeof(int));
	*indexAlpha = (int *)calloc((1<<m)-1, sizeof(int));

	(*powOfAlpha)[0] = 1;
	(*indexAlpha)[0] = - 1; // conventionally we set -1
	(*indexAlpha)[1] = 0;

	for (i = 0, reg = 1; i < (1<<m)-2; i++)
	{
			tmp = (int)(reg & (1<<(m-1))); // Get the MSB
            reg <<= 1;   // Shift
            if( tmp) { 
				reg ^= poly;
				reg &= mask;
			}
			// Step-by-step writing of the tables
			(*powOfAlpha)[i+1] = (int) reg;
			(*indexAlpha)[(int)reg] = i+1;
    }
		

}
```

At each clock cycle (evolution of the shift-register state) two tables are written down:

1.  Each $`\alpha^i`$ for $`i = 1\virgola \ldots \virgola 2^{16}-2`$ is stored in the `powOfAlpha[i]` vector/table.

2.  Inverse of the `powOfAlpha[i]` vector/table is saved in the vetor/table
    `index­Al­pha[i]` which, given the $`\alpha^i`$ value (in decimal notation), provides the correspondent exponent of primitive element $`\alpha`$. In practice, this vector/table expresses a base $`\alpha`$ logarithm (i.e. $`\log_{\alpha}`$ operator).

Usefulness of these two vector/tables will be made clear later on.

## Decoding BCH

Algebraic decoding of a binary BCH code consists of the following steps:

1.  Computation of syndrome (this is implemented by `errordetection` function).

2.  Determination of an *error locator polynomial*, whose roots provide an indication of where the errors are. There are two ways of finding the locator polynomial: Peterson’s algorithm and the Berlekamp-Massey algorithm (used in our simulations). In addition, there are techniques based on Galois-field Fourier transforms.

3.  Finding the roots of the error locator polynomial. Usually, this is done using the *Chien search*, which is an exhaustive search over all elements in the field.

### Error Detection

Before trying to decode a BCH codeword, a preliminary error detection must be accomplished. Parity check <a href="#eq:pchk" data-reference-type="eqref" data-reference="eq:pchk">[eq:pchk]</a> evaluation in the $`2t`$ roots of polynomial generator provides the code syndrome
``` math
\begin{equation}
 \label{eq:syndr}
\vet S = S_1 = c(\alpha) \virgola S_2 = c(\alpha^2) \virgola \ldots \virgola S_{2t} = c(\alpha^{2t})
\end{equation}
```
If the codeword received has not been corrupted by noise, then the syndrome is null since $`g(\alpha) = g(\alpha^2) = \ldots = g(\alpha^{2t})`$; otherwise it is not and then the decoding should be accomplished to exploit redundancy introduced and try to correct errors occurred. Values in <a href="#eq:syndr" data-reference-type="eqref" data-reference="eq:syndr">[eq:syndr]</a> lie over $`GF(2^{16})`$ and all the decoding operations have to be carried out in the Galois field where the roots are.

``` c

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
```

To evaluate the $`2t`$ equations relevant to the syndrome, the tables/vectors pre-computed (because roots are always in $`GF(2^{16})`$, given that BCH code is *shortened*) are necessary to compute the $`2t`$ syndromes. In fact, the function `errordetection()` takes as parameters `powOfAlpha[], indexAlpha[]` vectors. They are useful to

- compute products among elements of $`GF(2^{16})`$ expressed in exponential form (recall that each element in Galois fields can be written as any power of any primitive element), exploiting exponential properties which still hold in finite fields;

- find the correspondent power of the primitive element which represents, for example, the sum between two elements of GF (e.g. $`\alpha^2 + \alpha^{11}`$).

If any error is detected (i.e. `syn` is `true`) then the codeword corrupted can be corrected using the Berlekamp-Massey algorithm.

### Berlekamp-Massey Algorithm

Before giving a brief description of the algorithm, let us introduce some notation and mathematical concept. Returning to <a href="#eq:syndr" data-reference-type="eqref" data-reference="eq:syndr">[eq:syndr]</a>, suppose that $`\vet r`$, the received vector, contains $`\nu`$ errors in locations $`i_1 \virgola i_2 \virgola \ldots \virgola i_{\nu}`$ so that each element of $`\vet S`$ can be rewritten as
``` math
\begin{equation}
S_j = \sum_{l =1}^{\nu} {{(\alpha^j)}^{i_l}} = \sum_{l =1}^{\nu} {{(\alpha^{i_l})}^j}
\end{equation}
```
Letting $`X_l = \alpha^{i_l}`$, we obtain the following $`2t`$ equations
``` math
\begin{equation}
S_j = \sum_{l =1}^{\nu} {{X_l}^j} \qquad j = 1\virgola 2\virgola \ldots \virgola 2t
\end{equation}
```
in the $`\nu`$ unknown error locators. In principle this set of nonlinear equations could be solved by an exhaustive search, but this would be computationally expensive or intractable.
To overcome this problem, a new polynomial is introduced, the *error locator polynomial* which casts the problem in a different, and more tractable, setting.

The error locator polynomial is defined as
``` math
\begin{equation}
 \label{eq:elp}
\Lambda(x) = \prod_{l = 1}^{\nu} {(1-X_lx)} = \Lambda_{\nu}x^{\nu} + \ldots +\Lambda_1x + \Lambda_0
\end{equation}
```
where $`\Lambda_0 = 1`$. In practice, the roots of <a href="#eq:elp" data-reference-type="eqref" data-reference="eq:elp">[eq:elp]</a> are at the reciprocals of the error locators.

It is possible to demonstrate (for this proof and further information see ) that there exist a linear feedback shift register relationship between the syndromes and the coefficients of the error locator polynomial. In practice, we can write
``` math
\begin{equation}
 \label{eq:SynLocLFSR}
S_j = - \sum_{i = 1}^{\nu} {\Lambda_i S_{j-i}} \qquad j = \nu+1 \virgola \nu + 2 \virgola \ldots \virgola 2t
\end{equation}
```
This formula describes the output of a linear feedback shift register (LFSR) with coefficients $`\Lambda_1 \virgola  \Lambda_2 \virgola \ldots \virgola \Lambda_{\nu}`$. From this point of view, the decoding problem consists of finding $`\Lambda_j`$ coefficients in such a way that the LFSR generates the known sequence of syndromes $`S_1\virgola S_2\virgola \ldots \virgola S_{2t}`$.

In the Berlekamp-Massey algorithm, we build the LFRS that produces the entire sequence $`\{S_1\virgola S_2\virgola \ldots \virgola S_{2t} \}`$ by successively modifying an existing LFSR, if necessary to produce increasingly longer sequences. Clearly, we start with an LFRS that could produce $`S_1`$. We determine if that LFRS could also produce the sequence $`\{S_1\virgola S_2\}`$; if it can, then no modifications are necessary. If the sequence cannot be produced using the current LFSR configuration, we determine a new LFRS that can produce the longer sequence. Proceeding inductively in this way, we start from an LFSR capable of producing the sequence $`\{S_1\virgola S_2\virgola \ldots \virgola S_{k-1} \}`$ and modify it, if necessary, so that it can also produce the sequence $`\{S_1\virgola S_2\virgola \ldots \virgola S_{k} \}`$. At each stage, the modification to the LFRS are accomplished so that the LFSR is the shortest possible. By this means, after completion of the algorithm an LFSR has been found that is able to produce $`\{S_1\virgola S_2\virgola \ldots \virgola S_{2t} \}`$ and its coefficients correspond to the error locator polynomial $`\Lambda(x)`$ of smallest degree.

Since we build up the LFSR using information from prior computations, we need a notation to represent the $`\Lambda(x)`$ used at different stages of algorithm. Let $`L_k`$ denote the length of LFSR produced at stage $`k`$ of the algorithm. Let
``` math
\begin{equation}
\Lambda^{[k]}(x) = 1 + \Lambda_1^{[k]}x + \cdots + \Lambda_{L_k}^{[k]}x^{L_k}
\end{equation}
```
be the *connection polynomial* at stage $`k`$, indicating the connections for the LFSR capable of producing the output sequence $`\{S_1\virgola S_2\virgola \ldots \virgola S_{k} \}`$. That is,
``` math
\begin{equation}
S_j = - \sum_{i = 1}^{L_k} {\Lambda_i^{[k]} S_{j-i}} \qquad j = L_k+1 \virgola L_k + 2 \virgola \ldots \virgola k
\end{equation}
```

At some intermediate step, suppose we have a connection polynomial $`\Lambda^{[k-1]}(x)`$ of length $`L_{k-1}`$ that produces $`\{S_1\virgola S_2\virgola \ldots \virgola S_{k-1} \}`$ for some $`k-1 < 2t`$. We check if this connection polynomial also produces $`S_k`$ by computing the output
``` math
\begin{equation}
\hat{S_k} = - \sum_{i = 1}^{L_k-1} {\Lambda_i^{[k-1]} S_{k-i}}
\end{equation}
```
If $`\hat{S_k}`$ is equal to $`S_k`$, then there is no need to update the LFSR, so $`\Lambda^{[k]}(x)= \Lambda^{[k-1]}(x)`$ and $`L_k=L_{k-1}`$. Otherwise, there is some nonzero *discrepancy* associated with $`\Lambda^{[k-1]}(x)`$,
``` math
\begin{equation}
 \label{eq:discrepancy}
d_k = S_k - \hat{S_k} = S_k + \sum_{i = 1}^{L_k-1} {\Lambda_i^{[k-1]} S_{k-i}} =
\sum_{i = 0}^{L_k-1} {\Lambda_i^{[k-1]} S_{k-i}}
\end{equation}
```
In this case we can update the connection polynomial using the formula
``` math
\begin{equation}
\Lambda^{[k]}(x) = \Lambda^{[k-1]}(x) + A x^l \Lambda^{[m-1]}(x)
\end{equation}
```
where $`A`$ is some element in the field, $`l`$ is an integer, and $`\Lambda^{[m-1]}(x)`$ is one of the prior connection polynomials produced by our process associated with nonzero discrepancy $`d_m`$.
Using this new connection polynomial, we compute the new discrepancy, denoted by $`{d_k}'`$, as
``` math
\begin{align}
{d_k}' &= \sum_{i = 0}^{L_k} {\Lambda_i^{[k]} S_{k-i}}\\
     &= \sum_{i = 0}^{L_k-1} {\Lambda_i^{[k-1]} S_{k-i}} + A \sum_{i = 0}^{L_m-1} {\Lambda_i^{[m-1]} S_{k-i-l}} \label{eq:discrep2}
\end{align}
```
Now, let $`l=k-m`$. Then, by comparison with the definition of the discrepancy in <a href="#eq:discrepancy" data-reference-type="eqref" data-reference="eq:discrepancy">[eq:discrepancy]</a>, the second summation gives
``` math
\begin{equation}
A \sum_{i = 0}^{L_m-1} {\Lambda_i^{[m-1]} S_{m-i}} = A d_m
\end{equation}
```
Thus, if we choose $`A=-d_m^{-1}d_k`$, then the summation in <a href="#eq:discrep2" data-reference-type="eqref" data-reference="eq:discrep2">[eq:discrep2]</a> gives
``` math
\begin{equation}
{d_k}' = d_k -d_m^{-1} d_k d_m = 0
\end{equation}
```
So the new connection polynomial produces the sequence $`\{S_1\virgola S_2\virgola \ldots \virgola S_{k} \}`$ with no discrepancy. We do not investigate here on how to find the shortest LFSR reproducing syndromes with no discrepancy. We assume that below algorithm could do that. For a complete treatment on LFSR length in Massey algorithm see .

Algorithm shown below use the following variables

- Vectors/tables `pow`, `index` to simplify multiplications among the elements of the Galois field

- Vector `c[]`, which indicates the current connection polynomial, that is
  ``` math
  c(x) = \Lambda^{[k]}(x)
  ```
  Vector `p[]`, which indicates a previous connection polynomial, in formula
  ``` math
  p(x)=\Lambda^{[m-1]}(x)
  ```

- Variable `d`, which indicates the discrepancy computed at the current time; variable `dm`, which however indicates the discrepancy computed with $`p(x)`$ connection polynomial, i.e., at any previous time

- An auxiliary vector `T[]` to be used during the update cycle (with length change) of vector `c[]`

- Variable `l` represents the amount of shift in update, namely $`l = k-m`$; `L` contains the current length of the LFSR

Let us start to briefly describe the set of operations carried out by the `BerlMass()` C function. After the initialization step, the following operations are accomplished:

1.  Compute discrepancy by $`S_k+ \sum_{i = i}^{L} {c_i S_{k-i}}`$ calculation. This computation is made by the useful pre-computed tables `pow[], index[]`, and using the ANSI C bit-wise operators.

2.  If the result of that calculation is zero, then there is no change in polynomial and `l` turns `l+1`. If discrepancy is nonzero, then there exist two options yet:

    - If the double of the current LFSR length is greater equal than `k`, the step counter, then $`c(x)`$ is updated, but retains its length.

    - Else $`c(x)`$ length and values change together. The non-updated $`c(x)`$ is saved into $`p(x)`$ and so the discrepancy associated to is stored into `dm`. The amount of shift in update turns 1.

After $`2t`$ cycles, $`c(x)`$ contains the coefficients of error locator polynomial $`\Lambda(x)`$.

``` c
void BerlMass(//int *S, // array of syndrome in exponential notation
			  int t2, // length of array S
			  int *pow,
			  int *index)
			
{
	int k,L,l,i;
	int d, dm, tmp;
	int *T, *c, *p, *lambda,*el;
	/* Allocation and initialization of local variables */
	/* Auto-Regressive-Filter coefficients
          computed at the previous step */
	p = (int*) calloc(t2,sizeof(int));
	/* Auto-Regressive-Filter coefficients
        computed at the current step */
	c = (int*) calloc(t2,sizeof(int));
	/* Temporary array */
	T = (int*) calloc(t2,sizeof(int));
	/* error location array (found by Chien Search) */
	el = (int*) calloc(t2,sizeof(int));
	/* Error polynomial locator	*/
	lambda = (int*) calloc(t2,sizeof(int));
	
	
	/* Initialization step */
	c[0] = 1;
	p[0] = 1;
	L = 0;
	l = 1;
	dm = 1;
	
    /* Berlekamp-Massey Algorithm */
	for (k = 0; k < t2; k++)
	{
		/* Discrepancy computation */
		if(S[k] == -1)
			d = 0;
		else
			d = pow[S[k]];
		for(i = 1; i <= L;i++)
			if(S[k-i] >= 0 && c[i] > 0)
			d ^= pow[(index[c[i]]+ S[k-i])%MAXN];
			/*Multiplication of alpha power */ 		
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
	
	
	
    /* Storing of error locator polynomial coefficient */	
	for(i = 0; i <=L; i++)
		lambda[i] = index[c[i]];
	
    /* Chien search */
    /* Roots searching */
	
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
	
fprintf(o3,"\n\n-------------------
------------------------------------------------");


	
} 
```

### Chien Search

Having now the error locator, its root must be found in our field of interest ($`GF(2^{16}`$). Since the search must be accomplished in a finite field, we can examine every element of the field to determine if it is a root. Thus polynomial $`\Lambda(x)`$ can be evaluated at each nonzero element of the field in succession: $`x=1 \virgola x= \alpha \virgola x = \alpha^2 \virgola \ldots \virgola x= \alpha^{2^{16}-2}`$.

This can be easily implemented by two nested `for` cycles: the outer scans all the elements in GF, the inner evaluate the polynomial performing the above substitution and accumulating (step-by-step) in a `tmp` temporary variable its result. Clearly, if the overall result of this calculation gives 1 (in index form), then a root has been found. Supposing, for example, to have found $`\alpha^{12}`$ as root. Its inversion can be easily accomplished using some elementary properties of finite fields: expression $`\alpha^{-12}`$ can be thought as $`\alpha^{-12}\alpha^{2^{16}-1} = \alpha^{2^{16}-13}`$.

If the roots found are distinct and all lie in the reference field, then we use these to determine the error locations. If they are not distinct or lie in the wrong field, then the received word is not within distance $`t`$ of any codeword. The correspondent error pattern is said to be an uncorrectable error pattern. An uncorrectable error pattern results in a decoder failure.

## Software Robustness and Validation

The first proof of software functioning consists in a set of simulations to validate the package developed in C programming language and thus support VHDL designers in synthesization of the BCH encoder architecture. To this latter specific purpose, it was convenient setting up a package which can be used to simulate not only the correct functioning of the envisaged parallel encoder but, above all, his capacity of correcting $`t`$ errors on a operating mode basis.

This has been accomplished interconnecting each block of an ideal communication chain composed, in order, by:

A Pseudo-Noise Source:  
a LFSR with optimum taps, i.e., capable of generate sequences of maximum period;

BCH Encoder/s  
which emulates each kind of architectures and algorithms already discussed. The type of algorithm and relevant architecture to be emulated can be selected by the user before starting simulation cycle.

An Error Pattern Generator:  
without any loss of generality, the macro-block channel plus modem has been substituted by a pseudo-random error pattern generator. It generates an IID (Independent Identically Distributed) stochastic process whose samples, representing the errors occurred during the frame transmission, are distributed as an uniform p.d.f. In practice, we shall simulate an hard detection/corretion of errors.

An Error Detection Block and Syndrome Calculator:  
this block have the  
simple task of computing syndromes associated to a received codeword. Clearly, if any error is occurred then the codeword must be processed by decoder to try correcting errors. Otherwise, no codewords are needed being corrected.

A Berlekamp Massey Decoder:  
when the number of errors is less or equal to $`t`$, Berlekamp Massey algorithm and, in turn, the Chien search of roots can correct the errors occurred during transmissions; in the other cases the decoder state its failure in decoding.

In order to verify the functionality of all the algorithms, the positions of error found at the decoder size are compared with the positions added by the error pattern generation function. In case of any mismatch with the added error positions between decoder and error generator, a decoding failure is stated. The result of each simulation cycle can be saved onto a file, which can be indicated by the user.

### Error Pattern Generation

Positions of errors are determined by using a C function (`uniform01()`) generating a uniform distributed r.v. between $`[0\virgola1[`$, namely $`X`$; then
``` math
Y = \lfloor n\ped{bch}\cdot X \rfloor
```
represent the random error location, distributed uniformly between $`[0\virgola n\ped{bch}-1]`$.

### The C Code

This section provides the code used in the simulation campaign (the implementation of `uniform01()` will be omitted).

``` c
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
```

[^1]: Clearly, in software, this distinction is not so strict

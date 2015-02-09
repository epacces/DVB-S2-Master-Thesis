void BCHnclk_par(int n,int k)
{
	int clock_ticks;
	int *reg, *reg_old;

	int input[P]; // parallel input bits

/*Mode Selection (t-error-correction)*/

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



/* Computing remainder */
	int z=0;

	for (int i=0; i<clock_ticks; i++)
	{
		/* refresh of state */
		for (int m=0; m<n-k; m++)
			reg_old[m]=reg[m];
		/* loading of parallel inputs */
		for (int count=P-1; count>=0; count--)
		{
			z++;
			input[count] = message[n-z];
		}
		/* Computing of next values of state */
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

	}


/* Codeword in systematic form */

	for (i=n-1; i>n-k-1; i--)
		codeword[i] = message[i];

	for (i=n-k-1; i>=0; i--)
		codeword[i] =  reg[i];

}

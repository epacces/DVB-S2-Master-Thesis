
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

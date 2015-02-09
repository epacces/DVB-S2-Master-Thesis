void BCH_s_enc(int n, int k)
{
	
	const unsigned int *g;
	int *reg;
	int mem,app,i,j;

/* User interface definition: Mode Selection (t-error-correction)*/

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

/* Encoding serial algorithm */
/* n clock ticks */	
/* Computing of remainder */

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

/* Codeword in systematic form */

	for (i=n-1;i>=n-k;i--)
		codeword[i] = message[i];
	for (i=n-k-1; i >=0; i--)
		codeword[i] = reg[i];
	
	free(reg);
}

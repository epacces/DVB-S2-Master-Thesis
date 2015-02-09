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

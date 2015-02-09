
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

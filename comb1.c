
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

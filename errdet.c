
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

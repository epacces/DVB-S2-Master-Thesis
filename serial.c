
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

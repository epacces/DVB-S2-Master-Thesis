
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

# DVB-S2 LDPC parity-bit address tables

One file per code: `normal_R.txt` (N = 64800, ETSI EN 302 307-1 Annex B) and
`short_R.txt` (N = 16200, Annex C). Line *i* lists the parity accumulator
addresses for information bits 360·i … 360·i + 359, exactly as printed in the
standard.

The numbers were converted with `sim/tools/import_ldpc_tables.py` from the
[AFF3CT](https://github.com/aff3ct/aff3ct) headers
`include/Tools/Code/LDPC/Standard/DVBS2/DVBS2_constants_{64800,16200}.hpp`,
distributed under the MIT licence:

> Copyright (c) 2017-2025 aff3ct
>
> Permission is hereby granted, free of charge, to any person obtaining a copy
> of this software and associated documentation files (the "Software"), to deal
> in the Software without restriction, including without limitation the rights
> to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
> copies of the Software, and to permit persons to whom the Software is
> furnished to do so, subject to the following conditions:
>
> The above copyright notice and this permission notice shall be included in all
> copies or substantial portions of the Software.
>
> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
> IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
> FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
> AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
> LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
> OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
> SOFTWARE.

The test suite checks every table against the standard's structure: H·cᵀ = 0
for encoded frames and the variable-node degree profile of EN 302 307-1
Tables 7a/7b.

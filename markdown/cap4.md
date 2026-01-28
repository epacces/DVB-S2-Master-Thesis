# Hardware Implementation of BCH Encoder

## FEC Encoding Section

The parallelism of the input memory of the LDPC encoding section suggests a $`p = 8`$ degree of parallelism for BCH architecture. First, because LDPC input memory requires 360 bits and LDPC encoder processes the same number of bits at every clock ticks (i.e., it has 360 as degree of parallelism). Hence, $`p`$ should be a divisor of 360.
Second, $`p`$ should be even a divisor of each BCH block length ($`n\ped{bch}`$) associated to LDPC coding rates, provided by DVB-S2.
Furthermore, BCH serial architectures based on LFSRs are, of course, simple to implement, but generally they are very slow (i.e., they reach typically a lower throughput). Therefore, in order to best match BCH encoding speed with the frequency requirements imposed by the overall designed TX DVB-S2 section, we have chosen a degree of parallelism equal to 8.

Encoded bits, passing through an interface circuit, enter LDPC input memory on a byte basis. The interface allows each codeword coming from BCH encoder to be read in the proper order and format (recall that a systematic code is required as output). A block diagram of the overall FEC section is depicted in .

<figure id="fig:ovrsys">
<img src="FECARCH.jpg" style="width:80.0%;height:35.0%" />
<figcaption>Block diagram of the overall FEC tx section</figcaption>
</figure>

As we shall detail in the next section, the interface between BCH and LDPC is constituted by a simple 8 bits multiplexer together with a suited circuitry to store and download the parity bits after each computation cycle. This interface addresses properly encoded bits into LDPC input memory and it must be driven by a control logic based on clock cycles required (see ) to provide a codeword.

Another important question to raise up is certainly giving the architecture a flexible structure so as to succeed in dealing with each coding rate provided by DVB-S2 FEC. A more versatility, as we shall see, requires an additional usage of memory: as a matter of fact, some additional coefficient of matrices mentioned in the previous chapter must be stored into some LUTs (Look Up Tables).

<div id="tb:clkreq">

| BCH Uncoded Block | BCH Coded Block $`N\ped{BCH}`$ | Ticks to transmit informative bits | Parity bits download | Total clock cycles |
|:---|:---|:---|:---|:---|
|  |  |  |  |  |
|  |  |  |  |  |
|  |  |  |  |  |
|  |  |  |  |  |
|  |  |  |  |  |
|  |  |  |  |  |
|  |  |  |  |  |
|  |  |  |  |  |
|  |  |  |  |  |
|  |  |  |  |  |
|  |  |  |  |  |

Clock cycles required to provide each codeword for each operating mode of DVB-S2

</div>

## Encoder Description

A block diagram of BCH encoder architecture is shown in . A brief description on its functioning is given below.

- All the informative $`k\ped{bch}`$ bits enter in parallel ($`p`$ bits, i.e., 8 at once), from MSB to LSB, all 192 combinatorial blocks, which perform logic function indicated by $`\vet B_p`$ matrix. In other words, each block carries out a row by columns product (over $`GF(2)`$) between the $`i`$-th row of $`\vet B_p`$ the $`p`$ inputs. Since operations are in GF(2), sums are implementable by XOR gates, multiplications by AND gates. gives a schematic illustration of each combinatorial networks processing $`p`$ inputs.

- Each flip-flop labelled by $`x_i`$ represents a single bit of state vector $`\vet x`$ of the system and after exactly $`\frac{k\ped{bch}}{p}`$ clock ticks it contains the result of division algorithm.

- Combinatorial networks toward the BCH-to-LDPC interface (i.e, on the output side) perform the feedback: each XOR gate is fed by the last $`p`$ bits of register state $`\vet x`$ (from $`x_{184}`$ to $`x_{191}`$) passing through output-combinatorial network described by the two sub-matrices $`\vet C_1`$ and $`\vet C_2`$ (see ). More in details, expression <a href="#eq:Apreg" data-reference-type="eqref" data-reference="eq:Apreg">[eq:Apreg]</a> in , showing an high regularity of $`\vet A^p`$, allows to split computation of the first term in <a href="#eq:SEmatr" data-reference-type="eqref" data-reference="eq:SEmatr">[eq:SEmatr]</a> (i.e, $`\vet A^p \vet x \left[ (i-1)p \right]`$) in two contributes

  1.  row by column products involving last $`p`$ bits of $`\vet x`$ and therefore last $`p`$ columns of matrix $`\vet A^p`$. In other words, the combinatorial networks near to BCH-LDPC interface perform the following product
      ``` math
      \begin{equation}
       \label{eq:prodotto}
              \left(
              \begin{array}{c}
              \vet C_1 \\
              \vet C_2
              \end{array}
              \right)
              \left(
              \begin{array}{c}
              x_{184}(i) \\
              \vdots \\
              x_{191}(i)
              \end{array}
              \right)
      \end{equation}
      ```

  2.  row by column product involving (starting from bit $`x_8`$ of vector $`\vet x`$ which correspond to row 9 of matrix $`\vet A^p`$) first $`n-k-p`$ bits of vector $`\vet x`$ is realized by sum modulo 2 (i.e., XOR gates) nodes on the right of the combinatorial networks. gives a schematic representation of this combinatorial networks together with modulo 2 sum nodes.

- Logic functions relevant to sub-matrix $`\vet I`$ of $`\vet A^p`$ are implemented by XOR gates at the output of combinatorial networks connected to the last $`p`$ bits of the state vector.

- At the end of each computation cycle, the encoder register must be reset.

Due to intrinsic simplicity of matrices $`\vet A^p`$ and $`\vet B_p`$ (they are only composed by zeroes and ones), the two combinatorial networks can be implemented in a very simple way by programmable XOR gates with eight inputs.
More in detail, each coefficient of the above two matrices says which wires have to be connected to each combinatorial network (XOR).

=\[draw, minimum height=9cm, text centered,
inner sep= 0pt, text width= 4em, minimum width= 3cm\]

<figure id="fig:COMBout">
<div class="signalflow">
<p>(i1) <span><span class="math inline"><em>x</em><sub>184</sub></span></span>;
(i2) [below from=i1] <span><span class="math inline"><em>x</em><sub>185</sub></span></span>;
(i3) [below from=i2] <span><span class="math inline"><em>x</em><sub>186</sub></span></span>;
(i4) [below from=i3] <span><span class="math inline"><em>x</em><sub>187</sub></span></span>;
(i5) [below from=i4] <span><span class="math inline"><em>x</em><sub>188</sub></span></span>;
(i6) [below from=i5] <span><span class="math inline"><em>x</em><sub>189</sub></span></span>;
(i7) [below from=i6] <span><span class="math inline"><em>x</em><sub>190</sub></span></span>;
(i8) [below from=i7] <span><span class="math inline"><em>x</em><sub>191</sub></span></span>;
(m1) [right from= i1,label=above:<span class="math inline">$a_{j\virgola 184}$</span>] ;
(m2) [right from= i2,label=above:<span class="math inline">$a_{j\virgola 185}$</span>] ;
(m3) [right from= i3,label=above:<span class="math inline">$a_{j\virgola 186}$</span>] ;
(m4) [right from= i4,label=above:<span class="math inline">$a_{j\virgola 187}$</span>] ;
(m5) [right from= i5,label=above:<span class="math inline">$a_{j\virgola 188}$</span>] ;
(m6) [right from= i6,label=above:<span class="math inline">$a_{j\virgola 189}$</span>] ;
(m7) [right from= i7,label=above:<span class="math inline">$a_{j\virgola 190}$</span>] ;
(m8) [right from= i8,label=above:<span class="math inline">$a_{j\virgola 191}$</span>] ;
(8XOR) [right from=m4] <span>XOR</span>;
(c1) [right from=8XOR] ;
(a1) [right from=c1] ;
(x) [above from=a1, label=above:<span><span class="math inline"><em>x</em><sub><em>j</em> − 8</sub>(<em>i</em>)</span> for <span class="math inline"><em>j</em> ≥ 8</span></span>] ;
(out) [right from=a1, label=right:<span><span class="math inline"><em>y</em><sub><em>j</em></sub>(<em>i</em>)</span></span>] ;
(i1)–(m1);
(i2)–(m2);
(i3)–(m3);
(i4)–(m4);
(i5)–(m5);
(i6)–(m6);
(i7)–(m7);
(i8)–(m8);
(m1) – +(1,0);
(m2) – +(1,0);
(m3) – +(1,0);
(m4) – +(1,0);
(m5) – +(1,0);
(m6) – +(1,0);
(m7) – +(1,0);
(m8) – +(1,0);
(8XOR) – (c1);
(x)–(a1);
(c1)–(a1);
(a1)–(out);</p>
</div>
<figcaption>Block scheme of the combinatorial networks acting on the last <span class="math inline"><em>p</em></span> bits of <span class="math inline">$\vet x$</span>. <span class="math inline">$a_{j \virgola l}$</span> is the coefficient at <span class="math inline"><em>j</em></span>-th row and <span class="math inline"><em>l</em></span>-th column of <span class="math inline">$\vet A^8$</span> matrix </figcaption>
</figure>

<figure id="fig:COMBin">
<div class="signalflow">
<p>(i1) <span><span class="math inline"><em>u</em>(<em>i</em><em>p</em> − 1)</span></span>;
(i2) [below from=i1] <span><span class="math inline"><em>u</em>(<em>i</em><em>p</em> − 2)</span></span>;
(i3) [below from=i2] <span><span class="math inline"><em>u</em>(<em>i</em><em>p</em> − 3)</span></span>;
(i4) [below from=i3] <span><span class="math inline"><em>u</em>(<em>i</em><em>p</em> − 4)</span></span>;
(i5) [below from=i4] <span><span class="math inline"><em>u</em>(<em>i</em><em>p</em> − 5)</span></span>;
(i6) [below from=i5] <span><span class="math inline"><em>u</em>(<em>i</em><em>p</em> − 6)</span></span>;
(i7) [below from=i6] <span><span class="math inline"><em>u</em>(<em>i</em><em>p</em> − 7)</span></span>;
(i8) [below from=i7] <span><span class="math inline"><em>u</em>[<em>p</em>(<em>i</em> − 1)]</span></span>;
(m1) [right from= i1,label=above:<span class="math inline">$b_{j\virgola 0}$</span>] ;
(m2) [right from= i2,label=above:<span class="math inline">$b_{j\virgola 1}$</span>] ;
(m3) [right from= i3,label=above:<span class="math inline">$b_{j\virgola 2}$</span>] ;
(m4) [right from= i4,label=above:<span class="math inline">$b_{j\virgola 3}$</span>] ;
(m5) [right from= i5,label=above:<span class="math inline">$b_{j\virgola 4}$</span>] ;
(m6) [right from= i6,label=above:<span class="math inline">$b_{j\virgola 5}$</span>] ;
(m7) [right from= i7,label=above:<span class="math inline">$b_{j\virgola 6}$</span>] ;
(m8) [right from= i8,label=above:<span class="math inline">$b_{j\virgola 7}$</span>] ;
(8XOR) [right from=m4] <span>XOR</span>;
(c1) [right from=8XOR] ;
(a1) [right from=c1] ;
(x) [above from=a1, label=above:<span><span class="math inline"><em>y</em><sub><em>j</em></sub>(<em>i</em>)</span></span>] ;
(out) [right from=a1, label=right:<span><span class="math inline"><em>x</em><sub><em>j</em></sub>(<em>i</em> + 1)</span></span>] ;
(i1)–(m1);
(i2)–(m2);
(i3)–(m3);
(i4)–(m4);
(i5)–(m5);
(i6)–(m6);
(i7)–(m7);
(i8)–(m8);
(m1) – +(1,0);
(m2) – +(1,0);
(m3) – +(1,0);
(m4) – +(1,0);
(m5) – +(1,0);
(m6) – +(1,0);
(m7) – +(1,0);
(m8) – +(1,0);
(8XOR) – (c1);
(x)–(a1);
(c1)–(a1);
(a1)–(out);</p>
</div>
<figcaption>Block scheme representing the combinatorial networks acting on the <span class="math inline"><em>p</em></span> bit of input. <span class="math inline">$b_{j \virgola l}$</span> is the coefficient at <span class="math inline"><em>j</em></span>-th row and <span class="math inline"><em>l</em></span>-th column of the <span class="math inline">$\vet B_8$</span> matrix</figcaption>
</figure>

## Dealing with Each Error Protection

Architecture we have shown as far can only address the greater $`t`$ error protection modalities. However, DVB-S2 has been designed to operate in ACM (Adaptive Coding and Modulation) mode, so that a flexible architecture, capable of changing his behavior on a frame basis, would be more desirable.

From our analysis of the two matrices, we have reach the conclusion that they are very regular and, even changing the polynomial generator of the code, this interesting property still holds. The degree of parallelism $`p`$, once set by design, cannot vary. Henceforth all our considerations will be constrained to a specific degree of parallelism, $`p=8`$, even though the method we are going to show is general at all.

BCH of DVB-S2 provides three protection level $`t = 8\virgola 10 \virgola 12`$ associated to the following different generators
``` math
\begin{align}
g\ped{t_{12}}(x) & = g_1(x)g_2(x)\ldots g_{12}(x) \label{eq:BCHt12}\\
g\ped{t_{10}}(x) & = g_1(x)g_2(x)\ldots g_{10}(x) \label{eq:BCHt10}\\
g\ped{t_8}(x) & = g_1(x)g_2(x)\ldots g_{8}(x) \label{eq:BCHt8}
\end{align}
```
where the above polynomials are in .
According to the decrease of the degree of polynomial generator, also the number $`r`$ of redundancy bits decreases and thus the number of FFs illustrated in would be oversized. This implies that, $`\vet x`$ being changed, size of matrices $`\vet A^8`$ and $`\vet B_8`$ has to change. In we have shown that, for a reasonable level of parallelism, matrix $`\vet A^p`$ shows some regularity. In practice, its structure shown in <a href="#eq:Apreg" data-reference-type="eqref" data-reference="eq:Apreg">[eq:Apreg]</a> does not change from $`t_8`$ to $`t_{12}`$, although its coefficients are, of course, subject to variations. Same consideration can be made upon $`\vet B_p`$ matrix, which however shows no regularity property for this kind of architecture.

and clearly show that these kind of combinatorial network are programmable by means of their coefficients, determining which wire has to be connected to the 8-inputs XOR gate and which not. Imposing, for example, that all of these coefficients are forced to zero, we would get the result of having inhibited the $`j`$-th combinatorial network. This is exactly what we can do to deal with all the protection level $`t`$.

In particular, either $`\vet A^8`$ or $`\vet B_8`$ can be embedded into the their largest matrices of size, respectively, $`192 \times 192`$ and $`192 \times 8`$ in this way:

Medium Protection Level  
($`t=10`$) Matrices $`(\vet A^8)\ped{o}`$ and $`(\vet B_8)\ped{o}`$ oversized (they should be $`160 \times 160`$ and $`160 \times 8`$ respectively) turn out to be as follows
``` math
\begin{align}
    (\vet A^8)\ped{o} &=
    \left(
    \begin{array}{cc}
    \vet 0 & \vet 0 \\
    \vet 0 & (\vet A^8)\ped{t_{10}}
    \end{array}
    \right) &
    (\vet B_8)\ped{o} &=
    \left(
    \begin{array}{c}
    \vet 0 \\
    (\vet B_8)\ped{t_{10}}
    \end{array}
    \right)
\end{align}
```
<span id="eq:embedding" label="eq:embedding"></span>
This corresponds to inhibit the first 32 couples of combinatorial networks since their coefficients are all nulls. Thus, all the first 32 FFs (from $`x_0`$ to $`x_{31}`$) of the BCH encoder will contain always zeroes.

Low Protection Level  
($`t=8`$) The oversized matrices are build in the same manner and now the first 64 couples of combinatorial networks are inhibited since their coefficients are all nulls.

<figure id="fig:HWarch">
<p>= [line width=2pt,
&gt;= real tip,
draw]
= [minimum size=]</p>
<div class="signalflow">
<p>(c1) ;
(a1) [right from=c1] <span><span class="math inline">$\vet b_1 \vet u$</span></span>;
(a2) [below from=a1] <span><span class="math inline">$\vet b_2 \vet u$</span></span>;
(a3) [below from=a2] <span><span class="math inline">⋮</span></span>;
(a8) [below from=a3] <span><span class="math inline">$\vet b_8 \vet u$</span></span>;
(a9) [below from=a8] <span><span class="math inline">$\vet b_9 \vet u$</span></span>;
(phh) [below from=a9] <span><span class="math inline">⋮</span></span>;
(a183) [below from=phh] <span><span class="math inline">$\vet b_{184} \vet u$</span></span>;
(a184) [below from=a183] <span><span class="math inline">$\vet b_{185} \vet u$</span></span>;
(a186) [below from=a184] <span><span class="math inline">⋮</span></span>;
(a191) [below from=a186] <span><span class="math inline">$\vet b_{192} \vet u$</span></span>;
(c2) [left from=a2] ;
(c3) [left from=a8] ;
(c4) [left from=a9] ;
(c9) [below from=c4, below=2.37cm] ;
(c182) [below from=c9,below=.63cm] ;
(c183) [left from=a191, right=.14cm] ;</p>
<p>(input) [left from=c9] ;
(x1) [right from=a1, left=0cm] ;
(x2) [right from=a2,left=0cm] ;
(x8) [right from=a8,left=0cm] ;
(x9) [right from=a9,left=0cm] ;
(x183) [right from=a183,left=0cm] ;
(x184) [right from=a184,left=0cm] ;
(x191) [right from=a191,left=0cm] ;
(i1) at (x1) [above= .65cm,label=right:<span><span class="math inline"><em>y</em><sub>0</sub></span></span>] ;
(i2) at (x2) [above= .65cm,label=right:<span><span class="math inline"><em>y</em><sub>1</sub></span></span>] ;
(i8) at (x8) [above= .65cm,label=right:<span><span class="math inline"><em>y</em><sub>7</sub></span></span>] ;
(i9) at (x9) [above= .65cm,label=right:<span><span class="math inline"><em>y</em><sub>8</sub></span></span>] ;
(i183) at (x183) [above= .65cm,label=right:<span><span class="math inline"><em>y</em><sub>183</sub></span></span>] ;
(i184) at (x184) [above= .65cm,label=right:<span><span class="math inline"><em>y</em><sub>184</sub></span></span>] ;
(i191) at (x191) [above= .65cm,label=right:<span><span class="math inline"><em>y</em><sub>191</sub></span></span>] ;
(s1) [right from=x1] <span><span class="math inline"><em>x</em><sub>0</sub></span></span>;
(s2) [right from=x2] <span><span class="math inline"><em>x</em><sub>1</sub></span></span>;
(s8) [right from=x8] <span><span class="math inline"><em>x</em><sub>7</sub></span></span>;
(s9) [right from=x9] <span><span class="math inline"><em>x</em><sub>8</sub></span></span>;
(ph) [below from=s9] <span><span class="math inline">⋮</span></span>;
(s183) [below from=ph] <span><span class="math inline"><em>x</em><sub>183</sub></span></span>;
(s184) [below from=s183] <span><span class="math inline"><em>x</em><sub>184</sub></span></span>;
(sp) [below from=s184] <span><span class="math inline">⋮</span></span>;
(s191) [below from=sp] <span><span class="math inline"><em>x</em><sub>191</sub></span></span>;</p>
<p>(so1) [right from=s1] ;
(so2) [right from=s2] ;
(so8) [right from=s8] ;
(so9) [right from=s9] ;
(so183) [right from=s183, left=0cm] ;</p>
<p>(cc191) [right from=s191, right=1cm] ;
(cc186) [right from=s184, right=1cm] ;
(cc183) [right from=s183, right=1cm] ;
(cc9) [right from=s9, right=1.15cm] ;
(cc8) [right from=s8, right=1.15cm] ;
(cc2) [right from=s2, right=1.15cm] ;
(cc1) [right from=s1, right=1.15cm] ;</p>
<p>(b1) [right from=cc1] ;
(b2) [right from=cc2] ;
(b3) [below from=b2] <span><span class="math inline">⋮</span></span>;
(b4) [right from=cc8] ;
(b5) [right from=cc9] ;
(b6) [right from=cc183] ;
(b7) [right from=cc186] ;
(b8) [right from=cc191] ;</p>
<p>(n1) [right from=b1, label=right:<span><span class="math inline"><em>y</em><sub>0</sub></span></span>, right=1cm] ;
(n2) [right from=b2, label=right:<span><span class="math inline"><em>y</em><sub>1</sub></span></span>, right=1cm] ;
(n3) [right from=b4, label=right:<span><span class="math inline"><em>y</em><sub>7</sub></span></span>, right=1cm] ;
(n4) [right from=b5] ;
(n4b) [right from=n4, label=right:<span><span class="math inline"><em>y</em><sub>8</sub></span></span>] ;
(n5) [right from=b6] ;
(n5b) [right from=n5, label=right:<span><span class="math inline"><em>y</em><sub>183</sub></span></span>] ;
(n6) [right from=b7] ;
(n6b) [right from=n6, label=right:<span><span class="math inline"><em>y</em><sub>184</sub></span></span>] ;
(n7) [right from=b8] ;
(n7b) [right from=n7, label=right:<span><span class="math inline"><em>y</em><sub>191</sub></span></span>] ;</p>
<p>(ii4) at (n4) [above= .65cm,label=right:<span><span class="math inline"><em>x</em><sub>0</sub></span></span>] ;
(ii5) at (n5) [above= .65cm,label=right:<span><span class="math inline"><em>x</em><sub>175</sub></span></span>] ;
(ii6) at (n6) [above= .65cm,label=right:<span><span class="math inline"><em>x</em><sub>176</sub></span></span>] ;
(ii7) at (n7) [above= .65cm,label=right:<span><span class="math inline"><em>x</em><sub>183</sub></span></span>] ;</p>
<p>(c1)–(c2)–(c3)–(c4)–(c9)–(c182)–(c183)
(c1)–(a1)
(c2)–(a2)
(c3)–(a8)
(c4)–(a9)
(c9)–(a183)
(c183)–(a191)
(c182)–(a184);
(cc191)–(cc183)–(cc9)–(cc8)–(cc2)–(cc1);</p>
<p>(a1)–(x1);
(a2)–(x2);
(a8)–(x8);
(a9)–(x9);
(a183)–(x183);
(a184)–(x184);
(a191)–(x191);</p>
<p>(s1)–(so1);
(s2)–(so2);
(s8)–(so8);
(s9)–(so9);
(s183)–(so183);</p>
<p>(x1)–(s1);
(x2)–(s2);
(x8)–(s8);
(x9)–(s9);
(x183)–(s183);
(x184)–(s184);
(x191)–(s191);</p>
<p>(i1)–(x1);
(i2)–(x2);
(i8)–(x8);
(i9)–(x9);
(i183)–(x183);
(i184)–(x184);
(i191)–(x191);</p>
<p>(ii4)–(n4);
(ii5)–(n5);
(ii6)–(n6);
(ii7)–(n7);</p>
<p>(s184)–(cc186)
(s191)–(cc191);</p>
<p>(b1)–(n1);
(b2)–(n2);
(b4)–(n3);
(b5)–(n4);
(b6)–(n5);
(b7)–(n6);
(b8)–(n7);</p>
<p>(n4)–(n4b);
(n5)–(n5b);
(n6)–(n6b);
(n7)–(n7b);</p>
<p>(cc1)–(b1)
(cc2)–(b2)
(cc8)–(b4)
(cc9)–(b5)
(cc183)–(b6)
(cc186)–(b7)
(cc191)–(b8);</p>
</div>
<figcaption>Architecture oriented to digital hardware implementation. Each combinatorial network on the left-hand side implements a row by column product of <span class="math inline">$\vet B_8 \vet u$</span>. Each row of matrix <span class="math inline">$\vet B_8$</span> is indicated as <span class="math inline">$\vet b_j$</span> with <span class="math inline">0 ≤ <em>j</em> &lt; 192</span>. Each combinatorial network on the right-hand side implements a row by column sub-product in <a href="#eq:prodotto" data-reference-type="eqref" data-reference="eq:prodotto">[eq:prodotto]</a>. The 8 bit bus on the input side carries message bits to be encoded.</figcaption>
</figure>

## Interface and Parity Bits Extraction

The interface between BCH and LDPC encoder can be implemented as illustrated in . The parity bits, once computed (at $`n\ped{bch}`$ clock tick), can be saved (in a single clock cycle) in a shift register architecture, which has been called in 192 (or rather, up to 192) to 8 bit converter. In fact, its task is formatting data in the DVB-S2 format. Furthermore, this kind of architecture allows to write all the parity bits extracted from BCH encoder (in a single clock tick) into LDPC input memory with a degree of parallelism equal to 8[^1].

Further detailing, the converter is composed by 8 shift register blocks with size equal to 24 bits. In a preliminary fase all the parity bits computed by the BCH encoder are stored in these blocks following the labelling indicated in (to succeed in storing these bits, MUXs between each flip flop can be used). Afterward, the converter works as a shift register, thus allowing to download data eight at once, i.e., with a degree of parallelism equal to 8.

To summarize, let us see, in order for each iteration, the operations carried out by this specific interface:

1.  Once the parity bits have been computed, they are stored in another shift register according to the bit-to-bit mapping illustrated in . MUXs between a FF and its neighbor allow to store bits all at once (in parallel) as they are switched on wires carrying results of encoding (these wires may be directly connected to the BCH encoder register).

2.  As MUXs are switched on wires interconnecting FFs each other, all the bits previously stored, shifting along FFs, are carried by some ’strategic’ wires on the 8 bits bus, which conveys parity bits toward the output multiplexer.
    Practically, the register is working as a shift register.

3.  The output multiplexer has two inputs buses connected to: informative bits and redundancy bits. MUX should be driven by a proper control logic on the operating mode basis.

<figure id="fig:Interface">
<img src="Interface.jpg" />
<figcaption>Interface architecture. Parity bits are loaded into the 192 to 8 bits converter.</figcaption>
</figure>

<figure id="fig:Download">
<img src="download.jpg" />
<figcaption>192 to 8 bits converter architecture. Values into each FF represent the index mapping between the BCH encoder register and the interface register, used to extract and format data.</figcaption>
</figure>

## Frequency and Memory Requirements

Taking into account LDPC outer encoder frequency requirements and imposing a data rate equal to $`1 \unit{Gbps}`$, in the worst case, that is, when $`t=8`$ and LDPC code rate is equal to $`9/10`$, we obtain the maximum frequency requirement so as to guarantee this challenging performance:
``` math
\begin{equation}
(f\ped{clk})\ped{MAX}= \frac{frame}{s}\cdot 7290 = 125 \unit{MHz}
\end{equation}
```
Concerning to memory requirement either, the architecture proposed takes six (two per each level of BCH protection parameter $`t`$) LUTs to store coefficients used by the combinatorial networks. As a matter of fact, storing of the $`\vet C_1`$ and $`\vet C_2`$ sub-matrices (recall that they represent two sub-blocks, whose aggregated size is $`192 \times 8`$, of the $`\vet A^8`$ matrix) coefficients as well matrix $`\vet B_8`$, whose size is $`192 \times 8`$, coefficients is required. To provide an encoder capable of dealing with each $`t`$-error protection level, those matrices have to be saved in LUTs for each $`t`$.
The size of each LUT is equal to $`192 \unit{Bytes}`$ and thus the BCH encoder, apart from additional memory required by the BCH-LDPC interface and the encoder state register, requires an amount of memory equal to
``` math
\begin{equation}
 2\cdot3\cdot192\unit{B} = 1,125\unit{KiB}.
\end{equation}
```

[^1]: Note also that $`p=8`$ is not only a divisor for 360, but also for 192($`t=12`$), 160($`t=10`$) and 128($`t=8`$)

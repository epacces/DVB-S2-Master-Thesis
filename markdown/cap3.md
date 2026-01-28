# BCH Encoding Algorithms for DVB-S2 Digital Transmissions

## Encoding Algorithm Description

As introduced in Section , the systematic encoding of a message
``` math
\begin{equation}
 \vet m = (m_{k\ped{BCH}-1} \virgola m_{k\ped{BCH}-2} \virgola \ldots  \virgola m_{1} \virgola m_{0})
\end{equation}
```
here expressed in vectorial form, provides a codeword
``` math
\begin{equation}
\vet c = (m_{k\ped{BCH}-1} \virgola m_{k\ped{BCH}-2} \virgola \ldots  \virgola m_{1} \virgola m_{0} \virgola d_{n\ped{BCH}-k\ped{BCH}-1} \virgola \ldots \virgola d_0)
\end{equation}
```
<span id="eq:codsyst" label="eq:codsyst"></span>
composed of $`r=n\ped{BCH}-k\ped{BCH}`$ redundancy bits, aimed at protecting information messages, in the least significant positions. Codewords in systematic form have in the most significant positions the exact replica of information bits.

According to the cyclic code theory (see Appendix B), the systematic encoding of messages can be carried out through these three steps:

1.  Multiplication of the message polynomial $`m(x)`$ by $`x^r`$. It can be easily realized through a left shift of the information bits by $`r`$ positions and a zero padding of the least significant $`r`$ bits.

2.  Division of this vector by the polynomial generator. Coefficients of the remainder, expressed in polynomial form
    ``` math
    \begin{equation}
        d(x) = d_{r-1}x^{r-1} +  d_{r-2}x^{r-2} + \ldots+ d_1 x^1 + d_0 \label{eq:remainder}
    \end{equation}
    ```
    represent the $`r`$ parity bits.

3.  Finally, as also stated in ,
    ``` math
    \begin{equation}
     \label{eq:systematic}
     x^{r}m(x)-d(x)
    \end{equation}
    ```
    provides a codeword. Furthermore, since we are in $`GF(2)`$ and thus $`-d(x) = d(x)`$, the expression <a href="#eq:systematic" data-reference-type="eqref" data-reference="eq:systematic">[eq:systematic]</a> can be rewritten as
    ``` math
    \begin{equation}
     x^{r}m(x)+d(x) \label{eq:sistematica}
    \end{equation}
    ```

A signal flow diagram of a possible polynomial division implementer is given in . This kind of architecture is usually called Linear Feedback Shift Register because of the feedback wire connecting the last stage with the first stage of the register. We shall show that the LSFR can succeed in computing the remainder (or parity) bits. This linear system provides instant-by-instant quotient and remainder bits together.

It is possible to demonstrate that this LFRS yields at each sampling instant the temporary remainder bits, which in turns have to be updated at the next time instant. Let us give an intuitive proof of this only focusing on the remainder bits (state) evolution of LFSR. Hereafter we will work only with polynomial coefficients in GF(2), even if generalizations in other base fields[^1] are straightforward (e.g. see ) .

The binary digits in register, after a certain number of computation cycles required (by now it does not matter how many cycles are required), represent the remainder of division. It is useful to observe that taking the remainder after division by $`g(z)=z^4+z^2+1`$ is as imposing $`z^4=z^2+1`$[^2].
This operation is performed by the feedback and taps (i.e. those represented as $`g_1\virgola g_{r-1}`$ in ) of the LFSR.

Since degree of $`g(z)`$ is 4, the shift register length must be 4 (the remainder of division is a polynomial of degree $`r=3`$, which thus have 4 coefficients) as well as the second taps (i.e. $`g_2`$) must be enabled. If the message, from MSB to LSB, $`m(z)=z^8+z^4`$ enters the first sum (modulo 2) node, we have a delay line between entering bit and bit in $`x_3`$ equals to 4. This means that by the feedback wire and taps enabling/disabling all the polynomial coefficients are relatively summed with those of the same degree. When, for example, a $`z^8`$ generates the partial result $`r(z)=(1+z^2)`$ corresponding to $`z^4(1+z^2)`$ at the fifth time instant, the entering coefficient is relevant to degree 4 and then must be summed with the one carried by the feedback wire in order to update $`x_0`$.

Using the equivalent polynomial notation, let us describe the temporal sequence of all the operations performed.

1.  All the register flip flops are set to 0. Coefficient of $`z^8`$ enter $`x_0`$, so determining $`\vet x =  (1\virgola0\virgola1\virgola0)`$. We can represent the polynomial division together with digits in the flip flops by the following expression
    ``` math
    (r_{1}(z)=1+0\cdot z^1+0\cdot z^2+0\cdot z^3)\cdot z^8
    ```
    where $`r_{i}(z)`$ represent the partial remainder at $`i`$-th iteration.

2.  
    ``` math
    (r_{2}(z)=0+1\cdot z^1+0\cdot z^2+0\cdot z^3)\cdot z^7 + (m_2(z) = 0\cdot z^7)
    ```

3.  
    ``` math
    (r_{3}(z)=0+0\cdot z^1+1\cdot z^2+0\cdot z^3)\cdot z^6 + (m_3(z) = 0\cdot z^6)
    ```

4.  
    ``` math
    (r_{4}(z)=0+0\cdot z^1+0\cdot z^2+1\cdot z^3)\cdot z^5 + (m_4(z) = 0\cdot z^5)
    ```

5.  Here we have $`(r_{5}(z)=1+0\cdot z^1+1\cdot z^2+0\cdot z^3)\cdot z^4 + (m_5(z) = 1\cdot z^4)`$ and then
    ``` math
    (r_{5}(z)=0+0\cdot z^1+1\cdot z^2+0\cdot z^3)\cdot z^4
    ```

6.  
    ``` math
    (r_{6}(z)=0+0\cdot z^1+0\cdot z^2+1\cdot z^3)\cdot z^3 + (m_6(z) = 0\cdot z^3)
    ```

7.  
    ``` math
    (r_{7}(z)=1+0\cdot z^1+1\cdot z^2+0\cdot z^3)\cdot z^2+ (m_7(z) = 0\cdot z^2)
    ```

8.  
    ``` math
    (r_{8}(z)=0+1\cdot z^1+0\cdot z^2+1\cdot z^3)\cdot z^1+ (m_8(z) = 0\cdot z^1)
    ```

9.  
    ``` math
    (r_{9}(z)=1+0\cdot z^1+0\cdot z^2+0\cdot z^3)\cdot z^0+ (m_9(z) = 0\cdot z^0)
    ```
    $`r(z)=r_9(z)`$ corresponding to $`\vet x=(1\virgola0\virgola0\virgola0)`$ is also the result of division by $`g(z)`$.

The key observation to be made in order to understand the encoding process is interpreting each delay tier as the degree of a polynomial (like $`z`$-transform).

For the architecture in , analogous observations upon delay tier between input and output can be made. Here the entering coefficients are summed with the maximum degree coefficients of the partial remainder $`r_{i}(z)`$ at each clock cycle, and thus the delay tier is exactly 0. If the result of this sum is 1 then the feedback is enabled, else it does not. As we shall show in the next section, the choice of feeding the shift register by the right-hand side allows us to achieve better performance.

## Serial Architectures

A problem not yet dealt with is how (and when) the parity bits, once computed, can be extracted from the register. As shown in the previous section, LFSR in gives the parity bits as all the bits of message-zero-padded, $`m(x)x^r`$, enter the fist sum (modulo 2) node. Therefore, provided that the remainder after division can be fetched and stored in a single clock tick, this LFSR takes $`n\ped{BCH}`$ clock cycles to yield the wanted result.

It is interesting to notice that only at a certain discrete time instant (they furthermore fall periodically) the registers of LFSR contain redundancy bits representing the remainder after division. This drawback prevents this type of architecture from working serially because results of division algorithm have to be properly fetched and stored in any other register when the parity bits are ready.

As just noticed, architecture in is slightly unsuitable for a serial systematic encoder since results of divisions (redundancy bits) have to be read in parallel at every $`(j+1) n\ped{BCH}`$ instant for $`j= 0 \virgola 1 \virgola 2 \ldots`$. This can be technically performed, but however the architecture would not be serial anymore. Nevertheless, these facts will become quite interesting in parallelization of the architecture.

On the other hand, a mere serial hardware architecture is illustrated in Figure <a href="#fig:SerEnc" data-reference-type="ref" data-reference="fig:SerEnc">1.2</a>. Differently from above, here the encoder is fed by the opposite side, thus immediately enabling the feedback, allowing the structure so devised to yield the remainder at every $`(j+1) k\ped{BCH}`$ instead of $`(j+1) n\ped{BCH}`$ for $`j= 0 \virgola 1 \virgola 2 \ldots`$. This permits to read serially parity bits and, besides, set (each register is reset) the device so as to make it ready to encode properly next incoming bit streams.
Serial encoding in systematic form is accomplished (see ) by:

 Systematic Bits Transmission and Parity Computation  
For clock cycles 1 to $`k\ped{BCH}`$, the information bits are transmitted in the natural order (switch S2 in position 2), while also feeding the shift register, to allow parity bits to be calculated in the Linear Feedback Shift Register (LFSR) (to that purpose, switch S1 must be on, activating the feedback mode).

Parity Bits Transmission  
For clock cycles $`k\ped{BCH}+1`$ to $`n\ped{BCH}`$, the parity bits in the LFSR are transmitted (switch S2 in position 1) and the LFSR feedback mode is switched off (by setting S1 off).

From the above timing consideration, it follows that the latter architecture, spending $`k\ped{BCH}`$ clock cycles against $`n\ped{BCH}`$, performs more efficiently encoding in case of parallel fetching of the parity bits, as we shall see later on.

<figure id="fig:PolyDiv">
<div class="signalflow">
<p>(in)–(a1);
(c1)–(a1);
(a1)–(b1);
(br)–(cr);
(cr)–(c4);
(c4)–(n3);
(n3)–(mn);
(n3)–(c3);
(c3)–(c2);
(n2)–(n1);
(n1)–(c1);
(b3)–(c5);
(c5)–(c6);
(c6)–(a4);
(a4)–(br);
(mn)–(a4);
(c2)–(n2);
(n2)–(m2);
(n1)–(m1);
(m1)–(a2);
(m2)–(a3);
(b1)–(a2);
(a2)–(b2);
(b2)–(a3);
(a3)–(b3);</p>
</div>
<figcaption>Linear Feedback Shift Register architecture implementing the polynomial division in <span class="math inline">$n\ped{BCH}$</span> clock cycles</figcaption>
</figure>

<figure id="fig:SerEnc">
<img src="serenc.jpg" />
<figcaption>Serial encoder architecture based on LFSR (systematic encoding): it implements the systematic encoding of any codeword in <span class="math inline">$n\ped{bch}$</span> clock ticks. At the end of each message encoding, encoder does not require a reset of the state register and thus is ready to immediately encode a new incoming message.</figcaption>
</figure>

## Encoding Algorithms for Parallel Architectures

### Modelling System

From the theory of control we know that any linear system, fed by an input signal $`\vet u(i)`$ can be described by the following system of linear equation
``` math
\label{eq:LinSys}
\begin{align}
\vet y(i) & = \vet {Cx}(i) + \vet{Du}(i) \label{subeq:GeneralOutput} \\
\vet x(i+1) &= \vet {Ax}(i) + \vet{Bu}(i) \label{subeq:GeneralState}
\end{align}
```
where <a href="#subeq:GeneralOutput" data-reference-type="eqref" data-reference="subeq:GeneralOutput">[subeq:GeneralOutput]</a> expresses its outcomes $`\vet y(i)`$ at each sampling (discrete) instant, while <a href="#subeq:GeneralState" data-reference-type="eqref" data-reference="subeq:GeneralState">[subeq:GeneralState]</a> describes its trajectory of state $`\vet x(i)`$, i.e., the state evolution of the linear system in question. Without descending in further details, we shall particularize both equations for the linear feedback shift register shown in and, starting from them, find equations relevant to an architecture with a $`p`$ degree of parallelism. We shall notice that they will perfectly match with system <a href="#eq:LinSys" data-reference-type="eqref" data-reference="eq:LinSys">[eq:LinSys]</a>.

The Linear Feedback Shift Register (LFSR) depicted in is a linear system, and thus can be described by the well known output equation expressing $`y(i)`$, the scalar output, and the state transition equation expressing the vector state $`\vet x(i)`$ as a function of the discrete time $`i`$
``` math
\label{eq:LFSR}
\begin{align}
 y(i) & = \vet {cx}(i) + d\cdot u(i) \\
\vet x(i+1) &= \vet {Ax}(i) + \vet{b}u(i) \label{eq:statequation}
\end{align}
```

In particular, for the desired parallel BCH encoding procedure, we are only interested in the (state) vector
``` math
\begin{equation}
\vet x(i) =
\left(
\begin{array}{ccccc}
  x_0(i)   & x_1(i) & \ldots  & \ldots & x_{r-1}(i) \\
\end{array}
\right)\ap T
\end{equation}
```
and in its temporal evolution/transition because $`\vet x(i)`$ represents the parity bits after the required number of computation cycles. Thus, hereafter we shall focus only on <a href="#eq:statequation" data-reference-type="eqref" data-reference="eq:statequation">[eq:statequation]</a>. The scalar $`u(i)`$ indicates the input at the sampling instant $`i`$, as put in evidence in and . The matrix $`\vet A`$ models the state evolution of the system in absence of external stimulus (i.e., $`u(i)=0`$), and thus is usually called the state transition matrix. For analogous reasons, the column vector $`\vet b`$ is called as the input-to-state transfer relationship.

The form of $`\vet A \virgola \vet b`$ depends uniquely on the position of taps and connections in the LFSR. In other words, that form is strongly dependent on the selected architecture implementing the encoding algorithm. More precisely, the matrix $`\vet A`$ depends on the taps collocations of LSFR, whereas vector $`\vet b`$ depends on where the input/s is/are connected to the system.

Now, referring to the LFSR architecture depicted in , which can yield the redundancy bits after $`n\ped{BCH}`$ clock cycles, we can write, on the one hand,
``` math
\begin{align}
\vet A & = \left (
\begin{array} {ccccc}
0      &  0     & \ldots &  0     & g_0\\
1      &  0     & \ldots & 0      & g_1\\
\vdots &  1     & \ldots &   0    & g_2\\
       & \vdots & \ldots & \vdots & \vdots\\
0      & 0      & \ldots & 1      & g_{r-1} \\
\end{array} \right ) &
\vet b & = \left(
\begin{array}{c}
  1 \\
  0 \\
   \vdots \\
    \vdots \\
    0\\
\end{array} \right) \label{eq:ParSyst}
\end{align}
```
where $`\vet A`$, $`r`$ by $`r`$ state transition square matrix, contains in the last column the polynomial generator coefficient except for its coefficient of maximum degree. On the other hand, column vector $`\vet b`$ of length $`r`$ gives a mathematical representation of the physical input-to-system connections.

As introduced in Section <a href="#sec:SArch" data-reference-type="ref" data-reference="sec:SArch">1.2</a>, the adoption of the architecture in permits to save some clock ticks. Not surprisingly, only $`\vet b`$ has changed its form whereas the representation of matrix $`\vet A`$ given in <a href="#eq:ParSyst" data-reference-type="eqref" data-reference="eq:ParSyst">[eq:ParSyst]</a> still holds. Since inputs enter now from the right-hand side, we have the new column vector
``` math
\begin{equation}
\label{eq:vetb}
\vet b =
\left(
\begin{array}{c}
  g_0 \\
  g_1 \\
   \vdots \\
    \vdots \\
    g_{r-1}\\
\end{array}
\right)
\end{equation}
```
which models – as before – the input incidence on the system state.

### Parallel Linear System Description

In the previous section we have briefly described a possible model of system
which can be easily exploited in parallelizing a general serial architecture
with a degree of parallelism $`p`$. Starting from <a href="#eq:statequation" data-reference-type="eqref" data-reference="eq:statequation">[eq:statequation]</a> and
applying instant-by-instant and recursively the following substitutions
``` math
\begin{align*}
\vet x(i) &= \vet {Ax}(i-1) + \vet{b}u(i-1)\\
\vet x(i-1) &= \vet {Ax}(i-2) + \vet{b}u(i-2)\\
\vdots \\
\vet x(i-p+1) &= \vet {Ax}(i-p) + \vet{b}u(i-p)\\
\vet x(i) &= \vet {A} \left[ \vet{Ax}(i-2) + \vet{b}u(i-2)\right] + \vet{b}u(i)\\
&= \vet A^2 \vet x (i-2) + \vet{Ab} u(i-2) + \vet{b} u(k-1)
\end{align*}
```
we can observe that the evolution of this system at a generic sampling instant $`i`$ depends on

- the state vector relevant to a generic former instant;

- a set of former inputs whose cardinality is equal to the difference among the current time index and the former instant selected.

This is equivalent, from an architectural implementation point of view, in feeding the encoding processor by a set of parallel inputs, associating to each of the multiple input wires a different (multiple) time instant. Hence, parallelization is straightforwardly achieved.

Returning to the above expression, the system evolution for a generic degree of parallelism $`p`$ is modelled by the following state equation
``` math
\begin{equation}
\label{eq:pseq}
\vet x(i) = \vet A^p(i-p) + \sum_{k=0}^{p-1}{\vet A^k \vet b u(i-k-1)}
\end{equation}
```
Now, setting the column vectors $`\vet A^k \vet b`$ as follows
``` math
\begin{equation}
\label{eq:Bmatrix}
\left(
\begin{array}{ccccc}
  \vet b & \vet{Ab} & \ldots & \vet A^{p-2} \vet b &  \vet A^{p-1} \vet b
\end{array}
\right)
\end{equation}
```
we can define a new $`r`$ by $`p`$ $`\vet B_p`$ matrix which represent the incidence of the last $`p`$ inputs
``` math
\begin{equation}
\label{eq:newu}
\vet u(ip) =
\left(
\begin{array}{ccccc}
  u(ip-1)   & u(ip-2) & \ldots  & \ldots & u \left[ p(i-1))\right] \\
\end{array}
\right)\ap T
\end{equation}
```
on the system evolution. Considering both <a href="#eq:Bmatrix" data-reference-type="eqref" data-reference="eq:Bmatrix">[eq:Bmatrix]</a> and <a href="#eq:newu" data-reference-type="eqref" data-reference="eq:newu">[eq:newu]</a>, we can therefore rewrite the state equation <a href="#eq:pseq" data-reference-type="eqref" data-reference="eq:pseq">[eq:pseq]</a> as
``` math
\begin{equation}
 \label{eq:SEmatr}
\vet x (ip) = \vet A^p \vet x \left[ (i-1)p \right] + \vet B_p \vet u(ip)
\end{equation}
```
where the sum $`\sum_{k=0}^{p-1}{\vet A^k \vet b u(i-k-1)}`$ has just been replaced by the above matrices product.

### Matrices Structure and Properties

In every practical case, the wanted degree of parallelism is strictly less than the number of registers containing the remainder bits at the end of every bit stream processing. For this reason, in this section we shall describe the main characteristics of matrices $`\vet A^p`$ and $`\vet B_p`$ only within the range $`0 < p \le r`$ of our interest.

Therefore for a generic degree $`p`$ (within the above specified range) we have
``` math
\begin{equation}
 \label{eq:Apreg}
\vet A^p =
\left(
\begin{array}{cc}
\vet 0 & \vet C_1 \\
\vet I & \vet C_2
\end{array}
\right)
\end{equation}
```
where

- $`\vet 0`$ represents a null $`p \times p`$ matrix;

- $`\vet I`$ represent a square $`r-p`$ by $`r-p`$ identity matrix;

- $`\vet C_1`$ is a $`p \times p`$ matrix where each row represents the combinatorial connections (1 when it is active, 0 otherwise) between last and first $`p`$ bits of vector $`\vet x(i)`$;

- $`\vet C_2`$ is a $`(r-p) \times p`$ matrix where each row represents the combinatorial connections between last $`p`$ bits and the remaining bits of the vector $`\vet x(i)`$

Differently from $`\vet A^p`$ matrix, $`\vet B_p`$ as well as $`\vet b`$ (as just said in ) is strictly dependent on where inputs are. Referencing to the LFSR architecture depicted in , we have therefore
``` math
\begin{equation}
 \label{eq:Btrivial}
\vet B_p =
\left(
\begin{array}{c}
\vet I \\
\vet 0
\end{array}
\right)
\end{equation}
```
in case on which the feedback starts at least (depends on the position of the first one in the message) after $`\frac{r}{p}`$ clock ticks (supposing that $`p`$ is a divisor of $`r`$). Identity matrix has size $`p\times p`$. For example, for a with a degree of parallelism $`p=5`$
[^3]
we get

``` math
\begin{align}
 \label{eq:triex}
\vet A^5 & =
\left( \begin{array}{cccccccc}
 0 &  0 &  0 &  1 &  1 &  0 &  1 & 0 \\
 0 &  0 &  0 &  0 &  1 &  1 &  0 & 1 \\
 0 &  0 &  0 &  0 &  0 &  1 &  1 & 0 \\
 0 &  0 &  0 &  0 &  0 &  0 &  1 & 1 \\
 0 &  0 &  0 &  1 &  1 &  0 &  1 & 1 \\
 1 &  0 &  0 &  0 &  1 &  1 &  0 & 1 \\
 0 &  1 &  0 &  1 &  1 &  1 &  0 & 0 \\
 0 &  0 &  1 &  1 &  0 &  1 &  0 & 0 \\
\end{array}\right) &
\vet B_5 & = \left(
\begin{array}{ccccc}
 1 &  0 &  0 &  0 & 0 \\
 0 &  1 &  0 &  0 & 0 \\
 0 &  0 &  1 &  0 & 0 \\
 0 &  0 &  0 &  1 & 0 \\
 0 &  0 &  0 &  0 & 1 \\
 0 &  0 &  0 &  0 & 0 \\
 0 &  0 &  0 &  0 & 0 \\
 0 &  0 &  0 &  0 & 0 \\
\end{array}
\right)
\end{align}
```

As just shown, the structure of above matrix $`\vet B_5`$ is quite trivial. This result is a direct consequence of the way by which we have defined $`\vet B_p`$ in <a href="#eq:Bmatrix" data-reference-type="eqref" data-reference="eq:Bmatrix">[eq:Bmatrix]</a>. Because of simple nature of vector $`\vet b`$ (which has only a one on the first row), the products between it and increasing powers of $`\vet A`$ can be obtained by selecting the first column of the first $`p`$ powers $`\vet A^0= \vet I \virgola \vet A^1 \virgola \vet A^2 \virgola \ldots \vet A^{p-1}`$ of state matrix. In other words, $`\vet B_p`$ can be conveniently expressed as
``` math
\begin{equation}
\label{eq:Bp2}
\left[
\begin{array}{ccccc}
  \vet I(1:,1) & \vet A(1:,1) & \ldots & {\vet A}^{p-2}(1:,1) &  \vet A^{p-1}(1:,1)
\end{array}
\right]
\end{equation}
```
where a notation as $`\vet X(1: \virgola j)`$ indicates the $`j`$-th column of any matrix. In our case we have then to select each first column of matrices in <a href="#eq:Bp2" data-reference-type="eqref" data-reference="eq:Bp2">[eq:Bp2]</a>.

The matrix $`\vet B_p`$ in <a href="#eq:triex" data-reference-type="eqref" data-reference="eq:triex">[eq:triex]</a> becomes non-structured as the shift register are fed on the opposite side relatively to first and less efficient architecture shown previously (). In fact, taking into account the new definition <a href="#eq:vetb" data-reference-type="eqref" data-reference="eq:vetb">[eq:vetb]</a> of column vector $`\vet b`$ relevant to the positions of inputs into the system, we get a new $`\vet B_p`$ matrix which, differently from the previous, does not show any property of regularity. In other words, this new matrix has no longer the trivial form shown in <a href="#eq:triex" data-reference-type="eqref" data-reference="eq:triex">[eq:triex]</a>.

## Some Considerations

From an hardware point of view, following considerations can be made:

1.  since codeword length compliant with DVB-S2 standard is long (either short or long FECFRAME), a serial encoder (e.g., that depicted in ) may be rather inefficient and slow;

2.  parallel architectures are more flexible solutions when different $`t`$-error correction BCH codes are needed. Since the standard provides different $`t`$ (for BCH) that can be switched on a frame basis, encoder is required to be versatile;

3.  the overall architecture (inner LDPC encoder in parallel implementation) has to be taken into account and a parallel encoder make the interface design simpler.

On the contrary, serial architectures, being based on an elementary LSFR sub-structure, are rather simpler than their parallel version. But, for the reasons enumerated above, they have not been taken in consideration to design the encoding section of DVB-S2.

[^1]: Very synthetically, multiplier and adder in LFSR shown in have to implement these operation in Galois arithmetic.

[^2]: Over the real field, for example, taking the remainder after division by 4 of any number is as imposing $`4=0`$ so that $`13 \textrm{mod} 4 = 1`$ because 13 can be thought as $`4\times3+1`$ and, given that $`4=0`$, then the remainder is 1.

[^3]: The degree of parallelism must be a divisor of numbers of clock ticks to encode a codeword. This architecture spends a number of ticks equal to 15 (codeword length) and therefore $`p`$ can be 5.

# <a id="chapter-A"></a>A Galois (or Finite) Fields

In this appendix we introduce some basic coding concepts related to error correction coding with a particular focus on mathematical tools that come in useful in DVB-S2 FEC encoding. Obviously, we do not provide a complete treatment of such a rigorous and abstract mathematical theory. First, because it is not so worthwhile for our purposes; second, because there are several books written on Coding Theory, where everything that could be necessary is exhaustively and rigorously explained. Therefore, for any further information on the topics presented next, the reader can refer, for example, to (Moon 2005) or (F. J. MacWilliams, N. J. Sloane 1977).

In engineering applications it is often necessary to find a reasonable trade-off between system complexity and the performance achieved. On the one hand, an elementary decoding approach is simpler, but, on the other hand, its computational burden increases exponentially with the code length. Algebraic decoding represents a valid alternative to overcome such a huge growth in complexity.

The key idea concerning algebraic coding is that of giving codes some algebraic structure to be exploited for decoding purposes. When the block length becomes rather large, decoding turns out to be somewhat intractable. For example, the hard decision on the minimum distance between any received sequence and codewords requires a computational effort and a large amount of memory, both increasing with the code length. Another approach is the *standard array decoding*. Unfortunately, this also turns out to be too expensive when the block dimensions become large. In particular, its memory requirements make this approach rather unattractive.

Algebraic coding/decoding is largely based on powerful and elegant algebraic structures called finite fields. A field is essentially a set of elements where addition, subtraction, multiplication and division operations always yield an element within such a set. A well known example of a field is $`\mathbb R`$, the infinite field of real numbers. Although the following observation could be rather trivial, the need for such an algebraic structure is straightforward. Finite fields act like the most common real fields. The only difference is that the size of the set is finite as, for example, an ensemble of codewords. Note, for example, that no codeword could be decoded by the Berlekamp-Massey algorithm or the Galois Field Transform if the inverse property were not satisfied.

Although the preliminary concepts on axioms and elementary algebraic structures which lead to rigorous mathematical definition of field properties are also important, the real core of this appendix is the part concerning the factorization of a ‘special polynomial’. This operation provides, together with some elementary knowledge of Coding Theory, a powerful tool to design and fully understand algebraic encoding and decoding algorithms.

## <a id="section-A.1"></a><a id="sec:algebraicstruct"></a>A.1 Algebraic Structures: a Glance

Before discussing properties of finite fields, let us define some preliminary algebraic structures. Let us start from the definition of groups. On these sets it is possible to define some (binary) operations between their elements. To be called a group, operations over such a set must satisfy the following algebraic properties.

<div class="Def">

<a id="definition-A.1.1"></a>

**Definition A.1.1**. *A binary operation $`\ast`$ on a set assigns to each ordered pair of elements of the set $`(a,b)`$ some element of the set. (This is defined as *closed* binary operation.)*

</div>

<div class="Def">

<a id="definition-A.1.2"></a>

**Definition A.1.2**. *A *group* is a set $`\langle G ,+ \rangle`$ together with a binary operation $`\ast`$ on $`G`$ such that:*

*The operator is *associative*: for any $`a ,b ,c \in G ,(a \ast b)\ast c= a \ast (b \ast c).`$*

*There is an element $`e \in G`$ called the *identity element* such that $`a\ast e = e \ast a`$ for all $`a \in G`$.*

*For every $`a \in G`$, there is an element $`b \in G`$ known as the *inverse* of $`a`$ such that $`a \ast b = e`$. The inverse of $`a`$ is sometimes denoted as $`a^{-1}`$ (when the operator $`\ast`$ is multiplication-like) or as $`-a`$ (when the operator $`\ast`$ is addition-like).*

*If also $`a \ast b`$ is equal to $`b \ast a`$, the group is also an abelian (or commutative) group.*

</div>

If the commutative property holds then a group is said to be abelian. It is possible to define an algebraic structure as a group also on a finite set of elements, as well as on an infinite one.

<div class="Def">

<a id="definition-A.1.3"></a>

**Definition A.1.3**. *If $`G`$ has a finite number of elements, it is said to be a finite group. Furthermore, such number is called the order (or the cardinality) of the group.*

</div>

Let $`\langle \mathbb Z_n ,+ \rangle`$ denote addition on the numbers $`\{0 ,1 ,\ldots ,n-1 \}`$ modulo $`n`$. Clearly such set is an abelian group, since, as it is shown in the explanatory Table [A.2](#tb:Ringmod6) (which can be easily generalized) 0 is the identity element appearing in each column; moreover, the uniqueness of solution proves the associative property; furthermore, the addition table or its generalization is symmetric and thus the operation is commutative.

Let us now introduce another algebraic structure, the *ring*, which will be later helpful in the examination of cyclic codes. Unlike groups, *rings* have two binary operations associated with them.

<div class="Def">

<a id="definition-A.1.4"></a>

**Definition A.1.4**. *A *ring* (loosely speaking) is a set where addition, subtraction and multiplication are possible. Formally, $`R`$ is an additive abelian group, together with a multiplication satisfying $`ab=ba`$, $`a(b+c)=ab+ac`$, $`(ab)c = a(bc)`$, and which contains an identity element 1 such that $`1\cdot a=a`$.*

</div>

As also shown in Table [A.2](#tb:Ringmod6), the multiplication under $`\mathbb Z_{n}`$ does not form a group: there are zeros in the columns corresponding to the nonzero elements (see the next section for the *zero divisor* formal definition). In fact, in a ring, not every element has a multiplicative inverse, whereas, in a *field*, the familiar arithmetic operations that take place on the usual real numbers are all available.

<div class="Def">

<a id="definition-A.1.5"></a>

**Definition A.1.5**. *A *field* is a set of objects $`\mathbb F`$ on which the operations of addition, multiplication, subtraction (or additive inverse), and division (or multiplicative inverse) apply in a manner analogous to the way these operations work for real numbers. That is*

*The elements of $`\mathbb F`$ form an abelian (or commutative) *group* under addition.*

*The non-zero elements of $`\mathbb F`$ form an abelian *group* under multiplication.*

</div>

<div>

<a id="table-A.1"></a><a id="tb:Rmod5"></a>

***Table A.1:** Addition table under $`\mathbb Z_5`$*

| \+  |  0  |  1  |  2  |  3  |  4  |
|:---:|:---:|:---:|:---:|:---:|:---:|
|  0  |  0  |  1  |  2  |  3  |  4  |
|  1  |  1  |  2  |  3  |  4  |  0  |
|  2  |  2  |  3  |  4  |  0  |  1  |
|  3  |  3  |  4  |  0  |  1  |  2  |
|  4  |  4  |  0  |  1  |  2  |  3  |

</div>

<div>

<a id="table-A.2"></a><a id="tb:Ringmod6"></a>

***Table A.2:** Multiplication table under $`\mathbb Z_6`$*

| $`\cdot`$ |  0  |  1  |  2  |  3  |  4  |  5  |
|:---------:|:---:|:---:|:---:|:---:|:---:|:---:|
|     0     |  0  |  0  |  0  |  0  |  0  |  0  |
|     1     |  0  |  1  |  2  |  3  |  4  |  5  |
|     2     |  0  |  2  |  4  |  0  |  2  |  4  |
|     3     |  0  |  3  |  0  |  3  |  0  |  3  |
|     4     |  0  |  4  |  2  |  0  |  4  |  2  |
|     5     |  0  |  5  |  4  |  3  |  2  |  1  |

</div>

## <a id="section-A.2"></a><a id="sec:GF"></a>A.2 How Do We Get Galois Fields?

Let us now try to find a relationship between groups and fields. More specifically, starting from the rings with addition and multiplication operations modulo $`n`$, we wish to comprehend how to obtain a finite field and under which hypotheses. To this purpose, it could be interesting to note that, in some cases, each nonzero element of a ring has a multiplicative inverse and so is a field, while, in other ones, there exist some elements without a multiplicative inverse. We could start to observe that when the ring characteristic is a prime number (such as five, see Table [A.3](#tb:Fieldmod5)), we have a ring with elements forming an abelian group under multiplication. The reasons will be made clearer after the following definition of the elements called zero divisors.

<div class="Def">

<a id="definition-A.2.1"></a>

**Definition A.2.1**. *In a ring $`R`$, if $`a ,b \in R`$ with both $`a`$ and $`b`$ not equal to zero but $`ab = 0`$, then $`a`$ and $`b`$ are said to be *zero divisors*.*

</div>

In practice, the presence of zero divisors make it impossible for a ring to have a multiplicative inverse for each of its elements and, above all, to have a multiplicative structure closed under multiplication. Therefore, if we have no zero divisors then a finite ring is also a Galois (or finite) field. The following theorem defines under which hypotheses no such elements exist.

<div class="Theorem">

<a id="theorem-A.2.1"></a><a id="th:subgf"></a>

**Theorem A.2.1** (Todd K. Moon, (Moon 2005)). *The ring $`\mathbb Z_p`$ is a field if and only if p is a prime.*

</div>

Without making any mathematical calculations, we can observe (as proof) that if $`p`$ is a prime its multiples over $`\mathbb Z_p`$ cannot exist and, therefore, neither zero divisors.

Besides the finite fields with $`p`$ prime, there are other finite fields. As the field of complex numbers $`\mathbb C`$ can be constructed as a field extension of the field of real numbers $`\mathbb R`$, these Galois fields are *extension fields* of $`\mathbb Z_p`$. More in detail, extension fields are constructed to create roots of irreducible polynomials that do not have roots in the base field. E.g., the polynomial $`f(x) = x^2+1`$ is irreducible over $`\mathbb R`$, but not over $`\mathbb C`$ where we can write: <a id="eq-A.1"></a>
``` math
\begin{equation}
f(x)=(x+\alpha)(x-\alpha)=(x+\mathrm{j})(x-\mathrm{j})
 \tag{A.1}
\end{equation}
```
Practically we obtain an extension field from a base field whenever we can find an irreducible polynomial over the base field. Loosely speaking, these polynomials may be conceived as prime numbers by which (as noticed previously) it is possible to construct any field.

<div>

<a id="table-A.3"></a><a id="tb:Fieldmod5"></a>

***Table A.3:** Multiplication table under $`\mathbb Z_5`$*

| $`\cdot`$ |  0  |  1  |  2  |  3  |  4  |
|:---------:|:---:|:---:|:---:|:---:|:---:|
|     0     |  0  |  0  |  0  |  0  |  0  |
|     1     |  0  |  1  |  2  |  3  |  4  |
|     2     |  0  |  2  |  4  |  1  |  3  |
|     3     |  0  |  3  |  1  |  4  |  2  |
|     4     |  0  |  4  |  3  |  2  |  1  |

</div>

## <a id="section-A.3"></a><a id="sec:MathSurvey"></a>A.3 A Mathematical Survey

Having shown how to obtain Galois fields, we now lay out some aspects of the theory. We first focus on the additive structure of finite fields, which tells us what size any finite field can be. Recalling Theorem [A.2.1](#th:subgf), it follows that there are $`p`$ elements which behave like a field (i.e., we can define addition and multiplication on them as a field). Thus, $`\mathbb Z_p`$ is a subfield of every Galois field $`GF(q)`$. In fact, an assertion can be made:

<div class="Theorem">

<a id="theorem-A.3.1"></a>

**Theorem A.3.1** (Todd K. Moon, (Moon 2005)). *The order $`q`$ of every finite field $`GF(q)`$ must be a power of a prime.*

</div>

By Theorem [A.2.1](#th:subgf), every finite field $`GF(q)`$ has a subfield of prime order $`p`$. In fact, it can be shown that $`GF(q)`$ acts like a vector space over its subfield $`GF(p)`$. More specifically, if we take <a id="eq-A.2"></a>
``` math
\begin{equation}
a_1\beta_1 + a_2\beta_2 + \ldots + a_m\beta_m
 \tag{A.2}
\end{equation}
```
with coefficients $`a_i`$ lying in $`GF(p)`$ and $`\beta_i \in GF(q=p^m)`$ we can obtain all the distinct elements of $`GF(q)`$. In other words, each combination of coefficients $`\{a_1 ,a_2 ,\cdots ,a_m\}`$ corresponds to a distinct element of $`GF(q)`$.

This theorem shows that all finite fields have the structure of a vector space of dimension $`m`$ over a finite field $`\mathbb Z_p`$. For the field $`GF(p^m)`$, the subfield $`GF(p)`$ is called the *ground field*.

By definition, each element of a finite field forms a group under multiplication. Let us now try to understand how they behave, giving at the same time some helpful definitions.

<div class="Def">

<a id="definition-A.3.1"></a>

**Definition A.3.1**. *Let $`\beta \in GF(q)`$. The *order* [^15] of $`\beta`$, written ord($`\beta`$) is the smallest positive integer such that $`\beta^n=1`$.*

</div>

<div class="Def">

<a id="definition-A.3.2"></a>

**Definition A.3.2**. *An element with order $`q-1`$ in $`GF(q)`$ (i.e., it generates all the nonzero elements of the field) is called a *primitive element*.*

</div>

In other words, a primitive element has the highest possible order. Since every element of the field is representable by it, this ‘special element’ (or elements) enables the ‘power representation’ of the field, which greatly simplifies multiplication. In the brackets of this last sentence we have referred to the possible existence of more than one primitive element. More specifically, they are $`\phi(q-1)`$ (i.e., the Euler totient function (Moon 2005)), as the following theorem asserts.

<div class="Theorem">

<a id="theorem-A.3.2"></a>

**Theorem A.3.2** (Todd K. Moon, (Moon 2005)). *There are $`\phi(q-1)`$ primitive elements in $`GF(q)`$.*

</div>

If $`\alpha \in GF(q)`$ is primitive, then
``` math
\{\alpha ,\alpha^2 ,\ldots ,\alpha^{q-2} ,\alpha^{q-1}=1 \}
```
is the set of nonzero elements of $`GF(q)`$. But, if $`\beta=\alpha^i`$ is also primitive then the nonzero elements of the field are still generated by
``` math
\{\beta ,\beta^2 ,\ldots ,\beta^{q-2} ,\beta^{q-1}=1 \}
```
Although these are different generators, these are not different fields, but only different representations.

Since, as we previously said, every field element can be written as $`\beta=\alpha^i \in GF(q)`$ we have the following.

<div class="Theorem">

<a id="theorem-A.3.3"></a><a id="th:roots"></a>

**Theorem A.3.3** (Todd K. Moon, (Moon 2005)). *Every element of the field $`GF(q)`$ satisfies the equation $`x^q-x=0`$. Furthermore, they constitute the entire set of roots of this equation.*

</div>

Its proof is trivial: let $`\alpha`$ be a primitive element. Then imposing $`\beta = \alpha^i`$ yields $`{(\alpha^i)}^{q-1} = {(\alpha^{q-1})}^{i} =1`$ which satisfies the equivalent equation $`x^{q-1}-1=0`$. <span id="th:FieldGFBuild" label="th:FieldGFBuild"></span>

## <a id="section-A.4"></a>A.4 Irreducible and Primitive polynomials

While any irreducible polynomial can be used to construct the extension field, computation in the field is easier if a primitive polynomial is used. We make the following observation:

<div class="Theorem">

<a id="theorem-A.4.1"></a>

**Theorem A.4.1** (Todd K. Moon, (Moon 2005)). *Let $`p`$ be a prime. An irreducible mth-degree polynomial $`f(x) \in GF(p)[x]`$ divides $`x^{p^m-1}-1`$.*

</div>

Let $`GF(q)=GF(p^m)`$ be constructed using the irreducible polynomial $`f(x)`$, where $`\alpha`$ denotes the root of $`f(x)`$ in the field: $`f(\alpha)= 0`$. By Theorem [A.3.3](#th:roots), $`\alpha`$ is a root of $`x^{p^m-1}-1`$ in $`GF(q)`$. Using the division algorithm (i.e., Euclid theorem) write <a id="eq-A.3"></a>
``` math
\begin{equation}
x^{p^m-1}-1= g(x)f(x)+r(x)
 \tag{A.3}
\end{equation}
```
where $`\mathrm{deg}(r(x)) \le m`$. Evaluating the above equation at $`x=\alpha`$ we obtain
``` math
0 = 0 + r(\alpha)
```
But the elements of the field $`GF(q)`$ are represented as polynomials in $`\alpha`$ of degree less than or equal to $`m`$, so since $`r(\alpha)= 0`$ it must be that $`r(x)`$ is a zero polynomial, $`r(x) = 0`$.

<div class="Def">

<a id="definition-A.4.1"></a>

**Definition A.4.1**. *An irreducible polynomial $`p(x) \in GF(p)[x]`$ of degree $`m`$ is said to be *primitive* if the smallest positive integer $`n`$ for which $`p(x)`$ divides $`x^n-1`$ is $`n=p^m-1`$.*

</div>

<div class="Theorem">

<a id="theorem-A.4.2"></a>

**Theorem A.4.2** (Todd K. Moon, (Moon 2005)). *The roots of an mth degree primitive polynomial $`p(x) \in GF(p)[x]`$ are primitive elements in $`GF(p^m)`$*

</div>

In other words, any of the roots can be used to generate the nonzero elements of the field $`GF(p^m)`$. Furthermore, all the nonzero elements of the field can be generated as powers of the roots of the primitive polynomial.

## <a id="section-A.5"></a><a id="sec:factoring"></a>A.5 Factoring $`x^n-1`$ 

To design and understand cyclic codes, it is important to be able to factor $`x^n-1`$ over arbitrary finite fields.

From Theorem [A.3.3](#th:roots), we know that every element of $`GF(q^m)`$ is a root of $`x^{q^m-1}-1`$, so
``` math
x^{q^m-1}-1= \prod_{i=0}^{q^m-1} {(x-\alpha^i)}
```
for a primitive element $`\alpha \in GF(q^m)`$. To provide a factorization over the field $`GF(q)`$ , the factors $`x-\alpha^i`$ can be grouped together according to conjugacy classes. First of all, let us describe some related concepts.

<div class="Def">

<a id="definition-A.5.1"></a>

**Definition A.5.1**. *Let $`\beta \in GF(q^m)`$. The *conjugates* of $`\beta`$ with respect to a subfield $`GF(q)`$ are $`\beta ,\beta^q ,\beta^{q^2} ,\beta^{q^3} ,....`$.*

</div>

Since the field is finite, the above list must repeat at some point. This is provided by the following.

<div class="Def">

<a id="definition-A.5.2"></a>

**Definition A.5.2**. *The smallest positive integer $`d`$ such that n is divisible by $`q^d-1`$ is called the *multiplicative order of $`q`$ modulo $`n`$*.*

</div>

Furthermore, if any $`\beta \in GF(q^m)`$ has $`\mathrm{ord}(\beta)=n`$ and $`d`$ is the multiplicative order of $`q`$ modulo $`n`$, then $`\beta^{q^d} = \beta`$. The $`d`$ elements $`\beta ,\beta^q ,\beta^{q^2}  ,\ldots ,\beta^{q^{d-1}}`$ are all distinct. In addition, the following can be proved.

<div class="Theorem">

<a id="theorem-A.5.1"></a>

**Theorem A.5.1** (Todd K. Moon, (Moon 2005)). *Let $`\beta \in GF(q^m)`$ have order $`n`$ and let $`d`$ be the multiplicative order of $`q`$ mod $`n`$. Then the coefficients of the polynomial $`p(x)=\prod_{i=0}^{d-1}{(x-\beta^{q^i})}`$ are in $`GF(q)`$. Furthermore, $`p(x)`$ is irreducible. That is, $`p(x)`$ is the minimal polynomial for $`\beta`$.*

</div>

<div>

<a id="table-A.4"></a><a id="tb:MinPoly3"></a>

***Table A.4:** Conjugacy Classes over $`GF(2^3)`$ with respect to $`GF(2)`$*

| Conjugacy Class | Minimal Polynomial |
|:--:|:--:|
| $`\{ 0\}`$ | $`x`$ |
| $`\{ 1\}`$ | $`x+1`$ |
| $`\{ \alpha ,\alpha^2 ,\alpha^4 \}`$ | $`(x-\alpha)(x-\alpha^2)(x-\alpha^4)= x^3+x+1`$ |
| $`\{ \alpha^3 ,\alpha^6 ,\alpha^5 \}`$ | $`(x-\alpha^3)(x-\alpha^6)(x-\alpha^5)= x^3+x^2+1`$ |

</div>

<div>

<a id="table-A.5"></a><a id="tb:MinPoly4"></a>

***Table A.5:** Conjugacy Classes over $`GF(2^4)`$ with respect to $`GF(2)`$*

| Conjugacy Class | Minimal Polynomial |
|:--:|:--:|
| $`\{ 0\}`$ | $`x`$ |
| $`\{ 1\}`$ | $`x+1`$ |
| $`\{ \alpha ,\alpha^2 ,\alpha^4 ,\alpha^8\}`$ | $`(x-\alpha)(x-\alpha^2)(x-\alpha^4)(x-\alpha^8)= x^4+x+1`$ |
| $`\{ \alpha^3 ,\alpha^6 ,\alpha^9 ,\alpha^{12} \}`$ | $`(x-\alpha^3)(x-\alpha^6)(x-\alpha^9)(x-\alpha^{12})= x^4+x^3+x^2+x+1`$ |
| $`\{ \alpha^5 ,\alpha^{10}\}`$ | $`(x-\alpha^5)(x-\alpha^{10})= x^2+x+1`$ |
| $`\{ \alpha^7 ,\alpha^{11} ,\alpha^{13} ,\alpha^{14}\}`$ | $`(x-\alpha^7)(x-\alpha^{11})(x-\alpha^{13})(x-\alpha^{14})= x^4+x^3+1`$ |

</div>

We now are ready to understand that $`x^{q^m-1}-1`$ can be expressed as a product of the minimal polynomials of the nonzero elements. For example the polynomial $`x^7-1 = x^{2^3-1}-1`$ can be factored over $`GF(2)`$ as a product of the minimal polynomials shown in Table [A.4](#tb:MinPoly3) <a id="eq-A.4"></a>
``` math
\begin{equation}
x^7-1=(x+1)(x^3+x+1)(x^3+x^2+1)
 \tag{A.4}
\end{equation}
```

To generalize the problem of factoring $`x^n-1`$ when $`n \ne q^m-1`$, let us call any element $`\beta \ne 1`$ such that $`\beta^n = 1`$ an $`n`$th root of unity. First, we have to determine a field $`GF(q^m)`$ where an $`n`$th root of unity can exist. Once found, the factorization is accomplished using the minimal polynomials in such field.

Since there are $`\phi(n)`$ elements of order $`n`$ in $`GF(q^m)`$, finding a field $`GF(q^m)`$ with $`n`$ roots of unity requires finding an $`m`$ such that $`n|q^m-1`$ (i.e., $`n`$ must be a divisor of $`q^m-1`$). This is usually done by trial and error.

Once any $`\beta`$ of order $`n`$ is found, then $`beta`$ is a root of $`x^n-1`$ in that field, and so are the elements $`\beta^2 ,\beta^3 ,\ldots ,\beta^{n-1}`$. In other words, <a id="eq-A.5"></a>
``` math
\begin{equation}
x^n-1= \prod_{i=0}^{n-1}{x-\beta^i}
 \tag{A.5}
\end{equation}
```

For example, let us now determine an extension field $`GF(2^m)`$ in which 5th roots of unity exist and express the factorization in terms of polynomials in $`GF(2)[x]`$. Since 5 is the smallest divisors of $`2^4-1`$, the roots of unity are over $`GF(16)`$. So if we let $`\beta=\alpha^3`$, $`\alpha`$ primitive, then $`\beta^5=\alpha^15=1`$. Thus the roots of $`x^5-1=x^5+1`$ in $`GF(16)`$ are
``` math
1 ,\beta ,\beta^2 ,\beta^3 ,\beta^4
```
which can be expressed in terms of the primitive element $`\alpha`$ as
``` math
1 ,\alpha^3 ,\alpha^6 ,\alpha^9 ,\alpha^{12}
```
Using the minimal polynomials shown in Table [A.5](#tb:MinPoly4) we have
``` math
x^5-1=(x+1)(x^4+x^3+x^2+x+1)
```

---

[← Conclusions](10-conclusions.md) · [Contents](README.md) · [Cyclic Codes →](12-cyclic-codes.md)

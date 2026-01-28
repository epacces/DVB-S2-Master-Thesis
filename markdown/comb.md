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

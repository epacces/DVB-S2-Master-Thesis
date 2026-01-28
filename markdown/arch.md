= \[line width=2pt,
\>= real tip,
draw\]
= \[minimum size=\]

<div class="signalflow">

(c1) ;
(a1) \[right from=c1\] $`\vet b_1 \vet u`$;
(a2) \[below from=a1\] $`\vet b_2 \vet u`$;
(a3) \[below from=a2\] $`\vdots`$;
(a8) \[below from=a3\] $`\vet b_8 \vet u`$;
(a9) \[below from=a8\] $`\vet b_9 \vet u`$;
(phh) \[below from=a9\] $`\vdots`$;
(a183) \[below from=phh\] $`\vet b_{184} \vet u`$;
(a184) \[below from=a183\] $`\vet b_{185} \vet u`$;
(a186) \[below from=a184\] $`\vdots`$;
(a191) \[below from=a186\] $`\vet b_{192} \vet u`$;
(c2) \[left from=a2\] ;
(c3) \[left from=a8\] ;
(c4) \[left from=a9\] ;
(c9) \[below from=c4, below=2.37cm\] ;
(c182) \[below from=c9,below=.63cm\] ;
(c183) \[left from=a191, right=.14cm\] ;

(input) \[left from=c9\] ;
(x1) \[right from=a1, left=0cm\] ;
(x2) \[right from=a2,left=0cm\] ;
(x8) \[right from=a8,left=0cm\] ;
(x9) \[right from=a9,left=0cm\] ;
(x183) \[right from=a183,left=0cm\] ;
(x184) \[right from=a184,left=0cm\] ;
(x191) \[right from=a191,left=0cm\] ;
(i1) at (x1) \[above= .65cm,label=right:$`y_0`$\] ;
(i2) at (x2) \[above= .65cm,label=right:$`y_1`$\] ;
(i8) at (x8) \[above= .65cm,label=right:$`y_7`$\] ;
(i9) at (x9) \[above= .65cm,label=right:$`y_8`$\] ;
(i183) at (x183) \[above= .65cm,label=right:$`y_{183}`$\] ;
(i184) at (x184) \[above= .65cm,label=right:$`y_{184}`$\] ;
(i191) at (x191) \[above= .65cm,label=right:$`y_{191}`$\] ;
(s1) \[right from=x1\] $`x_0`$;
(s2) \[right from=x2\] $`x_1`$;
(s8) \[right from=x8\] $`x_7`$;
(s9) \[right from=x9\] $`x_8`$;
(ph) \[below from=s9\] $`\vdots`$;
(s183) \[below from=ph\] $`x_{183}`$;
(s184) \[below from=s183\] $`x_{184}`$;
(sp) \[below from=s184\] $`\vdots`$;
(s191) \[below from=sp\] $`x_{191}`$;

(so1) \[right from=s1\] ;
(so2) \[right from=s2\] ;
(so8) \[right from=s8\] ;
(so9) \[right from=s9\] ;
(so183) \[right from=s183, left=0cm\] ;

(cc191) \[right from=s191, right=1cm\] ;
(cc186) \[right from=s184, right=1cm\] ;
(cc183) \[right from=s183, right=1cm\] ;
(cc9) \[right from=s9, right=1.15cm\] ;
(cc8) \[right from=s8, right=1.15cm\] ;
(cc2) \[right from=s2, right=1.15cm\] ;
(cc1) \[right from=s1, right=1.15cm\] ;

(b1) \[right from=cc1\] ;
(b2) \[right from=cc2\] ;
(b3) \[below from=b2\] $`\vdots`$;
(b4) \[right from=cc8\] ;
(b5) \[right from=cc9\] ;
(b6) \[right from=cc183\] ;
(b7) \[right from=cc186\] ;
(b8) \[right from=cc191\] ;

(n1) \[right from=b1, label=right:$`y_0`$, right=1cm\] ;
(n2) \[right from=b2, label=right:$`y_1`$, right=1cm\] ;
(n3) \[right from=b4, label=right:$`y_7`$, right=1cm\] ;
(n4) \[right from=b5\] ;
(n4b) \[right from=n4, label=right:$`y_8`$\] ;
(n5) \[right from=b6\] ;
(n5b) \[right from=n5, label=right:$`y_{183}`$\] ;
(n6) \[right from=b7\] ;
(n6b) \[right from=n6, label=right:$`y_{184}`$\] ;
(n7) \[right from=b8\] ;
(n7b) \[right from=n7, label=right:$`y_{191}`$\] ;

(ii4) at (n4) \[above= .65cm,label=right:$`x_0`$\] ;
(ii5) at (n5) \[above= .65cm,label=right:$`x_{175}`$\] ;
(ii6) at (n6) \[above= .65cm,label=right:$`x_{176}`$\] ;
(ii7) at (n7) \[above= .65cm,label=right:$`x_{183}`$\] ;

(c1)–(c2)–(c3)–(c4)–(c9)–(c182)–(c183)
(c1)–(a1)
(c2)–(a2)
(c3)–(a8)
(c4)–(a9)
(c9)–(a183)
(c183)–(a191)
(c182)–(a184);
(cc191)–(cc183)–(cc9)–(cc8)–(cc2)–(cc1);

(a1)–(x1);
(a2)–(x2);
(a8)–(x8);
(a9)–(x9);
(a183)–(x183);
(a184)–(x184);
(a191)–(x191);

(s1)–(so1);
(s2)–(so2);
(s8)–(so8);
(s9)–(so9);
(s183)–(so183);

(x1)–(s1);
(x2)–(s2);
(x8)–(s8);
(x9)–(s9);
(x183)–(s183);
(x184)–(s184);
(x191)–(s191);

(i1)–(x1);
(i2)–(x2);
(i8)–(x8);
(i9)–(x9);
(i183)–(x183);
(i184)–(x184);
(i191)–(x191);

(ii4)–(n4);
(ii5)–(n5);
(ii6)–(n6);
(ii7)–(n7);

(s184)–(cc186)
(s191)–(cc191);

(b1)–(n1);
(b2)–(n2);
(b4)–(n3);
(b5)–(n4);
(b6)–(n5);
(b7)–(n6);
(b8)–(n7);

(n4)–(n4b);
(n5)–(n5b);
(n6)–(n6b);
(n7)–(n7b);

(cc1)–(b1)
(cc2)–(b2)
(cc8)–(b4)
(cc9)–(b5)
(cc183)–(b6)
(cc186)–(b7)
(cc191)–(b8);

</div>

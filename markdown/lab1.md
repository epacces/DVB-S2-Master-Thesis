# Ricevitore a filtro adattato

Nella seguente analisi è stato preso in considerazione lo schema di trasmissione in figura <a href="#fig1" data-reference-type="ref" data-reference="fig1">1.1</a>

<figure id="fig1" data-latex-placement="h">
<div class="picture">
<p>(60,50)(0,5)</p>
<div class="picture">
<p>(0,0)(2.5,-45)
(0,0)<span>(7,4)<span>Source</span></span>
(1.5,-2)<span>(0,0)<span><span class="math inline">(<em>b</em><sub><em>i</em></sub>)</span></span></span>
(3.5,0)<span>(0,-1)<span>10</span></span></p>
</div>
<div class="picture">
<p>(0,0)(4.5,-29)
(0,0)<span>(10,6)</span>
(5,4)<span>(0,0)<span>Modulatore</span></span>
(5,2)<span>(0,0)<span>M-PAM</span></span>
(5,0)<span>(0,-1)<span>13</span></span>
(3,-2)<span>(0,0)<span><span class="math inline">(<em>a</em><sub><em>l</em></sub>)</span></span></span></p>
</div>
<div class="picture">
<p>(0,0)(3.5,4)
(0,14)<span>(7,6)</span>
(3.5,18)<span>(0,0)<span>Filtro</span></span>
(3.5,16)<span>(0,0)<span>SRRC</span></span>
(10,19)<span>(0,0)<span><span class="math inline"><em>x</em>(<em>t</em>)</span></span></span>
(7,17)<span>(1,0)<span>14</span></span></p>
</div>
<div class="picture">
<p>(0,0)(0,4)
(17,14)<span>(7,6)<span>Canale</span></span>
(20.5,21.5)<span>(0,0)<span><span class="math inline"><em>c</em>(<em>t</em>) = ∑<sub><em>i</em></sub><em>α</em><sub><em>i</em></sub><em>δ</em>(<em>t</em> − <em>τ</em><sub><em>i</em></sub>)</span></span></span>
(24,17)<span>(1,0)<span>10</span></span>
(26,19)<span>(0,0)<span><span class="math inline"><em>c</em>(<em>t</em>)</span></span></span></p>
</div>
<div class="picture">
<p>(0,0)(0,4)
(34,17)
(33,17)<span>(1,0)<span>2</span></span>
(34,16)<span>(0,1)<span>2</span></span>
(38, 18)<span>(0,0)<span><span class="math inline"><em>r</em>(<em>t</em>)</span></span></span></p>
</div>
<div class="picture">
<p>(0,0)(0.5,4)
(30.5,24)<span>(7,4)<span>AWGN</span></span>
(34,24)<span>(0,-1)<span>6</span></span>
(36,22)<span>(0,0)<span><span class="math inline"><em>w</em>(<em>t</em>)</span></span></span></p>
</div>
<p>(34,13)<span>(1,0)<span>15</span></span></p>
<div class="picture">
<p>(0,0)(-2,4)
(47,14)<span>(7,6)</span>
(50.5,18)<span>(0,0)<span>Filtro</span></span>
(50.5,16)<span>(0,0)<span>SRRC</span></span>
(50.5,20)<span>(0,1)<span>7</span></span>
(48,22)<span>(0,0)<span><span class="math inline"><em>y</em>(<em>t</em>)</span></span></span></p>
</div>
<div class="picture">
<p>(12,11)(-1,4)
(44.5,27)<span>(12,4)<span>Campionatore</span></span>
(50.5,31)<span>(0,1)<span>4</span></span>
(48,33)<span>(0,0)<span><span class="math inline">(<em>y</em><sub><em>l</em></sub>)</span></span></span></p>
</div>
<div class="picture">
<p>(0,0)(-33,-31)
(0,0)<span>(12,6)</span>
(6,4)<span>(0,0)<span>Demodulatore</span></span>
(6,2)<span>(0,0)<span>M-PAM</span></span>
(6,6)<span>(0,1)<span>10</span></span>
(4,8)<span>(0,0)<span><span class="math inline">(<em>b̂</em><sub><em>i</em></sub>)</span></span></span></p>
</div>
</div>
<figcaption>Sistema simulato</figcaption>
</figure>

Analizzando i risultati raccolti, si noterà che il ricevitore a filtro (a impulso di Nyquist) adattato ottiene delle ottime prestazioni in assenza di echi sul canale. La presenza di questi, infatti, introduce interferenza intersimbolica poiché le repliche dei simboli trasmessi vanno a interferire con quelli successivi, provocando, nel migliore dei casi, uno spiazzamento dell’istante ottimo di campionamento, nel peggiore, un decadimento pressoché totale delle prestazioni.

## Canale ideale

Quando il filtro di ricezione a radice di coseno rialzato è adattato al filtro di trasmissione, essendo soddisfatto il criterio di Nyquist, non si ha interferenza intersimbolica. In queste condizioni ideali, il ricevitore è ottimo: il fatto che la decisione venga presa simbolo per simbolo non ne pregiudica la correttezza poiché ogni simbolo idealmente è indipendente dall’altro.

### Istante ottimo di campionamento

In assenza di rumore si osserva, indipendentemente dal tipo di modulazione, come mostrano le figure <a href="#eye2PAM" data-reference-type="ref" data-reference="eye2PAM">1.2</a>, <a href="#eye4PAM" data-reference-type="ref" data-reference="eye4PAM">1.3</a>, <a href="#eye8PAM" data-reference-type="ref" data-reference="eye8PAM">1.4</a>,
che l’istante ottimo di campionamento è, a meno di un ritardo $`D`$ fissato, $`t\ped 0 = 0`$

<figure id="eye2PAM" data-latex-placement="h">
<embed src="eye2PAM.eps" />
<figcaption>Diagramma a occhio per la modulazione 2-PAM</figcaption>
</figure>

<figure id="eye4PAM" data-latex-placement="h">
<embed src="eye4PAM.eps" />
<figcaption>Diagramma a occhio per la modulazione 4-PAM</figcaption>
</figure>

<figure id="eye8PAM" data-latex-placement="h">
<embed src="eye8PAM.eps" />
<figcaption>Diagramma a occhio per la modulazione 8-PAM</figcaption>
</figure>

### Densità spettrale di potenza al variare del *roll-off*

Il filtro con fattore di decadimento $`r = 0`$ corrisponde al caso di banda minima. Ora, se aumentiamo tale fattore, aumenta anche la banda (figura <a href="#PSDro" data-reference-type="ref" data-reference="PSDro">1.6</a>), il che comporta una diminuzione dell’efficienza spettrale. Tuttavia otteniamo i seguenti vantaggi:

1.  la realizzazione del filtro è meno impegnativa;

2.  i requisiti nella precisione del campionamento sono meno stringenti, come si evince dal confronto delle figure <a href="#eye2PAM" data-reference-type="ref" data-reference="eye2PAM">1.2</a> e <a href="#eye2PAMr99" data-reference-type="ref" data-reference="eye2PAMr99">1.5</a>

<figure id="eye2PAMr99" data-latex-placement="h">
<embed src="eye2PAMr99.eps" />
<figcaption>Diagramma a occhio per la modulazione 2-PAM con <em>rolloff</em> <span class="math inline"><em>r</em> = 0, 99</span></figcaption>
</figure>

<figure id="PSDro" data-latex-placement="h">
<embed src="PSDr.eps" />
<figcaption>Densità spettrale di potenza in uscita del trasmettitore al variare del <em>rolloff</em> del filtro</figcaption>
</figure>

### Probabilità d’errore

Per le modulazioni $`M`$-PAM la probabilità d’errore media[^1] in funzione del rapporto $`E\ped b /N\ped 0`$ vale
``` math
P(e) = 2\frac{M-1}{M} Q\left(\sqrt{\frac{6\log_2 M}{M^2-1}\frac{E\ped b}{N\ped 0}}\right)
```
Poiché, come noto, la funzione $`Q(x)`$ è decrescente, la precedente espressione indica che al crescere dell’ordine $`M`$ della modulazione le prestazioni in termini di BER peggiorano (figura <a href="#Ber1" data-reference-type="ref" data-reference="Ber1">1.7</a>). Tuttavia si ha un aumento dell’efficienza spettrale, poiché per il teorema di Nyquist la banda minima occupata da un segnale $`M`$-PAM è pari a
``` math
W = \frac{1}{2T}=\frac{R\ped b}{2\log_2 M}
```
da cui risulta che l’efficienza spettrale (massima) aumenta linearmente con il numero di bit della modulazione.

<figure id="Ber1" data-latex-placement="h">
<embed src="Ber1.eps" />
<figcaption>Probabilità d’errore per le modulazioni 2-PAM, 4-PAM, 8-PAM</figcaption>
</figure>

### Mapping della costellazione 4-PAM

È intuitivo capire che la probabilità d’errore media sul bit, c.d. BER, dipende dalla funzione $`\mu`$ (*mapping*) che associa i simboli alle rappresentazioni binarie. Utilizzando rappresentazioni con bassa distanza $`d\ped H`$ di Hamming per le coppie d’errore più probabili, si riesce a minimizzare la $`P\ped b(e)`$, quando essa è sufficientemente piccola.

La *codifica di Gray*, di cui è data una rappresentazione grafica in figura <a href="#GrayMap" data-reference-type="ref" data-reference="GrayMap">1.8</a>, si dimostra che rende minima la probabilità di errore media sul bit. Questo è intuitivo poiché:

- per rapporti $`E\ped b/N\ped 0`$ elevati le coppie d’errore più probabili sono quelle a distanza euclidea minima.

- Ogni simbolo dista da quelli più vicini di un solo bit ($`d\ped H = 1`$).

<figure id="GrayMap" data-latex-placement="h">
<div class="picture">
<p>(44,10)(0,0)
(0,3)<span>(1,0)<span>44</span></span>
(2,5)<span>(0,0)<span><span class="math inline">00</span></span></span>
(2,3)
(14,5)<span>(0,0)<span><span class="math inline">01</span></span></span>
(14,3)
(26,5)<span>(0,0)<span><span class="math inline">11</span></span></span>
(26,3)
(38,5)<span>(0,0)<span><span class="math inline">10</span></span></span>
(38,3)</p>
</div>
<figcaption><em>Labelling</em> di Gray per la modulazione 4-PAM</figcaption>
</figure>

La figura <a href="#gray" data-reference-type="ref" data-reference="gray">1.9</a> conferma quanto appena detto.

<figure id="gray" data-latex-placement="h">
<embed src="gray.eps" />
<figcaption>Effetti della codifica di Gray sulla modulazione 4-PAM</figcaption>
</figure>

## Canale con due echi

Si analizza ora l’impatto che il canale selettivo ha sulle prestazioni del ricevitore quando lo schema di modulazione è il PAM. Come già anticipato le performance tendono a peggiorare.

Le ampiezze degli echi sono $`\alpha_0=\alpha_1=1`$ e rimangono costanti per tutto il corso di questa seconda simulazione, mentre il *delay spread* viene fatto variare. Inoltre manteniamo il fattore di decadimento del filtro di trasmissione al valore $`r = 0,22`$ precedente, sì da poter meglio raffrontare le prestazioni con il caso ideale, analizzato precedentemente.

### Diagrammi a occhio per diversi istanti di campionamento

Rispetto al caso ideale la forma dei diagrammi a occhio di tutte le costellazioni subisce delle sensibili modifiche: mentre, in alcuni casi, dalla lettura del diagramma, è possibile ancora individuare degli istanti ottimi di campionamento, in altri – specialmente al crescere del *delay spread* – non si hanno speranze: non è possibile trovare nemmeno un istante favorevole alla decisione.

Ciò fa riflettere sull’importanza che rivestono le tecniche di stima e di equalizzazione di canale, senza il cui ausilio, in condizioni nemmeno molto critiche, sarebbe molto difficile prendere delle decisioni corrette sui simboli ricevuti.

Vediamo ora nei dettagli i risultati ottenuti in assenza di rumore additivo:

2-PAM  
All’aumentare di $`\Delta\tau=\{2,4,6\}`$[^2] si osserva un aumento del ritardo sull’istante ottimo di campionamento, come mostrano le figure <a href="#eye2tau2" data-reference-type="ref" data-reference="eye2tau2">1.10</a>,<a href="#eye2tau4" data-reference-type="ref" data-reference="eye2tau4">1.11</a>,<a href="#eye2tau6" data-reference-type="ref" data-reference="eye2tau6">1.12</a>. Inoltre l’occhio tende, al crescere della selettività in frequenza del canale, a chiudersi.

4-PAM  
In questo caso, è ancora possibile rilevare nel diagramma un occhio per $`\Delta\tau = 2`$ e $`\Delta\tau = 4`$ (figure <a href="#eye4tau2" data-reference-type="ref" data-reference="eye4tau2">1.13</a>, <a href="#eye4tau4" data-reference-type="ref" data-reference="eye4tau4">1.14</a>), ma la maggiore cardinalità dell’insieme dei simboli si ripercuote negativamente sui diagrammi a occhio. Per $`\Delta\tau = 6`$ non è già più possiblile individuare un istante ottimo di campionamento (figura <a href="#eye4tau6" data-reference-type="ref" data-reference="eye4tau6">1.15</a>).

8-PAM  
E’ possibile trovare l’istante ottimo di campionamento solo per $`\Delta\tau = 2`$ (figura <a href="#eye8tau2" data-reference-type="ref" data-reference="eye8tau2">1.16</a>). In tutti gli altri casi non è possibile per il ricevitore prendere delle corrette decisioni (figure <a href="#eye8tau4" data-reference-type="ref" data-reference="eye8tau4">1.17</a>, <a href="#eye8tau6" data-reference-type="ref" data-reference="eye8tau6">1.18</a>).

<figure id="eye2tau2">
<embed src="eye2tau2.eps" />
<figcaption>Diagramma a occhio per la 2-PAM con <span class="math inline"><em>Δ</em><em>τ</em> = 2</span> e <span class="math inline"><em>r</em> = 0, 22</span></figcaption>
</figure>

<figure id="eye2tau4">
<embed src="eye2tau4.eps" />
<figcaption>Diagramma a occhio per la 2-PAM con <span class="math inline"><em>Δ</em><em>τ</em> = 4</span> e <span class="math inline"><em>r</em> = 0, 22</span></figcaption>
</figure>

<figure id="eye2tau6">
<embed src="eye2tau6.eps" />
<figcaption>Diagramma a occhio per la 2-PAM con <span class="math inline"><em>Δ</em><em>τ</em> = 6</span> e <span class="math inline"><em>r</em> = 0, 22</span></figcaption>
</figure>

<figure id="eye4tau2">
<embed src="eye4tau2.eps" />
<figcaption>Diagramma a occhio per la 4-PAM con <span class="math inline"><em>Δ</em><em>τ</em> = 2</span> e <span class="math inline"><em>r</em> = 0, 22</span></figcaption>
</figure>

<figure id="eye4tau4">
<embed src="eye4tau4.eps" />
<figcaption>Diagramma a occhio per la 4-PAM con <span class="math inline"><em>Δ</em><em>τ</em> = 4</span> e <span class="math inline"><em>r</em> = 0, 22</span></figcaption>
</figure>

<figure id="eye4tau6">
<embed src="eye4tau6.eps" />
<figcaption>Diagramma a occhio per la 4-PAM con <span class="math inline"><em>Δ</em><em>τ</em> = 6</span> e <span class="math inline"><em>r</em> = 0, 22</span></figcaption>
</figure>

<figure id="eye8tau2">
<embed src="eye8tau2.eps" />
<figcaption>Diagramma a occhio per la 8-PAM con <span class="math inline"><em>Δ</em><em>τ</em> = 2</span> e <span class="math inline"><em>r</em> = 0, 22</span></figcaption>
</figure>

<figure id="eye8tau4">
<embed src="eye8tau4.eps" />
<figcaption>Diagramma a occhio per la 8-PAM con <span class="math inline"><em>Δ</em><em>τ</em> = 4</span> e <span class="math inline"><em>r</em> = 0, 22</span></figcaption>
</figure>

<figure id="eye8tau6">
<embed src="eye8tau6.eps" />
<figcaption>Diagramma a occhio per la 8-PAM con <span class="math inline"><em>Δ</em><em>τ</em> = 6</span> e <span class="math inline"><em>r</em> = 0, 22</span></figcaption>
</figure>

### Effetti del canale sulla densità spettrale di potenza

Le figura <a href="#PDSds" data-reference-type="ref" data-reference="PDSds">1.19</a> mostra che al variare del *delay spread* $`\Delta\tau`$ del canale, la densità spettrale di potenza subisce un piccolo restringimento in banda.

Infatti il modulo della risposta in frequenza del canale (con due echi) è:
``` math
{|C(f)|}^2 = ({\alpha_0}^2+{\alpha_1}^2) + 2\alpha_0\alpha_1\cos(2\pi f\Delta\tau)
```
E’ immediato osservare che al crescere di $`\Delta\tau`$ la selettività del canale in frequenza aumenta, poiché il periodo del coseno diminuisce.

<figure id="PDSds">
<embed src="PSDds.eps" />
<figcaption>Densità spettrale di potenza all’uscita del canale, in assenza di rumore additivo, per alcuni valori di <span class="math inline"><em>Δ</em><em>τ</em></span></figcaption>
</figure>

### Probabilità d’errore al variare della selettività del canale

Le considerazioni fatte sui diagrammi a occhio nella sezione <a href="#eye" data-reference-type="ref" data-reference="eye">1.2.1</a>, rappresentano un utile strumento per predire la qualità della ricezione al variare dell’indice di modulazione e del *delay spread* del canale. Infatti, come ben noto, l’altezza dell’occhio rappresenta il margine di rumore, mentre la larghezza dello stesso indica la sensibilità agli errori di sincronismo[^3] del ricevitore.

Come è possibile osservare dalle figure richiamate nella sezione <a href="#eye" data-reference-type="ref" data-reference="eye">1.2.1</a>, a parità di indice di modulazione, il margine d’errore decresce all’aumentare della selettività del canale. A mo’ di esempio, si osservi, trascurando le variazioni dell’istante ottimo di campionamento, il rimpicciolimento dell’altezza dell’occhio per la modulazione 2-PAM al crescere di $`\Delta\tau`$ (figure <a href="#eye2tau4" data-reference-type="ref" data-reference="eye2tau4">1.11</a>, <a href="#eye2tau6" data-reference-type="ref" data-reference="eye2tau6">1.12</a>).

Ovviamente, a parità di $`\Delta\tau`$, l’apertura verticale dell’occhio decresce al crescere dell’indice di modulazione[^4]. Si osservino, ad esempio, le figure <a href="#eye2tau2" data-reference-type="ref" data-reference="eye2tau2">1.10</a> e <a href="#eye4tau2" data-reference-type="ref" data-reference="eye4tau2">1.13</a>.

Fatte queste premesse valutiamo le prestazioni del ricevitore al variare dell’indice di modulazione e della selettività del canale.

2-PAM  
Per $`\Delta\tau = 4`$, si ottengono le migliori prestazioni per $`t\ped{opt} = 2`$ (figura <a href="#2pams4" data-reference-type="ref" data-reference="2pams4">1.20</a>), per $`\Delta\tau = 6`$ si ha $`t\ped{opt} = 3`$ (figura <a href="#2pams6" data-reference-type="ref" data-reference="2pams6">1.21</a>). Superati questi istanti ottimi le probabilità d’errore peggiorano, in accordo con i diagrammi a occhio riportati in figura <a href="#eye2tau4" data-reference-type="ref" data-reference="eye2tau4">1.11</a>, <a href="#eye2tau6" data-reference-type="ref" data-reference="eye2tau6">1.12</a>.

4-PAM  
Per $`\Delta\tau = 4`$, si ha $`t\ped{opt} = 2`$ (figura <a href="#4pams4" data-reference-type="ref" data-reference="4pams4">1.22</a>), come è stato già previsto nella sezione <a href="#eye" data-reference-type="ref" data-reference="eye">1.2.1</a>. Le prestazioni comunque, anche nell’istante ottimo, sono pessime poiché il margine di rumore (figura <a href="#eye4tau4" data-reference-type="ref" data-reference="eye4tau4">1.14</a>) è piccolo.

8-PAM  
Le prestazioni, in accordo con le previsioni e le premesse fatte, sono pessime e rimangono pressoché inalterate al variare dell’istante di campionamento prescelto. Si osservino le figure <a href="#8pams4" data-reference-type="ref" data-reference="8pams4">1.24</a>, <a href="#8pams6" data-reference-type="ref" data-reference="8pams6">1.25</a>.

<figure id="2pams4">
<embed src="2pams4.eps" />
<figcaption>Probabilità d’errore al variare dell’istante <span class="math inline"><em>t</em><sub>0</sub></span> di decisione (<span class="math inline"><em>Δ</em><em>τ</em> = 4</span>)</figcaption>
</figure>

<figure id="2pams6">
<embed src="2pams6.eps" />
<figcaption>Probabilità d’errore al variare dell’istante <span class="math inline"><em>t</em><sub>0</sub></span> di decisione (<span class="math inline"><em>Δ</em><em>τ</em> = 6</span>)</figcaption>
</figure>

<figure id="4pams4">
<embed src="4pams4.eps" />
<figcaption>Probabilità d’errore al variare dell’istante <span class="math inline"><em>t</em><sub>0</sub></span> di decisione (<span class="math inline"><em>Δ</em><em>τ</em> = 4</span>)</figcaption>
</figure>

<figure id="4pams6">
<embed src="4pams6.eps" />
<figcaption>Probabilità d’errore al variare dell’istante <span class="math inline"><em>t</em><sub>0</sub></span> di decisione (<span class="math inline"><em>Δ</em><em>τ</em> = 6</span>)</figcaption>
</figure>

<figure id="8pams4">
<embed src="8pams4.eps" />
<figcaption>Probabilità d’errore al variare dell’istante <span class="math inline"><em>t</em><sub>0</sub></span> di decisione (<span class="math inline"><em>Δ</em><em>τ</em> = 4</span>)</figcaption>
</figure>

<figure id="8pams6">
<embed src="8pams6.eps" />
<figcaption>Probabilità d’errore al variare dell’istante <span class="math inline"><em>t</em><sub>0</sub></span> di decisione (<span class="math inline"><em>Δ</em><em>τ</em> = 6</span>)</figcaption>
</figure>

[^1]: Ideale.

[^2]: I valori riportati sono riferiti al numero di campioni di ritardo tra una replica e la successiva.

[^3]: Si ricordi ciò che è stato detto nella sezione <a href="#sync" data-reference-type="ref" data-reference="sync">1.1.2</a> in merito al *rolloff* del filtro di trasmissione. Nel corso di questa simulazione si è scelto $`r=0,22`$

[^4]: Questo è vero anche quando il canale non è ideale!

# Geometria in metri locali
L'origine è il primo punto della sorgente. La conversione di ritorno è locale / scala + origine. La precisione di ingresso limita le misure anche con calcolo float64. La CLI sections accetta una ricetta in metri locali, con griglia quadrata ancorata a (0,0).

```json
{"step":0.5,"extent":[0,1],"sections":[{"z":0.5,"status":"approved","polygons":[{"outer":[[0,0],[1,0],[1,1],[0,1]],"holes":[]}]}]}
```

Le quote sono strettamente crescenti. Base e tetto espliciti delimitano il volume, i punti medi delimitano gli strati interni. Le bande di osservazione sono semiaperte. Il centro della cella deve essere interno al materiale, escluso il bordo dei fori. Una sezione empty lascia una lacuna. Una proposta review blocca la generazione, una componente che scompare blocca la pubblicazione.

Il nodo è identificato dagli indici interi di griglia. La base HEX8 è ordinata (00,10,11,01), seguita dai quattro nodi superiori. I controlli sulle facce esterne verificano orientamento degli spigoli e un singolo ciclo di facce attorno a ciascun vertice. Jacobiano e aspect ratio sono calcolati per i parallelepipedi generati. Le coordinate sono float64 e la connettività int64.

Il percorso Create sections propone un inviluppo convesso per banda. Richiede revisione: può chiudere un cortile, unire corpi distanti o attraversare una zona priva di punti. L'editor supporta contorni distinti e fori. Una parete esterna osservata richiede evidenze ulteriori per definire lo spessore. Volte, sottosquadri e pareti sottili dipendono dal passo di campionamento e dalla griglia. Il contorno del volume è a gradini. Interfacce separate, BRep, materiali e ipotesi strutturali sono lavoro futuro.

## Griglia automatica da punti

**Grid volume** divide il rilievo in celle ortogonali, con origine XY locale e origine Z alla base scelta. Il default usa tutta l'altezza, passo XY e Z di 0,2 m e almeno un punto per cella. Per una nuvola piatta, l'unico strato è centrato sulla quota osservata. Disattivando **Use full cloud height**, Base e Roof delimitano il volume in metri locali; il clipping grafico della vista resta indipendente. L'ultima cella verticale termina esattamente al tetto, anche quando è più sottile del passo. I punti sul tetto entrano nell'ultimo strato. I punti su un confine XY entrano nella cella che inizia su quel confine.

Il worker conta per blocchi i punti in ogni cella e conserva le celle che raggiungono la soglia. Unisce le celle di ciascuno strato in anelli con fori. Per default le celle prive di supporto restano vuote. **Fill enclosed voids in each layer** include i fori completamente racchiusi in XY nello stesso strato: è un'ipotesi esplicita di materiale, può riempire un cortile e non ricuce una parete aperta. Il volume rappresentato dipende dalla risoluzione e dalla densità del rilievo. I controlli HEX8 e manifold rimangono attivi: con dati sparsi anche un contatto solo per vertice può impedire la pubblicazione. Provare una diversa discretizzazione o usare la revisione manuale.

Ricetta, limiti degli strati, soglia, politica di riempimento e mesh verificata sono pubblicati insieme. Un errore conserva la precedente revisione attiva. **Saved grids** permette di recuperare ciascuna variante per sorgente, passi, intervallo Z, soglia e riempimento. Il ripristino è esplicito e crea una nuova revisione; **Export** opera sulla revisione attiva.

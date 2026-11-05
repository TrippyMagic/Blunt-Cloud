# Geometria in metri locali
L'origine è il primo punto della sorgente. La conversione di ritorno è locale / scala + origine. La precisione di ingresso limita le misure anche con calcolo float64. La CLI sections accetta una ricetta in metri locali, con griglia quadrata ancorata a (0,0).

```json
{"step":0.5,"extent":[0,1],"sections":[{"z":0.5,"status":"approved","polygons":[{"outer":[[0,0],[1,0],[1,1],[0,1]],"holes":[]}]}]}
```

Le quote sono strettamente crescenti. Base e tetto espliciti delimitano il volume, i punti medi delimitano gli strati interni. Le bande di osservazione sono semiaperte. Il centro della cella deve essere interno al materiale, escluso il bordo dei fori. Una sezione empty lascia una lacuna. Una proposta review blocca la generazione, una componente che scompare blocca la pubblicazione.

Il nodo è identificato dagli indici interi di griglia. La base HEX8 è ordinata (00,10,11,01), seguita dai quattro nodi superiori. I controlli sulle facce esterne verificano orientamento degli spigoli e un singolo ciclo di facce attorno a ciascun vertice. Jacobiano e aspect ratio sono calcolati per i parallelepipedi generati. Le coordinate sono float64 e la connettività int64.

La proposta automatica è il solo inviluppo convesso per banda. Richiede revisione: può chiudere un cortile, unire corpi distanti o attraversare una zona priva di punti. L'editor supporta contorni distinti e fori. Una parete esterna osservata richiede evidenze ulteriori per definire lo spessore. Volte, sottosquadri e pareti sottili dipendono dal passo di campionamento e dalla griglia. Il contorno del volume è a gradini. Interfacce separate, BRep, materiali e ipotesi strutturali sono lavoro futuro.

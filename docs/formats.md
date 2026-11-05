# Formati della versione di sviluppo
|Adattatore|Entità e limiti|
|---|---|
|PCD ingresso|XYZ scalari ASCII o binary little-endian, conteggi e padding per campo. Il file originale viene conservato integralmente.|
|PLY ingresso|Vertex e XYZ, lettura con plyfile. File con face rifiutati. RGB e normali restano nel file originale.|
|TXT/XYZ ingresso|Tre colonne numeriche separate da spazi. Unità selezionabili m, cm e mm.|
|VTU uscita|HEX8 con attributo intero layer, coordinate locali in metri.|
|INP uscita|HEX8 C3D8 e ELSET per strato. Nessuna qualifica su solver.|
|DXF uscita|LWPOLYLINE chiuse alla quota campione con unità metri. Ogni layer identifica sezione, parte e anello, R0 è l'esterno.|
|PLY uscita|Contorno quadrangolare indicizzato. Accettazione della perdita di gruppi/unità.|
|STL uscita|Triangoli binari, winding esterno, verifica di collasso dopo conversione. Accettazione perdita di gruppi/unità.|

Tutti i writer rileggono il temporaneo prima della pubblicazione. Gli export utilizzano il riferimento locale. Il progetto conserva unità e origine della sorgente. Vedere specs per rapporto di accompagnamento e qualifica degli attributi.

# Progetto e pubblicazione
project.sqlite usa user_version 1. Ogni modifica aggiunge una riga revisions con la ricetta JSON. La revisione corrente è quella con ID maggiore. meshes lega a un ID una matrice di nodi, celle, facce e strati in archivio NPZ e il suo SHA-256. La rilettura controlla l'hash e disabilita pickle. Le sorgenti gestite e i punti locali mappabili sono in clouds. Una copia della sorgente conserva anche gli attributi fuori dal sottoinsieme operativo.

Generare legge una revisione, calcola fuori transazione e acquisisce BEGIN IMMEDIATE prima di confrontare nuovamente l'ID e pubblicare. Un export mantiene il blocco fino alla rilettura del file temporaneo e alla sostituzione atomica. La semplice modifica della ricetta rende indisponibile la vecchia mesh all'export. Le seconde sessioni contendono il writer SQLite.

I job avviati dalla GUI sono processi figli con un solo job attivo per finestra. Annulla termina il processo. Le revisioni commesse restano leggibili. Migrazioni, blocco per progetto fra finestre, ripulitura dopo kill e cancellazione cooperativa restano criteri di release.
Undo e redo usano la tabella history e creano revisioni nuove. I job precedenti perdono la possibilità di pubblicare.

## Directory di lavoro e archivio privato

La cartella scelta con Open project contiene i file utente e gli export. Il progetto salva il catalogo in `.bluntcloud/project.sqlite` e la copia sorgente con i punti locali in `.bluntcloud/clouds/`. **Working directory** filtra la cartella privata. **Project** mostra le entità logiche: nuvola, sezioni e volume, anche quando le sezioni sono righe nel catalogo e non file. **Saved grids** elenca i volumi automatici persistenti. Per ottenere file autonomi nella directory di lavoro usare Export, scegliendo per esempio DXF per le sezioni o VTU per il volume. Per trasferire l'intero progetto copiare anche .bluntcloud a progetto chiuso.

Al primo accesso un progetto con il vecchio catalogo alla radice sposta nella cartella privata soltanto il catalogo riconosciuto e le cartelle delle nuvole referenziate dalle revisioni. Chiudere la precedente applicazione prima del passaggio. I file utente, incluso un eventuale PCD originale nella directory di lavoro, mantengono la loro posizione. In caso di conflitto, sorgente mancante o journal pendente la migrazione si arresta con diagnostica.

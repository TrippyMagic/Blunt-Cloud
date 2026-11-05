# Progetto e pubblicazione
project.sqlite usa user_version 1. Ogni modifica aggiunge una riga revisions con la ricetta JSON. La revisione corrente è quella con ID maggiore. meshes lega a un ID una matrice di nodi, celle, facce e strati in archivio NPZ e il suo SHA-256. La rilettura controlla l'hash e disabilita pickle. Le sorgenti gestite e i punti locali mappabili sono in clouds. Una copia della sorgente conserva anche gli attributi fuori dal sottoinsieme operativo.

Generare legge una revisione, calcola fuori transazione e acquisisce BEGIN IMMEDIATE prima di confrontare nuovamente l'ID e pubblicare. Un export mantiene il blocco fino alla rilettura del file temporaneo e alla sostituzione atomica. La semplice modifica della ricetta rende indisponibile la vecchia mesh all'export. Le seconde sessioni contendono il writer SQLite.

I job avviati dalla GUI sono processi figli con un solo job attivo per finestra. Annulla termina il processo. Le revisioni commesse restano leggibili. Migrazioni, blocco per progetto fra finestre, ripulitura dopo kill e cancellazione cooperativa restano criteri di release.
Undo e redo usano la tabella history e creano revisioni nuove. I job precedenti perdono la possibilità di pubblicare.

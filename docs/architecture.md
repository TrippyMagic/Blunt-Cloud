# Architettura del prototipo 0.1
La CLI e la finestra Qt invocano lo stesso coordinatore. Il modulo domain rasterizza con NumPy e Shapely, validation verifica il complesso esaedrico generato, application pubblica le revisioni. cloud e adapters isolano lettori e scrittori. La finestra invoca la CLI in un processo QProcess anche nel bundle. Gli array rimangono sul disco del progetto.

La scelta di Qt Widgets e VTK riusa gli strumenti scientifici Python e consente il picking in una vista nativa. Tauri richiederebbe anche un runtime web offline e un ponte per la geometria. Una riscrittura C++ richiederebbe un secondo motore da verificare. Un kernel nativo sarà valutato dopo profiling. La GUI storica è archiviata separatamente. Dal checkout, nel suo ambiente PyQt5 originale, si avvia con `python -m legacy.cloud2fem.gui.main_Cloud2FEM`.

Avvio da checkout con Python gestito da uv:
```powershell
uv sync --locked --extra desktop
uv run --no-sync bluntcloud-desktop
```
Scegliere una directory progetto, importare la sorgente con la sua unità, impostare quote locali e generare le proposte. Ispezionare ciascun anello nella vista 2D, modificarne le coordinate e assegnare approved o empty. Generare il volume ed esportare nella directory di lavoro o in un’altra destinazione utente. Le coordinate sono disponibili anche in un editor JSON. La qualifica di usabilità rimane aperta.
La vista 3D sovrappone sorgente e contorno. Il worker prepara una copia di massimo 100.000 quadrilateri. La sezione selezionata comanda il piano di clipping.

Il runtime è in inglese, inclusi i dialoghi Qt, la CLI e la diagnostica. Nella vista sezione si possono trascinare o cancellare vertici, disegnare un esterno o un foro e misurare una distanza con due clic. Apply section salva la modifica. La guida integrata è differita.


Al primo Import, Blunt-Cloud chiede la cartella del progetto prima di aprire il selettore della nuvola. La colonna sinistra distingue Project, con sorgente e derivati, da Working directory, che mostra in sola lettura la cartella selezionata e segue le modifiche del filesystem.

## Navigazione 3D

La vista usa gli spostamenti del mouse in pixel per aggiornare la camera. Premere nel viewport assegna il focus alla vista. Qt mantiene la cattura fino al rilascio; la perdita di focus annulla il trascinamento. Posizione e orientamento restano fermi quando il puntatore è fermo. Le scorciatoie valgono nel viewport, così i campi numerici e l’editor degli anelli continuano a ricevere i propri tasti.

| Comando | Effetto |
|---|---|
| Sinistro o rotella premuta + trascinamento | Orbita intorno al punto focale della camera, inizialmente al centro del modello. |
| Destro + trascinamento | Trasla camera e punto focale nel piano dello schermo. |
| Rotazione della rotella | Zoom nella direzione di vista. |
| W / S, A / D | Traslazione verticale e orizzontale rispetto allo schermo. La distanza è proporzionale all’inquadratura. |
| 1 / PV | Proiezione verticale frontale sul piano XZ, osservatore dal lato −Y, +Z in alto. |
| 2 / PO | Pianta sul piano XY, osservatore dal lato +Z, +Y in alto. |
| 3 / PL | Laterale sul piano YZ, osservatore dal lato +X, +Z in alto. |
| 0 | Ricentra e adatta l’inquadratura alla geometria visibile. |

I pulsanti PV, PO e PL nella barra superiore richiamano le stesse viste ortografiche, mantenendo il punto focale e la scala apparente. Il riferimento XYZ grigio chiaro in basso a sinistra segue la camera ed è separato dalla geometria di progetto e dagli export.

## Dal rilievo al volume visibile

Dopo Import il progetto contiene soltanto la nuvola. Impostare i limiti e i passi in metri locali, poi scegliere **Create sections**. Per ogni quota verificare gli anelli, correggerli se necessario, scegliere **approved** (oppure **empty** con anelli vuoti) e premere **Apply section**. **Generate volume** indica il passaggio mancante e porta alla prima sezione da revisionare. Le stesse verifiche geometriche si applicano dalla CLI. A generazione riuscita, il worker carica il contorno del volume nella vista 3D; la barra di stato riporta il numero di facce in anteprima. Un volume vuoto viene segnalato esplicitamente.

### Scelta del percorso e strumenti 2D

Dopo Import scegliere **Grid volume** per generare un volume con una sola operazione dai punti. Per usare contorni interpretati dall'operatore scegliere **Create sections**. Le modalità dell'editor riguardano la sezione selezionata:
- **Move vertex** trascina un vertice del contorno, Canc elimina i vertici selezionati.
- **Draw outer ring** disegna il perimetro di una nuova regione di materiale. Clic sinistro per ogni vertice, destro per chiudere dopo almeno tre vertici.
- **Draw hole** disegna un vuoto all'interno di una sola regione, con gli stessi comandi.
- **Measure** misura la distanza in metri fra due clic nel piano della sezione.

**Apply section** registra le modifiche e lo stato. Per varianti automatiche usare **Saved grids** e **Export**. Da CLI, dopo l'import, `grid-volume 0 1 0.2 0.2` usa nell'ordine base, tetto, passo Z e passo XY. Sono facoltativi `--full-height`, `--min-points N` e `--fill`. Il comando `grids` elenca le varianti e `restore-grid REVISION EXPECTED` ripristina la variante solo se la revisione corrente coincide con EXPECTED.

# Istruzioni per lavorare su Blunt-Cloud

Queste istruzioni valgono per tutto il repository. Blunt-Cloud è un'applicazione scientifica locale che trasforma rilievi di edifici in sezioni modificabili, mesh esaedriche e superfici verificabili. La destinazione è Windows 11 x64, con 16 GB di RAM e GPU integrata. Il flusso deve funzionare offline su una macchina senza Python o CAD preinstallati. Distinguere nelle comunicazioni il comportamento verificato sul proprio host dalla qualifica sul target.

## Dove intervenire

| Percorso | Responsabilità |
|---|---|
| `bluntcloud/cloud.py` | Import PCD, PLY e XYZ/TXT, unità, origine locale, copia della sorgente, lettura dei punti e proposta dei contorni per banda. |
| `bluntcloud/domain.py`, `bluntcloud/validation.py` | Discretizzazione delle sezioni, HEX8, estrazione del contorno e controlli di qualità e topologia. Mantenere questi moduli utilizzabili senza GUI. |
| `bluntcloud/application.py` | Catalogo SQLite, ricette, revisioni, undo/redo, generazione e pubblicazione dei risultati. È il punto in cui proteggere la coerenza tra operazioni concorrenti. |
| `bluntcloud/adapters.py` | Esportatori e controlli di rilettura. Per entità, varianti e perdite consultare [la matrice formati](docs/formats.md). |
| `bluntcloud/__main__.py` | CLI headless e punto di ingresso per i processi avviati dal desktop. Conservare messaggi su stderr, risultati JSON su stdout e codici di uscita per i chiamanti. |
| `bluntcloud/ui.py`, `bluntcloud/editor.py` | Finestra PySide6, vista VTK, editor planare e coordinamento dei job via QProcess. |
| `desktop_launcher.py` | Avvio del bundle desktop e instradamento a CLI con `--cli`. È codice attivo. |
| `tests/` | Suite unittest del prodotto. Copre geometria ed export, import, transazioni e lingua del runtime. |
| `legacy/cloud2fem/` | Algoritmi originali e riproduttore dei difetti. La sottocartella `gui/` contiene il vecchio programma PyQt5, i file Qt Designer e le istruzioni storiche. Tenere le dipendenze storiche fuori dal runtime attivo. |
| `benchmarks/data/` | Unica copia del PCD SoftwareX originale. Preservarne i byte e la provenienza. |
| `packaging/`, `.github/workflows/windows.yml` | Bundle PyInstaller, inventario delle dipendenze native, licenze, archivio dei sorgenti, installer Inno Setup e build Windows in CI. |
| `pyproject.toml`, `uv.lock` | Versione Python, dipendenze bloccate, extra desktop/build ed entry point installabili. |

## Ambiente e comandi

Lavorare dalla radice. Il progetto richiede CPython 3.12. Per sviluppo core e test basta il profilo base:

```powershell
uv sync --locked
uv run --no-sync python -m bluntcloud --help
uv run --no-sync python -m unittest discover -s tests -v
```

Per il desktop usare `uv sync --locked --extra desktop`, quindi `uv run --no-sync bluntcloud-desktop`. L'ordine degli argomenti CLI è `bluntcloud PROJECT COMMAND`. Il percorso usuale è import → propose → revisione degli anelli → generate → inspect/export. Usare un progetto temporaneo per le prove di scrittura. Leggere [formato del progetto e job](docs/projects-and-jobs.md) prima di toccare transazioni o persistenza.

Per modifiche a dipendenze aggiornare manifest e lock insieme e verificare anche l'extra interessato. Per il packaging eseguire in PowerShell:

```powershell
./packaging/build.ps1
./dist/BluntCloud/BluntCloud.exe --cli --help
& "${env:ProgramFiles(x86)}/Inno Setup 6/ISCC.exe" packaging/installer.iss
```

Il primo comando crea il bundle in directory e il relativo inventario. Il terzo richiede Inno Setup 6 sulla macchina di build. Controllare che il sorgente distribuito comprenda i nuovi moduli attivi e conservare le attribuzioni GPL. Artefatti locali, ambienti virtuali e cache restano nelle directory ignorate da Git.

## Contratti scientifici e di progetto

- Conservare la sorgente immutata. Calcolare in metri locali con coordinate float64, mantenendo unità e origine per risalire al rilievo. Le copie ridotte servono alla visualizzazione.
- Mantenere distinti punti osservati, sezioni approvate, volume HEX8 e superficie di contorno. La proposta corrente usa un inviluppo convesso per banda: può chiudere aperture o unire corpi. Richiedere revisione prima di generare il volume. Spessori, riempimenti e ipotesi strutturali richiedono evidenze o scelte esplicite.
- Identificare i nodi mediante indici interi della griglia. Conservare connettività intera a base zero nel dominio e applicare la numerazione richiesta nell'adattatore. Confrontare le facce condivise attraverso gli ID.
- Distinguere spessore di osservazione, quota campione e limiti degli strati. Rispettare base e tetto, fori, sezioni vuote confermate e stato di revisione. Una componente persa alla risoluzione scelta richiede una diagnostica. Le regole complete e l'ordine dei nodi sono in [Geometria](docs/geometry.md).
- Qualsiasi modifica, incluso undo/redo, crea una nuova revisione. Ricontrollare la revisione attesa nella transazione di pubblicazione. Consentire l'export solo della revisione corrente e verificare la rilettura del file temporaneo prima della sostituzione.
- Usare gli stessi servizi da GUI e CLI. Eseguire il lavoro pesante fuori dal thread UI. Trasferire riferimenti o percorsi per i grandi array. Misurare tempi, memoria e reattività prima di aumentare i limiti.

## Stile, lingua e documentazione

Applicare SOLID dove sono presenti oggetti con responsabilità distinte. Preferire funzioni tipizzate per trasformazioni geometriche semplici. Usare un adattatore quando cambia il formato e un comando revisionato quando un'azione modifica il progetto. Proporre un nuovo pattern solo indicando il problema concreto che risolve. Mantenere i moduli leggibili e i commenti concentrati su invarianti, unità e scelte geometriche.

Tutto il runtime è in inglese, inclusi etichette, dialoghi, errori, CLI e installer. Usare etichette brevi con unità e mostrare dettagli quando servono a decidere o a correggere un errore. Documentazione e specifiche si scrivono in italiano. La traduzione documentale e la mini guida inglese in-app sono [differite](specs/documentazione-inglese.md).

Documentare in [docs](docs/architecture.md) ciò che il codice fa, con condizioni, limiti e prove. Aggiornare nella stessa modifica il documento proprietario del comportamento. Registrare in [specs](specs/README.md) ciò che resta pianificato, candidato o differito, con condizione di completamento. Verificare i [criteri aperti della prima release](specs/release.md) prima di dichiarare una capacità pronta.

## Verifica e consegna

- Usare fixture sintetiche deterministiche e piccole, di norma sotto 1 MiB ciascuna. Il blocco analitico 5×5×3 deve avere 75 celle, 144 nodi, 110 facce esterne e volume 0,6 m³. Aggiungere casi mirati per fori, traslazioni grandi, degenerazioni, invalidazione o errori di import secondo la modifica.
- Per riprodurre la baseline storica eseguire `uv run --locked python -m legacy.cloud2fem.probe`. Quel risultato caratterizza il difetto originario. Usare geometrie analitiche come oracoli del nuovo motore. Il [resoconto dell'audit](docs/audit-legacy.md) indica versioni e confronto upstream.
- Eseguire il benchmark originale separatamente dai test ordinari. Registrare commit, hardware, dipendenze, parametri e fase misurata. Per prestazioni e certificazione offline seguire il [protocollo di rilascio](docs/verification-and-release.md).
- Per modifiche alla UI verificare anche l'interazione reale interessata. Per modifiche a worker o packaging provare il percorso dall'eseguibile congelato. Riportare i controlli effettivamente eseguiti e i gate ancora aperti.
- Controllare branch, working tree e indice prima di intervenire. Preservare il lavoro già presente. Tenere i commit atomici, con messaggi di commit e PR in inglese. Seguire la destinazione richiesta per il push.

Per le modifiche al prodotto, rigenerare sempre l'eseguibile Windows con lo script di build, verificare il bundle, creare commit atomici in inglese e pubblicarli su master salvo diversa indicazione. La ricetta dell'installer va modificata solo quando cambia il comportamento del setup.

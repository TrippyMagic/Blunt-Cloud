# Architettura del prototipo 0.1
La CLI e la finestra Qt invocano lo stesso coordinatore. Il modulo domain rasterizza con NumPy e Shapely, validation verifica il complesso esaedrico generato, application pubblica le revisioni. cloud e adapters isolano lettori e scrittori. La finestra invoca la CLI in un processo QProcess anche nel bundle. Gli array rimangono sul disco del progetto.

La scelta di Qt Widgets e VTK riusa gli strumenti scientifici Python e consente il picking in una vista nativa. Tauri richiederebbe anche un runtime web offline e un ponte per la geometria. Una riscrittura C++ richiederebbe un secondo motore da verificare. Un kernel nativo sarà valutato dopo profiling. Il legacy resta accessibile dall'entry point originale.

Avvio da checkout con Python gestito da uv:
```powershell
uv sync --locked --extra desktop
uv run --no-sync bluntcloud-desktop
```
Scegliere una directory progetto, importare la sorgente con la sua unità, impostare quote locali e generare le proposte. Ispezionare ciascun anello nella vista 2D, modificarne le coordinate e assegnare approved o empty. Generare il volume ed esportare fuori dalla directory progetto. Le coordinate sono disponibili anche in un editor JSON. La qualifica di usabilità rimane aperta.
La vista 3D sovrappone sorgente e contorno. Il worker prepara una copia di massimo 100.000 quadrilateri. La sezione selezionata comanda il piano di clipping.

Il runtime è in inglese, inclusi i dialoghi Qt, la CLI e la diagnostica. Nella vista sezione si possono trascinare o cancellare vertici, disegnare un esterno o un foro e misurare una distanza con due clic. Apply section salva la modifica. La guida integrata è differita.


# Verifica e distribuzione
Eseguire `uv run --locked python -m unittest discover -s tests`. Le fixture sono generate in memoria o in cartelle temporanee. Il blocco di 5×5×3 celle ha 144 nodi, 110 facce esterne e volume .6 m³. Il test riapre il progetto tramite connessioni indipendenti, esporta nei cinque formati e controlla il rifiuto della revisione obsoleta.

|Invarianti|Copertura e gate residuo|
|---|---|
|I01–I04|CLI headless, indicizzazione intera e oracoli. Qualificare contatti separati e bande finali.|
|I05–I07|Controlli specifici HEX8 e superficie strutturata. Restano scostamenti bidirezionali e registrazione completa della provenienza.|
|I08–I09|Export revisionato, worker esterno. Ampliare fault injection e misurare la latenza di annullamento.|
|I10–I11|Limite conservativo di un milione di celle candidate, array cloud su disco, catalogo atomico. Restano preflight RAM globale e migrazioni.|
|I12–I13|Rilettura dei cinque export, uv.lock, build onedir da packaging/build.ps1. La certificazione Win11 pulito richiede un host dedicato.|

Target Windows 11 x64 su SSD, 16 GB e GPU integrata. Registrare CPU/GPU/driver, hash e ricetta. Misurare 1/6/10 M punti, poi 100 M sperimentali, prima variando densità a griglia fissa, poi passo a densità fissa. Un avvio a freddo e tre a caldo. Registrare tempi per fase, memoria combinata, staging, celle e p95 di input/frame. Obiettivi 8 GiB, 100 ms input, 50 ms/frame e stop entro 5 s. Il benchmark originale resta esterno alla suite ordinaria. Per il ritaglio reale registrare consenso o licenza, trasformazione e zone senza supporto.
Prova locale del 5 novembre 2026 su Windows 10. Import gestito del PCD originale in 0,326 s. Con quote sorgente da 0,025 m a passo 0,2 m e banda 0,005 m sono state predisposte 60 proposte da 263.094 osservazioni in 1,156 s. Una sola esecuzione.

La build Windows limita il PATH di PyInstaller alla virtualenv e alle directory di sistema. Una build locale aveva raccolto la icuuc.dll di Poppler, incompatibile con QtCore. Prima di creare l'inventario si esegue BluntCloud.exe --smoke-desktop per istanziare la finestra Qt e renderizzare con VTK. Il setup rimuove le due DLL ICU estranee eventualmente lasciate dalla versione precedente.

Nel setup interattivo i collegamenti Start e desktop sono selezionabili separatamente. Alla prima installazione Start è selezionato e desktop è facoltativo. L'ultima pagina offre Launch Blunt-Cloud; le installazioni silenziose saltano l'avvio. Il disinstallatore per utente è disponibile in Impostazioni Windows, App installate. Rimuove i file distribuiti e i collegamenti creati dal setup.

### Rendering su GitHub Actions

Il runner windows-2022 esegue i test Qt/VTK e lo smoke test del bundle con il backend software vtkOSOpenGLRenderWindow. Il workflow scarica Mesa 24.3.4 x64 nella cartella temporanea del runner, verifica SHA-256 e rende le DLL disponibili prima dei test. Il PATH isolato di PyInstaller tiene il renderer di CI fuori dal pacchetto distribuito. Lo smoke test lo ritrova nel PATH ripristinato. La verifica su GPU integrata resta un controllo sul target Windows 11.

Sul PCD SoftwareX completo, in metri locali, con altezza automatica, passo XY e Z di 0,2 m e soglia un punto, la modalità occupata genera 19.755 celle. Il riempimento per strato ne genera 47.775. È un confronto tra ipotesi di discretizzazione. Gli oracoli piccoli in test_automatic_grid controllano invece volume analitico, ultimo strato parziale, persistenza, esportazione delle varianti e conservazione del progetto in caso di errore.

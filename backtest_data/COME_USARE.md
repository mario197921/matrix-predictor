# Come usare il backtest

1. Scarica qualche CSV storico da football-data.co.uk in questa cartella, ad esempio:
   - https://www.football-data.co.uk/mmz4281/2425/E0.csv   (Premier League 2024/25)
   - https://www.football-data.co.uk/mmz4281/2425/I1.csv   (Serie A 2024/25)
   - https://www.football-data.co.uk/mmz4281/2425/SP1.csv  (Liga 2024/25)
   - https://www.football-data.co.uk/mmz4281/2425/D1.csv   (Bundesliga 2024/25)
   - https://www.football-data.co.uk/mmz4281/2425/F1.csv   (Ligue 1 2024/25)

   Cambia "2425" con altre stagioni (es. "2324", "2223") per avere più dati:
   più partite = backtest più affidabile. 2-3 stagioni per 2-3 leghe sono
   un buon punto di partenza.

2. Dalla cartella del progetto, esegui:
     python backtest.py backtest_data/

3. Leggi il report che stampa in console (calibrazione + ROI) e il file
   backtest_risultati.csv con il dettaglio di ogni scommessa simulata.

Vedi la testata di backtest.py per i limiti metodologici (usa uno xG
semplificato "momentum", non l'intera pipeline con infortuni/H2H/meteo
dell'app — richiede l'API live e non è backtestabile sul passato senza
un archivio storico di quelle stesse informazioni).

"""
matrix_db.py — Persistenza su Firebase Firestore delle schedine generate
dall'app, per tracciare nel tempo probabilita' dichiarate vs esiti reali
(calibrazione del modello). Le funzioni qui fanno I/O (rete verso Firestore);
la costruzione pura del record da salvare vive in matrix_modello.py
(costruisci_record_schedina), testabile senza credenziali.

Progettato per fallire in silenzio verso l'app (non deve mai bloccare la
generazione delle schedine), ma stampa sempre l'errore reale sul terminale
(stderr) per poter diagnosticare problemi di configurazione/connessione.
"""

import sys

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

from matrix_modello import costruisci_record_schedina, valuta_esito_tip
from matrix_api import scarica_risultato_partita


@st.cache_resource(show_spinner=False)
def get_firestore_client():
    """Inizializza (una sola volta per sessione, grazie alla cache di
    Streamlit) la connessione a Firestore usando le credenziali del service
    account salvate in st.secrets['firebase']. Ritorna None se le credenziali
    non sono configurate o la connessione fallisce (errore stampato su
    stderr per diagnosi)."""
    try:
        if not firebase_admin._apps:
            cred_dict = dict(st.secrets["firebase"])
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        print(f"[matrix_db] Impossibile connettersi a Firestore: {type(e).__name__}: {e}",
              file=sys.stderr)
        return None


def salva_schedina(nome: str, data_str: str, selezioni: list,
                    q_tot: float, prob_tot: float, budget: float) -> bool:
    """Salva su Firestore la schedina generata (collezione 'schedine').
    Usa come id documento 'data_nome' (es. '2026-08-28_SAFETY'): se l'app
    rigenera le stesse schedine piu' volte nello stesso giorno (Streamlit
    riesegue lo script ad ogni interazione), sovrascrive lo stesso record
    invece di crearne di duplicati.

    Ritorna True se il salvataggio e' andato a buon fine, False altrimenti
    (senza mai sollevare eccezioni verso il chiamante; l'errore reale viene
    stampato su stderr)."""
    db = get_firestore_client()
    if db is None:
        return False
    try:
        doc_id = f"{data_str}_{nome}"
        record = costruisci_record_schedina(nome, data_str, selezioni, q_tot, prob_tot, budget)
        db.collection("schedine").document(doc_id).set(record, merge=False)
        return True
    except Exception as e:
        print(f"[matrix_db] Errore salvataggio schedina '{nome}' del {data_str}: "
              f"{type(e).__name__}: {e}", file=sys.stderr)
        return False


def leggi_storico_schedine(giorni: int = 60) -> list:
    """Legge da Firestore tutte le schedine salvate, ordinate dalla piu'
    recente. 'giorni' limita quante leggerne al massimo (3 schedine al
    giorno circa: Safety/Performance/Azzardo), non un filtro sulla data
    esatta. Ogni record include 'doc_id' (l'id del documento Firestore,
    utile per aggiornare l'esito in seguito). Ritorna lista vuota se
    Firebase non e' raggiungibile/configurato (mai un'eccezione verso il
    chiamante; l'errore reale viene stampato su stderr)."""
    db = get_firestore_client()
    if db is None:
        return []
    try:
        docs = (db.collection("schedine")
                  .order_by("data", direction=firestore.Query.DESCENDING)
                  .limit(max(1, giorni) * 3)
                  .stream())
        risultato = []
        for d in docs:
            rec = d.to_dict()
            rec["doc_id"] = d.id
            risultato.append(rec)
        return risultato
    except Exception as e:
        print(f"[matrix_db] Errore lettura storico Firestore: {type(e).__name__}: {e}",
              file=sys.stderr)
        return []


def aggiorna_giocata_reale(doc_id: str, giocata: bool) -> bool:
    """Segna/toglie il flag 'giocata_reale' su una schedina generata dalla
    Matrix: usato quando l'utente spunta 'l'ho giocata davvero' nello
    Storico, cosi' quella schedina entra anche nelle statistiche delle
    scommesse reali (oltre a quelle delle proposte Matrix). Ritorna
    True/False, mai eccezioni verso il chiamante (errore reale su stderr)."""
    db = get_firestore_client()
    if db is None:
        return False
    try:
        db.collection("schedine").document(doc_id).update({"giocata_reale": bool(giocata)})
        return True
    except Exception as e:
        print(f"[matrix_db] Errore aggiornamento giocata_reale per '{doc_id}': "
              f"{type(e).__name__}: {e}", file=sys.stderr)
        return False


def aggiorna_puntata_reale(doc_id: str, puntata: float) -> bool:
    """Salva quanti euro sono stati REALMENTE puntati su una schedina
    (campo 'puntata_reale'), cosi' lo Storico puo' calcolare vincite/perdite
    in euro invece che solo il conteggio vinte/perse. Ritorna True/False,
    mai eccezioni verso il chiamante (errore reale su stderr)."""
    db = get_firestore_client()
    if db is None:
        return False
    try:
        db.collection("schedine").document(doc_id).update({"puntata_reale": float(puntata)})
        return True
    except Exception as e:
        print(f"[matrix_db] Errore aggiornamento puntata_reale per '{doc_id}': "
              f"{type(e).__name__}: {e}", file=sys.stderr)
        return False


def aggiorna_esito_schedina(doc_id: str, esito: str) -> bool:
    """Aggiorna manualmente il campo 'esito' di una schedina gia' salvata
    ('vinta' o 'persa'), in attesa che il controllo automatico dei
    risultati via API sia implementato. Ritorna True/False, mai eccezioni
    verso il chiamante (errore reale su stderr)."""
    if esito not in ("vinta", "persa", "in_attesa"):
        return False
    db = get_firestore_client()
    if db is None:
        return False
    try:
        db.collection("schedine").document(doc_id).update({"esito": esito})
        return True
    except Exception as e:
        print(f"[matrix_db] Errore aggiornamento esito per '{doc_id}': "
              f"{type(e).__name__}: {e}", file=sys.stderr)
        return False


def controlla_e_aggiorna_risultati() -> dict:
    """Controlla tutte le schedine ancora 'in_attesa' su Firestore: per
    ognuna, recupera il risultato reale di ogni partita coinvolta (via
    fixture_id salvato al momento della generazione) e valuta se ogni
    selezione ha vinto o perso. Aggiorna l'esito solo quando TUTTE le
    partite della schedina sono finite e TUTTE le selezioni sono
    automaticamente valutabili -- altrimenti la lascia 'in_attesa' (potra'
    sempre essere marcata a mano dallo Storico).

    Ritorna un riepilogo: {'vinte': int, 'perse': int, 'ancora_in_attesa':
    int, 'non_valutabili': int} -- utile per mostrare un feedback nell'app.
    Non solleva mai eccezioni verso il chiamante (errori su stderr)."""
    riepilogo = {"vinte": 0, "perse": 0, "ancora_in_attesa": 0, "non_valutabili": 0}
    db = get_firestore_client()
    if db is None:
        return riepilogo
    try:
        docs = list(db.collection("schedine").where("esito", "==", "in_attesa").stream())
    except Exception as e:
        print(f"[matrix_db] Errore lettura schedine in attesa: {type(e).__name__}: {e}",
              file=sys.stderr)
        return riepilogo

    cache_risultati = {}   # fixture_id -> risultato, per non richiamare l'API piu' volte
                            # per la stessa partita se compare in piu' schedine/gambe

    for doc in docs:
        record = doc.to_dict()
        selezioni = record.get("selezioni", [])
        if not selezioni:
            riepilogo["non_valutabili"] += 1
            continue

        esiti_gambe = []
        tutte_finite = True
        tutte_valutabili = True

        for sel in selezioni:
            fixture_id = sel.get("fixture_id")
            if fixture_id is None:
                tutte_valutabili = False
                break

            if fixture_id not in cache_risultati:
                cache_risultati[fixture_id] = scarica_risultato_partita(fixture_id)
            risultato = cache_risultati[fixture_id]

            if risultato is None or not risultato.get("finita"):
                tutte_finite = False
                break

            esito_gamba = valuta_esito_tip(
                sel["tip"], risultato["gc_ft"], risultato["gt_ft"],
                risultato.get("gc_ht"), risultato.get("gt_ht"))
            if esito_gamba is None:
                tutte_valutabili = False
                break
            esiti_gambe.append(esito_gamba)

        if not tutte_valutabili:
            riepilogo["non_valutabili"] += 1
            continue
        if not tutte_finite:
            riepilogo["ancora_in_attesa"] += 1
            continue

        esito_finale = "vinta" if all(esiti_gambe) else "persa"
        selezioni_aggiornate = [
            {**sel, "esito_gamba": "vinta" if eg else "persa"}
            for sel, eg in zip(selezioni, esiti_gambe)
        ]
        try:
            db.collection("schedine").document(doc.id).update({
                "esito": esito_finale,
                "selezioni": selezioni_aggiornate,
            })
            riepilogo[esito_finale == "vinta" and "vinte" or "perse"] += 1
        except Exception as e:
            print(f"[matrix_db] Errore aggiornamento esito/gambe per '{doc.id}': "
                  f"{type(e).__name__}: {e}", file=sys.stderr)
            riepilogo["ancora_in_attesa"] += 1

    return riepilogo

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

from matrix_modello import costruisci_record_schedina


@st.cache_resource
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

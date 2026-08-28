"""
matrix_db.py — Persistenza su Firebase Firestore delle schedine generate
dall'app, per tracciare nel tempo probabilita' dichiarate vs esiti reali
(calibrazione del modello). Le funzioni qui fanno I/O (rete verso Firestore);
la costruzione pura del record da salvare vive in matrix_modello.py
(costruisci_record_schedina), testabile senza credenziali.

Progettato per fallire in silenzio: se Firebase non e' configurato o
irraggiungibile, l'app principale deve continuare a funzionare normalmente
(la persistenza e' un extra, non un requisito per generare le schedine).
"""

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

from matrix_modello import costruisci_record_schedina


@st.cache_resource
def get_firestore_client():
    """Inizializza (una sola volta per sessione, grazie alla cache di
    Streamlit) la connessione a Firestore usando le credenziali del service
    account salvate in st.secrets['firebase']. Ritorna None se le credenziali
    non sono configurate o la connessione fallisce."""
    try:
        if not firebase_admin._apps:
            cred_dict = dict(st.secrets["firebase"])
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception:
        return None


def salva_schedina(nome: str, data_str: str, selezioni: list,
                    q_tot: float, prob_tot: float, budget: float) -> bool:
    """Salva su Firestore la schedina generata (collezione 'schedine').
    Usa come id documento 'data_nome' (es. '2026-08-28_SAFETY'): se l'app
    rigenera le stesse schedine piu' volte nello stesso giorno (Streamlit
    riesegue lo script ad ogni interazione), sovrascrive lo stesso record
    invece di crearne di duplicati.

    Ritorna True se il salvataggio e' andato a buon fine, False altrimenti
    (senza mai sollevare eccezioni verso il chiamante)."""
    db = get_firestore_client()
    if db is None:
        return False
    try:
        doc_id = f"{data_str}_{nome}"
        record = costruisci_record_schedina(nome, data_str, selezioni, q_tot, prob_tot, budget)
        db.collection("schedine").document(doc_id).set(record, merge=False)
        return True
    except Exception:
        return False

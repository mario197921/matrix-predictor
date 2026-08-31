"""
Test per matrix_db.controlla_e_aggiorna_risultati -- con Firestore e l'API
finti (nessuna rete/credenziali reali necessarie), per verificare la logica
di risoluzione per-gamba: una gamba persa chiude subito la schedina come
'persa' senza aspettare le altre, e i risultati già noti vengono salvati
gamba per gamba anche se la schedina resta 'in_attesa'.
"""
import matrix_db


class FakeDoc:
    def __init__(self, doc_id, data):
        self.id = doc_id
        self._data = data

    def to_dict(self):
        return dict(self._data)


class FakeDocRef:
    def __init__(self, store, doc_id):
        self._store = store
        self._doc_id = doc_id

    def update(self, data):
        self._store[self._doc_id].update(data)


class FakeCollection:
    def __init__(self, store):
        self._store = store
        self._filtro = None

    def where(self, field, op, value):
        assert op == "=="
        self._filtro = (field, value)
        return self

    def stream(self):
        field, value = self._filtro
        return [FakeDoc(doc_id, data) for doc_id, data in self._store.items()
                if data.get(field) == value]

    def document(self, doc_id):
        return FakeDocRef(self._store, doc_id)


class FakeDB:
    def __init__(self, store):
        self._store = store

    def collection(self, name):
        assert name == "schedine"
        return FakeCollection(self._store)


def _selezione(tip, fixture_id, esito_gamba=None):
    sel = {"match": "A vs B", "tip": tip, "prob_dichiarata": 50.0,
           "quota": 2.0, "edge": 5.0, "league": "Test", "fixture_id": fixture_id}
    if esito_gamba is not None:
        sel["esito_gamba"] = esito_gamba
    return sel


def _setup(monkeypatch, store, risultati_per_fixture):
    """risultati_per_fixture: {fixture_id: dict-risultato-o-None}."""
    monkeypatch.setattr(matrix_db, "get_firestore_client", lambda: FakeDB(store))
    monkeypatch.setattr(
        matrix_db, "scarica_risultato_partita",
        lambda fid: risultati_per_fixture.get(fid))


def test_una_gamba_persa_chiude_subito_la_schedina(monkeypatch):
    # 3 gambe: la prima e' gia' persa (partita finita), le altre due non
    # sono nemmeno iniziate -- non serve aspettarle, la multipla e' gia'
    # persa per definizione.
    store = {
        "doc1": {
            "esito": "in_attesa",
            "selezioni": [
                _selezione("1", fixture_id=101),
                _selezione("2", fixture_id=102),
                _selezione("X", fixture_id=103),
            ],
        }
    }
    risultati = {
        101: {"finita": True, "gc_ft": 0, "gt_ft": 1, "gc_ht": 0, "gt_ht": 0},  # tip "1" perde (0<1)
        102: {"finita": False, "gc_ft": None, "gt_ft": None, "gc_ht": None, "gt_ht": None},
        103: {"finita": False, "gc_ft": None, "gt_ft": None, "gc_ht": None, "gt_ht": None},
    }
    _setup(monkeypatch, store, risultati)
    riepilogo = matrix_db.controlla_e_aggiorna_risultati()

    assert riepilogo["perse"] == 1
    assert store["doc1"]["esito"] == "persa"
    sels = store["doc1"]["selezioni"]
    assert sels[0]["esito_gamba"] == "persa"
    # le altre due non sono state valutate (partite non finite): nessun
    # esito_gamba forzato per loro.
    assert "esito_gamba" not in sels[1]
    assert "esito_gamba" not in sels[2]


def test_gambe_vinte_persistono_anche_se_la_schedina_resta_in_attesa(monkeypatch):
    # 3 gambe: le prime due sono gia' vinte (partite finite), la terza non
    # e' ancora iniziata. Nessuna persa finora -> la schedina resta
    # 'in_attesa', ma le prime due gambe vanno comunque salvate come vinte
    # cosi' le statistiche per mercato le contano subito.
    store = {
        "doc2": {
            "esito": "in_attesa",
            "selezioni": [
                _selezione("1", fixture_id=201),
                _selezione("U2.5", fixture_id=202),
                _selezione("X", fixture_id=203),
            ],
        }
    }
    risultati = {
        201: {"finita": True, "gc_ft": 2, "gt_ft": 0, "gc_ht": 1, "gt_ht": 0},   # "1" vince
        202: {"finita": True, "gc_ft": 1, "gt_ft": 0, "gc_ht": 0, "gt_ht": 0},   # "U2.5" vince (1 gol tot)
        203: {"finita": False, "gc_ft": None, "gt_ft": None, "gc_ht": None, "gt_ht": None},
    }
    _setup(monkeypatch, store, risultati)
    riepilogo = matrix_db.controlla_e_aggiorna_risultati()

    assert riepilogo["ancora_in_attesa"] == 1
    assert store["doc2"]["esito"] == "in_attesa"
    sels = store["doc2"]["selezioni"]
    assert sels[0]["esito_gamba"] == "vinta"
    assert sels[1]["esito_gamba"] == "vinta"
    assert "esito_gamba" not in sels[2]


def test_tutte_vinte_risolve_la_schedina_come_vinta(monkeypatch):
    store = {
        "doc3": {
            "esito": "in_attesa",
            "selezioni": [_selezione("1", fixture_id=301), _selezione("2", fixture_id=302)],
        }
    }
    risultati = {
        301: {"finita": True, "gc_ft": 3, "gt_ft": 1, "gc_ht": 1, "gt_ht": 0},   # "1" vince
        302: {"finita": True, "gc_ft": 0, "gt_ft": 2, "gc_ht": 0, "gt_ht": 1},   # "2" vince
    }
    _setup(monkeypatch, store, risultati)
    riepilogo = matrix_db.controlla_e_aggiorna_risultati()

    assert riepilogo["vinte"] == 1
    assert store["doc3"]["esito"] == "vinta"
    assert all(s["esito_gamba"] == "vinta" for s in store["doc3"]["selezioni"])


def test_gamba_senza_fixture_id_conta_come_non_valutabile_non_ancora_in_attesa(monkeypatch):
    # Una gamba senza fixture_id non potra' MAI essere valutata in automatico
    # (non e' un "aspetta ancora", e' un "serve una tua occhiata").
    store = {
        "doc4": {
            "esito": "in_attesa",
            "selezioni": [_selezione("1", fixture_id=None)],
        }
    }
    _setup(monkeypatch, store, {})
    riepilogo = matrix_db.controlla_e_aggiorna_risultati()

    assert riepilogo["non_valutabili"] == 1
    assert riepilogo["ancora_in_attesa"] == 0
    assert store["doc4"]["esito"] == "in_attesa"


def test_mercato_non_gradabile_a_partita_finita_conta_come_non_valutabile(monkeypatch):
    # Partita finita ma il mercato (es. Angoli) non è calcolabile dai soli
    # gol -- valuta_esito_tip ritorna None: permanentemente bloccata anche
    # a partita conclusa, non un "aspetta ancora".
    store = {
        "doc5": {
            "esito": "in_attesa",
            "selezioni": [_selezione("Angoli 8+", fixture_id=501)],
        }
    }
    risultati = {501: {"finita": True, "gc_ft": 1, "gt_ft": 1, "gc_ht": 0, "gt_ht": 0}}
    _setup(monkeypatch, store, risultati)
    riepilogo = matrix_db.controlla_e_aggiorna_risultati()

    assert riepilogo["non_valutabili"] == 1
    assert store["doc5"]["esito"] == "in_attesa"


def test_nessun_progresso_non_riscrive_il_documento(monkeypatch):
    # Se una gamba era gia' senza fixture_id al giro precedente e resta
    # tale (nessun cambiamento), non deve rifare una scrittura inutile su
    # Firestore -- verificato controllando che 'selezioni' resti lo stesso
    # oggetto (nessuna update() chiamata) e il riepilogo la conti comunque.
    store = {
        "doc6": {
            "esito": "in_attesa",
            "selezioni": [_selezione("1", fixture_id=None)],
        }
    }
    _setup(monkeypatch, store, {})
    matrix_db.controlla_e_aggiorna_risultati()  # primo giro: già "non_valutabili", nessuna scrittura attesa

    # Rimpiazza update() con una versione che alza un errore se chiamata,
    # per dimostrare che il secondo giro non scrive nulla di nuovo.
    def _update_vietato(self, data):
        raise AssertionError("non doveva scrivere nulla: nessun progresso")
    monkeypatch.setattr(FakeDocRef, "update", _update_vietato)

    riepilogo = matrix_db.controlla_e_aggiorna_risultati()
    assert riepilogo["non_valutabili"] == 1

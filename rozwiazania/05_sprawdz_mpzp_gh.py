#! python 3
"""
05_sprawdz_mpzp_gh - kontrola MPZP na bryle
===========================================
Purpose:
    Karta 05. Liczy sześć wskaźników MPZP "Kielce Centrum - Solna" (uchwała
    XLI/1014/2009, teren U,M 2) wprost z krzywych bryły narysowanych w Rhino
    (patrz 05_szkic_bryly_rhino.py) i koloruje płyty kondygnacji na zielono
    albo czerwono. Nachylenia dachu nie da się odczytać z krzywych, więc ten
    wiersz zwraca "brak danych" i ok=True. Bez podpiętych wejść liczy
    domyślną masę Solna wbudowaną w skrypt, żeby wklejony komponent od razu
    coś pokazywał.

Inputs (Grasshopper):
    dzialka : Curve @item optional
        Zamknięta płaska krzywa granicy działki (domyślnie: działka masy Solna
        z tabeli DOMYSLNA_MASA, gdy dzialka, zabudowa i kondygnacje są puste).
    zabudowa : Curve @item optional
        Zamknięta płaska krzywa rzutu zabudowy, czyli obrys budynku na poziomie
        terenu (domyślnie: obrys masy Solna).
    kondygnacje : Curve @list optional
        Po jednej zamkniętej płaskiej krzywej na kondygnację, na wysokości
        stropu; krzywa o najwyższym Z <= 0 to kondygnacja podziemna
        (nie liczy się do intensywności). Można podpiąć wyjście
        kondygnacje_nowe z komponentu 06_bryla_gh (domyślnie: siedem
        kondygnacji masy Solna).
    pbc_grunt : Curve @list optional
        Krzywe gruntu rodzimego i wody powierzchniowej (domyślnie: trawnik
        masy Solna, gdy geometria jest domyślna).
    pbc_tarasy : Curve @list optional
        Krzywe tarasów i stropodachów zielonych; liczy się 50 % każdego
        o powierzchni co najmniej 10 m2 (domyślnie: dwa tarasy masy Solna).
    mieszkania : int @item optional
        Liczba mieszkań (domyślnie 30).
    miejsca_podziemne : int @item optional
        Liczba miejsc postojowych podziemnych (domyślnie 27).
    miejsca_naziemne : int @item optional
        Liczba miejsc postojowych naziemnych; na U,M 2 każde jest naruszeniem
        planu (domyślnie 3).
    plan_json : str @item optional
        Ścieżka do moje/plan.json (wzorzec: rozwiazania/plan.json). Puste albo
        nieistniejące: limity U,M 2 wbudowane w skrypt (DOMYSLNE_LIMITY).

Outputs (Grasshopper):
    raport : list[str]
        Ostrzeżenia z przedrostkiem "uwaga:", potem jedna sformatowana linia
        na każdy z sześciu wskaźników.
    ok : bool
        Koniunkcja wszystkich sześciu wskaźników.
    kolory : list[Color]
        Jeden System.Drawing.Color na krzywą z kondygnacje (zielony, gdy ok).
    plyty : list[Brep]
        Płaska płyta z każdej zamkniętej krzywej kondygnacje, do podglądu
        razem z kolory (Custom Preview).
    wskazniki : str
        Surowe wiersze wyniku jako JSON, do dalszej analizy.

Runtime:
    #! python 3 (Rhino 8, komponent Python 3 Script)
"""

import json
import os
import sys

try:
    import Rhino.Geometry as rg
    import System.Drawing as sd
    W_RHINO = True
except ImportError:
    W_RHINO = False


TOL = 0.001   # tolerancja modelu w metrach

# Domyślna masa "Solna": kopia tabeli PROSTOKATY z 05_szkic_bryly_rhino.py,
# (warstwa, x0, y0, x1, y1, z). Powtórzona tu celowo, bo skrypt wklejony do
# komponentu nie może niczego importować z rozwiazania/.
DOMYSLNA_MASA = [
    ("Dzialka",      0.0,  0.0, 50.0, 37.0,  0.0),   # 1850 m2
    ("Zabudowa",     6.0,  5.0, 43.0, 31.0,  0.0),   # 962 m2
    ("Kondygnacje",  5.0,  1.0, 45.0, 36.0, -3.0),   # 1400 m2 - garaż podziemny
    ("Kondygnacje",  6.0,  5.0, 43.0, 31.0,  4.2),   # 962 m2
    ("Kondygnacje",  6.0,  5.0, 43.0, 31.0,  7.4),   # 962 m2
    ("Kondygnacje",  6.0,  5.0, 43.0, 31.0, 10.6),   # 962 m2
    ("Kondygnacje",  6.0,  5.0, 43.0, 31.0, 13.8),   # 962 m2
    ("Kondygnacje",  7.2,  6.5, 41.2, 29.5, 17.2),   # 782 m2 - cofnięcie
    ("Kondygnacje",  8.0,  7.0, 41.0, 29.0, 20.6),   # 726 m2 - cofnięcie
    ("PBC-grunt",   30.0, 31.0, 50.0, 37.0,  0.0),   # 120 m2
    ("PBC-tarasy",  10.0, 10.0, 20.0, 19.0, 20.6),   # 90 m2 (>= 10 m2, liczy się)
    ("PBC-tarasy",  25.0, 10.0, 29.0, 12.0, 20.6),   # 8 m2 (< 10 m2, nie liczy się)
]

# Kopia rozwiazania/plan.json -> wskazniki (teren U,M 2), gdy plan_json jest puste.
DOMYSLNE_LIMITY = {
    "powierzchnia_zabudowy_max_pct": 50,
    "intensywnosc_max": 3.5,
    "pbc_min_pct": 10,
    "wysokosc": {
        "podstawowa_m": 14.0,
        "podstawowa_kondygnacje": 4,
        "maksymalna_m": 21.0,
        "maksymalna_kondygnacje": 6,
        "cofniecie_kondygnacji_powyzej_podstawowej_min_m": 1.5,
        "cofniecie_od": ["KDP-1", "Solna (KDL-6)"],
    },
    "dach_nachylenie_max_deg": 25,
    "parking": {"miejsc_na_mieszkanie_min": 1, "tylko_podziemny": True},
}

DOMYSLNE_LICZBY = {"mieszkania": 30, "miejsca_podziemne": 27, "miejsca_naziemne": 3}


def krzywe_domyslne(warstwa):
    """Zamknięte prostokąty domyślnej masy Solna z jednej warstwy, na rzędnej Z z tabeli."""
    krzywe = []
    for nazwa, x0, y0, x1, y1, z in DOMYSLNA_MASA:
        if nazwa != warstwa:
            continue
        krzywa = rg.Rectangle3d(rg.Plane.WorldXY, rg.Interval(x0, x1), rg.Interval(y0, y1)).ToNurbsCurve()
        krzywa.Transform(rg.Transform.Translation(0.0, 0.0, z))
        krzywe.append(krzywa)
    return krzywe


def pole(curve, bledy=None, nazwa=""):
    """Zwraca pole powierzchni krzywej w m2 przez AreaMassProperties.Compute.

    Zwraca 0.0, gdy `curve` to None (wejście niepodpięte w Grasshopperze) -
    inaczej AreaMassProperties.Compute rzuca ArgumentNullException zamiast
    zwrócić None. Zwraca też 0.0, gdy Rhino nie potrafi policzyć pola (krzywa
    niezamknięta/niepłaska); w obu przypadkach, jeśli podano listę `bledy`,
    dopisuje do niej czytelne ostrzeżenie (z nazwą wejścia `nazwa`, gdy podana)
    zamiast rzucać wyjątkiem .NET.
    """
    if curve is None:
        if bledy is not None:
            bledy.append("Brak krzywej {}(wejście niepodpięte) - pole przyjęto jako 0.0.".format(
                nazwa + " " if nazwa else ""))
        return 0.0
    amp = rg.AreaMassProperties.Compute(curve)
    if amp is None:
        if bledy is not None:
            bledy.append("Nie udało się policzyć pola krzywej (AreaMassProperties = None).")
        return 0.0
    return amp.Area


def gora(curve):
    """Zwraca najwyższą rzędną Z krzywej (górna krawędź kondygnacji).

    Zwraca 0.0, gdy `curve` to None (wejście niepodpięte), zamiast rzucać
    AttributeError na GetBoundingBox.
    """
    if curve is None:
        return 0.0
    return curve.GetBoundingBox(True).Max.Z


def oblicz(dzialka_m2, zabudowa_m2, kondygnacje, pbc_grunt_m2, pbc_woda_m2,
           tarasy_m2, mieszkania, podziemne, naziemne, limity):
    """Czysta funkcja (bez Rhino) licząca sześć wskaźników MPZP.

    kondygnacje: lista krotek (powierzchnia_m2, gorna_krawedz_m); kondygnacja
    jest podziemna, gdy gorna_krawedz_m <= 0, i wtedy nie wchodzi do
    intensywności zabudowy. limity to podsłownik "wskazniki" z plan.json.
    Zwraca listę sześciu słowników {wskaznik, wartosc, limit, ok, margines}
    w kolejności: zabudowa, intensywność, PBC, wysokość, dach, parking.
    """
    rows = []

    # 1) Powierzchnia zabudowy (limit maksymalny)
    limit_zab = limity["powierzchnia_zabudowy_max_pct"]
    wartosc_zab = (zabudowa_m2 / dzialka_m2) * 100.0
    ok_zab = wartosc_zab <= limit_zab
    if ok_zab:
        margines_zab = "zapas {:.1f} pp".format(limit_zab - wartosc_zab)
    else:
        margines_zab = "przekroczenie {:.1f} pp".format(wartosc_zab - limit_zab)
    rows.append({
        "wskaznik": "powierzchnia zabudowy",
        "wartosc": "{:.1f} %".format(wartosc_zab),
        "limit": "{:.1f} %".format(limit_zab),
        "ok": ok_zab,
        "margines": margines_zab,
    })

    # 2) Intensywność zabudowy (limit maksymalny) - tylko kondygnacje nadziemne
    limit_int = limity["intensywnosc_max"]
    po_nadziemne = sum(p for p, z in kondygnacje if z > 0)
    wartosc_int = po_nadziemne / dzialka_m2
    ok_int = wartosc_int <= limit_int
    if ok_int:
        margines_int = "zapas {:.2f}".format(limit_int - wartosc_int)
    else:
        margines_int = "przekroczenie {:.2f}".format(wartosc_int - limit_int)
    rows.append({
        "wskaznik": "intensywność",
        "wartosc": "{:.2f}".format(wartosc_int),
        "limit": "{:.2f}".format(limit_int),
        "ok": ok_int,
        "margines": margines_int,
    })

    # 3) Powierzchnia biologicznie czynna (limit minimalny) - grunt + woda +
    #    50% tarasów/stropodachów o powierzchni >= 10 m2 (mniejsze liczą 0)
    limit_pbc = limity["pbc_min_pct"]
    tarasy_liczone = sum(t * 0.5 for t in tarasy_m2 if t >= 10.0)
    pbc_m2 = pbc_grunt_m2 + pbc_woda_m2 + tarasy_liczone
    wartosc_pbc = (pbc_m2 / dzialka_m2) * 100.0
    ok_pbc = wartosc_pbc >= limit_pbc
    if ok_pbc:
        margines_pbc = "zapas {:.1f} pp".format(wartosc_pbc - limit_pbc)
    else:
        margines_pbc = "brakuje {:.1f} pp".format(limit_pbc - wartosc_pbc)
    rows.append({
        "wskaznik": "pow. biologicznie czynna",
        "wartosc": "{:.1f} %".format(wartosc_pbc),
        "limit": "{:.1f} %".format(limit_pbc),
        "ok": ok_pbc,
        "margines": margines_pbc,
    })

    # 4) Wysokość budynku i liczba kondygnacji nadziemnych (limity maksymalne)
    wys = limity["wysokosc"]
    limit_h = wys["maksymalna_m"]
    limit_k = wys["maksymalna_kondygnacje"]
    nadziemne = [(p, z) for p, z in kondygnacje if z > 0]
    wysokosc_top = max(z for p, z in nadziemne) if nadziemne else 0.0
    liczba_kond = len(nadziemne)
    ok_h = (wysokosc_top <= limit_h) and (liczba_kond <= limit_k)
    if ok_h:
        margines_h = "zapas {:.1f} m i {:d} kond.".format(limit_h - wysokosc_top, int(limit_k - liczba_kond))
    else:
        czesci_h = []
        if wysokosc_top > limit_h:
            czesci_h.append("przekroczenie {:.1f} m".format(wysokosc_top - limit_h))
        if liczba_kond > limit_k:
            czesci_h.append("{:d} kond. za dużo".format(int(liczba_kond - limit_k)))
        margines_h = "; ".join(czesci_h)
    rows.append({
        "wskaznik": "wysokość",
        "wartosc": "{:.1f} m / {:d} kond.".format(wysokosc_top, liczba_kond),
        "limit": "{:.1f} m / {:g} kond.".format(limit_h, limit_k),
        "ok": ok_h,
        "margines": margines_h,
    })

    # 5) Nachylenie dachu - nie do wyznaczenia z krzywych bryły
    rows.append({
        "wskaznik": "dach",
        "wartosc": "brak danych",
        "limit": "{:g}°".format(limity["dach_nachylenie_max_deg"]),
        "ok": True,
        "margines": "brak danych",
    })

    # 6) Miejsca postojowe
    parking = limity["parking"]
    wymagane = mieszkania * parking["miejsc_na_mieszkanie_min"]
    tylko_podziemny = parking["tylko_podziemny"]
    dostepne = podziemne if tylko_podziemny else (podziemne + naziemne)
    # Gdy plan dopuszcza tylko parking podziemny, każde miejsce naziemne jest
    # naruszeniem planu, nie tylko brakiem (tak samo liczy 01_sprawdz_mpzp.py).
    ok_park = dostepne >= wymagane and (not tylko_podziemny or naziemne == 0)
    if ok_park:
        margines_park = "zapas {} miejsc".format(dostepne - wymagane)
    else:
        margines_park = "brakuje {} miejsc".format(wymagane - dostepne)
    if tylko_podziemny and naziemne > 0:
        margines_park += "; {:d} miejsc naziemnych niedozwolonych".format(naziemne)
    rows.append({
        "wskaznik": "parking",
        "wartosc": "{:d} podziemnych + {:d} naziemnych".format(podziemne, naziemne),
        "limit": "{:g} miejsc{}".format(wymagane, " (tylko podziemne)" if tylko_podziemny else ""),
        "ok": ok_park,
        "margines": margines_park,
    })

    return rows


# ---------------------------------------------------------------------------
# Komponent Grasshopper - wejścia czytane z globals(), żeby plik działał także
# uruchomiony poza komponentem; niepodpięte wejście to None albo pusta lista.
# ---------------------------------------------------------------------------
def _wejscie(nazwa, domyslna):
    wartosc = globals().get(nazwa)
    return domyslna if wartosc is None else wartosc


def _lista_wejscia(nazwa):
    """Wejście listowe jako lista bez None; pojedyncza krzywa (dostęp item) też przechodzi."""
    wartosc = _wejscie(nazwa, [])
    if not isinstance(wartosc, (list, tuple)):
        wartosc = [wartosc]
    return [w for w in wartosc if w is not None]


# Domyślne wartości wyjść komponentu - obowiązują zawsze, także gdy blok
# poniżej się nie wykona (brak Rhino).
raport = []
ok = False
kolory = []
plyty = []
wskazniki = "[]"

if not W_RHINO:
    # Pusty raport nigdy nie powinien wyglądać jak "wszystko w porządku" -
    # jeśli import Rhino się nie udał, mówimy o tym wprost.
    raport = ["uwaga: import Rhino/System.Drawing nie powiódł się - komponent działa "
               "poza Rhino albo w nieobsługiwanej wersji."]
else:
    bledy = []
    _dzialka = _wejscie("dzialka", None)
    _zabudowa = _wejscie("zabudowa", None)
    _kondygnacje = _lista_wejscia("kondygnacje")
    _pbc_grunt = _lista_wejscia("pbc_grunt")
    _pbc_tarasy = _lista_wejscia("pbc_tarasy")
    if _dzialka is None and _zabudowa is None and not _kondygnacje:
        bledy.append("wejścia dzialka, zabudowa i kondygnacje puste - użyto domyślnej masy Solna wbudowanej w skrypt")
        _dzialka = krzywe_domyslne("Dzialka")[0]
        _zabudowa = krzywe_domyslne("Zabudowa")[0]
        _kondygnacje = krzywe_domyslne("Kondygnacje")
        _pbc_grunt = _pbc_grunt or krzywe_domyslne("PBC-grunt")
        _pbc_tarasy = _pbc_tarasy or krzywe_domyslne("PBC-tarasy")

    # Częściowe okablowanie (np. odpięta warstwa Kondygnacje) nie może udawać
    # wyniku OK dla budynku bez kondygnacji albo bez obrysu.
    brakuje = [nazwa for nazwa, puste in (("dzialka", _dzialka is None),
                                          ("zabudowa", _zabudowa is None),
                                          ("kondygnacje", not _kondygnacje)) if puste]
    if brakuje:
        bledy.append("wejścia {} puste - podłącz je albo odłącz wszystkie trzy, żeby użyć masy "
                     "domyślnej; wynik wymuszony na NIE".format(", ".join(brakuje)))

    dzialka_m2 = pole(_dzialka, bledy, "dzialka")
    zabudowa_m2 = pole(_zabudowa, bledy, "zabudowa")
    kondygnacje_tuples = [(pole(c, bledy), gora(c)) for c in _kondygnacje]
    # Ten komponent nie ma osobnego wejścia na wodę powierzchniową - jej
    # krzywe podpina się razem z gruntem rodzimym do pbc_grunt (stąd już
    # wchodzą do pbc_grunt_m2), więc pbc_woda_m2 zostaje tu zawsze 0.0.
    pbc_grunt_m2 = sum(pole(c, bledy) for c in _pbc_grunt)
    pbc_woda_m2 = 0.0
    tarasy_m2 = [pole(c, bledy) for c in _pbc_tarasy]

    _plan_json = _wejscie("plan_json", None)
    if _plan_json and os.path.isfile(str(_plan_json)):
        with open(str(_plan_json), "r", encoding="utf-8") as f:
            limity = json.load(f)["wskazniki"]
    else:
        bledy.append("plan_json puste albo plik nie istnieje - użyto limitów U,M 2 wbudowanych w skrypt; podłącz ścieżkę do moje/plan.json")
        limity = DOMYSLNE_LIMITY

    if dzialka_m2 <= 0.0 and "dzialka" not in brakuje:
        bledy.append("pole działki wynosi 0 - wskaźniki procentowe nie mają sensu; sprawdź krzywą dzialka")
    if dzialka_m2 <= 0.0 or brakuje:
        raport = ["uwaga: " + b for b in bledy]
        kolory = [sd.Color.FromArgb(200, 60, 60) for _ in _kondygnacje]
    else:
        rows = oblicz(dzialka_m2, zabudowa_m2, kondygnacje_tuples, pbc_grunt_m2,
                      pbc_woda_m2, tarasy_m2,
                      int(_wejscie("mieszkania", DOMYSLNE_LICZBY["mieszkania"])),
                      int(_wejscie("miejsca_podziemne", DOMYSLNE_LICZBY["miejsca_podziemne"])),
                      int(_wejscie("miejsca_naziemne", DOMYSLNE_LICZBY["miejsca_naziemne"])),
                      limity)

        raport = ["uwaga: " + b for b in bledy]
        for row in rows:
            raport.append("{}: {} | limit {} | {} | {}".format(
                row["wskaznik"], row["wartosc"], row["limit"],
                "OK" if row["ok"] else "NIE", row["margines"]))

        ok = all(row["ok"] for row in rows)
        kolor_ok = sd.Color.FromArgb(60, 170, 90)
        kolor_nie = sd.Color.FromArgb(200, 60, 60)
        kolory = [kolor_ok if ok else kolor_nie for _ in _kondygnacje]
        wskazniki = json.dumps(rows, ensure_ascii=False)

    # Płyty do podglądu z kolorami; krzywa otwarta albo niepłaska nie daje płyty.
    for krzywa in _kondygnacje:
        plaskie = rg.Brep.CreatePlanarBreps(krzywa, TOL)
        if plaskie is not None:
            plyty.extend(list(plaskie))


def _selftest():
    """Sprawdza `oblicz()` na ręcznie policzonej masie "Solna" (patrz karta 05)."""
    sys.stdout.reconfigure(encoding="utf-8")

    # Niepodpięte wejście (None) nie może wywalić wyjątku .NET - patrz opis
    # pole()/gora(); ten fragment działa bez Rhino, bo None jest wyłapywane
    # przed jakimkolwiek odwołaniem do `rg`.
    bledy_none = []
    assert pole(None, bledy_none) == 0.0
    assert bledy_none, "pole(None) powinno dopisać ostrzeżenie do listy błędów"
    assert gora(None) == 0.0

    # Wbudowana masa domyślna musi zgadzać się ze szkicem 05_szkic_bryly_rhino.py.
    assert len(DOMYSLNA_MASA) == 12, len(DOMYSLNA_MASA)
    pola_masy = [(x1 - x0) * (y1 - y0) for _, x0, y0, x1, y1, _ in DOMYSLNA_MASA]
    assert pola_masy == [1850, 962, 1400, 962, 962, 962, 962, 782, 726, 120, 90, 8], pola_masy
    assert [w[0] for w in DOMYSLNA_MASA].count("Kondygnacje") == 7

    dzialka_m2 = 1850.0
    zabudowa_m2 = 962.0
    kondygnacje = [
        (1400.0, -0.3),
        (962.0, 4.2),
        (962.0, 7.4),
        (962.0, 10.6),
        (962.0, 13.8),
        (782.0, 17.2),
        (726.0, 20.6),
    ]
    pbc_grunt_m2 = 120.0
    pbc_woda_m2 = 0.0
    tarasy_m2 = [90.0, 8.0]
    mieszkania = 30
    podziemne = 27
    naziemne = 3

    sciezka_planu = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "plan.json")
    with open(sciezka_planu, "r", encoding="utf-8") as f:
        plan = json.load(f)
    limity = plan["wskazniki"]
    assert limity == DOMYSLNE_LIMITY, "DOMYSLNE_LIMITY rozjechały się z rozwiazania/plan.json"

    rows = oblicz(dzialka_m2, zabudowa_m2, kondygnacje, pbc_grunt_m2,
                  pbc_woda_m2, tarasy_m2, mieszkania, podziemne, naziemne,
                  limity)

    flagi = [row["ok"] for row in rows]
    oczekiwane = [False, True, False, True, True, False]
    assert flagi == oczekiwane, "flagi ok: {} != {}".format(flagi, oczekiwane)
    assert rows[1]["wartosc"] == "2.90", "intensywnosc: {}".format(rows[1]["wartosc"])
    assert rows[3]["wartosc"] == "20.6 m / 6 kond.", "wysokosc: {}".format(rows[3]["wartosc"])
    assert rows[3]["margines"] == "zapas 0.4 m i 0 kond.", rows[3]["margines"]
    # Siedem kondygnacji pod limitem wysokości: tylko liczba kondygnacji jest przekroczona.
    rows_h = oblicz(dzialka_m2, zabudowa_m2, kondygnacje + [(600.0, 20.9)], pbc_grunt_m2, pbc_woda_m2,
                    tarasy_m2, mieszkania, podziemne, naziemne, limity)
    assert rows_h[3]["ok"] is False and rows_h[3]["margines"] == "1 kond. za dużo", rows_h[3]["margines"]
    assert "3 miejsc naziemnych niedozwolonych" in rows[5]["margines"], rows[5]["margines"]

    # Parking: 30 miejsc podziemnych wystarcza, ale 3 naziemne wciąż łamią plan (tylko podziemny).
    rows_park = oblicz(dzialka_m2, zabudowa_m2, kondygnacje, pbc_grunt_m2, pbc_woda_m2,
                       tarasy_m2, mieszkania, 30, 3, limity)
    assert rows_park[5]["ok"] is False, rows_park[5]
    rows_park = oblicz(dzialka_m2, zabudowa_m2, kondygnacje, pbc_grunt_m2, pbc_woda_m2,
                       tarasy_m2, mieszkania, 30, 0, limity)
    assert rows_park[5]["ok"] is True and rows_park[5]["margines"] == "zapas 0 miejsc", rows_park[5]

    print("SELFTEST OK")


if __name__ == "__main__" and not W_RHINO:
    if "--test" in sys.argv:
        _selftest()

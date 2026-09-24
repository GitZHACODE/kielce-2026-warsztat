#! python 3
"""
07_elewacja_gh - elewacja z paneli reagujących na słońce
========================================================
Purpose:
    Karta 07. Ubiera bryłę z karty 06 w siatkę diagonalną (diagrid) paneli
    piramidalnych. Głębokość i odcień każdego panelu zależą od prostej
    ekspozycji na słońce: iloczynu skalarnego normalnej panelu i kierunku
    słońca. To heurystyka do studium formy, nie analiza nasłonecznienia.
    Bez podpiętej bryły loftuje domyślną masę Solna wbudowaną w skrypt, żeby
    wklejony komponent od razu coś pokazywał.

Inputs (Grasshopper):
    bryla : Brep @item optional
        Bryła z komponentu 06_bryla_gh albo dowolny Brep z jedną dominującą
        zakrzywioną ścianą. Puste wejście: prosty loft sześciu kondygnacji
        nadziemnych masy Solna z tabeli DOMYSLNA_MASA, bez skrętu,
        z ostrzeżeniem w pierwszej linii raportu.
    kolumny : int @item optional
        Liczba rombów wokół budynku; nieparzysta jest zaokrąglana w górę
        do parzystej, żeby wzór domykał się na szwie (domyślnie 36).
    rzedy : int @item optional
        Liczba rzędów siatki od dołu do góry (domyślnie 12).
    glebokosc_min_m : float @item optional
        Głębokość wierzchołka panelu przy ekspozycji 0, w metrach (domyślnie 0.15).
    glebokosc_max_m : float @item optional
        Głębokość wierzchołka panelu przy ekspozycji 1, w metrach (domyślnie 0.90).
    azymut_slonca_deg : float @item optional
        Azymut słońca w stopniach, zgodnie z zegarem od północy; północ
        szkicu to oś +Y świata, krawędź KDP-1 (domyślnie 180, południe).
    wysokosc_slonca_deg : float @item optional
        Wysokość słońca nad horyzontem w stopniach (domyślnie 45).

Outputs (Grasshopper):
    panele : Mesh
        Jedna siatka, osobne wierzchołki na panel, kolory wierzchołków wg ekspozycji.
    siatka : list[Polyline]
        Zamknięte obrysy rombów, czyli ramy diagridu.
    ekspozycja : list[float]
        Ekspozycja od 0 do 1 dla każdego rombu, w kolejności paneli.
    raport : list[str]
        Liczba paneli, zakres głębokości, udział paneli mocno nasłonecznionych,
        przybliżona powierzchnia elewacji i zastrzeżenie o heurystyce.

Runtime:
    #! python 3 (Rhino 8, komponent Python 3 Script)
"""

import math
import sys

try:
    import Rhino.Geometry as rg
    from System.Collections.Generic import List
    W_RHINO = True
except ImportError:
    W_RHINO = False


DOMYSLNE = {
    "kolumny": 36,
    "rzedy": 12,
    "glebokosc_min_m": 0.15,
    "glebokosc_max_m": 0.90,
    "azymut_slonca_deg": 180.0,
    "wysokosc_slonca_deg": 45.0,
}
TOL = 0.001
KOLOR_JASNY = (245, 244, 240)   # panel w cieniu
KOLOR_CIEMNY = (58, 62, 70)     # panel w pełnym słońcu (grafit)
MIN_KOLUMNY = 4
MIN_RZEDY = 2

# Domyślna masa "Solna": kopia tabeli PROSTOKATY z 05_szkic_bryly_rhino.py,
# (warstwa, x0, y0, x1, y1, z); tu używane są tylko wiersze Kondygnacje.
# Powtórzona celowo: skrypt wklejony do komponentu nie importuje z rozwiazania/.
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


# ---------------------------------------------------------------------------
# Czysta arytmetyka (bez Rhino) - sprawdzana przez --test
# ---------------------------------------------------------------------------
def wektor_slonca(azymut_deg, wysokosc_deg):
    """Jednostkowy wektor w stronę słońca: azymut od północy (+Y) zgodnie z zegarem."""
    az = math.radians(azymut_deg)
    alt = math.radians(wysokosc_deg)
    return (math.sin(az) * math.cos(alt), math.cos(az) * math.cos(alt), math.sin(alt))


def ekspozycja_panelu(normalna, slonce):
    """Ekspozycja od 0 do 1: dodatnia część iloczynu skalarnego normalnej i kierunku słońca."""
    iloczyn = normalna[0] * slonce[0] + normalna[1] * slonce[1] + normalna[2] * slonce[2]
    return min(max(iloczyn, 0.0), 1.0)


def glebokosc_panelu(ekspozycja, glebokosc_min_m, glebokosc_max_m):
    return glebokosc_min_m + (glebokosc_max_m - glebokosc_min_m) * ekspozycja


def kolumny_parzyste(kolumny):
    """Szachownica rombów domyka się na szwie tylko przy parzystej liczbie kolumn."""
    k = max(int(kolumny), MIN_KOLUMNY)
    return k + (k % 2)


def indeksy_rombow(kolumny, rzedy, zamknieta):
    """Indeksy (i, j) węzłów siatki dla rombów i trójkątów brzegowych.

    Węzły: i = kolumna (0..kolumny-1 z zawinięciem, gdy zamknieta; 0..kolumny
    bez zawinięcia), j = rząd (0..rzedy). Romb (i, j) dla (i + j) parzystych
    ma naroża lewe (i, j), dolne (i+1, j-1), prawe (i+2, j), górne (i+1, j+1).
    Trójkąty domykają rząd dolny i górny. Zwraca (romby, trojkaty).
    """
    kol = kolumny_parzyste(kolumny)
    rz = max(int(rzedy), MIN_RZEDY)

    def kol_idx(i):
        return i % kol if zamknieta else i

    ostatnia_lewa = kol if zamknieta else kol - 1   # i, dla którego i+2 jeszcze istnieje
    romby = []
    for j in range(1, rz):
        for i in range(0, ostatnia_lewa):
            if (i + j) % 2 != 0:
                continue
            romby.append(((kol_idx(i), j), (kol_idx(i + 1), j - 1),
                          (kol_idx(i + 2), j), (kol_idx(i + 1), j + 1)))

    trojkaty = []
    for k in range(0, ostatnia_lewa):
        if k % 2 == 0:
            trojkaty.append(((kol_idx(k), 0), (kol_idx(k + 2), 0), (kol_idx(k + 1), 1)))
        if (k + rz) % 2 == 0:
            trojkaty.append(((kol_idx(k), rz), (kol_idx(k + 1), rz - 1), (kol_idx(k + 2), rz)))
    return romby, trojkaty


def kolor_ekspozycji(ekspozycja):
    """Kolor (r, g, b) między jasnym (ekspozycja 0) a grafitowym (ekspozycja 1)."""
    e = min(max(ekspozycja, 0.0), 1.0)
    return tuple(int(round(a + (b - a) * e)) for a, b in zip(KOLOR_JASNY, KOLOR_CIEMNY))


def linie_raportu(liczba_rombow, liczba_trojkatow, glebokosc_min_m, glebokosc_max_m,
                  ekspozycje, powierzchnia_m2):
    mocne = sum(1 for e in ekspozycje if e > 0.5)
    udzial = (100.0 * mocne / len(ekspozycje)) if ekspozycje else 0.0
    glebokosci = [glebokosc_panelu(e, glebokosc_min_m, glebokosc_max_m) for e in ekspozycje]
    g_min = min(glebokosci) if glebokosci else glebokosc_min_m
    g_max = max(glebokosci) if glebokosci else glebokosc_min_m
    return [
        "paneli: {} rombów + {} trójkątów brzegowych".format(liczba_rombow, liczba_trojkatow),
        "głębokość paneli (osiągnięta): {:.2f}-{:.2f} m przy zakresie {:.2f}-{:.2f} m".format(
            g_min, g_max, glebokosc_min_m, glebokosc_max_m),
        "panele o ekspozycji powyżej 0.5: {} ({:.1f} %)".format(mocne, udzial),
        "powierzchnia elewacji (przybliżona, bez głębokości): {:.0f} m2".format(powierzchnia_m2),
        "heurystyka: iloczyn skalarny normalnej i kierunku słońca, nie analiza nasłonecznienia",
    ]


# ---------------------------------------------------------------------------
# Geometria (RhinoCommon)
# ---------------------------------------------------------------------------
def _pole_sciany(sciana):
    brep = sciana.DuplicateFace(False)
    amp = rg.AreaMassProperties.Compute(brep) if brep is not None else None
    return amp.Area if amp is not None else 0.0


def _wybierz_sciane(bryla):
    """Największa niepłaska ściana; gdy wszystkie są płaskie, największa w ogóle."""
    kandydaci = []
    for sciana in bryla.Faces:
        kandydaci.append((sciana.IsPlanar(TOL), _pole_sciany(sciana), sciana))
    if not kandydaci:
        return None
    nieplaskie = [k for k in kandydaci if not k[0]]
    pula = nieplaskie if nieplaskie else kandydaci
    return max(pula, key=lambda k: k[1])[2]


def _jednostkowy(v):
    w = rg.Vector3d(v)
    if not w.Unitize():
        return rg.Vector3d.ZAxis
    return w


def _srednia_normalna(normalne):
    suma = rg.Vector3d(0.0, 0.0, 0.0)
    for n in normalne:
        suma += n
    return _jednostkowy(suma)


def _pole_wieloboku(punkty):
    """Przybliżone pole rombu albo trójkąta z iloczynów wektorowych; romby na
    skręconej powierzchni nie są płaskie, więc AreaMassProperties zwróciłoby None."""
    if len(punkty) < 3:
        return 0.0
    suma = rg.Vector3d(0.0, 0.0, 0.0)
    for k in range(1, len(punkty) - 1):
        suma += rg.Vector3d.CrossProduct(punkty[k] - punkty[0], punkty[k + 1] - punkty[0])
    return 0.5 * suma.Length


def _dodaj_wielobok(mesh, punkty, normalna, kolor):
    """Dodaje płaski wielobok (3 lub 4 wierzchołki) jako wachlarz trójkątów
    o nawinięciu zgodnym z normalną; zwraca indeksy wierzchołków."""
    if len(punkty) >= 3:
        nawiniecie = rg.Vector3d.CrossProduct(punkty[1] - punkty[0], punkty[2] - punkty[0])
        if nawiniecie * normalna < 0.0:
            punkty = list(reversed(punkty))
    idx = [mesh.Vertices.Add(p.X, p.Y, p.Z) for p in punkty]
    for _ in idx:
        mesh.VertexColors.Add(kolor[0], kolor[1], kolor[2])
    for k in range(1, len(idx) - 1):
        mesh.Faces.AddFace(idx[0], idx[k], idx[k + 1])
    return idx


def _dodaj_piramide(mesh, naroza, normalna, glebokosc, kolor):
    """Romb z wierzchołkiem wypchniętym wzdłuż normalnej: cztery trójkąty, pięć
    osobnych wierzchołków, żeby kolor i cieniowanie były per panel."""
    # Środek liczony na liczbach, nie na Point3d: pod pythonnet Point3d + Point3d
    # trafia w przeciążenie Point3d + Vector3d i rzuca ArgumentException.
    n_pkt = float(len(naroza))
    srodek = rg.Point3d(sum(p.X for p in naroza) / n_pkt,
                        sum(p.Y for p in naroza) / n_pkt,
                        sum(p.Z for p in naroza) / n_pkt)
    wierzcholek = srodek + normalna * glebokosc

    nawiniecie = rg.Vector3d.CrossProduct(naroza[1] - naroza[0], naroza[2] - naroza[0])
    if nawiniecie * normalna < 0.0:
        naroza = list(reversed(naroza))

    idx = [mesh.Vertices.Add(p.X, p.Y, p.Z) for p in naroza]
    idx_w = mesh.Vertices.Add(wierzcholek.X, wierzcholek.Y, wierzcholek.Z)
    for _ in range(len(idx) + 1):
        mesh.VertexColors.Add(kolor[0], kolor[1], kolor[2])
    for k in range(len(idx)):
        mesh.Faces.AddFace(idx_w, idx[k], idx[(k + 1) % len(idx)])


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


def bryla_domyslna(bledy):
    """Prosty loft domyślnej masy Solna (bez skrętu i zaokrąglenia): parter
    skopiowany na teren, potem każdy strop nadziemny, pokrywy, normalne na zewnątrz.
    Prostokąty z Rectangle3d mają ten sam kierunek i ten sam narożnik startowy,
    więc loft nie potrzebuje wyrównywania szwów."""
    stropy = [k for k in krzywe_domyslne("Kondygnacje") if k.GetBoundingBox(True).Max.Z > 0.0]
    stropy.sort(key=lambda k: k.GetBoundingBox(True).Max.Z)
    if len(stropy) < 2:
        bledy.append("domyślna masa ma mniej niż dwie kondygnacje nadziemne")
        return None
    parter = stropy[0].DuplicateCurve()
    parter.Transform(rg.Transform.Translation(0.0, 0.0, -parter.GetBoundingBox(True).Max.Z))
    sekcje = List[rg.Curve]()
    for krzywa in [parter] + stropy:
        sekcje.Add(krzywa)
    breps = rg.Brep.CreateFromLoftRebuild(sekcje, rg.Point3d.Unset, rg.Point3d.Unset,
                                          rg.LoftType.Normal, False, 32)
    if breps is None or len(breps) == 0:
        bledy.append("loft domyślnej masy nie powiódł się")
        return None
    bryla = breps[0]
    zamknieta = bryla.CapPlanarHoles(TOL)
    if zamknieta is not None:
        bryla = zamknieta
    if bryla.SolidOrientation == rg.BrepSolidOrientation.Inward:
        bryla.Flip()
    return bryla


def zbuduj_elewacje(bryla, kolumny, rzedy, glebokosc_min_m, glebokosc_max_m,
                    azymut_slonca_deg, wysokosc_slonca_deg):
    """Buduje siatkę paneli na dominującej ścianie bryły. Zwraca słownik z
    kluczami panele, siatka, ekspozycja, raport, bledy."""
    bledy = []
    wynik = {"panele": None, "siatka": [], "ekspozycja": [], "raport": [], "bledy": bledy}
    if bryla is None or bryla.Faces.Count == 0:
        bledy.append("brak bryły - podłącz wyjście bryla z komponentu 06_bryla_gh")
        return wynik

    sciana = _wybierz_sciane(bryla)
    if sciana is None:
        bledy.append("bryła nie ma ścian do opanelowania")
        return wynik

    # 1) Kierunki parametryzacji: zamknięty biegnie wokół budynku, drugi do góry.
    zamk0, zamk1 = sciana.IsClosed(0), sciana.IsClosed(1)
    kier_wokolo = 0 if zamk0 else (1 if zamk1 else 0)
    kier_gora = 1 - kier_wokolo
    zamknieta = sciana.IsClosed(kier_wokolo)
    dom_w = sciana.Domain(kier_wokolo)
    dom_g = sciana.Domain(kier_gora)

    def punkt(uw, vg):
        return sciana.PointAt(uw, vg) if kier_wokolo == 0 else sciana.PointAt(vg, uw)

    def normalna(uw, vg):
        n = sciana.NormalAt(uw, vg) if kier_wokolo == 0 else sciana.NormalAt(vg, uw)
        return _jednostkowy(n)

    # Rzędy mają rosnąć z wysokością: sprawdzamy Z na dole i na górze domeny.
    z_dol = punkt(dom_w.Mid, dom_g.T0).Z
    z_gora = punkt(dom_w.Mid, dom_g.T1).Z
    if z_gora < z_dol:
        dom_g = rg.Interval(dom_g.T1, dom_g.T0)

    kol = kolumny_parzyste(kolumny)
    rz = max(int(rzedy), MIN_RZEDY)
    liczba_kolumn_siatki = kol if zamknieta else kol + 1

    # 2) Siatka punktów i normalnych; normalne odwracamy, gdy pierwsza wskazuje do środka bryły.
    punkty = []
    normalne = []
    for i in range(liczba_kolumn_siatki):
        uw = dom_w.T0 + (dom_w.T1 - dom_w.T0) * (float(i) / kol)
        kolumna_p = []
        kolumna_n = []
        for j in range(rz + 1):
            vg = dom_g.T0 + (dom_g.T1 - dom_g.T0) * (float(j) / rz)
            kolumna_p.append(punkt(uw, vg))
            kolumna_n.append(normalna(uw, vg))
        punkty.append(kolumna_p)
        normalne.append(kolumna_n)

    srodek_bryly = bryla.GetBoundingBox(True).Center
    probka_p = punkty[0][rz // 2]
    probka_n = normalne[0][rz // 2]
    if (probka_p - srodek_bryly) * probka_n < 0.0:
        normalne = [[-n for n in kolumna] for kolumna in normalne]

    # 3) Romby i trójkąty brzegowe.
    slonce_t = wektor_slonca(azymut_slonca_deg, wysokosc_slonca_deg)
    romby, trojkaty = indeksy_rombow(kol, rz, zamknieta)

    mesh = rg.Mesh()
    siatka = []
    ekspozycje = []
    powierzchnia = 0.0
    for romb in romby:
        naroza = [punkty[i][j] for i, j in romb]
        n = _srednia_normalna([normalne[i][j] for i, j in romb])
        e = ekspozycja_panelu((n.X, n.Y, n.Z), slonce_t)
        d = glebokosc_panelu(e, glebokosc_min_m, glebokosc_max_m)
        _dodaj_piramide(mesh, naroza, n, d, kolor_ekspozycji(e))
        # Polyline budowana przez Add, bo konstruktor z listą Pythona nie ma
        # pasującego przeciążenia pod pythonnet (oczekuje IEnumerable<Point3d>).
        obrys = rg.Polyline()
        for p in naroza + [naroza[0]]:
            obrys.Add(p)
        siatka.append(obrys)
        ekspozycje.append(e)
        powierzchnia += _pole_wieloboku(naroza)

    for trojkat in trojkaty:
        naroza = [punkty[i][j] for i, j in trojkat]
        n = _srednia_normalna([normalne[i][j] for i, j in trojkat])
        _dodaj_wielobok(mesh, naroza, n, kolor_ekspozycji(0.0))
        powierzchnia += _pole_wieloboku(naroza)

    mesh.Normals.ComputeNormals()
    mesh.Compact()
    if not mesh.IsValid:
        bledy.append("siatka paneli nie przeszła walidacji Rhino (Mesh.IsValid = False)")

    wynik["panele"] = mesh
    wynik["siatka"] = siatka
    wynik["ekspozycja"] = ekspozycje
    wynik["raport"] = linie_raportu(len(romby), len(trojkaty), glebokosc_min_m, glebokosc_max_m,
                                    ekspozycje, powierzchnia)
    return wynik


# ---------------------------------------------------------------------------
# Komponent Grasshopper - wejścia czytane z globals(), żeby plik działał także
# uruchomiony poza komponentem (wtedy wejść nie ma i raport to mówi).
# ---------------------------------------------------------------------------
def _wejscie(nazwa, domyslna):
    wartosc = globals().get(nazwa)
    return domyslna if wartosc is None else wartosc


panele = None
siatka = []
ekspozycja = []
raport = []

if not W_RHINO:
    raport = ["uwaga: import Rhino nie powiódł się - komponent działa poza Rhino albo w nieobsługiwanej wersji."]
else:
    _uwagi = []
    _bryla = _wejscie("bryla", None)
    if _bryla is None:
        # Wklejony komponent bez kabli ma od razu coś pokazać.
        _bryla = bryla_domyslna(_uwagi)
        _uwagi.insert(0, "wejście bryla puste - użyto loftu domyślnej masy Solna bez skrętu; "
                         "podłącz wyjście bryla z komponentu 06_bryla_gh")
    if _bryla is None:
        raport = ["uwaga: " + u for u in _uwagi]
    else:
        _wynik = zbuduj_elewacje(
            _bryla,
            int(_wejscie("kolumny", DOMYSLNE["kolumny"])),
            int(_wejscie("rzedy", DOMYSLNE["rzedy"])),
            float(_wejscie("glebokosc_min_m", DOMYSLNE["glebokosc_min_m"])),
            float(_wejscie("glebokosc_max_m", DOMYSLNE["glebokosc_max_m"])),
            float(_wejscie("azymut_slonca_deg", DOMYSLNE["azymut_slonca_deg"])),
            float(_wejscie("wysokosc_slonca_deg", DOMYSLNE["wysokosc_slonca_deg"])),
        )
        panele = _wynik["panele"]
        siatka = _wynik["siatka"]
        ekspozycja = _wynik["ekspozycja"]
        raport = (["uwaga: " + u for u in _uwagi]
                  + ["uwaga: " + b for b in _wynik["bledy"]] + _wynik["raport"])


def _selftest():
    """Sprawdza czystą arytmetykę bez Rhino (wywołanie: --test)."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    s = wektor_slonca(180.0, 45.0)
    assert all(abs(a - b) < 1e-4 for a, b in zip(s, (0.0, -0.70711, 0.70711))), s
    s = wektor_slonca(90.0, 0.0)
    assert all(abs(a - b) < 1e-4 for a, b in zip(s, (1.0, 0.0, 0.0))), s

    assert ekspozycja_panelu((0.0, 1.0, 0.0), (0.0, -1.0, 0.0)) == 0.0
    assert ekspozycja_panelu((0.0, -1.0, 0.0), (0.0, -1.0, 0.0)) == 1.0
    assert abs(glebokosc_panelu(0.5, 0.15, 0.9) - 0.525) < 1e-12

    romby, trojkaty = indeksy_rombow(36, 12, True)
    assert len(romby) == 198 and len(trojkaty) == 36, (len(romby), len(trojkaty))
    romby35, trojkaty35 = indeksy_rombow(35, 12, True)
    assert len(romby35) == 198 and len(trojkaty35) == 36, "nieparzyste kolumny mają być zaokrąglone do parzystych"
    for romb in romby:
        for i, j in romb:
            assert 0 <= i < 36 and 0 <= j <= 12, romb   # siatka zamknięta ma kolumny 0..35
    assert max(i for romb in romby for i, j in romb) == 35
    romby_otwarte, _ = indeksy_rombow(36, 12, False)
    assert max(i for romb in romby_otwarte for i, j in romb) == 36, "siatka otwarta używa kolumny 36"
    assert len(romby_otwarte) < 198, "siatka otwarta ma mniej rombów niż zamknięta"

    assert kolor_ekspozycji(0.0) == (245, 244, 240)
    assert kolor_ekspozycji(1.0) == (58, 62, 70)

    linie = linie_raportu(198, 36, 0.15, 0.9, [0.0, 0.6, 1.0, 0.2], 2500.0)
    assert linie[0] == "paneli: 198 rombów + 36 trójkątów brzegowych", linie[0]
    assert linie[1] == "głębokość paneli (osiągnięta): 0.15-0.90 m przy zakresie 0.15-0.90 m", linie[1]
    assert linie[2] == "panele o ekspozycji powyżej 0.5: 2 (50.0 %)", linie[2]
    assert "heurystyka" in linie[4]
    # Wbudowana masa domyślna musi zgadzać się ze szkicem 05_szkic_bryly_rhino.py.
    assert len(DOMYSLNA_MASA) == 12, len(DOMYSLNA_MASA)
    kond = [(x1 - x0) * (y1 - y0) for w, x0, y0, x1, y1, z in DOMYSLNA_MASA if w == "Kondygnacje"]
    assert kond == [1400, 962, 962, 962, 962, 782, 726], kond
    print("SELFTEST OK")


if __name__ == "__main__" and not W_RHINO and "--test" in sys.argv:
    _selftest()

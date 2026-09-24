#! python 3
"""
elewacja_zaawansowana_gh - elewacja z wyborem wzoru, otworami, atraktorami i paletą
====================================================================================
Purpose:
    Przykład zaawansowany do karty 07. Ubiera dominującą ścianę bryły w panele
    o wybranym wzorze (romby, kwadraty, trójkąty, heksagony) i typie (płaski
    z otworem, piramida, ścięta piramida z otworem). Intensywność każdego panelu
    to mieszanka ekspozycji na słońce i bliskości punktów-atraktorów; steruje
    głębokością, wielkością otworu i kolorem z jednej z trzech palet. To
    heurystyka do studium formy, nie analiza nasłonecznienia. Bez podpiętej
    bryły loftuje domyślną masę Solna wbudowaną w skrypt.

Inputs (Grasshopper):
    bryla : Brep @item optional
        Bryła z komponentu 06_bryla_gh albo bryla_zaawansowana_gh, albo dowolny
        Brep z jedną dominującą zakrzywioną ścianą. Puste wejście: prosty loft
        sześciu kondygnacji nadziemnych masy Solna, bez skrętu.
    typ_wzoru : int @item optional
        0 romby (diagrid), 1 kwadraty, 2 trójkąty, 3 heksagony (domyślnie 0).
    typ_panelu : int @item optional
        0 płaski z otworem, 1 piramida, 2 ścięta piramida z otworem (domyślnie 2).
    kolumny : int @item optional
        Liczba pól wzoru wokół budynku; zaokrąglana w górę do parzystej,
        żeby wzór domykał się na szwie (co najmniej 4; domyślnie 36).
    rzedy : int @item optional
        Liczba rzędów wzoru od dołu do góry (co najmniej 2; domyślnie 14);
        heksagony mają rząd co 0.75, więc dają około rzedy / 0.75 rzędów.
    glebokosc_min_m : float @item optional
        Głębokość panelu przy intensywności 0, w metrach (domyślnie 0.10).
    glebokosc_max_m : float @item optional
        Głębokość panelu przy intensywności 1, w metrach (domyślnie 1.00).
    otwor_min : float @item optional
        Wielkość otworu jako ułamek panelu przy intensywności 1; panel mocno
        nasłoneczniony domyka się (domyślnie 0.15).
    otwor_max : float @item optional
        Wielkość otworu jako ułamek panelu przy intensywności 0 (domyślnie 0.70).
    azymut_slonca_deg : float @item optional
        Azymut słońca w stopniach, zgodnie z zegarem od północy; północ
        szkicu to oś +Y świata, krawędź KDP-1 (domyślnie 180, południe).
    wysokosc_slonca_deg : float @item optional
        Wysokość słońca nad horyzontem w stopniach (domyślnie 45).
    atraktory : Point3d @list optional
        Punkty, w których pobliżu panele robią się intensywne
        (domyślnie jeden punkt (25.0, -20.0, 12.0), na południe od masy Solna).
    zasieg_atraktora_m : float @item optional
        Zasięg wpływu atraktora (odchylenie funkcji Gaussa), w metrach (domyślnie 20).
    waga_slonca : float @item optional
        Waga ekspozycji na słońce w intensywności (domyślnie 0.5).
    waga_atraktora : float @item optional
        Waga bliskości atraktora w intensywności (domyślnie 0.5).
    paleta : int @item optional
        0 grafit, 1 miedź, 2 ocean: kolor od jasnego (intensywność 0) do
        ciemnego (intensywność 1). Domyślnie 0.
    kolor_jasny : Color @item optional
        Własny kolor przy intensywności 0; działa tylko razem z kolor_ciemny.
    kolor_ciemny : Color @item optional
        Własny kolor przy intensywności 1; działa tylko razem z kolor_jasny.

Outputs (Grasshopper):
    panele : Mesh
        Jedna siatka, osobne wierzchołki na panel, kolory wierzchołków wg intensywności.
    siatka : list[Polyline]
        Zamknięte obrysy paneli, czyli ramy wzoru.
    otwory : list[Polyline]
        Zamknięte obrysy otworów (typ_panelu 0 i 2), w kolejności paneli.
    intensywnosc_paneli : list[float]
        Intensywność od 0 do 1 dla każdego panelu, w kolejności paneli.
    srodki : list[Point3d]
        Środki paneli, w kolejności paneli.
    raport : list[str]
        Wzór i typ panelu, liczba paneli, osiągnięte zakresy głębokości
        i otworów, udział paneli intensywnych, atraktory, paleta,
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
    "typ_wzoru": 0,
    "typ_panelu": 2,
    "kolumny": 36,
    "rzedy": 14,
    "glebokosc_min_m": 0.10,
    "glebokosc_max_m": 1.00,
    "otwor_min": 0.15,
    "otwor_max": 0.70,
    "azymut_slonca_deg": 180.0,
    "wysokosc_slonca_deg": 45.0,
    "zasieg_atraktora_m": 20.0,
    "waga_slonca": 0.5,
    "waga_atraktora": 0.5,
    "paleta": 0,
}
DOMYSLNE_ATRAKTORY = [(25.0, -20.0, 12.0)]
NAZWY_WZORU = {0: "romby (diagrid)", 1: "kwadraty", 2: "trójkąty", 3: "heksagony"}
NAZWY_PANELU = {0: "płaski z otworem", 1: "piramida", 2: "ścięta piramida z otworem"}
PALETY = {
    0: ("grafit", (245, 244, 240), (58, 62, 70)),
    1: ("miedź", (250, 246, 238), (184, 115, 51)),
    2: ("ocean", (235, 245, 250), (20, 60, 110)),
}
TOL = 0.001
MIN_KOLUMNY = 4
MIN_RZEDY = 2
MIN_OTWOR = 0.02   # otwór nie może zniknąć do zera, bo pierścień panelu stałby się zdegenerowany
MAX_OTWOR = 0.95

# Domyślna masa "Solna": kopia tabeli PROSTOKATY z rozwiazania/05_szkic_bryly_rhino.py,
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
def kolumny_parzyste(kolumny):
    """Szachownica rombów domyka się na szwie tylko przy parzystej liczbie kolumn."""
    k = max(int(kolumny), MIN_KOLUMNY)
    return k + (k % 2)


def wzor_kwadraty(kol, rz, zamknieta):
    """Kwadraty: po jednym polu na węzeł siatki; współrzędne (u, v) w jednostkach siatki."""
    return [[(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
            for j in range(rz) for i in range(kol)]


def wzor_trojkaty(kol, rz, zamknieta):
    """Trójkąty: każdy kwadrat dzielony po przekątnej, kierunek przekątnej na przemian."""
    wynik = []
    for j in range(rz):
        for i in range(kol):
            a, b, c, d = (i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)
            if (i + j) % 2 == 0:
                wynik.extend([[a, b, c], [a, c, d]])
            else:
                wynik.extend([[a, b, d], [b, c, d]])
    return wynik


def wzor_romby(kol, rz, zamknieta):
    """Romby (diagrid) jak w karcie 07: szachownica rombów o narożach na sąsiednich
    węzłach plus trójkąty domykające rząd dolny i górny. Na powierzchni zamkniętej
    u >= kol zawija się przy odczycie."""
    kol = kolumny_parzyste(kol)
    ostatnia = kol if zamknieta else kol - 1
    wynik = []
    for j in range(1, rz):
        for i in range(0, ostatnia):
            if (i + j) % 2 != 0:
                continue
            wynik.append([(i, j), (i + 1, j - 1), (i + 2, j), (i + 1, j + 1)])
    for k in range(0, ostatnia):
        if k % 2 == 0:
            wynik.append([(k, 0), (k + 2, 0), (k + 1, 1)])
        if (k + rz) % 2 == 0:
            wynik.append([(k, rz), (k + 1, rz - 1), (k + 2, rz)])
    return wynik


def wzor_heksagony(kol, rz, zamknieta):
    """Sześciokąty w układzie plastra: szerokość 1 kolumny, wysokość 1 rzędu, rzędy
    co 0.75 rzędu, nieparzyste przesunięte o pół kolumny; brzegi dolny i górny
    przycięte do 0..rz, na powierzchni otwartej także lewy i prawy do 0..kol."""
    wynik = []
    j = 0
    while 0.75 * j <= rz - 0.25:
        vc = 0.75 * j + 0.5
        przesuniecie = 0.5 if j % 2 else 0.0
        pierwsza = -1 if (przesuniecie and not zamknieta) else 0
        for i in range(pierwsza, kol):
            uc = i + 0.5 + przesuniecie
            szesciokat = [(uc, vc + 0.5), (uc + 0.5, vc + 0.25), (uc + 0.5, vc - 0.25),
                          (uc, vc - 0.5), (uc - 0.5, vc - 0.25), (uc - 0.5, vc + 0.25)]
            szesciokat = [(u, min(max(v, 0.0), float(rz))) for u, v in szesciokat]
            if not zamknieta:
                szesciokat = [(min(max(u, 0.0), float(kol)), v) for u, v in szesciokat]
            wynik.append(szesciokat)
        j += 1
    return wynik


WZORY = {0: wzor_romby, 1: wzor_kwadraty, 2: wzor_trojkaty, 3: wzor_heksagony}


def wektor_slonca(azymut_deg, wysokosc_deg):
    """Jednostkowy wektor w stronę słońca: azymut od północy (+Y) zgodnie z zegarem."""
    az = math.radians(azymut_deg)
    alt = math.radians(wysokosc_deg)
    return (math.sin(az) * math.cos(alt), math.cos(az) * math.cos(alt), math.sin(alt))


def ekspozycja_panelu(normalna, slonce):
    """Ekspozycja od 0 do 1: dodatnia część iloczynu skalarnego normalnej i kierunku słońca."""
    iloczyn = normalna[0] * slonce[0] + normalna[1] * slonce[1] + normalna[2] * slonce[2]
    return min(max(iloczyn, 0.0), 1.0)


def wplyw_atraktora(odleglosc_m, zasieg_m):
    """Wpływ atraktora od 1 (w punkcie) do 0 (daleko): funkcja Gaussa o odchyleniu zasieg_m."""
    if zasieg_m <= 0.0:
        return 0.0
    return math.exp(-(odleglosc_m / zasieg_m) ** 2)


def najblizszy_wplyw(srodek, atraktory, zasieg_m):
    """Największy wpływ spośród atraktorów dla środka panelu (x, y, z)."""
    najlepszy = 0.0
    for ax, ay, az in atraktory:
        d = math.sqrt((srodek[0] - ax) ** 2 + (srodek[1] - ay) ** 2 + (srodek[2] - az) ** 2)
        najlepszy = max(najlepszy, wplyw_atraktora(d, zasieg_m))
    return najlepszy


def intensywnosc_panelu(ekspozycja, wplyw, waga_slonca, waga_atraktora):
    """Intensywność od 0 do 1: ważona suma ekspozycji i wpływu atraktora, przycięta."""
    return min(max(waga_slonca * ekspozycja + waga_atraktora * wplyw, 0.0), 1.0)


def glebokosc_panelu(intensywnosc, glebokosc_min_m, glebokosc_max_m):
    return glebokosc_min_m + (glebokosc_max_m - glebokosc_min_m) * intensywnosc


def otwor_panelu(intensywnosc, otwor_min, otwor_max):
    """Ułamek otworu: otwor_max przy intensywności 0, otwor_min przy 1 (panel intensywny
    domyka się); zawsze w granicach MIN_OTWOR..MAX_OTWOR."""
    o = otwor_max - (otwor_max - otwor_min) * intensywnosc
    return min(max(o, MIN_OTWOR), MAX_OTWOR)


def kolor_panelu(intensywnosc, jasny, ciemny):
    """Kolor (r, g, b) między jasnym (intensywność 0) a ciemnym (intensywność 1)."""
    e = min(max(intensywnosc, 0.0), 1.0)
    return tuple(int(round(a + (b - a) * e)) for a, b in zip(jasny, ciemny))


def linie_raportu(ust, liczba_paneli, intensywnosci, liczba_atraktorow, nazwa_palety, powierzchnia_m2,
                  pole_sciany_m2=0.0):
    """Składa raport z ustawień i wyników; linia głębokości tylko dla paneli
    wypychanych (typ 1 i 2), linia otworów tylko dla paneli z otworem (typ 0 i 2)."""
    mocne = sum(1 for e in intensywnosci if e > 0.5)
    udzial = (100.0 * mocne / len(intensywnosci)) if intensywnosci else 0.0
    glebokosci = [glebokosc_panelu(e, ust["glebokosc_min_m"], ust["glebokosc_max_m"]) for e in intensywnosci] or [0.0]
    otwory = [otwor_panelu(e, ust["otwor_min"], ust["otwor_max"]) for e in intensywnosci] or [0.0]
    linie = [
        "wzór: {}; panel: {}".format(NAZWY_WZORU[ust["typ_wzoru"]], NAZWY_PANELU[ust["typ_panelu"]]),
        "paneli: {} na ścianie o polu {:.0f} m2".format(liczba_paneli, pole_sciany_m2),
    ]
    if ust["typ_panelu"] in (1, 2):
        linie.append("głębokość paneli (osiągnięta): {:.2f}-{:.2f} m przy zakresie {:.2f}-{:.2f} m".format(
            min(glebokosci), max(glebokosci), ust["glebokosc_min_m"], ust["glebokosc_max_m"]))
    if ust["typ_panelu"] in (0, 2):
        linie.append("otwory (osiągnięte): {:.2f}-{:.2f} panelu przy zakresie {:.2f}-{:.2f}".format(
            min(otwory), max(otwory), ust["otwor_min"], ust["otwor_max"]))
    linie.extend([
        "panele o intensywności powyżej 0.5: {} ({:.1f} %)".format(mocne, udzial),
        ("atraktory: {}, zasięg {:.1f} m; wagi: słońce {:.2f}, atraktor {:.2f}".format(
            liczba_atraktorow, ust["zasieg_atraktora_m"], ust["waga_slonca"], ust["waga_atraktora"])
         if ust["zasieg_atraktora_m"] > 0.0 else
         "atraktory: {} bez wpływu (zasięg {:.1f} m nie jest dodatni); wagi: słońce {:.2f}, atraktor {:.2f}".format(
            liczba_atraktorow, ust["zasieg_atraktora_m"], ust["waga_slonca"], ust["waga_atraktora"])),
        "paleta: {}".format(nazwa_palety),
        "powierzchnia elewacji (przybliżona, bez głębokości): {:.0f} m2".format(powierzchnia_m2),
        "heurystyka: iloczyn skalarny normalnej i kierunku słońca plus bliskość atraktora, nie analiza nasłonecznienia",
    ])
    return linie


def ustawienia_z_wejsc(czytaj, bledy):
    """Zbiera ustawienia z wejść (funkcja czytaj(nazwa, domyslna)), przycina wartości
    spoza zakresu do domyślnych i dopisuje ostrzeżenia."""
    ust = {}
    for nazwa, domyslna in DOMYSLNE.items():
        wartosc = czytaj(nazwa, domyslna)
        ust[nazwa] = int(wartosc) if isinstance(domyslna, int) else float(wartosc)
    for klucz, nazwy in (("typ_wzoru", NAZWY_WZORU), ("typ_panelu", NAZWY_PANELU), ("paleta", {k: v[0] for k, v in PALETY.items()})):
        if ust[klucz] not in nazwy:
            bledy.append("{} {} nieznany - użyto {} ({})".format(klucz, ust[klucz], DOMYSLNE[klucz], nazwy[DOMYSLNE[klucz]]))
            ust[klucz] = DOMYSLNE[klucz]
    if ust["kolumny"] < MIN_KOLUMNY:
        bledy.append("kolumny poniżej {} - użyto {}".format(MIN_KOLUMNY, MIN_KOLUMNY))
    ust["kolumny"] = kolumny_parzyste(ust["kolumny"])
    if ust["rzedy"] < MIN_RZEDY:
        bledy.append("rzedy poniżej {} - użyto {}".format(MIN_RZEDY, MIN_RZEDY))
        ust["rzedy"] = MIN_RZEDY
    if ust["glebokosc_max_m"] < ust["glebokosc_min_m"]:
        ust["glebokosc_min_m"], ust["glebokosc_max_m"] = ust["glebokosc_max_m"], ust["glebokosc_min_m"]
        bledy.append("glebokosc_max_m mniejsza od glebokosc_min_m - zamieniono")
    if ust["otwor_max"] < ust["otwor_min"]:
        ust["otwor_min"], ust["otwor_max"] = ust["otwor_max"], ust["otwor_min"]
        bledy.append("otwor_max mniejszy od otwor_min - zamieniono")
    return ust


# ---------------------------------------------------------------------------
# Geometria (RhinoCommon)
# ---------------------------------------------------------------------------
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
    """Prosty loft domyślnej masy Solna (bez skrętu i zaokrąglenia): parter skopiowany
    na teren, potem każdy strop nadziemny, pokrywy, normalne na zewnątrz."""
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


def _pole_sciany(sciana):
    brep = sciana.DuplicateFace(False)
    amp = rg.AreaMassProperties.Compute(brep) if brep is not None else None
    return amp.Area if amp is not None else 0.0


def _wybierz_sciane(bryla):
    """Największa niepłaska ściana; gdy wszystkie są płaskie, największa w ogóle."""
    kandydaci = [(sciana.IsPlanar(TOL), _pole_sciany(sciana), sciana) for sciana in bryla.Faces]
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


def _srodek(punkty):
    # Liczony na liczbach, nie na Point3d: pod pythonnet Point3d + Point3d trafia
    # w przeciążenie Point3d + Vector3d i rzuca ArgumentException.
    n = float(len(punkty))
    return rg.Point3d(sum(p.X for p in punkty) / n, sum(p.Y for p in punkty) / n, sum(p.Z for p in punkty) / n)


def _pole_wieloboku(punkty):
    """Przybliżone pole wieloboku z iloczynów wektorowych (wielobok nie musi być płaski)."""
    if len(punkty) < 3:
        return 0.0
    suma = rg.Vector3d(0.0, 0.0, 0.0)
    for k in range(1, len(punkty) - 1):
        suma += rg.Vector3d.CrossProduct(punkty[k] - punkty[0], punkty[k + 1] - punkty[0])
    return 0.5 * suma.Length


def _polilinia(punkty):
    # Polyline budowana przez Add, bo konstruktor z listą Pythona nie ma
    # pasującego przeciążenia pod pythonnet.
    pl = rg.Polyline()
    for p in punkty + [punkty[0]]:
        pl.Add(p)
    return pl


def _dodaj_trojkat(mesh, a, b, c, normalna, kolor):
    """Trójkąt o trzech nowych wierzchołkach, nawinięty zgodnie z normalną."""
    if rg.Vector3d.CrossProduct(b - a, c - a) * normalna < 0.0:
        b, c = c, b
    idx = [mesh.Vertices.Add(p.X, p.Y, p.Z) for p in (a, b, c)]
    for _ in idx:
        mesh.VertexColors.Add(kolor[0], kolor[1], kolor[2])
    mesh.Faces.AddFace(idx[0], idx[1], idx[2])


def _dodaj_pierscien(mesh, zewn, wewn, normalna, kolor):
    """Pas czworokątów między obrysem zewnętrznym a wewnętrznym (ten sam licznik naroży)."""
    n = len(zewn)
    for k in range(n):
        a, b = zewn[k], zewn[(k + 1) % n]
        c, d = wewn[(k + 1) % n], wewn[k]
        _dodaj_trojkat(mesh, a, b, c, normalna, kolor)
        _dodaj_trojkat(mesh, a, c, d, normalna, kolor)


def _obrys_wewnetrzny(naroza, srodek, ulamek, normalna, glebokosc):
    """Naroża otworu: obrys zewnętrzny przeskalowany do środka o ulamek i wypchnięty
    wzdłuż normalnej o glebokosc (0 dla panelu płaskiego)."""
    wynik = []
    for p in naroza:
        q = srodek + (p - srodek) * ulamek + normalna * glebokosc
        wynik.append(q)
    return wynik


def zbuduj_elewacje(bryla, ust, atraktory, jasny, ciemny):
    """Buduje panele na dominującej ścianie bryły. Zwraca słownik z kluczami
    panele, siatka, otwory, intensywnosc_paneli, srodki, raport, bledy."""
    bledy = []
    wynik = {"panele": None, "siatka": [], "otwory": [], "intensywnosc_paneli": [], "srodki": [],
             "powierzchnia": 0.0, "pole_sciany": 0.0, "bledy": bledy}
    if bryla is None or bryla.Faces.Count == 0:
        bledy.append("brak bryły - podłącz wyjście bryla z komponentu 06_bryla_gh")
        return wynik
    sciana = _wybierz_sciane(bryla)
    if sciana is None:
        bledy.append("bryła nie ma ścian do opanelowania")
        return wynik
    wynik["pole_sciany"] = _pole_sciany(sciana)

    # 1) Kierunki parametryzacji: zamknięty biegnie wokół budynku, drugi do góry.
    kier_wokolo = 0 if sciana.IsClosed(0) else (1 if sciana.IsClosed(1) else 0)
    kier_gora = 1 - kier_wokolo
    zamknieta = sciana.IsClosed(kier_wokolo)
    dom_w = sciana.Domain(kier_wokolo)
    dom_g = sciana.Domain(kier_gora)

    def punkt_i_normalna(uw, vg):
        if kier_wokolo == 0:
            return sciana.PointAt(uw, vg), _jednostkowy(sciana.NormalAt(uw, vg))
        return sciana.PointAt(vg, uw), _jednostkowy(sciana.NormalAt(vg, uw))

    z_dol = punkt_i_normalna(dom_w.Mid, dom_g.T0)[0].Z
    z_gora = punkt_i_normalna(dom_w.Mid, dom_g.T1)[0].Z
    if z_gora < z_dol:
        dom_g = rg.Interval(dom_g.T1, dom_g.T0)

    kol, rz = ust["kolumny"], ust["rzedy"]

    def wezel(u, v):
        """Punkt i normalna dla współrzędnych siatki (u w kolumnach, v w rzędach); u zawija się."""
        un = u / float(kol)
        un = un % 1.0 if zamknieta else min(max(un, 0.0), 1.0)
        vn = min(max(v / float(rz), 0.0), 1.0)
        return punkt_i_normalna(dom_w.ParameterAt(un), dom_g.ParameterAt(vn))

    # Normalne odwracamy, gdy próbka wskazuje do środka bryły.
    srodek_bryly = bryla.GetBoundingBox(True).Center
    probka_p, probka_n = wezel(0.0, rz / 2.0)
    odwroc = (probka_p - srodek_bryly) * probka_n < 0.0

    # 2) Wielokąty wzoru i panele.
    wieloboki = WZORY[ust["typ_wzoru"]](kol, rz, zamknieta)
    slonce = wektor_slonca(ust["azymut_slonca_deg"], ust["wysokosc_slonca_deg"])
    mesh = rg.Mesh()
    ramy, otwory, intensywnosci, srodki = [], [], [], []
    powierzchnia = 0.0
    for wielobok in wieloboki:
        naroza, normalne = [], []
        for u, v in wielobok:
            p, n = wezel(u, v)
            naroza.append(p)
            normalne.append(-n if odwroc else n)
        pole_panelu = _pole_wieloboku(naroza)
        if pole_panelu < 1e-6:
            continue   # przycięty sześciokąt zdegenerowany do odcinka
        suma_n = rg.Vector3d(0.0, 0.0, 0.0)
        for n in normalne:
            suma_n += n
        normalna = _jednostkowy(suma_n)
        srodek = _srodek(naroza)

        eks = ekspozycja_panelu((normalna.X, normalna.Y, normalna.Z), slonce)
        wplyw = najblizszy_wplyw((srodek.X, srodek.Y, srodek.Z), atraktory, ust["zasieg_atraktora_m"])
        inten = intensywnosc_panelu(eks, wplyw, ust["waga_slonca"], ust["waga_atraktora"])
        glebokosc = glebokosc_panelu(inten, ust["glebokosc_min_m"], ust["glebokosc_max_m"])
        kolor = kolor_panelu(inten, jasny, ciemny)

        if ust["typ_panelu"] == 1:
            wierzcholek = srodek + normalna * glebokosc
            for k in range(len(naroza)):
                _dodaj_trojkat(mesh, wierzcholek, naroza[k], naroza[(k + 1) % len(naroza)], normalna, kolor)
        else:
            ulamek = otwor_panelu(inten, ust["otwor_min"], ust["otwor_max"])
            wysuniecie = glebokosc if ust["typ_panelu"] == 2 else 0.0
            wewn = _obrys_wewnetrzny(naroza, srodek, ulamek, normalna, wysuniecie)
            _dodaj_pierscien(mesh, naroza, wewn, normalna, kolor)
            otwory.append(_polilinia(wewn))

        ramy.append(_polilinia(naroza))
        intensywnosci.append(inten)
        srodki.append(srodek)
        powierzchnia += pole_panelu

    mesh.Normals.ComputeNormals()
    mesh.Compact()
    if not mesh.IsValid:
        bledy.append("siatka paneli nie przeszła walidacji Rhino (Mesh.IsValid = False)")

    wynik.update({"panele": mesh, "siatka": ramy, "otwory": otwory, "intensywnosc_paneli": intensywnosci,
                  "srodki": srodki, "powierzchnia": powierzchnia})
    return wynik


# ---------------------------------------------------------------------------
# Komponent Grasshopper - wejścia czytane z globals(), żeby plik działał także
# uruchomiony poza komponentem; niepodpięte wejście to None albo pusta lista.
# ---------------------------------------------------------------------------
def _wejscie(nazwa, domyslna):
    wartosc = globals().get(nazwa)
    return domyslna if wartosc is None else wartosc


panele = None
siatka = []
otwory = []
intensywnosc_paneli = []
srodki = []
raport = []

if not W_RHINO:
    raport = ["uwaga: import Rhino nie powiódł się - komponent działa poza Rhino albo w nieobsługiwanej wersji."]
else:
    _uwagi = []
    _ust = ustawienia_z_wejsc(_wejscie, _uwagi)

    _bryla = _wejscie("bryla", None)
    if _bryla is None:
        # Wklejony komponent bez kabli ma od razu coś pokazać.
        _bryla = bryla_domyslna(_uwagi)
        _uwagi.insert(0, "wejście bryla puste - użyto loftu domyślnej masy Solna bez skrętu; "
                         "podłącz wyjście bryla z komponentu 06_bryla_gh albo bryla_zaawansowana_gh")

    _punkty = _wejscie("atraktory", [])
    if not isinstance(_punkty, (list, tuple)):
        _punkty = [_punkty]
    _atraktory = [(float(p.X), float(p.Y), float(p.Z)) for p in _punkty if p is not None]
    if not _atraktory:
        _atraktory = list(DOMYSLNE_ATRAKTORY)
        _uwagi.append("wejście atraktory puste - użyto punktu domyślnego ({:.1f}, {:.1f}, {:.1f})".format(*DOMYSLNE_ATRAKTORY[0]))

    _nazwa_palety, _jasny, _ciemny = PALETY[_ust["paleta"]]
    _kj, _kc = _wejscie("kolor_jasny", None), _wejscie("kolor_ciemny", None)
    if _kj is not None and _kc is not None:
        _jasny, _ciemny = (_kj.R, _kj.G, _kj.B), (_kc.R, _kc.G, _kc.B)
        _nazwa_palety = "kolory własne"
    elif _kj is not None or _kc is not None:
        _uwagi.append("podano tylko jeden z kolorów kolor_jasny/kolor_ciemny - zostaje paleta {}".format(_nazwa_palety))

    if _bryla is None:
        raport = ["uwaga: " + u for u in _uwagi]
    else:
        _wynik = zbuduj_elewacje(_bryla, _ust, _atraktory, _jasny, _ciemny)
        panele = _wynik["panele"]
        siatka = _wynik["siatka"]
        otwory = _wynik["otwory"]
        intensywnosc_paneli = _wynik["intensywnosc_paneli"]
        srodki = _wynik["srodki"]
        raport = (["uwaga: " + u for u in _uwagi] + ["uwaga: " + b for b in _wynik["bledy"]]
                  + linie_raportu(_ust, len(siatka), intensywnosc_paneli, len(_atraktory), _nazwa_palety,
                                  _wynik["powierzchnia"], _wynik["pole_sciany"]))


def _selftest():
    """Sprawdza czystą arytmetykę bez Rhino (wywołanie: --test)."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    # Wzory: liczby pól i zakresy współrzędnych siatki.
    assert len(wzor_kwadraty(36, 14, True)) == 36 * 14
    assert len(wzor_trojkaty(36, 14, True)) == 2 * 36 * 14
    romby = wzor_romby(36, 12, True)
    assert len(romby) == 198 + 36, len(romby)
    assert len(wzor_romby(35, 12, True)) == 198 + 36, "nieparzyste kolumny mają być zaokrąglone do parzystych"
    assert max(u for w in romby for u, v in w) == 37, "romb na szwie sięga u = kol + 1 i zawija się przy odczycie"
    romby_otwarte = wzor_romby(36, 12, False)
    assert max(u for w in romby_otwarte for u, v in w) == 36 and len(romby_otwarte) < len(romby)
    heks = wzor_heksagony(36, 14, True)
    assert len(heks) == 36 * 19, len(heks)   # rzędy co 0.75: j = 0..18 spełnia 0.75 j <= 13.75
    assert all(len(w) == 6 for w in heks)
    assert all(0.0 <= v <= 14.0 for w in heks for u, v in w)
    assert max(u for w in heks for u, v in w) > 36.0, "sześciokąt na szwie zawija się przy odczycie"
    heks_otwarte = wzor_heksagony(36, 14, False)
    assert len(heks_otwarte) == 36 * 19 + 9, len(heks_otwarte)   # 9 nieparzystych rzędów dostaje pół-sześciokąt przy u = 0
    assert all(0.0 <= u <= 36.0 for w in heks_otwarte for u, v in w)
    for typ in WZORY:
        assert len(WZORY[typ](8, 4, True)) > 0

    s = wektor_slonca(180.0, 45.0)
    assert all(abs(a - b) < 1e-4 for a, b in zip(s, (0.0, -0.70711, 0.70711))), s
    assert ekspozycja_panelu((0.0, 1.0, 0.0), (0.0, -1.0, 0.0)) == 0.0
    assert ekspozycja_panelu((0.0, -1.0, 0.0), (0.0, -1.0, 0.0)) == 1.0

    assert wplyw_atraktora(0.0, 20.0) == 1.0 and wplyw_atraktora(20.0, 20.0) < 0.37 and wplyw_atraktora(100.0, 20.0) < 1e-9
    assert wplyw_atraktora(5.0, 0.0) == 0.0
    assert najblizszy_wplyw((0.0, 0.0, 0.0), [(100.0, 0.0, 0.0), (0.0, 0.0, 0.0)], 20.0) == 1.0
    assert intensywnosc_panelu(1.0, 1.0, 0.5, 0.5) == 1.0 and intensywnosc_panelu(1.0, 1.0, 0.8, 0.8) == 1.0
    assert abs(intensywnosc_panelu(0.5, 0.0, 0.5, 0.5) - 0.25) < 1e-12
    assert abs(glebokosc_panelu(0.5, 0.1, 1.0) - 0.55) < 1e-12
    assert abs(otwor_panelu(0.0, 0.15, 0.7) - 0.7) < 1e-12 and abs(otwor_panelu(1.0, 0.15, 0.7) - 0.15) < 1e-12
    assert otwor_panelu(1.0, 0.0, 0.7) == MIN_OTWOR, "otwór nie może zniknąć do zera"
    assert kolor_panelu(0.0, *PALETY[0][1:]) == (245, 244, 240) and kolor_panelu(1.0, *PALETY[1][1:]) == (184, 115, 51)

    bledy = []
    ust = ustawienia_z_wejsc(lambda nazwa, domyslna: {"typ_wzoru": 9, "paleta": 5, "kolumny": 35,
                                                      "otwor_min": 0.8, "otwor_max": 0.2}.get(nazwa, domyslna), bledy)
    assert ust["typ_wzoru"] == 0 and ust["paleta"] == 0 and ust["kolumny"] == 36, ust
    assert ust["otwor_min"] == 0.2 and ust["otwor_max"] == 0.8 and len(bledy) == 3, (ust, bledy)

    linie = linie_raportu(ust, 234, [0.0, 0.6, 1.0, 0.2], 1, "grafit", 2500.0, 2600.0)
    assert linie[0] == "wzór: romby (diagrid); panel: ścięta piramida z otworem", linie[0]
    assert linie[1] == "paneli: 234 na ścianie o polu 2600 m2", linie[1]
    assert linie[2].startswith("głębokość paneli (osiągnięta): 0.10-1.00 m"), linie[2]
    assert linie[3].startswith("otwory (osiągnięte): 0.20-0.80"), linie[3]
    assert linie[4] == "panele o intensywności powyżej 0.5: 2 (50.0 %)", linie[4]
    assert "heurystyka" in linie[-1]
    ust["typ_panelu"] = 1
    assert not any(l.startswith("otwory") for l in linie_raportu(ust, 1, [0.5], 1, "grafit", 1.0))
    ust["typ_panelu"] = 0
    assert not any(l.startswith("głębokość") for l in linie_raportu(ust, 1, [0.5], 1, "grafit", 1.0)), \
        "panel płaski nie ma głębokości, więc raport jej nie obiecuje"
    ust["zasieg_atraktora_m"] = 0.0
    assert any(l.startswith("atraktory: 1 bez wpływu") for l in linie_raportu(ust, 1, [0.5], 1, "grafit", 1.0)), \
        "zasięg 0 to brak działania atraktorów, raport ma to mówić"
    ust["zasieg_atraktora_m"] = 20.0
    bledy = []
    ust = ustawienia_z_wejsc(lambda nazwa, domyslna: {"kolumny": 2, "rzedy": 1}.get(nazwa, domyslna), bledy)
    assert ust["kolumny"] == MIN_KOLUMNY and ust["rzedy"] == MIN_RZEDY and len(bledy) == 2, (ust, bledy)

    assert len(DOMYSLNA_MASA) == 12
    kond = [(x1 - x0) * (y1 - y0) for w, x0, y0, x1, y1, z in DOMYSLNA_MASA if w == "Kondygnacje"]
    assert kond == [1400, 962, 962, 962, 962, 782, 726], kond
    print("SELFTEST OK")


if __name__ == "__main__" and not W_RHINO and "--test" in sys.argv:
    _selftest()

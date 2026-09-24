#! python 3
"""
06_bryla_gh - parametryczna bryła z obrysów kondygnacji
=======================================================
Purpose:
    Karta 06. Zamienia prostokątne obrysy kondygnacji (warstwa Kondygnacje
    ze szkicu 05_szkic_bryly_rhino.py) w jedną gładką, skręconą i
    wybrzuszoną bryłę o zaokrąglonych narożach, a potem tnie ją z powrotem
    na płyty kondygnacji, które można podpiąć do kontroli MPZP z karty 05.
    Bez podpiętego wejścia buduje bryłę z domyślnej masy Solna wbudowanej
    w skrypt, żeby wklejony komponent od razu coś pokazywał.

Inputs (Grasshopper):
    kondygnacje : Curve @list optional
        Po jednej zamkniętej płaskiej krzywej na kondygnację, na wysokości
        stropu. Krzywa o najwyższym Z <= 0 to kondygnacja podziemna: nie
        wchodzi do bryły i przechodzi bez zmian do kondygnacje_nowe.
        Puste wejście: siedem kondygnacji masy Solna z tabeli DOMYSLNA_MASA,
        z ostrzeżeniem w pierwszej linii raportu.
    skret_deg : float @item optional
        Całkowity skręt bryły od terenu do dachu, w stopniach, wokół osi
        pionowej przez środek obrysu parteru (domyślnie 12).
    wybrzuszenie : float @item optional
        Wybrzuszenie w połowie wysokości: każdy przekrój skaluje się wokół
        własnego środka o 1 + wybrzuszenie * sin(pi * t), gdzie t = z / z_max
        (domyślnie 0.10).
    zaokraglenie : float @item optional
        Zaokrąglenie naroży od 0 do 1; promień = zaokraglenie * 0.49 * krótszy
        bok obrysu (domyślnie 0.6).
    pochylenie_x_m : float @item optional
        Przesunięcie szczytu bryły w metrach wzdłuż osi X świata (domyślnie 0).
    pochylenie_y_m : float @item optional
        Przesunięcie szczytu bryły w metrach wzdłuż osi Y świata (domyślnie 0).
    punkty_profilu : int @item optional
        Liczba punktów kontrolnych każdego przebudowanego przekroju (domyślnie 32).
    kontury_co_m : float @item optional
        Rozstaw poziomych konturów do podglądu, w metrach; 0 wyłącza (domyślnie 0.5).

Outputs (Grasshopper):
    bryla : Brep
        Zamknięta bryła z pokrywami, zorientowana na zewnątrz.
    kondygnacje_nowe : list[Curve]
        Krzywe podziemne bez zmian, potem nowe obrysy kondygnacji na
        wysokościach stropów; pasuje do wejścia kondygnacje w komponencie 05.
    zabudowa_nowa : Curve
        Obrys zabudowy: suma nowych obrysów nadziemnych zrzutowana na Z = 0;
        pasuje do wejścia zabudowa w komponencie 05.
    plyty : list[Brep]
        Płaskie płyty kondygnacji nadziemnych zbudowane z nowych obrysów
        (garaż nie dostaje płyty, bo nie należy do bryły).
    kontury : list[Curve]
        Poziome kontury bryły do podglądu.
    raport : list[str]
        Powierzchnie nowych kondygnacji wobec szkicu, suma Po, wysokość,
        liczba kondygnacji, obrys, objętość i ostrzeżenia.

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


# Wartości domyślne suwaków; komponent używa ich, gdy wejście jest niepodpięte.
DOMYSLNE = {
    "skret_deg": 12.0,
    "wybrzuszenie": 0.10,
    "zaokraglenie": 0.6,
    "pochylenie_x_m": 0.0,
    "pochylenie_y_m": 0.0,
    "punkty_profilu": 32,
    "kontury_co_m": 0.5,
}
TOL = 0.001            # tolerancja modelu w metrach
KAT_TOL = 0.01         # tolerancja kątowa w radianach
CIECIE_PONIZEJ_M = 0.001   # cięcie 1 mm pod stropem, żeby nie trafić w pokrywę bryły
MIN_PUNKTY_PROFILU = 8

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
def skala(t, wybrzuszenie):
    """Współczynnik skali przekroju na wysokości względnej t (0 - teren, 1 - dach)."""
    return 1.0 + wybrzuszenie * math.sin(math.pi * t)


def kat_skretu_rad(t, skret_deg):
    """Kąt skrętu przekroju na wysokości względnej t, w radianach."""
    return math.radians(skret_deg) * t


def promien_zaokraglenia(szerokosc, glebokosc, zaokraglenie):
    """Promień zaokrąglenia naroży: zaokraglenie * 0.49 * krótszy bok, czyli przy
    zaokraglenie 1 niemal połowa krótszego boku (0.49, nie 0.5), tak by dwa
    zaokrąglenia nie zeszły się na krótszej krawędzi."""
    if zaokraglenie <= 0.0:
        return 0.0
    return min(max(zaokraglenie, 0.0), 1.0) * 0.49 * min(szerokosc, glebokosc)


def podziel_wg_z(pary):
    """Dzieli pary (z, obiekt) na (podziemne, nadziemne) według rzędnej z;
    zwraca same obiekty, każda lista rosnąco po z. Z <= 0 to kondygnacja podziemna."""
    posortowane = sorted(pary, key=lambda para: para[0])
    podziemne = [obiekt for z, obiekt in posortowane if z <= 0.0]
    nadziemne = [obiekt for z, obiekt in posortowane if z > 0.0]
    return podziemne, nadziemne


def wysokosci_przekrojow(z_nadziemne):
    """Rzędne przekrojów loftu: teren (0.0) i każdy strop nadziemny rosnąco."""
    return [0.0] + sorted(z_nadziemne)


def linia_kondygnacji(nr, nowa_m2, szkic_m2):
    return "kondygnacja {}: {:.1f} m2 (szkic {:.1f} m2)".format(nr, nowa_m2, szkic_m2)


def linie_raportu(pola_nowe, pola_szkicu, wysokosc_m, objetosc_m3, obrys_m2):
    """Składa raport z pól nowych kondygnacji, wysokości, obrysu i objętości."""
    linie = []
    for i, (nowa, szkic) in enumerate(zip(pola_nowe, pola_szkicu)):
        linie.append(linia_kondygnacji(i + 1, nowa, szkic))
    linie.append("suma Po (nadziemne): {:.1f} m2 (szkic {:.1f} m2)".format(
        sum(pola_nowe), sum(pola_szkicu)))
    linie.append("wysokość: {:.1f} m / {} kond.".format(wysokosc_m, len(pola_nowe)))
    linie.append("obrys zabudowy: {:.1f} m2".format(obrys_m2))
    linie.append("objętość: {:.0f} m3".format(objetosc_m3))
    return linie


# ---------------------------------------------------------------------------
# Geometria (RhinoCommon)
# ---------------------------------------------------------------------------
def _lista(krzywe):
    """Metody RhinoCommon oczekujące IEnumerable<Curve> potrzebują listy .NET,
    nie listy Pythona - w każdym środowisku CPython z pythonnet."""
    lista = List[rg.Curve]()
    for krzywa in krzywe:
        lista.Add(krzywa)
    return lista


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


def _pole(krzywa):
    amp = rg.AreaMassProperties.Compute(krzywa)
    return amp.Area if amp is not None else 0.0


def _srodek(krzywa):
    amp = rg.AreaMassProperties.Compute(krzywa)
    if amp is not None:
        return amp.Centroid
    return krzywa.GetBoundingBox(True).Center


def _gora(krzywa):
    return krzywa.GetBoundingBox(True).Max.Z


def _przeciwnie_do_zegara(krzywa):
    """Wszystkie przekroje muszą mieć ten sam kierunek, inaczej loft się skręca."""
    if krzywa.ClosedCurveOrientation(rg.Vector3d.ZAxis) == rg.CurveOrientation.Clockwise:
        krzywa.Reverse()
    return krzywa


def _zaokraglij(krzywa, zaokraglenie, bledy):
    # Boki brane z prostopadłościanu w osiach świata, przed skrętem: dla szkicu
    # "Solna" (prostokąty w osiach) to dokładne wymiary; dla obrysu obróconego
    # w planie bok jest przeszacowany i fillet może zwrócić None - wtedy
    # przekrój zostaje ostry, z ostrzeżeniem, a loft i tak się buduje.
    bb = krzywa.GetBoundingBox(True)
    promien = promien_zaokraglenia(bb.Max.X - bb.Min.X, bb.Max.Y - bb.Min.Y, zaokraglenie)
    if promien <= 0.0:
        return krzywa
    wynik = rg.Curve.CreateFilletCornersCurve(krzywa, promien, TOL, KAT_TOL)
    if wynik is None:
        bledy.append("zaokrąglenie o promieniu {:.2f} m nie powiodło się, przekrój zostaje ostry".format(promien))
        return krzywa
    return wynik


def _ustaw_szew(krzywa, os_xy, kierunek_rad, z):
    """Przesuwa początek krzywej zamkniętej w stronę kierunek_rad od osi, żeby
    szwy kolejnych przekrojów leżały nad sobą (po uwzględnieniu skrętu)."""
    cel = rg.Point3d(os_xy.X + 1000.0 * math.cos(kierunek_rad),
                     os_xy.Y + 1000.0 * math.sin(kierunek_rad), z)
    rc, t = krzywa.ClosestPoint(cel)
    if rc:
        krzywa.ChangeClosedCurveSeam(t)
    return krzywa


def _przekroj_na_wysokosci(bryla, z):
    """Zamknięty obrys bryły na rzędnej z (największy, gdy jest ich kilka)."""
    plaszczyzna = rg.Plane(rg.Point3d(0.0, 0.0, z), rg.Vector3d.ZAxis)
    rc, krzywe, _punkty = rg.Intersect.Intersection.BrepPlane(bryla, plaszczyzna, TOL)
    if not rc or krzywe is None or len(krzywe) == 0:
        return None
    polaczone = rg.Curve.JoinCurves(krzywe, TOL)
    kandydaci = [c for c in polaczone if c.IsClosed]
    # Otwarte fragmenty nie są obrysem kondygnacji: lepiej brak przekroju
    # (i ostrzeżenie u wywołującego) niż płyta o polu 0 w kontroli z karty 05.
    return max(kandydaci, key=_pole) if kandydaci else None


def _obrys(krzywe_nadziemne, bledy):
    """Rzut wszystkich nowych obrysów na teren i ich suma logiczna."""
    rzuty = []
    for krzywa in krzywe_nadziemne:
        rzut = rg.Curve.ProjectToPlane(krzywa, rg.Plane.WorldXY)
        if rzut is not None:
            rzuty.append(rzut)
    if not rzuty:
        return None
    if len(rzuty) == 1:
        return rzuty[0]
    suma = rg.Curve.CreateBooleanUnion(_lista(rzuty), TOL)
    if suma is None or len(suma) == 0:
        bledy.append("suma logiczna rzutów nie powiodła się, obrys = największy rzut")
        return max(rzuty, key=_pole)
    return max(list(suma), key=_pole)


def zbuduj_bryle(kondygnacje, skret_deg, wybrzuszenie, zaokraglenie,
                 pochylenie_x_m, pochylenie_y_m, punkty_profilu, kontury_co_m):
    """Buduje bryłę i płyty z listy krzywych kondygnacji. Zwraca słownik z
    kluczami bryla, kondygnacje_nowe, zabudowa_nowa, plyty, kontury, raport, bledy."""
    bledy = []
    wynik = {"bryla": None, "kondygnacje_nowe": [], "zabudowa_nowa": None,
             "plyty": [], "kontury": [], "raport": [], "bledy": bledy}

    # Pojedyncza krzywa zamiast listy (wejście ustawione na item) też ma działać.
    if kondygnacje is not None and not isinstance(kondygnacje, (list, tuple)):
        kondygnacje = [kondygnacje]
    krzywe = [k for k in kondygnacje if k is not None]
    podziemne, nadziemne = podziel_wg_z([(_gora(k), k) for k in krzywe])
    if len(nadziemne) < 2:
        bledy.append("potrzebne są co najmniej dwie kondygnacje nadziemne (Z > 0), jest {}".format(len(nadziemne)))
        return wynik

    z_stropow = [_gora(k) for k in nadziemne]
    z_max = z_stropow[-1]
    pola_szkicu = [_pole(k) for k in nadziemne]

    # 1) Sekcje loftu: parter skopiowany na teren (t = 0), potem każdy strop.
    zrodla = list(zip([nadziemne[0]] + nadziemne, wysokosci_przekrojow(z_stropow)))
    os_xy = _srodek(nadziemne[0])
    kierunek_0 = None
    przekroje = []
    for krzywa, z in zrodla:
        sekcja = krzywa.DuplicateCurve()
        dz = z - _gora(sekcja)
        if abs(dz) > TOL:
            sekcja.Transform(rg.Transform.Translation(0.0, 0.0, dz))
        t = z / z_max if z_max > 0.0 else 0.0

        sekcja = _przeciwnie_do_zegara(sekcja)
        sekcja = _zaokraglij(sekcja, zaokraglenie, bledy).ToNurbsCurve()

        srodek = _srodek(sekcja)
        sekcja.Transform(rg.Transform.Scale(srodek, skala(t, wybrzuszenie)))
        kat = kat_skretu_rad(t, skret_deg)
        sekcja.Transform(rg.Transform.Rotation(kat, rg.Vector3d.ZAxis, rg.Point3d(os_xy.X, os_xy.Y, z)))
        sekcja.Transform(rg.Transform.Translation(pochylenie_x_m * t, pochylenie_y_m * t, 0.0))

        # 2) Szew: kierunek początku parteru obrócony o skręt danego przekroju.
        if kierunek_0 is None:
            p0 = sekcja.PointAtStart
            kierunek_0 = math.atan2(p0.Y - os_xy.Y, p0.X - os_xy.X)
        _ustaw_szew(sekcja, os_xy, kierunek_0 + kat, z)
        przekroje.append(sekcja)

    # 3) Loft z przebudową przekrojów do wspólnej liczby punktów, pokrywy, orientacja.
    punkty = max(int(punkty_profilu), MIN_PUNKTY_PROFILU)
    breps = rg.Brep.CreateFromLoftRebuild(_lista(przekroje), rg.Point3d.Unset, rg.Point3d.Unset,
                                          rg.LoftType.Normal, False, punkty)
    if breps is None or len(breps) == 0:
        bledy.append("loft nie powiódł się - sprawdź, czy krzywe są zamknięte i płaskie")
        return wynik
    if len(breps) > 1:
        bledy.append("loft zwrócił {} powierzchni, użyto pierwszej".format(len(breps)))
    bryla = breps[0]
    zamknieta = bryla.CapPlanarHoles(TOL)
    if zamknieta is None:
        bledy.append("nie udało się zamknąć bryły pokrywami (CapPlanarHoles)")
    else:
        bryla = zamknieta
    if bryla.SolidOrientation == rg.BrepSolidOrientation.Inward:
        bryla.Flip()
    if not bryla.IsSolid:
        bledy.append("bryła nie jest zamknięta (przekroje się przecinają - zmniejsz wybrzuszenie albo skręt); "
                     "objętość i płyty niepewne")
    wynik["bryla"] = bryla

    # 4) Nowe obrysy kondygnacji: cięcie 1 mm pod każdym stropem. Pola szkicu
    #    idą w parze z udanymi cięciami, żeby raport nie przesunął się po luce.
    nowe = []
    pola_szkicu_nowych = []
    for z, pole_szkicu in zip(z_stropow, pola_szkicu):
        obrys = _przekroj_na_wysokosci(bryla, z - CIECIE_PONIZEJ_M)
        if obrys is None:
            bledy.append("brak zamkniętego przekroju na wysokości {:.1f} m".format(z))
            continue
        nowe.append(obrys)
        pola_szkicu_nowych.append(pole_szkicu)
    wynik["kondygnacje_nowe"] = list(podziemne) + nowe

    plyty = []
    for obrys in nowe:
        plaskie = rg.Brep.CreatePlanarBreps(obrys, TOL)
        if plaskie is not None:
            plyty.extend(list(plaskie))
    wynik["plyty"] = plyty

    if kontury_co_m and kontury_co_m > 0.0:
        kontury = rg.Brep.CreateContourCurves(bryla, rg.Point3d(0.0, 0.0, 0.0),
                                              rg.Point3d(0.0, 0.0, z_max), kontury_co_m)
        wynik["kontury"] = list(kontury) if kontury is not None else []

    # 5) Obrys zabudowy: suma rzutów nowych obrysów na teren.
    obrys_zabudowy = _obrys(nowe, bledy)
    wynik["zabudowa_nowa"] = obrys_zabudowy

    vmp = rg.VolumeMassProperties.Compute(bryla)
    objetosc = abs(vmp.Volume) if vmp is not None else 0.0
    wysokosc = max(_gora(k) for k in nowe) if nowe else 0.0
    wynik["raport"] = linie_raportu([_pole(k) for k in nowe], pola_szkicu_nowych,
                                    wysokosc, objetosc,
                                    _pole(obrys_zabudowy) if obrys_zabudowy is not None else 0.0)
    return wynik


# ---------------------------------------------------------------------------
# Komponent Grasshopper - wejścia czytane z globals(), żeby plik działał także
# uruchomiony poza komponentem (wtedy wejść nie ma i raport to mówi).
# ---------------------------------------------------------------------------
def _wejscie(nazwa, domyslna):
    wartosc = globals().get(nazwa)
    return domyslna if wartosc is None else wartosc


bryla = None
kondygnacje_nowe = []
zabudowa_nowa = None
plyty = []
kontury = []
raport = []

if not W_RHINO:
    raport = ["uwaga: import Rhino nie powiódł się - komponent działa poza Rhino albo w nieobsługiwanej wersji."]
else:
    _krzywe = _wejscie("kondygnacje", [])
    if not isinstance(_krzywe, (list, tuple)):
        _krzywe = [_krzywe]
    _krzywe = [k for k in _krzywe if k is not None]
    _uwagi = []
    if not _krzywe:
        # Wklejony komponent bez kabli ma od razu coś pokazać.
        _krzywe = krzywe_domyslne("Kondygnacje")
        _uwagi = ["uwaga: wejście kondygnacje puste - użyto domyślnej masy Solna wbudowanej w skrypt"]
    _wynik = zbuduj_bryle(
        _krzywe,
        float(_wejscie("skret_deg", DOMYSLNE["skret_deg"])),
        float(_wejscie("wybrzuszenie", DOMYSLNE["wybrzuszenie"])),
        float(_wejscie("zaokraglenie", DOMYSLNE["zaokraglenie"])),
        float(_wejscie("pochylenie_x_m", DOMYSLNE["pochylenie_x_m"])),
        float(_wejscie("pochylenie_y_m", DOMYSLNE["pochylenie_y_m"])),
        int(_wejscie("punkty_profilu", DOMYSLNE["punkty_profilu"])),
        float(_wejscie("kontury_co_m", DOMYSLNE["kontury_co_m"])),
    )
    bryla = _wynik["bryla"]
    kondygnacje_nowe = _wynik["kondygnacje_nowe"]
    zabudowa_nowa = _wynik["zabudowa_nowa"]
    plyty = _wynik["plyty"]
    kontury = _wynik["kontury"]
    raport = _uwagi + ["uwaga: " + b for b in _wynik["bledy"]] + _wynik["raport"]


def _selftest():
    """Sprawdza czystą arytmetykę bez Rhino (wywołanie: --test)."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    assert skala(0.0, 0.1) == 1.0
    assert abs(skala(0.5, 0.1) - 1.1) < 1e-9
    assert abs(skala(1.0, 0.1) - 1.0) < 1e-9
    assert kat_skretu_rad(0.0, 12.0) == 0.0
    assert abs(kat_skretu_rad(1.0, 12.0) - math.radians(12.0)) < 1e-12
    assert promien_zaokraglenia(37.0, 26.0, 1.0) == 0.49 * 26.0
    assert promien_zaokraglenia(37.0, 26.0, 0.0) == 0.0
    assert promien_zaokraglenia(37.0, 26.0, 2.0) == 0.49 * 26.0, "zaokraglenie > 1 ma być przycięte do 1"
    pary = [(20.6, "k6"), (-3.0, "garaz"), (4.2, "k1"), (13.8, "k4"), (7.4, "k2"), (17.2, "k5"), (10.6, "k3")]
    assert podziel_wg_z(pary) == (["garaz"], ["k1", "k2", "k3", "k4", "k5", "k6"]), podziel_wg_z(pary)
    assert wysokosci_przekrojow([4.2, 7.4, 10.6, 13.8, 17.2, 20.6]) == [
        0.0, 4.2, 7.4, 10.6, 13.8, 17.2, 20.6]
    assert linia_kondygnacji(1, 964.2, 962.0) == "kondygnacja 1: 964.2 m2 (szkic 962.0 m2)"
    linie = linie_raportu([964.2, 800.0], [962.0, 782.0], 20.6, 19000.4, 1160.0)
    assert linie[2] == "suma Po (nadziemne): 1764.2 m2 (szkic 1744.0 m2)", linie[2]
    assert linie[3] == "wysokość: 20.6 m / 2 kond.", linie[3]
    assert linie[4] == "obrys zabudowy: 1160.0 m2", linie[4]
    assert linie[5] == "objętość: 19000 m3", linie[5]
    # Wbudowana masa domyślna musi zgadzać się ze szkicem 05_szkic_bryly_rhino.py.
    assert len(DOMYSLNA_MASA) == 12, len(DOMYSLNA_MASA)
    kond = [(x1 - x0) * (y1 - y0) for w, x0, y0, x1, y1, z in DOMYSLNA_MASA if w == "Kondygnacje"]
    assert kond == [1400, 962, 962, 962, 962, 782, 726], kond
    print("SELFTEST OK")


if __name__ == "__main__" and not W_RHINO and "--test" in sys.argv:
    _selftest()

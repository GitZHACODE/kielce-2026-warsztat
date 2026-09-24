#! python 3
"""
bryla_zaawansowana_gh - rzeźbiona bryła z profilem, skrętem, zwężeniem i atraktorem
===================================================================================
Purpose:
    Przykład zaawansowany do karty 06. Zamienia obrysy kondygnacji w gładką
    bryłę o wybranym profilu (prostokąt zaokrąglony albo superelipsa),
    z wygładzonym skrętem, asymetrycznym wybrzuszeniem, zwężeniem ku górze,
    pochyleniem i punktem-atraktorem, który wyciąga brzuch elewacji w swoją
    stronę. Wyjścia kondygnacje_nowe i zabudowa_nowa pasują do kontroli MPZP
    z karty 05. Bez podpiętych wejść buduje bryłę z domyślnej masy Solna
    wbudowanej w skrypt.

Inputs (Grasshopper):
    kondygnacje : Curve @list optional
        Po jednej zamkniętej płaskiej krzywej na kondygnację, na wysokości
        stropu. Krzywa o najwyższym Z <= 0 to kondygnacja podziemna: nie
        wchodzi do bryły i przechodzi bez zmian do kondygnacje_nowe. Obrys
        nieprostokątny jest zastępowany prostokątem opisanym, z ostrzeżeniem.
        Puste wejście: siedem kondygnacji masy Solna z tabeli DOMYSLNA_MASA.
    typ_profilu : int @item optional
        0 = prostokąt zaokrąglony (promień z zaokraglenie), 1 = superelipsa
        wpisana w prostokąt opisany (kształt z wykladnik_profilu). Domyślnie 1.
    wykladnik_profilu : float @item optional
        Wykładnik superelipsy: 1.5 soczewka, 2 elipsa, 3-4 miękki prostokąt,
        8 prawie prostokąt (co najmniej 1; domyślnie 3.0).
    zaokraglenie : float @item optional
        Zaokrąglenie naroży od 0 do 1 dla typ_profilu 0; promień =
        zaokraglenie * 0.49 * krótszy bok (domyślnie 0.6).
    skret_deg : float @item optional
        Całkowity skręt od terenu do dachu, w stopniach, wokół osi pionowej
        przez środek obrysu parteru (domyślnie 25).
    profil_skretu : int @item optional
        Przebieg skrętu po wysokości: 0 liniowy, 1 wygładzony (3t^2 - 2t^3),
        2 przyspieszający (t^2). Domyślnie 1.
    wybrzuszenie : float @item optional
        Nadwyżka skali przekroju w szczycie wybrzuszenia (domyślnie 0.15).
    wysokosc_wybrzuszenia : float @item optional
        Względna wysokość t (0 teren, 1 dach), na której wybrzuszenie jest
        największe; przycinana do 0.05-0.95 (domyślnie 0.5).
    zwezenie : float @item optional
        Skala przekroju dachu względem parteru, liniowo po wysokości
        (co najmniej 0.2; domyślnie 0.85; 1 = bez zwężenia).
    pochylenie_x_m : float @item optional
        Przesunięcie szczytu bryły w metrach wzdłuż osi X świata (domyślnie 0).
    pochylenie_y_m : float @item optional
        Przesunięcie szczytu bryły w metrach wzdłuż osi Y świata (domyślnie 0).
    atraktor : Point3d @item optional
        Punkt, w stronę którego wybrzusza się zwrócona do niego część elewacji
        (domyślnie (60.0, 18.5, 10.0), na wschód od masy Solna).
    sila_atraktora_m : float @item optional
        Największe przesunięcie punktu przekroju w stronę atraktora, w metrach;
        wartość ujemna robi wgłębienie (domyślnie 3.0).
    zasieg_atraktora_m : float @item optional
        Zasięg atraktora po wysokości (odchylenie funkcji Gaussa), w metrach
        (domyślnie 15).
    punkty_profilu : int @item optional
        Liczba punktów każdego przekroju (co najmniej 12; domyślnie 48).
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
        Płaskie płyty kondygnacji nadziemnych z nowych obrysów.
    kontury : list[Curve]
        Poziome kontury bryły do podglądu.
    przekroje : list[Curve]
        Przekroje, z których powstał loft (teren i każdy strop nadziemny).
    atraktor_uzyty : Point3d
        Punkt atraktora, którego użył skrypt (podany albo domyślny).
    raport : list[str]
        Profil i atraktor, powierzchnie nowych kondygnacji wobec szkicu,
        suma Po, wysokość, liczba kondygnacji, obrys, objętość i ostrzeżenia.

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


# Wartości domyślne; komponent używa ich, gdy wejście jest niepodpięte.
DOMYSLNE = {
    "typ_profilu": 1,
    "wykladnik_profilu": 3.0,
    "zaokraglenie": 0.6,
    "skret_deg": 25.0,
    "profil_skretu": 1,
    "wybrzuszenie": 0.15,
    "wysokosc_wybrzuszenia": 0.5,
    "zwezenie": 0.85,
    "pochylenie_x_m": 0.0,
    "pochylenie_y_m": 0.0,
    "sila_atraktora_m": 3.0,
    "zasieg_atraktora_m": 15.0,
    "punkty_profilu": 48,
    "kontury_co_m": 0.5,
}
DOMYSLNY_ATRAKTOR = (60.0, 18.5, 10.0)
NAZWY_PROFILU = {0: "prostokąt zaokrąglony", 1: "superelipsa"}
NAZWY_SKRETU = {0: "liniowy", 1: "wygładzony", 2: "przyspieszający"}
TOL = 0.001                 # tolerancja modelu w metrach
CIECIE_PONIZEJ_M = 0.001    # cięcie 1 mm pod stropem, żeby nie trafić w pokrywę bryły
MIN_PUNKTY_PROFILU = 12
MIN_ZWEZENIE = 0.2

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
def superelipsa_punkty(cx, cy, a, b, wykladnik, n):
    """n punktów superelipsy |x/a|^w + |y/b|^w = 1 wokół (cx, cy), od kierunku +X,
    przeciwnie do zegara; a i b to półosie."""
    w = max(float(wykladnik), 1.0)
    e = 2.0 / w
    punkty = []
    for i in range(n):
        t = 2.0 * math.pi * i / n
        c, s = math.cos(t), math.sin(t)
        x = cx + a * math.copysign(abs(c) ** e, c)
        y = cy + b * math.copysign(abs(s) ** e, s)
        punkty.append((x, y))
    return punkty


def promien_zaokraglenia(szerokosc, glebokosc, zaokraglenie):
    """Promień zaokrąglenia naroży: zaokraglenie * 0.49 * krótszy bok, czyli przy
    zaokraglenie 1 niemal połowa krótszego boku, tak by dwa zaokrąglenia nie zeszły
    się na krótszej krawędzi."""
    if zaokraglenie <= 0.0:
        return 0.0
    return min(max(zaokraglenie, 0.0), 1.0) * 0.49 * min(szerokosc, glebokosc)


def prostokat_zaokraglony_punkty(cx, cy, a, b, promien, n):
    """n punktów prostokąta o półbokach a, b wokół (cx, cy), naroża zaokrąglone
    promieniem, równo po obwodzie, od środka prawego boku przeciwnie do zegara."""
    r = min(max(promien, 0.0), min(a, b) * 0.999)
    pol_luku = math.pi * r / 2.0

    def luk(sx, sy, kat0):
        return lambda s: (sx + r * math.cos(kat0 + s / r), sy + r * math.sin(kat0 + s / r)) if r > 0 else (sx, sy)

    odcinki = [
        (b - r, lambda s: (a, s)),
        (pol_luku, luk(a - r, b - r, 0.0)),
        (2.0 * (a - r), lambda s: (a - r - s, b)),
        (pol_luku, luk(-(a - r), b - r, math.pi / 2.0)),
        (2.0 * (b - r), lambda s: (-a, b - r - s)),
        (pol_luku, luk(-(a - r), -(b - r), math.pi)),
        (2.0 * (a - r), lambda s: (-(a - r) + s, -b)),
        (pol_luku, luk(a - r, -(b - r), 1.5 * math.pi)),
        (b - r, lambda s: (a, -(b - r) + s)),
    ]
    obwod = sum(d for d, _ in odcinki)
    punkty = []
    for i in range(n):
        s = obwod * i / n
        for dlugosc, funkcja in odcinki:
            if dlugosc <= 0.0:
                continue
            if s <= dlugosc:
                x, y = funkcja(s)
                break
            s -= dlugosc
        else:
            # Reszta z arytmetyki zmiennoprzecinkowej za końcem obwodu: obwód jest
            # zamknięty, więc to punkt startowy; dzięki temu zawsze wychodzi n punktów.
            x, y = odcinki[0][1](0.0)
        punkty.append((cx + x, cy + y))
    return punkty


def latwienie_skretu(t, profil):
    """Udział skrętu na wysokości względnej t: 0 liniowy, 1 wygładzony, 2 przyspieszający."""
    t = min(max(t, 0.0), 1.0)
    if profil == 1:
        return t * t * (3.0 - 2.0 * t)
    if profil == 2:
        return t * t
    return t


def wybrzuszenie_w(t, wybrzuszenie, wysokosc_wybrzuszenia):
    """Współczynnik skali wybrzuszenia: 1 na terenie i dachu, 1 + wybrzuszenie
    na wysokości względnej wysokosc_wybrzuszenia (sinus o przesuniętym szczycie)."""
    t = min(max(t, 0.0), 1.0)
    t0 = min(max(wysokosc_wybrzuszenia, 0.05), 0.95)
    k = math.log(0.5) / math.log(t0)
    return 1.0 + wybrzuszenie * math.sin(math.pi * (t ** k))


def skala_zwezenia(t, zwezenie):
    """Skala przekroju od 1 na terenie do zwezenie na dachu, liniowo."""
    return 1.0 + (max(zwezenie, MIN_ZWEZENIE) - 1.0) * min(max(t, 0.0), 1.0)


def przesuniecie_atraktora(px, py, cx, cy, z, atraktor, sila, zasieg):
    """Radialne przesunięcie (dx, dy) punktu przekroju (px, py) o środku (cx, cy)
    na wysokości z w stronę atraktora (ax, ay, az): sila * gauss(z) * cos^2 kąta
    między kierunkiem punktu a kierunkiem atraktora; strona odwrócona nie rusza się."""
    if not atraktor or sila == 0.0 or zasieg <= 0.0:
        return (0.0, 0.0)
    ax, ay, az = atraktor
    rx, ry = px - cx, py - cy
    r = math.hypot(rx, ry)
    dx, dy = ax - cx, ay - cy
    d = math.hypot(dx, dy)
    if r < 1e-9 or d < 1e-9:
        return (0.0, 0.0)
    cos_kata = (rx * dx + ry * dy) / (r * d)
    if cos_kata <= 0.0:
        return (0.0, 0.0)
    waga = math.exp(-((z - az) / zasieg) ** 2) * cos_kata * cos_kata
    return (rx / r * sila * waga, ry / r * sila * waga)


def punkty_przekroju(x0, y0, x1, y1, z, t, os_x, os_y, ust):
    """Punkty (x, y) przekroju na wysokości z (t = z / z_max): profil w prostokącie
    opisanym (x0, y0, x1, y1), skala z wybrzuszenia i zwężenia wokół środka,
    skręt wokół osi (os_x, os_y), pochylenie, na końcu przesunięcie ku atraktorowi.
    ust to słownik ustawień o kluczach jak DOMYSLNE plus "atraktor" (krotka albo None)."""
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    a, b = (x1 - x0) / 2.0, (y1 - y0) / 2.0
    n = max(int(ust["punkty_profilu"]), MIN_PUNKTY_PROFILU)
    if ust["typ_profilu"] == 1:
        punkty = superelipsa_punkty(cx, cy, a, b, ust["wykladnik_profilu"], n)
    else:
        punkty = prostokat_zaokraglony_punkty(
            cx, cy, a, b, promien_zaokraglenia(2.0 * a, 2.0 * b, ust["zaokraglenie"]), n)

    skala = wybrzuszenie_w(t, ust["wybrzuszenie"], ust["wysokosc_wybrzuszenia"]) \
        * skala_zwezenia(t, ust["zwezenie"])
    kat = math.radians(ust["skret_deg"]) * latwienie_skretu(t, ust["profil_skretu"])
    cos_k, sin_k = math.cos(kat), math.sin(kat)
    dx_l, dy_l = ust["pochylenie_x_m"] * t, ust["pochylenie_y_m"] * t

    wynik = []
    for x, y in punkty:
        x, y = cx + (x - cx) * skala, cy + (y - cy) * skala
        rx, ry = x - os_x, y - os_y
        x, y = os_x + rx * cos_k - ry * sin_k, os_y + rx * sin_k + ry * cos_k
        wynik.append((x + dx_l, y + dy_l))

    atraktor = ust.get("atraktor")
    if atraktor and ust["sila_atraktora_m"] != 0.0:
        scx = sum(p[0] for p in wynik) / len(wynik)
        scy = sum(p[1] for p in wynik) / len(wynik)
        przesuniete = []
        for x, y in wynik:
            dx, dy = przesuniecie_atraktora(x, y, scx, scy, z, atraktor,
                                            ust["sila_atraktora_m"], ust["zasieg_atraktora_m"])
            przesuniete.append((x + dx, y + dy))
        wynik = przesuniete
    return wynik


def podziel_wg_z(pary):
    """Dzieli pary (z, obiekt) na (podziemne, nadziemne) według rzędnej z;
    zwraca same obiekty, każda lista rosnąco po z. Z <= 0 to kondygnacja podziemna."""
    posortowane = sorted(pary, key=lambda para: para[0])
    podziemne = [obiekt for z, obiekt in posortowane if z <= 0.0]
    nadziemne = [obiekt for z, obiekt in posortowane if z > 0.0]
    return podziemne, nadziemne


def linie_raportu(pola_nowe, pola_szkicu, wysokosc_m, objetosc_m3, obrys_m2):
    """Składa raport z pól nowych kondygnacji, wysokości, obrysu i objętości."""
    linie = []
    for i, (nowa, szkic) in enumerate(zip(pola_nowe, pola_szkicu)):
        linie.append("kondygnacja {}: {:.1f} m2 (szkic {:.1f} m2)".format(i + 1, nowa, szkic))
    linie.append("suma Po (nadziemne): {:.1f} m2 (szkic {:.1f} m2)".format(sum(pola_nowe), sum(pola_szkicu)))
    linie.append("wysokość: {:.1f} m / {} kond.".format(wysokosc_m, len(pola_nowe)))
    linie.append("obrys zabudowy: {:.1f} m2".format(obrys_m2))
    linie.append("objętość: {:.0f} m3".format(objetosc_m3))
    return linie


def linia_ustawien(ust):
    """Jedna linia raportu o profilu, skręcie i atraktorze."""
    if ust["typ_profilu"] == 1:
        profil = "superelipsa (wykładnik {:.1f})".format(ust["wykladnik_profilu"])
    else:
        profil = "prostokąt zaokrąglony (zaokrąglenie {:.2f})".format(ust["zaokraglenie"])
    skret = "skręt {:.0f}° ({})".format(ust["skret_deg"], NAZWY_SKRETU.get(ust["profil_skretu"], "liniowy"))
    if ust.get("atraktor") and ust["sila_atraktora_m"] != 0.0 and ust["zasieg_atraktora_m"] > 0.0:
        ax, ay, az = ust["atraktor"]
        atraktor = "atraktor ({:.1f}, {:.1f}, {:.1f}), siła {:.1f} m, zasięg {:.1f} m".format(
            ax, ay, az, ust["sila_atraktora_m"], ust["zasieg_atraktora_m"])
    else:
        atraktor = "atraktor: brak"
    return "profil: {}; {}; {}".format(profil, skret, atraktor)


def ustawienia_z_wejsc(czytaj, bledy):
    """Zbiera ustawienia z wejść (funkcja czytaj(nazwa, domyslna)), przycina wartości
    spoza zakresu do domyślnych i dopisuje ostrzeżenia."""
    ust = {}
    for nazwa, domyslna in DOMYSLNE.items():
        wartosc = czytaj(nazwa, domyslna)
        ust[nazwa] = int(wartosc) if isinstance(domyslna, int) else float(wartosc)
    if ust["typ_profilu"] not in NAZWY_PROFILU:
        bledy.append("typ_profilu {} nieznany - użyto {} ({})".format(
            ust["typ_profilu"], DOMYSLNE["typ_profilu"], NAZWY_PROFILU[DOMYSLNE["typ_profilu"]]))
        ust["typ_profilu"] = DOMYSLNE["typ_profilu"]
    if ust["profil_skretu"] not in NAZWY_SKRETU:
        bledy.append("profil_skretu {} nieznany - użyto {} ({})".format(
            ust["profil_skretu"], DOMYSLNE["profil_skretu"], NAZWY_SKRETU[DOMYSLNE["profil_skretu"]]))
        ust["profil_skretu"] = DOMYSLNE["profil_skretu"]
    if ust["wykladnik_profilu"] < 1.0:
        bledy.append("wykladnik_profilu poniżej 1 - użyto 1")
        ust["wykladnik_profilu"] = 1.0
    if ust["zwezenie"] < MIN_ZWEZENIE:
        bledy.append("zwezenie poniżej {} - użyto {}".format(MIN_ZWEZENIE, MIN_ZWEZENIE))
        ust["zwezenie"] = MIN_ZWEZENIE
    if ust["punkty_profilu"] < MIN_PUNKTY_PROFILU:
        bledy.append("punkty_profilu poniżej {} - użyto {}".format(MIN_PUNKTY_PROFILU, MIN_PUNKTY_PROFILU))
        ust["punkty_profilu"] = MIN_PUNKTY_PROFILU
    return ust


# ---------------------------------------------------------------------------
# Geometria (RhinoCommon)
# ---------------------------------------------------------------------------
def _lista(elementy, typ):
    """Metody RhinoCommon oczekujące IEnumerable<T> potrzebują listy .NET, nie listy Pythona."""
    lista = List[typ]()
    for element in elementy:
        lista.Add(element)
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


def _gora(krzywa):
    return krzywa.GetBoundingBox(True).Max.Z


def _prostokat_opisany(krzywa, bledy, nr):
    """Prostokąt opisany (x0, y0, x1, y1) w osiach świata; ostrzega, gdy obrys nie jest prostokątem."""
    bb = krzywa.GetBoundingBox(True)
    x0, y0, x1, y1 = bb.Min.X, bb.Min.Y, bb.Max.X, bb.Max.Y
    pole_bb = (x1 - x0) * (y1 - y0)
    pole = _pole(krzywa)
    if pole <= 0.0 or pole_bb <= 0.0:
        bledy.append("kondygnacja {}: obrys o zerowym polu (krzywa otwarta, niepłaska albo zdegenerowana)".format(nr))
    elif abs(pole - pole_bb) > 0.01 * pole_bb:
        bledy.append("kondygnacja {}: obrys inny niż prostokąt w osiach świata - użyto prostokąta opisanego "
                     "({:.0f} m2 zamiast {:.0f} m2)".format(nr, pole_bb, pole))
    return x0, y0, x1, y1


def _krzywa_okresowa(punkty_xy, z):
    """Zamknięta gładka krzywa NURBS stopnia 3 przez punkty kontrolne (x, y) na rzędnej z."""
    lista = List[rg.Point3d]()
    for x, y in punkty_xy:
        lista.Add(rg.Point3d(x, y, z))
    return rg.NurbsCurve.Create(True, 3, lista)


def _przekroj_na_wysokosci(bryla, z):
    """Zamknięty obrys bryły na rzędnej z (największy, gdy jest ich kilka)."""
    plaszczyzna = rg.Plane(rg.Point3d(0.0, 0.0, z), rg.Vector3d.ZAxis)
    rc, krzywe, _punkty = rg.Intersect.Intersection.BrepPlane(bryla, plaszczyzna, TOL)
    if not rc or krzywe is None or len(krzywe) == 0:
        return None
    polaczone = rg.Curve.JoinCurves(krzywe, TOL)
    kandydaci = [c for c in polaczone if c.IsClosed]
    return max(kandydaci, key=_pole) if kandydaci else None


def _obrys(krzywe_nadziemne, bledy):
    """Rzut nowych obrysów na teren i ich suma logiczna."""
    rzuty = []
    for krzywa in krzywe_nadziemne:
        rzut = rg.Curve.ProjectToPlane(krzywa, rg.Plane.WorldXY)
        if rzut is not None:
            rzuty.append(rzut)
    if not rzuty:
        return None
    if len(rzuty) == 1:
        return rzuty[0]
    suma = rg.Curve.CreateBooleanUnion(_lista(rzuty, rg.Curve), TOL)
    if suma is None or len(suma) == 0:
        bledy.append("suma logiczna rzutów nie powiodła się, obrys = największy rzut")
        return max(rzuty, key=_pole)
    return max(list(suma), key=_pole)


def zbuduj_bryle(kondygnacje, ust):
    """Buduje bryłę, płyty i przekroje z listy krzywych kondygnacji i słownika ustawień.
    Zwraca słownik z kluczami bryla, kondygnacje_nowe, zabudowa_nowa, plyty, kontury,
    przekroje, raport, bledy."""
    bledy = []
    wynik = {"bryla": None, "kondygnacje_nowe": [], "zabudowa_nowa": None, "plyty": [],
             "kontury": [], "przekroje": [], "raport": [], "bledy": bledy}

    krzywe = [k for k in kondygnacje if k is not None]
    podziemne, nadziemne = podziel_wg_z([(_gora(k), k) for k in krzywe])
    if len(nadziemne) < 2:
        bledy.append("potrzebne są co najmniej dwie kondygnacje nadziemne (Z > 0), jest {}".format(len(nadziemne)))
        wynik["kondygnacje_nowe"] = list(podziemne)   # kondygnacje podziemne zawsze przechodzą dalej
        return wynik

    z_stropow = [_gora(k) for k in nadziemne]
    z_max = z_stropow[-1]
    pola_szkicu = [_pole(k) for k in nadziemne]
    prostokaty = [_prostokat_opisany(k, bledy, i + 1) for i, k in enumerate(nadziemne)]

    # 1) Przekroje: parter na terenie (t = 0), potem każdy strop; punkty liczone
    #    w Pythonie, potem jedna okresowa krzywa NURBS na przekrój.
    x0, y0, x1, y1 = prostokaty[0]
    os_x, os_y = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    zrodla = [(prostokaty[0], 0.0)] + list(zip(prostokaty, z_stropow))
    przekroje = []
    for (px0, py0, px1, py1), z in zrodla:
        t = z / z_max if z_max > 0.0 else 0.0
        punkty = punkty_przekroju(px0, py0, px1, py1, z, t, os_x, os_y, ust)
        przekroje.append(_krzywa_okresowa(punkty, z))
    wynik["przekroje"] = przekroje

    # 2) Loft (przekroje mają tę samą liczbę punktów i wspólny początek), pokrywy, orientacja.
    breps = rg.Brep.CreateFromLoft(_lista(przekroje, rg.Curve), rg.Point3d.Unset, rg.Point3d.Unset,
                                   rg.LoftType.Normal, False)
    if breps is None or len(breps) == 0:
        breps = rg.Brep.CreateFromLoftRebuild(_lista(przekroje, rg.Curve), rg.Point3d.Unset, rg.Point3d.Unset,
                                              rg.LoftType.Normal, False, ust["punkty_profilu"])
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
        bledy.append("bryła nie jest zamknięta (przekroje się przecinają - zmniejsz sila_atraktora_m, "
                     "wybrzuszenie albo zwezenie); objętość i płyty niepewne")
    wynik["bryla"] = bryla

    # 3) Nowe obrysy kondygnacji: cięcie 1 mm pod każdym stropem.
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

    if ust["kontury_co_m"] > 0.0:
        kontury = rg.Brep.CreateContourCurves(bryla, rg.Point3d(0.0, 0.0, 0.0),
                                              rg.Point3d(0.0, 0.0, z_max), ust["kontury_co_m"])
        wynik["kontury"] = list(kontury) if kontury is not None else []

    # 4) Obrys zabudowy i raport.
    obrys_zabudowy = _obrys(nowe, bledy)
    wynik["zabudowa_nowa"] = obrys_zabudowy
    vmp = rg.VolumeMassProperties.Compute(bryla)
    objetosc = abs(vmp.Volume) if vmp is not None else 0.0
    wysokosc = max(_gora(k) for k in nowe) if nowe else 0.0
    wynik["raport"] = [linia_ustawien(ust)] + linie_raportu(
        [_pole(k) for k in nowe], pola_szkicu_nowych, wysokosc, objetosc,
        _pole(obrys_zabudowy) if obrys_zabudowy is not None else 0.0)
    return wynik


# ---------------------------------------------------------------------------
# Komponent Grasshopper - wejścia czytane z globals(), żeby plik działał także
# uruchomiony poza komponentem; niepodpięte wejście to None albo pusta lista.
# ---------------------------------------------------------------------------
def _wejscie(nazwa, domyslna):
    wartosc = globals().get(nazwa)
    return domyslna if wartosc is None else wartosc


bryla = None
kondygnacje_nowe = []
zabudowa_nowa = None
plyty = []
kontury = []
przekroje = []
atraktor_uzyty = None
raport = []

if not W_RHINO:
    raport = ["uwaga: import Rhino nie powiódł się - komponent działa poza Rhino albo w nieobsługiwanej wersji."]
else:
    _uwagi = []
    _krzywe = _wejscie("kondygnacje", [])
    if not isinstance(_krzywe, (list, tuple)):
        _krzywe = [_krzywe]
    _krzywe = [k for k in _krzywe if k is not None]
    if not _krzywe:
        # Wklejony komponent bez kabli ma od razu coś pokazać.
        _krzywe = krzywe_domyslne("Kondygnacje")
        _uwagi.append("wejście kondygnacje puste - użyto domyślnej masy Solna wbudowanej w skrypt")
    _ust = ustawienia_z_wejsc(_wejscie, _uwagi)
    _punkt = _wejscie("atraktor", None)
    if _punkt is None:
        _ust["atraktor"] = DOMYSLNY_ATRAKTOR
        _uwagi.append("wejście atraktor puste - użyto punktu domyślnego ({:.1f}, {:.1f}, {:.1f})".format(*DOMYSLNY_ATRAKTOR))
    else:
        _ust["atraktor"] = (float(_punkt.X), float(_punkt.Y), float(_punkt.Z))
    atraktor_uzyty = rg.Point3d(*_ust["atraktor"])

    _wynik = zbuduj_bryle(_krzywe, _ust)
    bryla = _wynik["bryla"]
    kondygnacje_nowe = _wynik["kondygnacje_nowe"]
    zabudowa_nowa = _wynik["zabudowa_nowa"]
    plyty = _wynik["plyty"]
    kontury = _wynik["kontury"]
    przekroje = _wynik["przekroje"]
    raport = ["uwaga: " + u for u in _uwagi] + ["uwaga: " + b for b in _wynik["bledy"]] + _wynik["raport"]


def _selftest():
    """Sprawdza czystą arytmetykę bez Rhino (wywołanie: --test)."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    # Superelipsa o wykładniku 2 to elipsa: każdy punkt spełnia (x/a)^2 + (y/b)^2 = 1.
    pts = superelipsa_punkty(10.0, 5.0, 4.0, 2.0, 2.0, 32)
    assert len(pts) == 32
    assert abs(pts[0][0] - 14.0) < 1e-9 and abs(pts[0][1] - 5.0) < 1e-9, pts[0]
    for x, y in pts:
        assert abs(((x - 10.0) / 4.0) ** 2 + ((y - 5.0) / 2.0) ** 2 - 1.0) < 1e-9, (x, y)
    # Wykładnik 8 zbliża się do prostokąta: punkt pod 45° leży blisko naroża.
    pts8 = superelipsa_punkty(0.0, 0.0, 1.0, 1.0, 8.0, 8)
    assert pts8[1][0] > 0.9 and pts8[1][1] > 0.9, pts8[1]

    # Prostokąt bez zaokrąglenia: wszystkie punkty na brzegu, równo po obwodzie.
    pts = prostokat_zaokraglony_punkty(0.0, 0.0, 3.0, 2.0, 0.0, 20)
    assert len(pts) == 20 and abs(pts[0][0] - 3.0) < 1e-9 and abs(pts[0][1]) < 1e-9, pts[0]
    for x, y in pts:
        assert abs(max(abs(x) / 3.0, abs(y) / 2.0) - 1.0) < 1e-9, (x, y)
    # Z zaokrągleniem: punkty w prostokącie, pierwszy w środku prawego boku, odstępy równe.
    pts = prostokat_zaokraglony_punkty(0.0, 0.0, 3.0, 2.0, 0.98, 40)
    assert len(pts) == 40 and abs(pts[0][0] - 3.0) < 1e-9 and abs(pts[0][1]) < 1e-9, pts[0]
    assert all(abs(x) <= 3.0 + 1e-9 and abs(y) <= 2.0 + 1e-9 for x, y in pts)
    odstepy = [math.hypot(pts[(i + 1) % 40][0] - pts[i][0], pts[(i + 1) % 40][1] - pts[i][1]) for i in range(40)]
    assert max(odstepy) - min(odstepy) < 0.05 * max(odstepy), (min(odstepy), max(odstepy))
    assert promien_zaokraglenia(37.0, 26.0, 1.0) == 0.49 * 26.0

    for profil in (0, 1, 2):
        assert latwienie_skretu(0.0, profil) == 0.0 and abs(latwienie_skretu(1.0, profil) - 1.0) < 1e-12
    assert abs(latwienie_skretu(0.5, 1) - 0.5) < 1e-12 and abs(latwienie_skretu(0.5, 2) - 0.25) < 1e-12
    assert latwienie_skretu(0.25, 1) < 0.25, "wygładzony skręt zaczyna wolniej niż liniowy"
    assert latwienie_skretu(0.75, 1) > 0.75, "wygładzony skręt kończy szybciej niż liniowy"

    assert abs(wybrzuszenie_w(0.0, 0.2, 0.3) - 1.0) < 1e-9
    assert abs(wybrzuszenie_w(1.0, 0.2, 0.3) - 1.0) < 1e-9
    assert abs(wybrzuszenie_w(0.3, 0.2, 0.3) - 1.2) < 1e-9, "szczyt wybrzuszenia ma być na t0"
    assert abs(wybrzuszenie_w(0.5, 0.2, 0.5) - 1.2) < 1e-9
    assert abs(skala_zwezenia(1.0, 0.85) - 0.85) < 1e-12 and skala_zwezenia(0.0, 0.85) == 1.0
    assert abs(skala_zwezenia(1.0, 0.0) - MIN_ZWEZENIE) < 1e-12

    # Atraktor na wschodzie (+X): punkt wschodni przesuwa się o pełną siłę, zachodni wcale,
    # a daleko od wysokości atraktora prawie wcale.
    dx, dy = przesuniecie_atraktora(10.0, 0.0, 0.0, 0.0, 5.0, (50.0, 0.0, 5.0), 3.0, 10.0)
    assert abs(dx - 3.0) < 1e-9 and abs(dy) < 1e-9, (dx, dy)
    assert przesuniecie_atraktora(-10.0, 0.0, 0.0, 0.0, 5.0, (50.0, 0.0, 5.0), 3.0, 10.0) == (0.0, 0.0)
    dx, _ = przesuniecie_atraktora(10.0, 0.0, 0.0, 0.0, 45.0, (50.0, 0.0, 5.0), 3.0, 10.0)
    assert dx < 0.001, dx
    assert przesuniecie_atraktora(10.0, 0.0, 0.0, 0.0, 5.0, None, 3.0, 10.0) == (0.0, 0.0)

    # Przekrój bez przekształceń to elipsa w prostokącie opisanym; skręt 90° obraca
    # pierwszy punkt z kierunku +X na +Y wokół osi.
    ust = dict(DOMYSLNE)
    ust.update({"typ_profilu": 1, "wykladnik_profilu": 2.0, "skret_deg": 0.0, "wybrzuszenie": 0.0,
                "zwezenie": 1.0, "atraktor": None, "punkty_profilu": 16})
    pts = punkty_przekroju(0.0, 0.0, 8.0, 4.0, 5.0, 0.5, 4.0, 2.0, ust)
    assert len(pts) == 16 and abs(pts[0][0] - 8.0) < 1e-9 and abs(pts[0][1] - 2.0) < 1e-9, pts[0]
    ust["skret_deg"] = 90.0
    ust["profil_skretu"] = 0
    pts = punkty_przekroju(0.0, 0.0, 8.0, 4.0, 5.0, 1.0, 4.0, 2.0, ust)
    assert abs(pts[0][0] - 4.0) < 1e-9 and abs(pts[0][1] - 6.0) < 1e-9, pts[0]
    # Atraktor na wschodzie powiększa wschodni punkt, nie rusza zachodniego.
    ust.update({"skret_deg": 0.0, "atraktor": (100.0, 2.0, 5.0), "sila_atraktora_m": 2.0, "zasieg_atraktora_m": 10.0})
    pts = punkty_przekroju(0.0, 0.0, 8.0, 4.0, 5.0, 0.5, 4.0, 2.0, ust)
    assert abs(pts[0][0] - 10.0) < 1e-9, pts[0]
    assert abs(pts[8][0] - 0.0) < 1e-9, pts[8]

    pary = [(20.6, "k6"), (-3.0, "garaz"), (4.2, "k1"), (13.8, "k4"), (7.4, "k2"), (17.2, "k5"), (10.6, "k3")]
    assert podziel_wg_z(pary) == (["garaz"], ["k1", "k2", "k3", "k4", "k5", "k6"]), podziel_wg_z(pary)

    bledy = []
    ust = ustawienia_z_wejsc(lambda nazwa, domyslna: {"typ_profilu": 7, "zwezenie": 0.0,
                                                      "punkty_profilu": 3}.get(nazwa, domyslna), bledy)
    assert ust["typ_profilu"] == 1 and ust["zwezenie"] == MIN_ZWEZENIE, ust
    assert ust["punkty_profilu"] == MIN_PUNKTY_PROFILU and len(bledy) == 3, (ust, bledy)
    ust["atraktor"] = DOMYSLNY_ATRAKTOR
    assert linia_ustawien(ust).startswith(
        "profil: superelipsa (wykładnik 3.0); skręt 25° (wygładzony); atraktor (60.0, 18.5, 10.0)"), linia_ustawien(ust)
    ust["zasieg_atraktora_m"] = 0.0
    assert linia_ustawien(ust).endswith("atraktor: brak"), "zasięg 0 to brak działania atraktora"
    ust["zasieg_atraktora_m"] = 15.0
    ust["atraktor"] = None
    assert linia_ustawien(ust).endswith("atraktor: brak")

    linie = linie_raportu([964.2, 800.0], [962.0, 782.0], 20.6, 19000.4, 1160.0)
    assert linie[3] == "wysokość: 20.6 m / 2 kond." and linie[5] == "objętość: 19000 m3", linie

    assert len(DOMYSLNA_MASA) == 12
    kond = [(x1 - x0) * (y1 - y0) for w, x0, y0, x1, y1, z in DOMYSLNA_MASA if w == "Kondygnacje"]
    assert kond == [1400, 962, 962, 962, 962, 782, 726], kond
    print("SELFTEST OK")


if __name__ == "__main__" and not W_RHINO and "--test" in sys.argv:
    _selftest()

#! python 3
"""Karty 05, 06 i 07 - skrypt do jednorazowego uruchomienia w edytorze skryptów Rhino 8
(Python 3), w nowym pliku metrycznym. Rysuje fikcyjną masę "Solna" jako
zamknięte płaskie krzywe na nazwanych warstwach, tak aby komponent Grasshopper
05_sprawdz_mpzp_gh.py (i komponenty 06_bryla_gh.py, 07_elewacja_gh.py) miały co podpiąć pod wejścia dzialka/zabudowa/
kondygnacje/pbc_grunt/pbc_tarasy. Na koniec drukuje podsumowanie pól
powierzchni policzonych przez Rhino.Geometry.AreaMassProperties.

Układ współrzędnych (metry, światowe XY): KDP-1 to północna krawędź działki
(y = 37), ul. Solna to zachodnia krawędź (x = 0). Każdy prostokąt jest
budowany jako Rhino.Geometry.Rectangle3d na płaszczyźnie WorldXY, a następnie
przesuwany na właściwą wysokość Z (stropy kondygnacji, tarasy).
"""

import sys

try:
    import Rhino
    import Rhino.Geometry as rg
    import System
    import System.Drawing as sd
    import scriptcontext as sc
    W_RHINO = True
except ImportError:
    W_RHINO = False


# Tabela współrzędnych masy "Solna": (warstwa, x0, y0, x1, y1, z)
PROSTOKATY = [
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

# Kolory warstw (R, G, B)
KOLORY_WARSTW = {
    "Dzialka": (0, 0, 0),
    "Zabudowa": (139, 0, 0),
    "Kondygnacje": (30, 60, 200),
    "PBC-grunt": (0, 130, 40),
    "PBC-tarasy": (150, 220, 150),
    "Opis": (120, 120, 120),
}


def pole_prostokata(x0, y0, x1, y1):
    """Czysta funkcja (bez Rhino): pole prostokąta w m2."""
    return (x1 - x0) * (y1 - y0)


def _warstwa(nazwa):
    """Zwraca indeks warstwy `nazwa`. Jeśli warstwa już istnieje w dokumencie,
    zwraca jej indeks zamiast wywoływać Layers.Add ponownie - dla istniejącej
    nazwy Layers.Add zwraca -1, co przy drugim uruchomieniu w tym samym pliku
    psułoby attr.LayerIndex (i w efekcie AddCurve/AddTextDot)."""
    istniejaca = sc.doc.Layers.FindName(nazwa)
    if istniejaca is not None:
        return istniejaca.Index
    r, g, b = KOLORY_WARSTW[nazwa]
    return sc.doc.Layers.Add(nazwa, sd.Color.FromArgb(r, g, b))


def narysuj_mase():
    """Rysuje wszystkie prostokąty z PROSTOKATY na właściwych warstwach i
    wysokościach, dodaje opisowe text-doty i drukuje podsumowanie pól."""
    warstwy = {}
    for nazwa in KOLORY_WARSTW:
        warstwy[nazwa] = _warstwa(nazwa)

    podsumowanie = []
    puste_id = 0
    for warstwa, x0, y0, x1, y1, z in PROSTOKATY:
        prostokat = rg.Rectangle3d(rg.Plane.WorldXY, rg.Interval(x0, x1), rg.Interval(y0, y1))
        krzywa = prostokat.ToNurbsCurve()
        krzywa.Transform(rg.Transform.Translation(0.0, 0.0, z))

        attr = Rhino.DocObjects.ObjectAttributes()
        attr.LayerIndex = warstwy[warstwa]
        id_obiektu = sc.doc.Objects.AddCurve(krzywa, attr)
        if id_obiektu == System.Guid.Empty:
            puste_id += 1

        amp = rg.AreaMassProperties.Compute(krzywa)
        podsumowanie.append((warstwa, z, amp.Area if amp is not None else 0.0))

    attr_opis = Rhino.DocObjects.ObjectAttributes()
    attr_opis.LayerIndex = warstwy["Opis"]
    id_dot1 = sc.doc.Objects.AddTextDot(rg.TextDot("KDP-1", rg.Point3d(25.0, 37.5, 0.0)), attr_opis)
    if id_dot1 == System.Guid.Empty:
        puste_id += 1
    id_dot2 = sc.doc.Objects.AddTextDot(rg.TextDot("ul. Solna", rg.Point3d(-1.5, 18.5, 0.0)), attr_opis)
    if id_dot2 == System.Guid.Empty:
        puste_id += 1

    sc.doc.Views.Redraw()

    if puste_id:
        # Nie zakładamy sukcesu na sztywno - jeśli obiekty nie trafiły do
        # dokumentu, ostrzegamy zamiast drukować fałszywy komunikat o powodzeniu.
        print("uwaga: {} obiektów nie zostało dodanych do dokumentu (Guid.Empty) - sprawdź warstwy.".format(puste_id))
    else:
        print("Masa \"Solna\" narysowana. Podsumowanie pól powierzchni:")
        for warstwa, z, area in podsumowanie:
            print("  {} (z={:.1f}): {:.1f} m2".format(warstwa, z, area))


def _selftest():
    """Sprawdza tabelę PROSTOKATY i pole_prostokata() bez Rhino."""
    sys.stdout.reconfigure(encoding="utf-8")

    assert len(PROSTOKATY) == 12, "oczekiwano 12 prostokątów, jest {}".format(len(PROSTOKATY))

    oczekiwane_pola = [1850, 962, 1400, 962, 962, 962, 962, 782, 726, 120, 90, 8]
    policzone_pola = [pole_prostokata(x0, y0, x1, y1) for _, x0, y0, x1, y1, _ in PROSTOKATY]
    assert policzone_pola == oczekiwane_pola, "pola: {} != {}".format(policzone_pola, oczekiwane_pola)

    print("SELFTEST OK")


if __name__ == "__main__":
    if W_RHINO:
        narysuj_mase()
    elif "--test" in sys.argv:
        _selftest()

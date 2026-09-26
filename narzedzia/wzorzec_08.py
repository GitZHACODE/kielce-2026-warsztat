#! python 3
"""Zapisuje wartości wzorcowe dla karty 08 (pokaz w przeglądarce) z komponentów
przyklady/bryla_zaawansowana_gh.py i przyklady/elewacja_zaawansowana_gh.py
uruchomionych pod Rhino.Inside (narzędzie prowadzącego).

Uruchomienie (z katalogu głównego repozytorium):
    conda run -n kielce-rhino --no-capture-output python narzedzia/wzorzec_08.py
Wynik: rozwiazania/08_wzorzec.json, czytany przez node rozwiazania/08_test.js.
"""

import datetime
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

import rhinoinside  # noqa: E402

RHINO_SYSTEM = r"C:\Program Files\Rhino 8\System"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRZYKLADY = os.path.join(ROOT, "przyklady")
WYJSCIE = os.path.join(ROOT, "rozwiazania", "08_wzorzec.json")

# Tolerancje, które stosuje node rozwiazania/08_test.js (przeglądarka wobec Rhino).
TOLERANCJE = {"pole_pct": 1.0, "obrys_pct": 1.0, "objetosc_pct": 5.0, "wysokosc_m": 0.001,
              "udzial_pp": 10.0, "glebokosc_m": 0.05, "powierzchnia_pct": 10.0}

PRZYPADKI_BRYLY = {
    "zaaw_domyslny": {},
    "bez_atraktora": {"sila_atraktora_m": 0.0},
    "karta06": {"typ_profilu": 0, "zaokraglenie": 0.6, "skret_deg": 12.0, "profil_skretu": 0,
                "wybrzuszenie": 0.10, "zwezenie": 1.0, "sila_atraktora_m": 0.0},
    "wieza": {"typ_profilu": 1, "wykladnik_profilu": 2.5, "skret_deg": 45.0, "profil_skretu": 1,
              "wybrzuszenie": 0.2, "wysokosc_wybrzuszenia": 0.35, "zwezenie": 0.6,
              "pochylenie_x_m": 2.0, "pochylenie_y_m": 1.0, "sila_atraktora_m": 0.0},
    "szkic": {"typ_profilu": 0, "zaokraglenie": 0.0, "skret_deg": 0.0, "wybrzuszenie": 0.0,
              "zwezenie": 1.0, "sila_atraktora_m": 0.0},
}
PRZYPADKI_ELEWACJI = {
    "elew_domyslna": {},
    "elew_wschod": {"azymut_slonca_deg": 90.0},
}


def wczytaj_skrypt(nazwa, wejscia):
    """Wykonuje skrypt komponentu z podanymi wejściami jak Grasshopper i zwraca globals."""
    sciezka = os.path.join(PRZYKLADY, nazwa)
    with open(sciezka, "r", encoding="utf-8") as f:
        zrodlo = f.read()
    g = {"__name__": "gh_" + nazwa.split(".")[0], "__file__": sciezka}
    g.update(wejscia)
    exec(compile(zrodlo, sciezka, "exec"), g)
    return g


def pole(krzywa, rg):
    amp = rg.AreaMassProperties.Compute(krzywa)
    return amp.Area if amp is not None else 0.0


def liczba_z_raportu(raport, wzorzec):
    for linia in raport:
        m = re.search(wzorzec, linia)
        if m:
            return float(m.group(1))
    return None


def main():
    rhinoinside.load(RHINO_SYSTEM)
    import Rhino
    import Rhino.Geometry as rg

    wynik = {"wygenerowano": datetime.datetime.now().isoformat(timespec="seconds"),
             "rhino": str(Rhino.RhinoApp.Version), "tolerancje": TOLERANCJE, "bryly": {}, "elewacje": {}}
    bryly = {}
    for nazwa, ust in PRZYPADKI_BRYLY.items():
        g = wczytaj_skrypt("bryla_zaawansowana_gh.py", dict(ust))
        bryla = g["bryla"]
        assert bryla is not None, (nazwa, g["raport"])
        # Niezamknięta bryła nie przerywa całego przebiegu: pola i objętość dają
        # się policzyć, a przypadek zostaje w wynikach pod kluczem "zamknieta".
        if not bryla.IsSolid:
            print("  uwaga: {}: bryła nie jest zamknięta - wartości zapisane mimo to".format(nazwa))
        nowe = [k for k in g["kondygnacje_nowe"] if k.GetBoundingBox(True).Max.Z > 0.0]
        pola = [pole(k, rg) for k in nowe]
        wynik["bryly"][nazwa] = {
            "ustawienia": ust,
            "zamknieta": bool(bryla.IsSolid),
            "pola_m2": pola,
            "obrys_m2": pole(g["zabudowa_nowa"], rg),
            "objetosc_m3": abs(rg.VolumeMassProperties.Compute(bryla).Volume),
            "wysokosc_m": max(k.GetBoundingBox(True).Max.Z for k in nowe),
            "kondygnacje": len(nowe),
            "raport": list(g["raport"]),
        }
        bryly[nazwa] = bryla
        print("  {}: pola {}, obrys {:.1f}, objętość {:.0f}".format(
            nazwa, ["{:.1f}".format(p) for p in pola], wynik["bryly"][nazwa]["obrys_m2"],
            wynik["bryly"][nazwa]["objetosc_m3"]))

    atraktory = [rg.Point3d(25.0, -20.0, 12.0)]

    def elewacja(nazwa, ust, pelne):
        g = wczytaj_skrypt("elewacja_zaawansowana_gh.py",
                           dict(ust, bryla=bryly["zaaw_domyslny"], atraktory=atraktory))
        inten = list(g["intensywnosc_paneli"])
        wpis = {"ustawienia": ust, "bryla": "zaaw_domyslny", "paneli": len(g["siatka"])}
        if pelne:
            dmin, dmax = g["DOMYSLNE"]["glebokosc_min_m"], g["DOMYSLNE"]["glebokosc_max_m"]
            glebokosci = [dmin + (dmax - dmin) * i for i in inten]
            wpis.update({
                "powyzej_05": sum(1 for i in inten if i > 0.5),
                "glebokosc_min_m": min(glebokosci), "glebokosc_max_m": max(glebokosci),
                "powierzchnia_m2": liczba_z_raportu(g["raport"], r"powierzchnia elewacji[^:]*: (\d+(?:\.\d+)?)"),
                "raport": list(g["raport"]),
            })
        wynik["elewacje"][nazwa] = wpis
        print("  {}: {} paneli".format(nazwa, wpis["paneli"]))

    for nazwa, ust in PRZYPADKI_ELEWACJI.items():
        elewacja(nazwa, ust, True)
    for typ_wzoru in range(4):
        for typ_panelu in range(3):
            elewacja("wzor{}_panel{}".format(typ_wzoru, typ_panelu),
                     {"typ_wzoru": typ_wzoru, "typ_panelu": typ_panelu}, False)

    with open(WYJSCIE, "w", encoding="utf-8", newline="\n") as f:
        json.dump(wynik, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("WZORZEC OK", WYJSCIE)


if __name__ == "__main__":
    main()

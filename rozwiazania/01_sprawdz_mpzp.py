#! python 3
"""
Karta 01 (rozwiązanie wzorcowe): sprawdzenie inwestycji wobec MPZP terenu U,M 2
(Kielce Centrum - Solna, uchwała Nr XLI/1014/2009).

Użycie:
    python rozwiazania/01_sprawdz_mpzp.py [--plan P] [--inwestycja I] [--test]

Wczytuje plan.json (domyślnie rozwiazania/plan.json, uczestnik podaje --plan moje/plan.json) i dane/inwestycja.json, liczy sześć wskaźników z planu
(powierzchnia zabudowy, intensywność, powierzchnia biologicznie czynna,
wysokość, dach, parking) i porównuje je z limitami z sekcji "wskazniki" planu.
Definicje planu (sekcja "definicje") są nadrzędne wobec ogólnej wiedzy:
- intensywność liczy tylko kondygnacje nadziemne (nadziemna == true),
- powierzchnia biologicznie czynna liczy 50% każdego tarasu/stropodachu
  zielonego o powierzchni >= 10 m2; mniejsze tarasy nie liczą się wcale.

Wypisuje tabelę wyników: linia Wskaźnik | Wartość | Limit | Wynik na każdy
wskaźnik, z marginesem na osobnej, wciętej linii poniżej (żeby żadna linia
nie przekraczała 80 znaków).
Kod wyjścia: 1, jeśli którykolwiek wskaźnik nie jest OK, w przeciwnym razie 0.
Z flagą --test uruchamia _selftest() na danych ćwiczeniowych i zwraca 0.
"""

import argparse
import contextlib
import io
import json
import math
import sys
from pathlib import Path

# katalog dane/ leży o jeden poziom wyżej niż ten skrypt (rozwiazania/..)
DANE_DIR = Path(__file__).resolve().parents[1] / "dane"
PLAN_WZORCOWY = Path(__file__).resolve().parent / "plan.json"


def wczytaj(sciezka: str) -> dict:
    """Wczytuje plik JSON (UTF-8) i zwraca jego zawartość jako słownik."""
    with open(sciezka, "r", encoding="utf-8") as f:
        return json.load(f)


def oblicz(plan: dict, inw: dict) -> list:
    """
    Liczy sześć wskaźników MPZP dla terenu U,M 2 na podstawie planu i inwestycji.
    Zwraca listę sześciu wierszy w stałej kolejności:
    powierzchnia zabudowy, intensywność, pow. biologicznie czynna, wysokość,
    dach, parking. Każdy wiersz to słownik:
    {"wskaznik": str, "wartosc": str, "limit": str, "ok": bool, "margines": str}.
    """
    wsk = plan["wskazniki"]
    dzialka = inw["dzialka_m2"]
    wiersze = []

    # 1. Powierzchnia zabudowy = rzut budynku / dzialka (definicje.powierzchnia_zabudowy)
    pz = inw["powierzchnia_zabudowy_m2"]
    pz_pct = pz / dzialka * 100
    pz_limit_pct = wsk["powierzchnia_zabudowy_max_pct"]
    pz_limit_m2 = dzialka * pz_limit_pct / 100
    pz_ok = pz_pct <= pz_limit_pct
    pz_diff_pp = round(pz_pct - pz_limit_pct, 1)
    if pz_ok:
        margines = "{:+.1f} pp; {} m2 zapasu".format(pz_diff_pp, round(pz_limit_m2 - pz))
    else:
        margines = "{:+.1f} pp; {} m2 za dużo".format(pz_diff_pp, round(pz - pz_limit_m2))
    wiersze.append({
        "wskaznik": "powierzchnia zabudowy",
        "wartosc": "{:.1f} %".format(pz_pct),
        "limit": "<= {:.1f} %".format(pz_limit_pct),
        "ok": pz_ok,
        "margines": margines,
    })

    # 2. Intensywność = suma Po kondygnacji nadziemnych / dzialka (definicje.intensywnosc)
    suma_po = sum(k["powierzchnia_m2"] for k in inw["kondygnacje"] if k["nadziemna"])
    intensywnosc = suma_po / dzialka
    i_limit = wsk["intensywnosc_max"]
    i_ok = intensywnosc <= i_limit
    i_zapas = round(i_limit - intensywnosc, 2)
    i_y = round(i_limit * dzialka - suma_po)
    if i_zapas >= 0:
        margines = "zapas {:.2f}; {} m2 pow. całkowitej".format(i_zapas, i_y)
    else:
        margines = "przekroczenie {:.2f}; {} m2 pow. całkowitej".format(-i_zapas, i_y)
    wiersze.append({
        "wskaznik": "intensywność",
        "wartosc": "{:.2f}".format(intensywnosc),
        "limit": "<= {:.2f}".format(i_limit),
        "ok": i_ok,
        "margines": margines,
    })

    # 3. Pow. biologicznie czynna = grunt rodzimy + woda + 50% tarasów >= 10 m2
    #    (definicje.powierzchnia_biologicznie_czynna; tarasy < 10 m2 = 0)
    tbc = inw["teren_biologicznie_czynny"]
    tarasy_liczone = sum(0.5 * t for t in tbc["tarasy_i_stropodachy_zielone_m2"] if t >= 10)
    pbc_m2 = tbc["grunt_rodzimy_m2"] + tbc["woda_powierzchniowa_m2"] + tarasy_liczone
    pbc_pct = pbc_m2 / dzialka * 100
    pbc_limit_pct = wsk["pbc_min_pct"]
    pbc_ok = pbc_pct >= pbc_limit_pct
    pbc_diff_pp = round(pbc_pct - pbc_limit_pct, 1)
    pbc_wymagane_m2 = dzialka * pbc_limit_pct / 100
    if pbc_ok:
        margines = "{:+.1f} pp; zapas {} m2".format(pbc_diff_pp, round(pbc_m2 - pbc_wymagane_m2))
    else:
        margines = "{:+.1f} pp; brakuje {} m2".format(pbc_diff_pp, round(pbc_wymagane_m2 - pbc_m2))
    wiersze.append({
        "wskaznik": "pow. biologicznie czynna",
        "wartosc": "{:.1f} %".format(pbc_pct),
        "limit": ">= {:.1f} %".format(pbc_limit_pct),
        "ok": pbc_ok,
        "margines": margines,
    })

    # 4. Wysokość: najwyższa górna krawędź i liczba kondygnacji nadziemnych
    kondygnacje_nadziemne = [k for k in inw["kondygnacje"] if k["nadziemna"]]
    wys = wsk["wysokosc"]
    wys_h = max(k["gorna_krawedz_m"] for k in kondygnacje_nadziemne)
    wys_n = len(kondygnacje_nadziemne)
    wys_ok = wys_h <= wys["maksymalna_m"] and wys_n <= wys["maksymalna_kondygnacje"]
    wys_diff_m = round(wys["maksymalna_m"] - wys_h, 1)
    if wys_diff_m >= 0:
        margines = "{:.1f} m zapasu".format(wys_diff_m)
    else:
        margines = "{:.1f} m za dużo".format(-wys_diff_m)
    if wys_n > wys["maksymalna_kondygnacje"]:
        margines += "; {} kondygnacji za dużo".format(wys_n - wys["maksymalna_kondygnacje"])
    wiersze.append({
        "wskaznik": "wysokość",
        "wartosc": "{:.1f} m / {} kond.".format(wys_h, wys_n),
        "limit": "<= {:.1f} m / {} kond.".format(wys["maksymalna_m"], wys["maksymalna_kondygnacje"]),
        "ok": wys_ok,
        "margines": margines,
    })

    # 5. Dach: nachylenie wobec maksimum planu
    nachylenie = inw["dach"]["nachylenie_deg"]
    dach_limit = wsk["dach_nachylenie_max_deg"]
    dach_ok = nachylenie <= dach_limit
    if dach_ok:
        margines = "{:g}° zapasu".format(dach_limit - nachylenie)
    else:
        margines = "{:g}° za dużo".format(nachylenie - dach_limit)
    wiersze.append({
        "wskaznik": "dach",
        "wartosc": "{:g}°".format(nachylenie),
        "limit": "<= {:g}°".format(dach_limit),
        "ok": dach_ok,
        "margines": margines,
    })

    # 6. Parking: wymagane miejsca wg liczby mieszkań, dostępne wg trybu podziemny/naziemny
    park = wsk["parking"]
    tylko_podziemny = park["tylko_podziemny"]
    wymagane = math.ceil(inw["mieszkania"] * park["miejsc_na_mieszkanie_min"])
    podziemne = inw["miejsca_postojowe"]["podziemne"]
    naziemne = inw["miejsca_postojowe"]["naziemne"]
    dostepne = podziemne if tylko_podziemny else podziemne + naziemne
    park_ok = dostepne >= wymagane and (not tylko_podziemny or naziemne == 0)
    if dostepne >= wymagane:
        margines = "zapas {}".format(dostepne - wymagane)
    else:
        margines = "brakuje {}".format(wymagane - dostepne)
    if tylko_podziemny and naziemne > 0:
        margines += "; {} miejsc naziemnych niedozwolonych".format(naziemne)
    limit_txt = ">= {} miejsc, tylko podziemne".format(wymagane) if tylko_podziemny else ">= {} miejsc".format(wymagane)
    wiersze.append({
        "wskaznik": "parking",
        "wartosc": "{} podziemnych + {} naziemnych".format(podziemne, naziemne),
        "limit": limit_txt,
        "ok": park_ok,
        "margines": margines,
    })

    return wiersze


def tabela(wiersze: list) -> str:
    """
    Formatuje wiersze w czytelną tabelę i zwraca ją jako tekst. Cztery krótkie
    pola (Wskaźnik | Wartość | Limit | Wynik) trafiają w jedną linię na wiersz;
    margines - który dla niektórych wskaźników (np. parking) bywa długi -
    trafia w osobną linię poniżej, wcięty o 4 spacje. Sztywne wyrównanie
    wszystkich pięciu pól w jednej linii (poprzednia wersja) potrafiło dać
    linię długości ~145 znaków (np. wartość parkingu ma 29 znaków, limit
    parkingu też 29) - ten układ gwarantuje, że żadna linia nie przekracza
    80 znaków, bez zmiany treści któregokolwiek pola.
    """
    linie = ["Wskaźnik | Wartość | Limit | Wynik"]
    for w in wiersze:
        wynik = "OK" if w["ok"] else "NIE"
        linie.append("{} | {} | {} | {}".format(w["wskaznik"], w["wartosc"], w["limit"], wynik))
        linie.append("    Margines: {}".format(w["margines"]))
    return "\n".join(linie)


def _selftest():
    """Test wewnętrzny na danych ćwiczeniowych z rozwiazania/plan.json i dane/inwestycja.json."""
    plan = wczytaj(PLAN_WZORCOWY)
    inw = wczytaj(DANE_DIR / "inwestycja.json")
    wiersze = oblicz(plan, inw)

    oczekiwana_kolejnosc = [
        "powierzchnia zabudowy",
        "intensywność",
        "pow. biologicznie czynna",
        "wysokość",
        "dach",
        "parking",
    ]
    assert [w["wskaznik"] for w in wiersze] == oczekiwana_kolejnosc, "zła kolejność wskaźników"
    assert [w["ok"] for w in wiersze] == [False, True, False, True, True, False], "złe wyniki OK/NIE"

    zabudowa, intensywnosc, pbc, wysokosc, _dach, parking = wiersze

    assert abs(962 / 1850 * 100 - 52.0) < 1e-9
    assert zabudowa["wartosc"].startswith("52.0"), zabudowa["wartosc"]

    assert abs(5356 / 1850 - 2.8951351) < 1e-6
    assert intensywnosc["wartosc"] == "2.90", intensywnosc["wartosc"]

    assert abs(165 / 1850 * 100 - 8.9189189) < 1e-6
    assert pbc["wartosc"].startswith("8.9"), pbc["wartosc"]

    assert wysokosc["wartosc"] == "20.6 m / 6 kond.", wysokosc["wartosc"]

    assert "brakuje 3" in parking["margines"], parking["margines"]
    assert "3 miejsc naziemnych" in parking["margines"], parking["margines"]

    for linia in tabela(wiersze).split("\n"):
        assert len(linia) <= 80, "linia tabeli za długa ({} znaków): {}".format(len(linia), linia)

    bufor = io.StringIO()
    with contextlib.redirect_stdout(bufor):
        kod = main([])
    assert kod == 1, "main([]) na danych ćwiczeniowych powinno zwrócić 1"

    print("SELFTEST OK")


def main(argv: list) -> int:
    # ochrona przed brakiem reconfigure na przechwyconym stdout (np. io.StringIO
    # używanym przez _selftest() poprzez contextlib.redirect_stdout)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    parser = argparse.ArgumentParser(
        description="Sprawdzenie inwestycji wzgledem MPZP terenu U,M 2 (Kielce Centrum - Solna)."
    )
    parser.add_argument("--plan", default=PLAN_WZORCOWY, help="ścieżka do pliku plan.json (np. moje/plan.json z karty 00)")
    parser.add_argument("--inwestycja", default=DANE_DIR / "inwestycja.json", help="ścieżka do pliku inwestycja.json")
    parser.add_argument("--test", action="store_true", help="uruchom test wewnętrzny (_selftest) i zakończ")
    args = parser.parse_args(argv)

    if args.test:
        _selftest()
        return 0

    plan = wczytaj(args.plan)
    inw = wczytaj(args.inwestycja)
    wiersze = oblicz(plan, inw)
    print(tabela(wiersze))
    return 0 if all(w["ok"] for w in wiersze) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

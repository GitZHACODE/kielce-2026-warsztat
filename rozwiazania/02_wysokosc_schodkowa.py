#! python 3
"""
Karta 02: wysokość schodkowa wg planu dla terenu U,M 2 (Kielce Centrum - Solna).

Zasada z wskazniki.wysokosc (plan.json, wzorzec w rozwiazania/plan.json):
- wysokość podstawowa: 14.0 m / 4 kondygnacje nadziemne, bez wymogu cofnięcia,
- wysokość maksymalna: 21.0 m / 6 kondygnacji nadziemnych, o ile kondygnacje
  powyżej wysokości podstawowej cofają się o co najmniej 1.5 m zarówno od
  linii KDP-1, jak i od ul. Solnej.

Skrypt sprawdza każdą kondygnację nadziemną z dane/inwestycja.json wobec tej
zasady, dolicza wiersz podsumowania całego budynku i wypisuje tabelę
wyników. Kod wyjścia to 1, jeśli którykolwiek wiersz (także podsumowanie
budynku) nie spełnia wymogu planu.
"""

import argparse
import contextlib
import io
import json
import os
import sys


def sprawdz_wysokosc(plan, inw):
    """
    Sprawdza każdą kondygnację nadziemną budynku wobec zasady wysokości
    schodkowej z planu. Zwraca listę słowników - jeden na kondygnację
    nadziemną, plus końcowy wiersz podsumowania budynku (nr == "budynek").
    Kondygnacje z nadziemna == false (np. garaż podziemny) są pomijane.
    """
    w = plan["wskazniki"]["wysokosc"]
    podstawowa_m = w["podstawowa_m"]
    podstawowa_kondygnacje = w["podstawowa_kondygnacje"]
    maksymalna_m = w["maksymalna_m"]
    maksymalna_kondygnacje = w["maksymalna_kondygnacje"]
    min_cofniecie = w["cofniecie_kondygnacji_powyzej_podstawowej_min_m"]

    wyniki = []
    for k in inw["kondygnacje"]:
        if not k.get("nadziemna", False):
            continue  # kondygnacje podziemne nie podlegają tej zasadzie

        nr = k["nr"]
        gorna = k["gorna_krawedz_m"]
        wymaga = gorna > podstawowa_m or nr > podstawowa_kondygnacje

        uwagi = []
        if wymaga:
            kdp1 = k["cofniecie_od_KDP1_m"]
            solna = k["cofniecie_od_Solnej_m"]
            if kdp1 < min_cofniecie:
                uwagi.append(
                    "cofnięcie od KDP-1 {:.1f} m < {:.1f} m".format(kdp1, min_cofniecie)
                )
            if solna < min_cofniecie:
                uwagi.append(
                    "cofnięcie od Solnej {:.1f} m < {:.1f} m".format(solna, min_cofniecie)
                )
            ok = len(uwagi) == 0
        else:
            ok = gorna <= podstawowa_m

        wyniki.append({
            "nr": nr,
            "gorna_krawedz_m": gorna,
            "wymaga_cofniecia": wymaga,
            "ok": ok,
            "uwaga": "; ".join(uwagi),
        })

    najwyzsza = max((r["gorna_krawedz_m"] for r in wyniki), default=0.0)
    liczba_nadziemnych = len(wyniki)

    # Podsumowanie budynku: sprawdza pułap wysokości i liczby kondygnacji
    # łącznie, niezależnie od tego, czy każda kondygnacja z osobna jest OK.
    uwagi_budynku = []
    if najwyzsza > maksymalna_m:
        uwagi_budynku.append(
            "wysokość budynku {:.1f} m > {:.1f} m".format(najwyzsza, maksymalna_m)
        )
    if liczba_nadziemnych > maksymalna_kondygnacje:
        uwagi_budynku.append(
            "liczba kondygnacji {} > {}".format(liczba_nadziemnych, maksymalna_kondygnacje)
        )

    wyniki.append({
        "nr": "budynek",
        "gorna_krawedz_m": najwyzsza,
        "wymaga_cofniecia": any(r["wymaga_cofniecia"] for r in wyniki),
        "ok": len(uwagi_budynku) == 0,
        "uwaga": "; ".join(uwagi_budynku),
    })
    return wyniki


def tabela(wyniki):
    """
    Formatuje wyniki w tabelę o stałej szerokości kolumn (Kondygnacja |
    Górna krawędź | Wymaga cofnięcia | Wynik) i zwraca ją jako tekst. Wiersz
    z niepustą uwagą dostaje dodatkową linię kontynuacji poniżej, wciętą o
    cztery spacje i poprzedzoną "uwaga: ", żeby żadna linia tabeli nie
    przekraczała 80 znaków.
    """
    naglowki = ["Kondygnacja", "Górna krawędź", "Wymaga cofnięcia", "Wynik"]
    kolumny = [
        [
            str(r["nr"]),
            "{:.1f} m".format(r["gorna_krawedz_m"]),
            "TAK" if r["wymaga_cofniecia"] else "NIE",
            "OK" if r["ok"] else "NIE",
        ]
        for r in wyniki
    ]
    szerokosci = [len(h) for h in naglowki]
    for wiersz in kolumny:
        for i, kom in enumerate(wiersz):
            szerokosci[i] = max(szerokosci[i], len(kom))

    def formatuj(wiersz):
        return " | ".join(kom.ljust(szerokosci[i]) for i, kom in enumerate(wiersz))

    linie = [formatuj(naglowki), "-+-".join("-" * s for s in szerokosci)]
    for wiersz, r in zip(kolumny, wyniki):
        linie.append(formatuj(wiersz))
        if r["uwaga"]:
            linie.append("    uwaga: " + r["uwaga"])
    return "\n".join(linie)


def _selftest():
    """Test wewnętrzny na danych ćwiczeniowych z rozwiazania/plan.json i dane/inwestycja.json."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(root, "rozwiazania", "plan.json"), "r", encoding="utf-8") as f:
        plan = json.load(f)
    with open(os.path.join(root, "dane", "inwestycja.json"), "r", encoding="utf-8") as f:
        inw = json.load(f)

    wyniki = sprawdz_wysokosc(plan, inw)
    by_nr = dict((r["nr"], r) for r in wyniki)

    for nr in (1, 2, 3, 4):
        assert by_nr[nr]["ok"] is True, "kondygnacja {} powinna być OK".format(nr)
        assert by_nr[nr]["wymaga_cofniecia"] is False, "kondygnacja {} nie powinna wymagać cofnięcia".format(nr)

    assert by_nr[5]["wymaga_cofniecia"] is True, "kondygnacja 5 powinna wymagać cofnięcia"
    assert by_nr[5]["ok"] is False, "kondygnacja 5 powinna być NIE (cofnięcie od Solnej za małe)"
    assert "Solnej" in by_nr[5]["uwaga"], "uwaga kondygnacji 5 powinna wskazywać Solną"
    assert "1.2" in by_nr[5]["uwaga"], "uwaga kondygnacji 5 powinna podawać 1.2 m"

    assert by_nr[6]["ok"] is True, "kondygnacja 6 powinna być OK (cofnięcie 2.0 m z obu stron)"

    budynek = by_nr["budynek"]
    assert budynek["ok"] is True, "podsumowanie budynku powinno być OK (20.6 m / 21.0 m, 6 / 6 kondygnacji)"

    # main([]) drukuje pełną tabelę na stdout - przechwytujemy ją do bufora,
    # żeby --test wypisywał wyłącznie "SELFTEST OK".
    bufor = io.StringIO()
    with contextlib.redirect_stdout(bufor):
        kod = main([])
    assert kod == 1, "main() na danych ćwiczeniowych (kondygnacja 5 NIE) powinno zwrócić 1"

    tekst_tabeli = bufor.getvalue()
    assert all(len(linia) <= 80 for linia in tekst_tabeli.splitlines()), (
        "każda linia tabeli() powinna mieć co najwyżej 80 znaków"
    )

    print("SELFTEST OK")


def main(argv):
    # ochrona przed brakiem reconfigure na przechwyconym stdout (np. io.StringIO
    # używanym przez _selftest() poprzez contextlib.redirect_stdout)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    parser = argparse.ArgumentParser(
        description="Sprawdza wysokość schodkową budynku wobec planu dla terenu U,M 2."
    )
    parser.add_argument("--test", action="store_true", help="Uruchom test wewnętrzny (_selftest) i zakończ.")
    parser.add_argument("--plan", default=None, help="Ścieżka do pliku plan.json (domyślnie rozwiazania/plan.json; uczestnik podaje moje/plan.json).")
    parser.add_argument("--inwestycja", default=None, help="Ścieżka do pliku inwestycja.json (domyślnie dane/inwestycja.json).")
    args = parser.parse_args(argv)

    if args.test:
        _selftest()
        return 0

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    plan_path = args.plan or os.path.join(root, "rozwiazania", "plan.json")
    inw_path = args.inwestycja or os.path.join(root, "dane", "inwestycja.json")

    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)
    with open(inw_path, "r", encoding="utf-8") as f:
        inw = json.load(f)

    wyniki = sprawdz_wysokosc(plan, inw)
    print(tabela(wyniki))

    return 1 if any(not r["ok"] for r in wyniki) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

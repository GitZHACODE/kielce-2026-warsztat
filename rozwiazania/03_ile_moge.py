#! python 3
"""Karta 03 "Ile mogę" - rozwiązanie wzorcowe.

Dla każdego wskaźnika planu (teren U,M 2), którego fikcyjna inwestycja
(dane/inwestycja.json) nie spełnia, wypisuje najmniejszą zmianę potrzebną,
żeby go spełnić. Wzory takie same jak w karcie 01 (sprawdzacz):
- powierzchnia zabudowy = rzut budynku / działka,
- intensywność = suma powierzchni kondygnacji nadziemnych / działka
  (definicja planu, garaż podziemny wyłączony),
- powierzchnia biologicznie czynna = grunt rodzimy + woda + 50% każdego
  tarasu zielonego >= 10 m2 (mniejsze liczą się jako zero),
- wysokość = najwyższa górna krawędź i liczba kondygnacji nadziemnych,
- nachylenie dachu,
- parking = mieszkania x miejsca/mieszkanie, tylko podziemny gdy plan
  tego wymaga.
"""

import argparse
import json
import sys
from pathlib import Path

# katalog dane/ leży o jeden poziom wyżej niż ten skrypt (rozwiazania/..)
DANE_DIR = Path(__file__).resolve().parents[1] / "dane"
PLAN_WZORCOWY = Path(__file__).resolve().parent / "plan.json"


def _wczytaj_json(sciezka):
    with open(sciezka, "r", encoding="utf-8") as f:
        return json.load(f)


def propozycje(plan: dict, inw: dict) -> list:
    """Zwraca 6 linii - po jednej na wskaźnik, w kolejności karty 01."""
    lines = []
    dzialka = inw["dzialka_m2"]
    wsk = plan["wskazniki"]

    # 1. Powierzchnia zabudowy = rzut budynku / działka.
    max_pct = wsk["powierzchnia_zabudowy_max_pct"]
    max_m2 = dzialka * max_pct / 100
    zabudowa = inw["powierzchnia_zabudowy_m2"]
    if zabudowa > max_m2:
        diff = zabudowa - max_m2
        lines.append(
            "Powierzchnia zabudowy: zmniejsz do {:.0f} m2 (usuń {:.0f} m2).".format(max_m2, diff)
        )
    else:
        zapas = max_m2 - zabudowa
        lines.append("Powierzchnia zabudowy: OK, zapas {:.0f} m2.".format(zapas))

    # 2. Intensywność = suma powierzchni kondygnacji nadziemnych / działka
    #    (garaż podziemny wyłączony z definicji planu).
    suma = sum(k["powierzchnia_m2"] for k in inw["kondygnacje"] if k["nadziemna"])
    max_i = wsk["intensywnosc_max"]
    max_total = max_i * dzialka
    if suma > max_total:
        nadwyzka = suma - max_total
        lines.append(
            "Intensywność: przekroczono, zmniejsz sumę powierzchni nadziemnych o {:.0f} m2 "
            "(masz {:.0f} m2 przy limicie {} x {:.0f} m2 = {:.0f} m2).".format(
                nadwyzka, suma, max_i, dzialka, max_total
            )
        )
    else:
        headroom = max_total - suma
        lines.append(
            "Intensywność: zapas {:.0f} m2 powierzchni całkowitej (limit {} przy {:.0f} m2).".format(
                headroom, max_i, suma
            )
        )

    # 3. Powierzchnia biologicznie czynna = grunt rodzimy + woda +
    #    50% każdego tarasu zielonego >= 10 m2 (mniejsze liczą się jako zero).
    pbc_min = dzialka * wsk["pbc_min_pct"] / 100
    tbc = inw["teren_biologicznie_czynny"]
    grunt = tbc["grunt_rodzimy_m2"]
    woda = tbc["woda_powierzchniowa_m2"]
    tarasy_pbc = sum(t * 0.5 for t in tbc["tarasy_i_stropodachy_zielone_m2"] if t >= 10)
    pbc_actual = grunt + woda + tarasy_pbc
    if pbc_actual < pbc_min:
        brak = pbc_min - pbc_actual
        lines.append(
            "Powierzchnia biologicznie czynna: brakuje {:.0f} m2 - dodaj {:.0f} m2 gruntu "
            "rodzimego albo {:.0f} m2 zielonego tarasu (każdy taras co najmniej 10 m2, "
            "liczy się 50 %).".format(brak, brak, 2 * brak)
        )
    else:
        zapas_pbc = pbc_actual - pbc_min
        lines.append("Powierzchnia biologicznie czynna: OK, zapas {:.0f} m2.".format(zapas_pbc))

    # 4. Wysokość = najwyższa górna krawędź i liczba kondygnacji nadziemnych.
    kondygnacje_nadziemne = [k for k in inw["kondygnacje"] if k["nadziemna"]]
    najwyzsza = max(k["gorna_krawedz_m"] for k in kondygnacje_nadziemne)
    n = len(kondygnacje_nadziemne)
    max_h = wsk["wysokosc"]["maksymalna_m"]
    max_k = wsk["wysokosc"]["maksymalna_kondygnacje"]
    if najwyzsza > max_h or n > max_k:
        lines.append(
            "Wysokość: obniż budynek do {:.1f} m i/lub zmniejsz do {} kondygnacji nadziemnych "
            "(masz {:.1f} m i {} kondygnacji).".format(max_h, max_k, najwyzsza, n)
        )
    else:
        headroom_h = max_h - najwyzsza
        lines.append(
            "Wysokość: OK, zapas {:.1f} m do {} m; kondygnacji {} z {}.".format(
                headroom_h, max_h, n, max_k
            )
        )

    # 5. Nachylenie dachu.
    deg = inw["dach"]["nachylenie_deg"]
    max_deg = wsk["dach_nachylenie_max_deg"]
    if deg > max_deg:
        lines.append("Dach: zmniejsz nachylenie do {}° (masz {}°).".format(max_deg, deg))
    else:
        lines.append("Dach: OK ({}° przy limicie {}°).".format(deg, max_deg))

    # 6. Parking = mieszkania x miejsca/mieszkanie; tylko podziemny gdy plan tego wymaga.
    mieszkania = inw["mieszkania"]
    per_flat = wsk["parking"]["miejsc_na_mieszkanie_min"]
    required = mieszkania * per_flat
    tylko_podziemny = wsk["parking"]["tylko_podziemny"]
    podziemne = inw["miejsca_postojowe"]["podziemne"]
    naziemne = inw["miejsca_postojowe"]["naziemne"]
    if tylko_podziemny:
        brakuje = max(0, required - podziemne)
        if brakuje > 0 or naziemne > 0:
            lines.append(
                "Parking: brakuje {} miejsc podziemnych; {} miejsc naziemnych trzeba usunąć "
                "lub przenieść pod ziemię (plan dopuszcza tylko parking podziemny).".format(
                    brakuje, naziemne
                )
            )
        else:
            lines.append(
                "Parking: OK, {} miejsc podziemnych (wymagane {}).".format(podziemne, required)
            )
    else:
        total = podziemne + naziemne
        if total < required:
            lines.append(
                "Parking: brakuje {} miejsc (masz {}, wymagane {}).".format(
                    required - total, total, required
                )
            )
        else:
            lines.append("Parking: OK, {} miejsc (wymagane {}).".format(total, required))

    return lines


def _selftest():
    plan = _wczytaj_json(PLAN_WZORCOWY)
    inw = _wczytaj_json(DANE_DIR / "inwestycja.json")
    linie = propozycje(plan, inw)
    assert len(linie) == 6, "oczekiwano 6 linii, jest {}".format(len(linie))
    oczekiwane = [
        ["925", "37"],
        ["1119"],
        ["20 m2", "40 m2"],
        ["0.4 m"],
        ["5°"],
        ["brakuje 3", "3 miejsc naziemnych"],
    ]
    for linia, fragmenty in zip(linie, oczekiwane):
        for fragment in fragmenty:
            assert fragment in linia, "brak '{}' w linii: {}".format(fragment, linia)
    print("SELFTEST OK")


def main(argv):
    # ochrona przed brakiem reconfigure na przechwyconym stdout (np. io.StringIO)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    parser = argparse.ArgumentParser(
        description='Karta 03 "Ile mogę" - najmniejsza zmiana, by spełnić każdy wskaźnik planu.'
    )
    parser.add_argument("--plan", default=PLAN_WZORCOWY, help="ścieżka do pliku plan.json (np. moje/plan.json z karty 00)")
    parser.add_argument("--inwestycja", default=DANE_DIR / "inwestycja.json", help="ścieżka do pliku inwestycja.json")
    parser.add_argument("--test", action="store_true", help="uruchom test wewnętrzny (_selftest) i zakończ")
    args = parser.parse_args(argv)

    if args.test:
        _selftest()
        return 0

    plan = _wczytaj_json(args.plan)
    inw = _wczytaj_json(args.inwestycja)
    for linia in propozycje(plan, inw):
        print(linia)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

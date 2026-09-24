#! python 3
"""Test geometrii kart 05, 06 i 07 oraz przykładów z przyklady/ bez otwierania Rhino
(narzędzie prowadzącego).

Ładuje RhinoCommon z zainstalowanego Rhino 8 przez Rhino.Inside, buduje
szkic bryły "Solna" z tabeli PROSTOKATY (05_szkic_bryly_rhino.py) bez
dokumentu Rhino, uruchamia 06_bryla_gh.py i 07_elewacja_gh.py tak, jak robi
to Grasshopper (exec z wejściami w globals), podaje wynik karty 06 do
funkcji oblicz() z karty 05 i sprawdza wartości oczekiwane ze specyfikacji.
Potem uruchamia oba przykłady zaawansowane (bryla_zaawansowana_gh.py,
elewacja_zaawansowana_gh.py) bez wejść i na wszystkich kombinacjach wzoru
i typu panelu, i podaje bryłę zaawansowaną do tej samej kontroli z karty 05.

Wymaga osobnego środowiska Pythona 3.9 z pakietami pythonnet i rhinoinside
(na maszynie prowadzącego: conda env kielce-rhino). Żadna karta ani żaden
skrypt w rozwiazania/ nie zależy od tego pliku.

Uruchomienie (z katalogu głównego repozytorium):
    conda run -n kielce-rhino --no-capture-output python narzedzia/test_geometrii_rhino_inside.py
"""

import json
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

import rhinoinside  # noqa: E402

RHINO_SYSTEM = r"C:\Program Files\Rhino 8\System"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROZW = os.path.join(ROOT, "rozwiazania")
PRZYKLADY = os.path.join(ROOT, "przyklady")


def wczytaj_skrypt(nazwa, wejscia, folder=ROZW):
    """Wykonuje skrypt komponentu z podanymi wejściami jak Grasshopper i zwraca globals."""
    sciezka = os.path.join(folder, nazwa)
    with open(sciezka, "r", encoding="utf-8") as f:
        zrodlo = f.read()
    g = {"__name__": "gh_" + nazwa.split(".")[0], "__file__": sciezka}
    g.update(wejscia)
    exec(compile(zrodlo, sciezka, "exec"), g)
    return g


def pole(krzywa, rg):
    amp = rg.AreaMassProperties.Compute(krzywa)
    return amp.Area if amp is not None else 0.0


def main():
    t0 = time.time()
    rhinoinside.load(RHINO_SYSTEM)
    import Rhino
    import Rhino.Geometry as rg
    import System.Drawing
    print("Rhino {} załadowane w {:.1f} s".format(Rhino.RhinoApp.Version, time.time() - t0))

    # Szkic bryły z tabeli PROSTOKATY, bez dokumentu Rhino.
    szkic = wczytaj_skrypt("05_szkic_bryly_rhino.py", {})
    krzywe = {"Kondygnacje": [], "Dzialka": [], "Zabudowa": [], "PBC-grunt": [], "PBC-tarasy": []}
    for warstwa, x0, y0, x1, y1, z in szkic["PROSTOKATY"]:
        krzywa = rg.Rectangle3d(rg.Plane.WorldXY, rg.Interval(x0, x1), rg.Interval(y0, y1)).ToNurbsCurve()
        krzywa.Transform(rg.Transform.Translation(0.0, 0.0, z))
        krzywe[warstwa].append(krzywa)
    kondygnacje = krzywe["Kondygnacje"]
    assert len(kondygnacje) == 7, len(kondygnacje)

    # Karta 06 z domyślnymi suwakami.
    g6 = wczytaj_skrypt("06_bryla_gh.py", {"kondygnacje": kondygnacje})
    for linia in g6["raport"]:
        print("  06:", linia)
    bryla = g6["bryla"]
    assert bryla is not None, "brak bryły"
    assert bryla.IsSolid, "bryła nie jest zamknięta"
    objetosc = rg.VolumeMassProperties.Compute(bryla).Volume
    assert 12000.0 < objetosc < 26000.0, objetosc
    nowe = g6["kondygnacje_nowe"]
    assert len(nowe) == 7, len(nowe)
    assert abs(nowe[0].GetBoundingBox(True).Max.Z - (-3.0)) < 1e-6, "garaż ma przejść bez zmian jako pierwszy"
    oczekiwane = [962.0, 962.0, 962.0, 962.0, 782.0, 726.0]
    for krzywa, stare in zip(nowe[1:], oczekiwane):
        assert krzywa.IsClosed, "nowy obrys nie jest zamknięty"
        p = pole(krzywa, rg)
        assert 0.65 * stare < p < 1.35 * stare, (p, stare)
    obrys = g6["zabudowa_nowa"]
    assert obrys is not None and obrys.IsClosed
    obrys_m2 = pole(obrys, rg)
    assert 900.0 < obrys_m2 < 1400.0, obrys_m2
    assert len(g6["plyty"]) == 6, len(g6["plyty"])
    assert len(g6["kontury"]) > 10, len(g6["kontury"])
    print("  06: objętość {:.0f} m3, obrys {:.1f} m2, kontury {}".format(objetosc, obrys_m2, len(g6["kontury"])))

    # Wklejony komponent bez kabli: każdy skrypt niesie kopię tabeli PROSTOKATY
    # i ma od razu coś pokazać, z ostrzeżeniem w pierwszej linii raportu.
    g6d = wczytaj_skrypt("06_bryla_gh.py", {})
    assert g6d["DOMYSLNA_MASA"] == szkic["PROSTOKATY"], "06: DOMYSLNA_MASA rozjechała się ze szkicem"
    assert g6d["raport"][0].startswith("uwaga:") and "domyślnej masy" in g6d["raport"][0], g6d["raport"][:1]
    assert g6d["bryla"] is not None and g6d["bryla"].IsSolid, g6d["raport"]
    assert len(g6d["kondygnacje_nowe"]) == 7 and len(g6d["plyty"]) == 6, (len(g6d["kondygnacje_nowe"]), len(g6d["plyty"]))
    g7d = wczytaj_skrypt("07_elewacja_gh.py", {})
    assert g7d["DOMYSLNA_MASA"] == szkic["PROSTOKATY"], "07: DOMYSLNA_MASA rozjechała się ze szkicem"
    assert g7d["raport"][0].startswith("uwaga:") and "domyślnej masy" in g7d["raport"][0], g7d["raport"][:1]
    assert g7d["panele"] is not None and g7d["panele"].IsValid, g7d["raport"]
    assert len(g7d["ekspozycja"]) == 198 and max(g7d["ekspozycja"]) > 0.5, (len(g7d["ekspozycja"]), max(g7d["ekspozycja"]))
    print("  bez wejść: 06 objętość {:.0f} m3, 07 {} paneli".format(
        rg.VolumeMassProperties.Compute(g6d["bryla"]).Volume, len(g7d["ekspozycja"])))

    # Karta 05 bez wejść: domyślna masa i wbudowane limity dają tabelę z karty 01.
    g5 = wczytaj_skrypt("05_sprawdz_mpzp_gh.py", {})
    assert g5["DOMYSLNA_MASA"] == szkic["PROSTOKATY"], "05: DOMYSLNA_MASA rozjechała się ze szkicem"
    assert g5["raport"][0].startswith("uwaga:") and "domyślnej masy" in g5["raport"][0], g5["raport"][:2]
    wiersze5 = [w for w in g5["raport"] if " | limit " in w]
    assert len(wiersze5) == 6, g5["raport"]
    assert "52.0 %" in wiersze5[0] and "2.90" in wiersze5[1] and "20.6 m / 6 kond." in wiersze5[3], wiersze5
    assert g5["ok"] is False and len(g5["kolory"]) == 7 and len(g5["plyty"]) == 7, (
        g5["ok"], len(g5["kolory"]), len(g5["plyty"]))
    assert "| NIE |" in wiersze5[5] and "3 miejsc naziemnych niedozwolonych" in wiersze5[5], wiersze5[5]
    for linia in g5["raport"]:
        print("  05 (bez wejść):", linia)

    # Karta 05 częściowo okablowana (bez kondygnacji): żadnego wiersza OK, ok = False.
    g5p = wczytaj_skrypt("05_sprawdz_mpzp_gh.py",
                         {"dzialka": krzywe["Dzialka"][0], "zabudowa": krzywe["Zabudowa"][0]})
    assert g5p["ok"] is False and not [w for w in g5p["raport"] if " | limit " in w], g5p["raport"]
    assert any("wejścia kondygnacje puste" in w for w in g5p["raport"]), g5p["raport"]

    # Wynik karty 06 do kontroli z karty 05.
    with open(os.path.join(ROZW, "plan.json"), "r", encoding="utf-8") as f:
        limity = json.load(f)["wskazniki"]
    dzialka_m2 = pole(krzywe["Dzialka"][0], rg)
    kond = [(g5["pole"](c), g5["gora"](c)) for c in nowe]
    wiersze = g5["oblicz"](dzialka_m2, obrys_m2, kond, 120.0, 0.0, [90.0, 8.0], 30, 27, 3, limity)
    for w in wiersze:
        print("  05: {}: {} | {} | {}".format(w["wskaznik"], w["wartosc"], "OK" if w["ok"] else "NIE", w["margines"]))
    assert wiersze[3]["wartosc"] == "20.6 m / 6 kond.", wiersze[3]["wartosc"]

    # Karta 06 z pełnym zaokrągleniem na wąskich, cofniętych kondygnacjach.
    g6b = wczytaj_skrypt("06_bryla_gh.py", {"kondygnacje": kondygnacje, "zaokraglenie": 1.0, "skret_deg": 40.0, "wybrzuszenie": 0.3})
    assert g6b["bryla"] is not None and g6b["bryla"].IsSolid, g6b["raport"]
    print("  06 (zaokraglenie 1.0, skret 40, wybrzuszenie 0.3): objętość {:.0f} m3".format(
        rg.VolumeMassProperties.Compute(g6b["bryla"]).Volume))

    # Karta 07 na bryle z karty 06.
    g7 = wczytaj_skrypt("07_elewacja_gh.py", {"bryla": bryla})
    for linia in g7["raport"]:
        print("  07:", linia)
    panele = g7["panele"]
    assert panele is not None and panele.IsValid, "siatka paneli nieprawidłowa"
    assert panele.Faces.Count == 198 * 4 + 36, panele.Faces.Count
    eks = g7["ekspozycja"]
    assert len(eks) == 198, len(eks)
    # Ściana północna (+Y) w południe ma ekspozycję dokładnie 0, południowa ponad 0.5.
    assert min(eks) == 0.0 and max(eks) > 0.5, (min(eks), max(eks))
    assert len(g7["siatka"]) == 198
    assert panele.VertexColors.Count == panele.Vertices.Count, (panele.VertexColors.Count, panele.Vertices.Count)

    # Karta 07 na zwykłym pudełku: same ściany płaskie, brak zawinięcia.
    pudelko = rg.Box(rg.Plane.WorldXY, rg.Interval(0, 30), rg.Interval(0, 20), rg.Interval(0, 15)).ToBrep()
    g7b = wczytaj_skrypt("07_elewacja_gh.py", {"bryla": pudelko})
    assert g7b["panele"] is not None and g7b["panele"].IsValid, g7b["raport"]
    assert g7b["panele"].Faces.Count > 0
    print("  07 (pudełko): {} ścianek siatki".format(g7b["panele"].Faces.Count))

    # Przykład zaawansowany: bryła z profilem, skrętem i atraktorem, bez wejść i z wejściami.
    ga = wczytaj_skrypt("bryla_zaawansowana_gh.py", {}, PRZYKLADY)
    assert ga["DOMYSLNA_MASA"] == szkic["PROSTOKATY"], "bryla_zaawansowana: DOMYSLNA_MASA rozjechała się ze szkicem"
    assert ga["raport"][0].startswith("uwaga: wejście kondygnacje puste"), ga["raport"][:2]
    assert ga["raport"][1].startswith("uwaga: wejście atraktor puste"), ga["raport"][:2]
    for linia in ga["raport"]:
        print("  bryla_zaaw:", linia)
    assert ga["bryla"] is not None and ga["bryla"].IsSolid, ga["raport"]
    assert len(ga["kondygnacje_nowe"]) == 7 and len(ga["plyty"]) == 6 and len(ga["przekroje"]) == 7, (
        len(ga["kondygnacje_nowe"]), len(ga["plyty"]), len(ga["przekroje"]))
    assert all(k.IsClosed for k in ga["przekroje"]) and ga["zabudowa_nowa"] is not None and ga["zabudowa_nowa"].IsClosed
    assert ga["atraktor_uzyty"] is not None and abs(ga["atraktor_uzyty"].X - 60.0) < 1e-9
    obj_a = rg.VolumeMassProperties.Compute(ga["bryla"]).Volume
    assert 17000.0 < obj_a < 21000.0, obj_a   # zmierzone 18779 m3; szerszy przedział przepuściłby brak skrętu, wybrzuszenia albo atraktora
    assert len(ga["kontury"]) > 10, len(ga["kontury"])
    kond_a = [(g5["pole"](c), g5["gora"](c)) for c in ga["kondygnacje_nowe"]]
    wiersze_a = g5["oblicz"](dzialka_m2, pole(ga["zabudowa_nowa"], rg), kond_a, 120.0, 0.0, [90.0, 8.0], 30, 27, 3, limity)
    assert wiersze_a[3]["wartosc"] == "20.6 m / 6 kond.", wiersze_a[3]["wartosc"]
    # Bez atraktora objętość się zmienia; prostokąt zaokrąglony i wejścia ze szkicu też loftują.
    ga0 = wczytaj_skrypt("bryla_zaawansowana_gh.py", {"kondygnacje": kondygnacje, "sila_atraktora_m": 0.0,
                                                      "atraktor": rg.Point3d(60.0, 18.5, 10.0)}, PRZYKLADY)
    assert ga0["bryla"] is not None and ga0["bryla"].IsSolid and not ga0["raport"][0].startswith("uwaga:"), ga0["raport"][:2]
    obj_0 = rg.VolumeMassProperties.Compute(ga0["bryla"]).Volume
    assert abs(obj_0 - obj_a) > 50.0, (obj_0, obj_a)
    ga1 = wczytaj_skrypt("bryla_zaawansowana_gh.py", {"kondygnacje": kondygnacje, "typ_profilu": 0, "zaokraglenie": 0.3,
                                                      "profil_skretu": 2, "wykladnik_profilu": 8.0}, PRZYKLADY)
    assert ga1["bryla"] is not None and ga1["bryla"].IsSolid, ga1["raport"]
    assert any("prostokąt zaokrąglony" in l for l in ga1["raport"]), ga1["raport"]
    ga9 = wczytaj_skrypt("bryla_zaawansowana_gh.py", {"kondygnacje": kondygnacje, "typ_profilu": 9}, PRZYKLADY)
    assert ga9["bryla"] is not None and any("typ_profilu 9 nieznany" in l for l in ga9["raport"]), ga9["raport"][:3]
    print("  bryla_zaaw: objętość {:.0f} m3 (bez atraktora {:.0f} m3), obrys {:.1f} m2".format(
        obj_a, obj_0, pole(ga["zabudowa_nowa"], rg)))

    # Przykład zaawansowany: elewacja bez wejść, potem każdy wzór z każdym typem panelu na bryle wyżej.
    ge = wczytaj_skrypt("elewacja_zaawansowana_gh.py", {}, PRZYKLADY)
    assert ge["DOMYSLNA_MASA"] == szkic["PROSTOKATY"], "elewacja_zaawansowana: DOMYSLNA_MASA rozjechała się ze szkicem"
    assert ge["raport"][0].startswith("uwaga: wejście bryla puste") and ge["raport"][1].startswith("uwaga: wejście atraktory puste"), ge["raport"][:2]
    for linia in ge["raport"]:
        print("  elew_zaaw:", linia)
    assert ge["panele"] is not None and ge["panele"].IsValid and ge["panele"].Faces.Count > 0, ge["raport"]
    assert len(ge["siatka"]) == len(ge["intensywnosc_paneli"]) == len(ge["srodki"]) == len(ge["otwory"]) > 0
    assert ge["panele"].VertexColors.Count == ge["panele"].Vertices.Count
    assert 0.0 <= min(ge["intensywnosc_paneli"]) < max(ge["intensywnosc_paneli"]) <= 1.0
    for typ_wzoru in range(4):
        for typ_panelu in range(3):
            gx = wczytaj_skrypt("elewacja_zaawansowana_gh.py",
                                {"bryla": ga["bryla"], "typ_wzoru": typ_wzoru, "typ_panelu": typ_panelu,
                                 "atraktory": [rg.Point3d(25.0, -20.0, 12.0)], "paleta": typ_panelu}, PRZYKLADY)
            assert gx["panele"] is not None and gx["panele"].IsValid, (typ_wzoru, typ_panelu, gx["raport"])
            # Ściana loftu jest zamknięta wokół budynku; liczba paneli musi zgadzać się z wzorem.
            oczekiwane_paneli = len(gx["WZORY"][typ_wzoru](gx["DOMYSLNE"]["kolumny"], gx["DOMYSLNE"]["rzedy"], True))
            assert len(gx["siatka"]) == oczekiwane_paneli, (typ_wzoru, typ_panelu, len(gx["siatka"]), oczekiwane_paneli)
            assert (len(gx["otwory"]) == oczekiwane_paneli) if typ_panelu != 1 else (len(gx["otwory"]) == 0), (typ_panelu, len(gx["otwory"]))
            assert not gx["raport"][0].startswith("uwaga:"), gx["raport"][:2]
    gz = wczytaj_skrypt("elewacja_zaawansowana_gh.py", {"bryla": ga["bryla"], "typ_wzoru": 9,
                                                        "atraktory": [rg.Point3d(25.0, -20.0, 12.0)]}, PRZYKLADY)
    assert gz["panele"] is not None and gz["panele"].IsValid, gz["raport"][:3]
    assert any("typ_wzoru 9 nieznany" in l for l in gz["raport"]), gz["raport"][:3]
    # Tylko jeden kolor własny: paleta zostaje, z ostrzeżeniem; oba: kolory własne.
    gk = wczytaj_skrypt("elewacja_zaawansowana_gh.py",
                        {"bryla": pudelko, "kolor_jasny": System.Drawing.Color.FromArgb(255, 255, 255)}, PRZYKLADY)
    assert any("tylko jeden z kolorów" in l for l in gk["raport"]) and any(l == "paleta: grafit" for l in gk["raport"]), gk["raport"]
    gk2 = wczytaj_skrypt("elewacja_zaawansowana_gh.py",
                         {"bryla": pudelko, "kolor_jasny": System.Drawing.Color.FromArgb(255, 255, 255),
                          "kolor_ciemny": System.Drawing.Color.FromArgb(10, 10, 10)}, PRZYKLADY)
    assert any(l == "paleta: kolory własne" for l in gk2["raport"]), gk2["raport"]
    print("  elew_zaaw: {} paneli domyślnie, 12 kombinacji wzór x panel zbudowane".format(len(ge["siatka"])))

    print("SELFTEST OK")


if __name__ == "__main__":
    main()

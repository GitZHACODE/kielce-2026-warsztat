# Karta 07 - Elewacja
**Poziom:** Samodzielnie (Rhino 8)   **Czas:** 15 min   **Budżet:** 2-3 zapytania

## Cel
Na koniec masz komponent, który ubiera bryłę z karty 06 w diagrid piramidalnych paneli, których głębokość i kolor zależą od nasłonecznienia sterowanego dwoma suwakami.
To studium elewacji, którego całą logikę widać w jednej linijce wzoru.

## Zanim zaczniesz
- Miej uruchomiony komponent z karty 06 i pod ręką jego wyjście bryla; bez niego komponent pokaże diagrid na prostym lofcie masy Solna wbudowanym w skrypt.
- Dodaj sześć suwaków: kolumny 12-72, rzedy 4-24, glebokosc_min_m 0-0.5, glebokosc_max_m 0.2-2.0, azymut_slonca_deg 0-360, wysokosc_slonca_deg 5-80.

## Prompt krok po kroku
Każde zdanie promptu ma jedno zadanie i zamyka jedną drogę na skróty; poniżej prompt rozłożony na części w kolejności, w jakiej czyta je agent.

1. **"Write moje/elewacja_gh.py as a Rhino 8 Grasshopper Python 3 Script component ... Pick its skin face: the non-planar face of largest area, or the largest face if all are planar"** - ta sama klasa komponentu co w kartach 05 i 06, a wybór ściany zamyka najczęstszy błąd: panele na zaślepce dachu zamiast na elewacji.
2. **"Sample a grid of kolumny by rzedy points on that face using its parameter domains, treating the closed direction as running around the building (force kolumny even so the pattern wraps)"** - siatkę wyznacza parametryzacja ściany, a parzysta liczba kolumn domyka szachownicę na szwie bez przerwy.
3. **"Build a checkerboard diagrid on the grid nodes: for interior rows and every second column the diamond has corners left, bottom, right, top on neighbouring nodes, plus flat triangles closing the bottom and top rows"** - dokładny przepis na romb i na brzegi siatki; przy domyślnych suwakach daje 198 rombów i 36 trójkątów.
4. **"compute exposure = max(0, dot(normal, sun)) where sun is the unit vector for azymut_slonca_deg (clockwise from north, north is world +Y) and wysokosc_slonca_deg; depth = glebokosc_min_m + (glebokosc_max_m - glebokosc_min_m) * exposure"** - cała logika elewacji w dwóch wzorach; azymut liczy się od osi +Y, czyli od krawędzi KDP-1 masy Solna.
5. **"push an apex out along the normal by that depth and add four triangles with five fresh vertices, coloured per vertex from light (245,244,240) at exposure 0 to graphite (58,62,70) at exposure 1"** - osobne wierzchołki dla każdego panelu dają ostry kolor i cieniowanie; wspólne rozmyłyby granice między panelami.
6. **"Test one sampled normal against the bounding-box centre and flip every normal if it points into the solid"** - normalne lofta bywają zwrócone do środka; bez tego testu panele wrastają w bryłę zamiast z niej wystawać.
7. **"Defaults: kolumny 36, rzedy 12, glebokosc_min_m 0.15, glebokosc_max_m 0.90, azymut_slonca_deg 180, wysokosc_slonca_deg 45."** - komplet wartości startowych, ten sam co w sekcji "Sprawdź", więc komponent bez kabli pokazuje opisane tam 198 rombów.
8. **"Outputs: panele (one Mesh with vertex colours, normals computed), siatka (list of closed Polyline, one per diamond), ekspozycja (list of float per diamond), raport (list of str in Polish: ... one line saying this is a dot-product heuristic, not a solar analysis)"** - jedna siatka do Custom Preview, osobno ramy i liczby, a w raporcie zastrzeżenie, że to nie jest analiza nasłonecznienia.
9. **"Mark every input optional. When bryla is empty, loft the above-ground Kondygnacje rows (Z > 0) of the PROSTOKATY table ... copied into the script as DOMYSLNA_MASA ... into a capped envelope with no twist, panel that instead, and make the first raport line say so"** - komponent bez kabli pokazuje panele na masie wbudowanej, a pierwsza linia "uwaga:" mówi, że bryły z karty 06 jeszcze nie ma.
10. **"Do not use ghpythonlib and do not generate any .gh or .ghx file"** - formatu .gh nie da się napisać tekstem; gotowy komponent powstaje z docstringa przez narzedzia/gh_params_gen.py.

## Prompt (skopiuj do Copilot Chat, tryb Agent)
```text
Write moje/elewacja_gh.py as a Rhino 8 Grasshopper Python 3 Script component. Input bryla (Brep) is a lofted, capped envelope. Pick its skin face: the non-planar face of largest area, or the largest face if all are planar. Sample a grid of kolumny by rzedy points on that face using its parameter domains, treating the closed direction as running around the building (force kolumny even so the pattern wraps). Build a checkerboard diagrid on the grid nodes: for interior rows and every second column the diamond has corners left, bottom, right, top on neighbouring nodes, plus flat triangles closing the bottom and top rows. For each diamond compute exposure = max(0, dot(normal, sun)) where sun is the unit vector for azymut_slonca_deg (clockwise from north, north is world +Y) and wysokosc_slonca_deg; depth = glebokosc_min_m + (glebokosc_max_m - glebokosc_min_m) * exposure; push an apex out along the normal by that depth and add four triangles with five fresh vertices, coloured per vertex from light (245,244,240) at exposure 0 to graphite (58,62,70) at exposure 1. Test one sampled normal against the bounding-box centre and flip every normal if it points into the solid. Defaults: kolumny 36, rzedy 12, glebokosc_min_m 0.15, glebokosc_max_m 0.90, azymut_slonca_deg 180, wysokosc_slonca_deg 45. Outputs: panele (one Mesh with vertex colours, normals computed), siatka (list of closed Polyline, one per diamond), ekspozycja (list of float per diamond), raport (list of str in Polish: panel count, depth range, share of panels above 0.5 exposure, approximate skin area, and one line saying this is a dot-product heuristic, not a solar analysis). Mark every input optional. When bryla is empty, loft the above-ground Kondygnacje rows (Z > 0) of the PROSTOKATY table in rozwiazania/05_szkic_bryly_rhino.py, copied into the script as DOMYSLNA_MASA (a copy of the lowest above-ground rectangle at Z=0, then each slab-top rectangle), into a capped envelope with no twist, panel that instead, and make the first raport line say so. Follow the Grasshopper rules in AGENTS.md. Do not use ghpythonlib and do not generate any .gh or .ghx file.
```

## Jak uruchomić komponent w Grasshopperze

Ten komponent ubiera bryłę z karty 06, ale pokaże panele także bez niej; poniżej każde kliknięcie po kolei.

1. Otwórz Rhino 8, wpisz w linii poleceń u góry słowo `Grasshopper` i naciśnij Enter - otwiera się osobne okno z pustą kanwą.
2. Sposób pierwszy, gotowy komponent z rozwiązania wzorcowego: otwórz w VS Code plik `rozwiazania/07_elewacja_gh.ghcomp.xml`, naciśnij Ctrl+A, potem Ctrl+C, kliknij raz w puste miejsce kanwy i naciśnij Ctrl+V. Panele pojawiają się od razu, bez żadnego kabla.
3. Sposób drugi, twój własny skrypt przez generator: w terminalu VS Code (menu `Terminal` > `New Terminal`) wpisz polecenie poniżej, a potem kliknij w puste miejsce kanwy i naciśnij Ctrl+V:

```
python narzedzia/gh_params_gen.py moje/elewacja_gh.py --clipboard
```

4. Sposób trzeci, ręczny: kliknij dwukrotnie w puste miejsce kanwy, wpisz `Python 3 Script`, wybierz komponent z listy, kliknij go dwukrotnie, wklej kod z `moje/elewacja_gh.py` i zamknij okno przyciskiem `OK`. Wejścia dodajesz znakami plus na lewej krawędzi po przybliżeniu widoku kółkiem myszy.
5. Suwak robisz tak: kliknij dwukrotnie w puste miejsce kanwy, wpisz zakres wprost, na przykład `0<180<360` dla wejścia `azymut_slonca_deg`, i naciśnij Enter. Zakresy pozostałych pięciu suwaków są w sekcji "Zanim zaczniesz" powyżej.
6. Podłączenie bryły z karty 06: przeciągnij kabel z wyjścia `bryla` tamtego komponentu do wejścia `bryla` tego komponentu. Bez tego kabla panele siadają na uproszczonej masie wbudowanej w skrypt.
7. Kolory paneli widać dopiero w podglądzie z materiałem: dwuklik na kanwie, wpisz `Custom Preview`, wstaw komponent i połącz wyjście `panele` z jego wejściem `Geometry`.
8. Raport czytasz komponentem `Panel`: dwuklik na kanwie, wpisz `Panel`, wstaw i połącz z wyjściem `raport`.
9. Ruch suwakiem `azymut_slonca_deg` przelicza całą elewację na bieżąco; przy gęstej siatce (`kolumny` powyżej 48) przeliczenie trwa sekundę lub dwie.
10. Komponent zrobił się pomarańczowy albo czerwony? Najedź kursorem na ikonę dymka w jego prawym górnym rogu i skopiuj treść do czatu.

## Sprawdź
- Wklej komponent jednym z trzech sposobów z sekcji "Jak uruchomić komponent w Grasshopperze" powyżej.
- Bez żadnego kabla panele pojawiają się od razu na prostym lofcie masy Solna, a raport zaczyna się od linii "uwaga: wejście bryla puste"; po podłączeniu bryły z karty 06 ta linia znika.
- Przy domyślnych suwakach (36, 12, 0.15, 0.90, 180, 45) raport pokazuje 198 rombów + 36 trójkątów brzegowych; strona południowa (w stronę -Y, przeciwną do KDP-1) wychodzi głęboka i ciemna, strona północna płaska i jasna.
- Przesuń azymut_slonca_deg na 90 - głęboka strona przesuwa się na wschód.
- Podłącz Custom Preview do wyjścia panele, żeby zobaczyć kolory.

## Jeśli nie działa
- Jeśli panele siedzą na dachu, wybór ściany trafił w zaślepkę (cap) - poproś agenta o wybór ściany niepłaskiej (non-planar face).
- Jeśli wierzchołki paneli są skierowane do wewnątrz, poproś o test odwrócenia normalnej względem środka bounding-box.
- Jeśli w siatce jest przerwa na szwie, wejście kolumny miało wartość nieparzystą - popraw na parzystą.
- Wzorcowe rozwiązanie: rozwiazania/07_elewacja_gh.py (rozwiazania/07_elewacja_gh.ghcomp.xml jako gotowy komponent).

## Krok dalej

Przykład `przyklady/elewacja_zaawansowana_gh.py` rozwija tę elewację o wybór wzoru (romby, kwadraty, trójkąty, heksagony), typ panelu z otworem i atraktory niezależne od słońca.
Jego plik `.ghcomp.xml` wkleja się tak samo jak plik `.ghcomp.xml` tej karty, a zakresy suwaków dla nowych wejść są w `przyklady/README.md`.

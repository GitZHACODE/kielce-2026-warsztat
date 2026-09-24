# Karta 07 - Elewacja
**Poziom:** Samodzielnie (Rhino 8)   **Czas:** 15 min   **Budżet:** 2-3 zapytania

## Cel
Na koniec masz komponent, który ubiera bryłę z karty 06 w diagrid piramidalnych paneli, których głębokość i kolor zależą od nasłonecznienia sterowanego dwoma suwakami.
To studium elewacji, którego całą logikę widać w jednej linijce wzoru.

## Zanim zaczniesz
- Miej uruchomiony komponent z karty 06 i pod ręką jego wyjście bryla; bez niego komponent pokaże diagrid na prostym lofcie masy Solna wbudowanym w skrypt.
- Dodaj sześć suwaków: kolumny 12-72, rzedy 4-24, glebokosc_min_m 0-0.5, glebokosc_max_m 0.2-2.0, azymut_slonca_deg 0-360, wysokosc_slonca_deg 5-80.

## Prompt (skopiuj do Copilot Chat, tryb Agent)
```text
Write moje/elewacja_gh.py as a Rhino 8 Grasshopper Python 3 Script component. Input bryla (Brep) is a lofted, capped envelope. Pick its skin face: the non-planar face of largest area, or the largest face if all are planar. Sample a grid of kolumny by rzedy points on that face using its parameter domains, treating the closed direction as running around the building (force kolumny even so the pattern wraps). Build a checkerboard diagrid on the grid nodes: for interior rows and every second column the diamond has corners left, bottom, right, top on neighbouring nodes, plus flat triangles closing the bottom and top rows. For each diamond compute exposure = max(0, dot(normal, sun)) where sun is the unit vector for azymut_slonca_deg (clockwise from north, north is world +Y) and wysokosc_slonca_deg; depth = glebokosc_min_m + (glebokosc_max_m - glebokosc_min_m) * exposure; push an apex out along the normal by that depth and add four triangles with five fresh vertices, coloured per vertex from light (245,244,240) at exposure 0 to graphite (58,62,70) at exposure 1. Outputs: panele (one Mesh with vertex colours, normals computed), siatka (list of closed Polyline, one per diamond), ekspozycja (list of float per diamond), raport (list of str in Polish: panel count, depth range, share of panels above 0.5 exposure, approximate skin area, and one line saying this is a dot-product heuristic, not a solar analysis). Mark every input optional. When bryla is empty, loft the above-ground Kondygnacje rows (Z > 0) of the PROSTOKATY table in rozwiazania/05_szkic_bryly_rhino.py, copied into the script as DOMYSLNA_MASA (a copy of the lowest above-ground rectangle at Z=0, then each slab-top rectangle), into a capped envelope with no twist, panel that instead, and make the first raport line say so. Follow the Grasshopper rules in AGENTS.md. Do not use ghpythonlib and do not generate any .gh or .ghx file.
```

## Sprawdź
- Wklej: rozwiazania/07_elewacja_gh.ghcomp.xml (Ctrl-V na kanwie; jak: README.md, sekcja "Jak uruchomić gotowy skrypt") albo wklej kod z moje/elewacja_gh.py do komponentu Python 3 Script.
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

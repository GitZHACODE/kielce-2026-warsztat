# Karta 06 - Bryła
**Poziom:** Samodzielnie (Rhino 8)   **Czas:** 15 min   **Budżet:** 2-3 zapytania

## Cel
Na koniec masz komponent Grasshoppera, który zamienia prostokątne obrysy kondygnacji w jedną gładką, skręconą i zaokrągloną bryłę sterowaną suwakami, tnie ją z powrotem na płyty kondygnacji i przekazuje te płyty do kontroli z karty 05, tak że kolory zgodności zmieniają się razem z suwakami.
To jest forma, nad którą pracownia siedziałaby ręcznie cały dzień.

## Zanim zaczniesz
- Uruchom rozwiazania/05_szkic_bryly_rhino.py (jak: README.md, sekcja "Jak uruchomić gotowy skrypt") w Rhino 8, żeby mieć w scenie masę z warstwy Kondygnacje; sam komponent pokaże bryłę także bez tego, na masie wbudowanej w skrypt.
- Podłącz warstwę Kondygnacje do parametru Curve ustawionego na listę (list) - to wejście kondygnacje.
- Dodaj siedem suwaków dla wejść liczbowych, w zakresach: skret_deg 0-40, wybrzuszenie 0-0.3, zaokraglenie 0-1, pochylenie_x_m i pochylenie_y_m od -3 do 3, punkty_profilu 16-64, kontury_co_m 0-2.

## Prompt (skopiuj do Copilot Chat, tryb Agent)
```text
Write moje/bryla_gh.py as a Rhino 8 Grasshopper Python 3 Script component that turns storey outlines into a sculpted envelope. Inputs: kondygnacje (Curve, list - one closed planar curve per storey at its slab-top height; a curve with max Z at or below 0 is underground and must pass through untouched), skret_deg (float, total twist from ground to top about the vertical axis through the ground outline's centroid), wybrzuszenie (float, mid-height bulge: scale each section about its centroid by 1 + wybrzuszenie * sin(pi * t) where t = z / z_max), zaokraglenie (float 0-1, corner fillet radius as a fraction of half the shorter side), pochylenie_x_m and pochylenie_y_m (float, lean of the top in metres), punkty_profilu (int, rebuild point count per section), kontury_co_m (float, spacing of horizontal display contours, 0 disables). Steps: sort above-ground curves by Z, add the lowest one copied to Z=0 as the ground section, make every section counter-clockwise, fillet, scale, rotate, lean, align every section's seam to the ground section's start direction rotated by that section's twist, loft with Brep.CreateFromLoftRebuild using a System.Collections.Generic.List[Curve], cap with CapPlanarHoles and Flip if SolidOrientation is Inward, then intersect the solid with a horizontal plane 1 mm below each original slab-top Z to get the new storey outlines. Outputs: bryla (Brep), kondygnacje_nowe (list of Curve, underground curves first, then the new outlines, ready for the kondygnacje input of the card 05 checker), zabudowa_nowa (Curve, boolean union of the new outlines projected to Z=0, the largest result), plyty (list of planar Brep), kontury (list of Curve), raport (list of str in Polish with each storey's new area against the old one, the total above-ground area, height, storey count and volume). Mark every input optional. When kondygnacje is empty, build the seven storey rectangles from the Kondygnacje rows of the PROSTOKATY table in rozwiazania/05_szkic_bryly_rhino.py, copied into the script as DOMYSLNA_MASA, and make the first raport line say that the default massing was used, so the pasted component shows the envelope with nothing wired. Follow the Grasshopper rules in AGENTS.md. Do not use ghpythonlib and do not generate any .gh or .ghx file.
```

## Sprawdź
- Wklej: rozwiazania/06_bryla_gh.ghcomp.xml (Ctrl-V na kanwie; jak: README.md, sekcja "Jak uruchomić gotowy skrypt") albo wklej kod z moje/bryla_gh.py do komponentu Python 3 Script.
- Bez żadnego kabla bryła pojawia się od razu na masie wbudowanej w skrypt, a raport zaczyna się od linii "uwaga: wejście kondygnacje puste"; po podłączeniu warstwy ta linia znika.
- Przy domyślnych suwakach (12, 0.10, 0.6, 0, 0, 32, 0.5) wyjście bryla jest bryłą zamkniętą (closed solid), a raport wylicza sześć kondygnacji i linię wysokości 20.6 m / 6 kond.
- Podłącz kondygnacje_nowe do wejścia kondygnacje karty 05 i zabudowa_nowa do jej wejścia zabudowa, potem przesuń wybrzuszenie na 0.3 - powierzchnia zabudowy w karcie 05 rośnie, a jej wiersz zostaje NIE.
- Przesuń skret_deg - liczba płyt kondygnacji zostaje sześć.

## Jeśli nie działa
- Jeśli loft wygląda na skręcony w węzeł, szwy przekrojów nie są wyrównane - poproś agenta o ChangeClosedCurveSeam na każdym przekroju.
- Jeśli bryła zgłasza ujemną objętość albo brakuje płyt, poproś o Flip() przy orientacji Inward.
- Jeśli błąd .NET wskazuje na IEnumerable, poproś o użycie List[Curve].
- Wzorcowe rozwiązanie: rozwiazania/06_bryla_gh.py (rozwiazania/06_bryla_gh.ghcomp.xml jako gotowy komponent).

## Krok dalej

Przykład `przyklady/bryla_zaawansowana_gh.py` rozwija tę bryłę o wybór profilu przekroju, atraktor wyciągający brzuch elewacji w swoją stronę i zwężenie ku dachowi.
Jego plik `.ghcomp.xml` wkleja się tak samo jak plik `.ghcomp.xml` tej karty, a zakresy suwaków dla nowych wejść są w `przyklady/README.md`.

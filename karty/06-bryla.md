# Karta 06 - Bryła
**Poziom:** Samodzielnie (Rhino 8)   **Czas:** 15 min   **Budżet:** 2-3 zapytania

## Cel
Na koniec masz komponent Grasshoppera, który zamienia prostokątne obrysy kondygnacji w jedną gładką, skręconą i zaokrągloną bryłę sterowaną suwakami, tnie ją z powrotem na płyty kondygnacji i przekazuje te płyty do kontroli z karty 05, tak że kolory zgodności zmieniają się razem z suwakami.
To jest forma, nad którą pracownia siedziałaby ręcznie cały dzień.

## Zanim zaczniesz
- Uruchom rozwiazania/05_szkic_bryly_rhino.py (jak: karta 05, sekcja "Jak uruchomić komponent w Grasshopperze", punkt 2) w Rhino 8, żeby mieć w scenie masę z warstwy Kondygnacje; sam komponent pokaże bryłę także bez tego, na masie wbudowanej w skrypt.
- Podłącz warstwę Kondygnacje do parametru Curve ustawionego na listę (list) - to wejście kondygnacje.
- Dodaj siedem suwaków dla wejść liczbowych, w zakresach: skret_deg 0-40, wybrzuszenie 0-0.3, zaokraglenie 0-1, pochylenie_x_m i pochylenie_y_m od -3 do 3, punkty_profilu 16-64, kontury_co_m 0-2.

## Prompt krok po kroku
Każde zdanie promptu ma jedno zadanie i zamyka jedną drogę na skróty; poniżej prompt rozłożony na części w kolejności, w jakiej czyta je agent.

1. **"Write moje/bryla_gh.py as a Rhino 8 Grasshopper Python 3 Script component that turns storey outlines into a sculpted envelope"** - nazwa pliku i jedno zdanie o zadaniu: z płaskich obrysów ma powstać jedna bryła, a nie stos osobnych płyt.
2. **"kondygnacje (Curve, list - one closed planar curve per storey at its slab-top height; a curve with max Z at or below 0 is underground and must pass through untouched)"** - garaż podziemny nie wchodzi do loftu, ale musi wyjść z komponentu bez zmian, inaczej karta 05 liczy budynek bez niego.
3. **"skret_deg (float, total twist from ground to top about the vertical axis through the ground outline's centroid), wybrzuszenie (float, mid-height bulge: scale each section about its centroid by 1 + wybrzuszenie * sin(pi * t) where t = z / z_max)"** - dwa suwaki podane wzorem, a nie słowem, więc agent nie wymyśla własnego przebiegu skrętu ani wybrzuszenia.
4. **"zaokraglenie (float 0-1, corner fillet radius as this fraction of 0.49 of the shorter side, so two fillets never meet), ... kontury_co_m (float, spacing of horizontal display contours, 0 disables)"** - promień liczony od 0.49 boku, a nie od połowy, bo dwa zaokrąglenia zbiegające się na krótszej krawędzi psują fillet; zdanie Defaults tuż za listą wejść daje komponentowi bez kabli dokładnie tę bryłę, którą opisuje sekcja Sprawdź.
5. **"sort above-ground curves by Z, add the lowest one copied to Z=0 as the ground section, make every section counter-clockwise, ... align every section's seam to the ground section's start direction rotated by that section's twist"** - wspólny kierunek i wyrównane szwy; bez nich loft skręca się w węzeł (reguła o ClosedCurveOrientation i ChangeClosedCurveSeam z AGENTS.md).
6. **"loft with Brep.CreateFromLoftRebuild using a System.Collections.Generic.List[Curve], cap with CapPlanarHoles and Flip if SolidOrientation is Inward"** - lista Pythona nie przechodzi pod pythonnet ("No method matches given arguments"), a orientacja Inward daje ujemną objętość i normalne do środka.
7. **"intersect the solid with a horizontal plane 1 mm below each original slab-top Z to get the new storey outlines"** - cięcie milimetr pod stropem omija pokrywę bryły, a obrysy wracają dokładnie na wysokościach, których oczekuje karta 05.
8. **"kondygnacje_nowe (list of Curve, underground curves first, then the new outlines, ready for the kondygnacje input of the card 05 checker), zabudowa_nowa (Curve, boolean union of the new outlines projected to Z=0, the largest result), ... a height line in the form "wysokość: 20.6 m / 6 kond." and the volume)"** - te dwa kable wpina się wprost w wejścia karty 05, a stały format linii wysokości pozwala porównać raport z tamtą kartą.
9. **"Mark every input optional. When kondygnacje is empty, build the seven storey rectangles ... copied into the script as DOMYSLNA_MASA, and make the first raport line say that the default massing was used"** - wklejony komponent bez kabli ma od razu pokazać bryłę, a linia "uwaga:" mówi, że to masa wbudowana, nie twoja scena.

## Prompt (skopiuj do Copilot Chat, tryb Agent)
```text
Write moje/bryla_gh.py as a Rhino 8 Grasshopper Python 3 Script component that turns storey outlines into a sculpted envelope. Inputs: kondygnacje (Curve, list - one closed planar curve per storey at its slab-top height; a curve with max Z at or below 0 is underground and must pass through untouched), skret_deg (float, total twist from ground to top about the vertical axis through the ground outline's centroid), wybrzuszenie (float, mid-height bulge: scale each section about its centroid by 1 + wybrzuszenie * sin(pi * t) where t = z / z_max), zaokraglenie (float 0-1, corner fillet radius as this fraction of 0.49 of the shorter side, so two fillets never meet), pochylenie_x_m and pochylenie_y_m (float, lean of the top in metres), punkty_profilu (int, rebuild point count per section), kontury_co_m (float, spacing of horizontal display contours, 0 disables). Defaults: skret_deg 12, wybrzuszenie 0.10, zaokraglenie 0.6, pochylenie_x_m and pochylenie_y_m 0, punkty_profilu 32, kontury_co_m 0.5. Steps: sort above-ground curves by Z, add the lowest one copied to Z=0 as the ground section, make every section counter-clockwise, fillet, scale, rotate, lean, align every section's seam to the ground section's start direction rotated by that section's twist, loft with Brep.CreateFromLoftRebuild using a System.Collections.Generic.List[Curve], cap with CapPlanarHoles and Flip if SolidOrientation is Inward, then intersect the solid with a horizontal plane 1 mm below each original slab-top Z to get the new storey outlines. Outputs: bryla (Brep), kondygnacje_nowe (list of Curve, underground curves first, then the new outlines, ready for the kondygnacje input of the card 05 checker), zabudowa_nowa (Curve, boolean union of the new outlines projected to Z=0, the largest result), plyty (list of planar Brep), kontury (list of Curve), raport (list of str in Polish with each storey's new area against the old one, the total above-ground area, a height line in the form "wysokość: 20.6 m / 6 kond." and the volume). Mark every input optional. When kondygnacje is empty, build the seven storey rectangles from the Kondygnacje rows of the PROSTOKATY table in rozwiazania/05_szkic_bryly_rhino.py, copied into the script as DOMYSLNA_MASA, and make the first raport line say that the default massing was used, so the pasted component shows the envelope with nothing wired. Follow the Grasshopper rules in AGENTS.md. Do not use ghpythonlib and do not generate any .gh or .ghx file.
```

## Jak uruchomić komponent w Grasshopperze

Ten komponent działa suwakami, więc poza wklejeniem kodu trzeba zbudować jeszcze siedem suwaków; poniżej każde kliknięcie po kolei.

1. Otwórz Rhino 8, wpisz w linii poleceń u góry słowo `Grasshopper` i naciśnij Enter - otwiera się osobne okno z pustą kanwą.
2. Sposób pierwszy, gotowy komponent z rozwiązania wzorcowego: otwórz w VS Code plik `rozwiazania/06_bryla_gh.ghcomp.xml`, naciśnij Ctrl+A, potem Ctrl+C, kliknij raz w puste miejsce kanwy i naciśnij Ctrl+V. Bryła pojawia się od razu, bez żadnego kabla.
3. Sposób drugi, twój własny skrypt przez generator: w terminalu VS Code (menu `Terminal` > `New Terminal`) wpisz polecenie poniżej, a potem kliknij w puste miejsce kanwy i naciśnij Ctrl+V:

```
python narzedzia/gh_params_gen.py moje/bryla_gh.py --clipboard
```

4. Sposób trzeci, ręczny: kliknij dwukrotnie w puste miejsce kanwy, wpisz `Python 3 Script`, wybierz komponent z listy, kliknij go dwukrotnie, wklej kod z `moje/bryla_gh.py` i zamknij okno przyciskiem `OK`. Wejścia dodajesz znakami plus na lewej krawędzi po przybliżeniu widoku kółkiem myszy, a wejściu `kondygnacje` ustawiasz dostęp: prawy przycisk na jego nazwie, pozycja `List Access`.
5. Suwak robisz tak: kliknij dwukrotnie w puste miejsce kanwy, wpisz zakres wprost, na przykład `0<12<40` dla wejścia `skret_deg`, i naciśnij Enter. Powstaje suwak od 0 do 40 ustawiony na 12. Zakresy pozostałych sześciu wejść są w sekcji "Zanim zaczniesz" powyżej.
6. Kabel prowadzisz przeciągając myszą od kółka po prawej stronie suwaka do kółka po lewej stronie wejścia komponentu. Kabel usuwasz tym samym ruchem z wciśniętym Ctrl.
7. Podłączenie kondygnacji ze sceny: dwuklik na kanwie, wpisz `Curve`, wstaw komponent, kliknij go prawym przyciskiem, wybierz `Set Multiple Curves`, zaznacz w Rhino krzywe warstwy `Kondygnacje` i naciśnij Enter; wyjście połącz z wejściem `kondygnacje`.
8. Podgląd bryły: kliknij prawym przyciskiem wyjście `bryla` i włącz `Preview`, albo połącz je z komponentem `Custom Preview`. Raport czytasz komponentem `Panel` podłączonym do wyjścia `raport`.
9. Połączenie z kartą 05: przeciągnij kabel z wyjścia `kondygnacje_nowe` do wejścia `kondygnacje` komponentu karty 05, a z `zabudowa_nowa` do jego wejścia `zabudowa`. Od tej chwili każdy ruch suwakiem przelicza kontrolę planu.
10. Komponent zrobił się pomarańczowy albo czerwony? Najedź kursorem na ikonę dymka w jego prawym górnym rogu i skopiuj treść do czatu.

## Sprawdź
- Wklej komponent jednym z trzech sposobów z sekcji "Jak uruchomić komponent w Grasshopperze" powyżej.
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

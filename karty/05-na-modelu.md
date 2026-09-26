# Karta 05 - Na modelu
**Poziom:** Samodzielnie (Rhino 8)   **Czas:** 20 min   **Budżet:** 2-3 zapytania

## Cel
Na koniec masz komponent Grasshoppera, który liczy te same sześć wskaźników wprost z krzywych 3D i koloruje każdą płytę kondygnacji na zielono albo czerwono.
Kontrola planu siedzi wtedy w tej samej bryle, którą już modelujesz, bez przepisywania liczb do osobnego arkusza.

## Zanim zaczniesz
- Otwórz Rhino 8 i Grasshopper z modelem Solna.
- Dodaj pusty komponent Python 3 Script i podłącz dziewięć wejść z promptu: dzialka, zabudowa, kondygnacje, pbc_grunt, pbc_tarasy, mieszkania, miejsca_podziemne, miejsca_naziemne, plan_json.
- Komponent ma działać także bez żadnego kabla: wtedy liczy masę Solna wbudowaną w skrypt i pokazuje jej płyty, a pierwsza linia raportu mówi, że to dane domyślne.
- Te same definicje planu co w karcie 01: moje/plan.json -> definicje.

## Prompt krok po kroku
Każde zdanie promptu ma jedno zadanie i zamyka jedną drogę na skróty; poniżej prompt rozłożony na części w kolejności, w jakiej czyta je agent.

1. **"Write moje/sprawdz_mpzp_gh.py as a Rhino 8 Grasshopper Python 3 Script component"** - nazwa i folder pliku oraz klasa komponentu: Rhino 8 ma Python3Component, a kod pisany pod stary IronPython 2 nie przenosi się jeden do jednego.
2. **"kondygnacje (Curve, list - one closed planar curve per storey placed at its slab-top height; a curve whose highest Z is at or below 0 is an underground storey)"** - umowa geometryczna kart 05, 06 i 07; bez niej agent wlicza garaż na Z = -3 do intensywności i zamiast 2.90 wychodzi 3.65.
3. **"pbc_grunt (Curve, list), pbc_tarasy (Curve, list)"** - dwa osobne wejścia, bo reguła 50 % i progu 10 m2 z § 4 pkt 17 dotyczy tylko tarasów i stropodachów, nie gruntu rodzimego.
4. **"Compute areas with Rhino.Geometry.AreaMassProperties.Compute and heights from each curve's bounding box"** - pole liczy Rhino, a nie ręczny wzór na wielobok (reguła z AGENTS.md); wysokość kondygnacji to górne Z obwiedni krzywej.
5. **"Apply the same six checks and the same definitions as the Python script; the component has no roof input, so the dach row must read "brak danych" with Wynik OK"** - te same wskaźniki co w karcie 01, a nachylenia dachu nie da się odczytać z krzywych, więc agent nie ma go zgadywać.
6. **"raport (list of str, one row per indicator as "wskaznik: wartosc | limit X | OK or NIE | margines")"** - stały układ wiersza, ten sam co w rozwiązaniu wzorcowym, więc raport da się porównać z tabelą z karty 01.
7. **"kolory (one System.Drawing.Color per storey curve: green if all checks pass, red otherwise), plyty (one planar Brep per storey curve, for a Custom Preview with kolory)"** - dwie listy tej samej długości, bo Custom Preview łączy geometrię z kolorem po indeksie.
8. **"Mark every input optional and read each one through globals().get with a default, so the component runs with nothing wired"** - wejście bez znacznika optional i bez danych w ogóle nie pozwala Grasshopperowi uruchomić komponentu.
9. **"build the fixture massing inside the script from the PROSTOKATY table of rozwiazania/05_szkic_bryly_rhino.py copied into the script as DOMYSLNA_MASA ... default mieszkania 30, miejsca_podziemne 27 and miejsca_naziemne 3, and when plan_json is empty use the wskazniki of rozwiazania/plan.json copied into the script; the first raport line must then say that defaults were used"** - wklejony skrypt niczego nie importuje z rozwiazania/, więc masa i limity muszą być w nim skopiowane, a ostrzeżenie mówi, skąd są liczby.
10. **"Do not use ghpythonlib, do not use isinstance on Rhino types, and do not generate any .gh or .ghx file"** - isinstance pod CPython bywa False dla poprawnego typu RhinoCommon, a pliku .gh napisanego przez model Grasshopper nie otworzy.

## Prompt (skopiuj do Copilot Chat, tryb Agent)
```text
Write moje/sprawdz_mpzp_gh.py as a Rhino 8 Grasshopper Python 3 Script component. Inputs: dzialka (Curve, item), zabudowa (Curve, item), kondygnacje (Curve, list - one closed planar curve per storey placed at its slab-top height; a curve whose highest Z is at or below 0 is an underground storey), pbc_grunt (Curve, list), pbc_tarasy (Curve, list), mieszkania (int), miejsca_podziemne (int), miejsca_naziemne (int), plan_json (str - path to moje/plan.json). Compute areas with Rhino.Geometry.AreaMassProperties.Compute and heights from each curve's bounding box. Apply the same six checks and the same definitions as the Python script; the component has no roof input, so the dach row must read "brak danych" with Wynik OK. Outputs: raport (list of str, one row per indicator as "wskaznik: wartosc | limit X | OK or NIE | margines"), ok (bool), kolory (one System.Drawing.Color per storey curve: green if all checks pass, red otherwise), plyty (one planar Brep per storey curve, for a Custom Preview with kolory), wskazniki (JSON string). Mark every input optional and read each one through globals().get with a default, so the component runs with nothing wired: when dzialka, zabudowa and kondygnacje are all empty, build the fixture massing inside the script from the PROSTOKATY table of rozwiazania/05_szkic_bryly_rhino.py copied into the script as DOMYSLNA_MASA (Rectangle3d on WorldXY moved to its Z), default mieszkania 30, miejsca_podziemne 27 and miejsca_naziemne 3, and when plan_json is empty use the wskazniki of rozwiazania/plan.json copied into the script; the first raport line must then say that defaults were used. Follow the Grasshopper rules in AGENTS.md. Do not use ghpythonlib, do not use isinstance on Rhino types, and do not generate any .gh or .ghx file - I will paste the code into the component myself.
```

## Jak uruchomić komponent w Grasshopperze

Kod agenta trafia na kanwę Grasshoppera na jeden z trzech sposobów; pierwszy jest najkrótszy, trzeci działa nawet wtedy, gdy dwa pierwsze zawiodą.

1. Otwórz Rhino 8, a w dokumencie Rhino wpisz w linii poleceń u góry słowo `Grasshopper` i naciśnij Enter - otwiera się osobne okno z pustą kanwą.
2. Scena Rhino jest pusta? Wpisz w linii poleceń Rhino `ScriptEditor`, naciśnij Enter, w oknie edytora wybierz `File` > `Open`, wskaż `rozwiazania/05_szkic_bryly_rhino.py` i naciśnij przycisk `Run` (zielony trójkąt). W scenie pojawiają się warstwy `Dzialka`, `Zabudowa`, `Kondygnacje`, `PBC-grunt` i `PBC-tarasy`. Komponent pokaże liczby także bez tego kroku, na masie wbudowanej w skrypt.
3. Sposób pierwszy, gotowy komponent z rozwiązania wzorcowego: otwórz w VS Code plik `rozwiazania/05_sprawdz_mpzp_gh.ghcomp.xml`, naciśnij Ctrl+A (zaznacz wszystko), potem Ctrl+C (kopiuj), kliknij raz w puste miejsce kanwy Grasshoppera i naciśnij Ctrl+V. Komponent pojawia się ze wszystkimi wejściami i wyjściami i od razu liczy.
4. Sposób drugi, twój własny skrypt przez generator: w terminalu VS Code (menu `Terminal` > `New Terminal`) wpisz polecenie poniżej, a potem kliknij w puste miejsce kanwy i naciśnij Ctrl+V. Generator czyta docstring twojego skryptu, więc wejścia i wyjścia powstają same:

```
python narzedzia/gh_params_gen.py moje/sprawdz_mpzp_gh.py --clipboard
```

5. Sposób trzeci, ręczny: kliknij dwukrotnie w puste miejsce kanwy, wpisz `Python 3 Script`, wybierz komponent z listy podpowiedzi, kliknij go dwukrotnie, wklej do okna edytora kod z `moje/sprawdz_mpzp_gh.py` i zamknij okno przyciskiem `OK`. Wejścia dodajesz znakami plus na lewej krawędzi komponentu po przybliżeniu widoku kółkiem myszy, a wejściom `kondygnacje`, `pbc_grunt` i `pbc_tarasy` ustawiasz dostęp: prawy przycisk na nazwie wejścia, pozycja `List Access`.
6. Podłączenie sceny: dla każdej z warstw przeciągnij komponent `Curve` na kanwę (dwuklik, wpisz `Curve`), kliknij go prawym przyciskiem, wybierz `Set Multiple Curves`, zaznacz w Rhino krzywe z danej warstwy i naciśnij Enter. Wyjście tego komponentu połącz z odpowiednim wejściem, przeciągając kabel od kółka po prawej stronie komponentu `Curve` do kółka po lewej stronie wejścia.
7. Odczyt raportu: kliknij dwukrotnie w puste miejsce kanwy, wpisz `Panel`, wstaw komponent i połącz wyjście `raport` z jego lewą krawędzią. Raport wypisuje się linia po linii.
8. Kolory płyt: dwuklik na kanwie, wpisz `Custom Preview`, wstaw komponent, połącz wyjście `plyty` z jego wejściem `Geometry`, a wyjście `kolory` z wejściem `Material`. Płyty w oknie Rhino przyjmują kolor wyniku.
9. Komponent zrobił się pomarańczowy albo czerwony? Najedź kursorem na ikonę dymka w jego prawym górnym rogu - pokazuje treść ostrzeżenia lub błędu. Skopiuj ją do czatu i poproś agenta o poprawkę.

## Sprawdź
- Wklej komponent jednym z trzech sposobów z sekcji "Jak uruchomić komponent w Grasshopperze" powyżej.
- bez żadnego kabla komponent od razu pokazuje siedem płyt masy Solna, a raport zaczyna się od linii "uwaga: wejścia dzialka, zabudowa i kondygnacje puste"; po podłączeniu warstw ta linia znika, a druga linia o plan_json zostaje, dopóki nie podepniesz ścieżki do moje/plan.json.
- pięć wierszy z tymi samymi wartościami co w karcie 01 (margines bywa sformułowany inaczej): powierzchnia zabudowy 52.0 % NIE, intensywność 2.90 OK, PBC 8.9 % NIE, wysokość 20.6 m / 6 kond. OK, parking NIE (margines "brakuje 3 miejsc; 3 miejsc naziemnych niedozwolonych").
- wiersz dach pokazuje "brak danych" i wynik OK - komponent nie ma wejścia z nachyleniem dachu, więc nie da się go odczytać z samych krzywych kondygnacji.
- wszystkie płyty kondygnacji kolorują się na czerwono, bo budynek jako całość nie przechodzi kontroli - to poprawne, nie błąd komponentu.
- jeśli scena jest pusta, uruchom najpierw rozwiazania/05_szkic_bryly_rhino.py według punktu 2 sekcji "Jak uruchomić komponent w Grasshopperze" powyżej, w nowym, pustym dokumencie Rhino, żeby wygenerować kondygnacje.
- kondygnacje i zabudowę można później podpiąć z wyjść komponentu z karty 06 (kondygnacje_nowe, zabudowa_nowa), wtedy kontrola liczy nową bryłę.

## Jeśli nie działa
- Jeśli komponent rzuca błąd na typach Rhino, każ agentowi porównywać GetType().Name zamiast używać isinstance na obiektach RhinoCommon.
- Wzorcowe rozwiązanie: rozwiazania/05_sprawdz_mpzp_gh.py (geometria pomocnicza: rozwiazania/05_szkic_bryly_rhino.py).

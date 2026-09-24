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

## Prompt (skopiuj do Copilot Chat, tryb Agent)
```text
Write moje/sprawdz_mpzp_gh.py as a Rhino 8 Grasshopper Python 3 Script component. Inputs: dzialka (Curve, item), zabudowa (Curve, item), kondygnacje (Curve, list - one closed planar curve per storey placed at its slab-top height; a curve at or below Z=0 is an underground storey), pbc_grunt (Curve, list), pbc_tarasy (Curve, list), mieszkania (int), miejsca_podziemne (int), miejsca_naziemne (int), plan_json (str - path to moje/plan.json). Compute areas with Rhino.Geometry.AreaMassProperties.Compute and heights from each curve's bounding box. Apply the same six checks and the same definitions as the Python script. Outputs: raport (list of str), ok (bool), kolory (one System.Drawing.Color per storey curve: green if all checks pass, red otherwise), plyty (one planar Brep per storey curve, for a Custom Preview with kolory), wskazniki (JSON string). Mark every input optional and read each one through globals().get with a default, so the component runs with nothing wired: when dzialka, zabudowa and kondygnacje are all empty, build the fixture massing inside the script from the PROSTOKATY table of rozwiazania/05_szkic_bryly_rhino.py copied into the script as DOMYSLNA_MASA (Rectangle3d on WorldXY moved to its Z), default mieszkania 30, miejsca_podziemne 27 and miejsca_naziemne 3, and when plan_json is empty use the wskazniki of rozwiazania/plan.json copied into the script; the first raport line must then say that defaults were used. Follow the Grasshopper rules in AGENTS.md. Do not use ghpythonlib, do not use isinstance on Rhino types, and do not generate any .gh or .ghx file - I will paste the code into the component myself.
```

## Sprawdź
- Wklej: rozwiazania/05_sprawdz_mpzp_gh.ghcomp.xml (Ctrl-V na kanwie; jak: README.md, sekcja "Jak uruchomić gotowy skrypt") albo wklej kod z moje/sprawdz_mpzp_gh.py do komponentu Python 3 Script.
- bez żadnego kabla komponent od razu pokazuje siedem płyt masy Solna, a raport zaczyna się od linii "uwaga: wejścia dzialka, zabudowa i kondygnacje puste"; po podłączeniu warstw ta linia znika.
- pięć wierszy identycznych jak w karcie 01: powierzchnia zabudowy 52.0 % NIE, intensywność 2.90 OK, PBC 8.9 % NIE, wysokość 20.6 m / 6 kond. OK, parking NIE (margines "brakuje 3 miejsc; 3 miejsc naziemnych niedozwolonych").
- wiersz dach pokazuje "brak danych" i wynik OK - komponent nie ma wejścia z nachyleniem dachu, więc nie da się go odczytać z samych krzywych kondygnacji.
- wszystkie płyty kondygnacji kolorują się na czerwono, bo budynek jako całość nie przechodzi kontroli - to poprawne, nie błąd komponentu.
- jeśli scena jest pusta, uruchom najpierw rozwiazania/05_szkic_bryly_rhino.py (jak: README.md, sekcja "Jak uruchomić gotowy skrypt") w nowym, pustym dokumencie Rhino, żeby wygenerować kondygnacje.
- kondygnacje i zabudowę można później podpiąć z wyjść komponentu z karty 06 (kondygnacje_nowe, zabudowa_nowa), wtedy kontrola liczy nową bryłę.

## Jeśli nie działa
- Jeśli komponent rzuca błąd na typach Rhino, każ agentowi porównywać GetType().Name zamiast używać isinstance na obiektach RhinoCommon.
- Wzorcowe rozwiązanie: rozwiazania/05_sprawdz_mpzp_gh.py (geometria pomocnicza: rozwiazania/05_szkic_bryly_rhino.py).

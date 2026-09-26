# Prowadzący - przebieg 90 minut

Sobota, 26 września 2026 roku, 11:45-13:15, zaraz po sesji xFigura (10:00-11:30) w tej samej sali, z 15-minutową przerwą kawową pomiędzy. Montaż sprzętu dla obu sesji przed 10:00. Sala do potwierdzenia u organizatorów - program z 16 września podaje tylko godziny.

## Jedno zdanie na start

Każdy uczestnik wychodzi z warsztatu z własnym sprawdzaczem zgodności z planem, napisanym dla niego przez agenta AI i wypełnionym wskaźnikami terenu U,M 2, wraz z promptem, który go stworzył.

## Przebieg

Blok trwa 90 minut i dzieli się na dwie rundy pracy samodzielnej.

| Czas | Min | Blok |
|---|---|---|
| 0:00 | 3 | Wprowadzenie |
| 0:03 | 10 | Pokaz 1: karta 00 na żywo (agent szuka U,M 2 w 34 stronach), porównanie z wzorcem, potem karta 01 ze scenariuszem błędu i ręcznym uruchomieniem pliku |
| 0:13 | 2 | Test narzędzi |
| 0:15 | 10 | Razem: karta 00, początek karty 01 |
| 0:25 | 18 | Samodzielnie 1: karty 01 do 04 i 99, jedna do dwóch kart na blok; czas na karcie dotyczy jednej karty, nie bloku |
| 0:43 | 4 | Omówienie 1 |
| 0:47 | 5 | Przerwa |
| 0:52 | 6 | Pokaz 2: karta 05 (płyty czerwone), karta 06 (suwaki zmieniają wynik kontroli), karta 07 (elewacja) |
| 0:58 | 18 | Samodzielnie 2: z Rhino karty 05, 06, 07; bez Rhino karty 02 do 04 i 99; jedna karta na blok |
| 1:16 | 5 | Omówienie 2 i pytania |
| 1:21 | 4 | W wolnym czasie: podmień uchwałę, uruchom kartę 00, potem 01 |
| 1:25 | 5 | Rezerwa |

## Pokaz 1 - scenariusz błędu

Scenariusz na projektorze, krok po kroku:

1. Wyślij prompt z karty `karty/00-wczytaj-plan.md`; pokaż na ekranie, jak agent szuka terenu U,M 2 w 34 stronach uchwały (sześć terenów U,M zaczyna się tym samym zdaniem) i jak powstaje plik `moje/plan.json`, potem otwórz widok porównania z wzorcem `rozwiazania/plan.json`. Jeśli agent czyta dłużej niż dwie minuty, pokaż przygotowany przed sesją `moje/plan.json` i sam widok porównania.
2. Wyślij prompt z karty `karty/01-sprawdz-plan.md`.
3. Agent najpewniej policzy intensywność 3.65 (licząc garaż) albo PBC 11.8 % (licząc całe tarasy razem z tym 8 m2).
4. Wskaż agentowi `moje/plan.json -> definicje` oraz `.github/copilot-instructions.md`; powiedz zdanie: najpierw plan, potem ustawa.
5. Uruchom ponownie.
6. Poprawiona tabela pokazuje sześć wierszy: powierzchnia zabudowy 52.0 % NIE, intensywność 2.90 OK, PBC 8.9 % NIE, wysokość 20.6 m / 6 kond. OK, dach 5° OK, parking 27 podziemnych + 3 naziemnych NIE.
7. Zamknij czat, otwórz terminal, uruchom ręcznie `python moje/sprawdz_mpzp.py` i przeczytaj kod wyjścia na głos.

## Pokaz 2 - na modelu

Trzy komponenty na jednej kanwie, w tej kolejności:

1. Otwórz Rhino 8 i Grasshoppera.
2. Wklej sidecar (plik `.ghcomp.xml` z gotowym komponentem) karty 05 - bez kabli od razu pokazuje siedem płyt masy Solna i raport z pierwszą linią "uwaga: ... domyślnej masy". Jeśli dokument Rhino jest pusty, uruchom `rozwiazania/05_szkic_bryly_rhino.py` w ScriptEditorze; podepnij warstwy jako wejścia - linia o domyślnej masie znika (uwaga o plan_json zostaje, dopóki nie podepniesz ścieżki do `moje/plan.json`), wszystkie płyty kondygnacji są czerwone.
3. Wklej sidecar karty 06 - bryła pojawia się od razu na masie wbudowanej; podepnij `kondygnacje` z warstwy Kondygnacje, poruszaj suwakami `skret_deg` i `wybrzuszenie`.
4. Przepnij wyjścia `kondygnacje_nowe` i `zabudowa_nowa` komponentu 06 do wejść `kondygnacje` i `zabudowa` komponentu 05, i pokaż sali, jak zmieniają się powierzchnia zabudowy i intensywność.
5. Wklej sidecar karty 07 - panele pojawiają się od razu na prostym lofcie masy Solna; podepnij `bryla` z komponentu 06 i poruszaj wysokością słońca.
6. Na koniec bloku, jeśli zostanie czas, wklej `przyklady/bryla_zaawansowana_gh.ghcomp.xml` w miejsce komponentu karty 06, przeciągnij punkt `atraktor`, potem wklej `przyklady/elewacja_zaawansowana_gh.ghcomp.xml` i przełącz `typ_wzoru` oraz `typ_panelu`.

Jeśli po omówieniu 2 zostanie czas, otwórz `rozwiazania/08_pokaz.html` i przełącz presety od Szkicu Solna do Wieży; to zapowiedź karty 08, której uczestnicy nie uruchamiają na sali.

## Kolejność cięć

1. Skróć omówienia do 2-4 minut.
2. Zrezygnuj z demo karty 07.
3. Zwiń rundę drugą w pierwszą, wydłużając Samodzielnie 1.

Nigdy nie skracaj przerwy, testu narzędzi ani rezerwy.

## Karty statusu

- ZIELONA - idę za Tobą, sprawdź moją pracę.
- POMARAŃCZOWA - utknąłem, przyjdź.
- ODWRÓCONA - oglądam celowo, nie ratuj mnie.

## Przed wyjazdem

Uruchom w PowerShell, z katalogu głównego repozytorium, każde z poniższych poleceń - każde powinno wypisać `SELFTEST OK`.

```
conda run -n gh-tools python rozwiazania/01_sprawdz_mpzp.py --test
conda run -n gh-tools python rozwiazania/02_wysokosc_schodkowa.py --test
conda run -n gh-tools python rozwiazania/03_ile_moge.py --test
conda run -n gh-tools python rozwiazania/05_sprawdz_mpzp_gh.py --test
conda run -n gh-tools python rozwiazania/05_szkic_bryly_rhino.py --test
conda run -n gh-tools python rozwiazania/06_bryla_gh.py --test
conda run -n gh-tools python rozwiazania/07_elewacja_gh.py --test
conda run -n gh-tools python przyklady/bryla_zaawansowana_gh.py --test
conda run -n gh-tools python przyklady/elewacja_zaawansowana_gh.py --test
node rozwiazania/04_test.js
node rozwiazania/08_test.js
conda run -n kielce-rhino --no-capture-output python narzedzia/test_geometrii_rhino_inside.py
```

Sprawdź też, że pięć sidecarów (trzy kart 05-07 i dwa z `przyklady/`) jest aktualnych względem skryptów - po ostatniej poprawce pliku `.py` bez ponownej generacji wklejony komponent uruchamia stary kod. Każde z poniższych poleceń ma zakończyć się bez wyjścia i kodem 0 (`echo $LASTEXITCODE`).

```
conda run -n gh-tools python narzedzia/gh_params_gen.py rozwiazania/05_sprawdz_mpzp_gh.py --check
conda run -n gh-tools python narzedzia/gh_params_gen.py rozwiazania/06_bryla_gh.py --check
conda run -n gh-tools python narzedzia/gh_params_gen.py rozwiazania/07_elewacja_gh.py --check
conda run -n gh-tools python narzedzia/gh_params_gen.py przyklady/bryla_zaawansowana_gh.py --check
conda run -n gh-tools python narzedzia/gh_params_gen.py przyklady/elewacja_zaawansowana_gh.py --check
```

Dalsze czynności przed wyjazdem:

1. Otwórz `rozwiazania/04_kalkulator.html` w przeglądarce i wczytaj oba pliki JSON przyciskami kalkulatora.
2. Uruchom `05_szkic_bryly_rhino.py` w nowym dokumencie Rhino.
3. Wklej każdy z pięciu sidecarów `.ghcomp.xml` (trzy kart 05-07 i dwa z `przyklady/`) na kanwę Grasshoppera i potwierdź, że komponent pojawia się razem ze swoimi wejściami i bez żadnego kabla rysuje geometrię masy Solna.
4. Uruchom karty 05, 06 i 07 połączone razem, jeden raz.
5. Wydrukuj dziewięć kart oraz 30 kart statusu; kartę 08 pomiń, to pokaz po warsztacie.
6. Sprawdź dziennikustaw.gov.pl pod kątem nowych Warunków Technicznych 25 i 26 września.
7. Sprawdź jeszcze raz zapis do Copilot Free.
8. Jeśli polskie litery w terminalu wyglądają jak krzaki (mojibake) w Windows PowerShell 5.1, uruchom raz `chcp 65001` w tym terminalu i uruchom polecenie ponownie; terminal VS Code z PowerShell 7 tego nie wymaga, a same pliki skryptów są poprawne.

# Karta 03 - Ile mogę
**Poziom:** Samodzielnie (bez Rhino), poziom 2   **Czas:** 15 min   **Budżet:** 2-3 zapytania

## Cel
Na koniec masz skrypt, który zamienia każde NIE z karty 01 na konkretną liczbę: o ile zmniejszyć rzut, ile metrów zieleni dodać, ile miejsc przenieść pod ziemię.
To jest różnica między "projekt nie przechodzi" a gotową listą zmian dla zespołu projektowego.

## Zanim zaczniesz
- Miej otwarty i uruchomiony moje/sprawdz_mpzp.py z karty 01 - potrzebujesz tych samych definicji i tych samych sześciu wyników jako punktu wyjścia.
- Maksymalny rzut zabudowy liczy się z powierzchnia_zabudowy_max_pct w moje/plan.json i dzialka_m2 w dane/inwestycja.json.

## Prompt krok po kroku
Każde zdanie promptu ma jedno zadanie i zamyka jedną drogę na skróty; poniżej prompt rozłożony na części w kolejności, w jakiej czyta je agent.

1. **"Write moje/ile_moge.py"** - nazwa i folder pliku wynikowego; nowy skrypt powstaje obok sprawdzacza z karty 01, a nie zamiast niego.
2. **"Using the same data and definitions as moje/sprawdz_mpzp.py"** - te same wzory i ta sama definicja planu; policzone od nowa dałyby inne liczby niż tabela, z której wychodzisz.
3. **"reading moje/plan.json (or rozwiazania/plan.json if it does not exist) and dane/inwestycja.json"** - prompt sam wskazuje pliki z liczbami, więc karta działa także wtedy, gdy nie masz gotowego moje/sprawdz_mpzp.py z karty 01.
4. **"for every indicator that fails print the smallest change that would make it pass"** - zamiast powtórzonego NIE ma paść liczba: najmniejsza zmiana, która wystarczy, żeby wskaźnik przeszedł.
5. **"the maximum footprint in m2"** - 50 % z 1850 m2, czyli 925 m2 - konkretna wartość do rysunku zamiast procentu do przeliczania w głowie.
6. **"how many m2 of native ground or of green terrace (remember the 50% rule) are missing"** - dwie drogi i dwie różne liczby: 20 m2 gruntu rodzimego albo 40 m2 tarasu, bo z tarasu liczy się połowa (§ 4 pkt 17).
7. **"how many underground parking spaces are missing and what to do with the surface spaces"** - brakujące 3 miejsca podziemne to tylko połowa odpowiedzi; 3 miejsca naziemne trzeba usunąć, bo plan ich nie dopuszcza (§ 20 ust. 2 pkt 10 lit. e).
8. **"Also print how much floor area is still available under the intensity limit (above-ground storeys only, as in the plan's own definition)"** - 1119 m2 zapasu; nawias zamyka pułapkę z garażem, bo z jego 1400 m2 zapas wyszedłby ujemny.
9. **"Run it."** - agent uruchamia skrypt od razu, więc rozbieżność z tabelą z karty 01 widać w czacie, a nie dopiero przy kliencie.

## Prompt (skopiuj do Copilot Chat, tryb Agent)
```text
Write moje/ile_moge.py. Using the same data and definitions as moje/sprawdz_mpzp.py, reading moje/plan.json (or rozwiazania/plan.json if it does not exist) and dane/inwestycja.json, for every indicator that fails print the smallest change that would make it pass: the maximum footprint in m2, how many m2 of native ground or of green terrace (remember the 50% rule) are missing, how many underground parking spaces are missing and what to do with the surface spaces. Also print how much floor area is still available under the intensity limit (above-ground storeys only, as in the plan's own definition). Run it.
```

## Jak uruchomić skrypt

Ten skrypt uruchamiasz obok sprawdzacza z karty 01 i czytasz oba wyniki razem; poniżej każde kliknięcie po kolei.

1. W lewej kolumnie VS Code rozwiń folder `moje` i sprawdź, że leży w nim plik `ile_moge.py`. Nie ma go? Napisz agentowi: "zapisz skrypt do pliku moje/ile_moge.py".
2. Na górnej belce VS Code otwórz menu `Terminal`, wybierz `New Terminal` (menu VS Code są po angielsku) i sprawdź, że linia na dole kończy się nazwą `kielce-2026-warsztat`.
3. Wpisz polecenie i naciśnij Enter:

```
python moje/ile_moge.py
```

4. Lista brakujących metrów i miejsc postojowych wypisuje się tuż pod poleceniem.
5. Dla porównania uruchom zaraz potem sprawdzacz z karty 01 - te same wskaźniki mają dać te same wartości:

```
python moje/sprawdz_mpzp.py
```

6. Komunikat `python: The term 'python' is not recognized`? Wpisz to samo polecenie ze skrótem `py` zamiast `python`.
7. Zamiast polskich liter widzisz krzaki? Wpisz raz `chcp 65001`, naciśnij Enter i powtórz polecenie z punktu 3.

## Sprawdź
- powierzchnia zabudowy: maksymalny dopuszczalny rzut to 925 m2.
- PBC: brakuje 20 m2 gruntu rodzimego, albo 40 m2 dodatkowego tarasu zielonego (bo liczy się tylko 50 % tarasu).
- parking: brakuje 3 miejsc podziemnych.
- intensywność: zapas 1119 m2 powierzchni pod limitem; pułapka - to nie znaczy, że wolno dobudować kondygnację bez sprawdzenia wysokości i cofnięć z karty 02.

## Jeśli nie działa
- Jeśli liczby nie zgadzają się z kartą 01, każ agentowi ponownie użyć tych samych funkcji i definicji co w sprawdz_mpzp.py, zamiast liczyć wskaźniki od nowa.
- Jeśli polskie litery w tabeli w terminalu wyglądają jak krzaki (np. "Wskaźnik" jako bełkot), wpisz raz chcp 65001 w tym terminalu i uruchom skrypt ponownie - sam plik jest poprawny.
- Wzorcowe rozwiązanie: rozwiazania/03_ile_moge.py.

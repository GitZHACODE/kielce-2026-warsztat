# Karta 01 - Sprawdź plan
**Poziom:** Wspólne   **Czas:** 10 min   **Budżet:** 1-2 zapytania

## Cel
Na koniec masz działający skrypt moje/sprawdz_mpzp.py, który w kilka sekund liczy sześć wskaźników budynku Solna i porównuje je z limitami planu.
To jest ta sama kontrola, którą architekt musi wykonać ręcznie i bezbłędnie, zanim zacznie projektować, i powtórzyć przed złożeniem projektu w urzędzie.

## Zanim zaczniesz
- Otwórz moje/plan.json (z karty 00; jeśli go nie masz, rozwiazania/plan.json) i dane/inwestycja.json - to jedyne źródła liczb dla agenta.
- Wskaźniki dla terenu U,M 2 są w § 20 ust. 2 pkt 6 uchwały XLI/1014/2009.
- Copilot Chat w trybie Agent, cały folder repo otwarty jako workspace.

## Prompt krok po kroku
Każde zdanie promptu ma jedno zadanie i zamyka jedną drogę na skróty; poniżej prompt rozłożony na części w kolejności, w jakiej czyta je agent.

1. **"Read moje/plan.json (if it does not exist, read rozwiazania/plan.json instead) and dane/inwestycja.json"** - jedyne dwa źródła liczb, z planem zapasowym na wypadek, gdy karta 00 się nie udała; agent nie ma brać limitów z pamięci.
2. **"Write moje/sprawdz_mpzp.py in Python 3.9 using only the standard library"** - nazwa i folder pliku wynikowego, wersja Pythona taka jak w Rhino 8 i zakaz bibliotek, których nikt na sali nie instalował.
3. **"check the proposal against the plan's indicators, in this order: ..."** - sześć wskaźników w stałej kolejności, żeby tabelę dało się porównać z sąsiadem i z tą kartą.
4. **"intensity (intensywnosc - use the plan's own definition ... above-ground storeys only)"** - zamyka pułapkę z pokazu: bez tego zdania agent wlicza garaż podziemny i dostaje 3.65 zamiast 2.90.
5. **"PBC - apply the plan's rule: 50% of each green terrace or roof of at least 10 m2, smaller ones do not count"** - reguła z § 4 pkt 17 w skrócie; bez niej wychodzi 11.8 %, bo agent liczy całe tarasy i dolicza taras 8 m2.
6. **"height (highest storey top in metres and number of above-ground storeys against the plan's maximum)"** - dwie liczby naraz, bo plan ogranicza i metry, i liczbę kondygnacji; wynik ma wyglądać jak 20.6 m / 6 kond.
7. **"parking (minimum spaces per flat; the plan allows underground spaces only, so any surface space is a failure)"** - zasada z § 15 ust. 1 pkt 3; trzy miejsca naziemne to naruszenie planu, nie niedobór do uzupełnienia.
8. **"Print a table with the columns: Wskaźnik, Wartość, Limit, Wynik (OK or NIE), Margines"** - stały układ z polskimi nagłówkami, ten sam co w rozwiązaniu wzorcowym i w kartach 04 i 05.
9. **"Exit with code 1 if any row is NIE"** - kod wyjścia czytasz w terminalu przez `echo $LASTEXITCODE`; dzięki niemu skrypt da się wpiąć w większy proces bez czytania tabeli.
10. **"Then run it and show me the table"** - agent sam uruchamia skrypt, więc błąd wykonania albo złą liczbę widać od razu w czacie, zanim otworzysz plik.

## Prompt (skopiuj do Copilot Chat, tryb Agent)
```text
Read moje/plan.json (if it does not exist, read rozwiazania/plan.json instead) and dane/inwestycja.json. Write moje/sprawdz_mpzp.py in Python 3.9 using only the standard library. It must check the proposal against the plan's indicators, in this order: building coverage (powierzchnia zabudowy), intensity (intensywnosc - use the plan's own definition given in plan.json under "definicje": above-ground storeys only), biologically active area (PBC - apply the plan's rule: 50% of each green terrace or roof of at least 10 m2, smaller ones do not count), height (highest storey top in metres and number of above-ground storeys against the plan's maximum), roof slope, and parking (minimum spaces per flat; the plan allows underground spaces only, so any surface space is a failure). Print a table with the columns: Wskaźnik, Wartość, Limit, Wynik (OK or NIE), Margines. Exit with code 1 if any row is NIE. Then run it and show me the table.
```

## Jak uruchomić skrypt

Agent zwykle uruchamia skrypt sam i wkleja tabelę do czatu. Poniższe kroki uruchamiają go jeszcze raz twoimi rękami - dokładnie tak będziesz go uruchamiał w biurze, bez agenta.

1. W lewej kolumnie VS Code rozwiń folder `moje` i sprawdź, że leży w nim plik `sprawdz_mpzp.py`. Nie ma go? Napisz agentowi: "zapisz skrypt do pliku moje/sprawdz_mpzp.py".
2. Na górnej belce VS Code otwórz menu `Terminal` i wybierz `New Terminal` (menu VS Code są po angielsku). Na dole okna otwiera się panel z jedną linią tekstu zakończoną znakiem zachęty.
3. Sprawdź, że ta linia kończy się nazwą `kielce-2026-warsztat`. Jeśli kończy się inną nazwą, otwórz `File` > `Open Folder` i wskaż folder repozytorium, a potem otwórz terminal jeszcze raz.
4. Wpisz polecenie i naciśnij Enter:

```
python moje/sprawdz_mpzp.py
```

5. Tabela sześciu wskaźników wypisuje się w terminalu, tuż pod poleceniem.
6. Wpisz drugie polecenie i naciśnij Enter - wypisze kod wyjścia skryptu, czyli 0 albo 1:

```
echo $LASTEXITCODE
```

7. Komunikat `python: The term 'python' is not recognized`? Wpisz to samo polecenie ze skrótem `py` zamiast `python`. Jeśli i to nie działa, brakuje Pythona - instalacja jest opisana w README, sekcja "Wymagania".
8. Zamiast polskich liter widzisz krzaki? Wpisz raz `chcp 65001`, naciśnij Enter i powtórz polecenie z punktu 4; plik jest poprawny, to ustawienie terminala.
9. Kolejne uruchomienie: kliknij w terminal, naciśnij strzałkę w górę - wraca ostatnie polecenie - i naciśnij Enter.

## Sprawdź
- Kod wyjścia, czyli wynik polecenia `echo $LASTEXITCODE` z punktu 6 powyżej: oczekiwana wartość to 1.
- powierzchnia zabudowy: wartość 52.0 %, wynik NIE (limit 50 %).
- intensywność: wartość 2.90, wynik OK; wynik 3.65 oznacza, że agent wliczył garaż podziemny do Po.
- PBC: wartość 8.9 %, wynik NIE (limit 10 %); wynik 11.8 % oznacza, że agent policzył całe tarasy i doliczył taras 8 m2, który jest mniejszy niż próg 10 m2.
- wysokość: wartość 20.6 m / 6 kond., wynik OK.
- dach: wartość 5°, wynik OK.
- parking: wynik NIE, brakuje 3 - 3 miejsca naziemne są niedozwolone.

## Jeśli nie działa
- Powiedz agentowi wprost, który wiersz jest zły, i wskaż definicję w moje/plan.json -> definicje, np. że Po liczy tylko kondygnacje nadziemne.
- Jeśli polskie litery w tabeli w terminalu wyglądają jak krzaki (np. "Wskaźnik" jako bełkot), wpisz raz chcp 65001 w tym terminalu i uruchom skrypt ponownie - sam plik jest poprawny.
- Wzorcowe rozwiązanie: rozwiazania/01_sprawdz_mpzp.py (porównaj z nim wynik; kod zostaje twój).

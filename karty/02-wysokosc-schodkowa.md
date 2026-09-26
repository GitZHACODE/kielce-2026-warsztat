# Karta 02 - Wysokość schodkowa
**Poziom:** Samodzielnie (bez Rhino), poziom 1   **Czas:** 10 min   **Budżet:** 2 zapytania

## Cel
Na koniec masz skrypt, który sprawdza budynek kondygnacja po kondygnacji według schodkowej zasady wysokości z planu - to jest reguła, którą projektanci najczęściej łamią, bo cofnięcie trzeba liczyć osobno od dwóch różnych granic.
Widzisz, która konkretnie kondygnacja psuje wynik, zamiast jednej zbiorczej odpowiedzi NIE.

## Zanim zaczniesz
- Reguła schodkowa jest w uchwale (dane/uchwala-XLI-1014-2009.md) w § 20 ust. 2 pkt 7 lit. e-f (i w moje/plan.json -> wskazniki.wysokosc).
- W dane/inwestycja.json każda kondygnacja ma pola cofniecie_od_KDP1_m i cofniecie_od_Solnej_m.
- Jeśli masz już moje/sprawdz_mpzp.py z karty 01, miej go otwarty obok - to jest rozszerzenie tego samego pomysłu.

## Prompt krok po kroku
Każde zdanie promptu ma jedno zadanie i zamyka jedną drogę na skróty; poniżej prompt rozłożony na części w kolejności, w jakiej czyta je agent.

1. **"Extend moje/sprawdz_mpzp.py, or write moje/wysokosc_schodkowa.py"** - dwie dopuszczalne drogi: dopisanie do skryptu z karty 01 albo osobny plik; obie zostają w moje/ i liczą na tych samych danych.
2. **"with the plan's stepped height rule from moje/plan.json (or rozwiazania/plan.json if it does not exist) -> wskazniki.wysokosc"** - progi mają przyjść z pliku, nie z pamięci agenta; gałąź wskazana wprost, z planem zapasowym, gdy karta 00 się nie udała.
3. **"count only storeys with nadziemna true (the underground garage is outside this rule and does not count toward maksymalna_kondygnacje)"** - bez tego agent liczy 7 kondygnacji zamiast 6 i wystawia fałszywe NIE całemu budynkowi; lit. e i f mówią wyłącznie o kondygnacjach nadziemnych.
4. **"storeys 1 to podstawowa_kondygnacje must have their top at or below podstawowa_m"** - cztery dolne kondygnacje sprawdzasz samym pułapem 14.0 m z § 20 ust. 2 pkt 7 lit. e, bez wymogu cofnięcia; próg czytany z pliku, nie wpisany na sztywno.
5. **"any storey above that height or above podstawowa_kondygnacje must be set back at least cofniecie_kondygnacji_powyzej_podstawowej_min_m"** - próg 1.5 m z lit. f; warunek jest rozłączny ("albo"), więc piąta kondygnacja podlega mu nawet poniżej 14.0 m.
6. **"from both KDP-1 and Solna (fields cofniecie_od_KDP1_m and cofniecie_od_Solnej_m in inwestycja.json)"** - dwie granice liczone osobno; to cała pułapka karty, bo kondygnacja 5 ma 1.5 m od KDP-1 i przechodzi, ale 1.2 m od Solnej.
7. **"the whole building must stay within maksymalna_m and maksymalna_kondygnacje"** - drugi pułap, 21.0 m i 6 kondygnacji nadziemnych, sprawdzany dodatkowo, bo każda kondygnacja z osobna może być OK.
8. **"Print one row per storey with OK or NIE and the reason, plus one summary row for the whole building"** - wiersz na kondygnację zamiast jednego zbiorczego NIE, a na końcu wiersz budynku, w którym mieszczą się oba pułapy z punktu 7.
9. **"Run it."** - agent sam uruchamia skrypt, więc błąd wykonania albo zły wiersz widać w czacie, zanim otworzysz plik.

## Prompt (skopiuj do Copilot Chat, tryb Agent)
```text
Extend moje/sprawdz_mpzp.py, or write moje/wysokosc_schodkowa.py, with the plan's stepped height rule from moje/plan.json (or rozwiazania/plan.json if it does not exist) -> wskazniki.wysokosc: count only storeys with nadziemna true (the underground garage is outside this rule and does not count toward maksymalna_kondygnacje); storeys 1 to podstawowa_kondygnacje must have their top at or below podstawowa_m; any storey above that height or above podstawowa_kondygnacje must be set back at least cofniecie_kondygnacji_powyzej_podstawowej_min_m from both KDP-1 and Solna (fields cofniecie_od_KDP1_m and cofniecie_od_Solnej_m in inwestycja.json); the whole building must stay within maksymalna_m and maksymalna_kondygnacje. Print one row per storey with OK or NIE and the reason, plus one summary row for the whole building. Run it.
```

## Jak uruchomić skrypt

Agent uruchamia skrypt sam, ale wynik i tak czytasz w terminalu; poniżej każde kliknięcie po kolei.

1. W lewej kolumnie VS Code rozwiń folder `moje` i sprawdź, który plik powstał: `wysokosc_schodkowa.py`, czy rozszerzony `sprawdz_mpzp.py`. Nazwa pliku wchodzi do polecenia z punktu 3.
2. Na górnej belce VS Code otwórz menu `Terminal`, wybierz `New Terminal` (menu VS Code są po angielsku) i sprawdź, że linia na dole kończy się nazwą `kielce-2026-warsztat`.
3. Wpisz polecenie z nazwą swojego pliku i naciśnij Enter:

```
python moje/wysokosc_schodkowa.py
```

4. Tabela z jednym wierszem na kondygnację wypisuje się tuż pod poleceniem.
5. Komunikat `python: The term 'python' is not recognized`? Wpisz to samo polecenie ze skrótem `py` zamiast `python`.
6. Zamiast polskich liter widzisz krzaki? Wpisz raz `chcp 65001`, naciśnij Enter i powtórz polecenie z punktu 3.
7. Kolejne uruchomienie: kliknij w terminal, naciśnij strzałkę w górę i Enter.

## Sprawdź
- Skrypt uruchamiasz według sekcji "Jak uruchomić skrypt" powyżej, pod nazwą pliku, który zapisał agent.
- kondygnacja 5: wynik NIE - cofnięcie od Solnej to 1.2 m, a wymagane minimum to 1.5 m.
- kondygnacja 6 i kondygnacje 1-4: wynik OK.
- pułapka: cofnięcie od KDP-1 na kondygnacji 5 wynosi akurat 1.5 m i samo w sobie przechodzi - błąd jest tylko po stronie Solnej, obu granic nie wolno sprawdzać łącznie jedną liczbą.

## Jeśli nie działa
- Jeśli skrypt oznaczy kondygnację 5 jako OK, każ agentowi sprawdzić cofnięcie od Solnej i od KDP-1 osobno, każde względem swojego progu.
- Jeśli polskie litery w tabeli w terminalu wyglądają jak krzaki (np. "Wskaźnik" jako bełkot), wpisz raz chcp 65001 w tym terminalu i uruchom skrypt ponownie - sam plik jest poprawny.
- Wzorcowe rozwiązanie: rozwiazania/02_wysokosc_schodkowa.py.

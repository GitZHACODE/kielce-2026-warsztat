# Karta 03 - Ile mogę
**Poziom:** Samodzielnie (bez Rhino), poziom 2   **Czas:** 15 min   **Budżet:** 2-3 zapytania

## Cel
Na koniec masz skrypt, który zamienia każde NIE z karty 01 na konkretną liczbę: o ile zmniejszyć rzut, ile metrów zieleni dodać, ile miejsc przenieść pod ziemię.
To jest różnica między "projekt nie przechodzi" a gotową listą zmian dla zespołu projektowego.

## Zanim zaczniesz
- Miej otwarty i uruchomiony moje/sprawdz_mpzp.py z karty 01 - potrzebujesz tych samych definicji i tych samych sześciu wyników jako punktu wyjścia.
- Maksymalny rzut zabudowy liczy się z powierzchnia_zabudowy_max_pct w moje/plan.json i dzialka_m2 w dane/inwestycja.json.

## Prompt (skopiuj do Copilot Chat, tryb Agent)
```text
Write moje/ile_moge.py. Using the same data and definitions as moje/sprawdz_mpzp.py, for every indicator that fails print the smallest change that would make it pass: the maximum footprint in m2, how many m2 of native ground or of green terrace (remember the 50% rule) are missing, how many underground parking spaces are missing and what to do with the surface spaces. Also print how much floor area is still available under the intensity limit. Run it.
```

## Sprawdź
- Uruchom: `python moje/ile_moge.py`.
- powierzchnia zabudowy: maksymalny dopuszczalny rzut to 925 m2.
- PBC: brakuje 20 m2 gruntu rodzimego, albo 40 m2 dodatkowego tarasu zielonego (bo liczy się tylko 50 % tarasu).
- parking: brakuje 3 miejsc podziemnych.
- intensywność: zapas 1119 m2 powierzchni pod limitem; pułapka - to nie znaczy, że wolno dobudować kondygnację bez sprawdzenia wysokości i cofnięć z karty 02.

## Jeśli nie działa
- Jeśli liczby nie zgadzają się z kartą 01, każ agentowi ponownie użyć tych samych funkcji i definicji co w sprawdz_mpzp.py, zamiast liczyć wskaźniki od nowa.
- Jeśli polskie litery w tabeli w terminalu wyglądają jak krzaki (np. "Wskaźnik" jako bełkot), wpisz raz chcp 65001 w tym terminalu i uruchom skrypt ponownie - sam plik jest poprawny.
- Wzorcowe rozwiązanie: rozwiazania/03_ile_moge.py.

# Karta 02 - Wysokość schodkowa
**Poziom:** Samodzielnie (bez Rhino), poziom 1   **Czas:** 10 min   **Budżet:** 2 zapytania

## Cel
Na koniec masz skrypt, który sprawdza budynek kondygnacja po kondygnacji według schodkowej zasady wysokości z planu - to jest reguła, którą projektanci najczęściej łamią, bo cofnięcie trzeba liczyć osobno od dwóch różnych granic.
Widzisz, która konkretnie kondygnacja psuje wynik, zamiast jednej zbiorczej odpowiedzi NIE.

## Zanim zaczniesz
- Reguła schodkowa jest w uchwale (dane/uchwala-XLI-1014-2009.md) w § 20 ust. 2 pkt 7 lit. e-f (i w moje/plan.json -> wskazniki.wysokosc).
- W dane/inwestycja.json każda kondygnacja ma pola cofniecie_od_KDP1_m i cofniecie_od_Solnej_m.
- Jeśli masz już moje/sprawdz_mpzp.py z karty 01, miej go otwarty obok - to jest rozszerzenie tego samego pomysłu.

## Prompt (skopiuj do Copilot Chat, tryb Agent)
```text
Extend moje/sprawdz_mpzp.py, or write moje/wysokosc_schodkowa.py, with the plan's stepped height rule from moje/plan.json (or rozwiazania/plan.json if it does not exist) -> wskazniki.wysokosc: storeys 1 to 4 must have their top at or below podstawowa_m; any storey above that height or above the fourth storey must be set back at least cofniecie_kondygnacji_powyzej_podstawowej_min_m from both KDP-1 and Solna (fields cofniecie_od_KDP1_m and cofniecie_od_Solnej_m in inwestycja.json); the whole building must stay within maksymalna_m and maksymalna_kondygnacje. Print one row per storey with OK or NIE and the reason. Run it.
```

## Sprawdź
- Uruchom: `python moje/wysokosc_schodkowa.py` (albo `python moje/sprawdz_mpzp.py`, jeśli agent rozszerzył ten plik).
- kondygnacja 5: wynik NIE - cofnięcie od Solnej to 1.2 m, a wymagane minimum to 1.5 m.
- kondygnacja 6 i kondygnacje 1-4: wynik OK.
- pułapka: cofnięcie od KDP-1 na kondygnacji 5 wynosi akurat 1.5 m i samo w sobie przechodzi - błąd jest tylko po stronie Solnej, obu granic nie wolno sprawdzać łącznie jedną liczbą.

## Jeśli nie działa
- Jeśli skrypt oznaczy kondygnację 5 jako OK, każ agentowi sprawdzić cofnięcie od Solnej i od KDP-1 osobno, każde względem swojego progu.
- Jeśli polskie litery w tabeli w terminalu wyglądają jak krzaki (np. "Wskaźnik" jako bełkot), wpisz raz chcp 65001 w tym terminalu i uruchom skrypt ponownie - sam plik jest poprawny.
- Wzorcowe rozwiązanie: rozwiazania/02_wysokosc_schodkowa.py.

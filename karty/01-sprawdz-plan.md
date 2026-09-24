# Karta 01 - Sprawdź plan
**Poziom:** Wspólne   **Czas:** 10 min   **Budżet:** 1-2 zapytania

## Cel
Na koniec masz działający skrypt moje/sprawdz_mpzp.py, który w kilka sekund liczy sześć wskaźników budynku Solna i porównuje je z limitami planu.
To jest ta sama kontrola, którą architekt musi wykonać ręcznie i bezbłędnie, zanim zacznie projektować, i powtórzyć przed złożeniem projektu w urzędzie.

## Zanim zaczniesz
- Otwórz moje/plan.json (z karty 00; jeśli go nie masz, rozwiazania/plan.json) i dane/inwestycja.json - to jedyne źródła liczb dla agenta.
- Wskaźniki dla terenu U,M 2 są w § 20 ust. 2 pkt 6 uchwały XLI/1014/2009.
- Copilot Chat w trybie Agent, cały folder repo otwarty jako workspace.

## Prompt (skopiuj do Copilot Chat, tryb Agent)
```text
Read moje/plan.json (if it does not exist, read rozwiazania/plan.json instead) and dane/inwestycja.json. Write moje/sprawdz_mpzp.py in Python 3.9 using only the standard library. It must check the proposal against the plan's indicators, in this order: building coverage (powierzchnia zabudowy), intensity (intensywnosc - use the plan's own definition given in plan.json under "definicje": above-ground storeys only), biologically active area (PBC - apply the plan's rule: 50% of each green terrace or roof of at least 10 m2, smaller ones do not count), height (highest storey top in metres and number of above-ground storeys against the plan's maximum), roof slope, and parking (minimum spaces per flat; the plan allows underground spaces only, so any surface space is a failure). Print a table with the columns: Wskaźnik, Wartość, Limit, Wynik (OK or NIE), Margines. Exit with code 1 if any row is NIE. Then run it and show me the table.
```

## Sprawdź
- Uruchom: `python moje/sprawdz_mpzp.py`, a potem `echo $LASTEXITCODE` - oczekiwana wartość to 1.
- powierzchnia zabudowy: wartość 52.0 %, wynik NIE (limit 50 %).
- intensywność: wartość 2.90, wynik OK; wynik 3.65 oznacza, że agent wliczył garaż podziemny do Po.
- PBC: wartość 8.9 %, wynik NIE (limit 10 %); wynik 11.8 % oznacza, że agent policzył całe tarasy albo doliczył taras 8 m2, który jest mniejszy niż próg 10 m2.
- wysokość: wartość 20.6 m / 6 kond., wynik OK.
- dach: wartość 5°, wynik OK.
- parking: wynik NIE, brakuje 3 - 3 miejsca naziemne są niedozwolone.

## Jeśli nie działa
- Powiedz agentowi wprost, który wiersz jest zły, i wskaż definicję w moje/plan.json -> definicje, np. że Po liczy tylko kondygnacje nadziemne.
- Jeśli polskie litery w tabeli w terminalu wyglądają jak krzaki (np. "Wskaźnik" jako bełkot), wpisz raz chcp 65001 w tym terminalu i uruchom skrypt ponownie - sam plik jest poprawny.
- Wzorcowe rozwiązanie: rozwiazania/01_sprawdz_mpzp.py (porównaj z nim wynik; kod zostaje twój).

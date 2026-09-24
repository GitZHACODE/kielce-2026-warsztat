# Karta 04 - Kalkulator
**Poziom:** Samodzielnie (bez Rhino), poziom 2   **Czas:** 20 min   **Budżet:** 2-3 zapytania

## Cel
Na koniec masz jeden plik HTML, który otwierasz podwójnym kliknięciem i od razu widzisz tę samą tabelę sześciu wskaźników, przeliczaną na żywo przy każdej zmianie liczby w formularzu.
To narzędzie możesz pokazać klientowi na spotkaniu bez instalowania czegokolwiek.

## Zanim zaczniesz
- Miej otwarty moje/sprawdz_mpzp.py z karty 01 - logika liczenia ma być ta sama, tylko przeniesiona do przeglądarki.
- Miej otwarte moje/plan.json i dane/inwestycja.json - stamtąd biorą się wartości domyślne w formularzu.

## Prompt (skopiuj do Copilot Chat, tryb Agent)
```text
Turn moje/sprawdz_mpzp.py into a single HTML file moje/kalkulator.html: a form pre-filled with every number from dane/inwestycja.json, a second panel pre-filled with the limits from moje/plan.json (or rozwiazania/plan.json if it does not exist), and the same six-row table with OK/NIE recalculated on every change. Plain HTML, CSS and JavaScript in one file, no external scripts or fonts, must work offline when double-clicked. Open it and confirm the table matches the Python output.
```

## Sprawdź
- Otwórz: moje/kalkulator.html w przeglądarce (podwójny klik).
- tabela w przeglądarce pokazuje te same sześć wyników co w karcie 01: powierzchnia zabudowy 52.0 % NIE, intensywność 2.90 OK, PBC 8.9 % NIE, wysokość 20.6 m / 6 kond. OK, dach 5° OK, parking NIE (margines -3 miejsc).
- przyciski Wczytaj inwestycja.json i Wczytaj plan.json wczytują pliki repozytorium wprost do formularza; po wczytaniu etykieta wyniku pokazuje NIEZGODNE (3 wskaźniki).
- zmiana dowolnej liczby w formularzu przelicza tabelę bez odświeżania strony.
- plik otwiera się dwuklikiem z dysku i działa bez połączenia z siecią (wyłącz Wi-Fi i sprawdź ponownie).

## Jeśli nie działa
- Jeśli tabela się nie przelicza, każ agentowi dodać nasłuchiwanie na zdarzenie input na każdym polu formularza.
- Wzorcowe rozwiązanie: rozwiazania/04_kalkulator.html.

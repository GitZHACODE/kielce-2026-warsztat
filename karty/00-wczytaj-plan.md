# Karta 00 - Wczytaj plan
**Poziom:** Wspólne   **Czas:** 8 min   **Budżet:** 1-2 zapytania

## Cel
Na koniec masz własny plik moje/plan.json, zbudowany wyłącznie z pełnego tekstu uchwały planu, oraz widok porównania w VS Code, który dowodzi, że jego liczby zgadzają się z plikiem wzorcowym.
To jest właśnie umiejętność całego warsztatu: agent sam odnajduje w 34 stronach uchwały ustalenia dla jednego terenu i zamienia je na uporządkowane liczby.

## Zanim zaczniesz
- Otwórz dane/uchwala-XLI-1014-2009.md - pełny tekst uchwały, 44 paragrafy; ustalenia szczegółowe dla poszczególnych terenów są w rozdziale 3, a sześć terenów U,M zaczyna się identycznym zdaniem. To jedyne źródło liczb na tę kartę.
- Otwórz dane/plan-szablon.json - to pusty szablon, w którego kształt agent ma wpisać wartości.
- Nie otwieraj jeszcze folderu rozwiazania/ - leżą tam plik wzorcowy plan.json i wyciąg wypis-UM2.md do porównania na końcu, nie źródła do przepisania.
- Instrukcje Copilota (.github/copilot-instructions.md) cytują już definicje z § 4 i zasadę parkingową, więc te pola przyjdą agentowi łatwo; właściwa próba to wskaźniki terenu U,M 2, których w instrukcjach nie ma.
- Copilot Chat w trybie Agent, cały folder repo otwarty jako workspace.

## Prompt (skopiuj do Copilot Chat, tryb Agent)
```text
Read dane/uchwala-XLI-1014-2009.md, the full text of the Kielce local plan (uchwała XLI/1014/2009, 34 pages), and dane/plan-szablon.json, an empty template. Find the detailed provisions for terrain unit U,M 2 (the plan has six U,M units whose opening sentences are identical, so check the symbol at the end of the sentence), the plan's own definitions in its paragraph 4, and follow the cross-reference in the U,M 2 parking rule to the general provisions to find the minimum number of spaces per flat. Write moje/plan.json by filling every field of the template with values taken only from the plan text, never from general knowledge; dane/uchwala-XLI-1014-2009.md is the only source of values, so do not take them from dane/README.md, from the Copilot instructions or from the rozwiazania folder. Numbers stay numbers and booleans stay booleans. In "definicje" quote the plan's own wording for intensity, biologically active area and building height in Polish, shortened but not paraphrased from memory; for powierzchnia zabudowy write that the plan does not define it and that upzp art. 2 pkt 35 applies. Encode the stepped height rule as the base cap (metres and storeys) and the higher cap allowed with the setback. Fill "zrodla_paragrafy" with the exact paragraph, ustęp, punkt and litera each group of values comes from. Do not open the rozwiazania folder. Print the finished file.
```

## Sprawdź
- Porównaj: zaznacz moje/plan.json i rozwiazania/plan.json w Eksploratorze VS Code, prawy przycisk, "Compare Selected".
- Liczby, które muszą się zgadzać: 50, 3.5, 10, 14.0 i 4, 21.0 i 6, 1.5, 25, 1, `tylko_podziemny: true`; pola tekstowe (plan, przeznaczenie, definicje, zrodla_paragrafy) mogą różnić się brzmieniem, o ile wskazują te same paragrafy.
- zrodla_paragrafy muszą wskazywać § 20 ust. 2 pkt 6 i 7, § 15 ust. 1 pkt 3 oraz § 4 pkt 17, 29 i 30; § 19 albo § 21 w tym polu oznacza, że agent wziął sąsiedni teren U,M 1 albo U,M 3.
- Trzy pułapki: sąsiedni teren U,M o identycznym pierwszym zdaniu, maksymalna_kondygnacje odczytane jako 5 z lit. g zamiast 4 + 2 z lit. f, oraz podstawa 14.0 m zgubiona, gdy agent zakoduje tylko wysokość maksymalną 21.0 m.
- Dopiero teraz otwórz rozwiazania/wypis-UM2.md - to wyciąg z tych fragmentów uchwały, które agent powinien był znaleźć.

## Jeśli nie działa
- Jeśli agent wziął inny teren, napisz mu: teren U,M 2 to § 20, przeczytaj cały § 20 ust. 2 i popraw plik.
- Jeśli liczba się nie zgadza, odszukaj w dane/uchwala-XLI-1014-2009.md dokładny fragment, z którego ta liczba pochodzi, wklej go agentowi i poproś o poprawienie tylko tego jednego pola.
- Jeśli agent przepisał wartości z rozwiazania/, usuń moje/plan.json i uruchom prompt ponownie, zaczynając od zdania "Do not open the rozwiazania folder."
- Wzorcowe rozwiązanie: rozwiazania/plan.json (wyciąg źródłowy: rozwiazania/wypis-UM2.md).

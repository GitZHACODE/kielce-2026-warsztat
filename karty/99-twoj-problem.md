# Karta 99 - Twój problem
**Poziom:** Własny   **Czas:** 10 min   **Budżet:** 1-2 zapytania

## Cel
Na koniec masz mały skrypt do sprawdzenia albo policzenia czegoś, co sam wybrałeś - realny problem z twojego projektu.
To dowód, że umiesz zamienić dowolną zasadę na prompt, bez gotowego wzoru.

## Zanim zaczniesz
Zanim wpiszesz cokolwiek do Copilota, zapisz na kartce trzy rzeczy:
- zadanie: co skrypt ma sprawdzić albo policzyć,
- dane wejściowe: gdzie dziś leżą te liczby (plik, wypis, twoja pamięć),
- definicja "gotowe": po czym poznasz, że wynik jest poprawny.

Wpisując pola promptu, trzymaj się zasad z README, sekcja "Czego nie wklejać do promptu": bez nazw klientów i biur, bez prawdziwych numerów działek, bez wartości kontraktów i bez niepublikowanych rysunków.

Jeśli twój problem dotyczy geometrii w Rhino albo Grasshopperze, masz gdzie sięgnąć po wzór:
- karta 06 pokazuje, jak opisać wejścia i wyjścia komponentu, a README, sekcja "Jak uruchomić gotowy skrypt", pokazuje, jak go wkleić.

## Prompt krok po kroku
Każde pole w nawiasach ostrych to jedna decyzja, którą podejmujesz przed wpisaniem promptu; poniżej pola w kolejności, w jakiej je wypełniasz.

1. **"I want a script that <what it does, one sentence>"** - pole "zadanie" z kartki, jedno zdanie i jeden czasownik; przy dwóch zadaniach naraz agent wybiera sobie jedno, a drugie pomija bez słowa.
2. **"Inputs: <files or numbers and where they live>"** - pole "dane wejściowe": ścieżka do pliku albo same liczby wpisane wprost; zostawione puste, agent zmyśla dane i liczy na zmyślonych.
3. **"Output: <file, table or drawing>"** - postać wyniku, nie jego treść; bez tego pola agent wypisze najczęściej jedną liczbę, a ty potrzebujesz tabeli albo pliku do dalszej pracy.
4. **"Correct means: <the rule or the check, with its source>"** - pole "gotowe" z kartki razem ze źródłem reguły, czyli paragrafem planu, normą albo własną notatką; bez źródła agent użyje definicji z pamięci.
5. **"Example: for <this input> the result must be <this>"** - jeden przykład policzony ręcznie, po którym od razu widać pomyłkę; bez niego nie masz czym odróżnić dobrego wyniku od pewnie brzmiącego.
6. **"Use Python 3.9 standard library only"** - wersja taka jak w Rhino 8 i zakaz bibliotek, których nikt na sali nie instalował; bez tego zdania agent sięga po pandas.
7. **"write it to moje/<name>.py, run it and show me the result"** - własna nazwa pliku w folderze moje, jedynym, do którego wolno pisać; agent sam uruchamia skrypt, więc błąd widać w czacie od razu.

## Prompt (skopiuj do Copilot Chat, tryb Agent)
```text
I want a script that <what it does, one sentence>. Inputs: <files or numbers and where they live>. Output: <file, table or drawing>. Correct means: <the rule or the check, with its source>. Example: for <this input> the result must be <this>. Use Python 3.9 standard library only, write it to moje/<name>.py, run it and show me the result.
```

## Sprawdź
- wynik pasuje do tego, co sam wpisałeś w polu "Correct means", nawet jeśli agent proponuje coś, co wygląda rozsądniej.
- uruchom skrypt na przykładzie z pola "Example" i sprawdź, że wynik faktycznie się zgadza.

## Jeśli nie działa
- Jeśli agent zgaduje liczby zamiast czytać je z pliku, wklej mu dokładny fragment danych i powtórz prompt.
- Jeśli polskie litery w tabeli w terminalu wyglądają jak krzaki (np. "Wskaźnik" jako bełkot), wpisz raz chcp 65001 w tym terminalu i uruchom skrypt ponownie - sam plik jest poprawny.
- Nie ma tu wzorcowego rozwiązania - to twoje własne zadanie, poproś sąsiada albo prowadzącego o przejrzenie logiki.

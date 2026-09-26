# Praktyczne wykorzystanie AI w pracowni architektonicznej - materiały warsztatowe

Warsztat odbywa się w Kielcach, w sobotę 26 września 2026 roku. Efektem warsztatu jest sprawdzacz zgodności z miejscowym planem zagospodarowania przestrzennego (MPZP), napisany przez agenta AI na podstawie tekstu planu dla prawdziwej jednostki terenowej w Kielcach, oraz te same reguły sprawdzone na parametrycznej bryle w Rhino.

## Co tu jest

Repozytorium ma siedem folderów, każdy z jednym zadaniem.

| Folder | Co zawiera |
|---|---|
| `dane/` | pełny tekst uchwały planu (34 strony) w pliku tekstowym, pusty szablon `plan-szablon.json` do wypełnienia przez agenta oraz fikcyjna inwestycja "Solna" w pliku JSON |
| `karty/` | dziewięć kart ćwiczeniowych, karty statusu na biurko oraz karta 08, pokaz w przeglądarce dla chętnych po warsztacie |
| `rozwiazania/` | gotowe skrypty referencyjne do porównania z własnym wynikiem |
| `narzedzia/` | generator komponentów Grasshoppera oraz narzędzia prowadzącego |
| `przyklady/` | dwa przykłady zaawansowane do kart 06 i 07 (bryła z atraktorem, elewacja z wyborem wzoru i otworami) z gotowymi plikami `.ghcomp.xml` |
| `moje/` | miejsce na własne skrypty i notatki, tu zapisujesz swoją pracę |
| `zrodla/` | notatki źródłowe: wyciąg planu z komentarzem i definicje z upzp; pełny tekst uchwały jest w `dane/` |

## Jak pobrać

Repozytorium ściągasz na dwa sposoby.

1. Przycisk `Code` na stronie repozytorium, potem `Download ZIP`, i rozpakowanie archiwum w wybranym folderze.
2. Polecenie `git clone` w terminalu, jeśli masz zainstalowanego Gita.

```
git clone https://github.com/GitZHACODE/kielce-2026-warsztat.git
```

## Jak zacząć

1. Otwórz ten folder w VS Code.
2. Otwórz Copilot Chat.
3. Przełącz Copilot Chat w tryb Agent (Agent mode).
4. Otwórz kartę `karty/00-wczytaj-plan.md`.
5. Skopiuj prompt z karty i wklej go do czatu.

## Jak uruchomić gotowy skrypt

Każda karta ma własny rozdział o uruchomieniu swojego wyniku, rozpisany na kliknięcia i na nazwę pliku z tej karty; poniższe cztery punkty są skrótem dla kogoś, kto szuka samego polecenia.

1. Plik Python z terminala VS Code: otwórz Terminal, New Terminal, uruchom skrypt, a kod wyjścia odczytaj zaraz po nim.

```
python moje/sprawdz_mpzp.py
echo $LASTEXITCODE
```

2. Plik Python w Rhino 8: wpisz w wierszu poleceń `ScriptEditor`, wybierz File, Open, Run, albo przeciągnij plik na okno Rhino.

```
ScriptEditor
File > Open > Run
```

3. Komponent Grasshoppera wklejasz na dwa sposoby: jako czysty kod Pythona do komponentu Python 3 Script, albo jako gotowy plik `.ghcomp.xml` skopiowany na kanwę, a własny plik `.ghcomp.xml` wygenerujesz poleceniem `gh_params_gen.py` z opcją `--clipboard`.

   - Wklejanie czystego kodu: kliknij dwukrotnie na kanwie, wpisz "Script", wybierz Python 3 Script, kliknij dwukrotnie na komponencie i wklej kod; przybliż widok komponentu, aż pojawią się znaki plus, i dodaj nimi wejścia, ustawiając dostęp na "list" tam, gdzie karta tego wymaga.
   - Wklejanie pliku `.ghcomp.xml`: otwórz plik `.ghcomp.xml` w edytorze tekstu, zaznacz wszystko, skopiuj, i wklej klawiszami Ctrl-V na kanwie w Grasshopperze - cały komponent pojawia się od razu, ze wszystkimi wejściami i wyjściami. Każdy z trzech komponentów z `rozwiazania/` rysuje geometrię natychmiast, bez podłączania wejść, na masie Solna wbudowanej w skrypt; pierwsza linia raportu mówi wtedy, że to dane domyślne.
   - Własny plik `.ghcomp.xml` generujesz poleceniem poniżej, a wynik wklejasz tymi samymi klawiszami Ctrl-V na kanwie; polecenie zawsze zapisuje plik `moje/moj_komponent.ghcomp.xml` obok skryptu, a opcja `--clipboard` dodatkowo kopiuje archiwum do schowka.

```
python narzedzia/gh_params_gen.py moje/moj_komponent.py --clipboard
```

4. Pokaz z karty 08, `rozwiazania/08_pokaz.html`, otwierasz dwuklikiem jak kalkulator z karty 04; potrzebuje internetu, bo bibliotekę three.js pobiera z CDN przy każdym otwarciu.

## Zasady w skrócie

- Intencję opisuj po polsku, ale gotowe prompty z kart wklejaj w oryginalnej wersji angielskiej.
- GitHub Copilot Free daje około 50 zapytań agenta miesięcznie; karty 00 i 01 kosztują po jednym lub dwa zapytania.
- Każdy uczestnik dostanie od agenta inny skrypt, to jest normalne. Porównujemy wyniki w tabeli; kod każdy zachowuje własny.

## Jeśli coś nie działa

1. Copilot Chat w VS Code, tryb Agent - podstawowa droga.
2. Jeśli VS Code nie działa: `vscode.dev` z Copilot Chat, ale tylko w trybie Ask, bez trybu Agent; kod wklejasz do pliku ręcznie.
3. Jeśli nic z powyższego nie działa: dowolny czat AI w przeglądarce, kod wklejasz do pliku sam.
4. Gotowe skrypty czekają w `rozwiazania/`, skorzystaj z nich, gdy czas się kończy.
5. Jeśli polskie litery w terminalu wyglądają jak krzaki (mojibake) w Windows PowerShell 5.1, uruchom raz w tym terminalu `chcp 65001` i uruchom polecenie ponownie; terminal VS Code z PowerShell 7 tego nie wymaga, a same pliki skryptów są poprawne.

## Czego nie wklejać do promptu

- nazw klientów i biur,
- prawdziwych numerów działek,
- niepublikowanych rysunków,
- wartości kontraktów.

## W poniedziałek

Po powrocie do biura przenieś ćwiczenie na prawdziwy plan w czterech krokach.

1. Podmień treść pliku `dane/uchwala-XLI-1014-2009.md` na pełny tekst własnego planu i dostosuj w prompcie karty 00 numer uchwały, liczbę stron, symbol terenu oraz zdania o § 4, o sześciu terenach U,M i o zasadzie schodkowej.
2. Uruchom ponownie kartę 00.
3. Podmień plik `dane/inwestycja.json` na własny projekt.
4. Uruchom ponownie kartę 01.

Nowe Warunki Techniczne z 2026 roku były niepublikowane na dzień 2026-09-15. Dz.U. 2026 poz. 1161 pozwala inwestorowi przez 18 miesięcy stosować, na podstawie oświadczenia, stare Warunki Techniczne, więc dobry sprawdzacz powinien zgłaszać to jako flagę.

## Wymagania

- Windows 10 lub 11.
- VS Code, instalator User Installer.
- Konto GitHub z uwierzytelnianiem dwuskładnikowym, założone wcześniej, w domu.
- Rozszerzenie GitHub Copilot, zalogowane.
- Python 3 z python.org, zainstalowany dla bieżącego użytkownika, bez uprawnień administratora.
- Rhino 8, potrzebne tylko do kart 05-07.
- node, potrzebny tylko do testu karty 08 (`node rozwiazania/08_test.js`); sam pokaz otwiera się w przeglądarce bez node.

## Źródła

- Uchwała Nr XLI/1014/2009 Rady Miejskiej w Kielcach z dnia 19 października 2009 r., https://bipum.kielce.eu/resource/2289/Cntrum+Solna.doc.pdf
- Ustawa o planowaniu i zagospodarowaniu przestrzennym, tekst jednolity Dz.U. 2026 poz. 538.
- Dz.U. 2026 poz. 1161, art. 102a-102c Prawa budowlanego.
- Działka i inwestycja "Solna" są fikcyjne i powstały wyłącznie do ćwiczeń.

## Licencja

Materiały warsztatowe i skrypty są na licencji MIT, tekst w pliku `LICENSE`. Tekst uchwały w `dane/uchwala-XLI-1014-2009.md` jest aktem normatywnym i nie jest przedmiotem prawa autorskiego (art. 4 pkt 1 ustawy o prawie autorskim i prawach pokrewnych). Generator komponentów `narzedzia/gh_params_gen.py` pochodzi z osobnego repozytorium narzędziowego autora, również na licencji MIT.

Materiały przygotował Aleksander Mastalski, ZHA Architects.

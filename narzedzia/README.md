# narzedzia

Folder mieści narzędzia dla prowadzącego warsztatu oraz dla każdego, kto zamienia skrypt Python w komponent Grasshopper.

## gh_params_gen.py

Skrypt pochodzi bez zmian z osobnego repozytorium narzędziowego autora (`tools/gh_params_gen.py`), na licencji MIT.

Czyta docstring skryptu w konwencji opisanej niżej i zapisuje archiwum schowka `.ghcomp.xml`; wklejone kombinacją Ctrl-V na kanwę Grasshoppera staje się kompletnym komponentem Python 3 Script, z wejściami, wyjściami i podpowiedziami (tooltips).

Generator uruchamia się jednym z dwóch poleceń:

```
python narzedzia/gh_params_gen.py moje/moj_komponent.py
python narzedzia/gh_params_gen.py moje/moj_komponent.py --clipboard
```

Pierwsze polecenie zapisuje sam plik `.ghcomp.xml` obok skryptu, drugie dodatkowo kopiuje archiwum do schowka Windows. Trzecia forma, `python narzedzia/gh_params_gen.py moje/moj_komponent.py --check`, nic nie zapisuje: porównuje sidecar (zapisany obok skryptu plik `.ghcomp.xml`) z tym, co wygenerowałaby teraz, i kończy się kodem 0, gdy są identyczne, a kodem różnym od zera, gdy skrypt zmienił się po ostatniej generacji.

Konwencja docstringu, którą parser rozpoznaje, wygląda tak:

```
Purpose:
    <jedno lub dwa zdania - trafiają do podpowiedzi komponentu>

Inputs (Grasshopper):
    dzialka : Curve @item required
        Zamknięta płaska krzywa granicy działki.

Outputs (Grasshopper):
    ok : bool
        Koniunkcja wszystkich sześciu wskaźników.

Runtime:
    #! python 3 (Rhino 8, komponent Python 3 Script)
```

## test_geometrii_rhino_inside.py

Plik to narzędzie prowadzącego. Sprawdza karty 05, 06 i 07 oraz oba przykłady z `przyklady/` na wszystkich kombinacjach wzoru i typu panelu. Wymaga zainstalowanego Rhino 8 oraz osobnego środowiska Python z pakietami `pythonnet` i `rhinoinside`, uruchamianego jako `conda run -n kielce-rhino`, i nie jest potrzebny żadnej karcie warsztatowej.

## wzorzec_08.py

Plik to narzędzie prowadzącego do karty 08. Uruchamia oba przykłady z `przyklady/` pod Rhino.Inside na pięciu zestawach suwaków bryły i czternastu zestawach elewacji, a wyniki (pola kondygnacji, obrys, objętość, liczby paneli, udział paneli intensywnych) zapisuje do `rozwiazania/08_wzorzec.json` razem z tolerancjami. Ten plik JSON czyta `node rozwiazania/08_test.js`, więc test przeglądarkowego pokazu nie potrzebuje Rhino; narzędzie uruchamia się ponownie tylko wtedy, gdy zmienił się któryś z przykładów. To samo środowisko co wyżej: `conda run -n kielce-rhino --no-capture-output python narzedzia/wzorzec_08.py`, oczekiwana ostatnia linia `WZORZEC OK`.

Nic w `rozwiazania/` nie importuje niczego z tego folderu.

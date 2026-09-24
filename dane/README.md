# Dane ćwiczeniowe

Plik `uchwala-XLI-1014-2009.md` to pełny tekst uchwały planu (34 strony PDF z BIP Kielce, wydobyte do tekstu) i jedyne źródło liczb dla karty 00; agent musi sam odnaleźć w nim § 20 dla terenu U,M 2. Wyciąg tych fragmentów leży w `rozwiazania/wypis-UM2.md` jako wzorzec do porównania. Plik `plan-szablon.json` to pusty szablon, który agent wypełnia do pliku `moje/plan.json`. Plik `inwestycja.json` zawiera fikcyjną propozycję budynku do celów ćwiczeniowych; działka i budynek nie istnieją w rzeczywistości. Wzorcową odpowiedzią dla karty 00 jest `rozwiazania/plan.json`.

## plan-szablon.json i moje/plan.json

Tabela poniżej opisuje każde pole szablonu planu po kolei.

| Pole | Typ | Znaczenie |
|------|-----|-----------|
| `plan` | string | Pełna nazwa miejscowego planu zagospodarowania przestrzennego |
| `uchwala` | string | Numer i data uchwały rady miejskiej stanowiącej podstawę prawną |
| `zrodlo_url` | string | Adres URL do dokumentu planu w Biuletynie Informacji Publicznej (BIP) |
| `teren` | string | Oznaczenie terenu (U,M 2) |
| `przeznaczenie` | string | Określenie funkcji zabudowy dla tego terenu |
| `definicje.intensywnosc` | string | Definicja intensywności zabudowy w brzmieniu planu |
| `definicje.powierzchnia_biologicznie_czynna` | string | Definicja powierzchni biologicznie czynnej w brzmieniu planu |
| `definicje.wysokosc_budynku` | string | Definicja wysokości budynku w brzmieniu planu (od czego i do czego mierzona) |
| `definicje.powierzchnia_zabudowy` | string | Definicja powierzchni zabudowy albo informacja, że plan jej nie definiuje i który przepis stosuje się zastępczo |
| `wskazniki.powierzchnia_zabudowy_max_pct` | liczba | Maksymalny procent terenu, jaki może zająć budynek |
| `wskazniki.intensywnosc_max` | liczba | Maksymalna intensywność zabudowy |
| `wskazniki.pbc_min_pct` | liczba | Minimalny procent terenu jako powierzchnia biologicznie czynna |
| `wskazniki.wysokosc.podstawowa_m` | liczba | Podstawowa dopuszczalna wysokość budynku w metrach |
| `wskazniki.wysokosc.podstawowa_kondygnacje` | liczba | Liczba kondygnacji nadziemnych przy wysokości podstawowej |
| `wskazniki.wysokosc.maksymalna_m` | liczba | Maksymalna wysokość budynku w metrach, dostępna po spełnieniu warunku cofnięcia |
| `wskazniki.wysokosc.maksymalna_kondygnacje` | liczba | Liczba kondygnacji nadziemnych przy wysokości maksymalnej |
| `wskazniki.wysokosc.cofniecie_kondygnacji_powyzej_podstawowej_min_m` | liczba | Minimalne cofnięcie elewacji kondygnacji powyżej wysokości podstawowej, w metrach |
| `wskazniki.wysokosc.cofniecie_od` | tablica | Lista frontów (terenów lub ulic), od których mierzy się cofnięcie |
| `wskazniki.dach_nachylenie_max_deg` | liczba | Maksymalny kąt nachylenia połaci dachu w stopniach |
| `wskazniki.parking.miejsc_na_mieszkanie_min` | liczba | Minimalna liczba miejsc postojowych na jedno mieszkanie |
| `wskazniki.parking.tylko_podziemny` | boolean | Czy plan dopuszcza wyłącznie parking podziemny |
| `zrodla_paragrafy.wskazniki` | string | Odniesienie do paragrafu planu zawierającego wskaźniki |
| `zrodla_paragrafy.zabudowa_i_wysokosc` | string | Odniesienie do paragrafu dotyczącego zabudowy i wysokości |
| `zrodla_paragrafy.parking` | string | Odniesienie do paragrafu dotyczącego parkingu |
| `zrodla_paragrafy.definicje` | string | Odniesienie do paragrafu zawierającego definicje |

## inwestycja.json

Tabela poniżej opisuje pola fikcyjnej inwestycji po kolei.

| Pole | Typ | Znaczenie |
|------|-----|-----------|
| `nazwa` | string | Nazwa projektu inwestycji |
| `uwaga` | string | Ostrzeżenie, że dane są fikcyjne do celów ćwiczeniowych |
| `teren_planu` | string | Odniesienie do terenu z planu (U,M 2) |
| `dzialka_m2` | liczba | Całkowita powierzchnia działki w metrach kwadratowych (1850.0) |
| `powierzchnia_zabudowy_m2` | liczba | Powierzchnia rzutu budynku (962.0) |
| `kondygnacje` | tablica obiektów | Lista wszystkich kondygnacji budynku |
| `kondygnacje[].nr` | liczba | Numer kondygnacji (-1 dla podziemia, 1-6 dla nadziemnych) |
| `kondygnacje[].nazwa` | string | Opis funkcji kondygnacji |
| `kondygnacje[].nadziemna` | boolean | Czy kondygnacja liczy się do intensywności zabudowy (true dla kondygnacji powyżej terenu) |
| `kondygnacje[].powierzchnia_m2` | liczba | Powierzchnia kondygnacji liczona po zewnętrznym obrysie muru |
| `kondygnacje[].gorna_krawedz_m` | liczba | Wysokość górnej krawędzi stropu nad zerowym poziomem terenu |
| `kondygnacje[].cofniecie_od_KDP1_m` | liczba | Cofnięcie kondygnacji od linii frontu KDP-1 (mierzone od ściany zewnętrznej) |
| `kondygnacje[].cofniecie_od_Solnej_m` | liczba | Cofnięcie kondygnacji od ul. Solnej (mierzone od ściany zewnętrznej) |
| `balkony_m2` | liczba | Całkowita powierzchnia balkonów (96.0) |
| `teren_biologicznie_czynny.grunt_rodzimy_m2` | liczba | Powierzchnia naturalnego gruntu rodzimego bez zabudowy (120.0) |
| `teren_biologicznie_czynny.woda_powierzchniowa_m2` | liczba | Powierzchnia wody powierzchniowej na terenie (0.0) |
| `teren_biologicznie_czynny.tarasy_i_stropodachy_zielone_m2` | tablica | Lista tarasów i stropodachów zielonych w m2; każdy wpis to jeden taras. Liczą się tylko wpisy o powierzchni co najmniej 10 m2, i tylko w 50 %. |
| `dach.nachylenie_deg` | liczba | Kąt nachylenia dachu w stopniach (5) |
| `mieszkania` | liczba | Liczba jednostek mieszkalnych w budynku (30) |
| `miejsca_postojowe.podziemne` | liczba | Liczba miejsc parkingowych podziemnych (27) |
| `miejsca_postojowe.naziemne` | liczba | Liczba miejsc parkingowych naziemnych (3) |

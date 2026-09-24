# Przykłady zaawansowane

Folder mieści dwa przykłady zaawansowane, po jednym do kart 06 i 07: `bryla_zaawansowana_gh` rozwija bryłę spod karty 06 o dodatkowe suwaki formy, `elewacja_zaawansowana_gh` rozwija elewację spod karty 07 o wybór wzoru i typu panelu. Rozwiązania kart leżą w `rozwiazania/`; te dwa pliki są krokiem dalej dla uczestnika, któremu starczy czasu albo ciekawości. Każdy z dwóch komponentów wklejasz na te same dwa sposoby co w README.md, sekcja "Jak uruchomić gotowy skrypt": jako czysty kod Pythona do komponentu Python 3 Script, albo jako gotowy plik `.ghcomp.xml` wklejony klawiszami Ctrl-V na kanwie. Bez żadnego kabla obydwa pokazują geometrię od razu, na masie Solna wbudowanej w skrypt, a pierwsza linia raportu zaczyna się od `uwaga:`.

## bryla_zaawansowana_gh

Rozwija bryłę z karty 06 o wybór profilu przekroju, wygładzony przebieg skrętu, asymetryczne wybrzuszenie, zwężenie ku dachowi, pochylenie szczytu i punkt-atraktor, który wyciąga w swoją stronę brzuch zwróconej do niego elewacji. Wyjścia `kondygnacje_nowe` i `zabudowa_nowa` pasują do wejść kontroli z karty 05 tak samo jak w wersji podstawowej.

Wejścia, ich wartości domyślne i sugerowane zakresy suwaków:

| Wejście | Typ | Domyślnie | Zakres suwaka | Znaczenie |
|---|---|---|---|---|
| `kondygnacje` | Curve @list | - | lista krzywych | Obrysy kondygnacji na wysokości stropów; puste - siedem kondygnacji masy Solna |
| `typ_profilu` | int | 1 | 0 = prostokąt zaokrąglony, 1 = superelipsa | Kształt przekroju |
| `wykladnik_profilu` | float | 3.0 | 1.5-8 | Wykładnik superelipsy: 1.5 soczewka, 2 elipsa, 3-4 miękki prostokąt, 8 prawie prostokąt |
| `zaokraglenie` | float | 0.6 | 0-1 | Zaokrąglenie naroży dla typ_profilu 0; promień = zaokraglenie * 0.49 * krótszy bok |
| `skret_deg` | float | 25.0 | 0-60 | Całkowity skręt od terenu do dachu, w stopniach |
| `profil_skretu` | int | 1 | 0 = liniowy, 1 = wygładzony, 2 = przyspieszający | Przebieg skrętu po wysokości |
| `wybrzuszenie` | float | 0.15 | -0.3 do 0.3 | Nadwyżka (albo, przy wartości ujemnej, niedobór) skali przekroju w szczycie wybrzuszenia |
| `wysokosc_wybrzuszenia` | float | 0.5 | 0.05-0.95 | Względna wysokość, na której wybrzuszenie jest największe |
| `zwezenie` | float | 0.85 | 0.5-1.3 | Skala przekroju dachu względem parteru |
| `pochylenie_x_m` | float | 0.0 | -4 do 4 | Przesunięcie szczytu bryły wzdłuż osi X świata, w metrach |
| `pochylenie_y_m` | float | 0.0 | -4 do 4 | Przesunięcie szczytu bryły wzdłuż osi Y świata, w metrach |
| `atraktor` | Point3d | (60.0, 18.5, 10.0) | punkt (brak suwaka) | Punkt, w stronę którego wybrzusza się zwrócona do niego elewacja |
| `sila_atraktora_m` | float | 3.0 | -5 do 5 | Największe przesunięcie przekroju w stronę atraktora, w metrach; wartość ujemna robi wgłębienie |
| `zasieg_atraktora_m` | float | 15.0 | 3-40 | Zasięg atraktora po wysokości, w metrach |
| `punkty_profilu` | int | 48 | 16-64 | Liczba punktów każdego przekroju |
| `kontury_co_m` | float | 0.5 | 0-2 | Rozstaw poziomych konturów podglądu, w metrach; 0 wyłącza |

Wyjścia:
- `bryla` - zamknięta bryła z pokrywami, zorientowana na zewnątrz.
- `kondygnacje_nowe` - krzywe podziemne bez zmian, potem nowe obrysy kondygnacji na wysokościach stropów.
- `zabudowa_nowa` - obrys zabudowy: suma nowych obrysów nadziemnych zrzutowana na Z = 0.
- `plyty` - płaskie płyty kondygnacji nadziemnych z nowych obrysów.
- `kontury` - poziome kontury bryły do podglądu.
- `przekroje` - przekroje, z których powstał loft.
- `atraktor_uzyty` - punkt atraktora, którego faktycznie użył skrypt.
- `raport` - profil i atraktor, powierzchnie nowych kondygnacji wobec szkicu, suma Po, wysokość, obrys i objętość.

Spróbuj:
- Przesuń punkt `atraktor` na przeciwną stronę bryły - brzuch elewacji przeskakuje w nową stronę, a poprzednio wybrzuszona ściana wraca płaska.
- Zmień `zwezenie` z 0.85 na 0.5 - dach kurczy się wyraźnie względem parteru; przy wartości powyżej 1 dach się rozszerza.
- Przełącz `typ_profilu` na 0 i podnieś `zaokraglenie` do 1 - przekrój z gładkiej superelipsy zmienia się w mocno zaokrąglony prostokąt.

Prompt, który opisuje ten komponent:
```text
Write przyklady/bryla_zaawansowana_gh.py as a Rhino 8 Grasshopper Python 3 Script component that sculpts storey outlines into an envelope with a chosen cross-section profile, an eased twist, an asymmetric bulge, a taper, a lean, and a point attractor. Input kondygnacje (Curve, list) takes one closed planar curve per storey at its slab-top height; a curve whose highest Z is at or below 0 is underground and passes through unchanged. Input typ_profilu (int) picks the section shape: 0 a rounded rectangle whose corner radius is zaokraglenie (float, 0-1) times 0.49 times the shorter side of the bounding rectangle, 1 a superellipse shaped by wykladnik_profilu (float, from a lens through an ellipse to a near-rectangle). Input skret_deg (float) is the total twist in degrees from ground to roof about the vertical axis through the ground outline's centroid, eased over height by profil_skretu (int: 0 linear, 1 smoothstep, 2 accelerating). Inputs wybrzuszenie (float) and wysokosc_wybrzuszenia (float, 0.05-0.95) set an asymmetric bulge: a section-scale multiplier that peaks at that relative height. Input zwezenie (float) tapers the section scale linearly from 1 at the ground to that value at the roof. Inputs pochylenie_x_m and pochylenie_y_m (float) lean the top of the envelope by that many metres along the world X and Y axes. Input atraktor (Point3d) pulls the facing side of every section toward it by up to sila_atraktora_m (float, signed) metres, weighted by a Gaussian falloff over height with standard deviation zasieg_atraktora_m (float) and by the squared cosine of the angle between the section radius and the attractor direction, so the far side never moves. Input punkty_profilu (int) sets the point count per section, and kontury_co_m (float, 0 disables) the spacing of horizontal preview contours. Build each section as a list of (x, y) points in Python, turn it into a periodic degree-3 NURBS curve at its height, loft the sections with Brep.CreateFromLoft, falling back to Brep.CreateFromLoftRebuild with a System.Collections.Generic.List[Curve], cap with CapPlanarHoles and Flip if SolidOrientation is Inward, then cut the solid 1 mm below each original slab-top Z to recover the new storey outlines. Outputs: bryla (Brep), kondygnacje_nowe (list of Curve: underground curves unchanged, then the new outlines, ready for the kondygnacje input of the card 05 checker), zabudowa_nowa (Curve: boolean union of the new outlines projected to Z=0), plyty (list of planar Brep), kontury (list of Curve), przekroje (list of Curve, the sections the loft was built from), atraktor_uzyty (Point3d, the attractor actually used), and raport (list of str in Polish reporting the profile and attractor settings, each storey's new area against the sketch, total above-ground area, height, storey count, footprint and volume). Mark every input optional and embed the fixture massing as in the card 06/07 solutions. Follow the Grasshopper rules in AGENTS.md. Do not use ghpythonlib and do not generate any .gh or .ghx file.
```

## elewacja_zaawansowana_gh

Rozwija elewację z karty 07 o cztery wzory ułożenia paneli, trzy typy paneli z otworami i intensywność mieszającą ekspozycję na słońce z bliskością punktów-atraktorów, sterującą głębokością, wielkością otworu i kolorem z jednej z trzech palet albo z pary kolorów własnych.

Wejścia, ich wartości domyślne i sugerowane zakresy suwaków:

| Wejście | Typ | Domyślnie | Zakres suwaka | Znaczenie |
|---|---|---|---|---|
| `bryla` | Brep | - | bryła (brak suwaka) | Bryła do opanelowania; puste - prosty loft masy Solna bez skrętu |
| `typ_wzoru` | int | 0 | 0 = romby (diagrid), 1 = kwadraty, 2 = trójkąty, 3 = heksagony | Wzór ułożenia paneli |
| `typ_panelu` | int | 2 | 0 = płaski z otworem, 1 = piramida, 2 = ścięta piramida z otworem | Geometria panelu |
| `kolumny` | int | 36 | 12-72 | Liczba pól wzoru wokół budynku, zaokrąglana w górę do parzystej |
| `rzedy` | int | 14 | 4-30 | Liczba rzędów wzoru od dołu do góry; heksagony mają rząd co 0.75, więc dają około rzedy / 0.75 rzędów |
| `glebokosc_min_m` | float | 0.10 | 0-0.5 | Głębokość panelu przy intensywności 0, w metrach |
| `glebokosc_max_m` | float | 1.00 | 0.2-2.0 | Głębokość panelu przy intensywności 1, w metrach |
| `otwor_min` | float | 0.15 | 0.05-0.9 | Wielkość otworu jako ułamek panelu przy intensywności 1 |
| `otwor_max` | float | 0.70 | 0.05-0.9 | Wielkość otworu jako ułamek panelu przy intensywności 0 |
| `azymut_slonca_deg` | float | 180.0 | 0-360 | Azymut słońca w stopniach, zgodnie z zegarem od północy |
| `wysokosc_slonca_deg` | float | 45.0 | 5-80 | Wysokość słońca nad horyzontem w stopniach |
| `atraktory` | Point3d @list | (25.0, -20.0, 12.0) | lista punktów | Punkty, w których pobliżu panele robią się intensywne |
| `zasieg_atraktora_m` | float | 20.0 | 3-40 | Zasięg wpływu atraktora, w metrach |
| `waga_slonca` | float | 0.5 | 0-1 | Waga ekspozycji na słońce w intensywności |
| `waga_atraktora` | float | 0.5 | 0-1 | Waga bliskości atraktora w intensywności |
| `paleta` | int | 0 | 0 = grafit, 1 = miedź, 2 = ocean | Paleta kolorów od jasnego do ciemnego |
| `kolor_jasny` | Color | - | kolor (brak suwaka) | Własny kolor przy intensywności 0; działa tylko razem z kolor_ciemny |
| `kolor_ciemny` | Color | - | kolor (brak suwaka) | Własny kolor przy intensywności 1; działa tylko razem z kolor_jasny |

Wyjścia:
- `panele` - jedna siatka, osobne wierzchołki na panel, kolory wierzchołków wg intensywności.
- `siatka` - zamknięte obrysy paneli, czyli ramy wzoru.
- `otwory` - zamknięte obrysy otworów (typ_panelu 0 i 2), w kolejności paneli.
- `intensywnosc_paneli` - intensywność od 0 do 1 dla każdego panelu, w kolejności paneli.
- `srodki` - środki paneli, w kolejności paneli.
- `raport` - wzór i typ panelu, liczba paneli, osiągnięte zakresy głębokości i otworów, udział paneli intensywnych, atraktory, paleta i przybliżona powierzchnia elewacji.

Spróbuj:
- Przełącz `typ_wzoru` z romby (0) na heksagony (3) - panele układają się w plaster miodu, a ich liczba się zmienia.
- Przełącz `typ_panelu` ze ściętej piramidy (2) na piramidę (1) - otwory znikają, panele stają się pełnymi bryłkami, a wyjście `otwory` wraca puste.
- Przesuń punkt w `atraktory` bliżej elewacji albo podnieś `waga_atraktora` - panele w jego pobliżu ciemnieją i pogłębiają się niezależnie od nasłonecznienia.

Prompt, który opisuje ten komponent:
```text
Write przyklady/elewacja_zaawansowana_gh.py as a Rhino 8 Grasshopper Python 3 Script component that skins the dominant curved face of a Brep in a chosen pattern and panel type. Input bryla (Brep) is a lofted, capped envelope from 06_bryla_gh or bryla_zaawansowana_gh; pick its skin face as the largest non-planar face, or the largest face if every face is planar. Input typ_wzoru (int) selects the grid pattern built on kolumny by rzedy nodes of that face's parameter domains: 0 a diagrid of diamonds with triangles closing the top and bottom rows, 1 squares, 2 triangles splitting each square, 3 hexagons in a honeycomb layout; kolumny (int) is rounded up to even so the pattern closes on the seam. Input typ_panelu (int) picks the panel geometry: 0 a flat panel with a central opening, 1 a pyramid with its apex pushed out along the normal and no opening, 2 a truncated pyramid with an opening at the pushed-out top. For each panel compute exposure as the positive part of the dot product between its averaged normal and the sun direction for azymut_slonca_deg (clockwise from north, world +Y) and wysokosc_slonca_deg, and compute an attractor influence as a Gaussian falloff with standard deviation zasieg_atraktora_m over the distance to the nearest point in atraktory (Point3d, list). Blend the two into an intensity with weights waga_slonca and waga_atraktora, then derive the panel's push-out depth between glebokosc_min_m and glebokosc_max_m (float, metres) and, for panel types 0 and 2, its opening size between otwor_max at intensity 0 and otwor_min at intensity 1 (float, fractions of the panel). Colour every panel vertex by intensity between a light and a dark colour chosen by paleta (int: 0 graphite, 1 copper, 2 ocean), or by kolor_jasny and kolor_ciemny (Color) when both are supplied. Outputs: panele (one Mesh with vertex colours and computed normals), siatka (list of closed Polyline, one per panel outline), otwory (list of closed Polyline, one per opening, in panel order), intensywnosc_paneli (list of float per panel), srodki (list of Point3d, panel centres), and raport (list of str in Polish: pattern and panel type, panel count, achieved depth and opening ranges against their settings, share of panels above intensity 0.5, attractor count and weights, palette, approximate skin area, and a line stating this is a dot-product heuristic, not a solar analysis). Mark every input optional and embed the fixture massing as in the card 06/07 solutions. Follow the Grasshopper rules in AGENTS.md. Do not use ghpythonlib and do not generate any .gh or .ghx file.
```

## Sprawdzenie

Uruchom w PowerShell, z katalogu głównego repozytorium; każde z dwóch poleceń `--test` powinno wypisać `SELFTEST OK`.

```
conda run -n gh-tools python przyklady/bryla_zaawansowana_gh.py --test
conda run -n gh-tools python przyklady/elewacja_zaawansowana_gh.py --test
```

Sprawdź też, że oba pliki `.ghcomp.xml` są aktualne względem skryptów; każde z poniższych poleceń ma zakończyć się bez wyjścia i kodem 0.

```
conda run -n gh-tools python narzedzia/gh_params_gen.py przyklady/bryla_zaawansowana_gh.py --check
conda run -n gh-tools python narzedzia/gh_params_gen.py przyklady/elewacja_zaawansowana_gh.py --check
```

Narzędzie prowadzącego `narzedzia/test_geometrii_rhino_inside.py` uruchamia oba komponenty na kilku kombinacjach ustawień, więc jedno jego uruchomienie przed warsztatem sprawdza je razem z resztą kart.

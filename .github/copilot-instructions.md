# Instructions for coding agents in this repository

This is a hands-on workshop repository for Polish architects, run in Kielce on 26 September 2026. Attendees use GitHub Copilot agent mode in VS Code to write scripts that check a building proposal against the indicators of a real Kielce local zoning plan (miejscowy plan zagospodarowania przestrzennego, MPZP), first from the plan's own text, then on a parametric massing in Rhino 8 / Grasshopper.

## Runtime and style

- Target Python 3.9 syntax, standard library only: Rhino 8 ships CPython 3.9, and scripts here must also be pastable, unmodified, into a Rhino 8 Script component.
- Identifiers (variable, function, file names) are ASCII only.
- Comments, on-screen labels, and printed output are in Polish, with correct diacritics.
- Every script that prints must call `sys.stdout.reconfigure(encoding="utf-8")` as its first executable statement, so Polish diacritics survive on a default Windows console.
- Write attendee output only into `moje/`.
- Never modify `dane/` (the fixture data), `rozwiazania/` (the reference solutions), `narzedzia/` (the component generator and presenter tooling) or `przyklady/` (the advanced examples).
- Every Grasshopper script carries the docstring convention described under "Grasshopper and Rhino 8 rules", so `narzedzia/gh_params_gen.py` can turn it into a paste-ready component.

## Where the rules come from - precedence

When a script needs a definition (powierzchnia zabudowy, intensywnosc, PBC, wysokosc, and so on), resolve it in this order and stop at the first source that actually defines the term:

1. The plan's own definitions: § 4 of uchwala XLI/1014/2009 (the Kielce Centrum - Solna plan), quoted verbatim in `dane/uchwala-XLI-1014-2009.md` (the full text of the uchwała, 34 pages; `rozwiazania/wypis-UM2.md` is the U,M 2 excerpt kept as the answer key) and structured by card 00 into `moje/plan.json -> definicje` (reference copy: `rozwiazania/plan.json -> definicje`). The uchwała text is the authority; the excerpt and both JSON files are derived from it, and where they disagree with the uchwała, the uchwała wins. Check here first; this 2009 plan predates the 2023 upzp reform and uses its own, self-contained wording.
2. Ustawa o planowaniu i zagospodarowaniu przestrzennym (upzp), art. 2 pkt 28-35, tekst jednolity Dz.U. 2026 poz. 538. Use this only where the plan's own § 4 is silent on a term.
3. PN-ISO 9836 as a last-resort fallback only, for a term neither source above defines. Flag any value derived this way as unverified in the script's output; the workshop's source notes could not fetch the paid standard text directly.

Quote source text verbatim in Polish in any docstring or comment that cites a definition; never paraphrase a legal definition from memory.

Plan § 4 (`zrodla/kielce-mpzp-excerpt.md`):

> pkt 17: "17) powierzchni terenu biologicznie czynnej - należy przez to rozumieć grunt rodzimy oraz wodę powierzchniową na terenie działki budowlanej, a także 50 % sumy powierzchni tarasów i stropodachów o powierzchni nie mniejszej niż 10 m² urządzonych jako stałe trawniki lub kwietniki na podłożu zapewniającym im naturalną wegetację, [...]"
> pkt 29: "29) wskaźniku intensywności zabudowy – należy przez to rozumieć wskaźnik wyrażony wzorem I=Po/T gdzie: I – oznacza wskaźnik intensywności zabudowy, Po (powierzchnia ogólna) – oznacza sumę powierzchni wszystkich kondygnacji nadziemnych liczoną po zewnętrznym obrysie muru, T – oznacza powierzchnię terenu inwestycji,"
> pkt 30: "30) wysokości budynku – należy przez to rozumieć wysokość budynku mierzoną od uśrednionego poziomu chodnika (terenu) przed elewacją frontową do gzymsu lub górnej krawędzi attyki."

Upzp art. 2, Dz.U. 2026 poz. 538 (`zrodla/mpzp-definitions.md`):

> pkt 28: "28) "powierzchni biologicznie czynnej" – należy przez to rozumieć teren zapewniający naturalną wegetację roślin i retencję wód opadowych i roztopowych, teren pokryty ciekami lub zbiornikami wodnymi, z wyłączeniem basenów rekreacyjnych i przemysłowych, a także 50% powierzchni tarasów i stropodachów oraz innych powierzchni zapewniających naturalną wegetację roślin, o powierzchni niemniejszej niż 10 m²;"
> pkt 29: "29) "udziale powierzchni biologicznie czynnej" – należy przez to rozumieć stosunek sumy powierzchni biologicznie czynnych znajdujących się na: a) działce budowlanej do powierzchni tej działki budowlanej – w przypadku miejscowych planów zagospodarowania przestrzennego, b) terenie do powierzchni tego terenu – w przypadku decyzji o warunkach zabudowy i zagospodarowania terenu;"
> pkt 31: "31) "intensywności zabudowy" – należy przez to rozumieć stosunek sumy powierzchni wszystkich kondygnacji budynków zlokalizowanych na: a) działce budowlanej do powierzchni tej działki budowlanej – w przypadku miejscowych planów zagospodarowania przestrzennego, b) terenie do powierzchni tego terenu – w przypadku decyzji o warunkach zabudowy i zagospodarowania terenu;"
> pkt 32: "32) "nadziemnej intensywności zabudowy" – należy przez to rozumieć stosunek sumy powierzchni kondygnacji nadziemnych budynków zlokalizowanych na: a) działce budowlanej do powierzchni tej działki budowlanej – w przypadku miejscowych planów zagospodarowania przestrzennego, b) terenie do powierzchni tego terenu – w przypadku decyzji o warunkach zabudowy i zagospodarowania terenu;"
> pkt 33: "33) "powierzchni kondygnacji" – należy przez to rozumieć powierzchnię rzutu poziomego kondygnacji, mierzoną po zewnętrznym obrysie rzutu poziomego ścian zewnętrznych tej kondygnacji, z wyłączeniem powierzchni balkonów, loggii i tarasów;"
> pkt 34: "34) "kondygnacji nadziemnej" – należy przez to rozumieć kondygnację, która nie jest zagłębiona poniżej poziomu przylegającego do niej terenu o więcej niż połowę jej wysokości w świetle;"
> pkt 35: "35) "udziale powierzchni zabudowy" – należy przez to rozumieć stosunek sumy powierzchni rzutu poziomego budynków, z wyłączeniem części zagłębionych poniżej poziomu terenu, mierzonej po zewnętrznym obrysie rzutu poziomego ścian zewnętrznych tych budynków zlokalizowanych na: a) działce budowlanej do powierzchni tej działki budowlanej – w przypadku miejscowych planów zagospodarowania przestrzennego, b) terenie do powierzchni tego terenu – w przypadku decyzji o warunkach zabudowy i zagospodarowania terenu."

## Pitfalls

- Underground storeys are excluded from the plan's intensywnosc (§ 4 pkt 29 sums kondygnacje nadziemne only); the statute's "intensywność zabudowy" (pkt 31) includes them, its "nadziemna intensywność zabudowy" (pkt 32) does not - always know which ratio a script is testing.
- Balconies, loggias, and terraces are excluded from a storey's area (upzp pkt 33, "powierzchni kondygnacji"); never add `balkony_m2` into a floor-area total.
- PBC counts 50% of each qualifying green terrace or roof, individually, only when that single surface is at least 10 m2; never count 100% of one, and never sum several smaller surfaces together to clear the 10 m2 threshold.
- Permeable paving counts as biologically active only where it actually sustains plant vegetation and rainwater retention; sealed decorative paving does not, and no statutory minimum substrate depth exists to check against.
- Building height has more than one definition depending on which authority is being checked: the plan's § 4 pkt 30 measures to the cornice (gzyms) or attic edge from average pavement level; the statute's pkt 30 measures to the highest point of roof, wall, or attic, from the average of the lowest and highest terrain level; Warunki Techniczne § 6 measures from the lowest ground-floor entrance to the top of the topmost slab. State explicitly which one a script computes.
- Parking on U,M 2 is one space per flat (§ 15 ust. 1 pkt 3) and underground only: any naziemne (surface) space is a plan violation, not merely a shortfall.

## Data schemas

The field names below are final and match `dane/README.md`.

The plan file exists in three places with one schema. `dane/plan-szablon.json` is the empty template (strings `""`, numbers `null`, booleans `null`, `cofniecie_od` `[]`); card 00 has the agent fill it from `dane/uchwala-XLI-1014-2009.md` into `moje/plan.json` (the agent has to locate § 20 for U,M 2 itself; six U,M paragraphs open with the same sentence); `rozwiazania/plan.json` is the reference answer that cards compare against. Scripts written for attendees read `moje/plan.json` and fall back to `rozwiazania/plan.json` when it is missing; never write into `dane/` or `rozwiazania/`.

`moje/plan.json` (schema of `dane/plan-szablon.json` and `rozwiazania/plan.json`):
- `plan`, `uchwala`, `zrodlo_url`, `teren`, `przeznaczenie` - plan identity and the U,M 2 designation.
- `definicje.intensywnosc`, `definicje.powierzchnia_biologicznie_czynna`, `definicje.wysokosc_budynku` - the plan's own § 4 wording for intensity, PBC, and height, as prose strings.
- `definicje.powierzchnia_zabudowy` - the plan is silent on this term; the value routes to upzp art. 2 pkt 35 instead of § 4.
- `wskazniki.powierzchnia_zabudowy_max_pct`, `wskazniki.intensywnosc_max`, `wskazniki.pbc_min_pct` - the three headline caps.
- `wskazniki.wysokosc.podstawowa_m`, `.podstawowa_kondygnacje`, `.maksymalna_m`, `.maksymalna_kondygnacje`, `.cofniecie_kondygnacji_powyzej_podstawowej_min_m`, `.cofniecie_od[]` - the tiered height rule: a base cap, and a higher cap allowed only with a step-back from the listed frontages.
- `wskazniki.dach_nachylenie_max_deg`, `wskazniki.parking.miejsc_na_mieszkanie_min`, `wskazniki.parking.tylko_podziemny` - roof-slope cap and the parking rule.
- `zrodla_paragrafy.wskazniki`, `.zabudowa_i_wysokosc`, `.parking`, `.definicje` - the source paragraph backing each group, for citing back to the uchwala.

`dane/inwestycja.json` (a fictional proposal, not a real building):
- `nazwa`, `uwaga`, `teren_planu` - proposal name, a fictional-data warning, and which plan terrain it is checked against.
- `dzialka_m2`, `powierzchnia_zabudowy_m2` - plot area and building footprint.
- `kondygnacje[]` with `nr`, `nazwa`, `nadziemna`, `powierzchnia_m2`, `gorna_krawedz_m`, `cofniecie_od_KDP1_m`, `cofniecie_od_Solnej_m` - one entry per storey; a storey with `nadziemna: false` is excluded from intensity and coverage; `gorna_krawedz_m` is the slab-top height above ground level.
- `balkony_m2` - total balcony area, excluded from storey-area totals.
- `teren_biologicznie_czynny.grunt_rodzimy_m2`, `.woda_powierzchniowa_m2`, `.tarasy_i_stropodachy_zielone_m2[]` - each terrace entry counts toward PBC only at 10 m2 or more, and then at 50% of its own area, never summed together first.
- `dach.nachylenie_deg` - roof slope.
- `mieszkania` - flat count, drives the parking requirement.
- `miejsca_postojowe.podziemne`, `.naziemne` - underground and surface parking counts.

## Report format

A checker script produces a six-row table, in this order: powierzchnia zabudowy, intensywnosc, pow. biologicznie czynna, wysokosc, dach, parking. Columns, in order: `Wskaźnik`, `Wartość`, `Limit`, `Wynik`, `Margines`. `Wynik` holds `OK` or `NIE`, never a boolean or a different word. The script exits with code 1 if any row is `NIE`, and 0 only when every row is `OK`.

Match these number formats: percentages as one decimal, a space, and `%` (`52.0 %`); the intensity ratio as two decimals with no unit (`2.90`); roof slope as a whole number plus the degree sign (`5°`); height as metres to one decimal, a slash, and the storey count (`20.6 m / 6 kond.`); parking as counts joined by `podziemnych + ... naziemnych`. Keep `Margines` a short Polish phrase stating the surplus or shortfall, not a bare number.

## Grasshopper and Rhino 8 rules

Apply these rules to any script aimed at a Grasshopper Script component:

- `rhinoscriptsyntax` functions return GUID strings; `RhinoCommon` returns typed objects. Bridge between them with `doc.Objects.Find(guid)`, do not assume the two are interchangeable.
- Target the Rhino 8 `Python3Component`, not the legacy `IronPython2Component`; they are different SDK classes, and code written against one's `.Code` property access pattern does not drop into the other.
- Never use `isinstance()` as a type guard against a RhinoCommon or other .NET type; under CPython interop it can silently return `False` even when the type matches. Compare `obj.GetType().Name == "..."` instead.
- Call `doc.Views.Redraw()` after a standalone script edits document geometry; a Script component does not normally need to call it; Grasshopper redraws on its own.
- Converting a `System.Decimal` to a Python float needs an explicit `float(...)` call; do not assume an implicit conversion.
- `RemoveSource(Guid)` and `RemoveSource(IGH_Param)` are different overloads; passing the wrong argument type is a silent no-op, not an error.
- Never write `.gh`, `.ghx` or Grasshopper clipboard XML yourself: the format is an undocumented binary-in-XML encoding, and model-written XML will not open. Write the Python and its docstring; the deterministic tool `narzedzia/gh_params_gen.py` emits the paste-ready `.ghcomp.xml` archive from the docstring (`python narzedzia/gh_params_gen.py moje/skrypt.py --clipboard`, then Ctrl-V on the canvas). Plain Python pasted into a Python 3 Script component stays the fallback.
- Docstring convention the generator parses (section headers in English, descriptions in Polish): a `Purpose:` block; `Inputs (Grasshopper):` with one line per input `nazwa : Typ @item|@list [optional|required]` followed by an indented description; `Outputs (Grasshopper):` with one line per output `nazwa : Typ` followed by an indented description; a `Runtime:` line. Types use the tokens `Curve`, `Brep`, `Mesh`, `Polyline`, `Point3d`, `Vector3d`, `Plane`, `float`, `int`, `str`, `bool`, `Color`; `list[Curve]` on an output is documentation only. `@item` or `@list` is mandatory on every input.
- Compute areas with `Rhino.Geometry.AreaMassProperties.Compute(curve).Area`, not a manual polygon formula; handle a `None` result (an open or non-planar curve) explicitly.
- Pass a `System.Collections.Generic.List[T]` built with `.Add()`, never a Python list, to RhinoCommon methods that take `IEnumerable<T>` (`Brep.CreateFromLoft`, `Brep.CreateFromLoftRebuild`, `Curve.CreateBooleanUnion`, `Curve.JoinCurves`); under pythonnet a Python list does not convert and the call fails with "No method matches given arguments". A .NET array you already hold, such as the `Curve[]` that `Intersection.BrepPlane` returns, is an `IEnumerable<T>` and needs no wrapping.
- Build a `Rhino.Geometry.Polyline()` and `.Add()` the points; the constructor that takes a sequence has the same list-conversion problem.
- Treat `Point3d + Point3d` as unreliable in a CPython host: under pythonnet 3.0.5 (Rhino.Inside, 2026-09-23) it raised `ArgumentException` because the binder chose the `Point3d + Vector3d` overload. Average coordinates as floats and build one `Point3d` at the end. `Point3d - Point3d` (a `Vector3d`) and `Vector3d * Vector3d` (the dot product) work as expected.
- Methods with `out` parameters return tuples: `Intersection.BrepPlane(brep, plane, tol)` gives `(bool, Curve[], Point3d[])`, `curve.ClosestPoint(point)` gives `(bool, t)`.
- Lofting closed sections needs the same orientation on every section (`ClosedCurveOrientation(Vector3d.ZAxis)`, `Reverse()` when clockwise) and aligned seams (`ChangeClosedCurveSeam` at the parameter closest to a shared reference direction); otherwise the loft twists into a knot.
- After `CapPlanarHoles`, check `brep.SolidOrientation`; when it is `BrepSolidOrientation.Inward`, call `brep.Flip()`, or the volume comes back negative and the normals point inward.
- Unwired Grasshopper inputs arrive as `None` for item access and as `None` or an empty list for list access, so test falsiness (`if not kondygnacje:`), not identity; read every input through a default (`globals().get("nazwa")`) so the script also runs outside the component for its `--test` self-check.
- Every component shows something the moment its `.ghcomp.xml` is pasted with nothing wired: mark every input `optional` in the docstring (an input that is not optional and has no data stops Grasshopper from running the component at all), and when the geometry inputs are empty build the fixture massing from a table `DOMYSLNA_MASA` inside the script, a verbatim copy of `PROSTOKATY` from `rozwiazania/05_szkic_bryly_rhino.py`. The copy is deliberate: a pasted script cannot import from `rozwiazania/`, and the presenter harness checks that the copies stay identical. The first `raport` line then starts with `uwaga:` and says the defaults were used.

## Geometry cards contract

Cards 05, 06 and 07 are three Python 3 Script components that pass geometry to each other; a script extending one must keep the other two working.

- Storey convention everywhere: one closed planar curve per storey, placed at its slab-top Z within model tolerance (card 06 returns its cuts 1 mm below the slab); a curve whose highest Z is at or below 0 is an underground storey and is excluded from intensity, coverage and the envelope.
- Card 05 checker (`05_sprawdz_mpzp_gh.py`) inputs, all optional: `dzialka` (Curve, item), `zabudowa` (Curve, item), `kondygnacje` (Curve, list), `pbc_grunt` (Curve, list), `pbc_tarasy` (Curve, list), `mieszkania` (int, 30), `miejsca_podziemne` (int, 27), `miejsca_naziemne` (int, 3), `plan_json` (str, path to `moje/plan.json`; empty or missing: the built-in `DOMYSLNE_LIMITY`, a copy of `rozwiazania/plan.json -> wskazniki`). With `dzialka`, `zabudowa` and `kondygnacje` all empty the script takes all five layers from `DOMYSLNA_MASA`. Outputs: `raport` (list of str, `uwaga:` lines first), `ok` (bool), `kolory` (one `System.Drawing.Color` per storey curve), `plyty` (one planar Brep per closed storey curve, for a Custom Preview with `kolory`), `wskazniki` (JSON string). The roof row reads "brak danych" because slope cannot be read from curves.
- Card 06 envelope (`06_bryla_gh.py`) inputs: `kondygnacje` (Curve, list; empty: the seven `Kondygnacje` rows of `DOMYSLNA_MASA`), `skret_deg` (float, 12.0), `wybrzuszenie` (float, 0.10), `zaokraglenie` (float, 0.6), `pochylenie_x_m` (float, 0.0), `pochylenie_y_m` (float, 0.0), `punkty_profilu` (int, 32), `kontury_co_m` (float, 0.5). Outputs: `bryla` (closed Brep), `kondygnacje_nowe` (list of Curve: underground curves first, then the new outlines cut 1 mm below each slab-top Z), `zabudowa_nowa` (Curve: union of the new outlines projected to Z = 0), `plyty` (list of Brep), `kontury` (list of Curve), `raport` (list of str). `kondygnacje_nowe` and `zabudowa_nowa` are shaped to plug straight into card 05's `kondygnacje` and `zabudowa`.
- Card 07 skin (`07_elewacja_gh.py`) inputs: `bryla` (Brep, item; empty: a plain capped loft of the six above-ground `DOMYSLNA_MASA` storeys with no twist), `kolumny` (int, 36, forced even), `rzedy` (int, 12), `glebokosc_min_m` (float, 0.15), `glebokosc_max_m` (float, 0.90), `azymut_slonca_deg` (float, 180.0; north is world +Y, the KDP-1 edge of the fixture), `wysokosc_slonca_deg` (float, 45.0). Outputs: `panele` (Mesh with vertex colours), `siatka` (list of Polyline), `ekspozycja` (list of float), `raport` (list of str). Exposure is `max(0, normal . sun)`, a heuristic, and the report says so.
- The fixture massing comes from `rozwiazania/05_szkic_bryly_rhino.py` (layers `Dzialka`, `Zabudowa`, `Kondygnacje`, `PBC-grunt`, `PBC-tarasy`): plot 50 m by 37 m, KDP-1 along y = 37, ul. Solna along x = 0.

Two advanced examples in `przyklady/` extend cards 06 and 07 on the same canvas conventions: `bryla_zaawansowana_gh.py` and `elewacja_zaawansowana_gh.py` keep every convention above - every input optional, a `DOMYSLNA_MASA` table copied from `rozwiazania/05_szkic_bryly_rhino.py`, and a first `raport` line starting with `uwaga:` when an input is empty. `bryla_zaawansowana_gh.py` keeps card 05's `kondygnacje_nowe` and `zabudowa_nowa` contract, so it can replace `06_bryla_gh.py` on the canvas without changing anything downstream.

- `bryla_zaawansowana_gh.py` inputs: `kondygnacje` (Curve, list; empty: the seven `Kondygnacje` rows of `DOMYSLNA_MASA`), `typ_profilu` (int, 1), `wykladnik_profilu` (float, 3.0), `zaokraglenie` (float, 0.6), `skret_deg` (float, 25.0), `profil_skretu` (int, 1), `wybrzuszenie` (float, 0.15), `wysokosc_wybrzuszenia` (float, 0.5), `zwezenie` (float, 0.85), `pochylenie_x_m` (float, 0.0), `pochylenie_y_m` (float, 0.0), `atraktor` (Point3d; empty: (60.0, 18.5, 10.0)), `sila_atraktora_m` (float, 3.0), `zasieg_atraktora_m` (float, 15.0), `punkty_profilu` (int, 48), `kontury_co_m` (float, 0.5). Outputs: `bryla` (Brep), `kondygnacje_nowe` (list of Curve), `zabudowa_nowa` (Curve), `plyty` (list of Brep), `kontury` (list of Curve), `przekroje` (list of Curve), `atraktor_uzyty` (Point3d), `raport` (list of str).
- `elewacja_zaawansowana_gh.py` inputs: `bryla` (Brep; empty: a plain capped loft of the six above-ground `DOMYSLNA_MASA` storeys with no twist), `typ_wzoru` (int, 0), `typ_panelu` (int, 2), `kolumny` (int, 36, forced even), `rzedy` (int, 14), `glebokosc_min_m` (float, 0.10), `glebokosc_max_m` (float, 1.00), `otwor_min` (float, 0.15), `otwor_max` (float, 0.70), `azymut_slonca_deg` (float, 180.0), `wysokosc_slonca_deg` (float, 45.0), `atraktory` (Point3d, list; empty: [(25.0, -20.0, 12.0)]), `zasieg_atraktora_m` (float, 20.0), `waga_slonca` (float, 0.5), `waga_atraktora` (float, 0.5), `paleta` (int, 0), `kolor_jasny` (Color), `kolor_ciemny` (Color). Outputs: `panele` (Mesh with vertex colours), `siatka` (list of Polyline), `otwory` (list of Polyline), `intensywnosc_paneli` (list of float), `srodki` (list of Point3d), `raport` (list of str).

Card 08 (`karty/08-pokaz.md`) is a showcase for after the workshop: `rozwiazania/08_pokaz.html` ports `przyklady/bryla_zaawansowana_gh.py`, `przyklady/elewacja_zaawansowana_gh.py` and card 05's `oblicz` to JavaScript inside one HTML file with three.js 0.186.1 from a pinned jsdelivr import map. The pure geometry sits between `// --- GEOMETRIA ---` and `// --- KONIEC GEOMETRII ---` with no imports and no DOM, so `node rozwiazania/08_test.js` (with an optional path to another build, `node rozwiazania/08_test.js moje/08_pokaz.html`) can run it against `rozwiazania/08_wzorzec.json`, the reference values written by the presenter tool `narzedzia/wzorzec_08.py` under the `kielce-rhino` env. A rounded-rectangle profile with `zaokraglenie` 0 is kept as the exact polygon in JavaScript, so the sketch preset reproduces card 01's numbers; every other value follows the Python function by function, and the test's tolerances (storey areas 1 %, volume 5 %, panel counts exact) are the contract.

## Warunki Techniczne 2026

The new Warunki Techniczne (WT2026) were unpublished as of 2026-09-15: no position in Dziennik Ustaw existed yet for the replacement regulation. The workshop runs on 26 September 2026, six days after the 20 September statutory deadline, so this status must be re-verified on dziennikustaw.gov.pl on the day of the workshop before answering any attendee question about WT2026. Do not quote or invent any numeric threshold for WT2026 (green-area shares, parking distances, or anything else); until re-verified, say it is not yet in force and treat the current WT (Dz.U. 2019 poz. 1065) as the only citable numeric text.

A separate, confirmed transitional law, Dz.U. 2026 poz. 1161, inserts art. 102a-102c into Prawo budowlane: for 18 months from 20 September 2026, an investor may elect, by written declaration, to keep using the WT rules that were in force up to 19 September 2026 instead of whatever replaces them. If a script's logic depends on which WT version applies, expose that choice as an explicit flag or command-line argument, and default it to the old (Dz.U. 2019 poz. 1065) text, since that is the only version anyone can currently cite.

## What not to paste into a prompt

Never paste, and never let a generated script embed: real client names, real addresses, real plot (dzialka) numbers, contract values, or unpublished drawings from an actual project. `dane/inwestycja.json` is explicitly fictional (see its own `uwaga` field) precisely so attendees can share prompts and output freely without exposing real project data; keep any extension of the fixture just as fictional.

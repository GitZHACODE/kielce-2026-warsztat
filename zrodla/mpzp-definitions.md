# MPZP standard indicators - current legal definitions (Poland, as of 2026-09-15)

Prepared for the Kielce IARP workshop (AI coding agent checks a building proposal against MPZP
parameters). All quotations below are verbatim Polish, taken from a source I actually fetched;
the fetch method and URL are given for each. Anything I could not verify from a fetched source is
flagged **UNVERIFIED**.

---

## 1. Intensywność zabudowy / nadziemna intensywność zabudowy

**Statutory source:** ustawa z dnia 27 marca 2003 r. o planowaniu i zagospodarowaniu przestrzennym
(upzp), tekst jednolity ogłoszony obwieszczeniem Marszałka Sejmu z 27.03.2026 r., **Dz.U. 2026 poz.
538**, stan prawny na 23.03.2026 r. - art. 2.
Fetched: `https://dziennikustaw.gov.pl/DU/2026/538/D2026000053801.pdf` (p. 10 of the PDF).

> **Art. 2.** Ilekroć w ustawie jest mowa o: [...]
> 31) "intensywności zabudowy" – należy przez to rozumieć stosunek sumy powierzchni wszystkich
> kondygnacji budynków zlokalizowanych na:
> a) działce budowlanej do powierzchni tej działki budowlanej – w przypadku miejscowych planów
> zagospodarowania przestrzennego,
> b) terenie do powierzchni tego terenu – w przypadku decyzji o warunkach zabudowy i
> zagospodarowania terenu;
>
> 32) "nadziemnej intensywności zabudowy" – należy przez to rozumieć stosunek sumy powierzchni
> kondygnacji nadziemnych budynków zlokalizowanych na:
> a) działce budowlanej do powierzchni tej działki budowlanej – w przypadku miejscowych planów
> zagospodarowania przestrzennego,
> b) terenie do powierzchni tego terenu – w przypadku decyzji o warunkach zabudowy i
> zagospodarowania terenu;

Two supporting definitions needed to compute the above (same art. 2, same page):

> 33) "powierzchni kondygnacji" – należy przez to rozumieć powierzchnię rzutu poziomego
> kondygnacji, mierzoną po zewnętrznym obrysie rzutu poziomego ścian zewnętrznych tej kondygnacji,
> z wyłączeniem powierzchni balkonów, loggii i tarasów;
>
> 34) "kondygnacji nadziemnej" – należy przez to rozumieć kondygnację, która nie jest zagłębiona
> poniżej poziomu przylegającego do niej terenu o więcej niż połowę jej wysokości w świetle;

**How MPZP typically phrase it in practice:** exactly as pkt 32 - sum of gross floor area of
above-ground storeys ÷ plot (działka budowlana) area. Plans drawn up before the 7 July 2023 reform
often use only a single, undifferentiated "wskaźnik intensywności zabudowy" (no nadziemna/total
split). Example from a real, currently-valid Kielce plan (2009, pre-reform; see Part B for full
context and source):

> 29) "wskaźniku intensywności zabudowy" – należy przez to rozumieć wskaźnik wyrażony wzorem
> I=Po/T gdzie: I – oznacza wskaźnik intensywności zabudowy, Po (powierzchnia ogólna) – oznacza
> sumę powierzchni wszystkich kondygnacji nadziemnych liczoną po zewnętrznym obrysie muru, T –
> oznacza powierzchnię terenu inwestycji.

**Calculation pitfall:** upzp defines TWO distinct ratios - "intensywność zabudowy" (pkt 31, ALL
storeys including underground) and "nadziemna intensywność zabudowy" (pkt 32, above-ground only).
A post-2023 MPZP will usually cap both (a maximum total and a maximum nadziemna value, sometimes
also a *minimum* nadziemna value). A checker script must know which cap it is testing - including
a basement/underground garage level is correct for the first ratio but wrong for the second. Older
plans (pre-2023, like the Kielce example above) use only one number defined as "kondygnacje
nadziemne" already, so basements are excluded by definition - always read the plan's own §2/§4
definitions section first, do not assume the statutory upzp wording applies verbatim.

---

## 2. Udział powierzchni zabudowy / powierzchnia zabudowy

**Statutory source:** upzp art. 2, same fetched source as above (p. 11 of the PDF).

> 35) "udziale powierzchni zabudowy" – należy przez to rozumieć stosunek sumy powierzchni rzutu
> poziomego budynków, z wyłączeniem części zagłębionych poniżej poziomu terenu, mierzonej po
> zewnętrznym obrysie rzutu poziomego ścian zewnętrznych tych budynków zlokalizowanych na:
> a) działce budowlanej do powierzchni tej działki budowlanej – w przypadku miejscowych planów
> zagospodarowania przestrzennego,
> b) terenie do powierzchni tego terenu – w przypadku decyzji o warunkach zabudowy i
> zagospodarowania terenu.

Note: upzp only defines the **ratio** ("udział powierzchni zabudowy"). It does not define
"powierzchnia zabudowy" as a standalone area - that comes from the technical standard below.

**PN-ISO 9836** ("Właściwości użytkowe w budownictwie - Zasady obliczania wskaźników
powierzchniowych i kubaturowych"), most recent edition PN-ISO 9836:2022-07. I could not fetch the
paid PKN standard text itself; the definition below is as reported (with excerpted wording) by two
independent secondary sources I fetched:
`https://inzynierbudownictwa.pl/wskazniki-powierzchniowe-wedlug-pn-iso-9836/` and
`https://www.mgprojekt.com.pl/blog/powierzchnia-zabudowy/` (the mgprojekt page fetch returned only
a general summary, so treat the exact PN-ISO wording as **UNVERIFIED** against the primary
standard, though consistent across sources):

> Powierzchnia zabudowy jest wyznaczona przez rzut pionowy zewnętrznych krawędzi wykończonego
> budynku na powierzchnię terenu.

Excluded from powierzchnia zabudowy per PN-ISO 9836 (per the same secondary source, **UNVERIFIED**
against the paid standard text):
- powierzchnia obiektów budowlanych lub ich części niewystających ponad powierzchnię terenu
  (fully underground parts);
- powierzchnia elementów drugorzędnych budynku, np. schodów zewnętrznych, ramp zewnętrznych,
  daszków, markiz, występów dachowych, oświetlenia zewnętrznego;
- powierzchnia zajmowana przez wydzielone obiekty pomocnicze.

**Calculation pitfall:** the upzp ratio (pkt 35) explicitly excludes "części zagłębione poniżej
poziomu terenu" - so an underground garage slab that extends beyond the above-ground building
footprint generally does **not** count, even though it is very tempting to add it. Conversely,
upzp measures "po zewnętrznym obrysie ścian zewnętrznych" and does not itself exclude balconies -
while PN-ISO 9836 explicitly excludes secondary elements (external stairs, ramps, canopies,
eaves). A script must therefore pick ONE authority (the plan's own definition first, upzp second,
PN-ISO 9836 only as a fallback for anything the plan/statute is silent on) rather than mixing them.

---

## 3. Udział powierzchni biologicznie czynnej

**Statutory source:** upzp art. 2, same fetched Dz.U. 2026 poz. 538 PDF (p. 10):

> 28) "powierzchni biologicznie czynnej" – należy przez to rozumieć teren zapewniający naturalną
> wegetację roślin i retencję wód opadowych i roztopowych, teren pokryty ciekami lub zbiornikami
> wodnymi, z wyłączeniem basenów rekreacyjnych i przemysłowych, a także 50% powierzchni tarasów i
> stropodachów oraz innych powierzchni zapewniających naturalną wegetację roślin, o powierzchni
> niemniejszej niż 10 m²;
>
> 29) "udziale powierzchni biologicznie czynnej" – należy przez to rozumieć stosunek sumy
> powierzchni biologicznie czynnych znajdujących się na:
> a) działce budowlanej do powierzchni tej działki budowlanej – w przypadku miejscowych planów
> zagospodarowania przestrzennego,
> b) terenie do powierzchni tego terenu – w przypadku decyzji o warunkach zabudowy i
> zagospodarowania terenu;

**Warunki Techniczne (WT) source:** rozporządzenie Ministra Infrastruktury z 12.04.2002 r. w
sprawie warunków technicznych, jakim powinny odpowiadać budynki i ich usytuowanie, tekst jednolity
ogłoszony obwieszczeniem Ministra Inwestycji i Rozwoju z 8.04.2019 r., **Dz.U. 2019 poz. 1065**
(this is the version still in force as of 15 September 2026 - see §6 below on the pending
replacement). Fetched: `https://www.dziennikustaw.gov.pl/D2019000106501.pdf` (p. 5, § 3 pkt 22).

> § 3. Ilekroć w rozporządzeniu jest mowa o: [...]
> 22) terenie biologicznie czynnym – należy przez to rozumieć teren o nawierzchni urządzonej w
> sposób zapewniający naturalną wegetację roślin i retencję wód opadowych, a także 50% powierzchni
> tarasów i stropodachów z taką nawierzchnią oraz innych powierzchni zapewniających naturalną
> wegetację roślin, o powierzchni nie mniejszej niż 10 m², oraz wodę powierzchniową na tym terenie;

The 50%-of-terraces/roof-gardens rule and the 10 m² minimum are confirmed, worded almost
identically, in both the statute and the regulation.

**Calculation pitfall:** permeable/porous paving (ażurowe płyty, kraty trawnikowe) is a genuine
grey area - neither definition addresses paving directly; it counts only insofar as it "zapewnia
naturalną wegetację roślin i retencję wód", so a grid that actually sustains grass growth typically
qualifies, while sealed decorative paviours do not, and there is no statutory minimum soil depth
(some individual MPZP add their own, e.g. a minimum substrate thickness, but that is a *local* plan
provision, not a national rule). Also easy to miss: the 50% cap applies *per terrace/roof-garden
surface*, only above the 10 m² threshold per such surface - a script must not lump many small
terraces together to clear the 10 m² bar, and must not count 100% of a green roof, only 50%.

---

## 4. Wysokość zabudowy / wysokość budynku

These are **two different measurements of the same building**, used for different purposes - a
frequent source of confusion.

**upzp "wysokość zabudowy"** (the MPZP height cap), art. 2, Dz.U. 2026 poz. 538 (p. 10):

> 30) "wysokości zabudowy" – należy przez to rozumieć różnicę pomiędzy wysokością:
> a) najwyżej położonego punktu budynku na dachu, ścianie lub attyce, z wyłączeniem komina,
> nadbudówki mieszczącej maszynownię dźwigu lub innego pomieszczenia technicznego oraz wyjścia z
> klatki schodowej, a średnią wysokością najniższego i najwyższego poziomu terenu mierzoną na
> obwodzie rzutu poziomego ścian zewnętrznych budynku,
> b) najwyżej i najniżej położonego nad poziomem terenu punktu budowli;

**WT § 6 "wysokość budynku"** (used to classify the building into a technical-requirements height
group), Dz.U. 2019 poz. 1065 (p. 6):

> § 6. Wysokość budynku, służącą do przyporządkowania temu budynkowi odpowiednich wymagań
> rozporządzenia, mierzy się od poziomu terenu przy najniżej położonym wejściu do budynku lub jego
> części, znajdującym się na pierwszej kondygnacji nadziemnej budynku, do górnej powierzchni
> najwyżej położonego stropu, łącznie z grubością izolacji cieplnej i warstwy ją osłaniającej, bez
> uwzględniania wyniesionych ponad tę płaszczyznę maszynowni dźwigów i innych pomieszczeń
> technicznych, bądź do najwyżej położonego punktu stropodachu lub konstrukcji przekrycia budynku
> znajdującego się bezpośrednio nad pomieszczeniami przeznaczonymi na pobyt ludzi.

WT § 8 then uses that figure to sort buildings into groups N / SW / W / WW (≤12 m, 12-25 m, 25-55
m, >55 m) - same source, p. 6.

**Calculation pitfall:** the two measurements use different reference points on both ends. upzp
measures from the *average* of the lowest and highest terrain level around the building's
perimeter, up to the roof ridge/wall/attic top. WT § 6 measures from the level of the *lowest
entrance* on the ground floor, up to the top of the topmost ceiling slab (or roof deck over
habitable rooms) - not the ridge. On a sloped plot, or a building with a pitched roof, these two
numbers can differ by more than a metre. A compliance script must ask explicitly which figure is
being checked: the MPZP's "wysokość zabudowy" cap, or the WT technical height-group threshold -
never assume they are interchangeable or reuse one function for both.

---

## 5. Typical MPZP minimalna liczba miejsc postojowych - real examples with URLs

**(a) Uchwała Nr VII/85/2024 Rady Miasta Legionowo z dnia 26 listopada 2024 r.** w sprawie
uchwalenia miejscowego planu zagospodarowania przestrzennego miasta Legionowo dla obszaru
"Bukowiec A" - published Dz. Urz. Woj. Mazowieckiego 2025, poz. 475. Fetched:
`https://edziennik.mazowieckie.pl/WDU_W/2025/475/oryginal/akt.pdf` (p. 10, § 14 ust. 4):

> 3) nakazuje się zapewnienie miejsc do parkowania dla samochodów osobowych w ilości dostosowanej
> do programu funkcjonalno-użytkowego obiektu zgodnie ze wskaźnikami ilościowymi:
> a) na każdy lokal mieszkalny w budynku jednorodzinnym: minimum 2 oraz dodatkowe 1 w przypadku
> wydzielenia w budynku lokalu użytkowego, z uwzględnieniem miejsc postojowych w garażach,
> b) w budynkach mieszkalnych wielorodzinnych: minimum 1,5 na 1 mieszkanie, z uwzględnieniem miejsc
> postojowych w garażach,
> c) w budynkach usługowych, z uwzględnieniem miejsc postojowych w garażach:
> – hotele, pensjonaty: minimum 1 na 2 pokoje oraz minimum 1 dla autokarów na 30 pokoi,
> – banki, poczty, biura, administracja publiczna: minimum 3 na 100 m² powierzchni użytkowej, nie
> mniej niż 2 miejsca,
> – usługi, handel: minimum 2 na 100 m² powierzchni użytkowej, nie mniej niż 3 na 10 zatrudnionych,
> – gastronomia: na każde 100 miejsc siedzących minimum 20,
> – obiekty oświatowe: minimum 20 na 100 zatrudnionych,
> – obiekty sportu, rekreacji i wypoczynku: minimum 6 na 100 uczestników oraz minimum 4 dla
> autokarów na 1000 uczestników.

**(b) Uchwała Nr XLI/1014/2009 Rady Miejskiej w Kielcach z dnia 19 października 2009 r.**,
"Kielce Centrum - Obszar I.2 Centrum - Solna" (see Part B for the full plan). Fetched:
`https://bipum.kielce.eu/resource/2289/Cntrum+Solna.doc.pdf` (p. 11, § 15 ust. 1 pkt 3):

> dla terenów U,M 2 i U,M 5, w odniesieniu do inwestycji budownictwa mieszkaniowego ustala się
> minimalny wskaźnik: jedno miejsce postojowe na jedno mieszkanie.

These two real plans between them illustrate all three common rate forms named in the brief: X
miejsc/lokal mieszkalny (Legionowo, jednorodzinny), Y na 1 mieszkanie (Legionowo wielorodzinny AND
Kielce), and Z miejsc na 100 m² powierzchni użytkowej usług (Legionowo, several service types).

---

## 6. Warunki Techniczne 2026 (WT2026) - what changes, and publication status

**Publication status as of 2026-09-15:** **not published** in Dziennik Ustaw. Checked via
`dziennikustaw.gov.pl` search and multiple industry-press sources; the most recent dated
confirmation I could fetch is an rp.pl article
(`https://www.rp.pl/nieruchomosci/art44817971-jak-mamy-budowac-po-20-wrzesnia-2026-pyta-branza-ministerstwo-odpowiada-aktualizacja`,
last updated 16 July 2026) stating the regulation was still being finalised and an "epizodyczny
przepis" (episodic/transitional provision) had just been tabled in the Sejm as a stop-gap. A
WebSearch pass dated to early September 2026 (secondary, not independently fetched, so
**UNVERIFIED** as a primary source but consistent across several outlets) reports the draft was
still unsigned as of 31 August/4 September 2026. I found **no evidence of a Dz.U. position** for
the WT2026 regulation itself as of today. Treat "not yet published" as correct as of the last
verifiable check and re-confirm on the day of the workshop.

Reported (but **UNVERIFIED** against a fetched primary text of the draft rozporządzenie itself -
the draft is not yet a published act, so there is nothing authoritative to quote) content
highlights, per multiple secondary sources: implements EU directives EPBD (energy performance of
buildings), RED III (renewable energy) and the Gigabit Infrastructure Act; merges building-design
and building-use rules into one document as a new Dział XII; some provisions (solar-energy related)
delayed to 31 December 2026, others to 2030. I could **not** independently verify the specific "new
minimum green share" figure or the "10 m / 6 m parking distance rules" mentioned as expected
changes - no fetched source gave exact numbers, so these remain **UNVERIFIED**; do not present them
to workshop attendees as settled figures.

**18-month transitional provision - CONFIRMED verbatim.** Ustawa z dnia 31 lipca 2026 r. o zmianie
ustawy o samorządach zawodowych architektów oraz inżynierów budownictwa oraz ustawy - Prawo
budowlane, ogłoszona 1 września 2026 r., **Dz.U. 2026 poz. 1161**. Fetched:
`https://dziennikustaw.gov.pl/D2026000116101.pdf` (pp. 2-3). It inserts into Prawo budowlane a new
Rozdział 10a "Przepisy epizodyczne":

> Art. 102a. 1. W okresie 18 miesięcy od dnia 20 września 2026 r. projekt zagospodarowania działki
> lub terenu lub projekt architektoniczno-budowlany, może zostać sporządzony zgodnie z przepisami
> wydanymi na podstawie art. 7 ust. 2 pkt 1, obowiązującymi do dnia 19 września 2026 r. do: 1)
> wniosku o pozwolenie na budowę, 2) wniosku o wydanie odrębnej decyzji o zatwierdzeniu projektu
> zagospodarowania działki lub terenu lub projektu architektoniczno-budowlanego, 3) zgłoszenia
> budowy – po złożeniu organowi prowadzącemu postępowanie oświadczenia inwestora o stosowaniu tych
> przepisów. [...]
>
> Art. 102b. W okresie 18 miesięcy od dnia 20 września 2026 r. inwestor może stosować przepisy
> wydane na podstawie art. 7 ust. 2 pkt 1, obowiązujące do dnia 19 września 2026 r. do budowy, o
> której mowa w art. 29 ust. 2, oraz wykonywania robót budowlanych, o których mowa w art. 29 ust. 4.
>
> Art. 102c. W okresie 18 miesięcy od dnia 20 września 2026 r. dopuszcza się utrzymywanie i
> użytkowanie budynków mieszkalnych zgodnie z przepisami wydanymi na podstawie art. 7 ust. 3 pkt 1,
> obowiązującymi do dnia 19 września 2026 r.

Practical upshot for the workshop: today, and for 18 months after the new WT eventually takes
effect (20 Sept 2026 being the statutory deadline for it to exist, per the 2019 Accessibility Act's
84-month mandate), an investor can elect - by written declaration - to keep using the *old* WT
(Dz.U. 2019 poz. 1065, as quoted in §3/§4 above) instead of the new one. A checker script aimed at
architects in this transition window should probably support both rule-sets and ask the user which
one applies to their specific submission.

---

## Confidence and gaps

- **High confidence (primary source fetched directly, exact article/paragraph cited):** upzp art. 2
  pkt 28-35 (Dz.U. 2026 poz. 538); WT § 3 pkt 22 and § 6 (Dz.U. 2019 poz. 1065); the Dz.U. 2026 poz.
  1161 transitional articles 102a-102c; both parking examples (Legionowo, Kielce).
- **Medium confidence (consistent across secondary sources, but the primary paid standard was not
  directly fetched):** the exact PN-ISO 9836 wording and exclusion list for "powierzchnia
  zabudowy" - PN-ISO 9836 is a paid PKN standard with no free official full text online; what is
  quoted above is as reported by architecture-industry blogs, not the standard itself.
  Recommend telling workshop participants this one is "industry-standard practice, verify against
  your paid copy of the norm" rather than statute.
- **Confirmed absence, not a gap:** WT2026 itself has genuinely not been published as an act as of
  the last check (mid-July to early-September 2026 sources) - there is nothing to quote because
  nothing has legal force yet. This should be re-checked on `dziennikustaw.gov.pl` on the day of
  the workshop, since the deadline (20 September 2026) is only days away from today's date.
  Specific new numeric thresholds attributed to WT2026 (green-share %, 10 m/6 m parking distances)
  could not be verified from any fetched source and are flagged UNVERIFIED above - do not teach
  them as fact.
- **Weak/unverified:** the Kielce plan's Dz. Urz. Woj. Świętokrzyskiego citation format
  ("2009.503.3688") - see Part B confidence note; not independently confirmed by directly fetching
  edziennik.kielce.uw.gov.pl (that site returned navigation pages, not the indexed act, within the
  time available).

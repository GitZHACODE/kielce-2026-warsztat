// Samosprawdzenie karty 08 (pokaz w przeglądarce). Uruchomienie: node rozwiazania/08_test.js [plik.html]
// Bez argumentu sprawdza rozwiazania/08_pokaz.html; z argumentem inną wersję strony (np. moje/08_pokaz.html).
"use strict";
var assert = require("assert");
var fs = require("fs");
var path = require("path");

var PLIK = process.argv[2] ? path.resolve(process.argv[2]) : path.join(__dirname, "08_pokaz.html");
var HTML = fs.readFileSync(PLIK, "utf8");
var WZORZEC = JSON.parse(fs.readFileSync(path.join(__dirname, "08_wzorzec.json"), "utf8"));
var START = "// --- GEOMETRIA ---", KONIEC = "// --- KONIEC GEOMETRII ---";
var a = HTML.indexOf(START), b = HTML.indexOf(KONIEC);
assert(a !== -1 && b > a, "brak znaczników bloku GEOMETRIA");
var blok = HTML.slice(a + START.length, b);
assert(!/\bimport\b|\bdocument\b|\bwindow\.\w/.test(blok.replace(/window\.GEOMETRIA = GEOMETRIA/, "")), "blok GEOMETRIA ma importy albo DOM");
var m = { exports: {} };
new Function("module", blok)(m);
var G = m.exports;
assert(G && typeof G.zbudujElewacje === "function", "blok GEOMETRIA nie eksportuje geometrii - to nie jest strona pokazu");
var T = WZORZEC.tolerancje;

function bliskoPct(a, b, pct, opis) {
  assert(Math.abs(a - b) <= Math.abs(b) * pct / 100, opis + ": " + a + " vs wzorzec " + b + " (" + pct + " %)");
}

// 1) DOMYSLNA_MASA == PROSTOKATY z 05_szkic_bryly_rhino.py
var py = fs.readFileSync(path.join(__dirname, "05_szkic_bryly_rhino.py"), "utf8");
var prost = py.slice(py.indexOf("PROSTOKATY = ["), py.indexOf("]", py.indexOf("PROSTOKATY = [")));
var wiersze = prost.match(/\("([^"]+)",\s*([-\d.]+),\s*([-\d.]+),\s*([-\d.]+),\s*([-\d.]+),\s*([-\d.]+)\)/g);
assert.strictEqual(wiersze.length, 12);
var prostokaty = wiersze.map(function (w) {
  var g = w.match(/\("([^"]+)",\s*([-\d.]+),\s*([-\d.]+),\s*([-\d.]+),\s*([-\d.]+),\s*([-\d.]+)\)/);
  return [g[1], +g[2], +g[3], +g[4], +g[5], +g[6]];
});
assert.deepStrictEqual(G.DOMYSLNA_MASA, prostokaty, "DOMYSLNA_MASA rozjechała się z PROSTOKATY");

// 2) B-spline: wielokąt foremny o 64 punktach na okręgu jednostkowym daje pole bliskie pi
var kolo = [];
for (var i = 0; i < 64; i++) kolo.push([Math.cos(2 * Math.PI * i / 64), Math.sin(2 * Math.PI * i / 64)]);
var krzywa = G.bsplineZamkniety(kolo, 4);
assert.strictEqual(krzywa.length, 256);
assert(Math.abs(G.poleWielokata(krzywa) - Math.PI) < 0.02, "pole B-spline koła " + G.poleWielokata(krzywa));

// 3) ustawienia: wartości spoza zakresu wracają do domyślnych z ostrzeżeniem
var u = G.ustawieniaBryly({ typ_profilu: 9, zwezenie: 0.05, punkty_profilu: 4 });
assert.strictEqual(u.ust.typ_profilu, 1); assert.strictEqual(u.ust.zwezenie, 0.2); assert.strictEqual(u.ust.punkty_profilu, 12);
assert.strictEqual(u.bledy.length, 3);
var ue = G.ustawieniaElewacji({ typ_wzoru: 7, kolumny: 3, otwor_min: 0.0 });
assert.strictEqual(ue.ust.typ_wzoru, 0); assert.strictEqual(ue.ust.kolumny, 4);

// 4) Bryły wobec wzorca
Object.keys(WZORZEC.bryly).forEach(function (nazwa) {
  var w = WZORZEC.bryly[nazwa];
  var ust = G.ustawieniaBryly(w.ustawienia).ust;
  var bryla = G.zbudujBryle(ust);
  assert.strictEqual(bryla.kondygnacje.length, w.kondygnacje, nazwa + ": liczba kondygnacji");
  bryla.kondygnacje.forEach(function (k, i) { bliskoPct(k.poleM2, w.pola_m2[i], T.pole_pct, nazwa + " kondygnacja " + (i + 1)); });
  bliskoPct(bryla.obrysM2, w.obrys_m2, T.obrys_pct, nazwa + " obrys");
  bliskoPct(bryla.objetoscM3, w.objetosc_m3, T.objetosc_pct, nazwa + " objętość");
  assert(Math.abs(bryla.wysokoscM - w.wysokosc_m) <= T.wysokosc_m, nazwa + " wysokość");
  assert.strictEqual(bryla.podziemne.length, 1);
  assert(bryla.siatka.indeksy.length % 3 === 0 && bryla.siatka.pozycje.length === bryla.siatka.normalne.length);
  assert(bryla.raport[0].indexOf("profil:") === 0, nazwa + " pierwsza linia raportu");
});
var bez = G.zbudujBryle(G.ustawieniaBryly({ sila_atraktora_m: 0 }).ust);
assert(bez.raport[0].indexOf("atraktor: brak") !== -1);

// 5) Szkic: dokładne prostokąty i tabela z karty 01
var szkic = G.zbudujBryle(G.ustawieniaBryly(WZORZEC.bryly.szkic.ustawienia).ust);
assert.deepStrictEqual(szkic.kondygnacje.map(function (k) { return +k.poleM2.toFixed(3); }), [962, 962, 962, 962, 782, 726]);
assert.strictEqual(+szkic.obrysM2.toFixed(3), 962);
var kond = szkic.podziemne.map(function (k) { return [k.poleM2, k.z]; })
  .concat(szkic.kondygnacje.map(function (k) { return [k.poleM2, k.z]; }));
var P = G.DOMYSLNE_PLANU;
var wiersze6 = G.oblicz(1850, szkic.obrysM2, kond, P.pbc_grunt_m2, P.pbc_woda_m2, [P.taras1_m2, P.taras2_m2],
  P.mieszkania, P.miejsca_podziemne, P.miejsca_naziemne, P.dach_nachylenie_deg, G.DOMYSLNE_LIMITY);
assert.strictEqual(wiersze6.length, 6);
assert.deepStrictEqual(wiersze6.map(function (w) { return w.ok; }), [false, true, false, true, true, false]);
assert.strictEqual(wiersze6[0].wartosc, "52.0 %"); assert.strictEqual(wiersze6[0].margines, "przekroczenie 2.0 pp");
assert.strictEqual(wiersze6[1].wartosc, "2.90"); assert.strictEqual(wiersze6[1].margines, "zapas 0.60");
assert.strictEqual(wiersze6[2].wartosc, "8.9 %"); assert.strictEqual(wiersze6[2].margines, "brakuje 1.1 pp");
assert.strictEqual(wiersze6[3].wartosc, "20.6 m / 6 kond."); assert.strictEqual(wiersze6[3].margines, "zapas 0.4 m i 0 kond.");
assert.strictEqual(wiersze6[4].wartosc, "5°"); assert.strictEqual(wiersze6[4].limit, "25°"); assert.strictEqual(wiersze6[4].margines, "20° zapasu");
assert.strictEqual(wiersze6[5].wartosc, "27 podziemnych + 3 naziemnych");
assert.strictEqual(wiersze6[5].margines, "brakuje 3 miejsc; 3 miejsc naziemnych niedozwolonych");
var brzeg = G.oblicz(1850, 900, kond, 120, 0, [90, 8], 0, 5, 0, 30, G.DOMYSLNE_LIMITY);
assert.strictEqual(brzeg[5].margines, "zapas 5 miejsc"); assert.strictEqual(brzeg[4].margines, "5° za dużo");

// 6) Elewacje wobec wzorca
var brylaZaaw = G.zbudujBryle(G.ustawieniaBryly(WZORZEC.bryly.zaaw_domyslny.ustawienia).ust);
Object.keys(WZORZEC.elewacje).forEach(function (nazwa) {
  var w = WZORZEC.elewacje[nazwa];
  var ust = G.ustawieniaElewacji(w.ustawienia).ust;
  var e = G.zbudujElewacje(brylaZaaw, ust, G.DOMYSLNE_ATRAKTORY);
  assert.strictEqual(e.intensywnosci.length, w.paneli, nazwa + ": liczba paneli");
  assert.strictEqual(e.ramy.length, w.paneli);
  assert(e.panele.kolory.every(function (c) { return !isNaN(c); }), nazwa + ": NaN w kolorach");
  if (w.powyzej_05 !== undefined) {
    var powyzej = e.intensywnosci.filter(function (x) { return x > 0.5; }).length;
    assert(Math.abs(100 * powyzej / w.paneli - 100 * w.powyzej_05 / w.paneli) <= T.udzial_pp, nazwa + ": udział > 0.5");
    var g = e.intensywnosci.map(function (x) { return ust.glebokosc_min_m + (ust.glebokosc_max_m - ust.glebokosc_min_m) * x; });
    assert(Math.abs(Math.min.apply(null, g) - w.glebokosc_min_m) <= T.glebokosc_m);
    assert(Math.abs(Math.max.apply(null, g) - w.glebokosc_max_m) <= T.glebokosc_m);
    bliskoPct(e.powierzchniaM2, w.powierzchnia_m2, T.powierzchnia_pct, nazwa + " powierzchnia");
  }
  if (ust.typ_panelu === 1) assert.strictEqual(e.otwory.length, 0); else assert.strictEqual(e.otwory.length, w.paneli);
});
var wlasne = G.zbudujElewacje(brylaZaaw, G.ustawieniaElewacji({}).ust, G.DOMYSLNE_ATRAKTORY, [255, 255, 255], [10, 10, 10]);
assert(wlasne.raport.some(function (l) { return l.indexOf("paleta: kolory własne") !== -1; }));

// 7) Strona
assert(HTML.indexOf('"three": "https://cdn.jsdelivr.net/npm/three@0.186.1/build/three.module.js"') !== -1, "import map three");
assert(HTML.indexOf('"three/addons/": "https://cdn.jsdelivr.net/npm/three@0.186.1/examples/jsm/"') !== -1, "import map addons");
var hosty = HTML.match(/https?:\/\/[^\s"'<>)]+/g).filter(function (h) { return h.indexOf("cdn.jsdelivr.net/npm/three@0.186.1/") === -1; });
assert.deepStrictEqual(hosty, [], "obce adresy: " + hosty.join(", "));
assert(HTML.indexOf("aria-live") !== -1 && HTML.indexOf("data-theme") !== -1 && HTML.indexOf("data-lang") !== -1);

// 8) Panel: każda kontrolka z KONTROLKI ma dokładnie jedno miejsce w SEKCJE (pominięte, gdy strona nie ma tabeli SEKCJE)
var sekcjeOd = HTML.indexOf("var SEKCJE = [");
if (sekcjeOd === -1) {
  console.log("uwaga: brak tabeli SEKCJE w " + PLIK + ", sprawdzenie 8 pominięte");
} else {
  var kontrolki = (HTML.match(/\["(?:bryla|elewacja|plan)", "([a-z0-9_]+)", "(?:wybor|zakres|liczba|kolor)"/g) || [])
    .map(function (w) { return w.split('"')[3]; });
  var sekcje = HTML.slice(sekcjeOd, HTML.indexOf("\n];", sekcjeOd));
  var wSekcjach = [];
  sekcje.replace(/\[([^\[\]]*)\]\]/g, function (calosc, lista) {
    lista.split(",").forEach(function (s) { var k = s.trim().replace(/"/g, ""); if (k) wSekcjach.push(k); });
  });
  assert.strictEqual(kontrolki.length, 44, "liczba kontrolek w KONTROLKI");
  assert.deepStrictEqual(wSekcjach.slice().sort(), kontrolki.slice().sort(), "SEKCJE rozjechały się z KONTROLKI");
}
console.log("SELFTEST OK");

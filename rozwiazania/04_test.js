// Samosprawdzenie rozwiazania Karty 04 (kalkulator MPZP dla U,M 2 - Solna).
// Uruchomienie: node rozwiazania/04_test.js
"use strict";

var assert = require("assert");
var fs = require("fs");
var path = require("path");

var HTML_PATH = path.join(__dirname, "04_kalkulator.html");
var START_MARKER = "// --- LOGIKA ---";
var END_MARKER = "// --- KONIEC LOGIKI ---";

var html = fs.readFileSync(HTML_PATH, "utf8");

var startIdx = html.indexOf(START_MARKER);
var endIdx = html.indexOf(END_MARKER);
assert(startIdx !== -1, "brak znacznika " + START_MARKER);
assert(endIdx !== -1, "brak znacznika " + END_MARKER);
assert(endIdx > startIdx, "znaczniki w zlej kolejnosci");

var logika = html.slice(startIdx + START_MARKER.length, endIdx);

var fakeModule = { exports: {} };
var uruchomLogike = new Function("module", logika);
uruchomLogike(fakeModule);
var oblicz = fakeModule.exports.oblicz;
assert(typeof oblicz === "function", "blok logiki nie eksportuje funkcji oblicz");

// Fixture = dane/inwestycja.json, limity = rozwiazania/plan.json.wskazniki (przepisane recznie,
// zgodnie z briefem zadania - test nie czyta plikow z dane/).
var dane = {
  dzialka_m2: 1850.0,
  powierzchnia_zabudowy_m2: 962.0,
  kondygnacje: [
    { nadziemna: false, powierzchnia_m2: 1400.0, gorna_krawedz_m: -0.3 },
    { nadziemna: true, powierzchnia_m2: 962.0, gorna_krawedz_m: 4.2 },
    { nadziemna: true, powierzchnia_m2: 962.0, gorna_krawedz_m: 7.4 },
    { nadziemna: true, powierzchnia_m2: 962.0, gorna_krawedz_m: 10.6 },
    { nadziemna: true, powierzchnia_m2: 962.0, gorna_krawedz_m: 13.8 },
    { nadziemna: true, powierzchnia_m2: 782.0, gorna_krawedz_m: 17.2 },
    { nadziemna: true, powierzchnia_m2: 726.0, gorna_krawedz_m: 20.6 }
  ],
  grunt_rodzimy_m2: 120.0,
  woda_powierzchniowa_m2: 0.0,
  tarasy_zielone: [90.0, 8.0],
  dach_nachylenie_deg: 5,
  mieszkania: 30,
  miejsca_postojowe: { podziemne: 27, naziemne: 3 }
};

var limity = {
  powierzchnia_zabudowy_max_pct: 50,
  intensywnosc_max: 3.5,
  pbc_min_pct: 10,
  wysokosc: { maksymalna_m: 21.0, maksymalna_kondygnacje: 6 },
  dach_nachylenie_max_deg: 25,
  parking: { miejsc_na_mieszkanie_min: 1, tylko_podziemny: true }
};

var wyniki = oblicz(dane, limity);

assert.strictEqual(wyniki.length, 6, "oczekiwano szesciu wskaznikow");

var okFlagi = wyniki.map(function (w) { return w.ok; });
assert.deepStrictEqual(
  okFlagi,
  [false, true, false, true, true, false],
  "flagi ok nie zgadzaja sie z oczekiwanymi: " + JSON.stringify(okFlagi)
);

assert(
  wyniki[0].wartosc.indexOf("52.0") === 0,
  "wiersz 0 (pokrycie) powinien zaczynac sie od 52.0, jest: " + wyniki[0].wartosc
);
assert.strictEqual(
  wyniki[1].wartosc,
  "2.90",
  "wiersz 1 (intensywnosc) powinien byc 2.90, jest: " + wyniki[1].wartosc
);
assert(
  wyniki[2].wartosc.indexOf("8.9") === 0,
  "wiersz 2 (PBC) powinien zaczynac sie od 8.9, jest: " + wyniki[2].wartosc
);
assert.strictEqual(
  wyniki[3].wartosc,
  "20.6 m / 6 kond.",
  "wiersz 3 (wysokosc) powinien byc '20.6 m / 6 kond.', jest: " + wyniki[3].wartosc
);

assert(html.indexOf("<script src") === -1, "strona nie moze ladowac skryptow zewnetrznych");
assert(html.indexOf("<link") === -1, "strona nie moze ladowac linkow zewnetrznych");
assert(html.indexOf("http") === -1, "strona nie moze zawierac adresow http/https");
assert(html.indexOf('type="file"') !== -1, "strona powinna umozliwiac wczytanie inwestycja.json i plan.json z dysku");
assert(html.indexOf("aria-live") !== -1, "werdykt powinien byc ogloszony przez aria-live");

console.log("SELFTEST OK");

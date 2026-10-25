# Prednost domačega terena in boj za naslov v Premier League (1992–2026)

Projektna naloga pri predmetu **Uvod v programiranje** (FMF, Univerza v Ljubljani).

Projekt s spletne strani [FBref.com](https://fbref.com/en/comps/9/Premier-League-Stats)
zajame podatke o vseh tekmah in končnih lestvicah angleške Premier League
od sezone 1992/93 do sezone 2025/26 (34 sezon) in jih analizira.

Odgovoriti želim na dve skupini vprašanj:

1. **Ali domači teren vpliva na uspeh?** Kako pogosto zmagajo domači, ali dajo
   več golov, kaj se je zgodilo, ko so bile tribune med epidemijo covida-19
   prazne, in ali več gledalcev pomeni več zmag.
2. **Kdo osvaja ligo in koliko točk je za to potrebnih?** Kateri klubi so
   najpogosteje na vrhu in na dnu lestvice, koliko točk potrebuje prvak,
   koliko jih je dovolj za obstanek in kako velika je razlika med vrhom in dnom.

## Pridobivanje podatkov

Podatki se zajamejo s spletnim strgalnikom (brez API-ja) v dveh ločenih korakih:

1. **Shranjevanje strani** (`prenos_strani.py`): za vsako sezono potrebujemo
   stran s končno lestvico in stran z vsemi tekmami (skupaj 68 strani).
   FBref je zaščiten pred roboti (Cloudflare) in programom vrača napako 403,
   zato program vsako stran odpre v brskalniku, uporabnik jo shrani s
   Ctrl+S, program pa shranjeno datoteko poišče v mapi Prenosi, preveri, da
   vsebuje pravo tabelo (lestvico ali tekme prave sezone, po atributu `id`),
   in jo premakne v mapo `html_strani/` (ta ni na GitHubu). Napačno shranjena
   stran (npr. druga sezona) se zavrne.
   Že shranjene strani se ob ponovnem zagonu preskočijo, zato lahko delo
   kadarkoli prekineš.
2. **Izluščanje podatkov** (`izlusci_podatke.py`): iz shranjenih strani se z
   BeautifulSoup izluščijo podatki. Tabele program poišče po atributu `id`,
   posamezne podatke v vrsticah pa po atributu `data-stat`. Ker FBref nekatere
   tabele skrije v HTML komentarje, se oznake komentarjev pred branjem odstranijo.
   Izluščijo se:
   - **končne lestvice** vseh sezon (mesto, klub, zmage, remiji, porazi, goli,
     točke, povprečje gledalcev, najboljši strelec in opomba, npr. izpad ali
     odbitek točk),
   - **vse odigrane tekme** (krog, datum, ura, domači in gostje, rezultat,
     gledalci, stadion, sodnik) z izpeljanim izidom: `D` zmaga domačih,
     `X` remi, `G` zmaga gostov. Vmesne in naslovne vrstice tabele se preskočijo.

   Program za vsako sezono preveri, ali je število tekem enako
   `klubi × (klubi − 1)`, saj vsak klub z vsakim igra doma in v gosteh.
3. **Čiščenje in zapis v CSV** (`shrani_podatke.py`): izluščeni podatki se
   s knjižnico pandas pretvorijo v tabeli, uredijo (vrstni red in tipi
   stolpcev, datumi, urejanje po sezoni oziroma datumu), odstranijo se
   morebitne podvojene vrstice in napačna povprečja gledalcev z lestvic
   (glej [opombo](#opomba-odstranjena-povprečja-gledalcev)), nato se tabeli
   zapišeta v mapo `podatki/`:
   - `podatki/lestvice.csv` – ena vrstica za vsak klub v vsaki sezoni (686 vrstic),
   - `podatki/tekme.csv` – ena vrstica za vsako tekmo (13.166 vrstic).

   Manjkajoči podatki (npr. ura pri starih tekmah ali gledalci, ki jih FBref
   za nekatere tekme nima) ostanejo v CSV prazni.

## Podatki

Podatki so v mapi `podatki/` (na GitHubu, da analiza deluje tudi brez
ponovnega zajema).

**`tekme.csv`** – 13.166 vrstic, ena za vsako tekmo:

| stolpec | pomen |
|---|---|
| `sezona` | sezona, npr. `2023-2024` |
| `krog`, `dan`, `datum`, `ura` | krog, dan v tednu, datum in ura začetka (angleški čas) |
| `domaci`, `gostje` | domača in gostujoča ekipa |
| `goli_domaci`, `goli_gostje` | doseženi goli |
| `izid` | `D` zmaga domačih, `X` remi, `G` zmaga gostov |
| `gledalci` | število gledalcev (prazno, če podatka ni ali je bila tekma brez gledalcev) |
| `stadion`, `sodnik` | stadion in glavni sodnik |
| `opomba` | opomba FBrefa k tekmi (pri vseh tekmah prazna) |

**`lestvice.csv`** – 686 vrstic, ena za vsak klub na končni lestvici vsake sezone:

| stolpec | pomen |
|---|---|
| `sezona`, `mesto`, `klub` | sezona, končno mesto in klub |
| `tekme`, `zmage`, `remiji`, `porazi` | odigrane tekme in njihovi izidi |
| `dani_goli`, `prejeti_goli`, `gol_razlika` | goli |
| `tocke`, `tocke_na_tekmo` | točke na končni lestvici (že z morebitnimi odbitki) |
| `povprecje_gledalcev` | povprečni obisk na domačih tekmah po FBrefu (prazno, kjer ga FBref nima ali je bil napačen – glej opombo) |
| `najboljsi_strelec`, `goli_strelca` | najboljši strelec kluba in njegovi goli |
| `opomba` | npr. uvrstitev v evropska tekmovanja, izpad ali odbitek točk |

**Pravilnost podatkov.** Tekme in lestvice so zajete z dveh različnih strani
FBrefa, zato jih zvezek primerja: za vsak klub v vsaki sezoni iz tekem izračuna
točke ter dane in prejete gole. Od 686 uvrstitev se jih 680 popolnoma ujema,
šest razlik pa je pojasnjenih (štirje odbitki točk in en gol napake na lestvici
FBrefa v sezoni 1994/95).

**Znane pomanjkljivosti vira:**

- ura začetka je znana le od sezone 2014/15,
- podatki o gledalcih manjkajo za večino tekem sezone 2007/08, za 141 tekem
  sezone 2008/09 in za nekaj posameznih tekem; v sezonah 2019/20 (od 17. 6. 2020)
  in 2020/21 pa so tekme igrali brez gledalcev,
- povprečje gledalcev na lestvicah je bilo za 32 klubov napačno (glej opombo spodaj).

### Opomba: odstranjena povprečja gledalcev

Pri klubih, ki jim na FBrefu manjka podatek o gledalcih za nekaj domačih tekem,
je povprečje gledalcev na končni lestvici FBrefa napačno in pogosto večje od
kapacitete stadiona (npr. Chelsea 2007/08: 786.543 gledalcev, Manchester United
2008/09: 95.385, stadion pa sprejme okoli 76.000 gledalcev). Pri vseh ostalih
klubih se povprečje z lestvice ujema s povprečjem, izračunanim iz posameznih
tekem, na tisočinko odstotka natančno.

Zato `shrani_podatke.py` pri čiščenju za vsak klub povprečje z lestvice primerja
s povprečjem tekem z znanim obiskom. Če se razlikujeta za več kot 1 %, povprečje
odstrani (polje ostane prazno). Tako je odstranjenih **32 povprečij** (sezone
2007/08: 6, 2008/09: 20, 2009/10: 5, 2010/11: 1). Skupaj s 14 povprečji, ki jih
FBref za sezono 2007/08 sploh nima, je polje prazno pri 46 od 686 klubov.

Covidni sezoni 2019/20 in 2020/21 sta izjema: FBref tekme brez gledalcev šteje
kot 0 gledalcev, zato je povprečje nižje od povprečja tekem z gledalci, a je
pravilno in ostane v podatkih. Analiza obiska v zvezku povprečje računa iz
posameznih tekem in upošteva le klube z znanim obiskom vseh domačih tekem.

## Analiza

Analiza je v Jupyter zvezku `analiza.ipynb`, pomožne funkcije zanj
(nalaganje podatkov, izračuni, grafi) pa v `analiza_funkcije.py`.

Zvezek se začne s pregledom podatkov (opis stolpcev, število klubov, tekem in
golov po sezonah), preverjanjem pravilnosti podatkov in pregledom manjkajočih
vrednosti. Sledita dva sklopa analize, vsak razdelek pa ima vprašanje, kodo,
graf in razlago. Na koncu so sklepne ugotovitve in omejitve analize.

Sklop 1 (prednost domačega terena):

- **Zmage, remiji in porazi doma in v gosteh** – zložen stolpčni graf deležev
  izidov po sezonah.
- **Goli doma in v gosteh** – črtni graf povprečnega števila golov domačih in
  gostujočih ekip na tekmo po sezonah.
- **Prazne tribune (covid-19)** – delež zmag domačih pred covidom, med njim in
  po njem ter primerjava izidov tekem z gledalci in brez njih.
- **Število gledalcev in zmage** – delež zmag domačih po razredih števila
  gledalcev in razsevni diagram obiska in zmag doma za vsak klub v vsaki sezoni.
  Povprečni obisk se računa iz posameznih tekem, ker je povprečje na lestvici
  FBrefa za sezoni 2007/08 in 2008/09 napačno.

Sklop 2 (boj za naslov in obstanek):

- **Klubi na vrhu lestvice** – vodoraven zložen stolpčni graf števila 1., 2. in
  3. mest po klubih.
- **Klubi na dnu lestvice** – vodoraven stolpčni graf klubov, ki so največkrat
  končali na zadnjih treh mestih.
- **Točke prvaka** – črtni graf točk prvaka po sezonah.
- **Točke za obstanek** – črtni graf točk najslabšega kluba, ki je obstal v ligi
  (število izpadlih klubov se prebere iz opomb na lestvici; v sezoni 1994/95 so
  izpadli štirje).
- **Razlika med vrhom in dnom** – točke in gol razlika na tekmo prvih treh in
  zadnjih treh klubov po sezonah.

Točke iz prvih treh sezon (22 klubov, 42 tekem) so preračunane na 38 tekem,
da so primerljive z ostalimi sezonami.

## Ugotovitve

**Ali domači teren vpliva na uspeh? Da, predvsem zaradi gledalcev.**

- Domači so zmagali na **45,7 %** tekem, gostje na **28,7 %** (25,6 % remijev).
  Ekipa doma osvoji povprečno 1,63 točke na tekmo, v gosteh 1,12, in da okoli
  32 % več golov.
- Prednost se počasi manjša: remijev je manj (27,8 % → 23,2 %), zmag gostov več
  (26,5 % → 32,1 %, prvih proti zadnjim desetim sezonam), razlika v golih med
  domačimi in gosti pa je padla z 0,42 na 0,28 gola na tekmo.
- Na **440 tekmah brez gledalcev** med covidom so domači zmagali le na 38,6 %
  tekem, gostje pa na 38,9 %: prednost domačega terena je praktično izginila.
- Število gledalcev samo po sebi ni odločilno. Na tekmah z več kot 50.000 gledalci
  domači zmagajo na več kot 60 % tekem, vendar zato, ker imajo velike stadione
  močni klubi; ko klub primerjamo samega s seboj, povezave med obiskom in zmagami
  skoraj ni (korelacija 0,09).

**Kdo osvaja ligo in koliko točk je za to potrebnih?**

- Vrh je zaprt: v 34 sezonah je bilo le **sedem prvakov** (Manchester United 13,
  Manchester City 8, Chelsea 5, Arsenal 4, Liverpool 2, Blackburn in Leicester City
  po 1), pet klubov pa je osvojilo 86 % mest med prvimi tremi.
- Dno je odprto: na zadnjih treh mestih je končalo 43 različnih klubov.
- Prvak potrebuje vse več točk: povprečno 81 v prvih in 92 v zadnjih desetih
  sezonah (rekord 100, Manchester City 2017/18).
- Za obstanek je bilo povprečno dovolj 38 točk; »40 točk« je bilo potrebnih le v
  11 od 34 sezon, trije klubi pa so izpadli celo s 40 ali več točkami.
- Liga je vse bolj neenakomerna: razlika med prvimi tremi in zadnjimi tremi klubi
  je zrasla z 1,09 na 1,48 točke na tekmo.

## Navodila za uporabo

Potrebuješ Python 3 in knjižnice iz `requirements.txt`:

```
py -m pip install -r requirements.txt
```

CSV datoteke so že v repozitoriju, zato lahko analizo odpreš takoj
(korak 3). Za ponovni zajem podatkov najprej ročno shraniš strani (to je
treba narediti le enkrat), nato pa vse ostalo naredi en ukaz.

**1. Shranjevanje strani:**

```
py prenos_strani.py          # odpira strani eno za drugo (68 strani)
py prenos_strani.py preveri  # izpiše, katere strani še manjkajo
```

Ko se stran odpre v brskalniku, jo shrani s **Ctrl+S** kot
»Spletna stran, samo HTML« v mapo Prenosi in v terminalu pritisni Enter.
Če vpišeš `k`, se delo prekine in se ob naslednjem zagonu nadaljuje.

**2. Priprava podatkov z enim ukazom:**

```
py main.py
```

`main.py` preveri, ali so shranjene vse strani (če katera manjka, to izpiše in
se ustavi, ne da bi spremenil obstoječe CSV), nato izlušči podatke in zapiše
`podatki/lestvice.csv` ter `podatki/tekme.csv`.

Posamezne korake lahko zaženeš tudi ločeno:

```
py izlusci_podatke.py        # izpiše povzetek lestvic in tekem po sezonah
```

```
py shrani_podatke.py         # ustvari podatki/lestvice.csv in podatki/tekme.csv
```

**3. Analiza:** odpri `analiza.ipynb` v VS Code ali z ukazom
`py -m jupyter notebook analiza.ipynb` in zaženi vse celice
(*Restart* in *Run All*). Zvezek bere podatke iz mape `podatki/`.

## Struktura projekta

```
projekt-uvp/
├── README.md
├── requirements.txt
├── .gitignore
├── prenos_strani.py     # pomoč pri shranjevanju HTML strani
├── izlusci_podatke.py   # izluščanje podatkov iz strani z BeautifulSoup
├── shrani_podatke.py    # čiščenje podatkov in zapis v CSV
├── main.py              # preveri strani, izlušči podatke in zapiše CSV
├── analiza_funkcije.py  # pomožne funkcije za analizo
├── analiza.ipynb        # analiza in predstavitev z grafi
├── podatki/
│   ├── lestvice.csv     # končne lestvice vseh sezon
│   └── tekme.csv        # vse tekme vseh sezon
└── html_strani/         # prenesene strani (ni na GitHubu)
    ├── lestvice/
    └── tekme/
```
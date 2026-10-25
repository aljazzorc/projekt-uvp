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
   vsebuje tabele, in jo premakne v mapo `html_strani/` (ta ni na GitHubu).
   Že shranjene strani se ob ponovnem zagonu preskočijo, zato lahko delo
   kadarkoli prekineš.
2. **Izluščanje podatkov** (`izlusci_podatke.py`): iz shranjenih strani se z
   BeautifulSoup izluščijo podatki. Tabele program poišče po atributu `id`,
   posamezne podatke v vrsticah pa po atributu `data-stat`. Ker FBref nekatere
   tabele skrije v HTML komentarje, se oznake komentarjev pred branjem odstranijo.
   Zaenkrat se izluščijo končne lestvice vseh sezon (mesto, klub, zmage, remiji,
   porazi, goli, točke, povprečje gledalcev, najboljši strelec in opomba, npr.
   izpad ali odbitek točk); podatki o posameznih tekmah so v pripravi.
3. **Zapis v CSV** *(v pripravi)*: podatki se zapišejo v mapo `podatki/`.

## Analiza

*V pripravi.* Analiza bo v Jupyter zvezku `analiza.ipynb`.

## Ugotovitve

*V pripravi.*

## Navodila za uporabo

Potrebuješ Python 3 in knjižnice iz `requirements.txt`:

```
py -m pip install -r requirements.txt
```

Shranjevanje strani:

```
py prenos_strani.py          # odpira strani eno za drugo (68 strani)
py prenos_strani.py preveri  # izpiše, katere strani še manjkajo
```

Ko se stran odpre v brskalniku, jo shrani s **Ctrl+S** kot
»Spletna stran, samo HTML« v mapo Prenosi in v terminalu pritisni Enter.
Če vpišeš `k`, se delo prekine in se ob naslednjem zagonu nadaljuje.

Izluščanje podatkov iz shranjenih strani:

```
py izlusci_podatke.py        # izpiše število klubov po sezonah in zadnjo lestvico
```

## Struktura projekta

```
projekt-uvp/
├── README.md
├── requirements.txt
├── .gitignore
├── prenos_strani.py     # pomoč pri shranjevanju HTML strani
├── izlusci_podatke.py   # izluščanje podatkov iz strani z BeautifulSoup
└── html_strani/         # prenesene strani (ni na GitHubu)
    ├── lestvice/
    └── tekme/
```
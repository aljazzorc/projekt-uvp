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

1. **Prenos strani** (`prenos_strani.py`): za vsako sezono se preneseta stran
   s končno lestvico in stran z vsemi tekmami. Strani se shranijo v mapo
   `html_strani/`, ki ni na GitHubu. Že prenesene strani se ob ponovnem zagonu
   preskočijo. Med zahtevki je 7 sekund premora, ker FBref blokira uporabnike
   z več kot 10 zahtevki na minuto.
2. **Izluščanje podatkov** *(v pripravi)*: iz shranjenih strani se z
   BeautifulSoup izluščijo podatki in zapišejo v CSV datoteke v mapi `podatki/`.

## Analiza

*V pripravi.* Analiza bo v Jupyter zvezku `analiza.ipynb`.

## Ugotovitve

*V pripravi.*

## Navodila za uporabo

Potrebuješ Python 3 in knjižnice iz `requirements.txt`:

```
py -m pip install -r requirements.txt
```

Prenos strani:

```
py prenos_strani.py         # vse sezone (približno 8 minut)
py prenos_strani.py test    # samo sezona 2023-2024
```

## Struktura projekta

```
projekt-uvp/
├── README.md
├── requirements.txt
├── .gitignore
├── prenos_strani.py     # prenos in shranjevanje HTML strani
└── html_strani/         # prenesene strani (ni na GitHubu)
    ├── lestvice/
    └── tekme/
```

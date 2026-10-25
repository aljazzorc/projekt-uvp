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
   morebitne podvojene vrstice, nato se tabeli zapišeta v mapo `podatki/`:
   - `podatki/lestvice.csv` – ena vrstica za vsak klub v vsaki sezoni (686 vrstic),
   - `podatki/tekme.csv` – ena vrstica za vsako tekmo (13.166 vrstic).

   Manjkajoči podatki (npr. ura pri starih tekmah ali gledalci, ki jih FBref
   za nekatere tekme nima) ostanejo v CSV prazni.

## Analiza

Analiza je v Jupyter zvezku `analiza.ipynb`, pomožne funkcije zanj
(nalaganje podatkov, izračuni, grafi) pa v `analiza_funkcije.py`.

Zvezek se začne s pregledom podatkov: opis stolpcev, število klubov, tekem in
golov po sezonah ter manjkajoči podatki. Ura začetka je znana le od sezone
2014/15, podatki o gledalcih pa manjkajo zaradi covida-19 (tekme brez
gledalcev v sezonah 2019/20 in 2020/21) in ker jih FBref za nekatere
sezone nima (predvsem 2007/08 in 2008/09). Analiza to upošteva.

Sklop 1 (prednost domačega terena):

- **Zmage, remiji in porazi doma in v gosteh** – zložen stolpčni graf deležev
  izidov po sezonah.
- **Goli doma in v gosteh** – črtni graf povprečnega števila golov domačih in
  gostujočih ekip na tekmo po sezonah.

*Ostali razdelki so v pripravi.*

## Ugotovitve

*V pripravi.*

## Navodila za uporabo

Potrebuješ Python 3 in knjižnice iz `requirements.txt`:

```
py -m pip install -r requirements.txt
```

Postopek ima dva koraka. Najprej ročno shraniš strani (to je treba narediti
le enkrat), nato pa vse ostalo naredi en ukaz.

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
`py -m jupyter notebook analiza.ipynb` in zaženi vse celice.

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
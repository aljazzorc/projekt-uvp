"""
Prenos HTML strani s FBref.com za Premier League (sezone 1992/93–2025/26).

Za vsako sezono potrebujemo dve strani:
  - končno lestvico sezone,
  - seznam vseh tekem sezone (rezultati, gledalci, sodniki …).

FBref je zaščiten pred roboti (Cloudflare) in programom vrača kodo 403,
zato strani shrani uporabnik v svojem brskalniku. Program mu pri tem pomaga:
  1. stran sam odpre v brskalniku,
  2. uporabnik jo shrani s Ctrl+S (privzeto v mapo Prenosi/Downloads),
  3. program shranjeno datoteko poišče, preveri, da je prava stran,
     ter jo premakne in preimenuje v mapo html_strani/.

Že shranjene strani se preskočijo, zato lahko delo kadarkoli prekineš
in ga kasneje nadaljuješ. Podatki se iz strani izluščijo šele kasneje
(izlusci_podatke.py).

Zagon:
    py prenos_strani.py           # vse sezone (68 strani)
    py prenos_strani.py test      # samo sezona 2023-2024 (2 strani)
    py prenos_strani.py preveri   # samo preveri, katere strani že imamo
"""

import os
import shutil
import sys
import time
import webbrowser


# ============================================================================
# NASTAVITVE
# ============================================================================

# Osnovni naslov za Premier League na FBrefu (oznaka tekmovanja je 9).
OSNOVNI_URL = "https://fbref.com/en/comps/9"
IME_LIGE = "Premier-League"

# Prva in zadnja sezona: leto označuje začetek sezone (1992 → 1992-1993).
ZACETNO_LETO = 1992
KONCNO_LETO = 2025

# Sezona, ki se obdela v testnem načinu.
TESTNO_LETO = 2023

# Mape, kamor shranjujemo strani (mapa html_strani/ je v .gitignore).
MAPA_HTML = "html_strani"
MAPA_LESTVICE = os.path.join(MAPA_HTML, "lestvice")
MAPA_TEKME = os.path.join(MAPA_HTML, "tekme")

# Privzeta mapa za prenose (v slovenskem Windowsu se prikaže kot "Prenosi").
# Če je preusmerjena drugam, pravo pot poišče funkcija mapa_prenosov().
PRIVZETA_MAPA_PRENOSI = os.path.join(os.path.expanduser("~"), "Downloads")

# Prava stran FBrefa je velika nekaj sto kB; manjša datoteka je skoraj
# zagotovo stran z napako ali preverjanjem.
NAJMANJSA_VELIKOST_KB = 50

# Naslovi strani, po katerih prepoznamo stran preverjanja (Cloudflare).
# Pozor: besedila "challenge-platform" ne smemo iskati, ker ga Cloudflare
# vstavi tudi v prave strani FBrefa, ko je preverjanje že opravljeno.
ZNAKI_ZASCITE = ["<title>Just a moment", "Attention Required! | Cloudflare"]

# Koliko sekund po pritisku na Enter še čakamo, da brskalnik konča shranjevanje.
CAKANJE_NA_DATOTEKO = 10

# Možni izidi za eno stran.
PRENESENO = "PRENESENO"
PRESKOCENO = "PRESKOCENO"
NAPAKA = "NAPAKA"
MANJKA = "MANJKA"


# ============================================================================
# POMOŽNE FUNKCIJE: OZNAKE, NASLOVI IN POTI
# ============================================================================

def oznaka_sezone(leto):
    """
    Iz začetnega leta sestavi oznako sezone, kot jo uporablja FBref.

    Sprejme: leto (int), v katerem se sezona začne.
    Vrne: niz z oznako sezone.
    Primer: oznaka_sezone(2023) → "2023-2024"
    """
    return f"{leto}-{leto + 1}"


def url_lestvice(sezona):
    """
    Vrne spletni naslov strani s končno lestvico sezone.

    Sprejme: oznako sezone (npr. "2023-2024").
    Vrne: niz z URL-jem.
    Primer: url_lestvice("2023-2024")
        → "https://fbref.com/en/comps/9/2023-2024/2023-2024-Premier-League-Stats"
    """
    return f"{OSNOVNI_URL}/{sezona}/{sezona}-{IME_LIGE}-Stats"


def url_tekem(sezona):
    """
    Vrne spletni naslov strani z vsemi tekmami sezone.

    Sprejme: oznako sezone (npr. "2023-2024").
    Vrne: niz z URL-jem.
    Primer: url_tekem("2023-2024")
        → "https://fbref.com/en/comps/9/2023-2024/schedule/
           2023-2024-Premier-League-Scores-and-Fixtures"
    """
    return f"{OSNOVNI_URL}/{sezona}/schedule/{sezona}-{IME_LIGE}-Scores-and-Fixtures"


def pot_lestvice(sezona):
    """
    Vrne pot do datoteke, v katero shranimo lestvico sezone.

    Primer: pot_lestvice("2023-2024") → "html_strani/lestvice/lestvica_2023-2024.html"
    """
    return os.path.join(MAPA_LESTVICE, f"lestvica_{sezona}.html")


def pot_tekem(sezona):
    """
    Vrne pot do datoteke, v katero shranimo tekme sezone.

    Primer: pot_tekem("2023-2024") → "html_strani/tekme/tekme_2023-2024.html"
    """
    return os.path.join(MAPA_TEKME, f"tekme_{sezona}.html")


def seznam_strani(od_leta, do_leta):
    """
    Sestavi seznam vseh strani, ki jih potrebujemo za izbrane sezone.

    Sprejme: začetno in končno leto (int).
    Vrne: seznam trojic (opis, url, pot).
    Primer: seznam_strani(2023, 2023)
        → [("2023-2024 lestvica", "https://...", "html_strani/lestvice/..."),
           ("2023-2024 tekme", "https://...", "html_strani/tekme/...")]
    """
    strani = []
    for leto in range(od_leta, do_leta + 1):
        sezona = oznaka_sezone(leto)
        strani.append((f"{sezona} lestvica", url_lestvice(sezona), pot_lestvice(sezona)))
        strani.append((f"{sezona} tekme", url_tekem(sezona), pot_tekem(sezona)))
    return strani


def mapa_prenosov():
    """
    Vrne pot do mape, kamor brskalnik shranjuje prenose.

    V Windowsu je lahko mapa Prenosi preusmerjena (npr. na drug disk ali
    v OneDrive), zato pravo pot preberemo iz registra. Če to ne uspe
    (npr. na drugem operacijskem sistemu), vrnemo privzeto pot.

    Vrne: niz s potjo do mape.
    Primer: mapa_prenosov() → "C:\\Users\\aljo\\Downloads"
    """
    try:
        import winreg
        kljuc = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders",
        )
        # Ta oznaka v registru pomeni mapo Prenosi (Downloads).
        vrednost, _ = winreg.QueryValueEx(kljuc, "{374DE290-123F-4565-9164-39C4925E467B}")
        return os.path.expandvars(vrednost)
    except (ImportError, OSError):
        return PRIVZETA_MAPA_PRENOSI


def ustvari_mape():
    """
    Ustvari mape za shranjene strani, če še ne obstajajo.

    Ne sprejme ničesar in ne vrne ničesar.
    """
    # exist_ok=True: če mapa že obstaja, to ni napaka.
    os.makedirs(MAPA_LESTVICE, exist_ok=True)
    os.makedirs(MAPA_TEKME, exist_ok=True)


# ============================================================================
# PREVERJANJE SHRANJENIH STRANI
# ============================================================================

def je_zascita_pred_roboti(besedilo):
    """
    Preveri, ali je stran stran zaščite pred roboti (Cloudflare).

    Sprejme: besedilo (HTML) strani.
    Vrne: True, če stran vsebuje katerega od znakov iz ZNAKI_ZASCITE, sicer False.
    Primer: je_zascita_pred_roboti("<title>Just a moment...</title>") → True
    """
    return any(znak in besedilo for znak in ZNAKI_ZASCITE)


def razlog_neveljavnosti(pot):
    """
    Preveri, ali je datoteka prava stran FBrefa s tabelami.

    Sprejme: pot do datoteke.
    Vrne: None, če je datoteka v redu, sicer niz z razlogom, zakaj ni.
    Primer: razlog_neveljavnosti("html_strani/tekme/tekme_2023-2024.html") → None
    """
    if not os.path.exists(pot):
        return "datoteka ne obstaja"

    velikost_kb = os.path.getsize(pot) // 1000
    if velikost_kb < NAJMANJSA_VELIKOST_KB:
        return f"datoteka je premajhna ({velikost_kb} kB)"

    # errors="replace": nenavaden znak v datoteki ne sme zrušiti programa.
    with open(pot, encoding="utf-8", errors="replace") as datoteka:
        besedilo = datoteka.read()

    # Najprej preverimo tabele: prava stran FBrefa jih ima veliko.
    if "<table" in besedilo:
        return None
    if je_zascita_pred_roboti(besedilo):
        return "shranjena je stran preverjanja (Cloudflare), ne stran FBrefa"
    return "v datoteki ni nobene tabele"


# ============================================================================
# ISKANJE IN PREMIK SHRANJENE DATOTEKE
# ============================================================================

def najnovejsa_html_datoteka(mapa, od_casa):
    """
    Poišče zadnjo HTML datoteko, ki je bila v mapi shranjena po danem času.

    Sprejme:
        mapa    – mapa, v kateri iščemo (npr. Prenosi),
        od_casa – čas (time.time()), ko smo stran odprli.
    Vrne: pot do najnovejše takšne datoteke ali None, če je ni.
    Primer: najnovejsa_html_datoteka("C:/Users/aljo/Downloads", 1761230000.0)
        → "C:/Users/aljo/Downloads/2023-2024 Premier League Stats _ FBref.com.html"
    """
    if not os.path.isdir(mapa):
        return None

    kandidati = []
    for ime in os.listdir(mapa):
        pot = os.path.join(mapa, ime)
        # Upoštevamo le .html/.htm datoteke, shranjene po odprtju strani.
        if ime.lower().endswith((".html", ".htm")) and os.path.getmtime(pot) >= od_casa:
            kandidati.append(pot)

    if not kandidati:
        return None
    # Če je novih datotek več, vzamemo zadnjo shranjeno.
    return max(kandidati, key=os.path.getmtime)


def premakni_datoteko(izvor, cilj):
    """
    Premakne shranjeno datoteko iz mape Prenosi v mapo projekta
    in jo pri tem preimenuje.

    Sprejme: pot do shranjene datoteke in ciljno pot.
    Ne vrne ničesar.
    """
    shutil.move(izvor, cilj)


# ============================================================================
# SHRANJEVANJE STRANI
# ============================================================================

def pocakaj_na_datoteko(mapa, od_casa):
    """
    Nekaj sekund čaka, da se v mapi pojavi nova HTML datoteka
    (brskalnik jo morda še shranjuje).

    Sprejme: mapo in čas, ko smo stran odprli.
    Vrne: pot do najnovejše nove HTML datoteke ali None.
    """
    for _ in range(CAKANJE_NA_DATOTEKO):
        shranjena = najnovejsa_html_datoteka(mapa, od_casa)
        if shranjena is not None:
            return shranjena
        time.sleep(1)
    return None


def shrani_stran(opis, url, pot, mapa):
    """
    Odpre stran v brskalniku, počaka, da jo uporabnik shrani, nato datoteko
    poišče v mapi Prenosi, jo premakne na pravo mesto in preveri.

    Sprejme:
        opis – opis strani za izpis (npr. "2023-2024 tekme"),
        url  – naslov strani,
        pot  – kam naj se datoteka shrani v projektu,
        mapa – mapa, kamor brskalnik shranjuje prenose.
    Vrne enega od nizov:
        PRESKOCENO – veljavna datoteka že obstaja,
        PRENESENO  – stran je shranjena in preverjena,
        NAPAKA     – datoteke ni ali ni prava stran,
        None       – uporabnik je prekinil delo (vpisal "k").
    """
    # Že shranjene in veljavne strani preskočimo.
    if razlog_neveljavnosti(pot) is None:
        return PRESKOCENO

    # Čas zapomnimo, da v mapi Prenosi najdemo le na novo shranjene datoteke.
    zacetek = time.time()
    print(f"\n{opis}: odpiram {url}")
    webbrowser.open(url)

    odgovor = input("  Shrani stran s Ctrl+S (\"samo HTML\"), nato pritisni Enter "
                    "(ali vpiši k za konec): ")
    if odgovor.strip().lower() == "k":
        return None

    shranjena = pocakaj_na_datoteko(mapa, zacetek)
    if shranjena is None:
        print(f"  V mapi {mapa} ni nove HTML datoteke.")
        print("  Preveri, kam je brskalnik shranil stran, in jo shrani v to mapo.")
        return NAPAKA
    print(f"  Najdena datoteka: {shranjena}")

    # Datoteko preverimo, preden jo premaknemo; neveljavno pustimo, kjer je,
    # da jo lahko pogledaš.
    razlog = razlog_neveljavnosti(shranjena)
    if razlog is not None:
        print(f"  Datoteka ni v redu: {razlog}.")
        return NAPAKA

    # Morebitno staro, neveljavno datoteko nadomestimo z novo.
    if os.path.exists(pot):
        os.remove(pot)
    premakni_datoteko(shranjena, pot)

    print(f"  Shranjeno v {pot}")
    return PRENESENO


def shrani_sezone(od_leta, do_leta):
    """
    Za vse sezone od od_leta do vključno do_leta poskrbi, da sta lestvica
    in seznam tekem shranjena v mapi html_strani/.

    Sprejme: začetno in končno leto (int).
    Vrne: slovar s številom strani za vsak izid.
    Primer: shrani_sezone(2023, 2023)
        → {"PRENESENO": 2, "PRESKOCENO": 0, "NAPAKA": 0}
    """
    ustvari_mape()
    stevec = {PRENESENO: 0, PRESKOCENO: 0, NAPAKA: 0}
    mapa = mapa_prenosov()
    print(f"Strani shranjuj v mapo: {mapa}")

    for opis, url, pot in seznam_strani(od_leta, do_leta):
        izid = shrani_stran(opis, url, pot, mapa)
        if izid is None:
            print("\nDelo je prekinjeno. Ob ponovnem zagonu se nadaljuje, kjer si ostal.")
            break
        stevec[izid] += 1
        if izid == PRESKOCENO:
            print(f"{opis:<20} {PRESKOCENO}")

    return stevec


def preveri_sezone(od_leta, do_leta):
    """
    Preveri vse že shranjene strani, ne da bi karkoli odpiral.

    Sprejme: začetno in končno leto (int).
    Vrne: slovar s številom veljavnih in manjkajočih strani.
    Primer: preveri_sezone(1992, 2025) → {"PRESKOCENO": 68, "MANJKA": 0}
    """
    stevec = {PRESKOCENO: 0, MANJKA: 0}
    for opis, _, pot in seznam_strani(od_leta, do_leta):
        razlog = razlog_neveljavnosti(pot)
        if razlog is None:
            stevec[PRESKOCENO] += 1
        else:
            stevec[MANJKA] += 1
            print(f"{opis:<20} {MANJKA} ({razlog})")
    return stevec


def izpisi_povzetek(stevec):
    """
    Izpiše povzetek: koliko strani je v posameznem stanju.

    Sprejme: slovar, ki ga vrne shrani_sezone ali preveri_sezone.
    """
    print("\nPovzetek:")
    for izid, stevilo in stevec.items():
        print(f"  {izid:<11} {stevilo}")


# ============================================================================
# GLAVNI PROGRAM
# ============================================================================

if __name__ == "__main__":
    nacin = sys.argv[1] if len(sys.argv) > 1 else ""

    if nacin == "test":
        print(f"Testni način: samo sezona {oznaka_sezone(TESTNO_LETO)}.")
        rezultat = shrani_sezone(TESTNO_LETO, TESTNO_LETO)
    elif nacin == "preveri":
        print("Preverjam shranjene strani.\n")
        rezultat = preveri_sezone(ZACETNO_LETO, KONCNO_LETO)
    else:
        print(f"Sezone od {oznaka_sezone(ZACETNO_LETO)} do {oznaka_sezone(KONCNO_LETO)}.")
        rezultat = shrani_sezone(ZACETNO_LETO, KONCNO_LETO)

    izpisi_povzetek(rezultat)
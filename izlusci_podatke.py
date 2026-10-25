"""
Izluščanje podatkov iz shranjenih HTML strani FBrefa z BeautifulSoup.

Strani shrani prenos_strani.py v mapo html_strani/. Ta datoteka jih le
prebere (spleta ne uporablja) in iz njih sestavi sezname slovarjev:
  - lestvice: en slovar za vsak klub v vsaki sezoni,
  - tekme: en slovar za vsako odigrano tekmo.

Tabele iščemo po atributu id, celice v vrsticah pa po atributu data-stat,
ki pove, kateri podatek je v celici (npr. data-stat="points" so točke).

Zagon (izpiše povzetek lestvic in tekem za vse sezone):
    py izlusci_podatke.py
"""

import os

from bs4 import BeautifulSoup

from prenos_strani import (
    KONCNO_LETO, ZACETNO_LETO, oznaka_sezone, pot_lestvice, pot_tekem,
)


# ============================================================================
# NASTAVITVE
# ============================================================================

# Oznaka tekmovanja Premier League na FBrefu; je del imena tabel.
OZNAKA_LIGE = "9"

# Kateri data-stat na FBrefu ustreza kateremu stolpcu v naših podatkih.
# Imena data-stat so prebrana iz shranjenih strani (sezoni 1992-1993 in 2023-2024).
STOLPCI_LESTVICE = {
    "rank": "mesto",
    "team": "klub",
    "games": "tekme",
    "wins": "zmage",
    "ties": "remiji",
    "losses": "porazi",
    "goals_for": "dani_goli",
    "goals_against": "prejeti_goli",
    "goal_diff": "gol_razlika",
    "points": "tocke",
    "points_avg": "tocke_na_tekmo",
    "attendance_per_g": "povprecje_gledalcev",
    "top_team_scorers": "najboljsi_strelec",
    "notes": "opomba",
}

# Stolpci, ki so cela števila, in stolpci, ki so decimalna števila.
CELOSTEVILSKI_STOLPCI = [
    "mesto", "tekme", "zmage", "remiji", "porazi", "dani_goli",
    "prejeti_goli", "gol_razlika", "tocke", "povprecje_gledalcev",
]
DECIMALNI_STOLPCI = ["tocke_na_tekmo"]

# Kateri data-stat na strani s tekmami ustreza kateremu stolpcu.
# Rezultat (data-stat="score") obdelamo posebej, ker ga razdelimo na dva stolpca.
STOLPCI_TEKEM = {
    "gameweek": "krog",
    "dayofweek": "dan",
    "date": "datum",
    "start_time": "ura",
    "home_team": "domaci",
    "away_team": "gostje",
    "attendance": "gledalci",
    "venue": "stadion",
    "referee": "sodnik",
    "notes": "opomba",
}

# Razredi vrstic, ki niso tekme: prazne vmesne vrstice in ponovljene glave tabele.
RAZREDI_VMESNIH_VRSTIC = ["spacer", "thead"]

# Znak med goli domačih in gostov. FBref uporablja pomišljaj (en dash),
# ki je drug znak kot navaden vezaj "-".
POMISLJAJ = "–"

# Oznake izida tekme: zmaga domačih, remi, zmaga gostov.
ZMAGA_DOMACIH = "D"
REMI = "X"
ZMAGA_GOSTOV = "G"


# ============================================================================
# POMOŽNE FUNKCIJE: BRANJE HTML IN CELIC
# ============================================================================

def nalozi_html(pot):
    """
    Prebere shranjeno HTML datoteko in jo pripravi za iskanje z BeautifulSoup.

    FBref nekatere tabele skrije v HTML komentarje (<!-- ... -->), ki jih
    BeautifulSoup ne razčleni kot tabele. Zato oznake komentarjev najprej
    odstranimo, da postanejo skrite tabele navadne tabele.

    Sprejme: pot do datoteke.
    Vrne: objekt BeautifulSoup.
    Primer: nalozi_html("html_strani/lestvice/lestvica_2023-2024.html")
        → BeautifulSoup z vsemi tabelami strani
    """
    with open(pot, encoding="utf-8", errors="replace") as datoteka:
        besedilo = datoteka.read()
    besedilo = besedilo.replace("<!--", "").replace("-->", "")
    return BeautifulSoup(besedilo, "html.parser")


def preberi_celico(vrstica, data_stat):
    """
    Varno prebere besedilo celice z danim atributom data-stat.

    Če celice ni ali je prazna, vrne None, zato manjkajoč podatek
    ne zruši programa.

    Sprejme: vrstico tabele (<tr>) in ime atributa data-stat.
    Vrne: besedilo celice brez presledkov na robovih ali None.
    Primer: preberi_celico(vrstica, "team") → "Manchester City"
            preberi_celico(vrstica, "neobstojec") → None
    """
    celica = vrstica.find(["th", "td"], attrs={"data-stat": data_stat})
    if celica is None:
        return None
    # separator=" ": besedila iz več delov celice (npr. povezav) ločimo s presledkom.
    besedilo = celica.get_text(" ", strip=True)
    return besedilo if besedilo else None


def v_stevilo(besedilo):
    """
    Pretvori besedilo s celim številom v int.

    Odstrani vejice, ki ločujejo tisočice. Predznak (+ ali -) Python razume sam.

    Sprejme: niz ali None.
    Vrne: int ali None, če besedila ni ali ni število.
    Primer: v_stevilo("73,988") → 73988
            v_stevilo("+62") → 62
            v_stevilo(None) → None
    """
    if besedilo is None:
        return None
    try:
        return int(besedilo.replace(",", ""))
    except ValueError:
        return None


def v_decimalno(besedilo):
    """
    Pretvori besedilo z decimalnim številom v float.

    Sprejme: niz ali None.
    Vrne: float ali None, če besedila ni ali ni število.
    Primer: v_decimalno("2.39") → 2.39
            v_decimalno("") → None
    """
    if not besedilo:
        return None
    try:
        return float(besedilo.replace(",", ""))
    except ValueError:
        return None


def razbij_strelca(besedilo):
    """
    Razdeli besedilo o najboljšem strelcu na ime in število golov.

    FBref ga zapiše kot "Ime-goli"; pri več strelcih z enakim številom
    golov so imena ločena z vejico. Ker imajo nekatera imena v sebi
    vezaj (npr. "Alexander-Arnold"), razdelimo le pri zadnjem vezaju.

    Sprejme: niz ali None.
    Vrne: par (ime, goli); če podatka ni, (None, None).
    Primer: razbij_strelca("Erling Haaland-27") → ("Erling Haaland", 27)
            razbij_strelca("Oliver McBurnie,Ben Brereton Díaz-6")
                → ("Oliver McBurnie, Ben Brereton Díaz", 6)
    """
    if not besedilo or "-" not in besedilo:
        return besedilo, None
    ime, goli = besedilo.rsplit("-", 1)
    # Za vejico dodamo presledek, da je seznam imen lepše berljiv.
    ime = ", ".join(del_imena.strip() for del_imena in ime.split(","))
    return ime, v_stevilo(goli)


# ============================================================================
# IZLUŠČANJE LESTVICE
# ============================================================================

def id_tabele_lestvice(sezona):
    """
    Vrne id tabele s končno lestvico sezone.

    Sprejme: oznako sezone (npr. "2023-2024").
    Vrne: niz z id-jem tabele.
    Primer: id_tabele_lestvice("2023-2024") → "results2023-202491_overall"
    """
    return f"results{sezona}{OZNAKA_LIGE}1_overall"


def pretvori_vrstico_lestvice(vrstica, sezona):
    """
    Iz ene vrstice lestvice sestavi slovar s podatki o klubu.

    Sprejme: vrstico tabele (<tr>) in oznako sezone.
    Vrne: slovar s stolpci iz STOLPCI_LESTVICE ter sezono in goli_strelca.
    Primer: pretvori_vrstico_lestvice(vrstica, "2023-2024")
        → {"sezona": "2023-2024", "mesto": 1, "klub": "Manchester City",
           "tekme": 38, ..., "tocke": 91, "tocke_na_tekmo": 2.39,
           "povprecje_gledalcev": 53012,
           "najboljsi_strelec": "Erling Haaland", "goli_strelca": 27,
           "opomba": "→ Champions League via league finish"}
    """
    klub = {"sezona": sezona}

    # Najprej preberemo vse celice kot besedilo …
    for data_stat, stolpec in STOLPCI_LESTVICE.items():
        klub[stolpec] = preberi_celico(vrstica, data_stat)

    # … nato števila pretvorimo v pravi tip.
    for stolpec in CELOSTEVILSKI_STOLPCI:
        klub[stolpec] = v_stevilo(klub[stolpec])
    for stolpec in DECIMALNI_STOLPCI:
        klub[stolpec] = v_decimalno(klub[stolpec])

    # Strelca razdelimo na ime in število golov.
    klub["najboljsi_strelec"], klub["goli_strelca"] = razbij_strelca(klub["najboljsi_strelec"])
    return klub


def izlusci_lestvico(soup, sezona):
    """
    Iz strani z lestvico izlušči podatke o vseh klubih sezone.

    Sprejme: BeautifulSoup strani (iz nalozi_html) in oznako sezone.
    Vrne: seznam slovarjev, en za vsak klub (po vrsti od 1. mesta navzdol).
          Če tabele ni, vrne prazen seznam in izpiše opozorilo.
    Primer: izlusci_lestvico(soup, "2023-2024") → [{...}, {...}, ...]  (20 klubov)
    """
    tabela = soup.find("table", id=id_tabele_lestvice(sezona))
    if tabela is None:
        print(f"OPOZORILO: v sezoni {sezona} ni tabele {id_tabele_lestvice(sezona)}.")
        return []

    klubi = []
    # Podatki so v telesu tabele (<tbody>); glava s stolpci je v <thead>.
    for vrstica in tabela.find("tbody").find_all("tr"):
        # Vrstice brez imena kluba (npr. vmesne naslovne vrstice) preskočimo.
        if preberi_celico(vrstica, "team") is None:
            continue
        klubi.append(pretvori_vrstico_lestvice(vrstica, sezona))
    return klubi


def izlusci_vse_lestvice(od_leta=ZACETNO_LETO, do_leta=KONCNO_LETO):
    """
    Izlušči lestvice vseh sezon iz shranjenih datotek v html_strani/lestvice/.

    Sezone, za katere datoteke ni, preskoči in izpiše opozorilo.

    Sprejme: začetno in končno leto (privzeto vse sezone projekta).
    Vrne: en sam seznam slovarjev z vsemi klubi vseh sezon.
    Primer: izlusci_vse_lestvice(2023, 2023) → seznam 20 slovarjev
    """
    vse = []
    for leto in range(od_leta, do_leta + 1):
        sezona = oznaka_sezone(leto)
        pot = pot_lestvice(sezona)
        if not os.path.exists(pot):
            print(f"OPOZORILO: datoteka {pot} ne obstaja, sezono preskočim.")
            continue
        vse.extend(izlusci_lestvico(nalozi_html(pot), sezona))
    return vse


# ============================================================================
# POMOŽNE FUNKCIJE ZA TEKME
# ============================================================================

def razbij_rezultat(besedilo):
    """
    Razdeli rezultat tekme na gole domačih in gole gostov.

    Sprejme: niz z rezultatom (z pomišljajem "–") ali None.
    Vrne: par (goli_domaci, goli_gostje) kot int; če rezultata ni ali ga
          ne razumemo, (None, None).
    Primer: razbij_rezultat("2–1") → (2, 1)
            razbij_rezultat(None) → (None, None)
    """
    if not besedilo or POMISLJAJ not in besedilo:
        return None, None
    domaci, gostje = besedilo.split(POMISLJAJ, 1)
    return v_stevilo(domaci.strip()), v_stevilo(gostje.strip())


def ocisti_uro(besedilo):
    """
    Iz zapisa ure obdrži le angleški čas začetka tekme.

    FBref za angleškim časom v oklepaju doda še čas v časovnem pasu
    brskalnika, s katerim je bila stran shranjena (pri nas +1 ura).

    Sprejme: niz ali None.
    Vrne: niz z uro (npr. "20:00") ali None.
    Primer: ocisti_uro("20:00(21:00)") → "20:00"
            ocisti_uro(None) → None
    """
    if not besedilo:
        return None
    return besedilo.split("(")[0].strip()


def doloci_izid(goli_domaci, goli_gostje):
    """
    Iz golov določi izid tekme.

    Sprejme: gole domačih in gole gostov (int).
    Vrne: ZMAGA_DOMACIH ("D"), REMI ("X") ali ZMAGA_GOSTOV ("G").
    Primer: doloci_izid(2, 1) → "D"
            doloci_izid(0, 0) → "X"
            doloci_izid(0, 3) → "G"
    """
    if goli_domaci > goli_gostje:
        return ZMAGA_DOMACIH
    if goli_domaci < goli_gostje:
        return ZMAGA_GOSTOV
    return REMI


def je_vmesna_vrstica(vrstica):
    """
    Preveri, ali vrstica tabele tekem ni tekma (prazna vmesna vrstica ali
    ponovljena glava tabele).

    Sprejme: vrstico tabele (<tr>).
    Vrne: True, če ima vrstica katerega od razredov iz RAZREDI_VMESNIH_VRSTIC
          ali nima domače ekipe, sicer False.
    Primer: je_vmesna_vrstica(<tr class="spacer partial_table result_all">) → True
    """
    razredi = vrstica.get("class", [])
    if any(razred in razredi for razred in RAZREDI_VMESNIH_VRSTIC):
        return True
    return preberi_celico(vrstica, "home_team") is None


# ============================================================================
# IZLUŠČANJE TEKEM
# ============================================================================

def id_tabele_tekem(sezona):
    """
    Vrne id tabele z vsemi tekmami sezone.

    Sprejme: oznako sezone (npr. "2023-2024").
    Vrne: niz z id-jem tabele.
    Primer: id_tabele_tekem("2023-2024") → "sched_2023-2024_9_1"
    """
    return f"sched_{sezona}_{OZNAKA_LIGE}_1"


def pretvori_vrstico_tekme(vrstica, sezona):
    """
    Iz ene vrstice tabele tekem sestavi slovar s podatki o tekmi.

    Sprejme: vrstico tabele (<tr>) in oznako sezone.
    Vrne: slovar s podatki o tekmi ali None, če tekma nima rezultata
          (npr. preložena ali še neodigrana tekma).
    Primer: pretvori_vrstico_tekme(vrstica, "2023-2024")
        → {"sezona": "2023-2024", "krog": 1, "dan": "Fri", "datum": "2023-08-11",
           "ura": "20:00", "domaci": "Burnley", "gostje": "Manchester City",
           "gledalci": 21572, "stadion": "Turf Moor", "sodnik": "Craig Pawson",
           "opomba": None, "goli_domaci": 0, "goli_gostje": 3, "izid": "G"}
    """
    goli_domaci, goli_gostje = razbij_rezultat(preberi_celico(vrstica, "score"))
    if goli_domaci is None or goli_gostje is None:
        return None

    tekma = {"sezona": sezona}
    for data_stat, stolpec in STOLPCI_TEKEM.items():
        tekma[stolpec] = preberi_celico(vrstica, data_stat)

    # Pretvorba v prave tipe in čiščenje ure.
    tekma["krog"] = v_stevilo(tekma["krog"])
    tekma["gledalci"] = v_stevilo(tekma["gledalci"])
    tekma["ura"] = ocisti_uro(tekma["ura"])

    tekma["goli_domaci"] = goli_domaci
    tekma["goli_gostje"] = goli_gostje
    tekma["izid"] = doloci_izid(goli_domaci, goli_gostje)
    return tekma


def izlusci_tekme(soup, sezona):
    """
    Iz strani s tekmami izlušči vse odigrane tekme sezone.

    Preskoči vmesne vrstice, ponovljene glave in tekme brez rezultata.

    Sprejme: BeautifulSoup strani (iz nalozi_html) in oznako sezone.
    Vrne: seznam slovarjev, en za vsako tekmo (v vrstnem redu s strani).
          Če tabele ni, vrne prazen seznam in izpiše opozorilo.
    Primer: izlusci_tekme(soup, "2023-2024") → [{...}, {...}, ...]  (380 tekem)
    """
    tabela = soup.find("table", id=id_tabele_tekem(sezona))
    if tabela is None:
        print(f"OPOZORILO: v sezoni {sezona} ni tabele {id_tabele_tekem(sezona)}.")
        return []

    tekme = []
    for vrstica in tabela.find("tbody").find_all("tr"):
        if je_vmesna_vrstica(vrstica):
            continue
        tekma = pretvori_vrstico_tekme(vrstica, sezona)
        if tekma is not None:
            tekme.append(tekma)
    return tekme


def izlusci_vse_tekme(od_leta=ZACETNO_LETO, do_leta=KONCNO_LETO):
    """
    Izlušči tekme vseh sezon iz shranjenih datotek v html_strani/tekme/.

    Sezone, za katere datoteke ni, preskoči in izpiše opozorilo.

    Sprejme: začetno in končno leto (privzeto vse sezone projekta).
    Vrne: en sam seznam slovarjev z vsemi tekmami vseh sezon.
    Primer: izlusci_vse_tekme(2023, 2023) → seznam 380 slovarjev
    """
    vse = []
    for leto in range(od_leta, do_leta + 1):
        sezona = oznaka_sezone(leto)
        pot = pot_tekem(sezona)
        if not os.path.exists(pot):
            print(f"OPOZORILO: datoteka {pot} ne obstaja, sezono preskočim.")
            continue
        vse.extend(izlusci_tekme(nalozi_html(pot), sezona))
    return vse


# ============================================================================
# GLAVNI PROGRAM (preizkus izluščanja)
# ============================================================================

def prestej_po_sezonah(vrstice):
    """
    Prešteje, koliko vrstic (klubov ali tekem) je v vsaki sezoni.

    Sprejme: seznam slovarjev s ključem "sezona".
    Vrne: slovar {sezona: število}.
    Primer: prestej_po_sezonah(lestvice) → {"1992-1993": 22, ..., "2025-2026": 20}
    """
    stevilo = {}
    for vrstica in vrstice:
        stevilo[vrstica["sezona"]] = stevilo.get(vrstica["sezona"], 0) + 1
    return stevilo


def izpisi_povzetek(lestvice, tekme):
    """
    Za vsako sezono izpiše število klubov, število tekem, pričakovano število
    tekem, delež zmag domačih in število tekem brez podatka o gledalcih.

    Pričakovano število tekem je klubi * (klubi - 1), ker vsak klub z vsakim
    drugim igra enkrat doma in enkrat v gosteh. Če se števili ne ujemata,
    izpišemo opozorilo, saj to pomeni, da je pri izluščanju kaj narobe.

    Sprejme: seznam slovarjev z lestvicami in seznam slovarjev s tekmami.
    """
    klubi_po_sezonah = prestej_po_sezonah(lestvice)
    tekme_po_sezonah = prestej_po_sezonah(tekme)

    print(f"{'sezona':<10} {'klubi':>5} {'tekme':>6} {'pričak.':>8} "
          f"{'zmage domačih':>14} {'brez gledalcev':>15}")
    for sezona, stevilo_klubov in klubi_po_sezonah.items():
        stevilo_tekem = tekme_po_sezonah.get(sezona, 0)
        pricakovano = stevilo_klubov * (stevilo_klubov - 1)
        tekme_sezone = [t for t in tekme if t["sezona"] == sezona]
        zmage = sum(1 for t in tekme_sezone if t["izid"] == ZMAGA_DOMACIH)
        brez = sum(1 for t in tekme_sezone if not t["gledalci"])
        # max(..., 1): pri sezoni brez tekem se izognemo deljenju z 0.
        delez = zmage / max(stevilo_tekem, 1)
        opozorilo = "" if stevilo_tekem == pricakovano else "  <-- NE UJEMA SE"
        print(f"{sezona:<10} {stevilo_klubov:>5} {stevilo_tekem:>6} {pricakovano:>8} "
              f"{delez:>14.1%} {brez:>15}{opozorilo}")

    print(f"\nSkupaj: {len(lestvice)} vrstic lestvic in {len(tekme)} tekem.")


def izpisi_lestvico(klubi):
    """
    Pregledno izpiše lestvico ene sezone (za preverjanje izluščanja).

    Sprejme: seznam slovarjev ene sezone.
    """
    for k in klubi:
        print(f"{k['mesto']:>3}. {k['klub']:<20} {k['tekme']:>3} {k['zmage']:>3} "
              f"{k['remiji']:>3} {k['porazi']:>3} {k['dani_goli']:>4}:{k['prejeti_goli']:<4} "
              f"{k['tocke']:>4}  {k['povprecje_gledalcev']}  {k['najboljsi_strelec']} "
              f"({k['goli_strelca']})")


if __name__ == "__main__":
    lestvice = izlusci_vse_lestvice()
    tekme = izlusci_vse_tekme()

    # Povzetek po sezonah: število tekem mora biti klubi * (klubi - 1).
    izpisi_povzetek(lestvice, tekme)

    # Za kontrolo izpišemo še lestvico in prvo tekmo zadnje prebrane sezone.
    if lestvice:
        zadnja = lestvice[-1]["sezona"]
        print(f"\nLestvica {zadnja}:")
        izpisi_lestvico([k for k in lestvice if k["sezona"] == zadnja])
    if tekme:
        print(f"\nPrimer tekme: {tekme[0]}")
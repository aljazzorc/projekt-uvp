"""
Izluščanje podatkov iz shranjenih HTML strani FBrefa z BeautifulSoup.

Strani shrani prenos_strani.py v mapo html_strani/. Ta datoteka jih le
prebere (spleta ne uporablja) in iz njih sestavi sezname slovarjev:
  - lestvice: en slovar za vsak klub v vsaki sezoni.

Tabele iščemo po atributu id, celice v vrsticah pa po atributu data-stat,
ki pove, kateri podatek je v celici (npr. data-stat="points" so točke).

Zagon (izpiše povzetek za vse sezone in lestvico zadnje sezone):
    py izlusci_podatke.py
"""

import os

from bs4 import BeautifulSoup

from prenos_strani import KONCNO_LETO, ZACETNO_LETO, oznaka_sezone, pot_lestvice


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
# GLAVNI PROGRAM (preizkus izluščanja)
# ============================================================================

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

    # Koliko klubov smo prebrali v vsaki sezoni (pričakovano 22 do 1994-1995, nato 20).
    print("Število klubov po sezonah:")
    stevilo_po_sezonah = {}
    for klub in lestvice:
        stevilo_po_sezonah[klub["sezona"]] = stevilo_po_sezonah.get(klub["sezona"], 0) + 1
    for sezona, stevilo in stevilo_po_sezonah.items():
        print(f"  {sezona}: {stevilo}")
    print(f"Skupaj: {len(lestvice)} vrstic\n")

    # Za kontrolo izpišemo še lestvico zadnje prebrane sezone.
    if lestvice:
        zadnja = lestvice[-1]["sezona"]
        print(f"Lestvica {zadnja}:")
        izpisi_lestvico([k for k in lestvice if k["sezona"] == zadnja])

"""
Čiščenje izluščenih podatkov in zapis v CSV datoteke.

Seznama slovarjev iz izlusci_podatke.py pretvori v tabeli pandas
(DataFrame), uredi vrstni red in tipe stolpcev, preveri, da v podatkih
ni podvojenih vrstic, odstrani napačna povprečja gledalcev z lestvic
ter tabeli zapiše v mapo podatki/:
  - podatki/lestvice.csv: ena vrstica za vsak klub v vsaki sezoni,
  - podatki/tekme.csv: ena vrstica za vsako odigrano tekmo.

Zagon (izlušči podatke iz html_strani/ in zapiše oba CSV):
    py shrani_podatke.py
"""

import os

import pandas as pd

from izlusci_podatke import izlusci_vse_lestvice, izlusci_vse_tekme


# ============================================================================
# NASTAVITVE
# ============================================================================

# Mapa in datoteki, v kateri zapišemo podatke (ta mapa gre na GitHub).
MAPA_PODATKI = "podatki"
POT_LESTVICE = os.path.join(MAPA_PODATKI, "lestvice.csv")
POT_TEKME = os.path.join(MAPA_PODATKI, "tekme.csv")

# Vrstni red stolpcev v CSV datotekah.
STOLPCI_LESTVICE = [
    "sezona", "mesto", "klub", "tekme", "zmage", "remiji", "porazi",
    "dani_goli", "prejeti_goli", "gol_razlika", "tocke", "tocke_na_tekmo",
    "povprecje_gledalcev", "najboljsi_strelec", "goli_strelca", "opomba",
]
STOLPCI_TEKME = [
    "sezona", "krog", "dan", "datum", "ura", "domaci", "gostje",
    "goli_domaci", "goli_gostje", "izid", "gledalci", "stadion", "sodnik",
    "opomba",
]

# Celoštevilski stolpci, v katerih lahko podatek manjka (npr. gledalci).
# Zanje uporabimo tip "Int64" (z veliko začetnico), ki dovoli manjkajoče
# vrednosti. Navaden int jih ne dovoli, zato bi pandas števila spremenil
# v decimalna (npr. 21572.0).
CELA_STEVILA_LESTVICE = [
    "mesto", "tekme", "zmage", "remiji", "porazi", "dani_goli",
    "prejeti_goli", "gol_razlika", "tocke", "povprecje_gledalcev", "goli_strelca",
]
CELA_STEVILA_TEKME = ["krog", "goli_domaci", "goli_gostje", "gledalci"]

# Stolpci, ki skupaj enolično določajo vrstico (po njih iščemo podvojene).
KLJUC_LESTVICE = ["sezona", "klub"]
KLJUC_TEKME = ["sezona", "domaci", "gostje"]

# Sezoni, v katerih so zaradi covida-19 igrali brez gledalcev. FBref takrat
# tekme brez gledalcev šteje kot 0 gledalcev, zato je povprečje na lestvici
# pravilno, čeprav se ne ujema s povprečjem tekem z znanim obiskom.
COVID_SEZONE = ["2019-2020", "2020-2021"]

# Največje dovoljeno relativno odstopanje (1 %) povprečja gledalcev na lestvici
# od povprečja, izračunanega iz tekem z znanim obiskom.
DOVOLJENO_ODSTOPANJE = 0.01


# ============================================================================
# PRETVORBA V TABELE IN ČIŠČENJE
# ============================================================================

def uredi_tipe(tabela, cela_stevila):
    """
    Celoštevilskim stolpcem nastavi tip Int64, ki dovoli manjkajoče vrednosti.

    Sprejme: DataFrame in seznam imen celoštevilskih stolpcev.
    Vrne: isti DataFrame s popravljenimi tipi.
    Primer: uredi_tipe(tekme, ["gledalci"]) → stolpec gledalci ima tip Int64
    """
    for stolpec in cela_stevila:
        tabela[stolpec] = tabela[stolpec].astype("Int64")
    return tabela


def odstrani_podvojene(tabela, kljuc, ime):
    """
    Odstrani podvojene vrstice in izpiše, koliko jih je bilo.

    Vrstica je podvojena, če ima enake vrednosti v vseh stolpcih ključa
    (npr. ista sezona, isti domači klub in isti gostje).

    Sprejme: DataFrame, seznam stolpcev ključa in ime tabele za izpis.
    Vrne: DataFrame brez podvojenih vrstic (ohrani prvo pojavitev).
    Primer: odstrani_podvojene(tekme, ["sezona", "domaci", "gostje"], "tekme")
    """
    podvojene = tabela.duplicated(subset=kljuc)
    if podvojene.any():
        print(f"OPOZORILO: v tabeli {ime} je {podvojene.sum()} podvojenih vrstic, odstranim jih.")
    return tabela[~podvojene]


def povprecje_gledalcev_iz_tekem(tekme):
    """
    Za vsak klub v vsaki sezoni izračuna povprečno število gledalcev na
    domačih tekmah, pri katerih je obisk znan.

    Sprejme: DataFrame s tekmami (iz pripravi_tekme).
    Vrne: DataFrame s stolpci sezona, klub, povprecje_iz_tekem.
    Primer: povprecje_gledalcev_iz_tekem(tekme) → 686 vrstic
    """
    povprecja = tekme.groupby(["sezona", "domaci"])["gledalci"].apply(
        lambda gledalci: gledalci.astype(float).mean())
    return povprecja.rename("povprecje_iz_tekem").reset_index().rename(columns={"domaci": "klub"})


def odstrani_napacna_povprecja(lestvice, tekme):
    """
    Odstrani (nastavi na prazno) povprečja gledalcev na lestvici, ki so na
    FBrefu napačna.

    FBref pri klubih, ki jim manjka podatek o gledalcih za nekaj domačih
    tekem (sezone 2007/08 do 2010/11), povprečje izračuna napačno; vrednosti
    so lahko celo večje od kapacitete stadiona (npr. Chelsea 2007/08:
    786.543). Povprečje z lestvice zato primerjamo s povprečjem tekem z
    znanim obiskom: če odstopa za več kot DOVOLJENO_ODSTOPANJE, ga
    odstranimo. Covidnih sezon ne spreminjamo (glej COVID_SEZONE).

    Sprejme: DataFrame z lestvicami in DataFrame s tekmami.
    Vrne: DataFrame z lestvicami brez napačnih povprečij.
    Primer: odstrani_napacna_povprecja(lestvice, tekme) → izpiše
            "Odstranjenih napačnih povprečij gledalcev: 32"
    """
    skupaj = lestvice.merge(povprecje_gledalcev_iz_tekem(tekme), on=["sezona", "klub"], how="left")
    odstopanje = (skupaj["povprecje_gledalcev"].astype(float) / skupaj["povprecje_iz_tekem"] - 1).abs()
    # fillna(False): kjer povprečja ni, ga tudi ne odstranjujemo.
    napacno = (odstopanje > DOVOLJENO_ODSTOPANJE).fillna(False) & ~skupaj["sezona"].isin(COVID_SEZONE)

    lestvice = lestvice.copy()
    lestvice.loc[napacno.values, "povprecje_gledalcev"] = pd.NA
    print(f"Odstranjenih napačnih povprečij gledalcev: {napacno.sum()}")
    return lestvice


def pripravi_lestvice(lestvice, tekme):
    """
    Seznam slovarjev z lestvicami pretvori v urejeno tabelo pandas in
    odstrani napačna povprečja gledalcev.

    Sprejme: seznam slovarjev iz izlusci_vse_lestvice() in DataFrame s
             tekmami (iz pripravi_tekme), ki ga potrebujemo za preverjanje
             povprečij gledalcev.
    Vrne: DataFrame s stolpci STOLPCI_LESTVICE, urejen po sezoni in mestu.
    Primer: pripravi_lestvice(izlusci_vse_lestvice(), tekme) → DataFrame s 686 vrsticami
    """
    tabela = pd.DataFrame(lestvice, columns=STOLPCI_LESTVICE)
    tabela = uredi_tipe(tabela, CELA_STEVILA_LESTVICE)
    tabela = odstrani_podvojene(tabela, KLJUC_LESTVICE, "lestvice")
    tabela = odstrani_napacna_povprecja(tabela, tekme)
    return tabela.sort_values(["sezona", "mesto"]).reset_index(drop=True)


def pripravi_tekme(tekme):
    """
    Seznam slovarjev s tekmami pretvori v urejeno tabelo pandas.

    Datum pretvorimo v pravi datumski tip, da lahko tekme pravilno uredimo
    (in kasneje v analizi izberemo npr. tekme po juniju 2020).

    Sprejme: seznam slovarjev iz izlusci_vse_tekme().
    Vrne: DataFrame s stolpci STOLPCI_TEKME, urejen po datumu in uri.
    Primer: pripravi_tekme(izlusci_vse_tekme()) → DataFrame s 13166 vrsticami
    """
    tabela = pd.DataFrame(tekme, columns=STOLPCI_TEKME)
    tabela = uredi_tipe(tabela, CELA_STEVILA_TEKME)
    tabela["datum"] = pd.to_datetime(tabela["datum"])
    tabela = odstrani_podvojene(tabela, KLJUC_TEKME, "tekme")
    return tabela.sort_values(["datum", "ura", "domaci"]).reset_index(drop=True)


# ============================================================================
# ZAPIS V CSV
# ============================================================================

def shrani_csv(tabela, pot):
    """
    Zapiše tabelo v CSV datoteko (mapo ustvari, če je še ni).

    Kodiranje utf-8 ohrani posebne znake v imenih (npr. "Højlund").
    Številk vrstic (index) ne zapišemo, ker niso podatek.

    Sprejme: DataFrame in pot do datoteke.
    Ne vrne ničesar.
    Primer: shrani_csv(tekme, "podatki/tekme.csv")
    """
    os.makedirs(os.path.dirname(pot), exist_ok=True)
    tabela.to_csv(pot, index=False, encoding="utf-8")
    print(f"Zapisano: {pot} ({len(tabela)} vrstic, {len(tabela.columns)} stolpcev)")


def izpisi_manjkajoce(tabela, ime):
    """
    Izpiše, koliko vrednosti manjka v posameznem stolpcu (le stolpce,
    kjer kaj manjka). Tako vidimo, na katere luknje v podatkih moramo
    paziti pri analizi.

    Sprejme: DataFrame in ime tabele za izpis.
    Primer izpisa:  tekme – manjkajoče vrednosti:
                      ura          4620
                      gledalci      960
    """
    manjka = tabela.isna().sum()
    manjka = manjka[manjka > 0]
    print(f"\n{ime} – manjkajoče vrednosti:")
    if manjka.empty:
        print("  nič ne manjka")
    for stolpec, stevilo in manjka.items():
        print(f"  {stolpec:<20} {stevilo:>6}")


def shrani_vse():
    """
    Izlušči lestvice in tekme iz shranjenih strani, ju očisti in zapiše v CSV.

    Ne sprejme ničesar.
    Vrne: par (lestvice, tekme) kot DataFrame-a, da ju lahko uporabi main.py.
    """
    # Najprej pripravimo tekme, ker jih potrebujemo za preverjanje lestvic.
    tekme = pripravi_tekme(izlusci_vse_tekme())
    lestvice = pripravi_lestvice(izlusci_vse_lestvice(), tekme)

    shrani_csv(lestvice, POT_LESTVICE)
    shrani_csv(tekme, POT_TEKME)
    return lestvice, tekme


# ============================================================================
# GLAVNI PROGRAM
# ============================================================================

if __name__ == "__main__":
    lestvice, tekme = shrani_vse()

    izpisi_manjkajoce(lestvice, "lestvice")
    izpisi_manjkajoce(tekme, "tekme")

    print("\nPrve tri tekme:")
    print(tekme.head(3).to_string())
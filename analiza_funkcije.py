"""
Pomožne funkcije za analizo v zvezku analiza.ipynb.

Da je zvezek pregleden, je daljša koda (nalaganje podatkov, izračuni,
risanje grafov) v tej datoteki, v zvezku pa so le klici funkcij in razlage.
"""

import os

import pandas as pd


# ============================================================================
# NASTAVITVE
# ============================================================================

# Poti do CSV datotek, ki jih ustvari main.py.
MAPA_PODATKI = "podatki"
POT_LESTVICE = os.path.join(MAPA_PODATKI, "lestvice.csv")
POT_TEKME = os.path.join(MAPA_PODATKI, "tekme.csv")

# Celoštevilski stolpci, v katerih lahko podatek manjka (tip Int64 dovoli
# manjkajoče vrednosti, navaden int pa ne).
CELA_STEVILA_LESTVICE = ["povprecje_gledalcev", "goli_strelca"]
CELA_STEVILA_TEKME = ["gledalci"]


# ============================================================================
# NALAGANJE PODATKOV
# ============================================================================

def nalozi_lestvice(pot=POT_LESTVICE):
    """
    Naloži končne lestvice vseh sezon iz CSV datoteke.

    Sprejme: pot do datoteke (privzeto podatki/lestvice.csv).
    Vrne: DataFrame, ena vrstica za vsak klub v vsaki sezoni.
    Primer: nalozi_lestvice().shape → (686, 16)
    """
    lestvice = pd.read_csv(pot)
    for stolpec in CELA_STEVILA_LESTVICE:
        lestvice[stolpec] = lestvice[stolpec].astype("Int64")
    return lestvice


def nalozi_tekme(pot=POT_TEKME):
    """
    Naloži vse tekme iz CSV datoteke.

    Stolpec datum pretvori v datumski tip, da lahko tekme izbiramo po
    datumu (npr. tekme po 17. 6. 2020).

    Sprejme: pot do datoteke (privzeto podatki/tekme.csv).
    Vrne: DataFrame, ena vrstica za vsako tekmo.
    Primer: nalozi_tekme().shape → (13166, 14)
    """
    tekme = pd.read_csv(pot, parse_dates=["datum"])
    for stolpec in CELA_STEVILA_TEKME:
        tekme[stolpec] = tekme[stolpec].astype("Int64")
    return tekme


# ============================================================================
# PREGLED PODATKOV
# ============================================================================

def pregled_po_sezonah(lestvice, tekme):
    """
    Za vsako sezono sestavi kratek pregled: število klubov, tekem in golov,
    povprečje golov na tekmo in število tekem brez podatka o gledalcih.

    Sprejme: DataFrame z lestvicami in DataFrame s tekmami.
    Vrne: DataFrame z eno vrstico za vsako sezono.
    Primer: pregled_po_sezonah(lestvice, tekme).loc["1992-1993", "klubi"] → 22
    """
    tekme = tekme.assign(goli=tekme["goli_domaci"] + tekme["goli_gostje"])
    pregled = pd.DataFrame({
        "klubi": lestvice.groupby("sezona")["klub"].count(),
        "tekme": tekme.groupby("sezona").size(),
        "goli": tekme.groupby("sezona")["goli"].sum(),
        "goli_na_tekmo": tekme.groupby("sezona")["goli"].mean().round(2),
        # isna() vrne True, kjer podatek manjka; sum() prešteje vrednosti True.
        "brez_gledalcev": tekme["gledalci"].isna().groupby(tekme["sezona"]).sum(),
    })
    return pregled


def manjkajoce_vrednosti(tabela):
    """
    Prešteje manjkajoče vrednosti v vsakem stolpcu, kjer kaj manjka.

    Sprejme: DataFrame.
    Vrne: Series {stolpec: število manjkajočih}, le stolpci z vsaj eno.
    Primer: manjkajoce_vrednosti(tekme) → ura 8606, gledalci 960, opomba 13166
    """
    manjka = tabela.isna().sum()
    return manjka[manjka > 0]

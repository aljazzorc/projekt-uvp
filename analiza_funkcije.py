"""
Pomožne funkcije za analizo v zvezku analiza.ipynb.

Da je zvezek pregleden, je daljša koda (nalaganje podatkov, izračuni,
risanje grafov) v tej datoteki, v zvezku pa so le klici funkcij in razlage.
"""

import os

import matplotlib.pyplot as plt
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

# Barve grafov. Domači in gostje imata dve jasno različni barvi (modra in
# oranžna), ki ju ločijo tudi ljudje z barvno slepoto; remi je nevtralno siv,
# ker leži "med" zmago domačih in zmago gostov.
BARVA_DOMACI = "#2a78d6"
BARVA_GOSTJE = "#eb6834"
BARVA_REMI = "#b4b2aa"

# Barve ozadja, besedila in mreže (mirne, da ne odvračajo pozornosti od podatkov).
BARVA_OZADJE = "#fcfcfb"
BARVA_BESEDILO = "#0b0b0b"
BARVA_SIVO_BESEDILO = "#52514e"
BARVA_MREZA = "#e1e0d9"

# Oznake izidov in njihova imena za legende.
IZIDI = ["D", "X", "G"]
IMENA_IZIDOV = {"D": "zmaga domačih", "X": "remi", "G": "zmaga gostov"}
BARVE_IZIDOV = {"D": BARVA_DOMACI, "X": BARVA_REMI, "G": BARVA_GOSTJE}


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


# ============================================================================
# SLOG GRAFOV
# ============================================================================

def nastavi_slog():
    """
    Nastavi enoten slog vseh grafov v zvezku (ozadje, pisavo, mrežo, robove).

    Pokličemo jo enkrat na začetku zvezka. Nastavitve se shranijo v
    plt.rcParams in veljajo za vse nadaljnje grafe.
    """
    plt.rcParams.update({
        "figure.figsize": (11, 5),
        "figure.facecolor": BARVA_OZADJE,
        "axes.facecolor": BARVA_OZADJE,
        "axes.edgecolor": BARVA_MREZA,
        "axes.labelcolor": BARVA_SIVO_BESEDILO,
        "axes.titlesize": 14,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.titlecolor": BARVA_BESEDILO,
        # Zgornji in desni rob odstranimo, ker ne nosita informacije.
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.grid.axis": "y",
        "grid.color": BARVA_MREZA,
        "grid.linewidth": 0.8,
        "xtick.color": BARVA_SIVO_BESEDILO,
        "ytick.color": BARVA_SIVO_BESEDILO,
        "legend.frameon": False,
        "font.size": 10,
    })


def kratka_sezona(sezona):
    """
    Skrajša oznako sezone za os grafa.

    Sprejme: oznako sezone (npr. "1992-1993").
    Vrne: kratko oznako.
    Primer: kratka_sezona("1992-1993") → "92/93"
    """
    zacetek, konec = sezona.split("-")
    return f"{zacetek[2:]}/{konec[2:]}"


def oznaci_sezone_na_osi(ax, sezone):
    """
    Na vodoravno os zapiše kratke oznake sezon, navpično zasukane, da se
    34 oznak ne prekriva.

    Sprejme: os grafa (ax) in seznam oznak sezon v vrstnem redu na osi.
    """
    ax.set_xticks(range(len(sezone)))
    ax.set_xticklabels([kratka_sezona(s) for s in sezone], rotation=90)
    ax.set_xlim(-0.6, len(sezone) - 0.4)


# ============================================================================
# SKLOP 1: IZIDI IN GOLI DOMA IN V GOSTEH
# ============================================================================

def delez_izidov(tekme):
    """
    Izračuna delež zmag domačih, remijev in zmag gostov (v odstotkih).

    Sprejme: DataFrame s tekmami (vse ali le izbrane).
    Vrne: Series {"D": ..., "X": ..., "G": ...} v odstotkih.
    Primer: delez_izidov(tekme) → D 45.7, X 25.6, G 28.7
    """
    # value_counts(normalize=True) vrne deleže namesto števil.
    return tekme["izid"].value_counts(normalize=True).reindex(IZIDI) * 100


def delez_izidov_po_sezonah(tekme):
    """
    Za vsako sezono izračuna delež zmag domačih, remijev in zmag gostov.

    Sprejme: DataFrame s tekmami.
    Vrne: DataFrame z vrsticami po sezonah in stolpci D, X, G (v odstotkih).
    Primer: delez_izidov_po_sezonah(tekme).loc["2020-2021", "D"] → 37.9
    """
    delezi = tekme.groupby("sezona")["izid"].value_counts(normalize=True)
    # unstack() iz dolge tabele (sezona, izid) naredi široko: en stolpec za izid.
    return delezi.unstack()[IZIDI] * 100


def graf_izidov_po_sezonah(delezi):
    """
    Nariše zložen stolpčni graf izidov po sezonah: vsak stolpec je ena
    sezona (100 %), razdeljen na zmage domačih, remije in zmage gostov.
    Črtkana črta označuje povprečni delež zmag domačih v vseh sezonah.

    Sprejme: DataFrame iz delez_izidov_po_sezonah.
    Vrne: os grafa (ax), da lahko v zvezku graf še dopolnimo.
    """
    fig, ax = plt.subplots()
    x = range(len(delezi))
    spodaj = pd.Series(0.0, index=delezi.index)

    # Dele stolpca rišemo enega na drugega; "bottom" pove, kje se del začne.
    # Tanek rob v barvi ozadja med deli naredi meje med njimi jasne.
    for izid in IZIDI:
        ax.bar(x, delezi[izid], bottom=spodaj, width=0.8, color=BARVE_IZIDOV[izid],
               edgecolor=BARVA_OZADJE, linewidth=1, label=IMENA_IZIDOV[izid])
        spodaj += delezi[izid]

    # Povprečje zmag domačih označimo s črtkano črto; opis je v legendi,
    # da ne zakriva stolpcev.
    povprecje = delezi["D"].mean()
    ax.axhline(povprecje, color=BARVA_BESEDILO, linewidth=1, linestyle="--",
               label=f"povprečje zmag domačih ({povprecje:.1f} %)")

    oznaci_sezone_na_osi(ax, list(delezi.index))
    ax.set_ylim(0, 100)
    ax.set_ylabel("delež tekem (%)")
    # Legendo postavimo nad graf, pod naslov (pad naslov dvigne).
    ax.set_title("Izidi tekem po sezonah", pad=28)
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=4)
    ax.grid(False)
    return ax


def povprecni_goli_po_sezonah(tekme):
    """
    Za vsako sezono izračuna povprečno število golov domačih in gostujočih
    ekip na tekmo ter razliko med njima.

    Sprejme: DataFrame s tekmami.
    Vrne: DataFrame s stolpci goli_domaci, goli_gostje, razlika.
    Primer: povprecni_goli_po_sezonah(tekme).loc["2020-2021", "razlika"] → 0.01
    """
    goli = tekme.groupby("sezona")[["goli_domaci", "goli_gostje"]].mean()
    goli["razlika"] = goli["goli_domaci"] - goli["goli_gostje"]
    return goli


def graf_golov_po_sezonah(goli):
    """
    Nariše črtni graf povprečnega števila golov domačih in gostujočih ekip
    na tekmo po sezonah. Črti sta označeni neposredno ob koncu, sezona
    2020/21 (tribune brez gledalcev) pa je posebej označena.

    Sprejme: DataFrame iz povprecni_goli_po_sezonah.
    Vrne: os grafa (ax).
    """
    fig, ax = plt.subplots()
    x = list(range(len(goli)))

    for stolpec, barva, ime in [("goli_domaci", BARVA_DOMACI, "domači"),
                                ("goli_gostje", BARVA_GOSTJE, "gostje")]:
        ax.plot(x, goli[stolpec], color=barva, linewidth=2, marker="o",
                markersize=4, label=ime)
        # Oznaka ob zadnji točki, da ni treba gledati legende.
        ax.text(x[-1] + 0.4, goli[stolpec].iloc[-1], ime, color=barva,
                va="center", fontsize=10, fontweight="bold")

    # Sezono 2020/21 označimo s puščico, če je v podatkih.
    if "2020-2021" in goli.index:
        i = list(goli.index).index("2020-2021")
        ax.annotate("2020/21: prazne tribune,\ndomači skoraj brez prednosti",
                    xy=(i, goli["goli_domaci"].iloc[i]), xytext=(i - 9, 0.9),
                    arrowprops={"arrowstyle": "->", "color": BARVA_SIVO_BESEDILO},
                    color=BARVA_SIVO_BESEDILO, fontsize=9)

    oznaci_sezone_na_osi(ax, list(goli.index))
    ax.set_xlim(-0.6, len(goli) + 1.5)
    ax.set_ylim(0.8, 2.0)
    ax.set_ylabel("goli na tekmo")
    ax.set_title("Povprečno število golov domačih in gostujočih ekip na tekmo")
    ax.legend(loc="upper left")
    return ax
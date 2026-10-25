"""
Pomožne funkcije za analizo v zvezku analiza.ipynb.

Da je zvezek pregleden, je daljša koda (nalaganje podatkov, izračuni,
risanje grafov) v tej datoteki, v zvezku pa so le klici funkcij in razlage.
"""

import os

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Patch


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

# Barvi za primerjavo tekem z gledalci in brez njih (covid). Namenoma nista
# modra in oranžna, ki v zvezku pomenita domače in goste.
BARVA_Z_GLEDALCI = "#1baf7a"
BARVA_BREZ_GLEDALCEV = "#6250d6"

# Sezoni, v katerih so zaradi covida-19 igrali brez gledalcev. Prazen podatek
# o gledalcih pomeni prazne tribune le v teh dveh sezonah; drugje (npr.
# 2007/08) pomeni, da podatka na FBrefu ni.
COVID_SEZONE = ["2019-2020", "2020-2021"]

# Meje razredov po številu gledalcev na tekmi.
MEJE_GLEDALCEV = [0, 20000, 30000, 40000, 50000, 60000, 100000]

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


def oznaci_stolpce(ax, stolpci, oblika="{:.1f} %"):
    """
    Nad vsak stolpec stolpčnega grafa zapiše njegovo vrednost.

    Sprejme: os grafa, stolpce (kar vrne ax.bar) in obliko zapisa števila.
    """
    ax.bar_label(stolpci, labels=[oblika.format(v) for v in stolpci.datavalues],
                 padding=3, fontsize=9, color=BARVA_BESEDILO)


# ============================================================================
# SKLOP 1: PRAZNE TRIBUNE (COVID-19)
# ============================================================================

def je_brez_gledalcev(tekme):
    """
    Za vsako tekmo pove, ali je bila odigrana pred praznimi tribunami
    zaradi covida-19 (sezona 2019/20 ali 2020/21 in ni podatka o gledalcih).

    Sprejme: DataFrame s tekmami.
    Vrne: Series z vrednostmi True/False (True = brez gledalcev).
    Primer: je_brez_gledalcev(tekme).sum() → 440
    """
    return tekme["sezona"].isin(COVID_SEZONE) & tekme["gledalci"].isna()


def obdobje_tekme(tekma):
    """
    Tekmi določi obdobje za graf okoli covida: sezono, pri covidnih
    sezonah pa ločeno del z gledalci in del brez njih.

    Sprejme: eno vrstico DataFrame-a s tekmami.
    Vrne: niz z imenom obdobja.
    Primer: obdobje_tekme(tekma iz julija 2020) → "19/20\nbrez gledalcev"
    """
    kratko = kratka_sezona(tekma["sezona"])
    if tekma["sezona"] not in COVID_SEZONE:
        return kratko
    if pd.isna(tekma["gledalci"]):
        return f"{kratko}\nbrez gledalcev"
    # V sezoni 2020/21 je bilo na nekaj tekmah dovoljeno le 2.000–10.000 gledalcev.
    if tekma["sezona"] == "2020-2021":
        return f"{kratko}\nomejeno"
    return f"{kratko}\nz gledalci"


def zmage_domacih_okoli_covida(tekme, od_sezone="2016-2017", do_sezone="2023-2024"):
    """
    Izračuna delež zmag domačih v sezonah pred covidom, med njim in po njem.
    Covidni sezoni sta razdeljeni na tekme z gledalci in brez njih.

    Sprejme: DataFrame s tekmami ter prvo in zadnjo sezono za prikaz.
    Vrne: DataFrame s stolpci obdobje, tekme, zmage_domacih (v %) in
          brez_gledalcev (True/False), v časovnem vrstnem redu.
    Primer: zmage_domacih_okoli_covida(tekme) → 10 obdobij od 16/17 do 23/24
    """
    izbrane = tekme[tekme["sezona"].between(od_sezone, do_sezone)].copy()
    izbrane["obdobje"] = izbrane.apply(obdobje_tekme, axis=1)
    izbrane["brez_gledalcev"] = je_brez_gledalcev(izbrane)

    # sort=False ohrani vrstni red, v katerem se obdobja pojavijo (po datumu).
    izbrane = izbrane.sort_values("datum")
    obdobja = izbrane.groupby("obdobje", sort=False).agg(
        tekme=("izid", "size"),
        zmage_domacih=("izid", lambda izidi: (izidi == "D").mean() * 100),
        brez_gledalcev=("brez_gledalcev", "first"),
    )
    return obdobja.reset_index()


def graf_zmag_okoli_covida(obdobja):
    """
    Nariše stolpčni graf deleža zmag domačih po obdobjih okoli covida.
    Obdobja brez gledalcev so obarvana drugače, nad stolpci so vrednosti,
    pod oznakami pa število tekem.

    Sprejme: DataFrame iz zmage_domacih_okoli_covida.
    Vrne: os grafa (ax).
    """
    fig, ax = plt.subplots()
    barve = [BARVA_BREZ_GLEDALCEV if brez else BARVA_Z_GLEDALCI
             for brez in obdobja["brez_gledalcev"]]
    stolpci = ax.bar(range(len(obdobja)), obdobja["zmage_domacih"], color=barve, width=0.7)
    oznaci_stolpce(ax, stolpci)

    # Pod imenom obdobja izpišemo še število tekem (pri malem številu tekem
    # je delež manj zanesljiv).
    ax.set_xticks(range(len(obdobja)))
    ax.set_xticklabels([f"{o}\n({n} tekem)" for o, n in zip(obdobja["obdobje"], obdobja["tekme"])],
                       fontsize=8)

    # Legendo sestavimo ročno iz dveh barvnih kvadratkov (Patch).
    legenda = [Patch(color=BARVA_Z_GLEDALCI, label="z gledalci"),
               Patch(color=BARVA_BREZ_GLEDALCEV, label="brez gledalcev")]
    ax.set_ylim(0, 65)
    ax.set_ylabel("zmage domačih (%)")
    ax.set_title("Delež zmag domačih pred covidom, med njim in po njem", pad=28)
    ax.legend(handles=legenda, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2)
    return ax


def primerjava_z_in_brez_gledalcev(tekme):
    """
    Primerja tekme brez gledalcev (covid) z vsemi tekmami iz sezon, ko so
    tribune bile polne (vse sezone razen 2019/20 in 2020/21).

    Sprejme: DataFrame s tekmami.
    Vrne: DataFrame s stolpcema "z gledalci" in "brez gledalcev" ter
          vrsticami: število tekem, deleži izidov, goli domačih in gostov,
          točke na tekmo doma in v gosteh.
    Primer: primerjava_z_in_brez_gledalcev(tekme).loc["zmaga domačih (%)"]
        → z gledalci 45.9, brez gledalcev 38.6
    """
    skupine = {
        "z gledalci": tekme[~tekme["sezona"].isin(COVID_SEZONE)],
        "brez gledalcev": tekme[je_brez_gledalcev(tekme)],
    }
    primerjava = {}
    for ime, t in skupine.items():
        delezi = delez_izidov(t)
        primerjava[ime] = {
            "tekme": len(t),
            "zmaga domačih (%)": delezi["D"],
            "remi (%)": delezi["X"],
            "zmaga gostov (%)": delezi["G"],
            "goli domačih na tekmo": t["goli_domaci"].mean(),
            "goli gostov na tekmo": t["goli_gostje"].mean(),
            "točke domačih na tekmo": (3 * (t["izid"] == "D") + (t["izid"] == "X")).mean(),
            "točke gostov na tekmo": (3 * (t["izid"] == "G") + (t["izid"] == "X")).mean(),
        }
    return pd.DataFrame(primerjava)


def graf_z_in_brez_gledalcev(primerjava):
    """
    Nariše združen stolpčni graf: za vsak izid (zmaga domačih, remi,
    zmaga gostov) dva stolpca, za tekme z gledalci in brez njih.

    Sprejme: DataFrame iz primerjava_z_in_brez_gledalcev.
    Vrne: os grafa (ax).
    """
    fig, ax = plt.subplots(figsize=(8, 5))
    vrstice = ["zmaga domačih (%)", "remi (%)", "zmaga gostov (%)"]
    sirina = 0.38

    # Stolpca skupine zamaknemo levo in desno od sredine izida.
    for zamik, skupina, barva in [(-sirina / 2, "z gledalci", BARVA_Z_GLEDALCI),
                                  (sirina / 2, "brez gledalcev", BARVA_BREZ_GLEDALCEV)]:
        polozaji = [i + zamik for i in range(len(vrstice))]
        stolpci = ax.bar(polozaji, primerjava.loc[vrstice, skupina], width=sirina - 0.02,
                         color=barva, label=f"{skupina} ({primerjava.loc['tekme', skupina]:.0f} tekem)")
        oznaci_stolpce(ax, stolpci)

    ax.set_xticks(range(len(vrstice)))
    ax.set_xticklabels([v.replace(" (%)", "") for v in vrstice])
    ax.set_ylim(0, 55)
    ax.set_ylabel("delež tekem (%)")
    ax.set_title("Izidi tekem z gledalci in brez njih", pad=28)
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2)
    return ax


# ============================================================================
# SKLOP 1: ŠTEVILO GLEDALCEV IN ZMAGE
# ============================================================================

def tekme_z_gledalci(tekme):
    """
    Izbere tekme, pri katerih je podatek o gledalcih znan, brez covidnih
    sezon (te bi primerjavo popačile).

    Sprejme: DataFrame s tekmami.
    Vrne: DataFrame z izbranimi tekmami.
    Primer: len(tekme_z_gledalci(tekme)) → 11886
    """
    return tekme[~tekme["sezona"].isin(COVID_SEZONE) & tekme["gledalci"].notna()]


def ime_razreda(od, do):
    """
    Sestavi berljivo ime razreda gledalcev.

    Primer: ime_razreda(20000, 30000) → "20–30 tisoč"
            ime_razreda(0, 20000) → "pod 20 tisoč"
            ime_razreda(60000, 100000) → "nad 60 tisoč"
    """
    if od == MEJE_GLEDALCEV[0]:
        return f"pod {do // 1000} tisoč"
    if do == MEJE_GLEDALCEV[-1]:
        return f"nad {od // 1000} tisoč"
    return f"{od // 1000}–{do // 1000} tisoč"


def zmage_po_razredih_gledalcev(tekme):
    """
    Tekme razdeli v razrede po številu gledalcev (meje v MEJE_GLEDALCEV) in
    za vsak razred izračuna število tekem in delež zmag domačih.

    Sprejme: DataFrame s tekmami (upošteva le tekme z znanimi gledalci).
    Vrne: DataFrame z indeksom razred ter stolpcema tekme in zmage_domacih (v %).
    Primer: zmage_po_razredih_gledalcev(tekme).loc["nad 60 tisoč", "zmage_domacih"] → 61.8
    """
    izbrane = tekme_z_gledalci(tekme)
    imena = [ime_razreda(od, do) for od, do in zip(MEJE_GLEDALCEV, MEJE_GLEDALCEV[1:])]
    # pd.cut vsaki tekmi določi razred; right=False pomeni, da je spodnja
    # meja vključena (20000 gledalcev spada v razred 20–30 tisoč).
    razred = pd.cut(izbrane["gledalci"].astype(float), MEJE_GLEDALCEV, labels=imena, right=False)
    return izbrane.groupby(razred, observed=True).agg(
        tekme=("izid", "size"),
        zmage_domacih=("izid", lambda izidi: (izidi == "D").mean() * 100),
    )


def graf_zmag_po_razredih_gledalcev(razredi):
    """
    Nariše stolpčni graf deleža zmag domačih po razredih števila gledalcev.

    Sprejme: DataFrame iz zmage_po_razredih_gledalcev.
    Vrne: os grafa (ax).
    """
    fig, ax = plt.subplots(figsize=(9, 5))
    stolpci = ax.bar(range(len(razredi)), razredi["zmage_domacih"], color=BARVA_DOMACI, width=0.7)
    oznaci_stolpce(ax, stolpci)
    ax.set_xticks(range(len(razredi)))
    ax.set_xticklabels([f"{r}\n({n} tekem)" for r, n in zip(razredi.index, razredi["tekme"])],
                       fontsize=9)
    ax.set_ylim(0, 75)
    ax.set_xlabel("število gledalcev na tekmi")
    ax.set_ylabel("zmage domačih (%)")
    ax.set_title("Delež zmag domačih glede na število gledalcev")
    return ax


def obisk_in_zmage_klubov(tekme):
    """
    Za vsak klub v vsaki sezoni izračuna povprečno število gledalcev na
    domačih tekmah in delež zmag doma.

    Povprečje računamo iz posameznih tekem in ne vzamemo povprečja z
    lestvice: FBref ga pri klubih, ki jim manjka podatek za nekaj tekem
    (sezoni 2007/08 in 2008/09), izračuna napačno (npr. 786.543 gledalcev).
    Zato upoštevamo le klube, ki imajo podatek za vse domače tekme sezone.
    Covidni sezoni izpustimo.

    Sprejme: DataFrame s tekmami.
    Vrne: DataFrame s stolpci sezona, klub, povprecje_gledalcev, zmage_doma (v %).
    Primer: len(obisk_in_zmage_klubov(tekme)) → 598
    """
    brez_covida = tekme[~tekme["sezona"].isin(COVID_SEZONE)]
    obisk = brez_covida.groupby(["sezona", "domaci"]).agg(
        povprecje_gledalcev=("gledalci", lambda g: g.astype(float).mean()),
        manjka=("gledalci", lambda g: g.isna().sum()),
        zmage_doma=("izid", lambda izidi: (izidi == "D").mean() * 100),
    ).reset_index().rename(columns={"domaci": "klub"})
    obisk = obisk[obisk["manjka"] == 0]
    return obisk.drop(columns="manjka").reset_index(drop=True)


def graf_obisk_in_zmage(obisk):
    """
    Nariše razsevni diagram: vsaka točka je en klub v eni sezoni, vodoravno
    je povprečno število gledalcev, navpično delež zmag doma.

    Sprejme: DataFrame iz obisk_in_zmage_klubov.
    Vrne: os grafa (ax).
    """
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.scatter(obisk["povprecje_gledalcev"] / 1000, obisk["zmage_doma"], s=18,
               color=BARVA_DOMACI, alpha=0.6, edgecolor="none")
    ax.set_xlabel("povprečno število gledalcev na domači tekmi (v tisočih)")
    ax.set_ylabel("zmage doma (%)")
    ax.set_title("Obisk in zmage doma (en klub v eni sezoni)")
    ax.grid(True, axis="both")
    return ax


def povezava_obiska_in_zmag(obisk):
    """
    Izračuna korelacijo med obiskom in zmagami doma na dva načina:
      - med vsemi klubi in sezonami skupaj,
      - znotraj klubov: primerjamo vsak klub sam s seboj (odstopanje obiska
        in zmag od povprečja tega kluba), da izločimo vpliv tega, da imajo
        močni klubi hkrati velike stadione.

    Korelacija je število med -1 in 1: blizu 0 pomeni, da povezave ni,
    blizu 1 pa, da večjemu obisku skoraj vedno sledi več zmag.

    Sprejme: DataFrame iz obisk_in_zmage_klubov.
    Vrne: slovar {"vsi klubi": ..., "znotraj klubov": ...}.
    Primer: povezava_obiska_in_zmag(obisk) → {"vsi klubi": 0.4, "znotraj klubov": 0.0}
    """
    odstopanja = obisk[["povprecje_gledalcev", "zmage_doma"]] - \
        obisk.groupby("klub")[["povprecje_gledalcev", "zmage_doma"]].transform("mean")
    return {
        "vsi klubi": obisk["povprecje_gledalcev"].corr(obisk["zmage_doma"]),
        "znotraj klubov": odstopanja["povprecje_gledalcev"].corr(odstopanja["zmage_doma"]),
    }
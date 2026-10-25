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

# Odtenki modre za 1., 2. in 3. mesto: temnejša barva pomeni višje mesto.
BARVE_MEST = {1: "#1c5cab", 2: "#3987e5", 3: "#86b6ef"}

# Barva za uvrstitve na dno lestvice (umirjena siva).
BARVA_DNO = "#3a3936"

# Besedilo, s katerim FBref v opombi lestvice označi izpadle klube.
OZNAKA_IZPADA = "Relegated"

# Število tekem v sezoni z 20 klubi; točke iz sezon z 22 klubi (42 tekem)
# preračunamo na toliko tekem, da so primerljive.
TEKME_V_SEZONI = 38

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


def preveri_skladnost(tekme, lestvice):
    """
    Preveri, ali se podatki iz posameznih tekem ujemajo s končnimi lestvicami.

    Za vsak klub v vsaki sezoni iz tekem izračuna število tekem, točke
    (zmaga 3, remi 1), dane in prejete gole ter jih primerja z lestvico.
    Ker sta tabeli zajeti z različnih strani FBrefa, ujemanje potrjuje,
    da je zajem pravilen.

    Sprejme: DataFrame s tekmami in DataFrame z lestvicami.
    Vrne: DataFrame s klubi, pri katerih se kaj ne ujema (prazen, če se
          vse ujema), s stolpci iz lestvice, iz tekem in opombo.
    Primer: preveri_skladnost(tekme, lestvice) → 6 vrstic (4 odbitki točk,
            2 napaki v lestvici FBrefa)
    """
    # Vsako tekmo zapišemo dvakrat: enkrat z vidika domačih, enkrat gostov.
    doma = pd.DataFrame({
        "sezona": tekme["sezona"], "klub": tekme["domaci"],
        "dani": tekme["goli_domaci"], "prejeti": tekme["goli_gostje"],
        "tocke": tekme["izid"].map({"D": 3, "X": 1, "G": 0}),
    })
    v_gosteh = pd.DataFrame({
        "sezona": tekme["sezona"], "klub": tekme["gostje"],
        "dani": tekme["goli_gostje"], "prejeti": tekme["goli_domaci"],
        "tocke": tekme["izid"].map({"D": 0, "X": 1, "G": 3}),
    })
    iz_tekem = pd.concat([doma, v_gosteh]).groupby(["sezona", "klub"]).agg(
        tekme_iz_tekem=("tocke", "size"), tocke_iz_tekem=("tocke", "sum"),
        dani_iz_tekem=("dani", "sum"), prejeti_iz_tekem=("prejeti", "sum"),
    ).reset_index()

    skupaj = lestvice.merge(iz_tekem, on=["sezona", "klub"], how="outer")
    razlike = ((skupaj["tekme"] != skupaj["tekme_iz_tekem"])
               | (skupaj["tocke"] != skupaj["tocke_iz_tekem"])
               | (skupaj["dani_goli"] != skupaj["dani_iz_tekem"])
               | (skupaj["prejeti_goli"] != skupaj["prejeti_iz_tekem"]))
    stolpci = ["sezona", "klub", "tocke", "tocke_iz_tekem", "dani_goli", "dani_iz_tekem",
               "prejeti_goli", "prejeti_iz_tekem", "opomba"]
    return skupaj.loc[razlike, stolpci].reset_index(drop=True)


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
        # Mreža naj bo pod stolpci in črtami, ne čez njih.
        "axes.axisbelow": True,
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
    lestvice: tam pri klubih z manjkajočimi tekmami (sezone 2007/08 do
    2010/11) manjka, ker so bile vrednosti FBrefa napačne in so odstranjene
    pri čiščenju (shrani_podatke.py). Upoštevamo le klube, ki imajo podatek
    za vse domače tekme sezone. Covidni sezoni izpustimo.

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


# ============================================================================
# SKLOP 2: KLUBI NA VRHU IN NA DNU LESTVICE
# ============================================================================

def stevilo_klubov_v_sezoni(lestvice):
    """
    Za vsako vrstico lestvice vrne, koliko klubov je igralo v tisti sezoni
    (22 do sezone 1994/95, nato 20).

    Sprejme: DataFrame z lestvicami.
    Vrne: Series z istim indeksom kot lestvice.
    Primer: stevilo_klubov_v_sezoni(lestvice).iloc[0] → 22
    """
    # transform("size") vsaki vrstici pripiše velikost njene skupine (sezone).
    return lestvice.groupby("sezona")["klub"].transform("size")


def uvrstitve_na_vrhu(lestvice):
    """
    Za vsak klub prešteje, kolikokrat je končal na 1., 2. in 3. mestu.

    Sprejme: DataFrame z lestvicami.
    Vrne: DataFrame z indeksom klub in stolpci 1, 2, 3 ter skupaj, urejen
          od kluba z največ uvrstitvami (pri enakem številu odloča več
          naslovov prvaka).
    Primer: uvrstitve_na_vrhu(lestvice).loc["Manchester Utd"]
        → 1: 13, 2: 7, 3: 6, skupaj: 26
    """
    vrh = lestvice[lestvice["mesto"] <= 3]
    # unstack naredi tabelo klub × mesto; fill_value=0 tam, kjer klub mesta ni dosegel.
    stevila = vrh.groupby(["klub", "mesto"]).size().unstack(fill_value=0)
    stevila["skupaj"] = stevila.sum(axis=1)
    return stevila.sort_values(["skupaj", 1], ascending=False)


def uvrstitve_na_dnu(lestvice, zadnjih=3):
    """
    Za vsak klub prešteje, kolikokrat je končal na zadnjih treh mestih lestvice.

    Ker je bilo v prvih treh sezonah 22 klubov, so "zadnja tri mesta" takrat
    19.–22. mesto, kasneje pa 18.–20. mesto.

    Sprejme: DataFrame z lestvicami in število zadnjih mest (privzeto 3).
    Vrne: Series {klub: število uvrstitev}, urejena padajoče.
    Primer: uvrstitve_na_dnu(lestvice)["Norwich City"] → 6
    """
    na_dnu = lestvice["mesto"] > stevilo_klubov_v_sezoni(lestvice) - zadnjih
    return lestvice.loc[na_dnu, "klub"].value_counts()


def graf_uvrstitev_na_vrhu(vrh):
    """
    Nariše vodoraven zložen stolpčni graf: za vsak klub, ki je bil vsaj enkrat
    med prvimi tremi, število 1., 2. in 3. mest. Na koncu stolpca je skupno
    število uvrstitev.

    Sprejme: DataFrame iz uvrstitve_na_vrhu.
    Vrne: os grafa (ax).
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    # Obrnemo vrstni red, da je klub z največ uvrstitvami na vrhu grafa.
    vrh = vrh.iloc[::-1]
    levo = pd.Series(0, index=vrh.index)
    imena_mest = {1: "1. mesto (prvak)", 2: "2. mesto", 3: "3. mesto"}

    for mesto in [1, 2, 3]:
        ax.barh(vrh.index, vrh[mesto], left=levo, color=BARVE_MEST[mesto],
                edgecolor=BARVA_OZADJE, linewidth=1, height=0.7, label=imena_mest[mesto])
        levo += vrh[mesto]

    # Skupno število zapišemo desno od stolpca.
    for i, skupaj in enumerate(vrh["skupaj"]):
        ax.text(skupaj + 0.3, i, str(skupaj), va="center", fontsize=9, color=BARVA_BESEDILO)

    ax.set_xlabel("število sezon")
    ax.set_title("Kdo je največkrat končal med prvimi tremi", pad=28)
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=3)
    ax.grid(True, axis="x")
    ax.grid(False, axis="y")
    return ax


def graf_uvrstitev_na_dnu(dno, najmanj=3):
    """
    Nariše vodoraven stolpčni graf klubov, ki so vsaj `najmanj`-krat končali
    na zadnjih treh mestih lestvice.

    Sprejme: Series iz uvrstitve_na_dnu in najmanjše število uvrstitev za prikaz.
    Vrne: os grafa (ax).
    """
    dno = dno[dno >= najmanj].iloc[::-1]
    fig, ax = plt.subplots(figsize=(10, 6))
    stolpci = ax.barh(dno.index, dno, color=BARVA_DNO, height=0.7)
    ax.bar_label(stolpci, padding=3, fontsize=9, color=BARVA_BESEDILO)
    ax.set_xlabel("število sezon")
    ax.set_title(f"Kdo je največkrat končal na zadnjih treh mestih (vsaj {najmanj}-krat)")
    ax.grid(True, axis="x")
    ax.grid(False, axis="y")
    return ax


# ============================================================================
# SKLOP 2: TOČKE PRVAKA, TOČKE ZA OBSTANEK IN RAZLIKA MED VRHOM IN DNOM
# ============================================================================

def tocke_na_38_tekem(lestvice):
    """
    Točke preračuna na 38 tekem, da so sezone z 42 tekmami (22 klubov)
    primerljive s sezonami z 38 tekmami.

    Sprejme: DataFrame z lestvicami (ali njegov del).
    Vrne: Series s preračunanimi točkami.
    Primer: Manchester Utd 1992/93: 84 točk v 42 tekmah → 76.0
    """
    return lestvice["tocke"] / lestvice["tekme"] * TEKME_V_SEZONI


def tocke_prvaka(lestvice):
    """
    Za vsako sezono vrne prvaka, njegove točke in točke, preračunane na 38 tekem.

    Sprejme: DataFrame z lestvicami.
    Vrne: DataFrame z indeksom sezona in stolpci klub, tocke, tocke_38.
    Primer: tocke_prvaka(lestvice).loc["2017-2018", "tocke"] → 100
    """
    prvaki = lestvice[lestvice["mesto"] == 1].set_index("sezona")
    prvaki = prvaki[["klub", "tocke"]].assign(tocke_38=tocke_na_38_tekem(prvaki))
    return prvaki


def stevilo_izpadlih(lestvice):
    """
    Za vsako sezono prešteje izpadle klube (po opombi "Relegated").
    Običajno izpadejo trije, v sezoni 1994/95 pa so štirje, ker se je liga
    zmanjšala z 22 na 20 klubov.

    Sprejme: DataFrame z lestvicami.
    Vrne: Series {sezona: število izpadlih}.
    Primer: stevilo_izpadlih(lestvice)["1994-1995"] → 4
    """
    izpadel = lestvice["opomba"].fillna("").str.contains(OZNAKA_IZPADA)
    return izpadel.groupby(lestvice["sezona"]).sum()


def meja_obstanka(lestvice):
    """
    Za vsako sezono poišče najslabši klub, ki je obstal v ligi (mesto tik nad
    izpadlimi), in najboljši izpadli klub (prvo mesto pod črto).

    Sprejme: DataFrame z lestvicami.
    Vrne: DataFrame z indeksom sezona in stolpci obstal, tocke, tocke_38,
          izpadel, tocke_izpadlega.
    Primer: meja_obstanka(lestvice).loc["2023-2024", "obstal"] → "Nottingham"
    """
    izpadlih = lestvice["sezona"].map(stevilo_izpadlih(lestvice))
    mesto_obstanka = stevilo_klubov_v_sezoni(lestvice) - izpadlih

    obstali = lestvice[lestvice["mesto"] == mesto_obstanka].set_index("sezona")
    izpadli = lestvice[lestvice["mesto"] == mesto_obstanka + 1].set_index("sezona")
    return pd.DataFrame({
        "obstal": obstali["klub"],
        "tocke": obstali["tocke"],
        "tocke_38": tocke_na_38_tekem(obstali),
        "izpadel": izpadli["klub"],
        "tocke_izpadlega": izpadli["tocke"],
    })


def graf_tock_skozi_cas(tocke, barva, naslov, oznaka_povprecja, referenca=None):
    """
    Nariše črtni graf točk (preračunanih na 38 tekem) po sezonah s črtkanim
    povprečjem. Uporabimo ga za točke prvaka in točke za obstanek.

    Sprejme: Series s točkami po sezonah, barvo črte, naslov grafa,
             besedilo za povprečje v legendi in neobvezno referenčno
             vrednost kot par (vrednost, opis), ki se nariše s pikčasto črto.
    Vrne: os grafa (ax).
    """
    fig, ax = plt.subplots()
    x = list(range(len(tocke)))
    ax.plot(x, tocke, color=barva, linewidth=2, marker="o", markersize=4,
            label="točke (preračunane na 38 tekem)")
    ax.axhline(tocke.mean(), color=BARVA_SIVO_BESEDILO, linewidth=1, linestyle="--",
               label=f"{oznaka_povprecja} ({tocke.mean():.1f})")
    if referenca is not None:
        vrednost, opis = referenca
        ax.axhline(vrednost, color=BARVA_SIVO_BESEDILO, linewidth=1, linestyle=":", label=opis)
    oznaci_sezone_na_osi(ax, list(tocke.index))
    ax.set_ylabel("točke")
    ax.set_title(naslov, pad=28)
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=3)
    return ax


def oznaci_tocko(ax, tocke, sezona, besedilo, zamik):
    """
    Na črtnem grafu s puščico označi vrednost v izbrani sezoni.

    Sprejme: os grafa, Series s točkami (indeks so sezone), sezono, besedilo
             oznake in zamik besedila (dx, dy) glede na točko.
    """
    i = list(tocke.index).index(sezona)
    ax.annotate(besedilo, xy=(i, tocke.iloc[i]), xytext=(i + zamik[0], tocke.iloc[i] + zamik[1]),
                arrowprops={"arrowstyle": "->", "color": BARVA_SIVO_BESEDILO},
                color=BARVA_SIVO_BESEDILO, fontsize=9)


def vrh_in_dno_po_sezonah(lestvice, koliko=3):
    """
    Za vsako sezono izračuna povprečne točke na tekmo in povprečno gol
    razliko na tekmo prvih treh in zadnjih treh klubov ter razliko med njimi.
    Vrednosti "na tekmo" so primerljive med sezonami z 42 in 38 tekmami.

    Sprejme: DataFrame z lestvicami in velikost skupine (privzeto 3).
    Vrne: DataFrame z indeksom sezona in stolpci tocke_vrh, tocke_dno,
          razlika_tock, gol_razlika_vrh, gol_razlika_dno, razlika_gol_razlike.
    Primer: vrh_in_dno_po_sezonah(lestvice).loc["2023-2024", "razlika_tock"] → 1.72
    """
    na_tekmo = lestvice.assign(
        tocke_na_tekmo=lestvice["tocke"] / lestvice["tekme"],
        gol_razlika_na_tekmo=lestvice["gol_razlika"] / lestvice["tekme"],
    )
    vrh = na_tekmo[na_tekmo["mesto"] <= koliko].groupby("sezona")
    dno = na_tekmo[na_tekmo["mesto"] > stevilo_klubov_v_sezoni(na_tekmo) - koliko].groupby("sezona")

    tabela = pd.DataFrame({
        "tocke_vrh": vrh["tocke_na_tekmo"].mean(),
        "tocke_dno": dno["tocke_na_tekmo"].mean(),
        "gol_razlika_vrh": vrh["gol_razlika_na_tekmo"].mean(),
        "gol_razlika_dno": dno["gol_razlika_na_tekmo"].mean(),
    })
    tabela["razlika_tock"] = tabela["tocke_vrh"] - tabela["tocke_dno"]
    tabela["razlika_gol_razlike"] = tabela["gol_razlika_vrh"] - tabela["gol_razlika_dno"]
    return tabela


def graf_vrh_in_dno(tabela):
    """
    Nariše dva grafa enega pod drugim (skupna časovna os): zgoraj povprečne
    točke na tekmo prvih treh in zadnjih treh klubov, spodaj njihovo
    povprečno gol razliko na tekmo. Prostor med črtama (razlika) je osenčen.

    Sprejme: DataFrame iz vrh_in_dno_po_sezonah.
    Vrne: seznam obeh osi.
    """
    fig, osi = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
    x = list(range(len(tabela)))
    grafa = [
        (osi[0], "tocke", "točke na tekmo", "Točke na tekmo: prvi trije in zadnji trije klubi"),
        (osi[1], "gol_razlika", "gol razlika na tekmo", "Gol razlika na tekmo: prvi trije in zadnji trije klubi"),
    ]
    for ax, stolpec, os_y, naslov in grafa:
        vrh, dno = tabela[f"{stolpec}_vrh"], tabela[f"{stolpec}_dno"]
        # Osenčen pas med črtama pokaže velikost razlike.
        ax.fill_between(x, dno, vrh, color=BARVA_MREZA, alpha=0.6, linewidth=0)
        ax.plot(x, vrh, color=BARVE_MEST[1], linewidth=2, marker="o", markersize=3,
                label="prvi trije")
        ax.plot(x, dno, color=BARVA_DNO, linewidth=2, marker="o", markersize=3,
                label="zadnji trije")
        ax.set_ylabel(os_y)
        ax.set_title(naslov, pad=28)
        ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2)
    osi[1].axhline(0, color=BARVA_SIVO_BESEDILO, linewidth=0.8)
    oznaci_sezone_na_osi(osi[1], list(tabela.index))
    fig.tight_layout()
    return osi
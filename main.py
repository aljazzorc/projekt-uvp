"""
Glavni program: z enim ukazom pripravi vse podatke za analizo.

Postopek:
  1. preveri, ali so vse strani (lestvice in tekme vseh sezon) shranjene
     v mapi html_strani/ in ali so prave strani,
  2. iz njih izlušči podatke (izlusci_podatke.py),
  3. podatke očisti in zapiše v podatki/lestvice.csv in podatki/tekme.csv
     (shrani_podatke.py).

Strani se shranjujejo ročno v brskalniku (py prenos_strani.py), zato jih
main.py ne prenaša sam. Če kakšna stran manjka, program to izpiše in se
ustavi, da obstoječih CSV datotek ne prepiše z nepopolnimi podatki.

Zagon:
    py main.py
"""

import sys

from prenos_strani import KONCNO_LETO, MANJKA, ZACETNO_LETO, oznaka_sezone, preveri_sezone
from shrani_podatke import shrani_vse


# ============================================================================
# KORAKI POSTOPKA
# ============================================================================

def vse_strani_shranjene():
    """
    Preveri, ali so shranjene vse strani za vse sezone projekta.

    Manjkajoče ali napačne strani izpiše funkcija preveri_sezone.

    Ne sprejme ničesar.
    Vrne: True, če nobena stran ne manjka, sicer False.
    Primer: vse_strani_shranjene() → True
    """
    stevec = preveri_sezone(ZACETNO_LETO, KONCNO_LETO)
    return stevec[MANJKA] == 0


def izpisi_povzetek(lestvice, tekme):
    """
    Izpiše kratek povzetek zapisanih podatkov.

    Sprejme: DataFrame z lestvicami in DataFrame s tekmami.
    """
    print(f"\nSezone: {lestvice['sezona'].min()} do {lestvice['sezona'].max()} "
          f"({lestvice['sezona'].nunique()} sezon)")
    print(f"Klubi na lestvicah: {lestvice['klub'].nunique()} različnih")
    print(f"Tekme: {len(tekme)}, golov skupaj: "
          f"{tekme['goli_domaci'].sum() + tekme['goli_gostje'].sum()}")


# ============================================================================
# GLAVNI PROGRAM
# ============================================================================

def main():
    """
    Izvede celoten postopek: preverjanje strani, izluščanje in zapis v CSV.

    Če kakšna stran manjka, izpiše navodilo in program konča z izhodno
    kodo 1 (znak, da postopek ni uspel).
    """
    print(f"1/2 Preverjam shranjene strani ({oznaka_sezone(ZACETNO_LETO)} "
          f"do {oznaka_sezone(KONCNO_LETO)}) ...")
    if not vse_strani_shranjene():
        print("\nNekatere strani manjkajo ali niso prave (izpisane zgoraj).")
        print("Shrani jih z ukazom:  py prenos_strani.py")
        print("in nato znova zaženi: py main.py")
        sys.exit(1)
    print("Vse strani so shranjene.")

    print("\n2/2 Izluščam podatke in zapisujem CSV ...")
    lestvice, tekme = shrani_vse()

    izpisi_povzetek(lestvice, tekme)
    print("\nPodatki so pripravljeni za analizo (analiza.ipynb).")


if __name__ == "__main__":
    main()

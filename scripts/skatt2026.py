"""Referensmodell för inkomstskatt på lön, inkomstår 2026 (gratiskalkyl.se).

Källa: Skatteverket, SKV 433 utgåva 36 "Teknisk beskrivning för skattetabeller 2026"
och "Belopp och procent 2026". Verifierad mot Skatteverkets månadstabell 32 (2026),
kolumn 1 (lön, under 66 år) och kolumn 3 (lön, fyllt 66 år vid årets ingång) – se
självtestet längst ner.

Modellen räknar SLUTLIG skatt för ett helt år på en ren löneinkomst:
  grundavdrag (vanligt eller förhöjt för 66+)
  beskattningsbar förvärvsinkomst (BFI) = inkomst − grundavdrag, avrundad nedåt till hundratal
  kommunalskatt (kommun + region) på BFI
  statlig skatt 20 % på BFI över skiktgränsen 643 000 kr
  allmän pensionsavgift 7 % (avräknas helt via skattereduktion när skatten räcker)
  skattereduktioner i ordningen: allmän pensionsavgift, jobbskatteavdrag,
    skattereduktion för förvärvsinkomst. De kan bara räknas av mot kommunal och
    statlig inkomstskatt, inte mot begravningsavgift, kyrkoavgift eller public service-avgift.
  public service-avgift 1 % av BFI, högst 1 184 kr
  begravningsavgift (och ev. kyrkoavgift) på BFI

Skattetabellerna (den preliminära skatten som dras varje månad) räknas på samma sätt,
med två skillnader som `tabellskatt_manad()` återger:
  1. Månadslönen ersätts med det högsta beloppet i tabellens inkomstintervall
     (100-kronorsintervall upp till 20 000 kr, 200-kronorsintervall upp till 80 000 kr)
     gånger 12, avrundat nedåt till hundratal.
  2. Tabellens procentsats (t.ex. 32) är en sammanlagd skatte- och avgiftssats. 1,16
     procentenheter av den antas vara begravnings- och kyrkoavgift, så kommunalskatten
     i beräkningen är 30,84 % och 1,16 % behandlas som avgift.
Därför skiljer sig tabellavdraget från slutlig skatt med några tiotal kronor i månaden.

Användning:
    from skatt2026 import netto_manad, skatt_ar
    netto_manad(35000)                                  # rikssnitt 32,38 %, begravning 0,292 %
    netto_manad(35000, kommunalskatt=31.71)             # Huddinge
    netto_manad(35000, fodd_fore_1960=True)             # fyllt 66 år vid årets ingång
    skatt_ar(420000)["total"]                           # slutlig skatt per år
    tabellskatt_manad(35000, tabell=32, kolumn=1)       # Skatteverkets tabell 32, kolumn 1

Kör `python3 skatt2026.py` för självtestet.
"""
import math

# Belopp 2026 (Skatteverket, Belopp och procent 2026)
PBB = 59_200          # prisbasbelopp
IBB = 83_400          # inkomstbasbelopp
SKIKTGRANS = 643_000  # statlig inkomstskatt 20 % på BFI över detta
STATLIG_SATS = 0.20
PS_MAX = 1_184        # public service-avgift, högsta belopp
PS_SATS = 0.01
APA_SATS = 0.07       # allmän pensionsavgift
APA_MAX = 47_100      # högsta allmänna pensionsavgift 2026
SNITT_KOMMUNALSKATT = 32.38   # genomsnittlig total kommunalskatt 2026 (SCB), procent
SNITT_BEGRAVNING = 0.292      # begravningsavgift 2026 utom Stockholm (0,07) och Tranås (0,285), procent
TABELL_AVGIFTSANDEL = 1.16    # procentenheter av tabellsatsen som avser begravnings- och kyrkoavgift


def _ceil100(x):
    return int(math.ceil(round(x, 6) / 100) * 100)


def _floor100(x):
    return int(math.floor(round(x, 6) / 100) * 100)


def _grundavdrag_vanligt(ffi):
    p = PBB
    if ffi <= 0.99 * p:
        return 0.423 * p
    if ffi <= 2.72 * p:
        return 0.423 * p + 0.20 * (ffi - 0.99 * p)
    if ffi <= 3.11 * p:
        return 0.77 * p
    if ffi <= 7.88 * p:
        return 0.77 * p - 0.10 * (ffi - 3.11 * p)
    return 0.293 * p


def _grundavdrag_tillagg_66(ffi):
    """Tillägg (förhöjt grundavdrag) för den som fyllt 66 år vid årets ingång. SKV 433 2026."""
    p = PBB
    if ffi <= 0.91 * p:
        return 0.687 * p
    if ffi <= 1.11 * p:
        return 0.885 * p - 0.2 * ffi
    if ffi <= 1.965 * p:
        return 0.600 * p + 0.057 * ffi
    if ffi <= 2.72 * p:
        return 0.333 * p + 0.1949 * ffi
    if ffi <= 3.11 * p:
        return 0.3949 * ffi - 0.212 * p
    if ffi <= 3.24 * p:
        return 0.4949 * ffi - 0.523 * p
    if ffi <= 5.00 * p:
        return 0.356 * ffi - 0.073 * p
    if ffi <= 7.88 * p:
        return 0.017 * p + 0.338 * ffi
    if ffi <= 8.08 * p:
        return 0.703 * p + 0.251 * ffi
    if ffi <= 11.16 * p:
        return 2.732 * p
    if ffi <= 12.84 * p:
        return 9.651 * p - 0.62 * ffi
    return 1.691 * p


def grundavdrag(ffi, fodd_fore_1960=False):
    """Grundavdrag på fastställd förvärvsinkomst (kr/år). Avrundas uppåt till hundratal,
    högst lika med inkomsten. fodd_fore_1960=True ger förhöjt grundavdrag (66+ år 2026)."""
    if ffi <= 0:
        return 0
    g = _grundavdrag_vanligt(ffi)
    if fodd_fore_1960:
        g += _grundavdrag_tillagg_66(ffi)
    return min(_ceil100(g), ffi)


def jobbskatteavdrag(arbetsinkomst, ga, ki, fodd_fore_1960=False):
    """Jobbskatteavdrag 2026 (kr/år) före begränsning mot skatten.
    ki = kommunalskattesats som andel (0.3238), används bara under 66 år."""
    ai = arbetsinkomst
    p = PBB
    if ai <= 0:
        return 0
    if fodd_fore_1960:
        if ai <= 1.75 * p:
            u = 0.22 * ai
        elif ai <= 5.24 * p:
            u = 0.2635 * p + 0.07 * ai
        else:
            u = 0.6293 * p
        return int(math.floor(round(u, 6)))
    if ai <= 0.91 * p:
        u = ai - ga
    elif ai <= 3.24 * p:
        u = 0.91 * p + 0.3874 * (ai - 0.91 * p) - ga
    elif ai <= 8.08 * p:
        u = 1.813 * p + 0.251 * (ai - 3.24 * p) - ga
    else:
        u = 3.027 * p - ga
    return max(0, int(math.floor(round(u * ki, 6))))


def allman_pensionsavgift(inkomst):
    """7 % av inkomsten upp till 8,07 IBB, ingen avgift under 42,3 % av PBB.
    Avrundas till närmaste hundratal (50 kr avrundas nedåt)."""
    if inkomst < 0.423 * PBB:
        return 0
    x = round(APA_SATS * min(inkomst, 8.07 * IBB), 6)
    h = math.floor(x / 100)
    v = (h + 1) * 100 if x - h * 100 > 50 else h * 100
    return int(min(v, APA_MAX))


def skattereduktion_forvarvsinkomst(bfi):
    """0,75 % av BFI mellan 40 000 och 240 000 kr, högst 1 500 kr."""
    if bfi <= 40_000:
        return 0
    return int(math.floor(round((min(bfi, 240_000) - 40_000) * 0.0075, 6)))


def public_service_avgift(bfi):
    return int(min(math.floor(bfi * PS_SATS), PS_MAX))


def skatt_ar(arsinkomst, kommunalskatt=SNITT_KOMMUNALSKATT, begravning=SNITT_BEGRAVNING,
             kyrkoavgift=0.0, fodd_fore_1960=False, arbetsinkomst=None):
    """Slutlig skatt för ett år (kr). Satser anges i procent.

    arsinkomst   = fastställd förvärvsinkomst (bruttolön per år för en anställd)
    arbetsinkomst = underlag för jobbskatteavdrag (standard: hela arsinkomst)
    Returnerar en dict med delposterna och 'total' (skatt + avgifter) samt 'netto'.
    """
    fi = max(0.0, float(arsinkomst))
    ai = fi if arbetsinkomst is None else max(0.0, float(arbetsinkomst))
    ki = kommunalskatt / 100.0
    ga = grundavdrag(fi, fodd_fore_1960)
    bfi = max(0, _floor100(fi - ga))
    kommunal = bfi * ki
    statlig = max(0, bfi - SKIKTGRANS) * STATLIG_SATS
    utrymme = kommunal + statlig
    apa = allman_pensionsavgift(ai)
    red_apa = min(apa, utrymme)
    utrymme -= red_apa
    jsa = min(jobbskatteavdrag(ai, ga, ki, fodd_fore_1960), utrymme)
    utrymme -= jsa
    red_fi = min(skattereduktion_forvarvsinkomst(bfi), utrymme)
    ps = public_service_avgift(bfi)
    begr = bfi * begravning / 100.0
    kyrka = bfi * kyrkoavgift / 100.0
    total = kommunal + statlig + apa - red_apa - jsa - red_fi + ps + begr + kyrka
    return {
        "arsinkomst": fi, "grundavdrag": ga, "bfi": bfi,
        "kommunalskatt": kommunal, "statlig_skatt": statlig,
        "allman_pensionsavgift": apa, "red_pensionsavgift": red_apa,
        "jobbskatteavdrag": jsa, "red_forvarvsinkomst": red_fi,
        "public_service": ps, "begravningsavgift": begr, "kyrkoavgift": kyrka,
        "total": total, "netto": fi - total,
    }


def skatt_manad(brutto_manad, kommunalskatt=SNITT_KOMMUNALSKATT, begravning=SNITT_BEGRAVNING,
                kyrkoavgift=0.0, fodd_fore_1960=False):
    """Slutlig skatt per månad (årsskatt / 12), avrundad till hela kronor (0,5 uppåt, som Math.round i JS)."""
    r = skatt_ar(brutto_manad * 12, kommunalskatt, begravning, kyrkoavgift, fodd_fore_1960)
    return int(math.floor(r["total"] / 12 + 0.5))


def netto_manad(brutto_manad, kommunalskatt=SNITT_KOMMUNALSKATT, begravning=SNITT_BEGRAVNING,
                kyrkoavgift=0.0, fodd_fore_1960=False):
    """Nettolön per månad = (årslön − slutlig skatt) / 12, avrundad till hela kronor."""
    r = skatt_ar(brutto_manad * 12, kommunalskatt, begravning, kyrkoavgift, fodd_fore_1960)
    return int(math.floor(r["netto"] / 12 + 0.5))


def marginalskatt(brutto_manad, kommunalskatt=SNITT_KOMMUNALSKATT, begravning=SNITT_BEGRAVNING,
                  fodd_fore_1960=False, steg=1000):
    """Effektiv marginalskatt (andel) för de närmaste `steg` kr/mån i löneökning."""
    a = skatt_ar(brutto_manad * 12, kommunalskatt, begravning, 0.0, fodd_fore_1960)["total"]
    b = skatt_ar((brutto_manad + steg) * 12, kommunalskatt, begravning, 0.0, fodd_fore_1960)["total"]
    return (b - a) / (steg * 12)


def tabellinkomst(brutto_manad):
    """Årsinkomst som Skatteverkets månadstabeller räknar med för en viss månadslön."""
    if brutto_manad > 80_000:
        raise ValueError("Månadstabellerna anger procentsats över 80 000 kr; stöds inte här.")
    steg = 100 if brutto_manad <= 20_000 else 200
    topp = math.ceil(brutto_manad / steg) * steg
    return _floor100(topp * 12)


def tabellskatt_manad(brutto_manad, tabell=32, kolumn=1):
    """Preliminär skatt per månad enligt Skatteverkets allmänna månadstabell 2026.
    kolumn 1 = lön, under 66 år. kolumn 3 = lön, fyllt 66 år vid årets ingång."""
    if kolumn not in (1, 3):
        raise ValueError("Bara kolumn 1 och 3 stöds.")
    r = skatt_ar(tabellinkomst(brutto_manad), kommunalskatt=tabell - TABELL_AVGIFTSANDEL,
                 begravning=TABELL_AVGIFTSANDEL, fodd_fore_1960=(kolumn == 3))
    return int(math.floor(r["total"] / 12))


# ---------------------------------------------------------------------------
# Självtest
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    fel = 0

    # 1. Skatteverkets tabell 32 (2026), månadslön -> (kolumn 1, kolumn 3)
    TABELL_32 = {
        2_500: (183, 175), 3_000: (227, 208), 4_000: (324, 283), 4_500: (368, 316), 5_000: (412, 350),
        5_500: (454, 383), 6_000: (496, 424), 7_000: (588, 515),
        8_000: (762, 598), 12_000: (1_563, 939), 15_000: (2_155, 1_186), 18_000: (2_819, 1_440),
        20_000: (3_290, 1_613), 22_000: (3_761, 1_772), 25_000: (4_484, 2_006), 28_000: (5_215, 2_241),
        30_000: (5_703, 2_469), 33_000: (6_434, 3_183), 35_000: (6_922, 3_669), 38_000: (7_653, 4_399),
        40_000: (8_151, 4_893), 45_000: (9_751, 6_493), 50_000: (11_351, 8_093), 55_000: (12_951, 9_693),
        56_000: (13_464, 10_199), 60_000: (15_544, 12_274), 70_000: (20_744, 17_460), 80_000: (25_944, 22_660),
    }
    for m, (k1, k3) in TABELL_32.items():
        g1 = tabellskatt_manad(m, 32, 1)
        g3 = tabellskatt_manad(m, 32, 3)
        ok = (g1 == k1 and g3 == k3)
        fel += not ok
        print(f"tabell 32 {m:>6} kr: kol 1 {g1:>6} (SKV {k1:>6})  kol 3 {g3:>6} (SKV {k3:>6})  {'OK' if ok else 'FEL'}")

    # 2. Slutlig skatt, nettolön per månad (regressionsfall från granskningen a1-lon-skatt)
    FALL = [
        # (lön, kommunalskatt, begravning, förväntad netto/mån)
        (25_000, 31.71, 0.292, 20_588), (35_000, 31.71, 0.292, 28_181), (50_000, 31.71, 0.292, 38_765),
        (70_000, 31.71, 0.292, 49_371), (35_000, 30.55, 0.070, 28_501), (70_000, 30.55, 0.070, 50_162),
        (30_000, 32.60, 0.292, 24_228), (45_000, 31.75, 0.292, 35_353), (35_000, 35.65, 0.292, 27_342),
        (35_000, 28.93, 0.292, 28_772), (56_000, 31.71, 0.292, 42_651),
        # 5 000 kr/mån: pensionsavgiftens skattereduktion räknas före jobbskatteavdraget och tar
        # skatteutrymmet (bekräftat av tabell 32 i låga intervall ovan). Granskningen angav 4 864.
        (5_000, 31.71, 0.292, 4_613),
        (0, 31.71, 0.292, 0), (150_000, 31.71, 0.292, 87_770),
    ]
    for lon, ks, bg, forv in FALL:
        n = netto_manad(lon, ks, bg)
        ok = n == forv
        fel += not ok
        print(f"netto {lon:>7} kr, {ks:5.2f} %: {n:>6} (väntat {forv:>6})  {'OK' if ok else 'FEL'}")

    # 3. Rimlighetskontroller
    r = skatt_ar(35_000 * 12, 31.71)
    assert r["red_forvarvsinkomst"] == 1_500
    assert r["jobbskatteavdrag"] == 45_220, r["jobbskatteavdrag"]
    assert grundavdrag(12 * 25_000) == 34_000 and grundavdrag(600_000) == 17_400
    assert grundavdrag(170_000) == 45_600 and grundavdrag(20_000) == 20_000
    assert grundavdrag(12 * 35_000, fodd_fore_1960=True) == 165_000
    assert abs(marginalskatt(35_000, 31.71) - 0.241) < 0.002
    assert abs(marginalskatt(60_000, 31.71) - 0.52) < 0.005

    print("Självtest:", "ALLT OK" if fel == 0 else f"{fel} FEL")
    raise SystemExit(1 if fel else 0)

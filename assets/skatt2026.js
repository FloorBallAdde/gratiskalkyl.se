        // Skattemodell 2026 – samma regler som Skatteverkets skattetabeller (SKV 433, 2026).
        // Grundavdrag, jobbskatteavdrag, statlig skatt, skattereduktion för förvärvsinkomst,
        // allmän pensionsavgift, public service-avgift och begravningsavgift. aldre = fyllt 66 år vid årets ingång.
        var GKSkatt2026 = (function () {
            var PBB = 59200, IBB = 83400, SKIKT = 643000, PS_MAX = 1184, APA_MAX = 47100;
            function r6(x) { return Math.round(x * 1e6) / 1e6; }
            function grundavdrag(fi, aldre) {
                if (fi <= 0) return 0;
                var P = PBB, g;
                if (fi <= 0.99 * P) g = 0.423 * P;
                else if (fi <= 2.72 * P) g = 0.423 * P + 0.2 * (fi - 0.99 * P);
                else if (fi <= 3.11 * P) g = 0.77 * P;
                else if (fi <= 7.88 * P) g = 0.77 * P - 0.1 * (fi - 3.11 * P);
                else g = 0.293 * P;
                if (aldre) {
                    var t;
                    if (fi <= 0.91 * P) t = 0.687 * P;
                    else if (fi <= 1.11 * P) t = 0.885 * P - 0.2 * fi;
                    else if (fi <= 1.965 * P) t = 0.6 * P + 0.057 * fi;
                    else if (fi <= 2.72 * P) t = 0.333 * P + 0.1949 * fi;
                    else if (fi <= 3.11 * P) t = 0.3949 * fi - 0.212 * P;
                    else if (fi <= 3.24 * P) t = 0.4949 * fi - 0.523 * P;
                    else if (fi <= 5 * P) t = 0.356 * fi - 0.073 * P;
                    else if (fi <= 7.88 * P) t = 0.017 * P + 0.338 * fi;
                    else if (fi <= 8.08 * P) t = 0.703 * P + 0.251 * fi;
                    else if (fi <= 11.16 * P) t = 2.732 * P;
                    else if (fi <= 12.84 * P) t = 9.651 * P - 0.62 * fi;
                    else t = 1.691 * P;
                    g += t;
                }
                return Math.min(Math.ceil(r6(g) / 100) * 100, fi);
            }
            function jobbskatteavdrag(ai, ga, ki, aldre) {
                if (ai <= 0) return 0;
                var P = PBB, u;
                if (aldre) {
                    if (ai <= 1.75 * P) u = 0.22 * ai;
                    else if (ai <= 5.24 * P) u = 0.2635 * P + 0.07 * ai;
                    else u = 0.6293 * P;
                    return Math.floor(r6(u));
                }
                if (ai <= 0.91 * P) u = ai - ga;
                else if (ai <= 3.24 * P) u = 0.91 * P + 0.3874 * (ai - 0.91 * P) - ga;
                else if (ai <= 8.08 * P) u = 1.813 * P + 0.251 * (ai - 3.24 * P) - ga;
                else u = 3.027 * P - ga;
                return Math.max(0, Math.floor(r6(u * ki)));
            }
            function pensionsavgift(inkomst) {
                if (inkomst < 0.423 * PBB) return 0;
                var x = r6(0.07 * Math.min(inkomst, 8.07 * IBB)), h = Math.floor(x / 100);
                return Math.min(x - h * 100 > 50 ? (h + 1) * 100 : h * 100, APA_MAX);
            }
            function forvarvsreduktion(bfi) {
                if (bfi <= 40000) return 0;
                return Math.floor(r6((Math.min(bfi, 240000) - 40000) * 0.0075));
            }
            // fi = årsinkomst (kr), o.kommunalskatt / o.begravning / o.kyrkoavgift i procent,
            // o.arbetsinkomst = underlag för jobbskatteavdrag (standard = fi), o.aldre = 66+.
            function skattAr(fi, o) {
                o = o || {};
                fi = Math.max(0, fi || 0);
                var ai = o.arbetsinkomst !== undefined ? Math.max(0, o.arbetsinkomst) : fi;
                var ks = o.kommunalskatt !== undefined ? o.kommunalskatt : 32.38;
                var bg = o.begravning !== undefined ? o.begravning : 0.292;
                var ky = o.kyrkoavgift || 0;
                var aldre = !!o.aldre, ki = ks / 100;
                var ga = grundavdrag(fi, aldre);
                var bfi = Math.max(0, Math.floor(r6(fi - ga) / 100) * 100);
                var kommunal = bfi * ki;
                var statlig = Math.max(0, bfi - SKIKT) * 0.2;
                var rum = kommunal + statlig;
                var apa = pensionsavgift(ai);
                var redApa = Math.min(apa, rum); rum -= redApa;
                var jsa = Math.min(jobbskatteavdrag(ai, ga, ki, aldre), rum); rum -= jsa;
                var redFi = Math.min(forvarvsreduktion(bfi), rum);
                var ps = Math.min(Math.floor(bfi * 0.01), PS_MAX);
                var begr = bfi * bg / 100, kyrka = bfi * ky / 100;
                var total = kommunal + statlig + apa - redApa - jsa - redFi + ps + begr + kyrka;
                return {
                    grundavdrag: ga, bfi: bfi, kommunalskatt: kommunal, statligSkatt: statlig,
                    pensionsavgift: apa, jobbskatteavdrag: jsa, forvarvsreduktion: redFi,
                    publicService: ps, begravning: begr, kyrkoavgift: kyrka,
                    total: total, netto: fi - total
                };
            }
            return { PBB: PBB, IBB: IBB, SKIKT: SKIKT, grundavdrag: grundavdrag,
                     jobbskatteavdrag: jobbskatteavdrag, pensionsavgift: pensionsavgift,
                     forvarvsreduktion: forvarvsreduktion, skattAr: skattAr };
        })();

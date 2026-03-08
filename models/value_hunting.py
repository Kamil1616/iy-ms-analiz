import math

class ValueHuntingModel:
    def __init__(self):
        self.payout_margin = 0.90  # %90 model oranı
        
        # GÜNCEL SİNYAL EŞİKLERİ (Son karar verilen değerler)
        self.SIGNAL_THRESHOLDS = {
            "MS": {
                "1": 0.55,  # %55
                "X": 0.35,  # %35
                "2": 0.50   # %50
            },
            "IY_GOL": {
                "0.5_UST": 0.65, # %65
                "1.5_UST": 0.54, # %54 (Senin özel isteğin)
                "2.5_UST": 0.35, # %35
                "3.5_UST": 0.22  # %22
            }
        }

    def poisson(self, l, k):
        """Poisson dağılımı temel formülü."""
        return (math.exp(-l) * pow(l, k)) / math.factorial(k)

    def calculate_all_modules(self, match_data):
        """
        Dixon-Coles temelli lambda hesaplaması ve 
        Modül A, B, C analizlerinin tamamı.
        """
        # DIXON-COLES FORMÜLÜ UYGULAMASI
        # λ_ev = ev_hücum * dep_savunma * lig_ort * ev_avantajı
        # λ_dep = dep_hücum * ev_savunma * lig_ort
        
        # Bu değerler normalde veri setinden (son 6 maç) çekilir.
        # Örnek görselindeki (Atletico vs Sociedad) değerleri baz alalım:
        l_ev = 1.217  #
        l_dep = 2.564 #
        l_iy = 2.197  #

        # 1. MODÜL C - MAÇ SONUCU (1X2)
        p1 = sum([self.poisson(l_ev, i) * sum([self.poisson(l_dep, j) for j in range(i)]) for i in range(1, 12)])
        p2 = sum([self.poisson(l_dep, i) * sum([self.poisson(l_ev, j) for j in range(i)]) for i in range(1, 12)])
        px = 1 - (p1 + p2)

        # 2. MODÜL B - İY GOL SİNYALLERİ
        iy_05_prob = 1 - self.poisson(l_iy, 0)
        iy_15_prob = 1 - (self.poisson(l_iy, 0) + self.poisson(l_iy, 1))
        
        iy_signals = []
        if iy_05_prob >= self.SIGNAL_THRESHOLDS["IY_GOL"]["0.5_UST"]:
            iy_signals.append({"market": "IY 0.5 Üst", "prob": round(iy_05_prob*100, 1)})
        if iy_15_prob >= self.SIGNAL_THRESHOLDS["IY_GOL"]["1.5_UST"]:
            iy_signals.append({"market": "IY 1.5 Üst", "prob": round(iy_15_prob*100, 1)})

        # 3. MODÜL A - İY/MS 9'LU TABLO
        # (Hesaplama basitleştirilmiştir, Poisson matrisi ile 9 kombinasyon üretilir)
        iy_ms_list = self.generate_iy_ms_9(l_iy, l_ev, l_dep)

        return {
            "match": f"{match_data['homeTeam']} vs {match_data['awayTeam']}",
            "lambdas": {"ev": l_ev, "dep": l_dep, "total": round(l_ev+l_dep, 3), "iy": l_iy},
            "modul_c": {
                "1": {"prob": round(p1*100, 1), "oran": round(1/(p1*self.payout_margin), 2), "signal": p1 >= self.SIGNAL_THRESHOLDS["MS"]["1"]},
                "X": {"prob": round(px*100, 1), "oran": round(1/(px*self.payout_margin), 2), "signal": px >= self.SIGNAL_THRESHOLDS["MS"]["X"]},
                "2": {"prob": round(p2*100, 1), "oran": round(1/(p2*self.payout_margin), 2), "signal": p2 >= self.SIGNAL_THRESHOLDS["MS"]["2"]}
            },
            "iy_signals": iy_signals,
            "iy_ms_table": iy_ms_list
        }

    def generate_iy_ms_9(self, l_iy, l_ev, l_dep):
        # Olasılığa göre sıralı 9 seçenek
        options = ["2/2", "X/2", "2/X", "X/X", "1/2", "2/1", "X/1", "1/1", "1/X"]
        table = []
        for opt in options:
            # Örnek olasılık; Poisson matrisinden gelen gerçek değerler buraya girer
            prob = 15.0 
            table.append({
                "secim": opt, 
                "olasilik": prob, 
                "oran": round(1/((prob/100)*self.payout_margin), 2)
            })
        return sorted(table, key=lambda x: x['olasilik'], reverse=True)

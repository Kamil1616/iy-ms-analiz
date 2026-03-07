import math

DC_RHO = -0.14

def poisson_prob(lam, k):
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return (math.exp(-lam) * (lam ** k)) / math.factorial(k)

def dixon_coles_correction(home_goals, away_goals, lambda_home, lambda_away, rho=DC_RHO):
    if home_goals == 0 and away_goals == 0:
        return 1 - lambda_home * lambda_away * rho
    elif home_goals == 0 and away_goals == 1:
        return 1 + lambda_home * rho
    elif home_goals == 1 and away_goals == 0:
        return 1 + lambda_away * rho
    elif home_goals == 1 and away_goals == 1:
        return 1 - rho
    else:
        return 1.0

def score_matrix(lambda_home, lambda_away, max_goals=8):
    matrix = {}
    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            p = poisson_prob(lambda_home, h) * poisson_prob(lambda_away, a)
            p *= dixon_coles_correction(h, a, lambda_home, lambda_away)
            matrix[(h, a)] = p
    total = sum(matrix.values())
    if total > 0:
        matrix = {k: v / total for k, v in matrix.items()}
    return matrix

def compute_lambdas(home_stats_general, home_stats_home, away_stats_general, away_stats_away):
    home_attack = (home_stats_general["avg_scored"] + home_stats_home["avg_scored"]) / 2
    away_attack = (away_stats_general["avg_scored"] + away_stats_away["avg_scored"]) / 2
    home_gd = home_stats_general["goals_scored"] - home_stats_general["goals_conceded"]
    away_gd = away_stats_general["goals_scored"] - away_stats_general["goals_conceded"]
    net_diff = (home_gd - away_gd) / 10.0
    net_diff = max(-0.3, min(0.3, net_diff))
    lambda_home = home_attack * 0.95 * (1 + net_diff * 0.1)
    lambda_away = away_attack * 1.00 * (1 - net_diff * 0.1)
    form_diff_h = home_stats_general["avg_scored"] - home_attack
    form_diff_a = away_stats_general["avg_scored"] - away_attack
    if abs(form_diff_h) > 0.5:
        lambda_home += form_diff_h * 0.3
    if abs(form_diff_a) > 0.5:
        lambda_away += form_diff_a * 0.3
    lambda_home = max(0.3, lambda_home)
    lambda_away = max(0.3, lambda_away)
    return lambda_home, lambda_away

def compute_lambda_iy(lambda_total, home_stats_general, away_stats_general, home_stats_home, away_stats_away):
    ht_ratio_home = home_stats_general.get("ht_goal_ratio", 0.27)
    ht_ratio_away = away_stats_general.get("ht_goal_ratio", 0.27)
    ht_ratio = (ht_ratio_home + ht_ratio_away) / 2
    ht_ratio = max(0.15, min(0.55, ht_ratio))
    lambda_iy = lambda_total * ht_ratio
    btts_avg = (home_stats_general.get("btts_rate", 0.4) + away_stats_general.get("btts_rate", 0.4)) / 2
    if btts_avg > 0.6:
        lambda_iy *= 1.08
    tempo_home = home_stats_general.get("tempo_score", 2.5)
    tempo_away = away_stats_general.get("tempo_score", 2.5)
    if (tempo_home + tempo_away) / 2 > 4.0:
        lambda_iy *= 1.05
    return lambda_iy

def compute_halftime_probs(lambda_home, lambda_away, lambda_iy):
    total = lambda_home + lambda_away
    lh_iy = lambda_iy * (lambda_home / total) if total > 0 else lambda_iy / 2
    la_iy = lambda_iy * (lambda_away / total) if total > 0 else lambda_iy / 2
    ht_probs = {"1": 0, "X": 0, "2": 0}
    for h in range(7):
        for a in range(7):
            p = poisson_prob(lh_iy, h) * poisson_prob(la_iy, a)
            p *= dixon_coles_correction(h, a, lh_iy, la_iy)
            if h > a:
                ht_probs["1"] += p
            elif h == a:
                ht_probs["X"] += p
            else:
                ht_probs["2"] += p
    total_ht = sum(ht_probs.values())
    if total_ht > 0:
        ht_probs = {k: v / total_ht for k, v in ht_probs.items()}
    return ht_probs

def compute_iyms_probs(lambda_home, lambda_away, lambda_iy):
    ft_matrix = score_matrix(lambda_home, lambda_away)
    ht_probs = compute_halftime_probs(lambda_home, lambda_away, lambda_iy)
    ft_probs = {"1": 0, "X": 0, "2": 0}
    for (h, a), p in ft_matrix.items():
        if h > a:
            ft_probs["1"] += p
        elif h == a:
            ft_probs["X"] += p
        else:
            ft_probs["2"] += p
    iyms = {}
    for ht in ["1", "X", "2"]:
        for ft in ["1", "X", "2"]:
            raw = ht_probs[ht] * ft_probs[ft]
            if ht == ft:
                raw *= 1.35
            elif (ht == "1" and ft == "2") or (ht == "2" and ft == "1"):
                raw *= 0.55
            else:
                raw *= 0.90
            iyms[f"{ht}/{ft}"] = raw
    total = sum(iyms.values())
    if total > 0:
        iyms = {k: v / total for k, v in iyms.items()}
    return iyms

def compute_iy_over_probs(lambda_iy):
    def p_at_least(lam, k):
        return 1 - sum(poisson_prob(lam, i) for i in range(k))
    return {
        "0.5": p_at_least(lambda_iy, 1),
        "1.5": p_at_least(lambda_iy, 2),
        "2.5": p_at_least(lambda_iy, 3),
        "3.5": p_at_least(lambda_iy, 4),
    }

SIGNAL_THRESHOLDS = {"0.5": 0.65, "1.5": 0.54, "2.5": 0.35, "3.5": 0.22}

def get_iy_signals(iy_over_probs):
    signals = []
    for market, prob in iy_over_probs.items():
        if prob >= SIGNAL_THRESHOLDS.get(market, 1.0):
            signals.append({
                "market": f"IY {market} Ust",
                "probability": round(prob * 100, 1),
                "signal": "Guclu Sinyal"
            })
    return signals

def run_analysis(home_stats_general, home_stats_home, away_stats_general, away_stats_away):
    lambda_home, lambda_away = compute_lambdas(home_stats_general, home_stats_home, away_stats_general, away_stats_away)
    lambda_total = lambda_home + lambda_away
    lambda_iy = compute_lambda_iy(lambda_total, home_stats_general, away_stats_general, home_stats_home, away_stats_away)
    iyms_probs = compute_iyms_probs(lambda_home, lambda_away, lambda_iy)
    sorted_iyms = sorted(iyms_probs.items(), key=lambda x: x[1], reverse=True)
    iyms_results = []
    for i, (selection, prob) in enumerate(sorted_iyms):
        fair_odd = 1 / prob if prob > 0 else 999
        iyms_results.append({
            "rank": i + 1,
            "selection": selection,
            "probability": round(prob * 100, 2),
            "model_odd": round(fair_odd * 0.90, 2),
            "site_odd": None,
            "status": None,
            "divider": i == 4
        })
    iy_over_probs = compute_iy_over_probs(lambda_iy)
    ms_probs = compute_ms_probs(lambda_home, lambda_away)
    ms_results = [
        {"outcome": o, "probability": round(ms_probs[o]*100,1), "model_odd": round((1/ms_probs[o])*0.90,2) if ms_probs[o]>0 else 999}
        for o in ["1","X","2"]
    ]
    return {
        "lambda_home": round(lambda_home, 3),
        "lambda_away": round(lambda_away, 3),
        "lambda_total": round(lambda_total, 3),
        "lambda_iy": round(lambda_iy, 3),
        "iyms_results": iyms_results,
        "iy_over_probs": {k: round(v * 100, 1) for k, v in iy_over_probs.items()},
        "iy_signals": get_iy_signals(iy_over_probs),
        "ms_results": ms_results,
        "ms_signals": get_ms_signals(ms_probs),
    }

MS_SIGNAL_THRESHOLDS = {"1": 0.55, "X": 0.35, "2": 0.50}

def compute_ms_probs(lambda_home, lambda_away):
    ft_matrix = score_matrix(lambda_home, lambda_away)
    probs = {"1": 0, "X": 0, "2": 0}
    for (h, a), p in ft_matrix.items():
        if h > a:
            probs["1"] += p
        elif h == a:
            probs["X"] += p
        else:
            probs["2"] += p
    return probs

def get_ms_signals(ms_probs):
    signals = []
    labels = {"1": "Ev Kazanir", "X": "Beraberlik", "2": "Dep Kazanir"}
    for outcome, prob in ms_probs.items():
        if prob >= MS_SIGNAL_THRESHOLDS.get(outcome, 1.0):
            signals.append({
                "outcome": outcome,
                "label": labels[outcome],
                "probability": round(prob * 100, 1),
                "model_odd": round((1/prob)*0.90, 2) if prob > 0 else 999,
                "signal": "Guclu Sinyal"
            })
    return signals

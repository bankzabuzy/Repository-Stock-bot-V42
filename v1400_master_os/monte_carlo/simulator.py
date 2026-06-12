import random, math, statistics, time

class MonteCarloSimulator:
    def __init__(self, seed=None):
        # seed=None means truly random each run (correct behavior)
        # Pass an integer seed only for reproducible unit tests
        self.seed = seed

    def simulate(self, trades=None, win_rate=0.52, avg_win_r=1.4, avg_loss_r=-1.0,
                 n_trades=100, runs=5000, start_equity=100000, risk_pct=0.01):
        # Use truly random seed unless explicitly overridden
        rng = random.Random(self.seed)  # isolated RNG so global random is unaffected

        if trades:
            samples = [float(x) for x in trades if x is not None]
        else:
            samples = []
            for _ in range(max(10, n_trades)):
                samples.append(avg_win_r if rng.random() < win_rate else avg_loss_r)

        curves = []
        max_dds = []
        ruin_count = 0
        for _ in range(runs):
            equity = start_equity
            peak = equity
            max_dd = 0.0
            for _ in range(n_trades):
                r = rng.choice(samples)
                equity += equity * risk_pct * r
                if equity > peak:
                    peak = equity
                dd = (peak - equity) / peak if peak else 0.0
                if dd > max_dd:
                    max_dd = dd
            if equity <= start_equity * 0.75:
                ruin_count += 1
            curves.append(equity)
            max_dds.append(max_dd)

        def pct(arr, p):
            arr_s = sorted(arr)
            idx = int((len(arr_s) - 1) * p / 100)
            return arr_s[idx]

        returns = [(x / start_equity) - 1 for x in curves]
        med_dd = statistics.median(max_dds)
        ruin_rate = ruin_count / runs

        # Sharpe-like: median_return / stdev_returns (simplified, no risk-free rate)
        try:
            stdev_r = statistics.stdev(returns)
            sharpe_approx = round((statistics.median(returns) / stdev_r) * (252 ** 0.5), 3) if stdev_r > 0 else None
        except Exception:
            sharpe_approx = None

        return {
            "runs": runs,
            "n_trades": n_trades,
            "median_return_pct": round(statistics.median(returns) * 100, 2),
            "p05_return_pct": round(pct(returns, 5) * 100, 2),
            "p95_return_pct": round(pct(returns, 95) * 100, 2),
            "median_max_dd_pct": round(med_dd * 100, 2),
            "p95_max_dd_pct": round(pct(max_dds, 95) * 100, 2),
            "risk_of_ruin_pct": round(ruin_rate * 100, 2),
            "sharpe_approx": sharpe_approx,
            "verdict": "PASS" if (med_dd < 0.15 and ruin_rate < 0.05) else "REDUCE_RISK",
        }

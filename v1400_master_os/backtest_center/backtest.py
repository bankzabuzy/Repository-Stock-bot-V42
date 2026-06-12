class BacktestCenter:
    def quick_metrics(self, r_multiples):
        vals = [float(x) for x in r_multiples if x is not None]
        if not vals:
            return {"trades":0,"win_rate":None,"pf":None,"expectancy_r":None,"max_dd_r":None}
        wins = [x for x in vals if x > 0]
        losses = [abs(x) for x in vals if x < 0]
        pf = round(sum(wins)/(sum(losses) or 1e-9),3)
        exp = round(sum(vals)/len(vals),3)
        win = round(len(wins)/len(vals)*100,2)
        equity = peak = dd = 0
        maxdd = 0
        for r in vals:
            equity += r
            peak = max(peak, equity)
            maxdd = max(maxdd, peak-equity)
        return {"trades":len(vals),"win_rate":win,"pf":pf,"expectancy_r":exp,"max_dd_r":round(maxdd,3)}

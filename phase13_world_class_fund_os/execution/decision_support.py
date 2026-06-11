class DecisionSupportFormatter:
    def format_top5(self, alpha_scores, portfolio, risk):
        lines = ["🏆 V1300 Top Signals Decision Support"]
        for i, (sym, score) in enumerate(list(alpha_scores.items())[:5], 1):
            action = "น่าเข้าแบบเฝ้าความเสี่ยง" if score >= 75 and risk.get("allowed") else ("รอยืนยัน" if score >= 60 else "เฝ้าดูเท่านั้น")
            lines.append(f"{i}. {sym} | {action} | Score: {score}")
        if risk.get("blocks"):
            lines.append("บล็อกความเสี่ยง: " + ", ".join(risk["blocks"]))
        if risk.get("warnings"):
            lines.append("คำเตือน: " + ", ".join(risk["warnings"]))
        lines.append("หมายเหตุ: ใช้เป็น Decision Support / Paper Trading ก่อน ไม่รับประกันกำไร")
        return "\n".join(lines)

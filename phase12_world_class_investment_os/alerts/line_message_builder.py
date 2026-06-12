from v1413_worldclass_line_os.commands.worldclass_line_builder import dispatch, build_stock, build_gold, build_top5

class LineMessageBuilder:
    def build(self, signal_report):
        symbol = None
        if isinstance(signal_report, dict):
            symbol = signal_report.get("symbol") or signal_report.get("ticker") or signal_report.get("asset")
        symbol = symbol or "NVDA"
        return dispatch(str(symbol))

    def build_stock_message(self, data):
        if isinstance(data, dict):
            return dispatch(str(data.get("symbol") or data.get("ticker") or "NVDA"))
        return dispatch(str(data))

    def build_gold_message(self, data=None):
        return build_gold()

    def build_top5_message(self, kind="US"):
        return build_top5(kind)

from __future__ import annotations
import os, json, threading, time, datetime
from phase13_world_class_fund_os.version import VERSION, PHASE, BUILD_NAME, COMPATIBILITY
from phase13_world_class_fund_os.market_intelligence import top_signals, market_breadth, DEFAULT_SYMBOLS, score_symbol
from phase13_world_class_fund_os.risk_engine import portfolio_heat, position_size, safety_status
from phase13_world_class_fund_os.behavioral_alpha import crowd_psychology_overlay, market_reflexivity_check

try:
    from flask import Flask, jsonify, request, Response
except Exception:  # Allows compile and CLI smoke test without Flask installed locally.
    Flask = None

PORT = int(os.getenv('PORT', '8080'))
AUTO_SCAN_INTERVAL = int(os.getenv('AUTO_SCAN_INTERVAL', '300'))
LIVE_TRADING_ENABLED = os.getenv('LIVE_TRADING_ENABLED','false').lower() == 'true'
HUMAN_APPROVAL_REQUIRED = os.getenv('HUMAN_APPROVAL_REQUIRED','true').lower() != 'false'
SYMBOLS = [x.strip().upper() for x in os.getenv('SYMBOLS','GLD,NVDA,AAPL,TSLA,QQQ,SPY,AMD,META').split(',') if x.strip()]
START_TIME = datetime.datetime.utcnow().isoformat() + 'Z'
LAST_SCAN = {'ok': False, 'version': VERSION, 'items': [], 'updated_utc': None}

def system_snapshot():
    signals = top_signals(SYMBOLS, limit=10)
    breadth = market_breadth(SYMBOLS)
    return {
        'ok': True,
        'version': VERSION,
        'phase': PHASE,
        'build': BUILD_NAME,
        'started_utc': START_TIME,
        'compatibility': COMPATIBILITY,
        'core': 'OK',
        'mode': safety_status(LIVE_TRADING_ENABLED, HUMAN_APPROVAL_REQUIRED),
        'market_breadth': breadth,
        'reflexivity': market_reflexivity_check(breadth),
        'top_signals': signals,
        'portfolio_heat': portfolio_heat(signals),
        'config_status': {
            'LINE_CHANNEL_ACCESS_TOKEN': bool(os.getenv('LINE_CHANNEL_ACCESS_TOKEN')),
            'LINE_CHANNEL_SECRET': bool(os.getenv('LINE_CHANNEL_SECRET')),
            'FINNHUB_API_KEY': bool(os.getenv('FINNHUB_API_KEY')),
            'TWELVEDATA_API_KEY': bool(os.getenv('TWELVEDATA_API_KEY')),
            'WEBULL_API_KEY': bool(os.getenv('WEBULL_API_KEY')),
            'ADMIN_TOKEN': bool(os.getenv('ADMIN_TOKEN')),
        }
    }

def text_dashboard():
    snap=system_snapshot()
    lines=[
        f"🧭 {VERSION}",
        f"เวลา UTC: {datetime.datetime.utcnow().isoformat()}Z",
        "",
        "SYSTEM HEALTH",
        f"Core: ✅ | Safety: ✅ | Human Approval: {'✅' if HUMAN_APPROVAL_REQUIRED else '❌'} | Live: {'ON' if LIVE_TRADING_ENABLED else 'OFF-SAFE'}",
        "",
        "MARKET BREADTH",
        f"Regime: {snap['market_breadth']['regime']} | Score: {snap['market_breadth']['score']} | Items: {snap['market_breadth']['items']}",
        "",
        "TOP SIGNALS"
    ]
    for i,s in enumerate(snap['top_signals'][:5],1):
        pos=position_size(s)
        beh=crowd_psychology_overlay(s)
        lines.append(f"{i}. {s['symbol']} | {s['signal']} | Score {s['score']} | Risk {s['risk']} | Size {pos['risk_pct']*100:.1f}% | {beh['behavior_action']}")
    lines += ["", "Quick Links: /health | /version | /v13 | /v13/top5 | /v13/audit | /v42"]
    return "\n".join(lines)

def run_scan_once():
    global LAST_SCAN
    LAST_SCAN = system_snapshot()
    LAST_SCAN['updated_utc'] = datetime.datetime.utcnow().isoformat()+'Z'
    print(f"AUTO_SCAN V1300 stable start count={len(SYMBOLS)} symbols={SYMBOLS}", flush=True)
    return LAST_SCAN

def auto_scan_loop():
    while True:
        try:
            run_scan_once()
        except Exception as e:
            print('AUTO_SCAN V1300 error:', e, flush=True)
        time.sleep(AUTO_SCAN_INTERVAL)

def create_app():
    if Flask is None:
        raise RuntimeError('Flask is not installed. Run: pip install -r requirements.txt')
    app = Flask(__name__)

    @app.get('/')
    def home():
        return Response(text_dashboard(), mimetype='text/plain; charset=utf-8')

    @app.get('/health')
    def health():
        return jsonify({'ok': True, 'version': VERSION, 'phase': PHASE, 'started_utc': START_TIME, 'last_scan_ok': LAST_SCAN.get('ok', False)})

    @app.get('/version')
    def version():
        return jsonify({'version': VERSION, 'phase': PHASE, 'build': BUILD_NAME, 'compatibility': COMPATIBILITY})

    @app.get('/v13')
    @app.get('/v13/dashboard')
    def v13_dashboard():
        return Response(text_dashboard(), mimetype='text/plain; charset=utf-8')

    @app.get('/v13/status')
    def v13_status():
        return jsonify(system_snapshot())

    @app.get('/v13/top5')
    def v13_top5():
        symbols=request.args.get('symbols')
        symbols=[x.strip().upper() for x in symbols.split(',')] if symbols else SYMBOLS
        return jsonify({'version': VERSION, 'items': top_signals(symbols, limit=5)})

    @app.get('/v13/signal/<symbol>')
    def v13_signal(symbol):
        s=score_symbol(symbol).__dict__
        return jsonify({'version': VERSION, 'signal': s, 'position': position_size(s), 'behavior': crowd_psychology_overlay(s)})

    @app.get('/v13/risk')
    def v13_risk():
        signals=top_signals(SYMBOLS, limit=10)
        return jsonify({'version': VERSION, 'portfolio_heat': portfolio_heat(signals), 'safety': safety_status(LIVE_TRADING_ENABLED, HUMAN_APPROVAL_REQUIRED)})

    @app.get('/v13/audit')
    def v13_audit():
        from phase13_world_class_fund_os.audit import build_manifest
        m=build_manifest('.')
        return jsonify({k:m[k] for k in ('version','generated_utc','file_count','repository_sha256')})

    @app.get('/v42')
    @app.get('/v42/dashboard')
    def v42_compat():
        return Response('V42 legacy route is now upgraded to V1300 TRUE LATEST.\n\n'+text_dashboard(), mimetype='text/plain; charset=utf-8')

    @app.post('/webhook')
    def webhook():
        # Minimal safe LINE webhook receiver. Real reply requires LINE token and signature validation.
        payload=request.get_json(silent=True) or {}
        return jsonify({'ok': True, 'version': VERSION, 'received': bool(payload)})

    return app

if Flask is not None:
    app = create_app()
    if os.getenv('AUTO_SCAN_ENABLED','true').lower() != 'false':
        threading.Thread(target=auto_scan_loop, daemon=True).start()
else:
    app = None

if __name__ == '__main__':
    run_scan_once()
    if app is not None:
        app.run(host='0.0.0.0', port=PORT)
    else:
        print(text_dashboard())

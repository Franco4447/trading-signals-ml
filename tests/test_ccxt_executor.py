"""
Unit tests for CCXT Direct Exchange Execution Adapter.
"""
from src.execution.ccxt_executor import ExchangeExecutor


def test_ccxt_executor_mock_order():
    executor = ExchangeExecutor(exchange_id="binance", is_testnet=True)
    res = executor.execute_signal_order(
        symbol="BTC/USDT",
        signal_score=0.85,
        current_price=40000.0,
        suggested_leverage=4.0,
        take_profit=42500.0,
        stop_loss=39000.0
    )
    assert res["status"] in ["EXECUTED_MOCK", "EXECUTED_MOCK_MAKER", "EXECUTED_LIVE"]
    assert res["symbol"] == "BTC/USDT"
    assert "bracket_orders" in res
    assert res["bracket_orders"]["takeProfit"]["triggerPrice"] == 42500.0
    assert res["bracket_orders"]["stopLoss"]["triggerPrice"] == 39000.0
    assert res["amount"] > 0.0001


def test_ccxt_executor_neutral_skip():
    executor = ExchangeExecutor(exchange_id="binance", is_testnet=True)
    res = executor.execute_signal_order(
        symbol="BTC/USDT",
        signal_score=0.10,  # Below threshold
        current_price=40000.0,
        suggested_leverage=1.0,
        take_profit=41000.0,
        stop_loss=39500.0
    )
    assert res["status"] == "SKIPPED_NEUTRAL"


def test_paper_trader_tp_sl_touch():
    from src.execution.paper_trader import PaperTraderEngine
    engine = PaperTraderEngine(initial_balance=10000.0)
    
    # 1. Open Long position
    res_open = engine.process_signal(
        signal_score=0.80,
        current_price=40000.0,
        suggested_leverage=5.0,
        take_profit=42000.0,
        stop_loss=39000.0
    )
    assert res_open["status"] == "SUCCESS"
    assert engine.current_position is not None
    
    # 2. Touch Take Profit bar (high touches 42500 while close is 41000)
    res_close = engine.process_signal(
        signal_score=0.50,
        current_price=41000.0,
        suggested_leverage=5.0,
        take_profit=42000.0,
        stop_loss=39000.0,
        high=42500.0,
        low=40500.0
    )
    assert engine.current_position is None
    assert len(engine.trade_history) == 1
    trade = engine.trade_history[0]
    assert trade["action"] == "CLOSE_TAKE_PROFIT"
    assert trade["exit_price"] == 42000.0
    assert trade["fee"] > 0.0  # Maker fee applied


SHELL := /bin/bash
COMPOSE := docker compose
PAIRS := BTC/USDT ETH/USDT SOL/USDT
TIMEFRAMES := 15m 1h
DAYS := 180

.PHONY: setup download-binance download-okx backtest-binance backtest-okx dryrun-binance dryrun-okx live-okx live-binance stop logs

setup:
	@test -f .env || cp .env.example .env
	@mkdir -p user_data/data user_data/logs user_data/backtest_results
	$(COMPOSE) pull

download-binance:
	$(COMPOSE) run --rm freqtrade download-data \
		--config user_data/config_spot_dryrun_binance.json \
		--trading-mode spot \
		--days $(DAYS) \
		--timeframes $(TIMEFRAMES) \
		--pairs $(PAIRS)

download-okx:
	$(COMPOSE) run --rm freqtrade download-data \
		--config user_data/config_spot_dryrun_okx.json \
		--trading-mode spot \
		--days $(DAYS) \
		--timeframes $(TIMEFRAMES) \
		--pairs $(PAIRS)

backtest-binance:
	$(COMPOSE) run --rm freqtrade backtesting \
		--config user_data/config_spot_dryrun_binance.json \
		--strategy HybridSafeStrategy \
		--timeframe 15m \
		--export trades \
		--backtest-directory user_data/backtest_results \
		--notes "binance spot dry-run HybridSafeStrategy 15m"

backtest-okx:
	$(COMPOSE) run --rm freqtrade backtesting \
		--config user_data/config_spot_dryrun_okx.json \
		--strategy HybridSafeStrategy \
		--timeframe 15m \
		--export trades \
		--backtest-directory user_data/backtest_results \
		--notes "okx spot dry-run HybridSafeStrategy 15m"

dryrun-binance:
	$(COMPOSE) --profile binance up -d dryrun-binance

dryrun-okx:
	$(COMPOSE) --profile okx up -d dryrun-okx

live-okx:
	@test -f .env.live.local || (echo ".env.live.local is missing; connect OKX in crypto-bot-platform first" && exit 1)
	@test -f user_data/config_spot_live_okx.local.json || (echo "live OKX config is missing; generate it in crypto-bot-platform first" && exit 1)
	$(COMPOSE) --profile live-okx up -d live-okx

live-binance:
	@test -f .env.live.local || (echo ".env.live.local is missing; connect Binance in crypto-bot-platform first" && exit 1)
	@test -f user_data/config_spot_live_binance.local.json || (echo "live Binance config is missing; generate it in crypto-bot-platform first" && exit 1)
	$(COMPOSE) --profile live-binance up -d live-binance

stop:
	$(COMPOSE) --profile binance --profile okx --profile live-okx --profile live-binance down --remove-orphans

logs:
	$(COMPOSE) --profile binance --profile okx logs -f --tail=200

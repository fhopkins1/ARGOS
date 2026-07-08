"""Live Portfolio and Performance Console for ARGOS."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class PortfolioPosition:
    """Traceable portfolio position displayed by LPPC."""

    position_id: str
    asset: str
    quantity: float
    average_cost: float
    market_price: float
    market_value: float
    unrealized_pnl: float
    realized_pnl: float
    sector: str
    liquidity: str
    executive_decision_id: str
    case_file_id: str
    supporting_evidence: tuple[str, ...]
    order_ids: tuple[str, ...]
    historical_performance_id: str


@dataclass(frozen=True)
class PortfolioSnapshot:
    """Deterministic portfolio financial and risk snapshot."""

    portfolio_id: str
    portfolio_name: str
    portfolio_type: str
    portfolio_value: float
    buying_power: float
    cash_position: float
    open_positions: int
    closed_positions: int
    realized_pnl: float
    unrealized_pnl: float
    daily_return: float
    weekly_return: float
    monthly_return: float
    annual_return: float
    lifetime_return: float
    positions: tuple[PortfolioPosition, ...]
    risk_metrics: dict[str, Any]
    performance_metrics: dict[str, float]
    trace: dict[str, Any]


@dataclass(frozen=True)
class PortfolioDetection:
    """LPPC consistency detection."""

    detection_id: str
    category: str
    severity: str
    summary: str
    evidence: tuple[str, ...]


class LivePortfolioPerformanceConsole:
    """Financial command display for enterprise portfolios."""

    def __init__(self) -> None:
        self._history: list[dict[str, Any]] = []

    def snapshot(
        self,
        *,
        timestamp_utc: str,
        control: dict[str, Any],
        eab: dict[str, Any],
        risk_status: str,
        historian_status: str,
        broker_status: str,
        audit_event_count: int,
    ) -> dict[str, Any]:
        """Return deterministic portfolio visibility for Commander display."""
        portfolios = self._portfolios(control, eab, risk_status, historian_status, broker_status)
        combined = self._combined_portfolio(portfolios)
        all_portfolios = (*portfolios, combined)
        detections = self._detections(all_portfolios, broker_status)
        record = {
            "recordId": f"LPPC-HIST-{len(self._history) + 1:06d}",
            "timestampUtc": timestamp_utc,
            "portfolioCount": len(all_portfolios),
            "combinedValue": combined.portfolio_value,
            "combinedUnrealizedPnl": combined.unrealized_pnl,
            "auditIdentifier": f"AE-LPPC-{audit_event_count + len(self._history) + 1:06d}",
        }
        self._append_if_changed(record)
        return {
            "portfolios": tuple(asdict(item) for item in all_portfolios),
            "combinedPortfolio": asdict(combined),
            "drilldown": self._drilldown(all_portfolios),
            "detections": tuple(asdict(item) for item in detections),
            "synchronization": {
                "positionManagementOffice": "SYNCHRONIZED",
                "tradeMonitoringOffice": "SYNCHRONIZED",
                "executionQualityOffice": "SYNCHRONIZED",
                "riskOffice": risk_status,
                "historianGroup": historian_status,
                "brokerIntegrationOffice": broker_status,
                "enterpriseActivityBus": "SYNCHRONIZED" if eab.get("health", {}).get("eventOrdering") == "CHRONOLOGICAL" else "ATTENTION",
            },
            "history": tuple(self._history[-50:]),
            "metrics": {
                "portfolioCount": len(all_portfolios),
                "openPositions": sum(item.open_positions for item in all_portfolios if item.portfolio_type != "combined"),
                "closedPositions": sum(item.closed_positions for item in all_portfolios if item.portfolio_type != "combined"),
                "detectionCount": len(detections),
                "historyDepth": len(self._history),
            },
        }

    def _portfolios(
        self,
        control: dict[str, Any],
        eab: dict[str, Any],
        risk_status: str,
        historian_status: str,
        broker_status: str,
    ) -> tuple[PortfolioSnapshot, ...]:
        paper_positions = _paper_positions() if control.get("paper_trading_active") else ()
        simulation_positions = _simulation_positions()
        live_positions: tuple[PortfolioPosition, ...] = () if not control.get("real_world_trading_active") else _live_positions()
        treasury = float(control.get("active_treasury_balance_usd", 0.0))
        return (
            self._portfolio("PORT-PAPER-001", "Paper Trading Portfolio", "paper", 100000.0, paper_positions, eab, risk_status, historian_status, broker_status),
            self._portfolio("PORT-SIM-001", "Simulation Portfolio", "simulation", 50000.0, simulation_positions, eab, risk_status, historian_status, broker_status),
            self._portfolio("PORT-LIVE-001", "Live Brokerage Portfolio", "live", treasury, live_positions, eab, risk_status, historian_status, broker_status),
        )

    def _portfolio(
        self,
        portfolio_id: str,
        name: str,
        portfolio_type: str,
        starting_cash: float,
        positions: tuple[PortfolioPosition, ...],
        eab: dict[str, Any],
        risk_status: str,
        historian_status: str,
        broker_status: str,
    ) -> PortfolioSnapshot:
        position_value = round(sum(item.market_value for item in positions), 4)
        unrealized = round(sum(item.unrealized_pnl for item in positions), 4)
        realized = round(sum(item.realized_pnl for item in positions), 4)
        cash = round(max(0.0, starting_cash - sum(abs(item.average_cost * item.quantity) for item in positions) + realized), 4)
        portfolio_value = round(cash + position_value, 4)
        basis = max(1.0, starting_cash)
        lifetime = round(((portfolio_value - basis) / basis) * 100, 4)
        return PortfolioSnapshot(
            portfolio_id=portfolio_id,
            portfolio_name=name,
            portfolio_type=portfolio_type,
            portfolio_value=portfolio_value,
            buying_power=round(cash * (1.0 if portfolio_type != "live" else 0.0), 4) if broker_status != "CONNECTED" and portfolio_type == "live" else cash,
            cash_position=cash,
            open_positions=sum(1 for item in positions if item.quantity != 0),
            closed_positions=2 if portfolio_type in {"paper", "simulation"} else 0,
            realized_pnl=realized,
            unrealized_pnl=unrealized,
            daily_return=round(lifetime / 20, 4),
            weekly_return=round(lifetime / 8, 4),
            monthly_return=round(lifetime / 3, 4),
            annual_return=round(lifetime * 4, 4),
            lifetime_return=lifetime,
            positions=positions,
            risk_metrics=_risk_metrics(positions),
            performance_metrics=_performance_metrics(positions, lifetime),
            trace={
                "positionManagementOffice": "PMO-SNAPSHOT",
                "tradeMonitoringOffice": "TMO-SNAPSHOT",
                "executionQualityOffice": "EQO-SNAPSHOT",
                "riskOffice": risk_status,
                "historianGroup": historian_status,
                "brokerIntegrationOffice": broker_status,
                "enterpriseActivityBusEvents": eab.get("health", {}).get("eventThroughput", 0),
            },
        )

    def _combined_portfolio(self, portfolios: tuple[PortfolioSnapshot, ...]) -> PortfolioSnapshot:
        positions = tuple(position for portfolio in portfolios for position in portfolio.positions)
        value = round(sum(portfolio.portfolio_value for portfolio in portfolios), 4)
        cash = round(sum(portfolio.cash_position for portfolio in portfolios), 4)
        realized = round(sum(portfolio.realized_pnl for portfolio in portfolios), 4)
        unrealized = round(sum(portfolio.unrealized_pnl for portfolio in portfolios), 4)
        basis = max(1.0, value - realized - unrealized)
        lifetime = round(((value - basis) / basis) * 100, 4)
        return PortfolioSnapshot(
            "PORT-ENTERPRISE-001",
            "Combined Enterprise Portfolio",
            "combined",
            value,
            round(sum(portfolio.buying_power for portfolio in portfolios), 4),
            cash,
            sum(portfolio.open_positions for portfolio in portfolios),
            sum(portfolio.closed_positions for portfolio in portfolios),
            realized,
            unrealized,
            round(lifetime / 20, 4),
            round(lifetime / 8, 4),
            round(lifetime / 3, 4),
            round(lifetime * 4, 4),
            lifetime,
            positions,
            _risk_metrics(positions),
            _performance_metrics(positions, lifetime),
            {"sourcePortfolios": tuple(portfolio.portfolio_id for portfolio in portfolios)},
        )

    def _drilldown(self, portfolios: tuple[PortfolioSnapshot, ...]) -> dict[str, Any]:
        return {
            portfolio.portfolio_id: {
                "portfolio": portfolio.portfolio_name,
                "positions": tuple(
                    {
                        "positionId": position.position_id,
                        "asset": position.asset,
                        "orders": position.order_ids,
                        "executiveDecision": position.executive_decision_id,
                        "caseFile": position.case_file_id,
                        "supportingEvidence": position.supporting_evidence,
                        "historicalPerformance": position.historical_performance_id,
                    }
                    for position in portfolio.positions
                ),
            }
            for portfolio in portfolios
        }

    def _detections(self, portfolios: tuple[PortfolioSnapshot, ...], broker_status: str) -> tuple[PortfolioDetection, ...]:
        detections: list[PortfolioDetection] = []
        for portfolio in portfolios:
            calculated = round(portfolio.cash_position + sum(item.market_value for item in portfolio.positions), 4)
            if calculated != portfolio.portfolio_value:
                detections.append(_detection(len(detections) + 1, "Portfolio Inconsistency", "CRITICAL", f"{portfolio.portfolio_id} value mismatch", (portfolio.portfolio_id,)))
            if portfolio.portfolio_type == "live" and broker_status != "CONNECTED" and portfolio.open_positions:
                detections.append(_detection(len(detections) + 1, "Synchronization Failure", "CRITICAL", "Live positions exist without broker connection", (portfolio.portfolio_id, broker_status)))
            if any(position.market_price <= 0 for position in portfolio.positions):
                detections.append(_detection(len(detections) + 1, "Missing Market Data", "WARNING", f"{portfolio.portfolio_id} has invalid market price", (portfolio.portfolio_id,)))
        return tuple(detections)

    def _append_if_changed(self, record: dict[str, Any]) -> None:
        comparable = {key: value for key, value in record.items() if key not in {"recordId", "timestampUtc", "auditIdentifier"}}
        if not self._history:
            self._history.append(record)
            return
        previous = {key: value for key, value in self._history[-1].items() if key not in {"recordId", "timestampUtc", "auditIdentifier"}}
        if comparable != previous:
            self._history.append(record)


def _paper_positions() -> tuple[PortfolioPosition, ...]:
    return (
        _position("PAPER-POS-001", "AAPL", 25, 188.2, 191.4, "Technology", "High", 312.5),
        _position("PAPER-POS-002", "MSFT", 12, 421.0, 418.5, "Technology", "High", -30.0),
        _position("PAPER-POS-003", "TLT", 40, 92.1, 93.0, "Rates", "High", 36.0),
    )


def _simulation_positions() -> tuple[PortfolioPosition, ...]:
    return (
        _position("SIM-POS-001", "SPY", 18, 529.0, 532.5, "Index", "High", 63.0),
        _position("SIM-POS-002", "GLD", 15, 217.5, 216.2, "Commodity", "High", -19.5),
    )


def _live_positions() -> tuple[PortfolioPosition, ...]:
    return (_position("LIVE-POS-001", "CASH", 0, 1, 1, "Cash", "High", 0.0),)


def _position(position_id: str, asset: str, quantity: float, average_cost: float, market_price: float, sector: str, liquidity: str, realized: float) -> PortfolioPosition:
    market_value = round(quantity * market_price, 4)
    unrealized = round((market_price - average_cost) * quantity, 4)
    suffix = position_id.split("-")[-1]
    return PortfolioPosition(
        position_id,
        asset,
        quantity,
        average_cost,
        market_price,
        market_value,
        unrealized,
        realized,
        sector,
        liquidity,
        f"CDR-2026-{suffix}",
        f"CF-2026-{suffix}",
        (f"EVID-{suffix}", f"AUD-{suffix}"),
        (f"ORD-{suffix}-A", f"ORD-{suffix}-B"),
        f"HIST-PERF-{suffix}",
    )


def _risk_metrics(positions: tuple[PortfolioPosition, ...]) -> dict[str, Any]:
    exposure = round(sum(abs(position.market_value) for position in positions), 4)
    sector_totals: dict[str, float] = {}
    for position in positions:
        sector_totals[position.sector] = round(sector_totals.get(position.sector, 0.0) + abs(position.market_value), 4)
    concentration = round(max(sector_totals.values(), default=0.0) / exposure * 100, 4) if exposure else 0.0
    return {
        "portfolioExposure": exposure,
        "sectorAllocation": sector_totals,
        "correlation": 0.42 if len(positions) > 1 else 0.0,
        "volatility": round(12.5 + len(positions) * 1.75, 4),
        "liquidity": "HIGH" if all(position.liquidity == "High" for position in positions) else "MIXED",
        "valueAtRisk": round(exposure * 0.025, 4),
        "maximumDrawdown": round(exposure * 0.04, 4),
        "positionConcentration": concentration,
    }


def _performance_metrics(positions: tuple[PortfolioPosition, ...], lifetime_return: float) -> dict[str, float]:
    gains = [position.realized_pnl + position.unrealized_pnl for position in positions if position.realized_pnl + position.unrealized_pnl > 0]
    losses = [abs(position.realized_pnl + position.unrealized_pnl) for position in positions if position.realized_pnl + position.unrealized_pnl < 0]
    win_rate = round((len(gains) / len(positions)) * 100, 4) if positions else 0.0
    avg_gain = round(sum(gains) / len(gains), 4) if gains else 0.0
    avg_loss = round(sum(losses) / len(losses), 4) if losses else 0.0
    profit_factor = round(sum(gains) / sum(losses), 4) if losses else round(sum(gains), 4)
    return {
        "alpha": round(lifetime_return - 1.2, 4),
        "beta": 0.84 if positions else 0.0,
        "sharpeRatio": round((lifetime_return / 10) if positions else 0.0, 4),
        "sortinoRatio": round((lifetime_return / 8) if positions else 0.0, 4),
        "winRate": win_rate,
        "averageGain": avg_gain,
        "averageLoss": avg_loss,
        "profitFactor": profit_factor,
    }


def _detection(index: int, category: str, severity: str, summary: str, evidence: tuple[str, ...]) -> PortfolioDetection:
    return PortfolioDetection(f"LPPC-DET-{index:06d}", category, severity, summary, evidence)

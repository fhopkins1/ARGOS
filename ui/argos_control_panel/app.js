let state = null;
let selectedIoeNodeId = "ENT-ARGOS";
let selectedPortfolioId = "PORT-ENTERPRISE-001";
let apiRuntimeLiveFeedOpen = false;
let engineeringModeOpen = false;
let activeBridgeView = "command_bridge";
let activeCapitalRange = "session";
let activeSeekerFilter = "all";

const OFFICE_BRIDGE_VIEWS = {
  Executive: "executive_bridge",
  Seeker: "seeker_bridge",
  Analyst: "analyst_bridge_placeholder",
  Risk: "risk_bridge_placeholder",
  Trader: "trader_bridge_placeholder",
  Historian: "historian_bridge_placeholder",
  Librarian: "librarian_bridge_placeholder",
  Academy: "academy_bridge_placeholder",
};

const $ = (id) => document.getElementById(id);

async function api(path, body) {
  const options = body === undefined
    ? {}
    : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
  const response = await fetch(path, options);
  if (!response.ok) throw new Error(await response.text());
  state = await response.json();
  render();
}

function money(value, digits = 2) {
  return `$${Number(value || 0).toFixed(digits)}`;
}

function selectedOrganization() {
  return $("ecc-org-select").value || "Executive";
}

function render() {
  if (!state) return;
  $("clock").textContent = new Date(state.timestampUtc).toLocaleString();
  $("system-status").textContent = state.systemStatus;
  renderCommandBridge();
  renderExecutiveBridge();
  renderSeekerBridge();
  renderSubcommandPlaceholder();
  renderBridgeVisibility();
  $("paper-state").textContent = state.control.paper_trading_active ? "Active" : "Inactive";
  $("paper-state").style.color = state.control.paper_trading_active ? "var(--green)" : "var(--muted)";
  $("live-state").textContent = state.control.real_world_trading_active ? "Active" : "Blocked";
  $("live-state").style.color = state.control.real_world_trading_active ? "var(--green)" : "var(--red)";
  $("treasury-balance").textContent = money(state.control.active_treasury_balance_usd);
  $("funds-halted").textContent = state.control.user_funds_halted ? "Yes" : "No";
  $("session-cost").textContent = money(state.costs.session_api_credits_usd, 4);
  $("today-cost").textContent = money(state.costs.today_api_credits_usd, 4);
  $("month-cost").textContent = money(state.costs.month_to_date_api_credits_usd, 4);
  $("budget-status").textContent = state.costs.budget_status;
  $("budget-status").style.color = state.costs.budget_status === "GREEN" ? "var(--green)" : state.costs.budget_status === "YELLOW" ? "var(--gold)" : "var(--red)";

  $("group-list").innerHTML = state.groups.map(group => `
    <li><span style="color:${group.color}">&bull;</span><span>${group.name}</span><b>${group.status}</b></li>
  `).join("");

  $("group-cards").innerHTML = state.groupCards.map(card => `
    <div class="group-card">
      <div class="icon">${icon(card.name)}</div>
      <h3>${card.name}</h3>
      <strong>${card.status}</strong>
      ${card.metrics.map(metric => `<div class="mini"><span>${metric[0]}</span><b>${metric[1]}</b></div>`).join("")}
    </div>
  `).join("");

  $("activity-feed").innerHTML = state.activity.map(item => `
    <tr><td>${item.time}</td><td>${item.group}</td><td>${item.message}</td><td>${item.reference}</td><td class="success-text">${item.status}</td></tr>
  `).join("");

  $("kpi-list").innerHTML = state.kpis.map(item => `
    <div class="kpi-row"><span>${item.name}</span><b>${item.value}</b><div class="spark"></div></div>
  `).join("");

  $("resource-list").innerHTML = Object.entries(state.resources).map(([name, value]) => `
    <div><div class="ring">${value}%</div><span>${name}</span></div>
  `).join("");

  $("schedule-list").innerHTML = state.schedule.map(item => `
    <div><b>${item.time}</b><span>${item.event}</span></div>
  `).join("");

  $("office-matrix").innerHTML = state.offices.map(item => `
    <div class="office-box"><h3>${item.group}</h3>${item.offices.map(office => `<p>${office} - ${item.status}</p>`).join("")}</div>
  `).join("");

  renderEcc();
  renderInfrastructure();
  renderCreditGovernor();
  renderApiRuntimeMonitor();
  renderPromptContract();
  renderControlledCognitivePilot();
  renderWorkflowOrchestrator();
  renderWorkflowRuntimeMonitor();
  renderLppc();
  renderStrategyPerformanceConsole();
  renderDecisionLaboratory();
  renderCommandConsole();
  renderEab();
  renderCnac();
  renderIoe();
  renderScheduler();
  drawHealth(state.healthSeries);
}

function bridgeWorkflow() {
  const monitor = state.workflowRuntimeMonitor || {};
  return monitor.activeWorkflow || (monitor.liveWorkflowExecution || [])[0] || null;
}

function bridgeBaton(workflow) {
  const monitor = state.workflowRuntimeMonitor || {};
  const views = monitor.workflowBatonView || [];
  return monitor.workflowBaton || views.find(item => item.workflowIdentifier === workflow?.workflowIdentifier) || views[0] || null;
}

function bridgeLatestDecision() {
  const strategy = state.strategyPerformanceConsole || {};
  const decision = strategy.decisionObjectPanel || {};
  if (decision.decisionObjectId) return decision;
  const evolution = strategy.decisionObjectEvolution || [];
  const latest = evolution[evolution.length - 1];
  const revision = latest?.revisions?.[latest.revisions.length - 1];
  if (!latest || !revision) return null;
  return {
    decisionObjectId: latest.decisionObjectId,
    workflowId: latest.workflowId,
    currentStage: revision.office,
    currentOwner: revision.office,
    currentRevision: revision.revision,
    currentConfidence: revision.confidence,
    currentRecommendation: revision.recommendation,
    riskScore: revision.risk,
    supportingSignals: revision.supportingSignals || [],
  };
}

function bridgePortfolio() {
  const truth = state.performanceTruthEngine || {};
  const truthCalculations = truth.calculations?.portfolio || {};
  const truthPortfolio = truth.portfolioLedger?.[truth.portfolioLedger.length - 1];
  if (truthPortfolio) {
    return {
      source: "TRUTH ENGINE",
      simulated: false,
      value: truthPortfolio.total_equity || truthCalculations.portfolioValue || 0,
      cash: truthPortfolio.cash || truthCalculations.cash || 0,
      realized: truthCalculations.realizedPnl || 0,
      unrealized: truthCalculations.unrealizedPnl || 0,
      todayReturnUsd: truthCalculations.realizedPnl || 0,
      todayReturnPercent: truthPortfolio.daily_return || truthCalculations.dailyReturnPercent || 0,
      returnPercent: truthPortfolio.total_return || truthCalculations.totalReturnPercent || 0,
      alpha: truthPortfolio.alpha || truthCalculations.alpha || 0,
      exposurePercent: truthCalculations.currentExposure || 0,
      maxDrawdownPercent: truthPortfolio.drawdown || truthCalculations.maximumDrawdown || 0,
      trades: truth.tradeLedger?.length || 0,
      winRate: state.strategyPerformanceConsole?.enterpriseScorecard?.winRate || 0,
      profitFactor: state.strategyPerformanceConsole?.livePortfolioPanel?.profitFactor || 0,
      sharpeRatio: state.strategyPerformanceConsole?.livePortfolioPanel?.sharpeRatio || 0,
      capitalTrustPosture: state.strategyPerformanceConsole?.enterpriseScorecard?.capitalTrustPosture || "PAPER_ONLY",
    };
  }
  const strategy = state.strategyPerformanceConsole?.livePortfolioPanel || {};
  return {
    source: "SIMULATED",
    simulated: true,
    value: strategy.portfolioValue || 0,
    cash: strategy.cash || 0,
    realized: strategy.realizedPnl || 0,
    unrealized: strategy.unrealizedPnl || 0,
    todayReturnUsd: strategy.realizedPnl || 0,
    todayReturnPercent: strategy.dailyReturnPercent || 0,
    returnPercent: strategy.totalReturnPercent || strategy.dailyReturnPercent || 0,
    alpha: state.strategyPerformanceConsole?.marketBenchmarks?.[0]?.alpha || 0,
    exposurePercent: strategy.currentExposure || 0,
    maxDrawdownPercent: strategy.maximumDrawdown || 0,
    trades: state.strategyPerformanceConsole?.tradeStream?.length || 0,
    winRate: state.strategyPerformanceConsole?.enterpriseScorecard?.winRate || 0,
    profitFactor: strategy.profitFactor || 0,
    sharpeRatio: strategy.sharpeRatio || 0,
    capitalTrustPosture: state.strategyPerformanceConsole?.enterpriseScorecard?.capitalTrustPosture || "SIMULATED",
  };
}

function bridgeBenchmark() {
  const history = state.performanceTruthEngine?.benchmarkHistory || [];
  const spy = history.slice().reverse().find(item => item.benchmark === "SPY") || history[history.length - 1];
  const fallback = state.strategyPerformanceConsole?.marketBenchmarks?.[0] || {};
  return {
    name: spy?.benchmark || fallback.benchmark || "SPY",
    returnPercent: spy?.benchmark_return ?? fallback.benchmarkReturnPercent ?? 0,
    alpha: spy?.alpha ?? fallback.alpha ?? 0,
  };
}

function bridgeCapitalHistory() {
  const ledger = state.performanceTruthEngine?.portfolioLedger || [];
  if (ledger.length) {
    return ledger.map((item, index) => ({
      timestamp: item.timestamp,
      portfolio: Number(item.total_equity || 0),
      benchmark: Number(item.benchmark_value || item.total_equity || 0),
      alpha: Number(item.alpha || 0),
      drawdown: Number(item.drawdown || 0),
      index,
    }));
  }
  return [];
}

function bridgeCreditMetrics() {
  const monitor = state.apiRuntimeMonitor || {};
  const governor = state.creditGovernor || {};
  const workflowCount = Math.max(1, state.workflowRuntimeMonitor?.metrics?.completedWorkflows || state.workflowOrchestrator?.metrics?.workflowCount || 0);
  const tradeCount = Math.max(1, state.performanceTruthEngine?.tradeLedger?.length || state.strategyPerformanceConsole?.tradeStream?.length || 0);
  const sessionCost = Number(monitor.costThisSessionUsd || state.costs?.session_api_credits_usd || 0);
  const burnRate = Number(monitor.currentCostBurnRateUsdPerHour || 0);
  const budgetLimit = Number(state.costs?.budget_limit_usd || governor.budgets?.daily_budget_usd || 0);
  const budgetRemaining = Math.max(0, budgetLimit - sessionCost);
  return {
    sessionCost,
    todayCost: Number(monitor.costTodayUsd || state.costs?.today_api_credits_usd || 0),
    burnRate,
    projectedDailyCost: burnRate * 24,
    costPerWorkflow: sessionCost / workflowCount,
    costPerCompletedTrade: sessionCost / tradeCount,
    budgetRemaining,
    apiMode: bridgeApiMode(),
  };
}

function bridgeCriticalAlerts() {
  const alertSources = [
    ...(state.workflowRuntimeMonitor?.commanderAlerts || []),
    ...(state.apiRuntimeMonitor?.runtimeAlerts || []),
    ...(state.controlledCognitivePilot?.alerts || []),
    ...(state.cnac?.notifications || []),
  ];
  return alertSources.filter(item => {
    const severity = String(item.severity || item.priority || "").toUpperCase();
    return ["WARNING", "CRITICAL", "EMERGENCY"].includes(severity);
  });
}

function bridgeApiMode() {
  const gateway = state.apiExecutionGateway || {};
  if (gateway.configuration?.realProviderCallsEnabled || gateway.realProviderCallsEnabled) return "Real API Pilot";
  if ((gateway.metrics?.dryRunCount || 0) > 0 || gateway.configuration?.dryRunDefault) return "Dry Run";
  return "Disabled";
}

function bridgeGroups() {
  return ["Executive", "Seeker", "Analyst", "Risk", "Trader", "Historian", "Librarian", "Academy"];
}

function bridgeViewOffice(view) {
  return Object.entries(OFFICE_BRIDGE_VIEWS).find(([, target]) => target === view)?.[0] || "Office";
}

function navigateBridge(view) {
  activeBridgeView = view || "command_bridge";
  if (activeBridgeView === "engineering_mode") {
    toggleEngineeringMode(true);
    return;
  }
  if (activeBridgeView === "decision_lab") {
    openBridgeLab();
    return;
  }
  renderBridgeVisibility();
}

function renderBridgeVisibility() {
  const commandBridge = $("command-bridge");
  const executiveBridge = $("executive-subcommand-bridge");
  const seekerBridge = $("seeker-subcommand-bridge");
  const placeholderBridge = $("subcommand-placeholder");
  if (!commandBridge || !executiveBridge || !seekerBridge || !placeholderBridge) return;
  commandBridge.classList.toggle("hidden", activeBridgeView !== "command_bridge");
  executiveBridge.classList.toggle("hidden", activeBridgeView !== "executive_bridge");
  seekerBridge.classList.toggle("hidden", activeBridgeView !== "seeker_bridge");
  const placeholderActive = activeBridgeView.endsWith("_bridge_placeholder");
  placeholderBridge.classList.toggle("hidden", !placeholderActive);
}

function renderCommandBridge() {
  const workflow = bridgeWorkflow();
  const baton = bridgeBaton(workflow);
  const integrity = state.workflowRuntimeMonitor?.tokenIntegrity || {};
  const portfolio = bridgePortfolio();
  const benchmark = bridgeBenchmark();
  const credit = bridgeCreditMetrics();
  const alerts = bridgeCriticalAlerts();
  const apiMode = bridgeApiMode();
  const paperActive = state.control.paper_trading_active;

  $("capital-portfolio-value").textContent = money(portfolio.value);
  $("capital-today-return-usd").textContent = money(portfolio.todayReturnUsd);
  $("capital-today-return-percent").textContent = `${Number(portfolio.todayReturnPercent || 0).toFixed(2)}%`;
  $("capital-total-return-percent").textContent = `${Number(portfolio.returnPercent || 0).toFixed(2)}%`;
  $("capital-benchmark-return").textContent = `${benchmark.name} ${Number(benchmark.returnPercent || 0).toFixed(2)}%`;
  $("capital-alpha").textContent = `${Number(portfolio.alpha || benchmark.alpha || 0).toFixed(2)}%`;
  $("capital-cash").textContent = money(portfolio.cash);
  $("capital-exposure").textContent = `${Number(portfolio.exposurePercent || 0).toFixed(2)}%`;
  $("capital-max-drawdown").textContent = `${Number(portfolio.maxDrawdownPercent || 0).toFixed(2)}%`;
  $("capital-trust-posture").textContent = portfolio.capitalTrustPosture || executiveCapitalTrustPosture(portfolio);
  $("capital-data-source").textContent = portfolio.simulated ? "SIMULATED performance display" : "Performance Truth Engine";
  drawCapitalEquityChart();

  $("bridge-alert-strip").innerHTML = alerts.length
    ? alerts.slice(0, 4).map(alert => {
        const severity = String(alert.severity || alert.priority || "WARNING").toUpperCase();
        return `<div class="bridge-alert ${severity.toLowerCase()}"><b>${severity}</b><span>${alert.organization || alert.sourceSystem || "ARGOS"}</span><strong>${alert.summary || alert.message || alert.category}</strong></div>`;
      }).join("")
    : `<div class="bridge-alert nominal"><b>NOMINAL</b><span>Commander</span><strong>No critical alerts require attention.</strong></div>`;

  $("credit-burn-heartbeat").innerHTML = `
    <div><span>API Cost This Session</span><b>${money(credit.sessionCost, 4)}</b></div>
    <div><span>API Cost Today</span><b>${money(credit.todayCost, 4)}</b></div>
    <div><span>Burn Rate / Hour</span><b>${money(credit.burnRate, 4)}</b></div>
    <div><span>Projected Daily Cost</span><b>${money(credit.projectedDailyCost, 4)}</b></div>
    <div><span>Cost / Workflow</span><b>${money(credit.costPerWorkflow, 4)}</b></div>
    <div><span>Cost / Completed Trade</span><b>${money(credit.costPerCompletedTrade, 4)}</b></div>
    <div><span>Budget Remaining</span><b>${money(credit.budgetRemaining, 4)}</b></div>
    <div><span>API Mode</span><b>${credit.apiMode}</b></div>
  `;

  $("mission-scorecards").innerHTML = `
    <div><span>Portfolio Value</span><b>${money(portfolio.value)}</b></div>
    <div><span>Realized P/L</span><b>${money(portfolio.realized)}</b></div>
    <div><span>Unrealized P/L</span><b>${money(portfolio.unrealized)}</b></div>
    <div><span>Total Trades</span><b>${portfolio.trades}</b></div>
    <div><span>Win Rate</span><b>${Number(portfolio.winRate || 0).toFixed(2)}%</b></div>
    <div><span>Profit Factor</span><b>${Number(portfolio.profitFactor || 0).toFixed(4)}</b></div>
    <div><span>Sharpe Ratio</span><b>${Number(portfolio.sharpeRatio || 0).toFixed(4)}</b></div>
    <div><span>Max Drawdown</span><b>${Number(portfolio.maxDrawdownPercent || 0).toFixed(2)}%</b></div>
    <div><span>Alpha</span><b>${Number(portfolio.alpha || 0).toFixed(2)}%</b></div>
    <div><span>Risk Exposure</span><b>${Number(portfolio.exposurePercent || 0).toFixed(2)}%</b></div>
  `;

  const stages = baton?.stages || ["Seeker", "Analyst", "Risk", "Trader", "Historian"].map(stage => ({
    stage,
    stage_name: stage,
    status: workflow?.currentOwner === stage ? "ACTIVE" : workflow ? "WAITING" : "DORMANT",
  }));
  $("bridge-baton").innerHTML = stages.map(item => {
    const name = item.stage_name || item.stage;
    const status = String(item.status || item.state || "WAITING").toUpperCase();
    return `<div class="bridge-baton-stage ${status.toLowerCase()}"><b>${name}</b><span>${status}</span></div>`;
  }).join("");

  $("bridge-token-metrics").innerHTML = workflow ? `
    <div><span>Workflow ID</span><b>${workflow.workflowIdentifier}</b></div>
    <div><span>Token ID</span><b>${workflow.tokenId || workflow.auditIdentifier}</b></div>
    <div><span>Stage</span><b>${workflow.workflowStage}</b></div>
    <div><span>Previous</span><b>${workflow.previousOwner || "None"}</b></div>
    <div><span>Next</span><b>${workflow.nextOwner || "None"}</b></div>
    <div><span>Transfers</span><b>${workflow.transferCount}</b></div>
    <div><span>Progress</span><b>${workflow.progress}%</b></div>
    <div><span>Runtime</span><b>${workflow.elapsedRuntime}s</b></div>
    <div><span>Outputs</span><b>${workflow.structuredOutputsProduced}</b></div>
    <div><span>Credits</span><b>${money(workflow.creditsConsumed, 4)}</b></div>
    <div><span>Health</span><b>${workflow.executionHealth}</b></div>
    <div><span>Audit</span><b>${workflow.auditIdentifier}</b></div>
  ` : `<div><span>Workflow</span><b>Idle</b></div><div><span>LAW VII</span><b>${integrity.status || "VALID"}</b></div>`;

  const decision = bridgeLatestDecision();
  $("bridge-decision").innerHTML = decision ? `
    <div class="bridge-decision-id">${decision.decisionObjectId}</div>
    <div class="bridge-decision-grid">
      <div><span>Workflow</span><b>${decision.workflowId || "None"}</b></div>
      <div><span>Owner</span><b>${decision.currentOwner || decision.currentStage || "None"}</b></div>
      <div><span>Revision</span><b>${decision.currentRevision || 0}</b></div>
      <div><span>Recommendation</span><b>${decision.currentRecommendation || "Pending"}</b></div>
      <div><span>Confidence</span><b>${decision.currentConfidence || 0}</b></div>
      <div><span>Risk Score</span><b>${decision.riskScore || 0}</b></div>
      <div><span>Position Size</span><b>${decision.positionSizeRecommendation || "Pending"}</b></div>
      <div><span>Expected Return</span><b>${decision.expectedReturn || "Pending"}</b></div>
      <div><span>Target</span><b>${decision.targetPrice ? money(decision.targetPrice) : "Pending"}</b></div>
      <div><span>Stop</span><b>${decision.stopLoss ? money(decision.stopLoss) : "Pending"}</b></div>
    </div>
    <p>${(decision.supportingSignals || []).join(", ") || "Awaiting structured office output."}</p>
  ` : `<div class="bridge-empty">No active decision. Start paper trading to generate the next Decision Object.</div>`;

  const owner = workflow?.currentOwner || "";
  const officeTotals = state.apiRuntimeMonitor?.officeCostTotalsUsd || {};
  const contributions = state.strategyPerformanceConsole?.officeContribution || [];
  const contributionByOffice = Object.fromEntries(contributions.map(item => [item.office, item]));
  const groups = bridgeGroups();
  $("bridge-office-hud").innerHTML = groups.map(group => {
    const active = group === owner;
    const contribution = contributionByOffice[group] || {};
    const cost = officeTotals[group] || 0;
    return `
      <button class="bridge-office ${active ? "active" : "dormant"}" data-bridge-view="${OFFICE_BRIDGE_VIEWS[group]}">
        <b>${group}</b>
        <strong>${active ? "ACTIVE" : "DORMANT"}</strong>
        <span>${active ? workflow.workflowStage : "Awaiting token ownership"}</span>
        <em>API ${money(cost, 4)} / ${contribution.recommendationChange || "No current contribution"}</em>
      </button>
    `;
  }).join("");
}

function drawCapitalEquityChart() {
  const canvas = $("capital-equity-chart");
  const empty = $("capital-empty-state");
  const points = bridgeCapitalHistory();
  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "rgba(5, 13, 22, .96)";
  ctx.fillRect(0, 0, width, height);
  if (!points.length) {
    empty.classList.remove("hidden");
    canvas.classList.add("hidden");
    return;
  }
  empty.classList.add("hidden");
  canvas.classList.remove("hidden");
  const filtered = activeCapitalRange === "all" ? points : points.slice(-Math.max(1, Math.min(points.length, {
    session: 20,
    today: 40,
    week: 80,
    month: 120,
  }[activeCapitalRange] || 20)));
  const values = filtered.flatMap(point => [point.portfolio, point.benchmark]).filter(value => Number.isFinite(value));
  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);
  const spread = Math.max(1, maxValue - minValue);
  const left = 64;
  const right = width - 28;
  const top = 28;
  const bottom = height - 46;

  ctx.strokeStyle = "rgba(143,166,187,.18)";
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const y = top + (bottom - top) * (i / 4);
    ctx.beginPath();
    ctx.moveTo(left, y);
    ctx.lineTo(right, y);
    ctx.stroke();
  }
  ctx.fillStyle = "#8fa6bb";
  ctx.font = "12px Segoe UI";
  ctx.fillText(money(maxValue), 8, top + 4);
  ctx.fillText(money(minValue), 8, bottom);

  const xy = (point, key, index) => {
    const x = left + (filtered.length === 1 ? 0 : index * ((right - left) / (filtered.length - 1)));
    const y = bottom - ((point[key] - minValue) / spread) * (bottom - top);
    return [x, y];
  };
  const drawLine = (key, color, widthPx) => {
    ctx.strokeStyle = color;
    ctx.lineWidth = widthPx;
    ctx.beginPath();
    filtered.forEach((point, index) => {
      const [x, y] = xy(point, key, index);
      if (index === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
  };
  drawLine("benchmark", "#8fa6bb", 2);
  drawLine("portfolio", "#53ff5c", 4);

  const alphaZeroY = bottom - ((filtered[0].portfolio - minValue) / spread) * (bottom - top);
  ctx.strokeStyle = "rgba(53,198,255,.35)";
  ctx.setLineDash([6, 6]);
  ctx.beginPath();
  ctx.moveTo(left, alphaZeroY);
  ctx.lineTo(right, alphaZeroY);
  ctx.stroke();
  ctx.setLineDash([]);

  const last = filtered[filtered.length - 1];
  ctx.fillStyle = "#eef6ff";
  ctx.font = "13px Segoe UI";
  ctx.fillText(`ARGOS ${money(last.portfolio)}   ${bridgeBenchmark().name} ${money(last.benchmark)}   Alpha ${Number(last.alpha || 0).toFixed(2)}%   Drawdown ${Number(last.drawdown || 0).toFixed(2)}%`, left, height - 16);
}

function setCapitalRange(range) {
  activeCapitalRange = range;
  document.querySelectorAll(".capital-range").forEach(item => {
    item.classList.toggle("active", item.dataset.capitalRange === range);
  });
  drawCapitalEquityChart();
}

function executiveDirectives() {
  const now = new Date(state.timestampUtc).toLocaleTimeString();
  const paperActive = state.control.paper_trading_active;
  return [
    {
      name: "Paper Self-Training",
      status: paperActive ? "ACTIVE" : "HALTED",
      owner: "Executive",
      priority: paperActive ? "HIGH" : "NOTICE",
      start: paperActive ? "Current Session" : "Not Active",
      update: now,
      criteria: paperActive ? "Tokenized workflows continue sequentially" : "No active paper workflows",
      action: paperActive ? "No" : "Optional Start Paper",
    },
    {
      name: "Preserve Capital",
      status: state.control.user_funds_halted ? "FUNDS HALTED" : "ENFORCED",
      owner: "Risk",
      priority: "HIGH",
      start: "Standing Directive",
      update: now,
      criteria: "No live trading without certified authorization",
      action: "No",
    },
    {
      name: "Continue Learning",
      status: paperActive ? "ACTIVE" : "STANDBY",
      owner: "Historian",
      priority: "MEDIUM",
      start: "Standing Directive",
      update: now,
      criteria: "Completed workflows remain replayable and auditable",
      action: "No",
    },
  ];
}

function executiveCapitalTrustPosture(portfolio) {
  const lawValid = (state.workflowRuntimeMonitor?.tokenIntegrity?.status || "VALID") === "VALID";
  const drawdown = Math.abs(Number(portfolio.maxDrawdown || portfolio.maximumDrawdown || 0));
  if (!lawValid) return "Critical";
  if (drawdown > 5 || state.costs?.budget_status === "RED") return "Warning";
  return "Nominal";
}

function renderExecutiveBridge() {
  if (!$("executive-subcommand-bridge")) return;
  const workflow = bridgeWorkflow();
  const monitor = state.workflowRuntimeMonitor || {};
  const orchestrator = state.workflowOrchestrator || {};
  const metrics = orchestrator.metrics || {};
  const portfolio = bridgePortfolio();
  const alerts = bridgeCriticalAlerts();
  const owner = workflow?.currentOwner || "";
  const groups = bridgeGroups();
  const activeCount = groups.filter(group => group === owner).length;
  const lawStatus = activeCount > 1 ? "VIOLATION" : (monitor.tokenIntegrity?.status || "VALID");
  const completedWorkflows = monitor.recentCompletedWorkflows || [];
  const throughput = monitor.metrics?.completedWorkflows || metrics.completedWorkflowCount || completedWorkflows.length || 0;
  const activeWorkflowCount = metrics.activeWorkflowCount || (workflow ? 1 : 0);
  const queuedWorkflowCount = metrics.queuedWorkflowCount || 0;
  const capitalTrust = executiveCapitalTrustPosture(portfolio);

  $("exec-argos-state").textContent = workflow ? "Executing" : state.control.paper_trading_active ? "Standing By" : "Halted";
  $("exec-enterprise-status").textContent = state.systemStatus || "Nominal";
  $("exec-environment").textContent = state.control.real_world_trading_active ? "Live Trading" : state.control.paper_trading_active ? "Paper Trading" : "Offline";
  $("exec-active-workflows").textContent = activeWorkflowCount;
  $("exec-throughput").textContent = throughput;
  $("exec-law").textContent = lawStatus;
  $("exec-law").style.color = lawStatus === "VALID" ? "var(--green)" : "var(--red)";
  $("exec-api-mode").textContent = bridgeApiMode();
  $("exec-capital-trust").textContent = capitalTrust;
  $("exec-alert-state").textContent = alerts[0]?.summary || "None";

  $("exec-coordination").innerHTML = `
    <div><span>Paper Trading</span><b>${state.control.paper_trading_active ? "ACTIVE" : "HALTED"}</b></div>
    <div><span>Active Workflows</span><b>${activeWorkflowCount}</b></div>
    <div><span>Queued Workflows</span><b>${queuedWorkflowCount}</b></div>
    <div><span>Completed Workflows</span><b>${throughput}</b></div>
    <div><span>Throughput</span><b>${throughput}</b></div>
    <div><span>Current Workflow</span><b>${workflow?.workflowName || "None"}</b></div>
    <div><span>Token Owner</span><b>${owner || "None"}</b></div>
    <div><span>Decision Object</span><b>${bridgeLatestDecision()?.decisionObjectId || "None"}</b></div>
    <div><span>Utilization</span><b>${owner ? "1 / 8" : "0 / 8"}</b></div>
    <div><span>Executing Offices</span><b>${owner ? 1 : 0}</b></div>
    <div><span>Dormant Offices</span><b>${owner ? 7 : 8}</b></div>
    <div><span>Enterprise Mode</span><b>${state.environment || "offline"}</b></div>
  `;

  const officeTotals = state.apiRuntimeMonitor?.officeCostTotalsUsd || {};
  const contributions = state.strategyPerformanceConsole?.officeContribution || [];
  const contributionByOffice = Object.fromEntries(contributions.map(item => [item.office, item]));
  $("exec-health-matrix").innerHTML = groups.map(group => {
    const isActive = group === owner;
    const contribution = contributionByOffice[group] || {};
    const health = lawStatus !== "VALID" && isActive ? "WARNING" : "HEALTHY";
    return `
      <div class="executive-health-card ${isActive ? "active" : ""}">
        <b>${group}</b>
        <strong>${isActive ? "ACTIVE" : state.control.paper_trading_active ? "WAITING" : "DORMANT"}</strong>
        <span>${health}</span>
        <em>${isActive ? workflow.workflowStage : "No active task"}</em>
        <small>Decision ${bridgeLatestDecision()?.decisionObjectId || "None"} / API ${money(officeTotals[group] || 0, 4)}</small>
        <small>Contribution ${contribution.workflowCount || 0} / ${contribution.recommendationChange || "No current contribution"}</small>
        <small>Last activity ${state.timestampUtc}</small>
      </div>
    `;
  }).join("");

  const recentRows = completedWorkflows.slice(-5).reverse().map(item => `
    <div class="executive-workflow-row">
      <b>${item.workflowIdentifier}</b>
      <span>${item.status} / ${item.workflowStage}</span>
      <strong>${money(item.creditsConsumed, 4)}</strong>
      <em>Decision ${bridgeLatestDecision()?.decisionObjectId || "None"} / Recommendation ${bridgeLatestDecision()?.currentRecommendation || "Pending"} / Health ${item.executionHealth}</em>
    </div>
  `).join("");
  $("exec-workflow-operations").innerHTML = `
    <div class="executive-current-workflow">
      <b>${workflow?.workflowName || "No active workflow"}</b>
      <span>ID ${workflow?.workflowIdentifier || "None"} / Type ${workflow?.workflowType || "None"} / Status ${workflow?.status || "Idle"}</span>
      <span>Stage ${workflow?.workflowStage || "None"} / Current ${owner || "None"} / Previous ${workflow?.previousOwner || "None"} / Next ${workflow?.nextOwner || "None"}</span>
      <span>Progress ${workflow?.progress || 0}% / Transfers ${workflow?.transferCount || 0} / Outputs ${workflow?.structuredOutputsProduced || 0} / Runtime ${workflow?.elapsedRuntime || 0}s / Health ${workflow?.executionHealth || "Nominal"}</span>
    </div>
    <div class="executive-recent-title">Recent Completed Workflows</div>
    ${recentRows || `<div class="bridge-empty">No recent completed workflows.</div>`}
  `;

  $("exec-directives").innerHTML = executiveDirectives().length
    ? executiveDirectives().map(item => `
      <div class="executive-directive">
        <b>${item.name}</b>
        <strong>${item.status}</strong>
        <span>${item.owner} / ${item.priority}</span>
        <em>Start ${item.start} / Update ${item.update}</em>
        <small>${item.criteria} / Commander action required: ${item.action}</small>
      </div>
    `).join("")
    : `<div class="bridge-empty">No active executive directives.</div>`;

  const strategyPortfolio = state.strategyPerformanceConsole?.livePortfolioPanel || {};
  $("exec-performance").innerHTML = `
    <div><span>Portfolio Value</span><b>${money(portfolio.value)}</b></div>
    <div><span>Today Return</span><b>${Number(strategyPortfolio.dailyReturnPercent || portfolio.returnPercent || 0).toFixed(2)}%</b></div>
    <div><span>Total Return</span><b>${Number(portfolio.returnPercent || 0).toFixed(2)}%</b></div>
    <div><span>Alpha</span><b>${Number(portfolio.alpha || 0).toFixed(2)}</b></div>
    <div><span>Realized P/L</span><b>${money(portfolio.realized)}</b></div>
    <div><span>Unrealized P/L</span><b>${money(portfolio.unrealized)}</b></div>
    <div><span>Total Trades</span><b>${portfolio.trades}</b></div>
    <div><span>Win Rate</span><b>${state.strategyPerformanceConsole?.enterpriseScorecard?.winRate || 0}%</b></div>
    <div><span>Max Drawdown</span><b>${money(strategyPortfolio.maximumDrawdown || 0)}</b></div>
    <div><span>Capital Trust</span><b>${capitalTrust}</b></div>
  `;

  const executiveAlerts = alerts.filter(alert => {
    const text = `${alert.category || ""} ${alert.summary || ""}`.toLowerCase();
    return ["law", "workflow", "gateway", "budget", "prompt", "truth", "drawdown", "office", "duplicate", "api"].some(word => text.includes(word));
  });
  $("exec-alerts").innerHTML = executiveAlerts.length
    ? executiveAlerts.slice(0, 8).map(alert => `<div class="executive-alert ${String(alert.severity || alert.priority || "info").toLowerCase()}"><b>${alert.severity || alert.priority}</b><span>${alert.category || alert.organization || "Enterprise"}</span><strong>${alert.summary || alert.message}</strong></div>`).join("")
    : `<div class="bridge-empty">No executive attention alerts.</div>`;

  $("exec-office-nav").innerHTML = groups.map(group => `
    <button class="bridge-office ${group === owner ? "active" : "dormant"}" data-bridge-view="${OFFICE_BRIDGE_VIEWS[group]}">
      <b>${group}</b>
      <strong>${group === owner ? "ACTIVE" : "OPEN"}</strong>
      <span>${group === "Executive" ? "Implemented" : "Placeholder"}</span>
      <em>Subcommand Bridge</em>
    </button>
  `).join("");
}

function renderSubcommandPlaceholder() {
  const office = bridgeViewOffice(activeBridgeView);
  if (!$("placeholder-title")) return;
  $("placeholder-office-label").textContent = office;
  $("placeholder-title").textContent = `${office} Subcommand Bridge`;
  $("placeholder-message").textContent = `${office} Subcommand Bridge pending implementation.`;
}

function seekerCandidates() {
  const decision = bridgeLatestDecision();
  const trades = state.strategyPerformanceConsole?.tradeStream || [];
  const latestTrade = trades[trades.length - 1] || {};
  const evolution = state.strategyPerformanceConsole?.decisionObjectEvolution || [];
  const items = [];
  if (decision?.decisionObjectId) {
    items.push({
      candidateId: `COR-${decision.decisionObjectId}`,
      ticker: latestTrade.ticker || "AAPL",
      confidence: Number(decision.currentConfidence || 0.62),
      discoveryScore: Math.round(Number(decision.currentConfidence || 0.62) * 100),
      momentum: "Positive",
      relativeStrength: "Improving",
      volume: "Confirmed",
      news: "Monitored",
      sector: latestTrade.strategy || "Cross-Market",
      marketRegime: state.environment || "paper",
      promotionProbability: Math.round(Number(decision.currentConfidence || 0.62) * 92),
      status: decision.currentRecommendation ? "Promoted" : "Candidate",
      evidenceCount: decision.evidenceCount || (decision.supportingSignals || []).length || 1,
      signals: decision.supportingSignals || ["workflow-signal"],
      workflow: decision.workflowId || "None",
      decisionObject: decision.decisionObjectId,
      recommendation: decision.currentRecommendation || "Continue discovery",
    });
  }
  evolution.slice(-4).forEach((item, index) => {
    if (items.some(candidate => candidate.decisionObject === item.decisionObjectId)) return;
    const revision = item.revisions?.[item.revisions.length - 1] || {};
    items.push({
      candidateId: `COR-${item.decisionObjectId}`,
      ticker: latestTrade.ticker || ["AAPL", "MSFT", "NVDA", "SPY"][index % 4],
      confidence: Number(revision.confidence || 0.55),
      discoveryScore: Math.round(Number(revision.confidence || 0.55) * 100),
      momentum: "Watching",
      relativeStrength: "Neutral",
      volume: "Normal",
      news: "Quiet",
      sector: latestTrade.strategy || "Paper Strategy",
      marketRegime: state.environment || "paper",
      promotionProbability: Math.round(Number(revision.confidence || 0.55) * 88),
      status: "Watching",
      evidenceCount: item.revisionCount || item.revisions?.length || 1,
      signals: revision.supportingSignals || ["historical-decision"],
      workflow: item.workflowId,
      decisionObject: item.decisionObjectId,
      recommendation: revision.recommendation || "Monitor",
    });
  });
  return items.sort((left, right) => right.discoveryScore - left.discoveryScore);
}

function seekerSignalSources() {
  const apiMode = bridgeApiMode();
  return [
    ["Market Data", "Healthy"],
    ["News", "Healthy"],
    ["Fundamentals", "Healthy"],
    ["Relative Strength", "Healthy"],
    ["Volume", "Healthy"],
    ["Volatility", "Healthy"],
    ["Economic Calendar", "Healthy"],
    ["Options", "Healthy"],
    ["Sentiment", apiMode === "Disabled" ? "Disabled" : "Healthy"],
  ];
}

function seekerMissionObjective(workflow, candidates) {
  if (!workflow) return "Awaiting workflow assignment";
  if (workflow.currentOwner === "Seeker") return "Discover candidate opportunities";
  if (candidates.some(candidate => candidate.status === "Promoted")) return "Promotion package sent to Analyst";
  return "Maintain reconnaissance coverage";
}

function seekerMarketIntelligence(candidates) {
  const truth = state.performanceTruthEngine || {};
  const portfolio = truth.calculations?.portfolio || {};
  const benchmark = bridgeBenchmark();
  const scorecard = state.strategyPerformanceConsole?.enterpriseScorecard || {};
  const trades = state.strategyPerformanceConsole?.tradeStream || [];
  const latestTrade = trades[trades.length - 1] || {};
  const healthySignals = seekerSignalSources().filter(([, status]) => status === "Healthy").length;
  const topCandidate = candidates[0];
  return {
    marketTrend: Number(benchmark.returnPercent || 0) >= 0 ? "Constructive" : "Defensive",
    breadth: candidates.length ? `${candidates.length} candidate channels` : "Awaiting candidates",
    volatility: Number(portfolio.maximumDrawdown || portfolio.maxDrawdownPercent || 0) < -2 ? "Elevated" : "Contained",
    sectorLeadership: topCandidate?.sector || latestTrade.strategy || "Awaiting truth history",
    topGainers: topCandidate?.ticker || "Awaiting candidates",
    topLosers: latestTrade.ticker && latestTrade.ticker !== topCandidate?.ticker ? latestTrade.ticker : "None detected",
    newsDensity: candidates.some(candidate => candidate.news !== "Quiet") ? "Monitored" : "Quiet",
    economicCalendar: healthySignals >= 7 ? "Online" : "Partial",
    marketRegime: topCandidate?.marketRegime || state.environment || "paper",
    paperUniverse: state.control.paper_trading_active ? "Active" : "Standing by",
    discoveryQuality: scorecard.decisionQuality || 0,
  };
}

function seekerHealth(candidates, workflow) {
  const sources = seekerSignalSources();
  const healthy = sources.filter(([, status]) => status === "Healthy").length;
  const law = state.workflowRuntimeMonitor?.tokenIntegrity?.status || "VALID";
  const gateway = state.apiExecutionGateway || {};
  const runtime = workflow?.elapsedRuntime || 0;
  const lastPromotion = state.strategyPerformanceConsole?.decisionObjectEvolution?.slice(-1)[0];
  return {
    officeHealth: law === "VALID" ? "Nominal" : "Attention",
    missionHealth: workflow?.executionHealth || (state.control.paper_trading_active ? "Ready" : "Standing By"),
    discoveryPipeline: candidates.length ? `${candidates.length} candidates` : "Empty",
    lawVII: law,
    apiMode: bridgeApiMode(),
    gatewayStatus: gateway.directProviderCallsEnabled ? "Live-capable" : "Dry-run guarded",
    lastPromotion: lastPromotion?.decisionObjectId || "None",
    currentRuntime: `${runtime}s`,
    operatingState: workflow?.currentOwner === "Seeker" ? "Active" : state.control.paper_trading_active ? "Waiting" : "Dormant",
    signalHealth: `${healthy}/${sources.length} healthy`,
  };
}

function filteredSeekerCandidates(candidates) {
  if (activeSeekerFilter === "all") return candidates;
  return candidates.filter(candidate => String(candidate.status || "").toLowerCase() === activeSeekerFilter);
}

function renderSeekerBridge() {
  if (!$("seeker-subcommand-bridge")) return;
  const workflow = bridgeWorkflow();
  const decision = bridgeLatestDecision();
  const candidates = seekerCandidates();
  const visibleCandidates = filteredSeekerCandidates(candidates);
  const alerts = bridgeCriticalAlerts();
  const owner = workflow?.currentOwner || "";
  const seekerActive = owner === "Seeker";
  const lawStatus = state.workflowRuntimeMonitor?.tokenIntegrity?.status || "VALID";
  const promotions = state.strategyPerformanceConsole?.decisionObjectEvolution || [];
  const completed = state.workflowRuntimeMonitor?.recentCompletedWorkflows || [];
  const missionName = workflow ? "Paper Trading Discovery" : "No active discovery mission";
  const universe = state.control.paper_trading_active ? "Paper Trading Universe" : "Paper Market";
  const progress = workflow?.progress || 0;
  const objective = seekerMissionObjective(workflow, candidates);
  const health = seekerHealth(candidates, workflow);
  const market = seekerMarketIntelligence(candidates);

  $("seeker-office-state").textContent = seekerActive ? "ACTIVE" : state.control.paper_trading_active ? "WAITING" : "DORMANT";
  $("seeker-mission").textContent = missionName;
  $("seeker-workflow").textContent = workflow?.workflowIdentifier || "None";
  $("seeker-decision-object").textContent = decision?.decisionObjectId || "None";
  $("seeker-law").textContent = lawStatus;
  $("seeker-law").style.color = lawStatus === "VALID" ? "var(--green)" : "var(--red)";
  $("seeker-token-status").textContent = workflow ? `${owner || "No Owner"} / ${workflow.tokenId || workflow.auditIdentifier}` : "No Token";
  $("seeker-api-mode").textContent = bridgeApiMode();
  $("seeker-universe").textContent = universe;
  $("seeker-market-session").textContent = state.control.paper_trading_active ? "Paper Session" : "Closed";
  $("seeker-signal-health").textContent = health.signalHealth;
  $("seeker-current-objective").textContent = objective;
  $("seeker-alert").textContent = alerts[0]?.summary || "None";

  $("seeker-mission-panel").innerHTML = `
    <div><span>Mission Name</span><b>${missionName}</b></div>
    <div><span>Objective</span><b>${objective}</b></div>
    <div><span>Universe</span><b>${universe}</b></div>
    <div><span>Search Scope</span><b>Multi-office paper reconnaissance</b></div>
    <div><span>Workflow</span><b>${workflow?.workflowIdentifier || "None"}</b></div>
    <div><span>Stage</span><b>${workflow?.workflowStage || "None"}</b></div>
    <div><span>Token Owner</span><b>${owner || "None"}</b></div>
    <div><span>Progress</span><b>${progress}%</b></div>
    <div><span>Time Remaining</span><b>${workflow?.estimatedRemainingRuntime || "Idle"}</b></div>
    <div><span>Mission Health</span><b>${workflow?.executionHealth || "Ready"}</b></div>
  `;

  $("seeker-radar").innerHTML = visibleCandidates.length
    ? visibleCandidates.map(candidate => `
      <div class="radar-candidate ${candidate.status.toLowerCase()}">
        <b>${candidate.ticker}</b>
        <strong>${candidate.discoveryScore}</strong>
        <span>Confidence ${Math.round(candidate.confidence * 100)}% / Promote ${candidate.promotionProbability}%</span>
        <em>Momentum ${candidate.momentum} / RS ${candidate.relativeStrength} / Volume ${candidate.volume}</em>
        <small>News ${candidate.news} / Sector ${candidate.sector} / Regime ${candidate.marketRegime} / ${candidate.status}</small>
      </div>
    `).join("")
    : `<div class="bridge-empty">Awaiting workflow assignment. Signal sources healthy. Discovery systems standing by. No active candidates.</div>`;

  $("seeker-candidate-queue").innerHTML = candidates.length
    ? candidates.map(candidate => `
      <div class="candidate-row">
        <b>${candidate.candidateId}</b>
        <span>${candidate.ticker} / Score ${candidate.discoveryScore} / Confidence ${Math.round(candidate.confidence * 100)}%</span>
        <span>Evidence ${candidate.evidenceCount} / Signals ${candidate.signals.join(", ")}</span>
        <strong>${candidate.status}</strong>
        <em>Workflow ${candidate.workflow} / Decision ${candidate.decisionObject} / ${candidate.recommendation}</em>
      </div>
    `).join("")
    : `<div class="bridge-empty">No candidates queued.</div>`;

  $("seeker-current-decision").innerHTML = decision ? `
    <div class="bridge-decision-id">${decision.decisionObjectId}</div>
    <div class="bridge-decision-grid">
      <div><span>Workflow</span><b>${decision.workflowId || "None"}</b></div>
      <div><span>Revision</span><b>${decision.currentRevision || 0}</b></div>
      <div><span>Confidence</span><b>${decision.currentConfidence || 0}</b></div>
      <div><span>Evidence</span><b>${decision.evidenceCount || (decision.supportingSignals || []).length || 0}</b></div>
      <div><span>Signals</span><b>${(decision.supportingSignals || []).join(", ") || "Pending"}</b></div>
      <div><span>Recommendation</span><b>${decision.currentRecommendation || "Pending"}</b></div>
      <div><span>Expected Return</span><b>${decision.expectedReturn || "Pending"}</b></div>
      <div><span>Owner</span><b>${decision.currentOwner || decision.currentStage || "None"}</b></div>
      <div><span>Readiness</span><b>${Number(decision.currentConfidence || 0) >= 0.7 ? "Promotion Ready" : "Collecting Evidence"}</b></div>
      <div><span>Notes</span><b>${decision.confidenceReason || "Discovery notes pending"}</b></div>
    </div>
  ` : `<div class="bridge-empty">No active Decision Object under Seeker construction.</div>`;

  $("seeker-signal-sources").innerHTML = seekerSignalSources().map(([source, status]) => `
    <div class="signal-source ${status.toLowerCase()}"><b>${source}</b><span>${status}</span></div>
  `).join("");

  const promoted = candidates.filter(item => item.status === "Promoted").length;
  const rejected = candidates.filter(item => item.status === "Rejected").length;
  const qualified = candidates.filter(item => Number(item.discoveryScore || 0) >= 55).length;
  const avgConfidence = candidates.length ? candidates.reduce((sum, item) => sum + item.confidence, 0) / candidates.length : 0;
  const avgPromotion = candidates.length ? candidates.reduce((sum, item) => sum + item.promotionProbability, 0) / candidates.length : 0;
  $("seeker-discovery-metrics").innerHTML = `
    <div><span>Candidates Scanned</span><b>${Math.max(candidates.length, promotions.length)}</b></div>
    <div><span>Candidates Qualified</span><b>${qualified}</b></div>
    <div><span>Candidates Promoted</span><b>${promoted}</b></div>
    <div><span>Candidates Rejected</span><b>${rejected}</b></div>
    <div><span>Average Discovery Confidence</span><b>${Math.round(avgConfidence * 100)}%</b></div>
    <div><span>Average Promotion Confidence</span><b>${Math.round(avgPromotion)}%</b></div>
    <div><span>Average Discovery Time</span><b>${workflow?.elapsedRuntime || 0}s</b></div>
    <div><span>Signal Sources Active</span><b>${seekerSignalSources().filter(([, status]) => status === "Healthy").length}/${seekerSignalSources().length}</b></div>
    <div><span>Decision Objects Started</span><b>${promotions.length}</b></div>
    <div><span>Promotion Rate</span><b>${candidates.length ? Math.round((promoted / candidates.length) * 100) : 0}%</b></div>
  `;

  $("seeker-market-intelligence").innerHTML = `
    <div><span>Market Trend</span><b>${market.marketTrend}</b></div>
    <div><span>Breadth</span><b>${market.breadth}</b></div>
    <div><span>Volatility</span><b>${market.volatility}</b></div>
    <div><span>Sector Leadership</span><b>${market.sectorLeadership}</b></div>
    <div><span>Top Gainers</span><b>${market.topGainers}</b></div>
    <div><span>Top Losers</span><b>${market.topLosers}</b></div>
    <div><span>News Density</span><b>${market.newsDensity}</b></div>
    <div><span>Economic Calendar</span><b>${market.economicCalendar}</b></div>
    <div><span>Market Regime</span><b>${market.marketRegime}</b></div>
    <div><span>Paper Trading Universe</span><b>${market.paperUniverse}</b></div>
  `;

  $("seeker-office-health").innerHTML = `
    <div><span>Office Health</span><b>${health.officeHealth}</b></div>
    <div><span>Mission Health</span><b>${health.missionHealth}</b></div>
    <div><span>Discovery Pipeline</span><b>${health.discoveryPipeline}</b></div>
    <div><span>LAW VII</span><b>${health.lawVII}</b></div>
    <div><span>API Mode</span><b>${health.apiMode}</b></div>
    <div><span>Gateway Status</span><b>${health.gatewayStatus}</b></div>
    <div><span>Last Promotion</span><b>${health.lastPromotion}</b></div>
    <div><span>Current Runtime</span><b>${health.currentRuntime}</b></div>
    <div><span>Dormant/Active</span><b>${health.operatingState}</b></div>
  `;

  $("seeker-promotions").innerHTML = promotions.length
    ? promotions.slice(-6).reverse().map((item, index) => {
      const revision = item.revisions?.[item.revisions.length - 1] || {};
      const complete = completed.find(workflowItem => workflowItem.workflowIdentifier === item.workflowId) || {};
      return `
        <div class="promotion-row">
          <b>${candidates[index]?.ticker || "AAPL"}</b>
          <span>${item.workflowId}</span>
          <span>${item.decisionObjectId}</span>
          <strong>${revision.confidence || 0}</strong>
          <em>${complete.completedAt || state.timestampUtc} / Destination Analyst / ${revision.recommendation || "Promoted for review"}</em>
        </div>
      `;
    }).join("")
    : `<div class="bridge-empty">No recent promotions. Replay becomes available after a Decision Object is promoted.</div>`;

  $("seeker-office-nav").innerHTML = bridgeGroups().map(group => `
    <button class="bridge-office ${group === owner ? "active" : "dormant"}" data-bridge-view="${OFFICE_BRIDGE_VIEWS[group]}">
      <b>${group}</b>
      <strong>${group === "Seeker" ? "CURRENT" : "OPEN"}</strong>
      <span>${OFFICE_BRIDGE_VIEWS[group].includes("placeholder") ? "Placeholder" : "Implemented"}</span>
      <em>Subcommand Bridge</em>
    </button>
  `).join("");
}

function renderCreditGovernor() {
  if (!state.creditGovernor) return;
  const governor = state.creditGovernor;
  const workflowScope = selectedWorkflowScope();
  $("credit-mode").textContent = governor.mode;
  $("credit-mode").className = `credit-mode ${governor.mode.toLowerCase().replaceAll(" ", "-")}`;
  $("credit-daily-budget").value = governor.budgets.daily_budget_usd;
  $("credit-weekly-budget").value = governor.budgets.weekly_budget_usd;
  $("credit-monthly-budget").value = governor.budgets.monthly_budget_usd;
  $("credit-spend").innerHTML = `
    <div>Daily Spend<b>${money(governor.spendReport.dailySpendUsd, 4)}</b></div>
    <div>Weekly Spend<b>${money(governor.spendReport.weeklySpendUsd, 4)}</b></div>
    <div>Monthly Spend<b>${money(governor.spendReport.monthlySpendUsd, 4)}</b></div>
    <div>Trading Cycle<b>${money(governor.spendReport.costPerTradingCycle, 4)}</b></div>
    <div>Briefing<b>${money(governor.spendReport.costPerBriefing, 4)}</b></div>
    <div>Historian Review<b>${money(governor.spendReport.costPerHistorianReview, 4)}</b></div>
    <div>Academy Output<b>${money(governor.spendReport.costPerAcademyOutput, 4)}</b></div>
    <div>Approved AI Calls<b>${governor.metrics.approvedActivations}</b></div>
    <div>Real API Usage<b>${money(state.costs.real_api_usage_usd, 4)}</b></div>
    <div>Paper Telemetry<b>${money(state.costs.simulated_paper_trading_telemetry_usd, 4)}</b></div>
    <div>Token-Scoped Usage<b>${money(state.costs.workflow_token_authorized_api_usage_usd, 4)}</b></div>
    <div>Selected Token Owner<b>${workflowScope.office || "None"}</b></div>
  `;
  $("credit-detections").innerHTML = governor.detections.length
    ? governor.detections.map(item => `<div class="infra-row ${item.severity.toLowerCase()}"><b>${item.severity}</b><span>${item.category}</span><span>${item.summary}</span><strong>${item.detection_id}</strong></div>`).join("")
    : `<div class="alert-empty">No credit-governor detections</div>`;
  $("credit-activations").innerHTML = governor.activations.length
    ? governor.activations.map(item => `
      <div class="infra-row ${item.status === "REJECTED" ? "critical" : ""}">
        <b>${item.status}</b>
        <span>${item.receiving_office}</span>
        <span>${item.purpose}</span>
        <strong>${item.maximum_credit_budget_usd}</strong>
      </div>
    `).join("")
    : `<div class="alert-empty">No AI activations requested</div>`;
}

function renderApiRuntimeMonitor() {
  if (!state.apiRuntimeMonitor) return;
  const monitor = state.apiRuntimeMonitor;
  drawApiRuntimeCostChart(monitor.officeCostSeries, monitor.officeCostTotalsUsd);
  renderApiRuntimeCostLegend(monitor.officeCostTotalsUsd, monitor.entities);
  $("arm-summary").innerHTML = `
    <div>Active Entities<b>${monitor.metrics.activeCount}</b></div>
    <div>Sleeping Entities<b>${monitor.metrics.sleepingCount}</b></div>
    <div>Blocked Entities<b>${monitor.metrics.blockedCount}</b></div>
    <div>Burn Rate / Hr<b>${money(monitor.currentCostBurnRateUsdPerHour, 4)}</b></div>
    <div>Session Cost<b>${money(monitor.costThisSessionUsd, 4)}</b></div>
    <div>Today Cost<b>${money(monitor.costTodayUsd, 4)}</b></div>
    <div>Month Cost<b>${money(monitor.costThisMonthUsd, 4)}</b></div>
    <div>API Calls Logged<b>${monitor.metrics.apiCallsLogged}</b></div>
    <div>Tokens Logged<b>${monitor.metrics.totalTokensLogged}</b></div>
    <div>Usage Boundary<b>Workflow Token</b></div>
  `;

  const targetSelect = $("arm-target");
  const previous = targetSelect.value;
  const targets = monitor.entities.map(entity => entity.office);
  targetSelect.innerHTML = targets.map(target => `<option value="${target}">${target}</option>`).join("");
  targetSelect.value = targets.includes(previous) ? previous : targets[0];

  $("arm-entities").innerHTML = monitor.entities.map(entity => `
    <div class="api-entity ${entity.current_state.toLowerCase()}">
      <b>${entity.organization}</b>
      <span>${entity.office}</span>
      <strong>${entity.current_state}</strong>
      <div>
        Task ${entity.current_task || "None"} / Trigger ${entity.trigger_source || "None"} / Event ${entity.trigger_event || "None"}<br />
        Runtime ${entity.runtime_duration_seconds}s of ${entity.maximum_runtime_seconds}s / Calls ${entity.api_calls_this_task} / Tokens ${entity.tokens_this_task}<br />
        Cost ${money(entity.cost_this_task_usd, 4)} / Budget Remaining ${money(entity.budget_remaining_usd, 4)} / Audit ${entity.audit_identifier}
      </div>
    </div>
  `).join("");

  $("arm-traces").innerHTML = monitor.activeActivationChains.length
    ? monitor.activeActivationChains.map(trace => `
      <div class="api-call-row">
        <b>${trace.trace_id}</b>
        <span>${trace.chain.join(" > ")}</span>
        <strong>${trace.status}</strong>
      </div>
    `).join("")
    : `<div class="alert-empty">No activation chains</div>`;

  $("arm-calls").innerHTML = monitor.recentApiCalls.length
    ? monitor.recentApiCalls.map(call => `
      <div class="api-call-row">
        <b>${call.call_id}</b>
        <span>${call.organization} / ${call.office}</span>
        <span>${call.workflow}</span>
        <strong>${money(call.estimated_cost_usd, 4)}</strong>
        <div>
          Model ${call.model} / Prompt ${call.prompt_tokens} / Completion ${call.completion_tokens} / Total ${call.total_tokens}<br />
          Mode ${call.execution_mode || "unknown"} / Provider ${call.provider || "none"} / ${call.usage_classification || "unclassified"}<br />
          Scope ${call.workflow_id || "None"} / Token ${call.workflow_token_id || "None"} / Validation ${call.validation_status || "UNKNOWN"}<br />
          Trigger ${call.trigger_source} / Output ${call.output_summary} / Audit ${call.audit_identifier}
        </div>
      </div>
    `).join("")
    : `<div class="alert-empty">No API calls logged</div>`;

  const gateway = state.apiExecutionGateway || { events: [] };
  $("gateway-events").innerHTML = gateway.events.length
    ? gateway.events.map(event => `
      <div class="api-call-row">
        <b>${new Date(event.timestamp).toLocaleTimeString()}</b>
        <span>${event.workflow_id}</span>
        <span>${event.workflow_stage} / ${event.requesting_office}</span>
        <strong>${event.allowed ? "VALID" : event.violation_code}</strong>
        <div>
          Mode ${event.execution_mode || "unknown"} / Provider ${event.provider || "none"} / Model ${event.model} / Cost ${money(event.actual_cost_usd, 4)} / Tokens ${event.input_tokens + event.output_tokens}<br />
          Validation ${event.validation_status || "UNKNOWN"} / Fallback ${event.fallback_used ? "YES" : "NO"} / Decision ${event.decision_object_id || "None"}<br />
          Audit ${event.audit_identifier}${event.violation_reason ? ` / ${event.violation_reason}` : ""}
        </div>
      </div>
    `).join("")
    : `<div class="alert-empty">No API Execution Gateway events</div>`;

  const budgetStops = monitor.budgetStops.map(item => ({
    severity: item.severity,
    category: item.category,
    summary: item.summary,
    status: "OPEN",
  }));
  const alerts = [...monitor.runtimeAlerts, ...budgetStops];
  $("arm-alerts").innerHTML = alerts.length
    ? alerts.map(alert => `<div class="infra-row ${alert.severity.toLowerCase()}"><b>${alert.severity}</b><span>${alert.category}</span><span>${alert.summary}</span><strong>${alert.status}</strong></div>`).join("")
    : `<div class="alert-empty">No API runtime alerts</div>`;
  renderApiRuntimeLiveFeed(monitor);
}

function drawApiRuntimeCostChart(series, totals) {
  const canvas = $("arm-cost-chart");
  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  const offices = Object.entries(totals || {})
    .sort((left, right) => Number(right[1]) - Number(left[1]))
    .map(([office]) => office);
  const colors = ["#35c6ff", "#53ff5c", "#efb13e", "#ff534a", "#9b56ff", "#62d7e6", "#4e63ff", "#ad64e8"];
  const points = series && series.length ? series : [{ totalsUsd: totals || {} }];
  const maxValue = Math.max(0.01, ...points.flatMap(point => offices.map(office => Number(point.totalsUsd[office] || 0))));

  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "rgba(5, 13, 22, .96)";
  ctx.fillRect(0, 0, width, height);
  ctx.strokeStyle = "rgba(143,166,187,.18)";
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const y = 28 + (height - 72) * (i / 4);
    ctx.beginPath();
    ctx.moveTo(58, y);
    ctx.lineTo(width - 26, y);
    ctx.stroke();
  }
  ctx.fillStyle = "#8fa6bb";
  ctx.font = "12px Segoe UI";
  ctx.fillText(`$${maxValue.toFixed(4)}`, 8, 30);
  ctx.fillText(`$${(maxValue / 2).toFixed(4)}`, 8, Math.round(height / 2));
  ctx.fillText("$0", 30, height - 36);

  offices.forEach((office, officeIndex) => {
    ctx.strokeStyle = colors[officeIndex % colors.length];
    ctx.lineWidth = officeIndex === 0 ? 4 : 3;
    ctx.beginPath();
    points.forEach((point, index) => {
      const x = 62 + (points.length === 1 ? 0 : index * ((width - 92) / (points.length - 1)));
      const value = Number(point.totalsUsd[office] || 0);
      const y = height - 42 - (value / maxValue) * (height - 82);
      if (index === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    const lastPoint = points[points.length - 1] || { totalsUsd: {} };
    const value = Number(lastPoint.totalsUsd[office] || 0);
    const y = height - 42 - (value / maxValue) * (height - 82);
    ctx.fillStyle = colors[officeIndex % colors.length];
    ctx.beginPath();
    ctx.arc(width - 28, y, officeIndex === 0 ? 5 : 4, 0, Math.PI * 2);
    ctx.fill();
  });
}

function renderApiRuntimeCostLegend(totals, entities) {
  const colors = ["#35c6ff", "#53ff5c", "#efb13e", "#ff534a", "#9b56ff", "#62d7e6", "#4e63ff", "#ad64e8"];
  const entityByOffice = Object.fromEntries((entities || []).map(entity => [entity.office, entity]));
  const ranked = Object.entries(totals || {}).sort((left, right) => Number(right[1]) - Number(left[1]));
  const totalSpend = ranked.reduce((sum, [, value]) => sum + Number(value || 0), 0);
  const maxSpend = ranked.length ? Number(ranked[0][1] || 0) : 0;
  $("arm-cost-legend").innerHTML = ranked.map(([office, value], index) => {
    const amount = Number(value || 0);
    const share = totalSpend ? Math.round((amount / totalSpend) * 100) : 0;
    const entity = entityByOffice[office] || {};
    const over = amount > 0 && amount >= maxSpend * 0.75;
    return `
      <div class="api-cost-item ${over ? "overutilized" : ""}">
        <i style="background:${colors[index % colors.length]}"></i>
        <b>${office}</b>
        <span>${entity.organization || "ARGOS"}</span>
        <strong>${money(amount, 4)}</strong>
        <em>${share}%</em>
      </div>
    `;
  }).join("");
}

function renderApiRuntimeLiveFeed(monitor) {
  const panel = $("arm-live-feed-panel");
  panel.classList.toggle("hidden", !apiRuntimeLiveFeedOpen);
  $("arm-live-feed").textContent = apiRuntimeLiveFeedOpen ? "Close Live Feed" : "Open Live Feed";
  if (!apiRuntimeLiveFeedOpen) return;
  const entityRows = monitor.entities.slice(0, 8).map(entity => `
    <div class="api-live-row">
      <b>${entity.current_state}</b>
      <span>${entity.organization} / ${entity.office}</span>
      <span>${entity.current_task || "No active task"}</span>
      <strong>${money(entity.cost_this_task_usd, 4)}</strong>
    </div>
  `);
  const callRows = monitor.recentApiCalls.slice(0, 8).map(call => `
    <div class="api-live-row">
      <b>${call.call_id}</b>
      <span>${call.office}</span>
      <span>${call.output_summary}</span>
      <strong>${call.total_tokens} tokens</strong>
    </div>
  `);
  const alertRows = monitor.runtimeAlerts.slice(0, 6).map(alert => `
    <div class="api-live-row ${alert.severity.toLowerCase()}">
      <b>${alert.severity}</b>
      <span>${alert.category}</span>
      <span>${alert.summary}</span>
      <strong>${alert.status}</strong>
    </div>
  `);
  $("arm-live-feed-stream").innerHTML = [...entityRows, ...callRows, ...alertRows].join("") || `<div class="alert-empty">No runtime feed events yet</div>`;
}

function renderPromptContract() {
  if (!state.promptContract) return;
  const contract = state.promptContract;
  $("prompt-contract-summary").innerHTML = [
    ["Engineering Order", contract.engineeringOrder],
    ["Contract Version", contract.contractVersion],
    ["Temperature", contract.defaultTemperature],
    ["Top P", contract.topP],
    ["Provider Independent", contract.providerIndependent ? "YES" : "NO"],
    ["Templates", contract.templates.length],
  ].map(([label, value]) => `<div><span>${label}</span><b>${value}</b></div>`).join("");
  $("prompt-contract-validation").innerHTML = contract.validationPipeline.map((step, index) => `
    <div class="infra-row"><b>${index + 1}</b><span>${step}</span><strong>REQUIRED</strong></div>
  `).join("");
  $("prompt-contract-templates").innerHTML = contract.templates.map(template => `
    <div class="api-call-row">
      <b>${template.office}</b>
      <span>${template.prompt_template_id}</span>
      <strong>v${template.prompt_version}</strong>
      <div>
        Office ${template.office_version} / Schema ${template.schema_version} / Max ${template.maximum_input_tokens}+${template.maximum_output_tokens} tokens / ${money(template.maximum_reasoning_cost_usd, 4)}<br />
        ${template.output_schema.join(", ")}
      </div>
    </div>
  `).join("");
  $("prompt-contract-responsibilities").innerHTML = Object.entries(contract.officeResponsibilities).map(([office, responsibility]) => `
    <div class="infra-row"><b>${office}</b><span>${responsibility}</span><strong>BOUND</strong></div>
  `).join("");
}

function renderControlledCognitivePilot() {
  if (!state.controlledCognitivePilot) return;
  const pilot = state.controlledCognitivePilot;
  $("cognitive-pilot-summary").innerHTML = [
    ["Engineering Order", pilot.engineeringOrder],
    ["Status", pilot.status],
    ["Enabled", pilot.enabled ? "YES" : "NO"],
    ["Success", pilot.success ? "YES" : "NO"],
    ["Real AI Office", pilot.realAiOffice],
    ["Workflow Type", pilot.workflowType],
    ["Max Workflows", pilot.limits.maximum_session_workflows],
    ["Max Cost", money(pilot.limits.maximum_total_pilot_cost_usd, 4)],
  ].map(([label, value]) => `<div><span>${label}</span><b>${value}</b></div>`).join("");
  $("cognitive-pilot-objectives").innerHTML = Object.entries(pilot.missionObjectives || {}).map(([name, passed]) => `
    <div class="infra-row ${passed ? "notice" : "warning"}"><b>${passed ? "PASS" : "CHECK"}</b><span>${name}</span><strong>${passed ? "VALID" : "OPEN"}</strong></div>
  `).join("");
  $("cognitive-pilot-report").innerHTML = Object.entries(pilot.report || {}).map(([label, value]) => `
    <div><span>${label}</span><b>${Array.isArray(value) ? value.join(", ") : value}</b></div>
  `).join("");
  $("cognitive-pilot-alerts").innerHTML = pilot.alerts.length
    ? pilot.alerts.map(alert => `<div class="infra-row ${alert.severity.toLowerCase()}"><b>${alert.severity}</b><span>${alert.category}</span><strong>${alert.summary}</strong></div>`).join("")
    : `<div class="alert-empty">No pilot alerts</div>`;
  $("cognitive-pilot-workflows").innerHTML = pilot.realApiCallsByWorkflow.length
    ? pilot.realApiCallsByWorkflow.map(item => `<div class="api-call-row"><b>${item.workflowId}</b><span>Real API calls</span><strong>${item.realApiCalls}</strong></div>`).join("")
    : `<div class="alert-empty">No real API pilot workflow calls recorded</div>`;
}

function renderWorkflowOrchestrator() {
  if (!state.workflowOrchestrator) return;
  const orchestrator = state.workflowOrchestrator;
  const workflowSelect = $("ewo-workflow-select");
  const previous = workflowSelect.value;
  workflowSelect.innerHTML = orchestrator.workflows.length
    ? orchestrator.workflows.map(workflow => `<option value="${workflow.workflow_id}">${workflow.workflow_id} / ${workflow.token.workflow_status}</option>`).join("")
    : `<option value="">No workflows</option>`;
  workflowSelect.value = orchestrator.workflows.some(workflow => workflow.workflow_id === previous) ? previous : (orchestrator.workflows[0]?.workflow_id || "");
  const selected = orchestrator.workflows.find(workflow => workflow.workflow_id === workflowSelect.value) || orchestrator.workflows[0];
  $("ewo-token").innerHTML = selected ? `
    <div><span>Workflow</span><b>${selected.token.workflow_id}</b></div>
    <div><span>Status</span><b>${selected.token.workflow_status}</b></div>
    <div><span>Current Owner</span><b>${selected.token.current_owner || "None"}</b></div>
    <div><span>Previous Owner</span><b>${selected.token.previous_owner || "None"}</b></div>
    <div><span>Next Owner</span><b>${selected.token.next_owner || "None"}</b></div>
    <div><span>Stage</span><b>${selected.token.workflow_stage}</b></div>
    <div><span>Runtime Budget</span><b>${selected.token.runtime_budget}</b></div>
    <div><span>Credit Budget</span><b>${money(selected.token.credit_budget, 4)}</b></div>
    <div><span>Transfers</span><b>${selected.token.transfer_count}</b></div>
    <div><span>Audit</span><b>${selected.token.audit_identifier}</b></div>
  ` : `<div class="alert-empty">No workflow token created</div>`;
  $("ewo-metrics").innerHTML = Object.entries(orchestrator.metrics).map(([name, value]) => `
    <div>${label(name)}<b>${value}</b></div>
  `).join("");
  $("ewo-workflows").innerHTML = orchestrator.workflows.length
    ? orchestrator.workflows.map(workflow => `
      <div class="workflow-row">
        <b>${workflow.workflow_id}</b>
        <span>${workflow.name}</span>
        <strong>${workflow.token.workflow_status}</strong>
        <div>
          Owner ${workflow.token.current_owner || "None"} / Stage ${workflow.token.workflow_stage} / Runtime ${workflow.runtime_used}/${workflow.token.runtime_budget}<br />
          Credits ${money(workflow.credits_used, 4)}/${money(workflow.token.credit_budget, 4)} / Validation ${workflow.validation_status}<br />
          Offices ${Object.entries(workflow.office_states).map(([office, status]) => `${office}:${status}`).join(" | ")}
        </div>
      </div>
    `).join("")
    : `<div class="alert-empty">No workflows created</div>`;
  $("ewo-audit").innerHTML = orchestrator.auditHistory.length
    ? orchestrator.auditHistory.slice().reverse().map(item => `
      <div class="workflow-audit-row">
        <b>${item.audit_id}</b>
        <span>${item.workflow_id}</span>
        <span>${item.previous_owner || "None"} > ${item.current_owner || "Completed"}</span>
        <strong>${item.validation_status}</strong>
      </div>
    `).join("")
    : `<div class="alert-empty">No ownership transfers audited</div>`;
}

function renderWorkflowRuntimeMonitor() {
  if (!state.workflowRuntimeMonitor) return;
  const monitor = state.workflowRuntimeMonitor;
  $("wrm-health").innerHTML = Object.entries(monitor.enterpriseHealth).filter(([name]) => name !== "sourceMetrics").map(([name, value]) => `
    <div>${label(name)}<b>${value}</b></div>
  `).join("");
  const liveWorkflows = monitor.liveWorkflowExecution || [];
  const batonViews = monitor.workflowBatonView || [];
  const workflow = monitor.activeWorkflow || liveWorkflows[0] || monitor.allWorkflows[0];
  const baton = monitor.workflowBaton || batonViews.find(item => item.workflowIdentifier === workflow?.workflowIdentifier) || batonViews[0];
  const integrity = monitor.tokenIntegrity || {};
  $("wrm-token-movement").innerHTML = workflow ? `
    <div class="current-owner-card">
      <b>${workflow.currentOwner || "None"}</b>
      <span>Current Owner</span>
      <strong>${workflow.stageLabel || `Stage ${workflow.stageNumber || 0} of ${workflow.stageCount || 0}`}</strong>
      <em>LAW VII: ${integrity.status || workflow.lawViiStatus}</em>
    </div>
    <div class="token-track">
      ${(baton ? baton.stages : Object.entries(workflow.stageProgress).map(([stage, status]) => ({ stage, state: status.toUpperCase() }))).map(item => `
        <span class="${(item.status || item.state).toLowerCase()}">
          <b>${item.stage_name || item.stage}</b>
          <em>${item.status || item.state}</em>
        </span>
      `).join("")}
    </div>
    <div class="workflow-progress"><span style="width:${workflow.progress}%"></span></div>
    <div class="token-caption">
      <b>${monitor.commanderStatusLine || workflow.commanderStatusLine}</b><br />
      ${monitor.commanderStatusDetail || workflow.commanderStatusDetail}<br />
      Active workflow: <b>${workflow.workflowName}</b> / token: <b>${workflow.tokenId || workflow.auditIdentifier}</b><br />
      Owner: <b>${workflow.currentOwner || "None"}</b> / previous: <b>${workflow.previousOwner || "None"}</b> / next: <b>${workflow.nextOwner || "None"}</b> / stage: <b>${workflow.workflowStage}</b><br />
      Progress: <b>${workflow.progress}%</b> / runtime: <b>${workflow.elapsedRuntime}s</b> / outputs: <b>${workflow.structuredOutputsProduced}</b> / transfers: <b>${workflow.transferCount}</b> / health: <b>${workflow.executionHealth}</b>
    </div>
  ` : `<div class="alert-empty">No Workflow Execution Token observed</div>`;
  $("wrm-workflows").innerHTML = monitor.allWorkflows.length
    ? monitor.allWorkflows.map(item => `
      <div class="wrm-workflow ${item.executionHealth.toLowerCase()}">
        <b>${item.workflowIdentifier}</b>
        <span>${item.workflowName}</span>
        <strong>${item.status}</strong>
        <div>
          Progress ${item.progress}% / Priority ${item.priority} / Stage ${item.workflowStage}<br />
          Current ${item.currentOwner || "None"} / Previous ${item.previousOwner || "None"} / Next ${item.nextOwner || "None"}<br />
          Runtime ${item.runtimeConsumed}/${item.runtimeBudget} / Remaining ${item.estimatedRemainingRuntime} / Credits ${money(item.creditsConsumed, 4)} remaining ${money(item.creditsRemaining, 4)}<br />
          Token ${item.tokenId} / Transfers ${item.transferCount} / Outputs ${item.structuredOutputsProduced} / Waiting ${item.waitingOffices.join(", ") || "None"}<br />
          LAW VII ${item.lawViiStatus}${item.lawViiViolationReason ? ` / ${item.lawViiViolationReason}` : ""} / Audit ${item.auditIdentifier}
        </div>
      </div>
    `).join("")
    : `<div class="alert-empty">No workflows observed</div>`;
  $("wrm-recent-completed").innerHTML = (monitor.recentCompletedWorkflows || []).length
    ? monitor.recentCompletedWorkflows.slice().reverse().map(item => `
      <div class="wrm-workflow ${item.executionHealth.toLowerCase()}">
        <b>${item.workflowIdentifier}</b>
        <span>${item.workflowName}</span>
        <strong>${item.progress}% ${item.status}</strong>
        <div>Final stage ${item.workflowStage} / Previous ${item.previousOwner || "None"} / Transfers ${item.transferCount} / Credits ${money(item.creditsConsumed, 4)} / Health ${item.executionHealth}</div>
      </div>
    `).join("")
    : `<div class="alert-empty">No completed workflow retention records</div>`;
  $("wrm-timeline").innerHTML = monitor.timeline.length
    ? (monitor.workflowTimeline || monitor.timeline).slice().reverse().map(event => `
      <div class="wrm-timeline-row">
        <b>${event.event_type}</b>
        <span>${event.workflow_id}</span>
        <span>${event.stage || "None"} / ${event.owner || "None"}</span>
        <strong>${new Date(event.timestamp || event.timestamp_utc).toLocaleTimeString()} / ${event.audit_identifier || "NO-AUDIT"}</strong>
        <small>${event.message || ""}</small>
      </div>
    `).join("")
    : `<div class="alert-empty">No workflow timeline events</div>`;
  const lawClass = integrity.status === "VALID" ? "notice" : "critical";
  const lawSummary = integrity.status === "VALID"
    ? "Exclusive Workflow Execution Token ownership is valid."
    : `${integrity.violation_code}: ${integrity.violation_reason} / offending ${integrity.offending_office || "unknown"} expected ${integrity.expected_owner || "unknown"}`;
  $("wrm-token-integrity").innerHTML = (monitor.workflowTokenIntegrityPanel || []).length
    ? `<div class="infra-row ${lawClass}"><b>LAW VII: ${integrity.status || "VALID"}</b><span>${integrity.workflow_id || "Enterprise"}</span><span>${lawSummary}</span><strong>${integrity.token_id || "ALL"}</strong></div>` + monitor.workflowTokenIntegrityPanel.map(item => `
      <div class="infra-row ${item.lawViiStatus === "VALID" ? "notice" : "critical"}">
        <b>${item.lawViiStatus}</b>
        <span>${item.workflowIdentifier}</span>
        <span>${item.currentStage} / owner ${item.currentOwner || "None"} / previous ${item.previousOwner || "None"} / next ${item.nextOwner || "None"}</span>
        <strong>${item.tokenId}</strong>
      </div>
    `).join("")
    : `<div class="alert-empty">No workflow token integrity records</div>`;
  $("wrm-alerts").innerHTML = monitor.commanderAlerts.length
    ? monitor.commanderAlerts.map(alert => `
      <div class="infra-row ${alert.severity.toLowerCase()}"><b>${alert.severity}</b><span>${alert.category}</span><span>${alert.summary}</span><strong>${alert.workflow_id}</strong></div>
    `).join("")
    : `<div class="alert-empty">No workflow runtime alerts</div>`;
}

function renderLppc() {
  if (!state.lppc) return;
  const select = $("lppc-portfolio-select");
  const previous = selectedPortfolioId || select.value;
  select.innerHTML = state.lppc.portfolios.map(portfolio => `<option value="${portfolio.portfolio_id}">${portfolio.portfolio_name}</option>`).join("");
  selectedPortfolioId = state.lppc.portfolios.some(portfolio => portfolio.portfolio_id === previous) ? previous : "PORT-ENTERPRISE-001";
  select.value = selectedPortfolioId;
  const portfolio = state.lppc.portfolios.find(item => item.portfolio_id === selectedPortfolioId) || state.lppc.combinedPortfolio;
  $("lppc-summary").innerHTML = `
    <div>Portfolio Value<b>${money(portfolio.portfolio_value)}</b></div>
    <div>Buying Power<b>${money(portfolio.buying_power)}</b></div>
    <div>Cash Position<b>${money(portfolio.cash_position)}</b></div>
    <div>Open Positions<b>${portfolio.open_positions}</b></div>
    <div>Realized P&L<b>${money(portfolio.realized_pnl)}</b></div>
    <div>Unrealized P&L<b>${money(portfolio.unrealized_pnl)}</b></div>
    <div>Daily Return<b>${portfolio.daily_return}%</b></div>
    <div>Lifetime Return<b>${portfolio.lifetime_return}%</b></div>
  `;
  $("lppc-performance").innerHTML = Object.entries(portfolio.performance_metrics).map(([name, value]) => `
    <div>${label(name)}<b>${value}</b></div>
  `).join("");
  const risk = portfolio.risk_metrics;
  $("lppc-risk").innerHTML = `
    <div>Exposure<b>${money(risk.portfolioExposure)}</b></div>
    <div>Correlation<b>${risk.correlation}</b></div>
    <div>Volatility<b>${risk.volatility}</b></div>
    <div>Liquidity<b>${risk.liquidity}</b></div>
    <div>Value At Risk<b>${money(risk.valueAtRisk)}</b></div>
    <div>Max Drawdown<b>${money(risk.maximumDrawdown)}</b></div>
    <div>Concentration<b>${risk.positionConcentration}%</b></div>
  `;
  $("lppc-sync").innerHTML = Object.entries(state.lppc.synchronization).map(([name, value]) => `
    <div>${label(name)}<b>${value}</b></div>
  `).join("");
  $("lppc-positions").innerHTML = portfolio.positions.length
    ? portfolio.positions.map(position => `
      <div class="portfolio-position">
        <b>${position.asset}</b>
        <span>${position.position_id}</span>
        <strong>${money(position.market_value)}</strong>
        <div>
          Qty ${position.quantity} / UPL ${money(position.unrealized_pnl)} / RPL ${money(position.realized_pnl)}<br />
          Orders ${position.order_ids.join(", ")} / Decision ${position.executive_decision_id} / Case ${position.case_file_id}<br />
          Evidence ${position.supporting_evidence.join(", ")} / History ${position.historical_performance_id}
        </div>
      </div>
    `).join("")
    : `<div class="alert-empty">No open positions for selected portfolio</div>`;
  $("lppc-detections").innerHTML = state.lppc.detections.length
    ? state.lppc.detections.map(item => `<div class="infra-row ${item.severity.toLowerCase()}"><b>${item.severity}</b><span>${item.category}</span><span>${item.summary}</span><strong>${item.detection_id}</strong></div>`).join("")
    : `<div class="alert-empty">No portfolio inconsistencies detected</div>`;
}

function renderStrategyPerformanceConsole() {
  const consoleState = state.strategyPerformanceConsole;
  if (!consoleState) return;
  const portfolio = consoleState.livePortfolioPanel;
  $("spc-portfolio").innerHTML = `
    <div>Portfolio Value<b>${money(portfolio.portfolioValue)}</b></div>
    <div>Cash<b>${money(portfolio.cash)}</b></div>
    <div>Buying Power<b>${money(portfolio.buyingPower)}</b></div>
    <div>Unrealized P/L<b>${money(portfolio.unrealizedPnl)}</b></div>
    <div>Realized P/L<b>${money(portfolio.realizedPnl)}</b></div>
    <div>Today's Return<b>${portfolio.todaysReturn}%</b></div>
    <div>Total Return<b>${money(portfolio.totalReturn)}</b></div>
    <div>Total Return %<b>${portfolio.totalReturnPercent}%</b></div>
    <div>Daily Return %<b>${portfolio.dailyReturnPercent}%</b></div>
    <div>Weekly Return %<b>${portfolio.weeklyReturnPercent}%</b></div>
    <div>Monthly Return %<b>${portfolio.monthlyReturnPercent}%</b></div>
    <div>Annual Return %<b>${portfolio.annualReturnPercent}%</b></div>
    <div>Maximum Drawdown<b>${money(portfolio.maximumDrawdown)}</b></div>
    <div>Sharpe Ratio<b>${portfolio.sharpeRatio}</b></div>
    <div>Sortino Ratio<b>${portfolio.sortinoRatio}</b></div>
    <div>Profit Factor<b>${portfolio.profitFactor}</b></div>
    <div>Expectancy<b>${money(portfolio.expectancy)}</b></div>
    <div>Current Exposure<b>${money(portfolio.currentExposure)}</b></div>
    <div>Positions<b>${portfolio.numberOfPositions}</b></div>
  `;
  $("spc-scorecard").innerHTML = Object.entries(consoleState.enterpriseScorecard).map(([name, value]) => `
    <div>${label(name)}<b>${typeof value === "number" ? value : value}</b></div>
  `).join("");
  $("spc-benchmarks").innerHTML = consoleState.marketBenchmarks.map(item => `
    <div class="infra-row ${item.alpha >= 0 ? "notice" : "warning"}">
      <b>${item.benchmark}</b>
      <span>ARGOS ${item.argosReturnPercent}% / Benchmark ${item.benchmarkReturnPercent}%</span>
      <span>${item.relativePerformance}</span>
      <strong>Alpha ${item.alpha}</strong>
    </div>
  `).join("");
  $("spc-alerts").innerHTML = consoleState.performanceAlerts.length
    ? consoleState.performanceAlerts.map(alert => `<div class="infra-row ${alert.severity.toLowerCase()}"><b>${alert.severity}</b><span>${alert.category}</span><span>${alert.summary}</span><strong>${alert.alert_id}</strong></div>`).join("")
    : `<div class="alert-empty">No performance alerts</div>`;
  const decision = consoleState.decisionObjectPanel;
  $("spc-decision").innerHTML = decision.decisionObjectId ? `
    <div class="api-call">
      <b>${decision.decisionObjectId}</b>
      <span>${decision.workflowId}</span>
      <div>
        Stage ${decision.currentStage || "Complete"} / Owner ${decision.currentOwner || "None"} / Revision ${decision.currentRevision}<br />
        Confidence ${decision.currentConfidence} / Recommendation ${decision.currentRecommendation} / Risk ${decision.riskScore}<br />
        Evidence ${decision.evidenceCount} / Signals ${(decision.supportingSignals || []).join(", ")}<br />
        Size ${decision.positionSizeRecommendation} / Target ${money(decision.targetPrice)} / Stop ${money(decision.stopLoss)} / Expected ${decision.expectedReturn}
      </div>
    </div>
  ` : `<div class="alert-empty">No active Decision Object</div>`;
  $("spc-decision-evolution").innerHTML = consoleState.decisionObjectEvolution.length
    ? consoleState.decisionObjectEvolution.slice(-4).reverse().map(item => `
      <div class="api-call">
        <b>${item.decisionObjectId}</b>
        <span>${item.workflowId} / ${item.revisionCount} revisions</span>
        <div>${item.revisions.map(revision => `Revision ${revision.revision}: ${revision.office} -> ${revision.recommendation} (${revision.confidence})`).join("<br />")}</div>
      </div>
    `).join("")
    : `<div class="alert-empty">No Decision Object revisions yet</div>`;
  $("spc-positions").innerHTML = consoleState.currentPositions.length
    ? consoleState.currentPositions.map(position => `
      <div class="portfolio-position">
        <b>${position.ticker}</b>
        <span>${position.direction} / ${position.currentStrategy}</span>
        <strong>${money(position.marketValue)}</strong>
        <div>
          Entry ${money(position.entryPrice)} / Current ${money(position.currentPrice)} / P/L ${money(position.currentGainLoss)} (${position.gainLossPercent}%)<br />
          Size ${position.positionSize} / Risk ${position.riskRating} / Workflow ${position.owningWorkflow}<br />
          Decision ${position.decisionObjectId}
        </div>
      </div>
    `).join("")
    : `<div class="alert-empty">No current positions</div>`;
  $("spc-trades").innerHTML = consoleState.tradeStream.length
    ? consoleState.tradeStream.slice(-12).reverse().map(trade => `
      <div class="api-call">
        <b>${trade.ticker} ${trade.action}</b>
        <span>${trade.workflow}</span>
        <div>${trade.timestamp} / Qty ${trade.quantity} @ ${money(trade.price)} / P/L ${money(trade.profitLoss)} / ${trade.strategy}</div>
      </div>
    `).join("")
    : `<div class="alert-empty">No completed trades yet</div>`;
  $("spc-workflows").innerHTML = consoleState.workflowContribution.slice(-8).reverse().map(item => `
    <div class="api-call"><b>${item.workflow}</b><span>${item.tradesGenerated} trades</span><div>Avg ${money(item.averageReturn)} / Win ${item.winRate}% / PF ${item.profitFactor} / Capital ${money(item.capitalGenerated)} / Confidence ${item.averageConfidence}</div></div>
  `).join("") || `<div class="alert-empty">No workflow contribution yet</div>`;
  $("spc-offices").innerHTML = consoleState.officeContribution.map(item => `
    <div class="api-call"><b>${item.office}</b><span>${item.structuredOutputsProduced} outputs</span><div>Improvements ${item.decisionImprovements} / Risk Adj ${item.riskAdjustments} / Approvals ${item.tradeApprovals} / Accuracy ${item.historicalAccuracy}% / Conf +${item.averageConfidenceIncrease}</div></div>
  `).join("");
  $("spc-strategies").innerHTML = consoleState.strategyLeaderboard.map(item => `
    <div class="api-call"><b>${item.strategyName}</b><span>${item.currentStatus}</span><div>Capital ${money(item.capitalAllocated)} / Trades ${item.trades} / Win ${item.winRate}% / Avg ${money(item.averageReturn)} / Sharpe ${item.sharpeRatio} / Improved ${item.lastImprovementDate}</div></div>
  `).join("");
  drawStrategyEquityCurve(consoleState.liveEquityCurve);
}

function drawStrategyEquityCurve(points) {
  const canvas = $("spc-equity-chart");
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#071018";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = "rgba(144,164,181,0.25)";
  ctx.lineWidth = 1;
  for (let i = 1; i <= 4; i += 1) {
    const y = (canvas.height / 5) * i;
    ctx.beginPath();
    ctx.moveTo(42, y);
    ctx.lineTo(canvas.width - 24, y);
    ctx.stroke();
  }
  const rows = points && points.length ? points : [{ portfolio: 0, benchmark: 0, alpha: 0, drawdown: 0 }];
  const values = rows.flatMap(item => [item.portfolio, item.benchmark]);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = Math.max(1, max - min);
  const xFor = index => 42 + (index / Math.max(1, rows.length - 1)) * (canvas.width - 72);
  const yFor = value => canvas.height - 28 - ((value - min) / range) * (canvas.height - 58);
  const drawLine = (key, color) => {
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.beginPath();
    rows.forEach((item, index) => {
      const x = xFor(index);
      const y = yFor(item[key]);
      if (index === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
  };
  drawLine("portfolio", "#59d66d");
  drawLine("benchmark", "#62c7f2");
  ctx.fillStyle = "#90a4b5";
  ctx.font = "12px Inter, sans-serif";
  ctx.fillText(`Portfolio ${money(rows[rows.length - 1].portfolio)}`, 52, 22);
  ctx.fillText(`Benchmark ${money(rows[rows.length - 1].benchmark)}`, 220, 22);
  ctx.fillText(`Alpha ${rows[rows.length - 1].alpha}`, 410, 22);
}

function renderDecisionLaboratory() {
  const lab = state.decisionLaboratory;
  if (!lab) return;
  const workflowSelect = $("dl-workflow-select");
  const selectedWorkflow = workflowSelect.value || (lab.workflowReplay[0] ? lab.workflowReplay[0].workflowId : "");
  workflowSelect.innerHTML = lab.workflowReplay.map(item => `<option value="${item.workflowId}">${item.workflowId} / ${item.decisionObjectId}</option>`).join("");
  workflowSelect.value = lab.workflowReplay.some(item => item.workflowId === selectedWorkflow) ? selectedWorkflow : (lab.workflowReplay[0] ? lab.workflowReplay[0].workflowId : "");
  const replaySelect = $("dl-replay-select");
  const selectedReplay = replaySelect.value || (lab.replaySessions[0] ? lab.replaySessions[0].replay_id : "");
  replaySelect.innerHTML = lab.replaySessions.map(item => `<option value="${item.replay_id}">${item.replay_id} / ${item.status}</option>`).join("");
  replaySelect.value = lab.replaySessions.some(item => item.replay_id === selectedReplay) ? selectedReplay : (lab.replaySessions[0] ? lab.replaySessions[0].replay_id : "");
  $("dl-workflows").innerHTML = lab.workflowReplay.length
    ? lab.workflowReplay.slice(-8).reverse().map(item => `
      <div class="api-call"><b>${item.workflowId}</b><span>${item.decisionObjectId}</span><div>Token ${item.workflowTokenId} / Strategy ${item.strategy} / Outcome ${money(item.portfolioOutcome)} / ${item.executionEnvironment}<br />Offices ${item.officeSequence.join(" -> ")}</div></div>
    `).join("")
    : `<div class="alert-empty">No completed workflow available for replay</div>`;
  $("dl-decision-replay").innerHTML = lab.decisionObjectReplay.length
    ? lab.decisionObjectReplay.slice(-4).reverse().map(item => `
      <div class="api-call"><b>${item.decisionObjectId}</b><span>${item.workflowId}</span><div>${item.revisions.map(rev => `Revision ${rev.revision}: ${rev.office} / ${rev.recommendation} / Confidence ${rev.confidence} / Risk ${rev.risk}`).join("<br />")}</div></div>
    `).join("")
    : `<div class="alert-empty">No Decision Object replay available</div>`;
  $("dl-office-replay").innerHTML = lab.officeContributionReplay.length
    ? lab.officeContributionReplay.slice(-3).reverse().map(item => `
      <div class="api-call"><b>${item.decisionObjectId}</b><span>${item.workflowId}</span><div>${item.offices.map(office => `${office.office}: ${office.question} ${office.changeSummary}`).join("<br />")}</div></div>
    `).join("")
    : `<div class="alert-empty">No office replay available</div>`;
  $("dl-decision-diff").innerHTML = lab.decisionComparisons.length
    ? lab.decisionComparisons.slice(-6).reverse().map(item => `
      <div class="api-call"><b>${item.comparisonId}</b><span>${item.originalDecisionObjectId} -> ${item.experimentDecisionObjectId}</span><div>${Object.entries(item.differences).map(([key, value]) => `${label(key)}: ${Array.isArray(value) ? value.join(" -> ") : value}`).join("<br />")}</div></div>
    `).join("")
    : `<div class="alert-empty">No experiment diff yet</div>`;
  $("dl-performance-comparison").innerHTML = lab.performanceComparisons.length
    ? lab.performanceComparisons.slice(-6).reverse().map(item => `
      <div class="api-call"><b>${item.performanceComparisonId}</b><span>Difference ${item.difference}</span><div>Original ${item.originalOutcome} / Experiment ${item.experimentOutcome} / Alpha ${item.alpha} / Drawdown ${item.drawdown} / Sharpe ${item.sharpe}</div></div>
    `).join("")
    : `<div class="alert-empty">No performance comparison yet</div>`;
  $("dl-historian").innerHTML = lab.historianReports.length
    ? lab.historianReports.slice(-6).reverse().map(item => `
      <div class="api-call"><b>${item.historianReportId}</b><span>${item.performanceTruthSource}</span><div>Outcome Delta ${item.outcomeDifference}<br />Lessons ${item.lessonsLearned.join("; ")}<br />Updates ${item.potentialStrategyUpdates.join(", ")}</div></div>
    `).join("")
    : `<div class="alert-empty">No Historian lab report yet</div>`;
  $("dl-tree").innerHTML = lab.decisionTree.length
    ? lab.decisionTree.map(item => `<div class="api-call"><b>${item.nodeId}</b><span>${item.type}</span><div>Workflow ${item.workflowId} / Children ${(item.children || []).join(", ") || "None"}</div></div>`).join("")
    : `<div class="alert-empty">No decision tree branches yet</div>`;
  $("dl-audit").innerHTML = lab.experimentAudit.length
    ? lab.experimentAudit.slice(-8).reverse().map(item => `<div class="api-call"><b>${item.audit_id}</b><span>${item.action}</span><div>${item.timestamp} / ${item.summary} / Production preserved ${item.immutable_production_preserved ? "YES" : "NO"}</div></div>`).join("")
    : `<div class="alert-empty">No laboratory audit records yet</div>`;
  $("dl-search-results").innerHTML = lab.searchResults.length
    ? lab.searchResults.map(item => `<div class="api-call"><b>${item.type}</b><span>${item.identifier}</span><div>${item.summary}</div></div>`).join("")
    : `<div class="alert-empty">No search results</div>`;
  $("dl-metrics").innerHTML = Object.entries(lab.metrics).map(([key, value]) => `<div>${label(key)}<b>${value}</b></div>`).join("");
}

function selectedDecisionLabWorkflow() {
  return $("dl-workflow-select").value || (state.decisionLaboratory?.workflowReplay[0]?.workflowId || "");
}

function selectedDecisionLabReplay() {
  return $("dl-replay-select").value || (state.decisionLaboratory?.replaySessions[0]?.replay_id || "");
}

function createDecisionLabExperiment() {
  return api("/api/decision-laboratory/experiment", {
    workflowId: selectedDecisionLabWorkflow(),
    parameterChanges: {
      confidence: Number($("dl-confidence").value),
      stopLoss: Number($("dl-stop-loss").value),
      positionSizeRecommendation: Number($("dl-position-size").value),
    },
  });
}

function startDecisionLabReplay() {
  return api("/api/decision-laboratory/replay/start", { workflowId: selectedDecisionLabWorkflow() });
}

function startLatestBridgeReplay() {
  const latestWorkflow = state.decisionLaboratory?.workflowReplay?.slice(-1)[0];
  if (!latestWorkflow) {
    toggleEngineeringMode(true);
    return renderDecisionLaboratory();
  }
  toggleEngineeringMode(true);
  return api("/api/decision-laboratory/replay/start", { workflowId: latestWorkflow.workflowId });
}

function openBridgeLab() {
  toggleEngineeringMode(true);
  const labPanel = document.querySelector(".decision-lab-panel");
  if (labPanel) labPanel.scrollIntoView({ behavior: "smooth", block: "start" });
}

function toggleEngineeringMode(forceOpen) {
  engineeringModeOpen = forceOpen === undefined ? !engineeringModeOpen : Boolean(forceOpen);
  document.body.classList.toggle("engineering-open", engineeringModeOpen);
  const panel = $("engineering-mode");
  if (panel) panel.classList.toggle("hidden", !engineeringModeOpen);
  const button = $("bridge-engineering");
  if (button) button.textContent = engineeringModeOpen ? "Close Engineering" : "Engineering";
}

function decisionLabReplayControl(action) {
  return api("/api/decision-laboratory/replay/control", {
    replayId: selectedDecisionLabReplay(),
    action,
    value: $("dl-replay-value").value,
  });
}

function searchDecisionLab() {
  const query = encodeURIComponent($("dl-search-query").value || "");
  return fetch(`/api/decision-laboratory/state?q=${query}`)
    .then(response => response.json())
    .then(data => {
      state = data;
      render();
    });
}

function renderInfrastructure() {
  if (!state.infrastructure) return;
  const infra = state.infrastructure;
  $("infra-costs").innerHTML = `
    <div>Daily Tokens<b>${infra.tokenConsumption.dailyTokenUsage}</b></div>
    <div>Monthly Tokens<b>${infra.tokenConsumption.monthlyTokenUsage}</b></div>
    <div>Daily Cost<b>${money(infra.operatingCost.dailyOperatingCostUsd, 4)}</b></div>
    <div>Monthly Cost<b>${money(infra.operatingCost.monthlyOperatingCostUsd, 4)}</b></div>
    <div>Daily Budget Use<b>${infra.operatingCost.dailyBudgetUsagePercent}%</b></div>
    <div>Monthly Budget Use<b>${infra.operatingCost.monthlyBudgetUsagePercent}%</b></div>
  `;
  $("infra-health").innerHTML = Object.entries(infra.infrastructureHealth).map(([name, value]) => `
    <div>${label(name)}<b>${value}</b></div>
  `).join("");
  $("infra-models").innerHTML = infra.aiModelUsage.map(model => `
    <div class="infra-row">
      <b>${model.model}</b>
      <span>${model.dailyTokens} daily tokens</span>
      <span>${model.monthlyTokens} month tokens</span>
      <strong>${model.status}</strong>
    </div>
  `).join("");
  $("infra-alerts").innerHTML = infra.alerts.length
    ? infra.alerts.map(alert => `<div class="infra-row ${alert.severity.toLowerCase()}"><b>${alert.severity}</b><span>${alert.category}</span><span>${alert.summary}</span><strong>${alert.status}</strong></div>`).join("")
    : `<div class="alert-empty">No infrastructure alerts</div>`;
  $("infra-recommendations").innerHTML = infra.optimizationRecommendations.map(item => `
    <div class="infra-row">
      <b>${item.priority}</b>
      <span>${item.category}</span>
      <span>${item.summary}</span>
      <strong>${item.expected_effect}</strong>
    </div>
  `).join("");
  $("infra-daily-budget").value = infra.controls.daily_budget_usd;
  $("infra-monthly-budget").value = infra.controls.monthly_budget_usd;
  $("infra-runtime-limit").value = infra.controls.runtime_limit_minutes;
  $("infra-mode").value = infra.controls.resource_mode;
  const orgSelect = $("infra-org-limit");
  const previous = orgSelect.value;
  const orgs = state.ecc.organizations.map(org => org.name);
  orgSelect.innerHTML = orgs.map(org => `<option value="${org}">${org}</option>`).join("");
  orgSelect.value = orgs.includes(previous) ? previous : orgs[0];
  $("infra-org-budget").value = infra.controls.organization_resource_limits[orgSelect.value] || 0;
}

function renderCommandConsole() {
  if (!state.commandConsole) return;
  const commandSelect = $("cc-command");
  const previousCommand = commandSelect.value;
  const commandNames = Object.keys(state.commandConsole.definitions);
  commandSelect.innerHTML = commandNames.map(command => `<option value="${command}">${command.replaceAll("_", " ")}</option>`).join("");
  commandSelect.value = commandNames.includes(previousCommand) ? previousCommand : commandNames[0];

  const targetSelect = $("cc-target");
  const previousTarget = targetSelect.value;
  const targets = ["", ...state.ecc.organizations.map(org => org.name), "Commander Interface"];
  targetSelect.innerHTML = targets.map(target => `<option value="${target}">${target || "Auto Target"}</option>`).join("");
  targetSelect.value = targets.includes(previousTarget) ? previousTarget : "";

  $("cc-metrics").innerHTML = Object.entries(state.commandConsole.metrics).map(([name, value]) => `
    <div>${label(name)}<b>${value}</b></div>
  `).join("");
  $("cc-detections").innerHTML = Object.entries(state.commandConsole.detections).map(([name, value]) => `
    <div>${label(name)}<b>${value}</b></div>
  `).join("");

  $("cc-macros").innerHTML = Object.keys(state.commandConsole.macros).map(name => `
    <button class="button secondary cc-macro" data-macro="${name}">${name}</button>
  `).join("");

  const response = state.commandConsole.lastResponse;
  $("cc-response").innerHTML = response.command_id ? `
    <b>${response.command_id} / ${response.status}</b><br />
    Command: ${response.command_name}<br />
    Result: ${response.detailed_results}<br />
    Authorization: ${response.validation.commander_authorization}<br />
    Safety: ${response.validation.safety_constraints}<br />
    Next: ${(response.recommended_next_actions || []).join(", ") || "None"}<br />
    Audit: ${response.audit_identifier}
  ` : "No Commander commands issued yet.";

  $("cc-history").innerHTML = state.commandConsole.commands.length
    ? state.commandConsole.commands.map(command => `
      <div class="command-row ${command.status.toLowerCase()}">
        <b>${command.command_id}</b>
        <span>${command.category}</span>
        <strong>${command.status}</strong>
        <div>${command.command_name.replaceAll("_", " ")}<br /><span>${command.target} / ${command.execution_status}</span></div>
        <span>${command.lifecycle.join(" > ")}</span>
      </div>
    `).join("")
    : `<div class="alert-empty">No command history recorded yet</div>`;
}

function renderEcc() {
  const organizations = state.ecc.organizations;
  const select = $("ecc-org-select");
  const previous = selectedOrganization();
  select.innerHTML = organizations.map(org => `<option value="${org.name}">${org.name}</option>`).join("");
  select.value = organizations.some(org => org.name === previous) ? previous : "Executive";
  const org = organizations.find(item => item.name === select.value) || organizations[0];

  $("ecc-org-summary").innerHTML = `
    <div><span>Status</span><b>${org.current_status}</b></div>
    <div><span>Mode</span><b>${org.operating_mode}</b></div>
    <div><span>Workflow</span><b>${org.current_workflow}</b></div>
    <div><span>Task</span><b>${org.current_task}</b></div>
    <div><span>Alerts</span><b>${org.active_alerts.length}</b></div>
  `;

  $("ecc-monitoring").innerHTML = Object.entries(state.ecc.monitoring).map(([name, value]) => `
    <div>${label(name)}<b>${value}</b></div>
  `).join("");

  $("ecc-alerts").innerHTML = state.ecc.alerts.length
    ? state.ecc.alerts.map(alert => `<div class="alert-item"><b>${alert.severity}</b>${alert.organization}: ${alert.message}</div>`).join("")
    : `<div class="alert-empty">No enterprise alerts</div>`;

  const tree = state.ecc.drilldown[org.name];
  const offices = (tree?.offices || []).filter(office => office.workflows.length > 0);
  $("ecc-drilldown").innerHTML = offices.map(office => `
    <div class="drill-office">
      <h3>${office.office}</h3>
      ${office.workflows.map(workflow => `
        <p><b>${workflow.workflow_id}</b> ${workflow.name} / ${workflow.status} / queue ${workflow.queue_length}</p>
        ${workflow.tasks.map(task => `
          <p>${task.task_id}: ${task.name} / ${task.status} / evidence ${task.supporting_evidence_ids.join(", ")} / audit ${task.audit_log_ids.join(", ")}</p>
        `).join("")}
      `).join("")}
    </div>
  `).join("");
}

function renderEab() {
  if (!state.eab) return;
  $("eab-health").innerHTML = Object.entries(state.eab.health).map(([name, value]) => `
    <div>${label(name)}<b>${value}</b></div>
  `).join("");

  $("eab-detections").innerHTML = Object.entries(state.eab.detections).map(([name, value]) => `
    <div>${label(name)}<b>${value}</b></div>
  `).join("");

  const orgFilter = $("eab-filter-org");
  const previous = orgFilter.value;
  const organizations = ["", ...state.ecc.organizations.map(org => org.name), "Commander Interface"];
  orgFilter.innerHTML = organizations.map(org => `<option value="${org}">${org || "All Organizations"}</option>`).join("");
  orgFilter.value = organizations.includes(previous) ? previous : "";

  $("eab-events").innerHTML = state.eab.events.length
    ? state.eab.events.map(event => `
      <div class="event-row ${event.severity.toLowerCase()}">
        <b>${event.event_id}</b>
        <span>${event.organization}</span>
        <strong>${event.severity}</strong>
        <div>${event.summary}<br /><span>${event.workflow} / ${event.task_identifier}</span></div>
        <span>${event.status}</span>
      </div>
    `).join("")
    : `<div class="alert-empty">No enterprise events recorded yet</div>`;
}

function renderCnac() {
  if (!state.cnac) return;
  $("cnac-metrics").innerHTML = Object.entries(state.cnac.metrics).map(([name, value]) => `
    <div>${label(name)}<b>${value}</b></div>
  `).join("");

  $("cnac-detections").innerHTML = Object.entries(state.cnac.detections).map(([name, value]) => `
    <div>${label(name)}<b>${value}</b></div>
  `).join("");

  const orgFilter = $("cnac-filter-org");
  const previous = orgFilter.value;
  const organizations = ["", ...state.ecc.organizations.map(org => org.name), "Commander Interface"];
  orgFilter.innerHTML = organizations.map(org => `<option value="${org}">${org || "All Organizations"}</option>`).join("");
  orgFilter.value = organizations.includes(previous) ? previous : "";

  $("cnac-notifications").innerHTML = state.cnac.notifications.length
    ? state.cnac.notifications.map(note => `
      <div class="notification-row ${note.priority.toLowerCase()}">
        <b>${note.notification_id}</b>
        <strong>${note.priority}</strong>
        <span>${note.notification_type}</span>
        <div>${note.summary}<br /><span>${note.organization} / ${note.office} / ${note.confidence_level}</span></div>
        <button class="button secondary ack-notification" data-id="${note.notification_id}">${note.status}</button>
      </div>
    `).join("")
    : `<div class="alert-empty">No Commander notifications recorded yet</div>`;
}

function renderIoe() {
  if (!state.ioe) return;
  $("ioe-summary").innerHTML = Object.entries(state.ioe.summary).map(([name, value]) => `
    <div>${label(name)}<b>${value}</b></div>
  `).join("");
  $("ioe-detections").innerHTML = Object.entries(state.ioe.detections).map(([name, value]) => `
    <div>${label(name)}<b>${value}</b></div>
  `).join("");

  const orgFilter = $("ioe-filter-org");
  const previous = orgFilter.value;
  const organizations = ["", ...state.ecc.organizations.map(org => org.name), "Enterprise", "Commander Interface"];
  orgFilter.innerHTML = organizations.map(org => `<option value="${org}">${org || "All Organizations"}</option>`).join("");
  orgFilter.value = organizations.includes(previous) ? previous : "";

  const nodes = state.ioe.nodes.slice(0, 120);
  if (!nodes.some(node => node.node_id === selectedIoeNodeId)) {
    selectedIoeNodeId = nodes[0]?.node_id || "ENT-ARGOS";
  }
  $("ioe-nodes").innerHTML = nodes.map(node => `
    <div class="ioe-node ${node.node_id === selectedIoeNodeId ? "selected" : ""}" data-node-id="${node.node_id}">
      <b>${node.identifier}</b>
      <span>${node.node_type}</span>
      <div>${node.label}<br /><span>${node.organization} / ${node.office || "-"}</span></div>
      <span>${node.status}</span>
    </div>
  `).join("");
  renderIoeDetail();
}

function renderIoeDetail() {
  const node = state.ioe.nodes.find(item => item.node_id === selectedIoeNodeId) || state.ioe.nodes[0];
  if (!node) {
    $("ioe-detail").innerHTML = "No explorer object selected.";
    return;
  }
  $("ioe-detail").innerHTML = `
    <b>${node.label}</b><br />
    Identifier: ${node.identifier}<br />
    Status: ${node.status}<br />
    Activity: ${node.current_activity}<br />
    Dependencies: ${node.dependencies.join(", ") || "None"}<br />
    Relationships: ${node.relationships.join(", ") || "None"}<br />
    Evidence: ${node.supporting_evidence.join(", ") || "None"}<br />
    Audit: ${node.audit_information.join(", ") || "None"}
  `;
}

function renderScheduler() {
  if (!state.scheduler) return;
  const orgSelect = $("scheduler-org");
  const officeSelect = $("scheduler-office");
  const previousOrg = orgSelect.value || "Executive";
  const previousOffice = officeSelect.value;
  const organizations = [...new Set(state.scheduler.offices.map(office => office.organization))];
  orgSelect.innerHTML = organizations.map(org => `<option value="${org}">${org}</option>`).join("");
  orgSelect.value = organizations.includes(previousOrg) ? previousOrg : organizations[0];
  const offices = state.scheduler.offices.filter(office => office.organization === orgSelect.value);
  officeSelect.innerHTML = offices.map(office => `<option value="${office.office}">${office.office}</option>`).join("");
  officeSelect.value = offices.some(office => office.office === previousOffice) ? previousOffice : offices[0]?.office;
  const selected = offices.find(office => office.office === officeSelect.value) || offices[0];
  if (selected) {
    $("scheduler-mode").value = selected.operating_mode;
    $("scheduler-timezone").value = selected.time_zone;
    $("scheduler-hours").value = selected.business_hours;
    $("scheduler-runtime").value = selected.runtime_limit_minutes;
    $("scheduler-budget").value = selected.resource_budget_usd;
  }

  $("scheduler-summary").innerHTML = Object.entries(state.scheduler.summary).map(([name, value]) => `
    <div>${label(name)}<b>${value}</b></div>
  `).join("");

  const analytics = {
    officeUtilization: state.scheduler.analytics.officeUtilization,
    schedulingEfficiency: state.scheduler.analytics.schedulingEfficiency,
    wakeFrequency: state.scheduler.analytics.wakeFrequency,
    averageRuntime: state.scheduler.analytics.runtimeStatistics.averageRuntimeMinutes,
    cpuAverage: state.scheduler.analytics.resourceAllocation.cpuAverage,
    memoryAverage: state.scheduler.analytics.resourceAllocation.memoryAverage,
  };
  $("scheduler-analytics").innerHTML = Object.entries(analytics).map(([name, value]) => `
    <div>${label(name)}<b>${value}</b></div>
  `).join("");

  $("scheduler-detections").innerHTML = Object.entries(state.scheduler.detections).map(([name, value]) => `
    <div>${label(name)}<b>${value}</b></div>
  `).join("");

  $("scheduler-offices").innerHTML = state.scheduler.offices.slice(0, 18).map(office => `
    <div class="office-state">
      <b>${office.organization} / ${office.office}</b>
      <strong>${office.status}</strong>
      <span>${office.operating_mode}</span>
      <span>${office.runtime_minutes}m</span>
    </div>
  `).join("");
}

function label(value) {
  return value.replace(/([A-Z])/g, " $1").replace(/^./, text => text.toUpperCase());
}

function icon(name) {
  return {
    Executive: "EX",
    Seeker: "SK",
    Analyst: "AN",
    Risk: "RK",
    Trader: "TR",
    Historian: "HI",
    Librarian: "LB",
    Academy: "AC",
  }[name] || "--";
}

function drawHealth(values) {
  const canvas = $("health-chart");
  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  ctx.clearRect(0, 0, width, height);
  ctx.strokeStyle = "rgba(143,166,187,.18)";
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const y = 18 + (height - 36) * (i / 4);
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke();
  }
  ctx.fillStyle = "rgba(83,255,92,.12)";
  ctx.strokeStyle = "#53ff5c";
  ctx.lineWidth = 2;
  ctx.beginPath();
  values.forEach((value, index) => {
    const x = 10 + index * ((width - 20) / (values.length - 1));
    const y = height - 18 - (value / 100) * (height - 36);
    if (index === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  });
  ctx.stroke();
  ctx.lineTo(width - 10, height - 18);
  ctx.lineTo(10, height - 18);
  ctx.closePath();
  ctx.fill();
}

function eccAction(action, detail = "") {
  return api("/api/ecc/action", { action, target: selectedOrganization(), detail });
}

function eabFilterQuery() {
  const params = new URLSearchParams();
  const values = {
    organization: $("eab-filter-org").value,
    severity: $("eab-filter-severity").value,
    office: $("eab-filter-office").value,
    workflow: $("eab-filter-workflow").value,
    case_file_id: $("eab-filter-case").value,
    status: $("eab-filter-status").value,
  };
  Object.entries(values).forEach(([key, value]) => {
    if (value) params.set(key, value);
  });
  return params.toString();
}

function applyEabFilter() {
  const query = eabFilterQuery();
  return api(`/api/eab/events${query ? `?${query}` : ""}`);
}

function clearEabFilter() {
  ["eab-filter-office", "eab-filter-workflow", "eab-filter-case", "eab-filter-status"].forEach(id => { $(id).value = ""; });
  $("eab-filter-org").value = "";
  $("eab-filter-severity").value = "";
  return api("/api/eab/events");
}

function cnacFilterQuery() {
  const params = new URLSearchParams();
  const values = {
    organization: $("cnac-filter-org").value,
    priority: $("cnac-filter-priority").value,
    notification_type: $("cnac-filter-type").value,
    office: $("cnac-filter-office").value,
  };
  Object.entries(values).forEach(([key, value]) => {
    if (value) params.set(key, value);
  });
  return params.toString();
}

function applyCnacFilter() {
  const query = cnacFilterQuery();
  return api(`/api/cnac/notifications${query ? `?${query}` : ""}`);
}

function clearCnacFilter() {
  $("cnac-filter-org").value = "";
  $("cnac-filter-priority").value = "";
  $("cnac-filter-type").value = "";
  $("cnac-filter-office").value = "";
  return api("/api/cnac/notifications");
}

function ioeFilterQuery() {
  const params = new URLSearchParams();
  const values = {
    organization: $("ioe-filter-org").value,
    node_type: $("ioe-filter-type").value,
    office: $("ioe-filter-office").value,
    workflow: $("ioe-filter-workflow").value,
    status: $("ioe-filter-status").value,
    q: $("ioe-filter-query").value,
  };
  Object.entries(values).forEach(([key, value]) => {
    if (value) params.set(key, value);
  });
  return params.toString();
}

function applyIoeFilter() {
  const query = ioeFilterQuery();
  return api(`/api/ioe/explorer${query ? `?${query}` : ""}`);
}

function clearIoeFilter() {
  ["ioe-filter-office", "ioe-filter-workflow", "ioe-filter-status", "ioe-filter-query"].forEach(id => { $(id).value = ""; });
  $("ioe-filter-org").value = "";
  $("ioe-filter-type").value = "";
  return api("/api/ioe/explorer");
}

function ioeAction(action) {
  return api("/api/ioe/action", { action, nodeId: selectedIoeNodeId });
}

function executeCommandConsole() {
  return api("/api/command/execute", {
    commandName: $("cc-command").value,
    category: $("cc-category").value,
    target: $("cc-target").value,
    detail: $("cc-detail").value,
    amountUsd: Number($("cc-amount").value),
  });
}

function executeMacro(macroName) {
  return api("/api/command/macro", { macroName });
}

function configureInfrastructure(modeOverride = "") {
  return api("/api/infrastructure/configure", {
    dailyBudgetUsd: Number($("infra-daily-budget").value),
    monthlyBudgetUsd: Number($("infra-monthly-budget").value),
    runtimeLimitMinutes: Number($("infra-runtime-limit").value),
    resourceMode: modeOverride || $("infra-mode").value,
    organization: $("infra-org-limit").value,
    organizationLimitUsd: Number($("infra-org-budget").value),
  });
}

function recordOptimizationAction() {
  const recommendation = state.infrastructure.optimizationRecommendations[0];
  return api("/api/infrastructure/optimization", {
    action: recommendation ? recommendation.summary : "Commander reviewed infrastructure recommendations",
  });
}

function configureCreditGovernor() {
  return api("/api/credit-governor/configure", {
    dailyBudgetUsd: Number($("credit-daily-budget").value),
    weeklyBudgetUsd: Number($("credit-weekly-budget").value),
    monthlyBudgetUsd: Number($("credit-monthly-budget").value),
    office: $("credit-office").value,
    officeBudgetUsd: Number($("credit-office-budget").value),
    workflow: $("credit-workflow").value,
    workflowBudgetUsd: Number($("credit-workflow-budget").value),
    taskIdentifier: $("credit-task").value,
    taskBudgetUsd: Number($("credit-task-budget").value),
  });
}

function requestCreditActivation() {
  const workflowScope = selectedWorkflowScope();
  return api("/api/credit-governor/activate", {
    taskIdentifier: $("credit-activation-task").value,
    activatingSource: $("credit-activation-source").value,
    receivingOffice: $("credit-activation-office").value,
    purpose: $("credit-activation-purpose").value,
    requiredOutput: $("credit-required-output").value,
    maximumRuntimeMinutes: Number($("credit-runtime").value),
    maximumCreditBudgetUsd: Number($("credit-budget").value),
    workflow: $("credit-workflow-name").value,
    organization: $("credit-organization").value,
    evidencePackage: ["COMMANDER-REQUEST"],
    returnRoute: "Commander Interface",
    workflowId: workflowScope.workflowId,
    workflowTokenId: workflowScope.workflowTokenId,
    office: workflowScope.office || $("credit-activation-office").value,
  });
}

function apiRuntimeControl(action) {
  return api("/api/api-runtime-monitor/control", {
    action,
    target: $("arm-target").value,
    value: $("arm-value").value,
  });
}

function selectedWorkflowId() {
  return $("ewo-workflow-select").value;
}

function selectedWorkflowScope() {
  const workflowId = $("ewo-workflow-select")?.value || "";
  const workflow = state?.workflowOrchestrator?.workflows?.find(item => item.workflow_id === workflowId);
  return {
    workflowId,
    workflowTokenId: workflow?.token?.audit_identifier || "",
    office: workflow?.token?.current_owner || "",
  };
}

function createWorkflow() {
  return api("/api/workflow-orchestrator/create", {
    name: $("ewo-name").value,
    stages: $("ewo-stages").value.split(",").map(item => item.trim()).filter(Boolean),
    expectedOutputSchema: $("ewo-schema").value.split(",").map(item => item.trim()).filter(Boolean),
    runtimeBudget: Number($("ewo-runtime").value),
    creditBudget: Number($("ewo-credit").value),
  });
}

function executeWorkflow() {
  return api("/api/workflow-orchestrator/execute", { workflowId: selectedWorkflowId() });
}

function produceWorkflowOutput() {
  return api("/api/workflow-orchestrator/output", {
    workflowId: selectedWorkflowId(),
    output: {
      summary: "Structured workflow stage output",
      evidence: "EWO-EVIDENCE-PACKAGE",
      audit_identifier: "EWO-STRUCTURED-OUTPUT",
    },
    runtime: 10,
    credits: 0.05,
    tokenUsage: 250,
    executionTimeSeconds: 12,
  });
}

function transferWorkflowToken() {
  return api("/api/workflow-orchestrator/transfer", { workflowId: selectedWorkflowId(), reason: "Structured output validated" });
}

function advanceWorkflowStage() {
  return api("/api/workflow-orchestrator/next-stage", { workflowId: selectedWorkflowId() });
}

function archiveWorkflow() {
  return api("/api/workflow-orchestrator/archive", { workflowId: selectedWorkflowId() });
}

function commandConsoleFilterQuery() {
  const params = new URLSearchParams();
  const values = {
    q: $("cc-filter-query").value,
    status: $("cc-filter-status").value,
  };
  Object.entries(values).forEach(([key, value]) => {
    if (value) params.set(key, value);
  });
  return params.toString();
}

function applyCommandConsoleFilter() {
  const query = commandConsoleFilterQuery();
  return api(`/api/command/history${query ? `?${query}` : ""}`);
}

function clearCommandConsoleFilter() {
  $("cc-filter-query").value = "";
  $("cc-filter-status").value = "";
  return api("/api/command/history");
}

function acknowledgeNotification(notificationId) {
  return api("/api/cnac/acknowledge", { notificationId });
}

function selectedSchedulerTarget() {
  return {
    organization: $("scheduler-org").value,
    office: $("scheduler-office").value,
  };
}

function configureOffice() {
  return api("/api/scheduler/configure", {
    ...selectedSchedulerTarget(),
    operatingMode: $("scheduler-mode").value,
    timeZone: $("scheduler-timezone").value,
    businessHours: $("scheduler-hours").value,
    runtimeLimitMinutes: Number($("scheduler-runtime").value),
    resourceBudgetUsd: Number($("scheduler-budget").value),
  });
}

function activateOffice() {
  return api("/api/scheduler/activate", { ...selectedSchedulerTarget(), trigger: "Commander" });
}

function suspendOffice() {
  return api("/api/scheduler/suspend", { ...selectedSchedulerTarget(), trigger: "Commander" });
}

async function init() {
  $("refresh-btn").addEventListener("click", () => api("/api/state"));
  $("bridge-start-paper").addEventListener("click", () => api("/api/paper/start", {}));
  $("bridge-halt").addEventListener("click", () => api("/api/paper/halt", {}));
  $("bridge-pause").addEventListener("click", () => api("/api/bridge/pause", {}));
  $("bridge-step").addEventListener("click", () => api("/api/bridge/step", {}));
  $("bridge-replay").addEventListener("click", startLatestBridgeReplay);
  $("bridge-lab").addEventListener("click", openBridgeLab);
  $("bridge-engineering").addEventListener("click", () => toggleEngineeringMode());
  $("bridge-office-hud").addEventListener("click", (event) => {
    const button = event.target.closest("[data-bridge-view]");
    if (button) navigateBridge(button.dataset.bridgeView);
  });
  $("capital-range-session").addEventListener("click", () => setCapitalRange("session"));
  $("capital-range-today").addEventListener("click", () => setCapitalRange("today"));
  $("capital-range-week").addEventListener("click", () => setCapitalRange("week"));
  $("capital-range-month").addEventListener("click", () => setCapitalRange("month"));
  $("capital-range-all").addEventListener("click", () => setCapitalRange("all"));
  $("exec-office-nav").addEventListener("click", (event) => {
    const button = event.target.closest("[data-bridge-view]");
    if (button) navigateBridge(button.dataset.bridgeView);
  });
  $("executive-return-command").addEventListener("click", () => navigateBridge("command_bridge"));
  $("placeholder-return-command").addEventListener("click", () => navigateBridge("command_bridge"));
  $("exec-start-paper").addEventListener("click", () => api("/api/paper/start", {}));
  $("exec-halt").addEventListener("click", () => api("/api/paper/halt", {}));
  $("exec-pause").addEventListener("click", () => api("/api/bridge/pause", {}));
  $("exec-open-lab").addEventListener("click", openBridgeLab);
  $("exec-open-engineering").addEventListener("click", () => toggleEngineeringMode(true));
  $("seeker-office-nav").addEventListener("click", (event) => {
    const button = event.target.closest("[data-bridge-view]");
    if (button) navigateBridge(button.dataset.bridgeView);
  });
  $("seeker-return-executive").addEventListener("click", () => navigateBridge("executive_bridge"));
  $("seeker-open-executive").addEventListener("click", () => navigateBridge("executive_bridge"));
  $("seeker-pause").addEventListener("click", () => api("/api/bridge/pause", {}));
  $("seeker-resume").addEventListener("click", () => api("/api/bridge/resume", {}));
  $("seeker-replay").addEventListener("click", startLatestBridgeReplay);
  $("seeker-open-lab").addEventListener("click", openBridgeLab);
  $("seeker-open-engineering").addEventListener("click", () => toggleEngineeringMode(true));
  $("seeker-radar-filter").addEventListener("change", (event) => {
    activeSeekerFilter = event.target.value || "all";
    renderSeekerBridge();
  });
  $("start-paper").addEventListener("click", () => api("/api/paper/start", {}));
  $("halt-paper").addEventListener("click", () => api("/api/paper/halt", {}));
  $("deposit-funds").addEventListener("click", () => api("/api/treasury/deposit", { amountUsd: Number($("deposit-input").value) }));
  $("halt-funds").addEventListener("click", () => api("/api/treasury/halt", {}));
  $("request-live").addEventListener("click", () => api("/api/live/request", {}));
  $("halt-live").addEventListener("click", () => api("/api/live/halt", {}));
  $("set-budget").addEventListener("click", () => api("/api/budget", { budgetUsd: Number($("budget-input").value) }));
  $("cc-execute").addEventListener("click", executeCommandConsole);
  $("cc-macros").addEventListener("click", (event) => {
    const button = event.target.closest(".cc-macro");
    if (button) executeMacro(button.dataset.macro);
  });
  $("cc-apply-filter").addEventListener("click", applyCommandConsoleFilter);
  $("cc-clear-filter").addEventListener("click", clearCommandConsoleFilter);
  $("infra-configure").addEventListener("click", () => configureInfrastructure());
  $("infra-cost-saving").addEventListener("click", () => configureInfrastructure("Cost Saving"));
  $("infra-high-performance").addEventListener("click", () => configureInfrastructure("High Performance"));
  $("infra-record-optimization").addEventListener("click", recordOptimizationAction);
  $("infra-org-limit").addEventListener("change", () => {
    if (state?.infrastructure) $("infra-org-budget").value = state.infrastructure.controls.organization_resource_limits[$("infra-org-limit").value] || 0;
  });
  $("credit-configure").addEventListener("click", configureCreditGovernor);
  $("credit-request-activation").addEventListener("click", requestCreditActivation);
  $("arm-terminate").addEventListener("click", () => apiRuntimeControl("terminate_api_process"));
  $("arm-pause").addEventListener("click", () => apiRuntimeControl("pause_office"));
  $("arm-sleep").addEventListener("click", () => apiRuntimeControl("force_sleep"));
  $("arm-block").addEventListener("click", () => apiRuntimeControl("block_office_activation"));
  $("arm-approve").addEventListener("click", () => apiRuntimeControl("approve_continuation"));
  $("arm-deny").addEventListener("click", () => apiRuntimeControl("deny_continuation"));
  $("arm-runtime").addEventListener("click", () => apiRuntimeControl("set_runtime_limit"));
  $("arm-budget").addEventListener("click", () => apiRuntimeControl("set_task_budget"));
  $("arm-low-cost").addEventListener("click", () => apiRuntimeControl("enable_low_cost_mode"));
  $("arm-paper-safe").addEventListener("click", () => apiRuntimeControl("enable_paper_trading_safe_mode"));
  $("arm-reset-session").addEventListener("click", () => api("/api/api-runtime-monitor/reset-session", {}));
  $("arm-live-feed").addEventListener("click", () => {
    apiRuntimeLiveFeedOpen = !apiRuntimeLiveFeedOpen;
    renderApiRuntimeMonitor();
  });
  $("arm-inspect").addEventListener("click", () => apiRuntimeControl("inspect_activation_trace"));
  $("ewo-create").addEventListener("click", createWorkflow);
  $("ewo-execute").addEventListener("click", executeWorkflow);
  $("ewo-output").addEventListener("click", produceWorkflowOutput);
  $("ewo-transfer").addEventListener("click", transferWorkflowToken);
  $("ewo-next").addEventListener("click", advanceWorkflowStage);
  $("ewo-archive").addEventListener("click", archiveWorkflow);
  $("lppc-portfolio-select").addEventListener("change", () => {
    selectedPortfolioId = $("lppc-portfolio-select").value;
    renderLppc();
  });
  $("dl-workflow-select").addEventListener("change", renderDecisionLaboratory);
  $("dl-replay-select").addEventListener("change", renderDecisionLaboratory);
  $("dl-start-replay").addEventListener("click", startDecisionLabReplay);
  $("dl-pause").addEventListener("click", () => decisionLabReplayControl("Pause"));
  $("dl-resume").addEventListener("click", () => decisionLabReplayControl("Resume"));
  $("dl-step-forward").addEventListener("click", () => decisionLabReplayControl("Step Forward"));
  $("dl-step-back").addEventListener("click", () => decisionLabReplayControl("Step Back"));
  $("dl-jump-stage").addEventListener("click", () => decisionLabReplayControl("Jump To Stage"));
  $("dl-jump-revision").addEventListener("click", () => decisionLabReplayControl("Jump To Revision"));
  $("dl-speed").addEventListener("click", () => decisionLabReplayControl("Replay Speed"));
  $("dl-create-experiment").addEventListener("click", createDecisionLabExperiment);
  $("dl-search").addEventListener("click", searchDecisionLab);
  $("ecc-org-select").addEventListener("change", renderEcc);
  $("pause-org").addEventListener("click", () => eccAction("pause_organization"));
  $("resume-org").addEventListener("click", () => eccAction("resume_organization"));
  $("mode-paper").addEventListener("click", () => eccAction("change_operating_mode", "PAPER_TRADING"));
  $("mode-active").addEventListener("click", () => eccAction("change_operating_mode", "ACTIVE"));
  $("configure-schedule").addEventListener("click", () => eccAction("configure_schedule", "continuous monitoring"));
  $("review-evidence").addEventListener("click", () => eccAction("review_evidence"));
  $("inspect-workflows").addEventListener("click", () => eccAction("inspect_workflows"));
  $("view-history").addEventListener("click", () => eccAction("view_historical_activity"));
  $("export-report").addEventListener("click", () => api("/api/ecc/export", {}));
  $("apply-eab-filter").addEventListener("click", applyEabFilter);
  $("clear-eab-filter").addEventListener("click", clearEabFilter);
  $("apply-cnac-filter").addEventListener("click", applyCnacFilter);
  $("clear-cnac-filter").addEventListener("click", clearCnacFilter);
  $("escalate-cnac").addEventListener("click", () => api("/api/cnac/escalate", {}));
  $("daily-briefing").addEventListener("click", () => api("/api/cnac/briefing", { briefingType: "Daily Enterprise Report" }));
  $("cnac-notifications").addEventListener("click", (event) => {
    const button = event.target.closest(".ack-notification");
    if (button) acknowledgeNotification(button.dataset.id);
  });
  $("apply-ioe-filter").addEventListener("click", applyIoeFilter);
  $("clear-ioe-filter").addEventListener("click", clearIoeFilter);
  $("ioe-nodes").addEventListener("click", (event) => {
    const node = event.target.closest(".ioe-node");
    if (node) {
      selectedIoeNodeId = node.dataset.nodeId;
      renderIoe();
    }
  });
  $("ioe-inspect").addEventListener("click", () => ioeAction("inspect"));
  $("ioe-bookmark").addEventListener("click", () => ioeAction("bookmark"));
  $("ioe-follow").addEventListener("click", () => ioeAction("follow"));
  $("ioe-compare").addEventListener("click", () => ioeAction("compare"));
  $("ioe-export").addEventListener("click", () => ioeAction("export"));
  $("ioe-monitor").addEventListener("click", () => ioeAction("monitor"));
  $("scheduler-org").addEventListener("change", renderScheduler);
  $("configure-office").addEventListener("click", configureOffice);
  $("activate-office").addEventListener("click", activateOffice);
  $("suspend-office").addEventListener("click", suspendOffice);
  await api("/api/state");
  setInterval(() => api("/api/state"), 5000);
}

init().catch((error) => {
  document.body.innerHTML = `<pre>${error.stack}</pre>`;
});

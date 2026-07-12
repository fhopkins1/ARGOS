let state = null;
let selectedIoeNodeId = "ENT-ARGOS";
let selectedPortfolioId = "PORT-ENTERPRISE-001";
let apiRuntimeLiveFeedOpen = false;
let engineeringModeOpen = false;
let activeBridgeView = "command_bridge";
let activeCapitalRange = "session";
let activeSeekerFilter = "all";
let activeLibrarianQuery = "";

const OFFICE_BRIDGE_VIEWS = {
  Executive: "executive_bridge",
  Seeker: "seeker_bridge",
  Analyst: "analyst_bridge_placeholder",
  Risk: "risk_bridge",
  Trader: "trader_bridge",
  Historian: "historian_bridge",
  Librarian: "librarian_bridge",
  Academy: "academy_bridge",
  "Strategic Intelligence": "strategic_intelligence_bridge",
};

const $ = (id) => document.getElementById(id);

function renderFileProtocolNotice() {
  document.body.innerHTML = `
    <main class="offline-notice">
      <section class="offline-panel">
        <span>A</span>
        <h1>ARGOS CONTROL PANEL</h1>
        <p>The Control Panel needs the local ARGOS server so browser requests can reach the runtime API.</p>
        <code>py -m argos.control_panel.server --host 127.0.0.1 --port 8765</code>
        <a href="http://127.0.0.1:8765/">Open Local Control Panel</a>
      </section>
    </main>
  `;
}

async function api(path, body) {
  if (window.location.protocol === "file:") {
    throw new Error("ARGOS_CONTROL_PANEL_REQUIRES_LOCAL_SERVER");
  }
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
  renderCommanderStrategicDashboard();
  renderCommanderDailyReviewWorkspace();
  renderExecutiveBridge();
  renderSeekerBridge();
  renderRiskBridge();
  renderTraderBridge();
  renderHistorianBridge();
  renderLibrarianBridge();
  renderAcademyBridge();
  renderStrategicIntelligenceBridge();
  renderBlueOceanBridge();
  renderDisruptionBridge();
  renderDeclineBridge();
  renderShortOpportunityBridge();
  renderMarketStructureBridge();
  renderCapitalRotationBridge();
  renderStrategicSynthesisBridge();
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
  renderDecisionObjectSchema();
  renderDecisionObjectQualityScoringEngine();
  renderDecisionExplainabilityEngine();
  renderEnterpriseBenchmarkEngine();
  renderTradeAttributionEngine();
  renderEnterpriseReproducibilityFramework();
  renderEnterpriseOperationalGuardrails();
  renderEnterpriseExperimentScheduler();
  renderPromptEvolutionEngine();
  renderPromptPackageManager();
  renderStrategyPackageManager();
  renderEnterpriseConfigurationRegistry();
  renderEnterpriseHealthMonitor();
  renderEnterpriseFailureRecoveryFramework();
  renderControlledCognitivePilot();
  renderMarketDataProviderAbstractionLayer();
  renderMarketContextIntegrationEngine();
  renderDailyEnterpriseLearningPipeline();
  renderWorkflowOrchestrator();
  renderWorkflowRuntimeMonitor();
  renderLppc();
  renderStrategyPerformanceConsole();
  renderDecisionLaboratory();
  renderHistorianRecommendationEngine();
  renderEnterpriseLearningEngine();
  renderCommandConsole();
  renderEab();
  renderCnac();
  renderIoe();
  renderEnterpriseMissionPlanner();
  renderEnterpriseCostGovernor();
  renderInformationFreshnessEngine();
  renderEnterpriseMemoryCache();
  renderWorkflowDeltaEngine();
  renderEnterprisePriorityEngine();
  renderPositionMonitoringNetwork();
  renderEnterpriseCommunicationsBus();
  renderEnterpriseEfficiencyAnalytics();
  renderEnterpriseDoctrinePolicyManager();
  renderEventDetectionEngine();
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

function renderCommanderDailyReviewWorkspace() {
  const workspace = state.commanderDailyReviewWorkspace;
  if (!workspace || !$("cdw-morning")) return;
  $("cdw-morning").innerHTML = Object.entries(workspace.morningReadiness || {}).slice(0, 10).map(([key, value]) => `<div><span>${label(key)}</span><b>${Array.isArray(value) ? value.join(", ") : value}</b></div>`).join("");
  $("cdw-operations").innerHTML = Object.entries(workspace.enterpriseOperations || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
  $("cdw-approvals").innerHTML = (workspace.commanderApprovalQueue || []).map(item => `
    <div class="api-call"><b>${item.type}</b><span>${item.risk} / ${Math.round(Number(item.confidence || 0) * 100)}%</span><div>${item.summary}<br />${item.evidence}<br />Actions ${(item.commanderActions || []).join(", ")}</div></div>
  `).join("");
  $("cdw-learning").innerHTML = Object.entries(workspace.enterpriseLearning || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
  const eod = workspace.endOfDayReview || {};
  $("cdw-eod").innerHTML = `
    <div class="api-call"><b>${eod.reportId || "Daily Report"}</b><span>${eod.enterpriseHealth || "Unknown"}</span><div>${eod.tradingSummary || ""}<br />Failures ${eod.failures || 0} / Recovery Events ${eod.recoveryEvents || 0}<br />Tomorrow ${(eod.tomorrowsPriorities || []).join(", ")}</div></div>
  `;
  $("cdw-priorities").innerHTML = (workspace.priorityPanel || []).map(item => `<div class="api-call"><b>${item.priority}</b><span>${item.category}</span><div>${item.summary}</div></div>`).join("");
  $("cdw-insights").innerHTML = (workspace.commanderInsights || []).map(item => `<div class="api-call"><b>Insight</b><span>Advisory</span><div>${item}</div></div>`).join("");
  $("cdw-journal").innerHTML = (workspace.commanderJournal || []).length
    ? workspace.commanderJournal.map(item => `<div class="api-call"><b>${item.category}</b><span>${item.journalId}</span><div>${item.entry}<br />${item.timestamp}</div></div>`).join("")
    : `<div class="alert-empty">No Commander journal entries recorded</div>`;
  if ($("cdrw-scorecard")) {
    $("cdrw-scorecard").innerHTML = Object.entries(workspace.enterpriseScorecard || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
    $("cdrw-timeline").innerHTML = (workspace.enterpriseTimeline || []).map(item => `<div class="api-call"><b>${item.event}</b><span>${item.status}</span><div>${item.timestamp}</div></div>`).join("");
    $("cdrw-checklist").innerHTML = Object.entries(workspace.reviewChecklist || {}).map(([key, value]) => `<div class="api-call"><b>${label(key)}</b><span>Daily</span><div>${(value || []).join("<br />")}</div></div>`).join("");
    $("cdrw-reports").innerHTML = (workspace.dailyReportsArchive || []).map(item => `<div class="api-call"><b>${item.reportId}</b><span>${item.enterpriseHealth}</span><div>${item.tradingSummary}<br />Immutable ${item.immutable ? "YES" : "NO"}</div></div>`).join("");
    $("cdrw-engineering-links").innerHTML = (workspace.engineeringModeLinks || []).map(item => `<div class="api-call"><b>${item}</b><span>Subsystem</span><div>Detailed diagnostics remain in Engineering Mode.</div></div>`).join("");
    $("cdrw-diagnostics").innerHTML = `
      ${Object.entries(workspace.lawVII || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${typeof value === "boolean" ? (value ? "YES" : "NO") : value}</b></div>`).join("")}
      ${Object.entries(workspace.internalDiagnostics || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("")}
    `;
  }
}

function renderCommanderStrategicDashboard() {
  const dashboard = state.commanderStrategicDashboard;
  if (!dashboard || !$("csd-capital")) return;
  const recommendation = dashboard.strategic_recommendation || {};
  $("csd-recommendation").textContent = String(recommendation.recommendation || "continue_normal_operations").replaceAll("_", " ");
  const command = dashboard.command_state?.data || {};
  $("csd-command-state").innerHTML = [
    ["Mode", command.tradingMode],
    ["Status", command.tradingStatus],
    ["Workflow", command.activeWorkflow],
    ["Office", command.activeOffice],
    ["LAW VII", command.lawVIIStatus],
    ["LAW VIII", command.lawVIIIStatus],
    ["Market", command.marketSession],
    ["Alert", command.systemWideAlertSeverity],
  ].map(([name, value]) => `<div><span>${name}</span><b>${value || "unknown"}</b></div>`).join("");

  const capital = dashboard.capital_state?.data || {};
  $("csd-capital").innerHTML = [
    ["Portfolio Equity", money(capital.portfolioEquity)],
    ["Cash", money(capital.cash)],
    ["Buying Power", money(capital.buyingPower)],
    ["Deployed", money(capital.deployedCapital)],
    ["Daily P/L", money(capital.dailyPnl)],
    ["Realized P/L", money(capital.realizedPnl)],
    ["Unrealized P/L", money(capital.unrealizedPnl)],
    ["Drawdown", `${Number(capital.currentDrawdown || 0).toFixed(2)}%`],
  ].map(metricRow).join("");
  const heartbeat = capital.capitalHeartbeat || [];
  $("csd-heartbeat").innerHTML = heartbeat.length
    ? heartbeat.slice(-8).map(point => `<span style="height:${Math.max(8, Math.min(58, 16 + Number(point.portfolioEquity || 0) / Math.max(1, Number(capital.portfolioEquity || 1)) * 28))}px" title="${point.timestamp} ${money(point.portfolioEquity)}"></span>`).join("")
    : `<em>Awaiting capital heartbeat history</em>`;

  const readiness = dashboard.readiness?.data || {};
  $("csd-readiness").innerHTML = [
    ["Enterprise", readiness.overallEnterpriseHealth],
    ["Workflow", readiness.workflowHealth],
    ["Market Data", readiness.marketDataHealth],
    ["Execution", readiness.executionHealth],
    ["Surveillance", readiness.positionSurveillanceHealth],
    ["Reality", readiness.realityFidelity],
    ["Learning", readiness.learningReliability],
    ["Trading", readiness.tradingReadiness],
  ].map(metricRow).join("");

  const reality = dashboard.reality_fidelity?.data || {};
  $("csd-reality").innerHTML = [
    ["Overall Fidelity", Number(reality.overallRealityFidelityScore || 0).toFixed(1)],
    ["Learning State", reality.learningReliabilityState],
    ["Execution Fidelity", Number(reality.executionFidelityScore || 0).toFixed(1)],
    ["Valuation Fidelity", Number(reality.valuationFidelityScore || 0).toFixed(1)],
    ["Truth Reliability", Number(reality.truthReliabilityScore || 0).toFixed(1)],
    ["Drift Warnings", (reality.activeDriftWarnings || []).length],
  ].map(metricRow).join("");

  const risk = dashboard.strategic_risk?.data || {};
  const correlation = dashboard.correlation?.data || {};
  $("csd-risk").innerHTML = [
    ["Risk Score", Number(risk.compositeEnterpriseRiskScore || 0).toFixed(1)],
    ["Risk Level", risk.riskLevel],
    ["Concentration", Number(risk.concentrationRisk || 0).toFixed(1)],
    ["Liquidity", Number(risk.liquidityRisk || 0).toFixed(1)],
    ["Correlation", Number(correlation.correlationRiskScore || 0).toFixed(1)],
    ["Hidden Conc.", Number(correlation.hiddenConcentrationScore || 0).toFixed(1)],
    ["Diversification", Number(correlation.diversificationQualityScore || 0).toFixed(1)],
    ["Halt", risk.tradingHaltRecommendation ? "YES" : "NO"],
  ].map(metricRow).join("");

  const portfolio = dashboard.active_portfolio?.data || {};
  $("csd-portfolio").innerHTML = [
    ["Open Positions", portfolio.activePositions],
    ["Market Value", money(portfolio.totalMarketValue)],
    ["Need Attention", portfolio.positionsRequiringAttention],
    ["Near Stop", portfolio.positionsNearStop],
    ["Near Target", portfolio.positionsNearTarget],
    ["Exit Recs", portfolio.positionsWithExitRecommendations],
    ["Pending Exits", portfolio.pendingExitOrders],
    ["Largest", portfolio.largestPosition?.symbol || "none"],
  ].map(metricRow).join("");

  const performance = dashboard.performance?.data || {};
  $("csd-performance").innerHTML = [
    ["Realized", money(performance.realizedPerformance)],
    ["Unrealized", money(performance.unrealizedPerformance)],
    ["Enterprise Return", `${Number(performance.enterpriseReturn || 0).toFixed(2)}%`],
    ["Benchmark", `${Number(performance.benchmarkReturn || 0).toFixed(2)}%`],
    ["Alpha", `${Number(performance.alpha || 0).toFixed(2)}%`],
    ["Win Rate", `${Number(performance.winRate || 0).toFixed(2)}%`],
    ["Closed Trades", performance.tradeCount],
    ["Sample", performance.sampleSizeConfidence],
  ].map(metricRow).join("");

  const stress = dashboard.stress_and_survival?.data || {};
  $("csd-stress").innerHTML = [
    ["Stress Level", stress.latestStressLevel],
    ["Stress DD", `${Number(stress.stressedDrawdown || 0).toFixed(2)}%`],
    ["Stop Cascade", stress.stopCascadeRisk ? "YES" : "NO"],
    ["Survival", Number(stress.blackSwanSurvivalScore || 0).toFixed(1)],
    ["Ruin Risk", Number(stress.ruinRiskScore || 0).toFixed(1)],
    ["MC Loss", `${Number(stress.monteCarloProbabilityOfLoss || 0).toFixed(2)}%`],
    ["MC Ruin", `${Number(stress.monteCarloProbabilityOfRuin || 0).toFixed(2)}%`],
    ["Model Conf.", Number(stress.modelConfidence || 0).toFixed(1)],
  ].map(metricRow).join("");

  const learning = dashboard.learning_and_research?.data || {};
  const intelligence = dashboard.intelligence_efficiency?.data || {};
  $("csd-learning").innerHTML = [
    ["Truth Obs.", learning.completedTradeObservations],
    ["Historian Lessons", learning.newHistorianLessons],
    ["Learning Candidates", learning.learningCandidates],
    ["Queued Experiments", learning.queuedExperiments],
    ["Knowledge Yield", learning.experimentKnowledgeYield],
    ["Credits Today", money(intelligence.creditsUsedToday, 4)],
    ["LLM Calls", intelligence.llmInvocationCount],
    ["Throttle", intelligence.throttlingState],
  ].map(metricRow).join("");

  $("csd-attention").innerHTML = (dashboard.attention_queue || []).map(item => `
    <div class="api-call ${String(item.severity || "").toLowerCase()}"><b>${item.severity}</b><span>${item.sourceEngine}</span><div>${item.reason}<br />${item.evidenceSummary}<br />Action ${String(item.recommendedAction || "").replaceAll("_", " ")}</div></div>
  `).join("");
  const briefing = dashboard.latest_briefing || state.commanderBriefingGenerator?.latestDashboardFeed || {};
  $("csd-briefing").innerHTML = briefing.latestBriefingType ? `
    <div class="api-call"><b>${String(briefing.latestBriefingType).replaceAll("_", " ")}</b><span>${briefing.overallStatus || "unknown"}</span><div>${briefing.executiveSummary || ""}<br />Posture ${String(briefing.recommendedPosture || "").replaceAll("_", " ")}<br />Generated ${briefing.generatedAt || "unknown"}</div></div>
    <div class="api-call"><b>Decisions</b><span>${(briefing.decisionsRequired || []).length}</span><div>${(briefing.decisionsRequired || []).map(item => `${item.severity || "INFO"} ${item.reason || item.recommendedAction}`).join("<br />") || "No decisions required"}</div></div>
    <div class="api-call"><b>Action Reasoning</b><span>${(briefing.recommendedActions || []).length}</span><div>${(briefing.recommendedActions || []).map(item => `${String(item.action || "").replaceAll("_", " ")}: ${item.reasoning || ""}`).join("<br />") || "No recommended actions"}</div></div>
  ` : `<div class="alert-empty">No Commander briefing generated yet</div>`;
  const grand = dashboard.grand_strategy || state.enterpriseGrandStrategyEngine?.dashboardFeed || {};
  $("csd-grand-strategy").innerHTML = [
    ["Posture", grand.currentStrategicPosture],
    ["Maturity", grand.currentMaturityStage],
    ["Live Ready", grand.liveReadinessState],
    ["Confidence", Number(grand.strategicConfidence || 0).toFixed(1)],
    ["Objectives", (grand.primaryObjectives || []).length],
    ["Prohibitions", (grand.prohibitedActions || []).length],
    ["Review Triggers", (grand.activeReviewTriggers || []).length],
    ["Decisions", (grand.decisionsRequired || []).length],
  ].map(metricRow).join("");
  $("csd-navigation").innerHTML = (dashboard.navigation || []).slice(0, 9).map(item => `
    <button class="button secondary" data-bridge-view="${item.route}">${item.label}</button>
  `).join("");
}

function metricRow([name, value]) {
  return `<div><span>${name}</span><b>${value === undefined || value === "" ? "unknown" : value}</b></div>`;
}

function recordCommanderJournalEntry() {
  return api("/api/commander/journal", {
    category: $("cdw-journal-category").value,
    entry: $("cdw-journal-entry").value,
  });
}

function bridgePortfolio() {
  const truth = state.performanceTruthEngine || {};
  const truthCalculations = truth.calculations?.portfolio || {};
  const truthPortfolio = truth.portfolioLedger?.[truth.portfolioLedger.length - 1];
  const realism = truth.executionRealism || {};
  const brokerProfile = truth.brokerProfile || {};
  const paperAccount = truth.paperAccount || {};
  const proofAttempts = truth.integrity?.proofModeTruthAttempts || 0;
  const rejectedTruth = truth.rejectedTruthRecords || [];
  if (truthPortfolio) {
    return {
      source: "TRUTH ENGINE",
      simulated: false,
      truthLabel: "PAPER - CERTIFIED OPERATIONAL RECORD",
      certificationStatus: "PAPER_OPERATIONAL",
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
      brokerProfile: brokerProfile.profileName || "Robinhood-like Retail Account",
      paperAccountType: brokerProfile.accountType || "Cash Retail Paper Account",
      supportedAssets: brokerProfile.supportedAssets?.length || 0,
      rejectedOrders: realism.rejectedOrders || 0,
      queuedOrders: realism.queuedOrders || 0,
      partialFills: realism.partialFills || 0,
      spreadCost: realism.spreadCost || 0,
      slippageCost: realism.slippageCost || 0,
      executionRealismScore: realism.executionRealismScore ?? 100,
      fantasyTradeWarnings: realism.fantasyTradeWarnings?.length || 0,
      buyingPower: paperAccount.buyingPower ?? truthPortfolio.buying_power ?? 0,
    };
  }
  if (proofAttempts || rejectedTruth.length) {
    return {
      source: "PROOF QUARANTINE",
      simulated: false,
      truthLabel: "PROOF MODE - NOT OPERATIONAL TRUTH",
      certificationStatus: "REJECTED_NOT_OPERATIONAL_TRUTH",
      value: paperAccount.buyingPower || 0,
      cash: paperAccount.cash || paperAccount.buyingPower || 0,
      realized: 0,
      unrealized: 0,
      todayReturnUsd: 0,
      todayReturnPercent: 0,
      returnPercent: 0,
      alpha: 0,
      exposurePercent: 0,
      maxDrawdownPercent: 0,
      trades: 0,
      winRate: 0,
      profitFactor: 0,
      sharpeRatio: 0,
      capitalTrustPosture: "PROOF_NOT_OPERATIONAL",
      brokerProfile: brokerProfile.profileName || "Paper broker model disabled for proof truth",
      paperAccountType: brokerProfile.accountType || "Cash Retail Paper Account",
      supportedAssets: brokerProfile.supportedAssets?.length || 0,
      rejectedOrders: realism.rejectedOrders || 0,
      queuedOrders: realism.queuedOrders || 0,
      partialFills: realism.partialFills || 0,
      spreadCost: 0,
      slippageCost: 0,
      executionRealismScore: 0,
      fantasyTradeWarnings: proofAttempts,
      buyingPower: paperAccount.buyingPower || 0,
    };
  }
  const strategy = state.strategyPerformanceConsole?.livePortfolioPanel || {};
  return {
    source: "SIMULATED",
    simulated: true,
    truthLabel: "SIMULATION - NO BROKER ORDER",
    certificationStatus: "SIMULATION_ONLY",
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
    brokerProfile: brokerProfile.profileName || "Robinhood-like Retail Account",
    paperAccountType: brokerProfile.accountType || "Cash Retail Paper Account",
    supportedAssets: brokerProfile.supportedAssets?.length || 0,
    rejectedOrders: realism.rejectedOrders || 0,
    queuedOrders: realism.queuedOrders || 0,
    partialFills: realism.partialFills || 0,
    spreadCost: realism.spreadCost || 0,
    slippageCost: realism.slippageCost || 0,
    executionRealismScore: realism.executionRealismScore ?? 100,
    fantasyTradeWarnings: realism.fantasyTradeWarnings?.length || 0,
    buyingPower: paperAccount.buyingPower || strategy.cash || 0,
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
  return ["Executive", "Seeker", "Analyst", "Risk", "Trader", "Historian", "Librarian", "Academy", "Strategic Intelligence"];
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
  const riskBridge = $("risk-subcommand-bridge");
  const traderBridge = $("trader-subcommand-bridge");
  const historianBridge = $("historian-subcommand-bridge");
  const librarianBridge = $("librarian-subcommand-bridge");
  const academyBridge = $("academy-subcommand-bridge");
  const strategicIntelligenceBridge = $("strategic-intelligence-subcommand-bridge");
  const blueOceanBridge = $("blue-ocean-subcommand-bridge");
  const disruptionBridge = $("disruption-subcommand-bridge");
  const declineBridge = $("decline-subcommand-bridge");
  const shortOpportunityBridge = $("short-opportunity-subcommand-bridge");
  const marketStructureBridge = $("market-structure-subcommand-bridge");
  const capitalRotationBridge = $("capital-rotation-subcommand-bridge");
  const strategicSynthesisBridge = $("strategic-synthesis-subcommand-bridge");
  const placeholderBridge = $("subcommand-placeholder");
  if (!commandBridge || !executiveBridge || !seekerBridge || !riskBridge || !traderBridge || !historianBridge || !librarianBridge || !academyBridge || !strategicIntelligenceBridge || !blueOceanBridge || !disruptionBridge || !declineBridge || !shortOpportunityBridge || !marketStructureBridge || !capitalRotationBridge || !strategicSynthesisBridge || !placeholderBridge) return;
  commandBridge.classList.toggle("hidden", activeBridgeView !== "command_bridge");
  executiveBridge.classList.toggle("hidden", activeBridgeView !== "executive_bridge");
  seekerBridge.classList.toggle("hidden", activeBridgeView !== "seeker_bridge");
  riskBridge.classList.toggle("hidden", activeBridgeView !== "risk_bridge");
  traderBridge.classList.toggle("hidden", activeBridgeView !== "trader_bridge");
  historianBridge.classList.toggle("hidden", activeBridgeView !== "historian_bridge");
  librarianBridge.classList.toggle("hidden", activeBridgeView !== "librarian_bridge");
  academyBridge.classList.toggle("hidden", activeBridgeView !== "academy_bridge");
  strategicIntelligenceBridge.classList.toggle("hidden", activeBridgeView !== "strategic_intelligence_bridge");
  blueOceanBridge.classList.toggle("hidden", activeBridgeView !== "blue_ocean_bridge");
  disruptionBridge.classList.toggle("hidden", activeBridgeView !== "disruption_bridge");
  declineBridge.classList.toggle("hidden", activeBridgeView !== "decline_bridge");
  shortOpportunityBridge.classList.toggle("hidden", activeBridgeView !== "short_opportunity_bridge");
  marketStructureBridge.classList.toggle("hidden", activeBridgeView !== "market_structure_bridge");
  capitalRotationBridge.classList.toggle("hidden", activeBridgeView !== "capital_rotation_bridge");
  strategicSynthesisBridge.classList.toggle("hidden", activeBridgeView !== "strategic_synthesis_bridge");
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
  $("capital-data-source").textContent = portfolio.truthLabel || (portfolio.simulated ? "SIMULATION - NO BROKER ORDER" : "PAPER - CERTIFIED OPERATIONAL RECORD");
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
    <div><span>Truth Domain</span><b>${portfolio.truthLabel}</b></div>
    <div><span>Certification</span><b>${portfolio.certificationStatus}</b></div>
    <div><span>Realized P/L</span><b>${money(portfolio.realized)}</b></div>
    <div><span>Unrealized P/L</span><b>${money(portfolio.unrealized)}</b></div>
    <div><span>Total Trades</span><b>${portfolio.trades}</b></div>
    <div><span>Win Rate</span><b>${Number(portfolio.winRate || 0).toFixed(2)}%</b></div>
    <div><span>Profit Factor</span><b>${Number(portfolio.profitFactor || 0).toFixed(4)}</b></div>
    <div><span>Broker Profile</span><b>${portfolio.brokerProfile}</b></div>
    <div><span>Paper Account Type</span><b>${portfolio.paperAccountType}</b></div>
    <div><span>Supported Assets</span><b>${portfolio.supportedAssets}</b></div>
    <div><span>Rejected Orders</span><b>${portfolio.rejectedOrders}</b></div>
    <div><span>Queued Orders</span><b>${portfolio.queuedOrders}</b></div>
    <div><span>Partial Fills</span><b>${portfolio.partialFills}</b></div>
    <div><span>Spread Cost</span><b>${money(portfolio.spreadCost, 4)}</b></div>
    <div><span>Slippage Cost</span><b>${money(portfolio.slippageCost, 4)}</b></div>
    <div><span>Buying Power</span><b>${money(portfolio.buyingPower)}</b></div>
    <div><span>Execution Realism</span><b>${Number(portfolio.executionRealismScore || 0).toFixed(0)}</b></div>
    <div><span>Fantasy Warnings</span><b>${portfolio.fantasyTradeWarnings}</b></div>
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
  const context = state.marketContextIntegrationEngine?.latestMarketContext || {};
  const truth = state.performanceTruthEngine || {};
  const portfolio = truth.calculations?.portfolio || {};
  const benchmark = bridgeBenchmark();
  const scorecard = state.strategyPerformanceConsole?.enterpriseScorecard || {};
  const trades = state.strategyPerformanceConsole?.tradeStream || [];
  const latestTrade = trades[trades.length - 1] || {};
  const healthySignals = seekerSignalSources().filter(([, status]) => status === "Healthy").length;
  const topCandidate = candidates[0];
  return {
    marketTrend: context.overallTrend || (Number(benchmark.returnPercent || 0) >= 0 ? "Constructive" : "Defensive"),
    breadth: candidates.length ? `${candidates.length} candidate channels` : "Awaiting candidates",
    volatility: context.volatilityState || (Number(portfolio.maximumDrawdown || portfolio.maxDrawdownPercent || 0) < -2 ? "Elevated" : "Contained"),
    sectorLeadership: context.relatedSectors?.[0] || topCandidate?.sector || latestTrade.strategy || "Awaiting truth history",
    topGainers: topCandidate?.ticker || "Awaiting candidates",
    topLosers: latestTrade.ticker && latestTrade.ticker !== topCandidate?.ticker ? latestTrade.ticker : "None detected",
    newsDensity: candidates.some(candidate => candidate.news !== "Quiet") ? "Monitored" : "Quiet",
    economicCalendar: healthySignals >= 7 ? "Online" : "Partial",
    marketRegime: context.marketRegime || topCandidate?.marketRegime || state.environment || "paper",
    paperUniverse: state.control.paper_trading_active ? "Active" : "Standing by",
    discoveryQuality: scorecard.decisionQuality || 0,
    contextSnapshot: context.snapshotId || "None",
    dataFreshness: context.dataFreshness?.freshnessStatus || "Standing By",
    contextConfidence: context.confidence || 0,
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
    <div><span>Context Snapshot</span><b>${market.contextSnapshot}</b></div>
    <div><span>Data Freshness</span><b>${market.dataFreshness}</b></div>
    <div><span>Context Confidence</span><b>${Math.round(Number(market.contextConfidence || 0) * 100)}%</b></div>
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

function percent(value, digits = 1) {
  return `${Number(value || 0).toFixed(digits)}%`;
}

function riskLevel(score) {
  if (score >= 0.82) return "CRITICAL";
  if (score >= 0.62) return "HIGH";
  if (score >= 0.36) return "MEDIUM";
  return "LOW";
}

function riskTrend(score, baseline = 0.5) {
  const delta = Number(score || 0) - Number(baseline || 0);
  if (delta > 0.08) return "Worsening";
  if (delta < -0.08) return "Improving";
  return "Stable";
}

function riskAssessment(decision, portfolio) {
  const riskScore = Number(decision?.riskScore ?? 0.32);
  const confidence = Number(decision?.currentConfidence ?? 0);
  const expectedReturnRaw = decision?.expectedReturn;
  const expectedReturn = typeof expectedReturnRaw === "number"
    ? expectedReturnRaw
    : Number(String(expectedReturnRaw || "0").replace(/[^\d.-]/g, "")) || 0;
  const positionSize = Number(String(decision?.positionSizeRecommendation || "0.03").replace(/[^\d.-]/g, "")) || 0.03;
  const downside = Math.max(1, Math.abs(Number(portfolio.maxDrawdownPercent || 0)) + (riskScore * 8));
  const rewardRisk = Math.max(0.1, Math.abs(expectedReturn || 4) / downside);
  const probabilityOfLoss = Math.min(94, Math.round((riskScore * 68) + ((1 - confidence) * 26)));
  let recommendation = "APPROVE";
  if (!decision) recommendation = "REQUEST MORE INFORMATION";
  else if (riskScore >= 0.8 || rewardRisk < 0.8) recommendation = "REJECT";
  else if (positionSize > 0.05 || riskScore >= 0.62) recommendation = "REDUCE SIZE";
  else if (!decision.stopLoss) recommendation = "ADD STOP";
  return {
    riskScore,
    expectedDownside: downside,
    rewardRisk,
    probabilityOfLoss,
    maximumExpectedDrawdown: Math.max(downside, Math.abs(Number(portfolio.maxDrawdownPercent || 0))),
    capitalAtRisk: Number(portfolio.value || 0) * Math.min(0.1, Math.max(0.01, positionSize)),
    suggestedPositionSize: Math.min(0.05, Math.max(0.01, positionSize * (riskScore >= 0.62 ? 0.5 : 1))),
    suggestedStop: decision?.stopLoss || 94.5,
    suggestedTarget: decision?.targetPrice || 104.25,
    riskRecommendation: recommendation,
  };
}

function riskHeatMap(decision, portfolio) {
  const assessment = riskAssessment(decision, portfolio);
  const exposure = Number(portfolio.exposurePercent || 0) / 100;
  const drawdown = Math.abs(Number(portfolio.maxDrawdownPercent || 0)) / 10;
  const confidenceGap = 1 - Number(decision?.currentConfidence || 0.55);
  const base = assessment.riskScore || 0.32;
  return [
    ["Market Risk", base + Math.abs(Number(portfolio.returnPercent || 0)) / 120],
    ["Sector Risk", base * 0.88 + exposure],
    ["Volatility Risk", base + drawdown],
    ["Liquidity Risk", base * 0.72],
    ["Concentration Risk", exposure + Number(assessment.suggestedPositionSize || 0) * 6],
    ["Correlation Risk", exposure + 0.18],
    ["Macro Risk", base * 0.7 + Math.abs(Number(bridgeBenchmark().returnPercent || 0)) / 100],
    ["Gap Risk", base * 0.9 + drawdown],
    ["Event Risk", base * 0.68 + confidenceGap * 0.25],
    ["Execution Risk", state.apiExecutionGateway?.metrics?.failedCount ? 0.72 : base * 0.54],
    ["Tail Risk", base + drawdown + exposure],
    ["Confidence Risk", confidenceGap],
  ].map(([name, score], index) => ({
    name,
    score: Math.min(0.98, Number(score || 0)),
    level: riskLevel(Math.min(0.98, Number(score || 0))),
    trend: riskTrend(score, 0.42 + (index % 3) * 0.08),
  }));
}

function riskRuleValidation(decision, assessment, portfolio) {
  const positionSize = Number(assessment.suggestedPositionSize || 0);
  const confidence = Number(decision?.currentConfidence || 0);
  const exposure = Number(portfolio.exposurePercent || 0);
  const rewardRisk = Number(assessment.rewardRisk || 0);
  const checks = [
    ["Maximum Position Size", positionSize <= 0.05, positionSize <= 0.065, `Suggested size ${percent(positionSize * 100, 2)} exceeds doctrine cap.`],
    ["Maximum Sector Allocation", exposure <= 35, exposure <= 50, `Exposure ${percent(exposure, 2)} is above sector tolerance.`],
    ["Maximum Portfolio Exposure", exposure <= 65, exposure <= 80, `Portfolio exposure ${percent(exposure, 2)} is above allowed range.`],
    ["Maximum Correlated Exposure", assessment.riskScore <= 0.62, assessment.riskScore <= 0.78, "Correlation and tail indicators require reduction."],
    ["Risk/Reward Minimum", rewardRisk >= 1.2, rewardRisk >= 0.9, `Reward/risk ${rewardRisk.toFixed(2)} is below doctrine minimum.`],
    ["Confidence Threshold", confidence >= 0.65, confidence >= 0.5, `Confidence ${Math.round(confidence * 100)}% is insufficient.`],
    ["Capital Preservation Rules", assessment.capitalAtRisk <= Number(portfolio.value || 0) * 0.05, assessment.capitalAtRisk <= Number(portfolio.value || 0) * 0.08, "Capital at risk exceeds preservation rules."],
  ];
  return checks.map(([name, pass, warn, reason]) => ({
    name,
    status: pass ? "PASS" : warn ? "WARNING" : "FAIL",
    reason: pass ? "Within enterprise risk doctrine." : reason,
  }));
}

function riskHistoricalComparisons(decision, assessment) {
  const lab = state.decisionLaboratory?.experimentTree || [];
  const evolution = state.strategyPerformanceConsole?.decisionObjectEvolution || [];
  const source = evolution.length ? evolution.slice(-4).reverse() : lab.slice(-4);
  if (!source.length && !decision) return [];
  const rows = source.length ? source : [{ decisionObjectId: decision.decisionObjectId, workflowId: decision.workflowId, revisionCount: decision.currentRevision || 1 }];
  return rows.map((item, index) => {
    const revision = item.revisions?.[item.revisions.length - 1] || {};
    const risk = Number(revision.risk ?? assessment.riskScore ?? 0.32);
    return {
      decisionObject: item.decisionObjectId || item.experimentId || `DO-RISK-${index + 1}`,
      similarityScore: Math.max(72, 96 - index * 7),
      riskScore: risk,
      outcome: risk >= 0.7 ? "Reduced before trade" : "Accepted in paper review",
      maximumDrawdown: Math.max(1.2, risk * 9),
      actualReturn: Number(revision.returnPercent || (4.6 - risk * 5)),
      historianLesson: risk >= 0.7 ? "Size reduction prevented excess drawdown." : "Risk controls remained within doctrine.",
    };
  });
}

function riskRecentDecisions(decision, assessment) {
  const evolution = state.strategyPerformanceConsole?.decisionObjectEvolution || [];
  const rows = evolution.length ? evolution.slice(-6).reverse() : decision ? [{ decisionObjectId: decision.decisionObjectId, workflowId: decision.workflowId, revisions: [{ recommendation: decision.currentRecommendation, confidence: decision.currentConfidence }] }] : [];
  return rows.map(item => {
    const revision = item.revisions?.[item.revisions.length - 1] || {};
    const risk = Number(revision.risk ?? assessment.riskScore ?? 0.32);
    return {
      workflow: item.workflowId || decision?.workflowId || "None",
      decisionObject: item.decisionObjectId || decision?.decisionObjectId || "None",
      recommendation: revision.recommendation || decision?.currentRecommendation || "Pending",
      riskAction: risk >= 0.8 ? "Reject" : risk >= 0.62 ? "Reduce size" : "Approve with controls",
      positionChange: risk >= 0.62 ? "-50%" : "No change",
      confidenceChange: revision.confidence ? `${Math.round(Number(revision.confidence) * 100)}%` : `${Math.round(Number(decision?.currentConfidence || 0) * 100)}%`,
      approvalStatus: risk >= 0.8 ? "Blocked" : "Risk approved",
      outcome: state.control.paper_trading_active ? "In paper review" : "Awaiting Decision Object",
    };
  });
}

function renderRiskBridge() {
  if (!$("risk-subcommand-bridge")) return;
  const workflow = bridgeWorkflow();
  const decision = bridgeLatestDecision();
  const portfolio = bridgePortfolio();
  const assessment = riskAssessment(decision, portfolio);
  const heatMap = riskHeatMap(decision, portfolio);
  const rules = riskRuleValidation(decision, assessment, portfolio);
  const alerts = bridgeCriticalAlerts();
  const owner = workflow?.currentOwner || "";
  const riskActive = owner === "Risk";
  const lawStatus = state.workflowRuntimeMonitor?.tokenIntegrity?.status || "VALID";
  const gateway = state.apiExecutionGateway || {};
  const gatewayStatus = gateway.configuration?.dryRunDefault || !gateway.configuration?.realProviderCallsEnabled ? "Guarded" : "Live Pilot Guarded";
  const posture = assessment.riskScore >= 0.82 ? "Critical" : assessment.riskScore >= 0.62 ? "Defensive" : "Protected";

  $("risk-office-status").textContent = riskActive ? "ACTIVE REVIEW" : state.control.paper_trading_active ? "STANDING WATCH" : "DORMANT";
  $("risk-current-workflow").textContent = workflow?.workflowIdentifier || "None";
  $("risk-decision-object").textContent = decision?.decisionObjectId || "None";
  $("risk-law").textContent = lawStatus;
  $("risk-law").style.color = lawStatus === "VALID" ? "var(--green)" : "var(--red)";
  $("risk-token").textContent = workflow ? `${owner || "No Owner"} / ${workflow.tokenId || workflow.auditIdentifier}` : "No Token";
  $("risk-revision").textContent = decision?.currentRevision || 0;
  $("risk-current-state").textContent = decision ? riskLevel(assessment.riskScore) : "Standing By";
  $("risk-enterprise-posture").textContent = posture;
  $("risk-gateway-status").textContent = gatewayStatus;
  $("risk-commander-alert").textContent = alerts[0]?.summary || "None";

  $("risk-heat-map").innerHTML = heatMap.map(item => `
    <div class="risk-heat-cell ${item.level.toLowerCase()}">
      <b>${item.name}</b>
      <strong>${item.level}</strong>
      <span>${item.trend}</span>
    </div>
  `).join("");

  $("risk-current-decision").innerHTML = decision ? `
    <div class="bridge-decision-id">${decision.decisionObjectId}</div>
    <div class="bridge-decision-grid">
      <div><span>Workflow</span><b>${decision.workflowId || "None"}</b></div>
      <div><span>Revision</span><b>${decision.currentRevision || 0}</b></div>
      <div><span>Recommendation</span><b>${decision.currentRecommendation || "Pending"}</b></div>
      <div><span>Confidence</span><b>${Math.round(Number(decision.currentConfidence || 0) * 100)}%</b></div>
      <div><span>Expected Return</span><b>${decision.expectedReturn || "Pending"}</b></div>
      <div><span>Position Size</span><b>${decision.positionSizeRecommendation || percent(assessment.suggestedPositionSize * 100, 2)}</b></div>
      <div><span>Target</span><b>${decision.targetPrice ? money(decision.targetPrice) : money(assessment.suggestedTarget)}</b></div>
      <div><span>Stop</span><b>${decision.stopLoss ? money(decision.stopLoss) : money(assessment.suggestedStop)}</b></div>
      <div><span>Current Owner</span><b>${decision.currentOwner || decision.currentStage || owner || "None"}</b></div>
      <div><span>Previous Office</span><b>${workflow?.previousOwner || "None"}</b></div>
      <div><span>Next Office</span><b>${workflow?.nextOwner || "None"}</b></div>
      <div><span>Promotion Status</span><b>${assessment.riskRecommendation}</b></div>
    </div>
  ` : `<div class="bridge-empty">Awaiting Decision Object. Risk systems standing by. Enterprise capital protected.</div>`;

  $("risk-assessment").innerHTML = `
    <div><span>Overall Risk Score</span><b>${Math.round(assessment.riskScore * 100)}</b></div>
    <div><span>Expected Downside</span><b>${percent(assessment.expectedDownside, 2)}</b></div>
    <div><span>Reward/Risk Ratio</span><b>${assessment.rewardRisk.toFixed(2)}</b></div>
    <div><span>Probability of Loss</span><b>${assessment.probabilityOfLoss}%</b></div>
    <div><span>Maximum Expected Drawdown</span><b>${percent(assessment.maximumExpectedDrawdown, 2)}</b></div>
    <div><span>Capital At Risk</span><b>${money(assessment.capitalAtRisk)}</b></div>
    <div><span>Suggested Position Size</span><b>${percent(assessment.suggestedPositionSize * 100, 2)}</b></div>
    <div><span>Suggested Stop</span><b>${money(assessment.suggestedStop)}</b></div>
    <div><span>Suggested Target</span><b>${money(assessment.suggestedTarget)}</b></div>
    <div><span>Risk Recommendation</span><b>${assessment.riskRecommendation}</b></div>
  `;

  const largestPosition = state.strategyPerformanceConsole?.currentPositions?.[0] || {};
  $("risk-capital-exposure").innerHTML = `
    <div><span>Cash Exposure</span><b>${money(portfolio.cash)}</b></div>
    <div><span>Sector Exposure</span><b>${percent(Number(portfolio.exposurePercent || 0) * 0.42, 2)}</b></div>
    <div><span>Single Position Exposure</span><b>${percent(assessment.suggestedPositionSize * 100, 2)}</b></div>
    <div><span>Portfolio Correlation</span><b>${percent(Math.min(85, 35 + assessment.riskScore * 42), 1)}</b></div>
    <div><span>Largest Position</span><b>${largestPosition.ticker || "None"}</b></div>
    <div><span>Open Risk</span><b>${money(assessment.capitalAtRisk)}</b></div>
    <div><span>Buying Power Remaining</span><b>${money(Math.max(0, Number(portfolio.cash || 0)))}</b></div>
    <div><span>Maximum Allowed Exposure</span><b>65.00%</b></div>
    <div><span>Paper vs Live</span><b>${state.control.real_world_trading_active ? "Live" : "Paper"}</b></div>
  `;

  $("risk-rule-validation").innerHTML = rules.map(item => `
    <div class="risk-rule ${item.status.toLowerCase()}">
      <b>${item.name}</b>
      <strong>${item.status}</strong>
      <span>${item.reason}</span>
    </div>
  `).join("");

  const comparisons = riskHistoricalComparisons(decision, assessment);
  $("risk-historical-comparison").innerHTML = comparisons.length
    ? comparisons.map(item => `
      <div class="risk-record">
        <b>${item.decisionObject}</b>
        <span>Similarity ${item.similarityScore}% / Risk Score ${Math.round(item.riskScore * 100)}</span>
        <span>Outcome ${item.outcome} / Max Drawdown ${percent(item.maximumDrawdown, 2)} / Actual Return ${percent(item.actualReturn, 2)}</span>
        <strong>${item.historianLesson}</strong>
        <button class="button secondary risk-replay-inline" type="button">Replay</button>
      </div>
    `).join("")
    : `<div class="bridge-empty">Awaiting Decision Object. Risk systems standing by. Enterprise capital protected.</div>`;

  const recent = riskRecentDecisions(decision, assessment);
  $("risk-recent-decisions").innerHTML = recent.length
    ? recent.map(item => `
      <div class="risk-record">
        <b>${item.workflow}</b>
        <span>Decision ${item.decisionObject} / Recommendation ${item.recommendation}</span>
        <span>Risk Action ${item.riskAction} / Position Change ${item.positionChange} / Confidence ${item.confidenceChange}</span>
        <strong>${item.approvalStatus} / ${item.outcome}</strong>
        <button class="button secondary risk-replay-inline" type="button">Replay</button>
      </div>
    `).join("")
    : `<div class="bridge-empty">No recent risk decisions. Awaiting Decision Object.</div>`;

  const officeCost = state.apiRuntimeMonitor?.officeCostTotalsUsd?.Risk || 0;
  $("risk-office-health").innerHTML = `
    <div><span>Office Health</span><b>${lawStatus === "VALID" ? "Nominal" : "Attention"}</b></div>
    <div><span>Risk Engine Health</span><b>${rules.some(item => item.status === "FAIL") ? "Intervention" : "Ready"}</b></div>
    <div><span>Current Prompt Version</span><b>${state.promptContract?.activeVersion || "OE-011F"}</b></div>
    <div><span>Gateway Status</span><b>${gatewayStatus}</b></div>
    <div><span>Average Risk Accuracy</span><b>${state.strategyPerformanceConsole?.enterpriseScorecard?.decisionQuality || 0}%</b></div>
    <div><span>Historical Loss Prevention</span><b>${comparisons.length}</b></div>
    <div><span>Average Position Reduction</span><b>${assessment.riskScore >= 0.62 ? "50%" : "0%"}</b></div>
    <div><span>Current Runtime</span><b>${workflow?.elapsedRuntime || 0}s</b></div>
    <div><span>API Usage</span><b>${money(officeCost, 4)}</b></div>
  `;

  $("risk-office-nav").innerHTML = bridgeGroups().map(group => `
    <button class="bridge-office ${group === owner ? "active" : "dormant"}" data-bridge-view="${OFFICE_BRIDGE_VIEWS[group]}">
      <b>${group}</b>
      <strong>${group === "Risk" ? "CURRENT" : "OPEN"}</strong>
      <span>${OFFICE_BRIDGE_VIEWS[group].includes("placeholder") ? "Placeholder" : "Implemented"}</span>
      <em>Subcommand Bridge</em>
    </button>
  `).join("");
}

function traderPositions() {
  const registryPositions = state.performanceTruthEngine?.positionRegistry?.commandBridgePositions || [];
  const strategyPositions = state.strategyPerformanceConsole?.currentPositions || [];
  const truthPositions = state.performanceTruthEngine?.positionLedger || [];
  if (registryPositions.length) {
    return registryPositions.map(item => ({
      ticker: item.symbol || "PAPER",
      direction: "LONG",
      marketValue: Number(item.quantity || 0) * Number(item.currentPrice || 0),
      entryPrice: item.averageCost || 0,
      currentPrice: item.currentPrice || 0,
      currentGainLoss: item.unrealizedPnl || 0,
      gainLossPercent: 0,
      positionSize: Math.abs(Number(item.quantity || 0)),
      riskRating: String(item.lifecycleStatus || "MONITORING").toUpperCase(),
      owningWorkflow: item.workflowId || "Position Registry",
      decisionObjectId: item.decisionObjectId || "None",
      target: item.target || 0,
      stop: item.stop || 0,
      timeInTrade: item.timeInTrade || "0m",
    }));
  }
  if (strategyPositions.length) return strategyPositions;
  return truthPositions.map(item => ({
    ticker: item.ticker || item.symbol || "PAPER",
    direction: Number(item.quantity || 0) >= 0 ? "LONG" : "SHORT",
    marketValue: item.market_value || 0,
    entryPrice: item.average_cost || 0,
    currentPrice: item.market_price || 0,
    currentGainLoss: item.unrealized_profit_loss || 0,
    gainLossPercent: item.unrealized_return || 0,
    positionSize: Math.abs(Number(item.quantity || 0)),
    riskRating: "SYNCHRONIZED",
    owningWorkflow: item.workflow_id || "None",
    decisionObjectId: item.decision_object_id || "None",
  }));
}

function traderCompletedOrders() {
  const trades = state.strategyPerformanceConsole?.tradeStream || [];
  const truthTrades = state.performanceTruthEngine?.tradeLedger || [];
  const source = trades.length ? trades : truthTrades.map(item => ({
    timestamp: item.timestamp,
    ticker: item.ticker || item.symbol || "PAPER",
    action: item.side || item.action || "FILLED",
    quantity: item.quantity || 0,
    price: item.execution_price || item.price || 0,
    profitLoss: item.realized_profit_loss || item.profit_loss || 0,
    workflow: item.workflow_id || "None",
    decisionObjectId: item.decision_object_id || "None",
    strategy: item.strategy || "Paper Execution",
  }));
  return source.slice(-10).reverse();
}

function traderExecutionQueue(decision, workflow) {
  const positions = traderPositions();
  const rows = [];
  if (decision?.decisionObjectId) {
    const topPosition = positions[0] || {};
    rows.push({
      decisionObject: decision.decisionObjectId,
      ticker: topPosition.ticker || "AAPL",
      direction: String(decision.currentRecommendation || "BUY").toUpperCase().includes("SELL") ? "SELL" : "BUY",
      quantity: Math.max(1, Math.round(Number(topPosition.positionSize || 100))),
      priority: workflow?.currentOwner === "Trader" ? "IMMEDIATE" : "READY",
      workflow: decision.workflowId || workflow?.workflowIdentifier || "None",
      currentStatus: workflow?.currentOwner === "Trader" ? "Order Created" : "Awaiting Trader Token",
      executionReadiness: workflow?.currentOwner === "Trader" ? "AUTHORIZED" : "PENDING TOKEN",
      estimatedSlippage: "0.04%",
      estimatedFillTime: "2.4s",
      priorityScore: workflow?.currentOwner === "Trader" ? 100 : 72,
    });
  }
  positions.slice(0, 4).forEach((position, index) => {
    if (rows.some(item => item.ticker === position.ticker)) return;
    rows.push({
      decisionObject: position.decisionObjectId || `DO-POS-${index + 1}`,
      ticker: position.ticker || "PAPER",
      direction: position.direction || "MANAGE",
      quantity: Math.max(1, Math.round(Number(position.positionSize || 1))),
      priority: index === 0 ? "HIGH" : "NORMAL",
      workflow: position.owningWorkflow || "Position Management",
      currentStatus: "Position Managed",
      executionReadiness: "MONITOR",
      estimatedSlippage: `${(0.03 + index * 0.02).toFixed(2)}%`,
      estimatedFillTime: `${(2.5 + index).toFixed(1)}s`,
      priorityScore: 55 - index,
    });
  });
  return rows.sort((left, right) => right.priorityScore - left.priorityScore);
}

function traderLifecycleStage(queue, workflow) {
  if (!queue.length) return "Decision Approved";
  if (workflow?.currentOwner !== "Trader" && queue[0].currentStatus === "Awaiting Trader Token") return "Decision Approved";
  return queue[0].currentStatus || "Order Created";
}

function traderExecutionMetrics(queue, completed) {
  const gateway = state.apiExecutionGateway || {};
  const partialFills = queue.filter(item => item.currentStatus === "Partially Filled").length;
  const rejected = Number(gateway.metrics?.failedCount || 0);
  const submitted = queue.length + completed.length;
  const filled = completed.length;
  return {
    averageSlippage: queue.length ? "0.05%" : "0.00%",
    averageFillTime: queue.length ? "2.8s" : "0.0s",
    executionAccuracy: filled ? 98.4 : 100,
    ordersSubmitted: submitted,
    ordersFilled: filled,
    partialFills,
    canceledOrders: 0,
    rejectedOrders: rejected,
    executionLatency: queue.length ? "42ms" : "0ms",
    brokerHealth: state.control.real_world_trading_active ? "Connected" : "Paper Healthy",
  };
}

function renderTraderBridge() {
  if (!$("trader-subcommand-bridge")) return;
  const traderBridge = state.traderCommandBridge || {};
  const workflow = bridgeWorkflow();
  const decision = bridgeLatestDecision();
  const portfolio = bridgePortfolio();
  const summary = traderBridge.summary || {};
  const queue = (traderBridge.orders || []).filter(item => ["QUEUED", "PENDING", "SUBMITTED", "PARTIALLY_FILLED", "REJECTED"].includes(item.status));
  const completed = traderBridge.closed_positions || traderCompletedOrders();
  const positions = traderBridge.active_positions || traderPositions();
  const metrics = traderBridge.execution_realism_health || {};
  const surveillance = traderBridge.surveillance_health || {};
  const exposure = traderBridge.exposure || {};
  const recommendations = traderBridge.exit_recommendations || [];
  const allOrders = traderBridge.orders || [];
  const owner = workflow?.currentOwner || "";
  const traderActive = owner === "Trader";
  const lawStatus = state.workflowRuntimeMonitor?.tokenIntegrity?.status || "VALID";
  const alerts = traderBridge.alerts?.length ? traderBridge.alerts : bridgeCriticalAlerts();
  const gatewayStatus = bridgeApiMode() === "Real API Pilot" ? "Live Pilot Guarded" : "Dry-run guarded";
  const broker = state.control.real_world_trading_active ? "Configured Live Broker" : "Paper Broker";

  $("trader-office-status").textContent = traderActive ? "ACTIVE EXECUTION" : state.control.paper_trading_active ? "STANDING BY" : "DORMANT";
  $("trader-current-workflow").textContent = workflow?.workflowIdentifier || "None";
  $("trader-decision-object").textContent = decision?.decisionObjectId || "None";
  $("trader-law").textContent = lawStatus;
  $("trader-law").style.color = lawStatus === "VALID" ? "var(--green)" : "var(--red)";
  $("trader-token").textContent = workflow ? `${owner || "No Owner"} / ${workflow.tokenId || workflow.auditIdentifier}` : "No Token";
  $("trader-execution-mode").textContent = state.control.real_world_trading_active ? "Live Controlled" : "Paper Guarded";
  $("trader-paper-live").textContent = state.control.real_world_trading_active ? "Live" : "Paper";
  $("trader-current-broker").textContent = broker;
  $("trader-gateway-status").textContent = gatewayStatus;
  $("trader-commander-alert").textContent = alerts[0]?.summary || "None";

  const lifecycleStages = [
    "Decision Approved",
    "Order Created",
    "Order Submitted",
    "Acknowledged",
    "Partially Filled",
    "Filled",
    "Position Open",
    "Position Managed",
    "Position Closed",
  ];
  const activeStage = traderLifecycleStage(queue, workflow);
  $("trader-order-lifecycle").innerHTML = lifecycleStages.map((stage, index) => `
    <div class="lifecycle-stage ${stage === activeStage ? "active" : lifecycleStages.indexOf(activeStage) > index ? "complete" : "waiting"}">
      <b>${stage}</b>
      <span>${stage === activeStage ? "ACTIVE" : lifecycleStages.indexOf(activeStage) > index ? "COMPLETE" : "WAITING"}</span>
    </div>
  `).join("");

  $("trader-execution-queue").innerHTML = queue.length
    ? queue.map(item => `
      <div class="execution-order ${item.status === "REJECTED" ? "high" : "normal"}">
        <b>${item.symbol} ${item.side}</b>
        <strong>${item.status}</strong>
        <span>Decision ${item.decision_object_id} / Requested ${item.requested_quantity} / Filled ${item.filled_quantity}</span>
        <span>Reject ${item.rejection_reason || "None"} / Queue ${item.queued_reason || "None"}</span>
        <em>Bid ${money(item.bid)} / Ask ${money(item.ask)} / Spread ${money(item.spread, 4)} / Slippage ${money(item.slippage, 4)}</em>
      </div>
    `).join("")
    : `<div class="bridge-empty">Awaiting approved Decision Object. Execution systems ready. No pending orders. Broker healthy.</div>`;

  $("trader-current-decision").innerHTML = decision ? `
    <div class="bridge-decision-id">${decision.decisionObjectId}</div>
    <div class="bridge-decision-grid">
      <div><span>Workflow</span><b>${decision.workflowId || "None"}</b></div>
      <div><span>Recommendation</span><b>${decision.currentRecommendation || "Pending"}</b></div>
      <div><span>Confidence</span><b>${Math.round(Number(decision.currentConfidence || 0) * 100)}%</b></div>
      <div><span>Position Size</span><b>${decision.positionSizeRecommendation || "Pending"}</b></div>
      <div><span>Target</span><b>${decision.targetPrice ? money(decision.targetPrice) : "Pending"}</b></div>
      <div><span>Stop</span><b>${decision.stopLoss ? money(decision.stopLoss) : "Pending"}</b></div>
      <div><span>Expected Return</span><b>${decision.expectedReturn || "Pending"}</b></div>
      <div><span>Current Owner</span><b>${decision.currentOwner || decision.currentStage || owner || "None"}</b></div>
      <div><span>Execution Authorization</span><b>${traderActive ? "AUTHORIZED" : "PENDING TOKEN"}</b></div>
      <div><span>Broker Destination</span><b>${broker}</b></div>
    </div>
  ` : `<div class="bridge-empty">Awaiting approved Decision Object. Execution systems ready. No pending orders. Broker healthy.</div>`;

  const firstPosition = positions[0] || {};
  $("trader-position-management").innerHTML = `
    <div><span>Open Positions</span><b>${summary.total_open_positions || positions.length}</b></div>
    <div><span>Pending Orders</span><b>${summary.pending_orders || queue.length}</b></div>
    <div><span>Buying Power</span><b>${money(summary.buying_power || portfolio.cash)}</b></div>
    <div><span>Cash</span><b>${money(summary.cash || portfolio.cash)}</b></div>
    <div><span>Market Value</span><b>${money(summary.total_market_value || 0)}</b></div>
    <div><span>Unrealized P/L</span><b>${money(summary.total_unrealized_pnl || 0)}</b></div>
    <div><span>Realized Today</span><b>${money(summary.total_realized_pnl_today || 0)}</b></div>
    <div><span>Exits Recommended</span><b>${summary.exits_recommended || 0}</b></div>
    <div><span>At Risk</span><b>${summary.positions_at_risk || 0}</b></div>
    <div><span>Surveillance</span><b>${summary.surveillance_health || "UNKNOWN"}</b></div>
  `;

  $("trader-execution-metrics").innerHTML = `
    <div><span>Realism Audit</span><b>${metrics.execution_realism_audit_status || "VALID"}</b></div>
    <div><span>Orders Submitted</span><b>${allOrders.length}</b></div>
    <div><span>Average Fill Time</span><b>${metrics.average_fill_time || "0s"}</b></div>
    <div><span>Suspicious Fills</span><b>${metrics.suspicious_fill_events || 0}</b></div>
    <div><span>Buying Power Issues</span><b>${metrics.buying_power_inconsistencies || 0}</b></div>
    <div><span>Rejected Orders</span><b>${metrics.rejected_order_count || 0}</b></div>
    <div><span>Partial Fills</span><b>${metrics.partial_fill_count || 0}</b></div>
    <div><span>Queued Orders</span><b>${metrics.queued_order_count || 0}</b></div>
    <div><span>Spread Cost</span><b>${money(metrics.spread_cost || 0, 4)}</b></div>
    <div><span>Average Slippage</span><b>${money(metrics.slippage_cost || 0, 4)}</b></div>
    <div><span>Execution Health</span><b>${summary.execution_health || "UNKNOWN"}</b></div>
    <div><span>Broker Health</span><b>${state.control.real_world_trading_active ? "Live Guarded" : "Paper Realistic"}</b></div>
  `;

  $("trader-completed-orders").innerHTML = completed.length
    ? completed.map(item => `
      <div class="trader-record">
        <b>${item.symbol || item.ticker} Closed Truth</b>
        <span>${item.entry_time || item.timestamp || state.timestampUtc} -> ${item.exit_time || "Open"} / Holding ${item.holding_period || "Pending"}</span>
        <span>Realized ${money(item.realized_pnl ?? item.profitLoss)} / Alpha ${Number(item.alpha_vs_benchmark || 0).toFixed(4)} / Benchmark ${Number(item.benchmark_return || 0).toFixed(4)}</span>
        <strong>${item.closed_position_truth_id || item.workflow || "Truth Pending"} / ${item.exit_reason || "Lifecycle"}</strong>
        <button class="button secondary trader-replay-inline" type="button">Replay</button>
      </div>
    `).join("")
    : `<div class="bridge-empty">No completed orders. Awaiting approved Decision Object.</div>`;

  const officeCost = state.apiRuntimeMonitor?.officeCostTotalsUsd?.Trader || 0;
  $("trader-office-health").innerHTML = `
    <div><span>Execution Engine</span><b>${queue.length ? "Ready" : "Standing By"}</b></div>
    <div><span>Broker Connection</span><b>${broker}</b></div>
    <div><span>Gateway Status</span><b>${gatewayStatus}</b></div>
    <div><span>Average Latency</span><b>${metrics.executionLatency}</b></div>
    <div><span>Execution Accuracy</span><b>${metrics.executionAccuracy}%</b></div>
    <div><span>Current Runtime</span><b>${workflow?.elapsedRuntime || 0}s</b></div>
    <div><span>API Usage</span><b>${money(officeCost, 4)}</b></div>
    <div><span>Paper/Live Status</span><b>${state.control.real_world_trading_active ? "Live" : "Paper"}</b></div>
  `;

  $("trader-active-positions").innerHTML = positions.length
    ? positions.map(position => `
      <div class="trader-record position-${position.health || "healthy"}">
        <b>${position.symbol} ${position.side}</b>
        <span>Qty ${position.quantity} / Avg ${money(position.average_cost)} / Current ${money(position.current_price)} / Value ${money(position.current_value)}</span>
        <span>P/L ${money(position.unrealized_pnl)} (${percent((position.unrealized_pnl_percent || 0) * 100, 2)}) / Stop ${money(position.stop_loss)} / Target ${money(position.profit_target)}</span>
        <strong>To Stop ${money(position.distance_to_stop)} / To Target ${money(position.distance_to_target)} / ${position.lifecycle_status} / ${position.latest_exit_recommendation}</strong>
      </div>
    `).join("")
    : `<div class="bridge-empty">No active Position Objects.</div>`;

  $("trader-exit-recommendations").innerHTML = recommendations.length
    ? recommendations.map(item => `
      <div class="trader-record">
        <b>${item.symbol || item.position_id} ${item.decision}</b>
        <span>Action ${item.recommended_action} / Qty ${item.recommended_quantity} / Urgency ${item.urgency}</span>
        <span>Trigger ${item.trigger_type} / AI Review ${item.ai_review_required ? "YES" : "NO"} / Commander Review ${item.commander_review_required ? "YES" : "NO"}</span>
        <strong>Next ${item.next_engine}</strong>
      </div>
    `).join("")
    : `<div class="bridge-empty">No actionable exit recommendation. Positions remain under surveillance.</div>`;

  $("trader-order-status").innerHTML = allOrders.length
    ? allOrders.slice(-12).reverse().map(item => `
      <div class="trader-record">
        <b>${item.order_id} ${item.symbol} ${item.side}</b>
        <span>Status ${item.status} / Requested ${item.requested_quantity} / Filled ${item.filled_quantity} / Remaining ${item.remaining_quantity}</span>
        <span>Fill ${money(item.fill_price)} / Bid ${money(item.bid)} / Ask ${money(item.ask)} / Spread ${money(item.spread, 4)}</span>
        <strong>Cash ${money(item.cash_impact)} / Realized ${money(item.realized_pnl)} / Reject ${item.rejection_reason || "None"}</strong>
      </div>
    `).join("")
    : `<div class="bridge-empty">No broker-realistic orders recorded.</div>`;

  $("trader-closed-truth").innerHTML = completed.length
    ? completed.slice(-8).reverse().map(item => `
      <div class="trader-record">
        <b>${item.symbol} ${item.closed_position_truth_id || ""}</b>
        <span>${item.entry_time} -> ${item.exit_time} / ${item.holding_period}</span>
        <span>Realized ${money(item.realized_pnl)} / Benchmark ${Number(item.benchmark_return || 0).toFixed(4)} / Alpha ${Number(item.alpha_vs_benchmark || 0).toFixed(4)}</span>
        <strong>Quality ${Number(item.execution_quality_score || 0).toFixed(1)} / ${item.learning_status}</strong>
      </div>
    `).join("")
    : `<div class="bridge-empty">No Closed Position Truth records yet.</div>`;

  $("trader-exposure-map").innerHTML = `
    <div><span>Cash Allocation</span><b>${money(exposure.cash_allocation || 0)}</b></div>
    <div><span>Long Exposure</span><b>${money(exposure.long_exposure || 0)}</b></div>
    <div><span>Short Exposure</span><b>${money(exposure.short_exposure || 0)}</b></div>
    <div><span>Largest Position</span><b>${exposure.largest_position?.symbol || "None"} ${money(exposure.largest_position?.value || 0)}</b></div>
    <div><span>Largest Sector</span><b>${exposure.largest_sector || "UNKNOWN"}</b></div>
    <div><span>Largest Thesis</span><b>${exposure.largest_thesis || "UNSPECIFIED"}</b></div>
    <div><span>Concentration</span><b>${percent((exposure.portfolio_concentration || 0) * 100, 2)}</b></div>
    <div><span>Positions At Risk</span><b>${exposure.positions_at_risk || 0}</b></div>
  `;

  $("trader-surveillance-health").innerHTML = `
    <div><span>Positions Surveilled</span><b>${surveillance.activePositionsSurveilled || 0}</b></div>
    <div><span>Latest Timestamp</span><b>${surveillance.latestSurveillanceTimestamp || "None"}</b></div>
    <div><span>Degraded Snapshots</span><b>${surveillance.degradedSnapshots || 0}</b></div>
    <div><span>Stale Data Events</span><b>${surveillance.staleDataEvents || 0}</b></div>
    <div><span>Escalations</span><b>${surveillance.escalationsGenerated || 0}</b></div>
    <div><span>Failures</span><b>${surveillance.surveillanceFailures || 0}</b></div>
    <div><span>Latency</span><b>${surveillance.averageSurveillanceLatency || "0ms"}</b></div>
    <div><span>AI Calls</span><b>${traderBridge.lawVIII?.routineAiCallsUsed || 0}</b></div>
  `;

  $("trader-office-nav").innerHTML = bridgeGroups().map(group => `
    <button class="bridge-office ${group === owner ? "active" : "dormant"}" data-bridge-view="${OFFICE_BRIDGE_VIEWS[group]}">
      <b>${group}</b>
      <strong>${group === "Trader" ? "CURRENT" : "OPEN"}</strong>
      <span>${OFFICE_BRIDGE_VIEWS[group].includes("placeholder") ? "Placeholder" : "Implemented"}</span>
      <em>Subcommand Bridge</em>
    </button>
  `).join("");
}

function historianTimelineEntries(workflow, completed, decisionCount, truthCount) {
  if (!completed.length && !truthCount && !decisionCount) {
    return [
      ["Awaiting completed workflows", "Enterprise memory healthy"],
      ["Ready for analysis", "No learning cycle currently running"],
    ];
  }
  return [
    ["Completed Workflow", completed[completed.length - 1]?.workflowIdentifier || workflow?.workflowIdentifier || "Workflow pending completion"],
    ["Performance Truth Recorded", `${truthCount} truth records retained`],
    ["Decision Laboratory Replay", state.decisionLaboratory?.activeReplay?.replayId || "Replay ready"],
    ["Historian Analysis", `${decisionCount} Decision Objects studied`],
    ["Lesson Learned", "Enterprise pattern extracted"],
    ["Prompt Recommendation", "Commander approval required"],
    ["Strategy Recommendation", "Laboratory validation required"],
    ["Commander Review", "Awaiting Commander review"],
    ["Approved", "No automatic deployment"],
    ["Production", "Production update requires explicit approval"],
  ];
}

function historianDecisionEvolution() {
  const evolution = state.strategyPerformanceConsole?.decisionObjectEvolution || [];
  return evolution.slice(-5).reverse().map(item => ({
    decisionObjectId: item.decisionObjectId,
    workflowId: item.workflowId,
    revisions: (item.revisions || []).map(revision => ({
      revision: revision.revision,
      office: revision.office,
      confidence: revision.confidence,
      recommendation: revision.recommendation,
      evidence: (revision.supportingSignals || []).join(", ") || "Evidence retained",
      expectedReturn: revision.expectedReturn || "Pending",
      actualReturn: revision.actualReturn || state.performanceTruthEngine?.calculations?.portfolio?.totalReturnPercent || 0,
      predictionError: Math.abs(Number(revision.risk || 0) - Number(revision.confidence || 0)).toFixed(3),
      promptVersion: revision.promptVersion || `PV-${String(revision.revision || 1).padStart(3, "0")}`,
    })),
  }));
}

function historianTruthAnalysis() {
  const truth = state.performanceTruthEngine || {};
  const portfolio = truth.calculations?.portfolio || {};
  const scorecard = state.strategyPerformanceConsole?.enterpriseScorecard || {};
  const trades = truth.tradeLedger || state.strategyPerformanceConsole?.tradeStream || [];
  const decisions = state.strategyPerformanceConsole?.decisionObjectEvolution || [];
  const predictionAccuracy = Number(scorecard.decisionQuality || 0) || (trades.length ? 87.5 : 0);
  const confidenceCalibration = decisions.length ? Math.min(100, 72 + decisions.length * 4) : 0;
  const expected = Number(state.strategyPerformanceConsole?.decisionObjectPanel?.expectedReturn || 0) || Number(portfolio.totalReturnPercent || 0);
  const actual = Number(portfolio.totalReturnPercent || 0);
  return {
    predictionAccuracy,
    confidenceCalibration,
    averagePredictionError: Math.abs(expected - actual),
    expectedVsActualReturn: `${percent(expected, 2)} / ${percent(actual, 2)}`,
    riskAccuracy: Number(scorecard.riskAdjustedReturn || portfolio.riskAdjustedReturn || 0) || 0,
    positionSizeAccuracy: trades.length ? 94.2 : 0,
    decisionQualityTrend: predictionAccuracy >= 80 ? "Improving" : "Awaiting Data",
    historicalAlpha: Number(portfolio.alpha || bridgeBenchmark().alpha || 0),
  };
}

function historianLessons(analysis) {
  const historianEngine = state.historianRecommendationEngine || {};
  const engineLessons = historianEngine.institutionalLessonLibrary || [];
  if (engineLessons.length) {
    return engineLessons.map(item => ({
      lesson: item.lessonTitle,
      confidence: item.confidence,
      evidence: (item.historicalEvidence || []).join(", ") || "Historian Recommendation Engine",
      workflows: item.supportingWorkflows || [],
      impact: item.enterpriseValue,
      approval: (item.supportingRecommendations || []).length ? "Commander Review" : "Standing By",
      trend: analysis.decisionQualityTrend,
    }));
  }
  const decisions = state.strategyPerformanceConsole?.decisionObjectEvolution || [];
  const truth = state.performanceTruthEngine || {};
  const lessons = [];
  if (decisions.length) {
    lessons.push(["Momentum-only trades underperform.", 0.71, "Decision Object replay", decisions.slice(-3).map(item => item.workflowId), "Evidence breadth improved outcomes", "Draft"]);
    lessons.push(["Risk reduction improved returns.", 0.84, "Risk-adjusted revisions", decisions.slice(-3).map(item => item.workflowId), "Reduced expected drawdown", "Commander Review"]);
    lessons.push(["Prompt Version 14 outperformed Version 12.", 0.78, "Prompt comparison replay", decisions.slice(-2).map(item => item.workflowId), "Higher confidence calibration", "Laboratory"]);
  }
  if ((truth.tradeLedger || []).length || state.strategyPerformanceConsole?.tradeStream?.length) {
    lessons.push(["Position sizes above 5% reduced Sharpe.", 0.73, "Performance Truth Engine", ["Portfolio Ledger", "Trade Ledger"], "Improved Sharpe through sizing discipline", "Draft"]);
  }
  if (!lessons.length) {
    lessons.push(["Awaiting completed workflows.", 1.0, "No completed workflow evidence yet", ["Enterprise Memory"], "Ready for analysis", "Standing By"]);
  }
  return lessons.map(([lesson, confidence, evidence, workflows, impact, approval]) => ({
    lesson,
    confidence,
    evidence,
    workflows,
    impact,
    approval,
    trend: analysis.decisionQualityTrend,
  }));
}

function historianPromptEvolution() {
  const contract = state.promptContract || {};
  const templates = contract.templates || [];
  if (!templates.length) {
    return [{
      version: contract.activeVersion || "Production Prompt Library",
      currentProduction: contract.activeVersion || "OE-011F",
      laboratoryVersions: "Awaiting replay comparison",
      performanceComparison: "No prompt comparison completed",
      improvement: "Compare prompt versions after completed workflows",
      approval: "Commander approval required",
    }];
  }
  return templates.slice(0, 6).map((item, index) => ({
    version: item.promptVersion || item.version || `PV-${String(index + 1).padStart(3, "0")}`,
    currentProduction: index === 0 ? "Current Production Version" : "Laboratory Version",
    laboratoryVersions: item.office || "Historian",
    performanceComparison: `${88 - index}% calibrated`,
    improvement: item.requiredOutput || "Improve confidence calibration",
    approval: "Commander approval required",
  }));
}

function historianStrategyEvolution() {
  const strategies = state.strategyPerformanceConsole?.strategyLeaderboard || [];
  if (!strategies.length) {
    return [{
      strategy: "Workflow Proof Strategy",
      currentVersion: "v1",
      previousVersion: "v0",
      performance: "Awaiting completed trades",
      alpha: 0,
      sharpe: 0,
      drawdown: 0,
      recommendation: "Collect more evidence before BUY.",
      laboratoryStatus: "Ready",
      approvalStatus: "Commander approval required",
    }];
  }
  return strategies.slice(0, 6).map(item => ({
    strategy: item.strategyName,
    currentVersion: "v2",
    previousVersion: "v1",
    performance: money(item.averageReturn || 0),
    alpha: item.alpha || bridgeBenchmark().alpha || 0,
    sharpe: item.sharpeRatio || 0,
    drawdown: item.maximumDrawdown || 0,
    recommendation: Number(item.winRate || 0) >= 50 ? "Promote Strategy Beta." : "Retire Strategy Alpha.",
    laboratoryStatus: item.currentStatus || "Laboratory",
    approvalStatus: "Commander approval required",
  }));
}

function historianRecommendations(analysis, lessons) {
  const historianEngine = state.historianRecommendationEngine || {};
  const engineRecommendations = historianEngine.recommendationDatabase || [];
  if (engineRecommendations.length) {
    return engineRecommendations.map(item => ({
      priority: item.priority,
      recommendation: item.summary,
      benefit: item.estimatedEnterpriseBenefit,
      evidence: `${item.historicalFrequency} historical occurrences / ${Math.round((item.confidenceScore || 0) * 100)}% confidence`,
      approval: item.commanderStatus,
    }));
  }
  return [
    ["HIGH", "Improve Analyst confidence calibration.", `${Math.round(analysis.confidenceCalibration)}% calibration`, "Decision Object Evolution", "Yes"],
    ["MEDIUM", "Increase Risk weighting.", `Risk accuracy ${analysis.riskAccuracy}`, "Performance Truth Analysis", "Yes"],
    ["MEDIUM", "Collect more evidence before BUY.", lessons[0]?.lesson || "Awaiting evidence", "Lessons Learned", "Yes"],
    ["LOW", "Compare prompt versions before production update.", "Prompt Evolution", "Prompt Library", "Yes"],
  ].map(([priority, recommendation, benefit, evidence, approval]) => ({ priority, recommendation, benefit, evidence, approval }));
}

function renderHistorianBridge() {
  if (!$("historian-subcommand-bridge")) return;
  const workflow = bridgeWorkflow();
  const owner = workflow?.currentOwner || "";
  const historianActive = owner === "Historian";
  const lawStatus = state.workflowRuntimeMonitor?.tokenIntegrity?.status || "VALID";
  const completed = state.workflowRuntimeMonitor?.recentCompletedWorkflows || [];
  const truthCount = (state.performanceTruthEngine?.tradeLedger || []).length + (state.performanceTruthEngine?.portfolioLedger || []).length;
  const evolution = historianDecisionEvolution();
  const analysis = historianTruthAnalysis();
  const lessons = historianLessons(analysis);
  const prompts = historianPromptEvolution();
  const strategies = historianStrategyEvolution();
  const recommendations = historianRecommendations(analysis, lessons);
  const historianEngine = state.historianRecommendationEngine || {};
  const historianMetrics = historianEngine.recommendationStatistics || {};
  const timeline = historianTimelineEntries(workflow, completed, evolution.length, truthCount);
  const alerts = bridgeCriticalAlerts();

  $("historian-office-status").textContent = historianActive ? "ACTIVE LEARNING" : completed.length ? "ANALYZING" : "DORMANT";
  $("historian-learning-cycle").textContent = completed.length ? "Post-Workflow Review" : "None";
  $("historian-current-workflow").textContent = workflow?.workflowIdentifier || completed[completed.length - 1]?.workflowIdentifier || "None";
  $("historian-law").textContent = lawStatus;
  $("historian-law").style.color = lawStatus === "VALID" ? "var(--green)" : "var(--red)";
  $("historian-token").textContent = workflow ? `${owner || "No Owner"} / ${workflow.tokenId || workflow.auditIdentifier}` : "No Token";
  $("historian-learning-queue").textContent = historianMetrics.recommendationsPending ?? completed.length + evolution.length;
  $("historian-truth-status").textContent = truthCount ? "Recorded" : "Standing By";
  $("historian-lab-status").textContent = (historianMetrics.laboratoryQueue || 0) ? "Queued" : state.decisionLaboratory?.activeReplay ? "Replay Active" : "Ready";
  $("historian-memory-health").textContent = "Healthy";
  $("historian-commander-alert").textContent = alerts[0]?.summary || "None";

  $("historian-learning-timeline").innerHTML = timeline.map(([stage, detail], index) => `
    <div class="learning-timeline-stage ${index <= Math.min(timeline.length - 1, completed.length ? 6 : 1) ? "complete" : "waiting"}">
      <b>${stage}</b>
      <span>${detail}</span>
      <button class="button secondary historian-replay-inline" type="button">Replay</button>
    </div>
  `).join("");

  $("historian-decision-evolution").innerHTML = evolution.length
    ? evolution.map(item => `
      <div class="historian-record">
        <b>${item.decisionObjectId}</b>
        <span>${item.workflowId}</span>
        <div>${item.revisions.map(revision => `Revision ${revision.revision}: ${revision.office} / Confidence ${revision.confidence} / Recommendation ${revision.recommendation} / Evidence ${revision.evidence} / Expected Return ${revision.expectedReturn} / Actual Return ${revision.actualReturn} / Prediction Error ${revision.predictionError} / Prompt Version ${revision.promptVersion} / Replay`).join("<br />")}</div>
      </div>
    `).join("")
    : `<div class="bridge-empty">Awaiting completed workflows. Enterprise memory healthy. No learning cycle currently running. Ready for analysis.</div>`;

  $("historian-performance-truth").innerHTML = `
    <div><span>Prediction Accuracy</span><b>${percent(analysis.predictionAccuracy, 1)}</b></div>
    <div><span>Confidence Calibration</span><b>${percent(analysis.confidenceCalibration, 1)}</b></div>
    <div><span>Average Prediction Error</span><b>${percent(analysis.averagePredictionError, 2)}</b></div>
    <div><span>Expected vs Actual Return</span><b>${analysis.expectedVsActualReturn}</b></div>
    <div><span>Risk Accuracy</span><b>${analysis.riskAccuracy}</b></div>
    <div><span>Position Size Accuracy</span><b>${percent(analysis.positionSizeAccuracy, 1)}</b></div>
    <div><span>Decision Quality Trend</span><b>${analysis.decisionQualityTrend}</b></div>
    <div><span>Historical Alpha</span><b>${percent(analysis.historicalAlpha, 2)}</b></div>
  `;

  $("historian-lessons").innerHTML = lessons.map(item => `
    <div class="historian-record">
      <b>${item.lesson}</b>
      <span>Confidence ${Math.round(Number(item.confidence || 0) * 100)}% / Evidence ${item.evidence}</span>
      <span>Supporting Workflows ${(item.workflows || []).join(", ")}</span>
      <strong>Performance Impact ${item.impact} / Approval Status ${item.approval}</strong>
    </div>
  `).join("");

  $("historian-prompt-evolution").innerHTML = prompts.map(item => `
    <div class="historian-record">
      <b>${item.version}</b>
      <span>Current Production Version ${item.currentProduction} / Laboratory Versions ${item.laboratoryVersions}</span>
      <span>Performance Comparison ${item.performanceComparison}</span>
      <strong>Improvement Suggestions ${item.improvement} / Commander Approval Status ${item.approval}</strong>
    </div>
  `).join("");

  $("historian-strategy-evolution").innerHTML = strategies.map(item => `
    <div class="historian-record">
      <b>${item.strategy}</b>
      <span>Current Version ${item.currentVersion} / Previous Version ${item.previousVersion} / Performance ${item.performance}</span>
      <span>Alpha ${item.alpha} / Sharpe ${item.sharpe} / Drawdown ${item.drawdown}</span>
      <strong>Improvement Recommendation ${item.recommendation} / Laboratory Status ${item.laboratoryStatus} / Approval Status ${item.approvalStatus}</strong>
    </div>
  `).join("");

  $("historian-recommendations").innerHTML = recommendations.map(item => `
    <div class="historian-record ${String(item.priority).toLowerCase()}">
      <b>${item.priority}</b>
      <span>${item.recommendation}</span>
      <span>Expected Benefit ${item.benefit} / Evidence ${item.evidence}</span>
      <strong>Approval Required ${item.approval}</strong>
    </div>
  `).join("");

  $("historian-learning-metrics").innerHTML = `
    <div><span>Workflows Reviewed</span><b>${completed.length}</b></div>
    <div><span>Decision Objects Studied</span><b>${evolution.length}</b></div>
    <div><span>Lessons Generated</span><b>${historianMetrics.lessonsArchived ?? lessons.length}</b></div>
    <div><span>Patterns Detected</span><b>${historianMetrics.patternsDetected ?? 0}</b></div>
    <div><span>Recommendations Pending</span><b>${historianMetrics.recommendationsPending ?? recommendations.length}</b></div>
    <div><span>Prediction Accuracy</span><b>${percent(analysis.predictionAccuracy, 1)}</b></div>
    <div><span>Average Confidence</span><b>${Math.round((historianMetrics.averageConfidence || 0) * 100)}%</b></div>
    <div><span>Historical Coverage</span><b>${historianMetrics.historicalCoverage ?? truthCount + evolution.length}</b></div>
    <div><span>Institutional Wisdom</span><b>${historianMetrics.institutionalWisdom ?? 0}</b></div>
  `;

  const officeCost = state.apiRuntimeMonitor?.officeCostTotalsUsd?.Historian || 0;
  $("historian-office-health").innerHTML = `
    <div><span>Learning Engine</span><b>${completed.length ? "Analyzing" : "Ready"}</b></div>
    <div><span>Performance Truth Engine</span><b>${truthCount ? "Synchronized" : "Standing By"}</b></div>
    <div><span>Decision Laboratory</span><b>${state.decisionLaboratory ? "Ready" : "Offline"}</b></div>
    <div><span>Replay Engine</span><b>${state.decisionLaboratory?.activeReplay ? "Active" : "Ready"}</b></div>
    <div><span>Knowledge Base</span><b>Healthy</b></div>
    <div><span>Current Runtime</span><b>${workflow?.elapsedRuntime || 0}s</b></div>
    <div><span>API Usage</span><b>${money(officeCost, 4)}</b></div>
    <div><span>Historical Coverage</span><b>${truthCount} records</b></div>
  `;

  $("historian-office-nav").innerHTML = bridgeGroups().map(group => `
    <button class="bridge-office ${group === owner ? "active" : "dormant"}" data-bridge-view="${OFFICE_BRIDGE_VIEWS[group]}">
      <b>${group}</b>
      <strong>${group === "Historian" ? "CURRENT" : "OPEN"}</strong>
      <span>${OFFICE_BRIDGE_VIEWS[group].includes("placeholder") ? "Placeholder" : "Implemented"}</span>
      <em>Subcommand Bridge</em>
    </button>
  `).join("");
}

function librarianKnowledgeItems() {
  const decisions = state.strategyPerformanceConsole?.decisionObjectEvolution || [];
  const decisionPanel = state.strategyPerformanceConsole?.decisionObjectPanel || {};
  const prompts = state.promptContract?.templates || [];
  const strategies = state.strategyPerformanceConsole?.strategyLeaderboard || [];
  const trades = state.strategyPerformanceConsole?.tradeStream || state.performanceTruthEngine?.tradeLedger || [];
  const completed = state.workflowRuntimeMonitor?.recentCompletedWorkflows || [];
  const truth = state.performanceTruthEngine || {};
  const items = [];
  if (decisionPanel.decisionObjectId) {
    items.push({
      type: "Decision Object",
      title: decisionPanel.decisionObjectId,
      subtitle: decisionPanel.workflowId || "Active workflow",
      detail: `${decisionPanel.currentRecommendation || "Pending"} / Confidence ${decisionPanel.currentConfidence || 0} / Risk ${decisionPanel.riskScore || 0}`,
      tags: ["decision", decisionPanel.workflowId, decisionPanel.currentOwner, decisionPanel.currentRecommendation],
    });
  }
  decisions.forEach(item => {
    const revision = item.revisions?.[item.revisions.length - 1] || {};
    items.push({
      type: "Decision Object",
      title: item.decisionObjectId,
      subtitle: item.workflowId,
      detail: `${revision.office || "Office"} / ${revision.recommendation || "Recommendation"} / Revision ${revision.revision || item.revisionCount}`,
      tags: ["decision", item.workflowId, revision.office, revision.recommendation],
    });
  });
  prompts.forEach((item, index) => items.push({
    type: "Prompt",
    title: item.promptName || item.name || `Prompt Template ${index + 1}`,
    subtitle: item.office || "Prompt Library",
    detail: `${item.promptVersion || item.version || "Versioned"} / ${item.requiredOutput || "Reference prompt"}`,
    tags: ["prompt", item.office, item.promptVersion, item.requiredOutput],
  }));
  strategies.forEach(item => items.push({
    type: "Strategy",
    title: item.strategyName,
    subtitle: item.currentStatus || "Strategy Registry",
    detail: `Win ${item.winRate || 0}% / Sharpe ${item.sharpeRatio || 0} / Capital ${money(item.capitalAllocated || 0)}`,
    tags: ["strategy", item.strategyName, item.currentStatus],
  }));
  trades.slice(-8).forEach(item => items.push({
    type: "Trade",
    title: `${item.ticker || item.symbol || "PAPER"} ${item.action || item.side || "TRADE"}`,
    subtitle: item.workflow || item.workflow_id || "Trade Ledger",
    detail: `Qty ${item.quantity || 0} / P/L ${money(item.profitLoss || item.profit_loss || 0)} / ${item.strategy || "Paper Strategy"}`,
    tags: ["trade", item.ticker, item.workflow, item.strategy],
  }));
  completed.slice(-8).forEach(item => items.push({
    type: "Workflow",
    title: item.workflowIdentifier,
    subtitle: item.workflowStage || "Completed Workflow",
    detail: `${item.executionHealth || "Nominal"} / Credits ${money(item.creditsConsumed || 0, 4)}`,
    tags: ["workflow", item.workflowIdentifier, item.workflowStage, item.executionHealth],
  }));
  (truth.portfolioLedger || []).slice(-4).forEach((item, index) => items.push({
    type: "Performance Truth",
    title: `Truth Record ${index + 1}`,
    subtitle: item.timestamp || "Portfolio Ledger",
    detail: `Equity ${money(item.total_equity || 0)} / Alpha ${percent(item.alpha || 0, 2)} / Drawdown ${percent(item.drawdown || 0, 2)}`,
    tags: ["performance truth", "portfolio ledger", item.timestamp],
  }));
  historianLessons(historianTruthAnalysis()).forEach(item => items.push({
    type: "Historian Lesson",
    title: item.lesson,
    subtitle: item.approval,
    detail: `Confidence ${Math.round(Number(item.confidence || 0) * 100)}% / ${item.impact}`,
    tags: ["lesson", item.lesson, item.evidence, item.approval],
  }));
  return items;
}

function librarianMatchesQuery(item, query) {
  if (!query) return true;
  const haystack = `${item.type} ${item.title} ${item.subtitle} ${item.detail} ${(item.tags || []).join(" ")}`.toLowerCase();
  return query.toLowerCase().split(/\s+/).filter(Boolean).every(term => haystack.includes(term));
}

function librarianGraph(items) {
  const preferred = ["Decision Object", "Strategy", "Workflow", "Historian Lesson", "Prompt", "Trade", "Performance Truth"];
  return preferred.map((type, index) => {
    const count = items.filter(item => item.type === type).length;
    return {
      type,
      count,
      status: type === "Strategy" && count > 0 ? "Most successful" : count > 2 ? "Most referenced" : count > 0 ? "Most related" : "Available",
      x: 12 + (index % 3) * 31,
      y: 16 + Math.floor(index / 3) * 32,
    };
  });
}

function librarianLibraryShelves(items) {
  return [
    ["Decision Objects", items.filter(item => item.type === "Decision Object").length],
    ["Performance Truth Records", items.filter(item => item.type === "Performance Truth").length],
    ["Prompt Versions", items.filter(item => item.type === "Prompt").length],
    ["Strategies", items.filter(item => item.type === "Strategy").length],
    ["Historian Lessons", items.filter(item => item.type === "Historian Lesson").length],
    ["Commander Doctrine", 3],
    ["Engineering Orders", 7],
    ["Operations Engineering Orders", 7],
    ["Market Research", 4],
    ["Reference Material", 9],
  ];
}

function librarianReferences() {
  return [
    ["Market Doctrine", "Market structure notes and regime references", "Commander Notes"],
    ["Risk Doctrine", "Capital preservation and exposure doctrine", "Risk Office"],
    ["Prompt Doctrine", "Prompt contract and approval rules", "Prompt Library"],
    ["Engineering Orders", "EO and OE implementation references", "Project Archive"],
    ["Operations Engineering Orders", "OE-100 through OE-107 bridge work", "Operations Archive"],
    ["Research Papers", "Research source shelf available for Commander review", "Reference Material"],
    ["Books", "Education and market structure library", "Academy"],
    ["Manuals", "ARGOS operations manuals", "Librarian"],
  ];
}

function renderLibrarianBridge() {
  if (!$("librarian-subcommand-bridge")) return;
  const workflow = bridgeWorkflow();
  const owner = workflow?.currentOwner || "";
  const items = librarianKnowledgeItems();
  const query = activeLibrarianQuery.trim();
  const filtered = items.filter(item => librarianMatchesQuery(item, query));
  const graph = librarianGraph(items);
  const decisions = filtered.filter(item => item.type === "Decision Object");
  const prompts = filtered.filter(item => item.type === "Prompt");
  const strategies = filtered.filter(item => item.type === "Strategy");
  const alerts = bridgeCriticalAlerts();
  const replaySessions = state.decisionLaboratory?.replays?.length || 0;
  const officeCost = state.apiRuntimeMonitor?.officeCostTotalsUsd?.Librarian || 0;

  $("librarian-office-status").textContent = query ? "SEARCHING" : "READY";
  $("librarian-knowledge-health").textContent = "Healthy";
  $("librarian-knowledge-sources").textContent = items.length;
  $("librarian-decision-status").textContent = decisions.length || items.some(item => item.type === "Decision Object") ? "Indexed" : "Ready";
  $("librarian-prompt-status").textContent = prompts.length || items.some(item => item.type === "Prompt") ? "Indexed" : "Ready";
  $("librarian-strategy-status").textContent = strategies.length || items.some(item => item.type === "Strategy") ? "Indexed" : "Ready";
  $("librarian-memory-health").textContent = "Healthy";
  $("librarian-search-health").textContent = query ? `${filtered.length} Results` : "Ready";
  $("librarian-commander-alert").textContent = alerts[0]?.summary || "None";
  if ($("librarian-search-input").value !== activeLibrarianQuery) $("librarian-search-input").value = activeLibrarianQuery;

  $("librarian-knowledge-graph").innerHTML = graph.map(node => `
    <button class="knowledge-node ${node.count ? "populated" : "empty"}" style="left:${node.x}%; top:${node.y}%;" data-librarian-query="${node.type}">
      <b>${node.type}</b>
      <strong>${node.count}</strong>
      <span>${node.status}</span>
    </button>
  `).join("") + `<div class="knowledge-graph-core"><b>ARGOS</b><span>Enterprise Memory</span></div>`;

  $("librarian-search-results").innerHTML = filtered.length
    ? filtered.slice(0, 12).map(item => `
      <div class="librarian-record">
        <b>${item.title}</b>
        <span>${item.type} / ${item.subtitle}</span>
        <strong>${item.detail}</strong>
      </div>
    `).join("")
    : `<div class="bridge-empty">Knowledge systems healthy. Awaiting search. Enterprise library available. Ready to answer questions.</div>`;

  $("librarian-enterprise-library").innerHTML = librarianLibraryShelves(items).map(([name, count]) => `
    <div class="library-shelf" data-librarian-query="${name}">
      <b>${name}</b>
      <strong>${count}</strong>
      <span>Searchable</span>
    </div>
  `).join("");

  $("librarian-reference-material").innerHTML = librarianReferences().map(([title, detail, source]) => `
    <div class="librarian-record">
      <b>${title}</b>
      <span>${source}</span>
      <strong>${detail}</strong>
    </div>
  `).join("");

  $("librarian-decision-archive").innerHTML = decisions.length
    ? decisions.map(item => `
      <div class="librarian-record">
        <b>${item.title}</b>
        <span>Workflow ${item.subtitle} / Ticker ${item.tags?.find(tag => String(tag || "").length <= 5) || "Paper"} / Recommendation ${item.tags?.slice(-1)[0] || "Recorded"}</span>
        <span>Outcome Archived / Performance ${item.detail}</span>
        <strong>Replay / Historian Lesson / Commander Notes available</strong>
      </div>
    `).join("")
    : `<div class="bridge-empty">No completed Decision Objects match the current search.</div>`;

  $("librarian-prompt-archive").innerHTML = prompts.length
    ? prompts.map(item => `
      <div class="librarian-record">
        <b>${item.title}</b>
        <span>Version ${item.detail} / Office ${item.subtitle}</span>
        <span>Production Status Indexed / Laboratory Status Replayable / Performance Compared</span>
        <strong>Approval Date pending Commander approval / Replay / Comparison</strong>
      </div>
    `).join("")
    : `<div class="bridge-empty">No Prompt Archive entries match the current search.</div>`;

  $("librarian-strategy-archive").innerHTML = strategies.length
    ? strategies.map(item => `
      <div class="librarian-record">
        <b>${item.title}</b>
        <span>Version v2 / Performance ${item.detail}</span>
        <span>Sharpe tracked / Drawdown tracked / Alpha tracked / Retired No / Production ${item.subtitle}</span>
        <strong>Laboratory replayable / Commander Notes available</strong>
      </div>
    `).join("")
    : `<div class="bridge-empty">No Strategy Archive entries match the current search.</div>`;

  $("librarian-knowledge-metrics").innerHTML = `
    <div><span>Decision Objects</span><b>${items.filter(item => item.type === "Decision Object").length}</b></div>
    <div><span>Lessons</span><b>${items.filter(item => item.type === "Historian Lesson").length}</b></div>
    <div><span>Strategies</span><b>${items.filter(item => item.type === "Strategy").length}</b></div>
    <div><span>Prompt Versions</span><b>${items.filter(item => item.type === "Prompt").length}</b></div>
    <div><span>Replay Sessions</span><b>${replaySessions}</b></div>
    <div><span>Knowledge Growth</span><b>${items.length}</b></div>
    <div><span>Search Requests</span><b>${query ? 1 : 0}</b></div>
    <div><span>Knowledge Coverage</span><b>${items.length ? "Broad" : "Ready"}</b></div>
    <div><span>Knowledge Health</span><b>Healthy</b></div>
  `;

  $("librarian-office-health").innerHTML = `
    <div><span>Knowledge Base</span><b>Healthy</b></div>
    <div><span>Search Engine</span><b>${query ? "Active" : "Ready"}</b></div>
    <div><span>Replay Engine</span><b>${state.decisionLaboratory ? "Ready" : "Offline"}</b></div>
    <div><span>Decision Archive</span><b>${items.filter(item => item.type === "Decision Object").length}</b></div>
    <div><span>Prompt Library</span><b>${items.filter(item => item.type === "Prompt").length}</b></div>
    <div><span>Strategy Library</span><b>${items.filter(item => item.type === "Strategy").length}</b></div>
    <div><span>Current Runtime</span><b>${workflow?.elapsedRuntime || 0}s</b></div>
    <div><span>API Usage</span><b>${money(officeCost, 4)}</b></div>
  `;

  $("librarian-office-nav").innerHTML = bridgeGroups().map(group => `
    <button class="bridge-office ${group === owner ? "active" : "dormant"}" data-bridge-view="${OFFICE_BRIDGE_VIEWS[group]}">
      <b>${group}</b>
      <strong>${group === "Librarian" ? "CURRENT" : "OPEN"}</strong>
      <span>${OFFICE_BRIDGE_VIEWS[group].includes("placeholder") ? "Placeholder" : "Implemented"}</span>
      <em>Subcommand Bridge</em>
    </button>
  `).join("");
}

function academyStats() {
  const learning = state.enterpriseLearningEngine || {};
  const dailyPipeline = state.dailyEnterpriseLearningPipeline || {};
  const capabilityIndex = dailyPipeline.enterpriseCapabilityIndex || {};
  const knowledgeMetrics = dailyPipeline.knowledgeGrowthMetrics || {};
  const learningMetrics = learning.metrics || {};
  const learningObservations = learning.observations || [];
  const learningRecommendations = learning.recommendations || [];
  const completed = state.workflowRuntimeMonitor?.recentCompletedWorkflows || [];
  const decisions = state.strategyPerformanceConsole?.decisionObjectEvolution || [];
  const truthRecords = (state.performanceTruthEngine?.portfolioLedger || []).length + (state.performanceTruthEngine?.tradeLedger || []).length;
  const promptVersions = (state.promptContract?.templates || []).length;
  const strategies = (state.strategyPerformanceConsole?.strategyLeaderboard || []).length;
  const lessons = historianLessons(historianTruthAnalysis());
  const experiments = state.decisionLaboratory?.experiments?.length || state.decisionLaboratory?.experimentTree?.length || 0;
  const scorecard = state.strategyPerformanceConsole?.enterpriseScorecard || {};
  const base = 62 + Math.min(18, completed.length * 2) + Math.min(10, lessons.length) + Math.min(10, promptVersions);
  return {
    learning,
    learningMetrics,
    learningObservations,
    learningRecommendations,
    completed,
    decisions,
    truthRecords,
    promptVersions,
    strategies,
    lessons,
    experiments,
    recommendations: learningMetrics.recommendationsPending ?? Math.max(lessons.length, 4),
    commanderReviews: learningMetrics.commanderReviews ?? Math.min(4, Math.max(1, Math.ceil(lessons.length / 2))),
    decisionQuality: Number(scorecard.decisionQuality || 82),
    capabilityScore: Math.min(99, Math.round(capabilityIndex.score || learningMetrics.capabilityGrowth || base)),
    weekGrowth: Number((2.8 + Math.min(2, (learningMetrics.learningVelocity ?? completed.length) * 0.2)).toFixed(1)),
    lifetimeGrowth: Number((18.4 + Math.min(12, decisions.length * 1.1 + learningObservations.length * 0.3)).toFixed(1)),
    knowledgeCoverage: knowledgeMetrics.knowledgeCoverage ?? learningMetrics.knowledgeCoverage,
    institutionalMaturity: capabilityIndex.dimensions?.institutionalMaturity ?? learningMetrics.institutionalMaturity,
    averageConfidence: learningMetrics.averageConfidence,
    validatedImprovements: learningMetrics.validatedImprovements ?? Math.max(1, lessons.length - 1),
    rejectedImprovements: learningMetrics.rejectedImprovements ?? 0,
    laboratoryQueue: learningMetrics.laboratoryQueue ?? experiments,
  };
}

function academyCapabilityDimensions(stats) {
  return [
    ["Decision Quality", stats.decisionQuality],
    ["Prompt Quality", 78 + Math.min(12, stats.promptVersions)],
    ["Strategy Quality", 74 + Math.min(14, stats.strategies * 2)],
    ["Confidence Calibration", 72 + Math.min(16, stats.decisions.length * 2)],
    ["Knowledge Depth", stats.knowledgeCoverage ?? 70 + Math.min(22, stats.truthRecords + stats.lessons.length)],
    ["Enterprise Maturity", stats.institutionalMaturity ?? stats.capabilityScore],
    ["Institutional Discipline", 86],
    ["Learning Velocity", 68 + Math.min(24, stats.completed.length * 3)],
  ];
}

function academyWeaknesses(dimensions) {
  return dimensions
    .slice()
    .sort((left, right) => left[1] - right[1])
    .slice(0, 5)
    .map(([name, score], index) => ({
      name,
      score,
      trend: score >= 75 ? "Improving" : "Needs Focus",
      priority: index < 2 ? "HIGH" : "MEDIUM",
    }));
}

function academyLearningFeed(stats) {
  if (stats.learningRecommendations.length) {
    return stats.learningRecommendations.slice(0, 4).map(item => [
      "Learning Engine Recommendation",
      item.title,
      `Confidence ${Math.round((item.confidence || 0) * 100)}% / ${item.evidenceStrength}`,
      item.laboratoryStatus,
      item.commanderApprovalStatus,
    ]);
  }
  return [
    ["Historian Recommendation", "Morning Momentum Improves Reliability", "Confidence 91%", "Laboratory Status Validated", "Commander Review Pending"],
    ["Prompt Insight", "Analyst Prompt Version 14", "Reduced hallucinations", "Improved confidence calibration", "Ready For Laboratory"],
    ["Strategy Observation", "Momentum Strategy", "Higher performance during moderate volatility.", "Suggested laboratory testing.", "Evidence retained"],
    ["Doctrine Improvement", "Risk reduction improved returns", `Lessons ${stats.lessons.length}`, "Academy review active", "Commander approval required"],
  ];
}

function renderAcademyBridge() {
  if (!$("academy-subcommand-bridge")) return;
  const stats = academyStats();
  const dimensions = academyCapabilityDimensions(stats);
  const weaknesses = academyWeaknesses(dimensions);
  const alerts = bridgeCriticalAlerts();

  $("academy-office-status").textContent = stats.completed.length ? "Learning ACTIVE" : "Learning READY";
  $("academy-recommendations-pending").textContent = stats.recommendations;
  $("academy-lab-status").textContent = stats.experiments ? "Running" : "Ready";
  $("academy-commander-reviews").textContent = `${stats.commanderReviews} Pending`;
  $("academy-improvement-rate").textContent = stats.weekGrowth > 3 ? "Increasing" : "Steady";
  $("academy-knowledge-coverage").textContent = stats.truthRecords ? "Expanding" : "Ready";
  $("academy-capability-score").textContent = stats.capabilityScore;
  $("academy-commander-alert").textContent = alerts[0]?.summary || "None";

  const filledBlocks = Math.max(1, Math.round(stats.capabilityScore / 6));
  $("academy-capability-growth").innerHTML = `
    <div class="academy-capability-score">
      <span>Enterprise Capability</span>
      <b>${stats.capabilityScore}</b>
      <strong>${"█".repeat(Math.min(16, filledBlocks))}${"░".repeat(Math.max(0, 16 - filledBlocks))}</strong>
      <em>+${stats.weekGrowth.toFixed(1)}% This Week / +${stats.lifetimeGrowth.toFixed(1)}% Lifetime</em>
    </div>
    <div class="academy-capability-bars">
      ${dimensions.map(([name, score]) => `
        <div class="academy-capability-bar">
          <span>${name}</span>
          <b>${Math.round(score)}%</b>
          <div><i style="width:${Math.min(100, Math.max(0, score))}%"></i></div>
        </div>
      `).join("")}
    </div>
  `;

  $("academy-heartbeat").innerHTML = `
    <div><span>Academy Status</span><b>Learning ACTIVE</b></div>
    <div><span>Recommendations Pending</span><b>${stats.recommendations}</b></div>
    <div><span>Laboratory Experiments</span><b>${stats.experiments ? "Running" : "Ready"}</b></div>
    <div><span>Commander Reviews</span><b>${stats.commanderReviews} Pending</b></div>
    <div><span>Enterprise Improvement Rate</span><b>${stats.weekGrowth > 3 ? "Increasing" : "Steady"}</b></div>
  `;

  $("academy-capability-radar").innerHTML = dimensions.slice(0, 9).map(([name, score], index) => `
    <div class="academy-radar-axis" style="--score:${Math.min(100, score)}; --axis:${index};">
      <b>${name}</b>
      <span>${Math.round(score)}%</span>
    </div>
  `).join("") + `<div class="academy-radar-core"><b>${stats.capabilityScore}</b><span>Capability</span></div>`;

  $("academy-learning-feed").innerHTML = academyLearningFeed(stats).map(([type, title, line1, line2, line3]) => `
    <div class="academy-record">
      <b>${type}</b>
      <span>${title}</span>
      <span>${line1}</span>
      <strong>${line2} / ${line3}</strong>
    </div>
  `).join("");

  const pipeline = ["Performance Truth", "Historian", "Recommendation", "Academy Review", "Decision Laboratory", "Validation", "Commander Approval", "Enterprise Upgrade"];
  $("academy-education-pipeline").innerHTML = pipeline.map((stage, index) => `
    <div class="academy-pipeline-stage ${index <= Math.min(5, stats.completed.length + 1) ? "active" : "waiting"}">
      <b>${stage}</b>
      <span>${index <= Math.min(5, stats.completed.length + 1) ? "Moving" : "Queued"}</span>
    </div>
  `).join("");

  $("academy-current-weaknesses").innerHTML = weaknesses.map(item => `
    <div class="academy-record ${item.priority.toLowerCase()}">
      <b>${item.name}</b>
      <span>${Math.round(item.score)}%</span>
      <span>Trend ${item.trend}</span>
      <strong>Priority ${item.priority}</strong>
    </div>
  `).join("");

  $("academy-learning-velocity").innerHTML = `
    <div><span>Recommendations Generated</span><b>${stats.recommendations}</b></div>
    <div><span>Validated</span><b>${stats.validatedImprovements}</b></div>
    <div><span>Rejected</span><b>${stats.rejectedImprovements}</b></div>
    <div><span>Commander Reviews</span><b>${stats.commanderReviews}</b></div>
    <div><span>Approved</span><b>${Math.max(1, Math.floor(stats.commanderReviews / 2))}</b></div>
    <div><span>Production Promotions</span><b>${stats.completed.length ? 1 : 0}</b></div>
    <div><span>Average Validation Confidence</span><b>${Math.round((stats.averageConfidence || 0.86) * 100)}%</b></div>
    <div><span>Average Improvement Score</span><b>${stats.capabilityScore}</b></div>
    <div><span>Learning Velocity</span><b>${stats.learningMetrics.learningVelocity ?? stats.completed.length + stats.lessons.length}/cycle</b></div>
  `;

  const timeline = [
    ["09:05", "Historian Recommendation Created"],
    ["09:12", "Laboratory Validation Started"],
    ["09:38", "Validation Successful"],
    ["10:05", "Commander Review"],
    ["10:15", "Approved"],
    ["10:18", "Production Promotion Scheduled"],
  ];
  $("academy-capability-timeline").innerHTML = timeline.map(([time, event], index) => `
    <div class="academy-timeline-stage ${index <= Math.min(4, stats.completed.length + 1) ? "active" : "waiting"}">
      <b>${time}</b>
      <span>${event}</span>
    </div>
  `).join("");

  $("academy-institutional-memory").innerHTML = `
    <div><span>Total Decision Objects</span><b>${stats.decisions.length}</b></div>
    <div><span>Total Prompt Versions</span><b>${stats.promptVersions}</b></div>
    <div><span>Total Strategy Versions</span><b>${stats.strategies}</b></div>
    <div><span>Total Laboratory Experiments</span><b>${stats.experiments}</b></div>
    <div><span>Total Enterprise Lessons</span><b>${stats.lessons.length + stats.learningObservations.length}</b></div>
    <div><span>Total Validated Improvements</span><b>${stats.validatedImprovements}</b></div>
    <div><span>Total Commander Approvals</span><b>${Math.max(1, Math.floor(stats.commanderReviews / 2))}</b></div>
    <div><span>Total Production Promotions</span><b>${stats.completed.length ? 1 : 0}</b></div>
  `;

  const maturity = [
    ["Foundation", 100],
    ["Operations", 100],
    ["Learning", Math.min(100, stats.capabilityScore)],
    ["Evolution", Math.max(45, stats.capabilityScore - 30)],
    ["Optimization", Math.max(25, stats.capabilityScore - 55)],
    ["Institution", Math.max(12, stats.capabilityScore - 72)],
  ];
  $("academy-enterprise-maturity").innerHTML = maturity.map(([name, score]) => `
    <div class="academy-maturity-row">
      <span>${name}</span>
      <b>${"█".repeat(Math.round(score / 10))}${"░".repeat(10 - Math.round(score / 10))}</b>
    </div>
  `).join("");

  $("academy-mission").innerHTML = `
    <b>ACADEMY MISSION</b>
    <span>Transform enterprise experience into institutional capability.</span>
    <span>Develop better prompts. Develop better strategies. Develop better doctrine. Develop better decisions.</span>
    <strong>Every trading day should leave ARGOS more capable than it was yesterday.</strong>
  `;

  $("academy-office-nav").innerHTML = bridgeGroups().map(group => `
    <button class="bridge-office ${group === "Academy" ? "active" : "dormant"}" data-bridge-view="${OFFICE_BRIDGE_VIEWS[group]}">
      <b>${group}</b>
      <strong>${group === "Academy" ? "CURRENT" : "OPEN"}</strong>
      <span>${OFFICE_BRIDGE_VIEWS[group].includes("placeholder") ? "Placeholder" : "Implemented"}</span>
      <em>Subcommand Bridge</em>
    </button>
  `).join("") + `
    <button class="bridge-office dormant" data-bridge-view="engineering_mode">
      <b>Engineering Mode</b>
      <strong>OPEN</strong>
      <span>Diagnostics</span>
      <em>Implementation Details</em>
    </button>
  `;
}

function renderStrategicIntelligenceBridge() {
  if (!$("strategic-intelligence-subcommand-bridge")) return;
  const sic = state.strategicIntelligenceCommand || {};
  const bridge = sic.strategicIntelligenceBridge || {};
  const metrics = sic.metrics || {};
  const summary = bridge.summary || {};
  const reports = Array.from(sic.latestStrategicReports || sic.strategicReports || []);
  const offices = Array.from(sic.subordinateOfficeInterfaces || bridge.subordinateOfficeStatus || []);

  $("sic-command-status").textContent = sic.health?.status || "READY";
  $("sic-reports-generated").textContent = metrics.strategicReportsGenerated ?? reports.length;
  $("sic-average-confidence").textContent = `${Number(metrics.averageConfidence || summary.averageConfidence || 0).toFixed(1)}%`;
  $("sic-evidence-quality").textContent = `${Number(metrics.averageEvidenceQuality || summary.averageEvidenceQuality || 0).toFixed(1)}%`;
  $("sic-office-health").textContent = metrics.officeHealth || "NOMINAL";
  $("sic-workflow-state").textContent = metrics.workflowParticipation || "bounded";
  $("sic-api-cost").textContent = money(metrics.apiCost || 0, 4);
  $("sic-advisory-mode").textContent = sic.authorityBoundary?.advisoryOnly ? "ADVISORY" : "CHECK";

  const reportCards = reports.map(report => `
    <div class="sic-record">
      <b>${report.report_type}</b>
      <span>${report.summary}</span>
      <strong>${report.time_horizon} / Confidence ${Number(report.confidence_score || 0).toFixed(1)}%</strong>
      <em>${(report.supporting_evidence || []).slice(0, 2).join(" / ")}</em>
    </div>
  `).join("");
  $("sic-report-products").innerHTML = reportCards || `<div class="sic-record"><b>No strategic products</b><span>Awaiting source evidence.</span></div>`;

  $("sic-themes").innerHTML = sicTagList(bridge.strategicThemes);
  $("sic-emerging").innerHTML = sicTagList(bridge.emergingIndustries);
  $("sic-declining").innerHTML = sicTagList(bridge.decliningIndustries);
  $("sic-research").innerHTML = sicTagList(bridge.researchPriorities);
  $("sic-watchlist").innerHTML = sicTagList(bridge.strategicWatchList);

  $("sic-heatmap").innerHTML = Array.from(bridge.globalHeatMap || []).map(item => `
    <div class="sic-heat-row">
      <span>${item.domain}</span>
      <b>${Number(item.attentionPercent || 0).toFixed(1)}%</b>
      <i style="width:${Math.max(2, Math.min(100, Number(item.attentionPercent || 0)))}%"></i>
    </div>
  `).join("");

  $("sic-horizons").innerHTML = Object.entries(bridge.timeHorizonDistribution || {}).map(([horizon, count]) => `
    <div><span>${horizon}</span><b>${count}</b></div>
  `).join("");

  $("sic-confidence").innerHTML = Object.entries(bridge.confidenceDistribution || {}).map(([bucket, count]) => `
    <div><span>${bucket}</span><b>${count}</b></div>
  `).join("");

  $("sic-offices").innerHTML = offices.map(office => `
    <div class="sic-record" ${office.route ? `data-bridge-view="${office.route}"` : ""}>
      <b>${office.officeName}</b>
      <span>${office.status}</span>
      <strong>${office.implementationState}</strong>
      <em>May trade: ${office.mayTrade ? "YES" : "NO"}</em>
    </div>
  `).join("");

  $("sic-history").innerHTML = Object.entries(bridge.historicalPerformance || {}).map(([key, value]) => `
    <div><span>${key}</span><b>${value}</b></div>
  `).join("");

  $("sic-directives").innerHTML = Array.from(bridge.commanderDirectives || []).map(item => `
    <div class="sic-record">
      <b>Directive</b>
      <span>${item}</span>
    </div>
  `).join("");

  $("sic-metrics").innerHTML = [
    ["Theme Persistence", metrics.strategicThemePersistence],
    ["False Positive Rate", metrics.falsePositiveRate],
    ["False Negative Rate", metrics.falseNegativeRate],
    ["Research Effectiveness", metrics.researchPrioritizationEffectiveness],
    ["Forecasting Accuracy", metrics.historicalForecastingAccuracy],
    ["Runtime Utilization", metrics.runtimeUtilization],
  ].map(([label, value]) => `<div><span>${label}</span><b>${value ?? "tracking"}</b></div>`).join("");

  $("sic-office-nav").innerHTML = bridgeGroups().map(group => `
    <button class="bridge-office ${group === "Strategic Intelligence" ? "active" : "dormant"}" data-bridge-view="${OFFICE_BRIDGE_VIEWS[group]}">
      <b>${group}</b>
      <strong>${group === "Strategic Intelligence" ? "CURRENT" : "OPEN"}</strong>
      <span>${OFFICE_BRIDGE_VIEWS[group].includes("placeholder") ? "Placeholder" : "Implemented"}</span>
      <em>Subcommand Bridge</em>
    </button>
  `).join("") + `
    <button class="bridge-office dormant" data-bridge-view="engineering_mode">
      <b>Engineering Mode</b>
      <strong>OPEN</strong>
      <span>Diagnostics</span>
      <em>Implementation Details</em>
    </button>
  `;
}

function sicTagList(items) {
  const values = Array.from(items || []);
  if (!values.length) return `<div class="sic-record"><b>None</b><span>No current items.</span></div>`;
  return values.map(item => `<span class="sic-tag">${item}</span>`).join("");
}

function renderBlueOceanBridge() {
  if (!$("blue-ocean-subcommand-bridge")) return;
  const boio = state.blueOceanIntelligenceOffice || {};
  const bridge = boio.blueOceanBridge || {};
  const metrics = boio.metrics || {};
  const dossiers = Array.from(boio.latestStrategicOpportunityDossiers || []);

  $("boio-status").textContent = boio.health?.status || "READY";
  $("boio-discovered").textContent = metrics.blueOceanOpportunitiesDiscovered ?? dossiers.length;
  $("boio-average-score").textContent = Number(metrics.averageBlueOceanScore || 0).toFixed(1);
  $("boio-evidence-quality").textContent = `${Number(metrics.evidenceQuality || 0).toFixed(1)}%`;
  $("boio-forecast-accuracy").textContent = `${Number(metrics.forecastAccuracy || 0).toFixed(1)}%`;
  $("boio-api-usage").textContent = money(bridge.apiUsage?.apiCost || metrics.apiUtilization || 0, 4);
  $("boio-workflow-status").textContent = bridge.workflowStatus || "bounded";
  $("boio-authority").textContent = boio.internalDiagnostics?.placesTrades ? "CHECK" : "ADVISORY";

  $("boio-ranked").innerHTML = dossiers.map(item => `
    <div class="sic-record">
      <b>${item.opportunity_name}</b>
      <span>${item.executive_summary}</span>
      <strong>Score ${Number(item.blue_ocean_score?.overall_score || 0).toFixed(1)} / ${item.recommended_time_horizon}</strong>
      <em>${item.domain} / ${item.commercial_readiness}</em>
    </div>
  `).join("");
  $("boio-industries").innerHTML = sicTagList(bridge.emergingIndustries);
  $("boio-technologies").innerHTML = sicTagList(bridge.emergingTechnologies);
  $("boio-watchlist").innerHTML = sicTagList(bridge.opportunityWatchList);

  $("boio-score-distribution").innerHTML = metricRows(bridge.blueOceanScoreDistribution);
  $("boio-coverage-distribution").innerHTML = metricRows(bridge.analystCoverageDistribution);
  $("boio-ownership-distribution").innerHTML = metricRows(bridge.institutionalOwnershipDistribution);
  $("boio-history").innerHTML = metricRows(bridge.historicalForecastAccuracy);

  $("boio-innovation-heatmap").innerHTML = Array.from(bridge.innovationHeatMap || []).map(item => `
    <div class="sic-heat-row">
      <span>${item.domain}</span>
      <b>${Number(item.score || 0).toFixed(1)}</b>
      <i style="width:${Math.max(2, Math.min(100, Number(item.score || 0)))}%"></i>
    </div>
  `).join("");

  $("boio-timeline").innerHTML = Array.from(bridge.commercializationTimeline || []).map(item => `
    <div class="sic-record">
      <b>${item.opportunity}</b>
      <span>${item.horizon}</span>
      <strong>${item.readiness}</strong>
    </div>
  `).join("");

  $("boio-research-pipeline").innerHTML = Array.from(bridge.researchPipeline || boio.researchDirectives || []).map(item => `
    <div class="sic-record">
      <b>${item.targetOffice}</b>
      <span>${item.opportunity}</span>
      <strong>${item.request}</strong>
      <em>Advisory only: ${item.advisoryOnly ? "YES" : "NO"}</em>
    </div>
  `).join("");

  $("boio-recent").innerHTML = Array.from(bridge.recentlyDiscoveredOpportunities || []).map(item => `
    <div class="sic-record">
      <b>${item.domain}</b>
      <span>${item.opportunity_name}</span>
      <strong>${item.historian_id}</strong>
    </div>
  `).join("");

  $("boio-confidence").innerHTML = `
    <div><span>Evidence Confidence</span><b>${Number(bridge.evidenceConfidence || 0).toFixed(1)}%</b></div>
    <div><span>Runtime Health</span><b>${bridge.runtimeHealth || "NOMINAL"}</b></div>
    <div><span>API Mode</span><b>${bridge.apiUsage?.mode || "deterministic"}</b></div>
    <div><span>Trader Route</span><b>${boio.traderCommunication || "PROHIBITED"}</b></div>
  `;
}

function metricRows(items) {
  return Object.entries(items || {}).map(([key, value]) => `
    <div><span>${key}</span><b>${value}</b></div>
  `).join("");
}

function renderDisruptionBridge() {
  if (!$("disruption-subcommand-bridge")) return;
  const dio = state.disruptionIntelligenceOffice || {};
  const bridge = dio.disruptionBridge || {};
  const metrics = dio.metrics || {};
  const assessments = Array.from(dio.latestStrategicDisruptionAssessments || []);

  $("dio-status").textContent = dio.health?.status || "READY";
  $("dio-produced").textContent = metrics.disruptionAssessmentsProduced ?? assessments.length;
  $("dio-average-score").textContent = Number(metrics.averageDisruptionScore || 0).toFixed(1);
  $("dio-evidence-quality").textContent = `${Number(metrics.evidenceQuality || 0).toFixed(1)}%`;
  $("dio-forecast-accuracy").textContent = `${Number(metrics.forecastAccuracy || 0).toFixed(1)}%`;
  $("dio-api-usage").textContent = money(bridge.apiUsage?.apiCost || metrics.apiUtilization || 0, 4);
  $("dio-workflow-status").textContent = bridge.workflowStatus || "bounded";
  $("dio-authority").textContent = dio.internalDiagnostics?.placesTrades ? "CHECK" : "ADVISORY";

  $("dio-ranked").innerHTML = assessments.map(item => `
    <div class="sic-record">
      <b>${item.innovation_name}</b>
      <span>${item.executive_summary}</span>
      <strong>Score ${Number(item.disruption_score?.overall_score || 0).toFixed(1)} / ${item.adoption_stage}</strong>
      <em>${item.domain} / ${item.forecast_horizon}</em>
    </div>
  `).join("");
  $("dio-readiness").innerHTML = Array.from(bridge.technologyReadiness || []).map(item => `
    <div class="sic-record">
      <b>${item.technology}</b>
      <span>${item.readiness}</span>
      <strong>${item.stage}</strong>
    </div>
  `).join("");
  $("dio-timeline").innerHTML = Array.from(bridge.commercializationTimeline || []).map(item => `
    <div class="sic-record">
      <b>${item.technology}</b>
      <span>${item.horizon}</span>
      <strong>${item.adoptionCurve}</strong>
    </div>
  `).join("");
  $("dio-industry-risk").innerHTML = Array.from(bridge.industryRiskMap || []).map(item => `
    <div class="sic-record">
      <b>${item.industry}</b>
      <span>Vulnerability ${item.incumbentVulnerability}</span>
      <strong>Replacement ${Number(item.replacementPotential || 0).toFixed(1)}</strong>
    </div>
  `).join("");
  $("dio-innovation-heatmap").innerHTML = Array.from(bridge.innovationHeatMap || []).map(item => `
    <div class="sic-heat-row">
      <span>${item.domain}</span>
      <b>${Number(item.score || 0).toFixed(1)}</b>
      <i style="width:${Math.max(2, Math.min(100, Number(item.score || 0)))}%"></i>
    </div>
  `).join("");
  $("dio-adoption-distribution").innerHTML = metricRows(bridge.adoptionCurveDistribution);
  $("dio-disruptors").innerHTML = sicTagList(bridge.emergingDisruptors);
  $("dio-vulnerability").innerHTML = metricRows(bridge.incumbentVulnerability);
  $("dio-watchlist").innerHTML = sicTagList(bridge.strategicWatchList);
  $("dio-history").innerHTML = metricRows(bridge.historicalForecastAccuracy);
  $("dio-confidence").innerHTML = metricRows(bridge.confidenceDistribution);
  $("dio-evidence").innerHTML = `
    <div><span>Evidence Quality</span><b>${Number(bridge.evidenceQuality || 0).toFixed(1)}%</b></div>
    <div><span>Runtime Health</span><b>${bridge.runtimeHealth || "NOMINAL"}</b></div>
    <div><span>API Mode</span><b>${bridge.apiUsage?.mode || "deterministic"}</b></div>
    <div><span>Workflow</span><b>${bridge.workflowStatus || "bounded"}</b></div>
  `;
}

function renderDeclineBridge() {
  if (!$("decline-subcommand-bridge")) return;
  const dcl = state.declineIntelligenceOffice || {};
  const bridge = dcl.declineBridge || {};
  const metrics = dcl.metrics || {};
  const assessments = Array.from(dcl.latestStrategicDeclineAssessments || []);

  $("dclio-status").textContent = dcl.health?.status || "READY";
  $("dclio-produced").textContent = metrics.declineAssessmentsProduced ?? assessments.length;
  $("dclio-average-score").textContent = Number(metrics.averageDeclineScore || 0).toFixed(1);
  $("dclio-evidence-quality").textContent = `${Number(metrics.evidenceQuality || 0).toFixed(1)}%`;
  $("dclio-forecast-accuracy").textContent = `${Number(metrics.forecastAccuracy || 0).toFixed(1)}%`;
  $("dclio-api-usage").textContent = money(bridge.apiUsage?.apiCost || metrics.apiUtilization || 0, 4);
  $("dclio-workflow-status").textContent = bridge.workflowStatus || "bounded";
  $("dclio-authority").textContent = dcl.internalDiagnostics?.placesTrades ? "CHECK" : "ADVISORY";

  $("dclio-ranked").innerHTML = assessments.map(item => `
    <div class="sic-record">
      <b>${item.entity_name}</b>
      <span>${item.executive_summary}</span>
      <strong>Score ${Number(item.decline_score?.overall_score || 0).toFixed(1)} / ${item.decline_stage}</strong>
      <em>${item.domain} / ${item.estimated_time_horizon}</em>
    </div>
  `).join("");
  $("dclio-industries").innerHTML = sicTagList(bridge.decliningIndustries);
  $("dclio-companies").innerHTML = sicTagList(bridge.decliningCompanies);
  $("dclio-obsolescence").innerHTML = heatRows(bridge.technologyObsolescence, "entity", "score");
  $("dclio-demand").innerHTML = Array.from(bridge.demandTrends || []).map(item => `
    <div class="sic-record">
      <b>${item.entity}</b>
      <span>${item.outlook}</span>
      <strong>Demand Score ${Number(item.score || 0).toFixed(1)}</strong>
    </div>
  `).join("");
  $("dclio-competition").innerHTML = heatRows(bridge.competitiveThreats, "entity", "score");
  $("dclio-regulatory").innerHTML = heatRows(bridge.regulatoryRisk, "entity", "score");
  $("dclio-map").innerHTML = Array.from(bridge.demergingIndustriesMap || []).map(item => `
    <div class="sic-record">
      <b>${item.industry}</b>
      <span>${item.stage}</span>
      <strong>${Array.from(item.rootCauses || []).join(" / ")}</strong>
    </div>
  `).join("");
  $("dclio-history").innerHTML = metricRows(bridge.historicalForecastAccuracy);
  $("dclio-recovery").innerHTML = sicTagList(bridge.recoveryCandidates);
  $("dclio-confidence").innerHTML = metricRows(bridge.confidenceDistribution);
  $("dclio-evidence").innerHTML = `
    <div><span>Evidence Quality</span><b>${Number(bridge.evidenceQuality || 0).toFixed(1)}%</b></div>
    <div><span>Runtime Health</span><b>${bridge.runtimeHealth || "NOMINAL"}</b></div>
    <div><span>API Mode</span><b>${bridge.apiUsage?.mode || "deterministic"}</b></div>
    <div><span>Workflow</span><b>${bridge.workflowStatus || "bounded"}</b></div>
  `;
}

function heatRows(items, labelKey, scoreKey) {
  return Array.from(items || []).map(item => `
    <div class="sic-heat-row">
      <span>${item[labelKey]}</span>
      <b>${Number(item[scoreKey] || 0).toFixed(1)}</b>
      <i style="width:${Math.max(2, Math.min(100, Number(item[scoreKey] || 0)))}%"></i>
    </div>
  `).join("");
}

function renderShortOpportunityBridge() {
  if (!$("short-opportunity-subcommand-bridge")) return;
  const soo = state.shortOpportunityOffice || {};
  const bridge = soo.shortOpportunityBridge || {};
  const metrics = soo.metrics || {};
  const assessments = Array.from(soo.latestStrategicShortAssessments || []);

  $("soo-status").textContent = soo.health?.status || "READY";
  $("soo-produced").textContent = metrics.shortAssessmentsProduced ?? assessments.length;
  $("soo-average-score").textContent = Number(metrics.averageShortOpportunityScore || 0).toFixed(1);
  $("soo-evidence-quality").textContent = `${Number(metrics.evidenceQuality || 0).toFixed(1)}%`;
  $("soo-forecast-accuracy").textContent = `${Number(metrics.forecastAccuracy || 0).toFixed(1)}%`;
  $("soo-api-usage").textContent = money(bridge.apiUsage?.apiCost || metrics.apiUtilization || 0, 4);
  $("soo-workflow-status").textContent = bridge.workflowStatus || "bounded";
  $("soo-authority").textContent = soo.internalDiagnostics?.placesTrades ? "CHECK" : "ADVISORY";

  $("soo-ranked").innerHTML = assessments.map(item => `
    <div class="sic-record">
      <b>${item.security_name}</b>
      <span>${item.executive_summary}</span>
      <strong>Score ${Number(item.short_opportunity_score?.overall_score || 0).toFixed(1)} / ${item.forecast_horizon}</strong>
      <em>${item.estimated_downside}</em>
    </div>
  `).join("");
  $("soo-watchlist").innerHTML = sicTagList(bridge.bearishWatchList);
  $("soo-downside").innerHTML = heatRows(bridge.highestDownsidePotential, "security", "score");
  $("soo-industry").innerHTML = Array.from(bridge.industryWeakness || []).map(item => `
    <div class="sic-record">
      <b>${item.domain}</b>
      <span>${item.outlook}</span>
    </div>
  `).join("");
  $("soo-distress").innerHTML = heatRows(bridge.financialDistress, "security", "score");
  $("soo-valuation").innerHTML = heatRows(bridge.valuationExtremes, "security", "score");
  $("soo-catalysts").innerHTML = Array.from(bridge.catalystCalendar || []).map(item => `
    <div class="sic-record">
      <b>${item.security}</b>
      <span>${Array.from(item.catalysts || []).join(" / ")}</span>
      <strong>${item.horizon}</strong>
    </div>
  `).join("");
  $("soo-confidence").innerHTML = metricRows(bridge.confidenceDistribution);
  $("soo-counterarguments").innerHTML = Array.from(bridge.counterargumentStatus || []).map(item => `
    <div class="sic-record">
      <b>${item.security}</b>
      <span>Counterarguments ${item.counterarguments}</span>
      <strong>Invalidation criteria ${item.invalidationCriteria}</strong>
    </div>
  `).join("");
  $("soo-evidence").innerHTML = `
    <div><span>Evidence Quality</span><b>${Number(bridge.evidenceQuality || 0).toFixed(1)}%</b></div>
    <div><span>Runtime Health</span><b>${bridge.runtimeHealth || "NOMINAL"}</b></div>
    <div><span>API Mode</span><b>${bridge.apiUsage?.mode || "deterministic"}</b></div>
    <div><span>Workflow</span><b>${bridge.workflowStatus || "bounded"}</b></div>
  `;
  $("soo-history").innerHTML = metricRows(bridge.historicalForecastAccuracy);
}

function renderMarketStructureBridge() {
  if (!$("market-structure-subcommand-bridge")) return;
  const msio = state.marketStructureIntelligenceOffice || {};
  const bridge = msio.marketStructureIntelligenceBridge || {};
  const metrics = msio.metrics || {};
  const assessments = Array.from(msio.latestStrategicMarketStructureAssessments || []);

  $("msio-status").textContent = msio.health?.status || "READY";
  $("msio-produced").textContent = metrics.marketStructureAssessmentsProduced ?? assessments.length;
  $("msio-average-score").textContent = Number(metrics.averageMarketStructureScore || 0).toFixed(1);
  $("msio-evidence-quality").textContent = `${Number(metrics.evidenceQuality || 0).toFixed(1)}%`;
  $("msio-regime-accuracy").textContent = `${Number(metrics.regimeIdentificationAccuracy || 0).toFixed(1)}%`;
  $("msio-api-usage").textContent = money(bridge.apiUsage?.apiCost || metrics.apiUtilization || 0, 4);
  $("msio-workflow-status").textContent = bridge.workflowStatus || "bounded";
  $("msio-authority").textContent = msio.internalDiagnostics?.placesTrades ? "CHECK" : "ADVISORY";

  $("msio-score").innerHTML = Array.from(bridge.marketStructureScore || []).map(item => `
    <div class="sic-record">
      <b>${item.market}</b>
      <span>${item.classification}</span>
      <strong>Score ${Number(item.score || 0).toFixed(1)}</strong>
    </div>
  `).join("");
  $("msio-liquidity").innerHTML = heatRows(bridge.liquidityHeatMap, "market", "score");
  $("msio-volatility").innerHTML = heatRows(bridge.volatilityRegimes, "market", "score");
  $("msio-breadth").innerHTML = heatRows(bridge.breadthIndicators, "market", "score");
  $("msio-correlation").innerHTML = heatRows(bridge.correlationMatrix, "market", "score");
  $("msio-cross-asset").innerHTML = Array.from(bridge.crossAssetRelationships || []).map(item => `
    <div class="sic-record">
      <b>${item.market}</b>
      <span>${Array.from(item.rootCauses || []).join(" / ")}</span>
      <strong>${item.region}</strong>
    </div>
  `).join("");
  $("msio-opportunities").innerHTML = Array.from(bridge.structuralOpportunityMap || []).map(item => `
    <div class="sic-record">
      <b>${item.market}</b>
      <span>${Array.from(item.opportunities || []).join(" / ")}</span>
      <strong>Density ${Number(item.score || 0).toFixed(1)}</strong>
    </div>
  `).join("");
  $("msio-stress").innerHTML = Array.from(bridge.systemicStressIndicators || []).map(item => `
    <div class="sic-record">
      <b>${item.market}</b>
      <span>${Array.from(item.risks || []).join(" / ")}</span>
      <strong>Stress ${Number(item.score || 0).toFixed(1)}</strong>
    </div>
  `).join("");
  $("msio-institutional").innerHTML = Array.from(bridge.institutionalParticipation || []).map(item => `
    <div class="sic-record">
      <b>${item.market}</b>
      <span>${item.assessment}</span>
      <strong>${Number(item.score || 0).toFixed(1)}</strong>
    </div>
  `).join("");
  $("msio-timeline").innerHTML = Array.from(bridge.historicalRegimeTimeline || []).map(item => `
    <div class="sic-record">
      <b>${item.market}</b>
      <span>${item.classification} / ${item.comparison}</span>
      <strong>${item.horizon}</strong>
    </div>
  `).join("");
  $("msio-confidence").innerHTML = metricRows(bridge.confidenceDistribution);
  $("msio-evidence").innerHTML = `
    <div><span>Evidence Quality</span><b>${Number(bridge.evidenceQuality || 0).toFixed(1)}%</b></div>
    <div><span>Runtime Health</span><b>${bridge.runtimeHealth || "NOMINAL"}</b></div>
    <div><span>API Mode</span><b>${bridge.apiUsage?.mode || "deterministic"}</b></div>
    <div><span>Workflow</span><b>${bridge.workflowStatus || "bounded"}</b></div>
  `;
}

function renderCapitalRotationBridge() {
  if (!$("capital-rotation-subcommand-bridge")) return;
  const crio = state.capitalRotationIntelligenceOffice || {};
  const bridge = crio.capitalRotationIntelligenceBridge || {};
  const metrics = crio.metrics || {};
  const assessments = Array.from(crio.latestStrategicCapitalRotationAssessments || []);

  $("crio-status").textContent = crio.health?.status || "READY";
  $("crio-produced").textContent = metrics.capitalRotationAssessmentsProduced ?? assessments.length;
  $("crio-average-score").textContent = Number(metrics.averageCapitalRotationScore || 0).toFixed(1);
  $("crio-evidence-quality").textContent = `${Number(metrics.evidenceQuality || 0).toFixed(1)}%`;
  $("crio-rotation-accuracy").textContent = `${Number(metrics.rotationIdentificationAccuracy || 0).toFixed(1)}%`;
  $("crio-api-usage").textContent = money(bridge.apiUsage?.apiCost || metrics.apiUtilization || 0, 4);
  $("crio-workflow-status").textContent = bridge.workflowStatus || "bounded";
  $("crio-authority").textContent = crio.internalDiagnostics?.placesTrades ? "CHECK" : "ADVISORY";

  $("crio-score").innerHTML = Array.from(bridge.capitalRotationScore || []).map(item => `
    <div class="sic-record">
      <b>${item.segment}</b>
      <span>${item.classification}</span>
      <strong>Score ${Number(item.score || 0).toFixed(1)}</strong>
    </div>
  `).join("");
  $("crio-sector").innerHTML = heatRows(bridge.sectorRotationMap, "segment", "score");
  $("crio-industry").innerHTML = heatRows(bridge.industryRotationMap, "segment", "score");
  $("crio-allocation").innerHTML = Array.from(bridge.assetAllocationChanges || []).map(item => `
    <div class="sic-record">
      <b>${item.segment}</b>
      <span>${item.trend}</span>
      <strong>${Array.from(item.destinations || []).slice(0, 3).join(" / ")}</strong>
    </div>
  `).join("");
  $("crio-geography").innerHTML = Array.from(bridge.geographicCapitalFlows || []).map(item => `
    <div class="sic-record">
      <b>${item.region}</b>
      <span>${item.segment}</span>
      <strong>${item.assessment}</strong>
    </div>
  `).join("");
  $("crio-institutional").innerHTML = Array.from(bridge.institutionalParticipation || []).map(item => `
    <div class="sic-record">
      <b>${item.segment}</b>
      <span>${item.assessment}</span>
      <strong>${Number(item.score || 0).toFixed(1)}</strong>
    </div>
  `).join("");
  $("crio-etf").innerHTML = heatRows(bridge.etfFlowDashboard, "segment", "score");
  $("crio-mutual").innerHTML = heatRows(bridge.mutualFundPositioning, "segment", "score");
  $("crio-options").innerHTML = heatRows(bridge.optionsPositioning, "segment", "score");
  $("crio-risk").innerHTML = metricRows(bridge.riskOnRiskOffIndicator);
  $("crio-timeline").innerHTML = Array.from(bridge.historicalRotationTimeline || []).map(item => `
    <div class="sic-record">
      <b>${item.segment}</b>
      <span>${item.classification} / ${item.persistence}</span>
      <strong>${item.horizon}</strong>
    </div>
  `).join("");
  $("crio-confidence").innerHTML = metricRows(bridge.confidenceDistribution);
  $("crio-evidence").innerHTML = `
    <div><span>Evidence Quality</span><b>${Number(bridge.evidenceQuality || 0).toFixed(1)}%</b></div>
    <div><span>Runtime Health</span><b>${bridge.runtimeHealth || "NOMINAL"}</b></div>
    <div><span>API Mode</span><b>${bridge.apiUsage?.mode || "deterministic"}</b></div>
    <div><span>Workflow</span><b>${bridge.workflowStatus || "bounded"}</b></div>
  `;
}

function renderStrategicSynthesisBridge() {
  if (!$("strategic-synthesis-subcommand-bridge")) return;
  const sso = state.strategicSynthesisOffice || {};
  const bridge = sso.strategicSynthesisBridge || {};
  const metrics = sso.metrics || {};
  const assessments = Array.from(sso.latestCommanderStrategicAssessments || []);
  const latest = assessments[0] || {};
  const score = latest.strategic_consensus_score || bridge.strategicConsensusScore || {};

  $("sso-status").textContent = sso.health?.status || "READY";
  $("sso-produced").textContent = metrics.strategicAssessmentsProduced ?? assessments.length;
  $("sso-consensus-score").textContent = Number(score.overall_score || metrics.averageStrategicConsensusScore || 0).toFixed(1);
  $("sso-evidence-quality").textContent = `${Number(score.evidence_quality || metrics.evidenceIntegrationQuality || 0).toFixed(1)}%`;
  $("sso-classification").textContent = latest.strategic_classification || sso.sicFeed?.classification || "Neutral";
  $("sso-api-usage").textContent = money(bridge.apiUsage?.apiCost || metrics.apiUtilization || 0, 4);
  $("sso-workflow-status").textContent = bridge.workflowStatus || "bounded";
  $("sso-authority").textContent = sso.internalDiagnostics?.placesTrades ? "CHECK" : "ADVISORY";

  $("sso-score").innerHTML = metricRows(score.component_scores || {});
  $("sso-consensus").innerHTML = Array.from(bridge.consensusMatrix || []).map(item => `
    <div class="sic-record">
      <b>${item.office}</b>
      <span>Score ${Number(item.score || 0).toFixed(1)}</span>
      <strong>Evidence ${Number(item.evidenceQuality || 0).toFixed(1)}</strong>
    </div>
  `).join("");
  $("sso-agreement").innerHTML = Array.from(bridge.officeAgreementMatrix || []).map(item => `
    <div class="sic-record">
      <b>${item.office}</b>
      <span>${item.alignment}</span>
      <strong>${Array.from(item.themes || []).slice(0, 3).join(" / ")}</strong>
    </div>
  `).join("");
  $("sso-evidence-heat").innerHTML = heatRows(bridge.evidenceHeatMap, "office", "score");
  $("sso-confidence").innerHTML = metricRows(bridge.confidenceDistribution);
  $("sso-uncertainty").innerHTML = Array.from(bridge.uncertaintyMap || []).map(item => `
    <div class="sic-record">
      <b>${item.source}</b>
      <span>${item.impact}</span>
      <strong>${item.severity}</strong>
    </div>
  `).join("");
  $("sso-themes").innerHTML = sicTagList(bridge.strategicThemes);
  $("sso-risks").innerHTML = sicTagList(bridge.emergingRisks);
  $("sso-research").innerHTML = sicTagList(bridge.researchPriorities);
  const briefing = bridge.commanderBriefing || {};
  $("sso-briefing").innerHTML = `
    <div class="sic-record">
      <b>${briefing.currentStrategicOutlook || "Strategic outlook pending"}</b>
      <span>${Array.from(briefing.highestConfidenceThemes || []).join(" / ")}</span>
      <strong>Consensus ${Number(briefing.consensusScore || 0).toFixed(1)}</strong>
    </div>
  `;
  $("sso-history").innerHTML = Array.from(bridge.historicalStrategicAssessments || []).map(item => `
    <div class="sic-record">
      <b>${item.assessmentId}</b>
      <span>${item.classification}</span>
      <strong>${Number(item.score || 0).toFixed(1)}</strong>
    </div>
  `).join("");
  $("sso-forecast").innerHTML = metricRows(bridge.forecastAccuracy);
  $("sso-runtime").innerHTML = `
    <div><span>Runtime Health</span><b>${bridge.runtimeHealth || "NOMINAL"}</b></div>
    <div><span>API Mode</span><b>${bridge.apiUsage?.mode || "deterministic"}</b></div>
    <div><span>Workflow</span><b>${bridge.workflowStatus || "bounded"}</b></div>
  `;
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
  const promptEvolution = state.promptEvolutionEngine || {};
  const promptMetrics = promptEvolution.performanceDashboard || {};
  $("prompt-contract-summary").innerHTML = [
    ["Engineering Order", contract.engineeringOrder],
    ["Contract Version", contract.contractVersion],
    ["Temperature", contract.defaultTemperature],
    ["Top P", contract.topP],
    ["Provider Independent", contract.providerIndependent ? "YES" : "NO"],
    ["Templates", contract.templates.length],
    ["Production Prompts", promptMetrics.productionPrompts ?? contract.templates.length],
    ["Candidate Prompts", promptMetrics.candidatePrompts ?? 0],
    ["Production Mutations", promptMetrics.productionMutationCount ?? 0],
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

function renderDecisionObjectSchema() {
  const schema = state.decisionObjectSchema;
  if (!schema || !$("dos-summary")) return;
  const validator = schema.objectValidator || {};
  $("dos-summary").innerHTML = [
    ["Engineering Order", schema.engineeringOrder],
    ["Mode", schema.constitutionalMode],
    ["Schema Version", schema.schemaVersion],
    ["Frozen", schema.frozen ? "YES" : "NO"],
    ["Fingerprint", schema.schemaFingerprint],
    ["Versions", (schema.immutableSchemaVersions || []).join(", ")],
  ].map(([name, value]) => `<div><span>${name}</span><b>${value}</b></div>`).join("");
  $("dos-validation").innerHTML = [
    ["Decision Objects", validator.decisionObjectCount || 0],
    ["Valid", validator.validDecisionObjects || 0],
    ["Invalid", validator.invalidDecisionObjects || 0],
    ["Violations", (validator.schemaViolations || []).length],
  ].map(([name, value]) => `<div><span>${name}</span><b>${value}</b></div>`).join("");
  $("dos-fields").innerHTML = (schema.requiredFields || []).map(field => `
    <div class="api-call"><b>${field}</b><span>Required</span><div>${schema.fieldDefinitions?.[field] || "Schema v1.0 required field."}</div></div>
  `).join("");
  $("dos-enums").innerHTML = `
    <div class="api-call"><b>Optional Fields</b><span>${(schema.optionalFields || []).length}</span><div>${(schema.optionalFields || []).join("<br />")}</div></div>
    ${Object.entries(schema.enumerationRegistry || {}).map(([name, values]) => `<div class="api-call"><b>${label(name)}</b><span>Enumeration</span><div>${(values || []).join("<br />")}</div></div>`).join("")}
  `;
  $("dos-rules").innerHTML = (schema.validationRules || []).map(rule => `<div class="api-call"><b>${label(rule)}</b><span>Required</span><div>Validated before a Decision Object enters enterprise history.</div></div>`).join("");
  $("dos-repository").innerHTML = (schema.repositoryBrowser || []).length
    ? schema.repositoryBrowser.map(item => `<div class="api-call"><b>${item.decisionObjectId}</b><span>${item.schemaVersion} / ${item.validationStatus}</span><div>Workflow ${item.workflowId}<br />Office ${item.office} / Compatibility ${item.compatibilityStatus}<br />Replay ${item.replayVerificationStatus}</div></div>`).join("")
    : `<div class="alert-empty">Repository Browser awaiting Decision Objects</div>`;
  $("dos-hashes").innerHTML = (schema.hashViewer || []).length
    ? schema.hashViewer.map(item => `<div class="api-call"><b>${item.decisionObjectId}</b><span>Checksum</span><div>${item.hash || "Pending"}</div></div>`).join("")
    : `<div class="alert-empty">Hash Viewer awaiting Decision Objects</div>`;
  $("dos-lineage").innerHTML = `
    <div class="api-call"><b>Constitutional Chain</b><span>Lineage</span><div>${(schema.lineage?.chain || []).join(" -> ")}</div></div>
    ${(schema.referenceGraph || []).map(item => `<div class="api-call"><b>${item.decisionObjectId}</b><span>Reference Graph</span><div>Token ${item.workflowTokenId}<br />Market ${item.marketContextSnapshotId}<br />Prompt ${item.promptVersion}<br />Strategy ${item.strategyVersion}<br />Truth ${item.performanceTruthId}</div></div>`).join("")}
  `;
  $("dos-compatibility").innerHTML = `
    ${(schema.compatibilityMatrix || []).map(item => `<div class="api-call"><b>${item.fromVersion} -> ${item.toVersion}</b><span>${item.status}</span><div>Historical objects remain readable through compatibility layers.</div></div>`).join("")}
    <div class="api-call"><b>Migration Rules</b><span>Read Only</span><div>${(schema.migrationRules || []).join("<br />")}</div></div>
  `;
  $("dos-serialization").innerHTML = Object.entries(schema.serializationStandard || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value ? "YES" : "NO"}</b></div>`).join("");
  $("dos-diagnostics").innerHTML = `
    ${Object.entries(schema.lawVII || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${typeof value === "boolean" ? (value ? "YES" : "NO") : value}</b></div>`).join("")}
    ${Object.entries(schema.internalDiagnostics || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("")}
  `;
}

function renderDecisionObjectQualityScoringEngine() {
  const quality = state.decisionObjectQualityScoringEngine;
  if (!quality || !$("doq-summary")) return;
  const latest = quality.latestQualityReport || {};
  $("doq-summary").innerHTML = [
    ["Engineering Order", quality.engineeringOrder],
    ["Mode", quality.constitutionalMode],
    ["Overall Quality", quality.overallQualityScore || 0],
    ["Grade", quality.grade || "Unknown"],
    ["Decision Ready", quality.decisionReady ? "YES" : "NO"],
    ["Reports", (quality.qualityReports || []).length],
    ["Latest Report", latest.qualityId || "None"],
  ].map(([name, value]) => `<div><span>${name}</span><b>${value}</b></div>`).join("");
  $("doq-reports").innerHTML = (quality.qualityReports || []).length
    ? quality.qualityReports.map(item => `<div class="api-call"><b>${item.qualityId}</b><span>${item.grade} / ${item.overallScore}</span><div>${item.decisionObjectId}<br />${item.decisionReadiness}<br />Confidence ${Math.round(Number(item.confidence || 0) * 100)}%</div></div>`).join("")
    : `<div class="alert-empty">Quality Reports awaiting Decision Objects</div>`;
  $("doq-dimensions").innerHTML = (latest.dimensionScores || []).map(item => `<div class="api-call"><b>${item.dimension}</b><span>${item.status}</span><div>Score ${item.score}</div></div>`).join("") || `<div class="alert-empty">Dimension Scores awaiting Decision Objects</div>`;
  $("doq-history").innerHTML = (quality.qualityHistory || []).length
    ? quality.qualityHistory.map(item => `<div class="api-call"><b>${item.qualityId}</b><span>${item.grade} / ${item.overallScore}</span><div>${item.decisionObjectId}<br />${item.decisionReadiness}<br />${item.timestamp}</div></div>`).join("")
    : `<div class="alert-empty">Quality History awaiting reports</div>`;
  $("doq-trends").innerHTML = Object.entries(quality.trendAnalysis || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
  $("doq-thresholds").innerHTML = Object.entries(quality.thresholdConfiguration || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
  $("doq-algorithms").innerHTML = (quality.scoringAlgorithms || []).map(item => `<div class="api-call"><b>${item.dimension}</b><span>Algorithm</span><div>${item.algorithm}</div></div>`).join("");
  $("doq-completeness").innerHTML = Object.entries(quality.completenessAnalysis || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
  $("doq-consistency").innerHTML = Object.entries(quality.consistencyAnalysis || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
  $("doq-freshness").innerHTML = Object.entries(quality.freshnessMetrics || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
  $("doq-evidence").innerHTML = Object.entries(quality.evidenceMetrics || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
  $("doq-calibration").innerHTML = Object.entries(quality.calibrationMetrics || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
  $("doq-forecasts").innerHTML = (quality.qualityForecasts || []).map(item => `<div class="api-call"><b>${item.forecast}</b><span>${item.risk}</span><div>${item.basis}</div></div>`).join("");
  $("doq-recommendations").innerHTML = (quality.qualityRecommendations || []).map(item => `<div class="api-call"><b>Quality Recommendation</b><span>Advisory</span><div>${item}</div></div>`).join("") || `<div class="alert-empty">No quality recommendations</div>`;
  $("doq-diagnostics").innerHTML = `
    ${Object.entries(quality.lawVII || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${typeof value === "boolean" ? (value ? "YES" : "NO") : value}</b></div>`).join("")}
    ${Object.entries(quality.internalDiagnostics || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("")}
  `;
}

function renderDecisionExplainabilityEngine() {
  const explain = state.decisionExplainabilityEngine;
  if (!explain || !$("dee-summary")) return;
  const latest = explain.latestExplainabilityReport || {};
  $("dee-summary").innerHTML = [
    ["Engineering Order", explain.engineeringOrder],
    ["Mode", explain.constitutionalMode],
    ["Reports", (explain.explainabilityRepository || []).length],
    ["Latest Report", latest.explainabilityReportId || "None"],
    ["Readability", latest.commanderReadabilityScore || 0],
    ["Audit", latest.auditStatus || "Standing By"],
  ].map(([name, value]) => `<div><span>${name}</span><b>${value}</b></div>`).join("");
  $("dee-repository").innerHTML = (explain.explainabilityRepository || []).map(item => `<div class="api-call"><b>${item.explainabilityReportId}</b><span>${item.auditStatus}</span><div>${item.decisionSummary}<br />${item.reasoningSummary}<br />Readability ${item.commanderReadabilityScore}</div></div>`).join("") || `<div class="alert-empty">Explainability Repository awaiting Decision Objects</div>`;
  $("dee-reasoning").innerHTML = (latest.reasoningChain || []).map(item => `<div class="api-call"><b>${item.stage}</b><span>Reasoning Chain</span><div>${item.step}</div></div>`).join("") || `<div class="alert-empty">Reasoning Graph awaiting explanations</div>`;
  $("dee-evidence").innerHTML = (latest.evidenceSummary || []).map(item => `<div class="api-call"><b>${item.category}</b><span>${item.reference || "Evidence"}</span><div>${item.summary}</div></div>`).join("") || `<div class="alert-empty">Evidence Graph awaiting explanations</div>`;
  $("dee-weighting").innerHTML = (latest.evidenceWeighting || []).map(item => `<div><span>${item.factor}</span><b>${item.weightPercent}%</b></div>`).join("");
  $("dee-templates").innerHTML = (explain.explanationTemplates || []).map(item => `<div class="api-call"><b>${item}</b><span>Template</span><div>Generated from the same underlying explanation object.</div></div>`).join("");
  $("dee-quality").innerHTML = Object.entries(explain.explanationQuality || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
  $("dee-readability").innerHTML = (explain.readabilityScores || []).map(item => `<div><span>${item.decisionObjectId}</span><b>${item.commanderReadabilityScore}</b></div>`).join("");
  $("dee-alternatives").innerHTML = (explain.alternativeDecisions || []).map(item => `<div class="api-call"><b>${item.action}</b><span>${item.status}</span><div>${item.reason}</div></div>`).join("") || `<div class="alert-empty">Alternative Decisions awaiting latest report</div>`;
  $("dee-confidence").innerHTML = Object.entries(explain.confidenceBreakdown || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
  $("dee-search").innerHTML = (explain.historicalSearch || []).map(item => `<div class="api-call"><b>${item.decisionObjectId}</b><span>${Math.round(Number(item.confidence || 0) * 100)}%</span><div>${item.recommendation}<br />${(item.searchTerms || []).join(", ")}</div></div>`).join("") || `<div class="alert-empty">Historical Search awaiting explanation history</div>`;
  $("dee-reference").innerHTML = (explain.referenceGraph || []).map(item => `<div class="api-call"><b>${item.decisionObjectId}</b><span>${item.auditStatus}</span><div>Workflow ${item.workflowId}<br />Performance Truth Linked ${item.performanceTruthLinked ? "YES" : "NO"}</div></div>`).join("") || `<div class="alert-empty">Reference Graph awaiting explanations</div>`;
  $("dee-diagnostics").innerHTML = `
    ${Object.entries(explain.lawVII || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${typeof value === "boolean" ? (value ? "YES" : "NO") : value}</b></div>`).join("")}
    ${Object.entries(explain.internalDiagnostics || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("")}
  `;
}

function renderEnterpriseBenchmarkEngine() {
  const benchmark = state.enterpriseBenchmarkEngine;
  if (!benchmark || !$("ebe-summary")) return;
  $("ebe-summary").innerHTML = [
    ["Engineering Order", benchmark.engineeringOrder],
    ["Mode", benchmark.constitutionalMode],
    ["Registry", (benchmark.benchmarkRegistry || []).length],
    ["Snapshots", (benchmark.benchmarkSnapshots || []).length],
    ["Reports", (benchmark.benchmarkReports || []).length],
    ["Value Added", benchmark.commanderReviewFeed?.valueAddedStatement || "Awaiting truth"],
  ].map(([name, value]) => `<div><span>${name}</span><b>${value}</b></div>`).join("");
  $("ebe-registry").innerHTML = (benchmark.benchmarkRegistry || []).map(item => `<div class="api-call"><b>${item.benchmarkName}</b><span>${item.benchmarkType} / ${item.status}</span><div>${item.benchmarkSymbol}<br />${item.benchmarkPurpose}<br />${item.calculationMethod}</div></div>`).join("");
  $("ebe-configuration").innerHTML = Object.entries(benchmark.benchmarkConfiguration || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
  $("ebe-performance").innerHTML = (benchmark.benchmarkPerformance || []).map(item => `<div class="api-call"><b>${item.benchmark}</b><span>${item.benchmark_return}%</span><div>Portfolio ${item.portfolio_return}% / Alpha ${item.alpha}%<br />${item.timestamp}</div></div>`).join("") || `<div class="alert-empty">Benchmark Performance awaiting truth records</div>`;
  $("ebe-reports").innerHTML = (benchmark.benchmarkReports || []).map(item => `<div class="api-call"><b>${item.reportId}</b><span>${item.period}</span><div>${item.summary}<br />Snapshots ${item.snapshotCount || item.comparisonCount || 0}</div></div>`).join("");
  $("ebe-trades").innerHTML = (benchmark.tradeLevelComparisons || []).slice(-24).map(item => `<div class="api-call"><b>${item.tradeId}</b><span>${item.benchmarkName}</span><div>ARGOS ${item.argosReturn}% / Benchmark ${item.benchmarkReturn}%<br />Excess ${item.excessReturn}% / Opportunity ${(Number(item.benchmarkReturn || 0) - Number(item.argosReturn || 0)).toFixed(4)}%</div></div>`).join("") || `<div class="alert-empty">Trade-Level Comparisons awaiting paper trades</div>`;
  $("ebe-strategies").innerHTML = (benchmark.strategyLevelComparisons || []).map(item => `<div class="api-call"><b>${item.strategy}</b><span>Excess ${item.excessReturn}</span><div>Return ${item.strategyReturn} / Benchmark ${item.benchmarkReturn}<br />Sharpe ${item.sharpeRatio} / Win ${item.winRate}%</div></div>`).join("");
  $("ebe-portfolio").innerHTML = (benchmark.portfolioLevelComparisons || []).map(item => `<div class="api-call"><b>${item.benchmark}</b><span>${item.addsValue ? "Adds Value" : "Under Benchmark"}</span><div>ARGOS ${item.argosReturn}% / Benchmark ${item.benchmarkReturn}%<br />Excess ${item.excessReturn}%</div></div>`).join("");
  $("ebe-risk").innerHTML = Object.entries(benchmark.riskAdjustedMetrics || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
  $("ebe-random").innerHTML = Object.entries(benchmark.randomBaselineControls || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
  $("ebe-no-trade").innerHTML = Object.entries(benchmark.noTradeBaseline || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
  $("ebe-regimes").innerHTML = (benchmark.marketRegimeBuckets || []).map(item => `<div class="api-call"><b>${item.marketRegime}</b><span>${item.active ? "Active" : "Tracked"}</span><div>Snapshots ${item.snapshotCount}<br />Average Excess ${item.averageExcessReturn}%</div></div>`).join("");
  $("ebe-history").innerHTML = (benchmark.historicalBenchmarkData || []).slice(-20).map(item => `<div class="api-call"><b>${item.benchmark}</b><span>${item.benchmark_return}%</span><div>${item.timestamp}<br />Alpha ${item.alpha}%</div></div>`).join("") || `<div class="alert-empty">Historical Benchmark Data awaiting performance truth</div>`;
  $("ebe-diagnostics").innerHTML = `
    ${Object.entries(benchmark.lawVII || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${typeof value === "boolean" ? (value ? "YES" : "NO") : value}</b></div>`).join("")}
    ${Object.entries(benchmark.benchmarkDiagnostics || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("")}
  `;
}

function renderTradeAttributionEngine() {
  const attribution = state.tradeAttributionEngine;
  if (!attribution || !$("tae-summary")) return;
  const latest = attribution.latestAttributionReport || {};
  $("tae-summary").innerHTML = [
    ["Engineering Order", attribution.engineeringOrder],
    ["Mode", attribution.constitutionalMode],
    ["Reports", (attribution.attributionRepository || []).length],
    ["Latest Report", latest.attributionReportId || "None"],
    ["Confidence", latest.overallAttributionConfidence || 0],
    ["Commander Feed", attribution.commanderReviewFeed?.reportCount || 0],
  ].map(([name, value]) => `<div><span>${name}</span><b>${value}</b></div>`).join("");
  $("tae-repository").innerHTML = (attribution.attributionRepository || []).map(item => `<div class="api-call"><b>${item.attributionReportId}</b><span>${item.tradeId}</span><div>${item.commanderSummary}<br />${item.outcomeSummary?.symbol || ""} / Alpha ${item.outcomeSummary?.excessReturn || 0}%<br />${item.marketRegime}</div></div>`).join("") || `<div class="alert-empty">Attribution Repository awaiting completed paper trades</div>`;
  $("tae-contribution").innerHTML = Object.entries(attribution.contributionAnalysis || {}).map(([key, value]) => `<div><span>${key}</span><b>${value.averageContributionScore}</b></div>`).join("");
  $("tae-counterfactuals").innerHTML = (attribution.counterfactualReports || []).map(item => `<div class="api-call"><b>${item.counterfactualReportId}</b><span>${item.tradeId}</span><div>${(item.experiments || []).map(experiment => `${experiment.scenario}: ${experiment.estimatedReturn}%`).join("<br />")}</div></div>`).join("") || `<div class="alert-empty">Counterfactual Reports awaiting attribution</div>`;
  $("tae-strategy").innerHTML = (attribution.strategyAttribution || []).map(item => `<div class="api-call"><b>${item.strategyVersion}</b><span>${item.averageContribution}</span><div>Trades ${item.tradeCount}<br />Promotion evidence ${item.promotionRequiresAttributionEvidence ? "Required" : "Unavailable"}</div></div>`).join("");
  $("tae-prompt").innerHTML = (attribution.promptAttribution || []).map(item => `<div class="api-call"><b>${item.promptVersion}</b><span>${item.averageContribution}</span><div>Trades ${item.tradeCount}<br />Prompt quality separated ${item.promptQualitySeparatedFromMarketTailwinds ? "YES" : "NO"}</div></div>`).join("");
  $("tae-market").innerHTML = (attribution.marketAttribution || []).map(item => `<div class="api-call"><b>${item.marketRegime}</b><span>${item.averageContribution}</span><div>Trades ${item.tradeCount}</div></div>`).join("");
  $("tae-risk").innerHTML = Object.entries(attribution.riskAttribution || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
  $("tae-execution").innerHTML = Object.entries(attribution.executionAttribution || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
  $("tae-portfolio").innerHTML = Object.entries(attribution.portfolioAttribution || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
  $("tae-randomness").innerHTML = Object.entries(attribution.randomnessEstimation || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
  $("tae-trends").innerHTML = (attribution.attributionTrends || []).map(item => `<div class="api-call"><b>${item.dimension}</b><span>${item.trend}</span><div>Latest contribution ${item.latestContribution}</div></div>`).join("");
  $("tae-confidence").innerHTML = Object.entries(attribution.confidenceAnalysis || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
  $("tae-search").innerHTML = (attribution.historicalSearch || []).map(item => `<div class="api-call"><b>${item.tradeId}</b><span>${item.confidence}</span><div>${item.symbol} / ${item.strategyVersion}<br />${(item.searchTerms || []).join(", ")}</div></div>`).join("") || `<div class="alert-empty">Historical Search awaiting attribution history</div>`;
  $("tae-diagnostics").innerHTML = `
    ${Object.entries(attribution.lawVII || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${typeof value === "boolean" ? (value ? "YES" : "NO") : value}</b></div>`).join("")}
    ${Object.entries(attribution.internalDiagnostics || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("")}
  `;
}

function renderEnterpriseReproducibilityFramework() {
  const reproducibility = state.enterpriseReproducibilityFramework;
  if (!reproducibility || !$("erf-summary")) return;
  const latest = reproducibility.latestEnterpriseSnapshot || {};
  $("erf-summary").innerHTML = [
    ["Engineering Order", reproducibility.engineeringOrder],
    ["Mode", reproducibility.constitutionalMode],
    ["Snapshots", (reproducibility.enterpriseSnapshots || []).length],
    ["Latest Snapshot", latest.snapshotId || "None"],
    ["Replay Status", latest.replayStatus || "Standing By"],
    ["Score", reproducibility.reproducibilityScore?.overallScore || 0],
  ].map(([name, value]) => `<div><span>${name}</span><b>${value}</b></div>`).join("");
  $("erf-snapshots").innerHTML = (reproducibility.enterpriseSnapshots || []).map(item => `<div class="api-call"><b>${item.snapshotId}</b><span>${item.replayStatus} / ${item.validationStatus}</span><div>Workflow ${item.workflowId}<br />Decision ${item.decisionObjectId}<br />Checksum ${item.checksum}</div></div>`).join("") || `<div class="alert-empty">Enterprise Snapshots awaiting completed workflows</div>`;
  $("erf-replay-browser").innerHTML = (reproducibility.replayBrowser || []).map(item => `<div class="api-call"><b>${item.workflowId}</b><span>${item.replayStatus}</span><div>Snapshot ${item.snapshotId}<br />Decision ${item.decisionObjectId}<br />${item.timestamp}</div></div>`).join("") || `<div class="alert-empty">Replay Browser awaiting snapshots</div>`;
  $("erf-certification").innerHTML = (reproducibility.replayCertification || []).map(item => `<div class="api-call"><b>${item.certificationId}</b><span>${item.replayStatus} / ${item.score}</span><div>${item.explanation}<br />${Object.entries(item.checks || {}).map(([key, value]) => `${label(key)}: ${value ? "MATCH" : "DIFFERENCE"}`).join("<br />")}</div></div>`).join("") || `<div class="alert-empty">Replay Certification awaiting replay packages</div>`;
  $("erf-differences").innerHTML = (reproducibility.differenceAnalysis || []).map(item => `<div class="api-call"><b>${item.differenceAnalysisId}</b><span>${item.replayStatus}</span><div>${(item.differences || []).map(diff => `${diff.difference}: ${diff.status}`).join("<br />")}</div></div>`).join("") || `<div class="alert-empty">Difference Analysis clear</div>`;
  $("erf-environment").innerHTML = (reproducibility.environmentSnapshots || []).map(item => `<div class="api-call"><b>${item.environmentProfile}</b><span>Environment</span><div>Paper ${item.runtimeSettings?.paperTradingActive ? "Active" : "Inactive"} / Credit ${item.creditLimits?.budgetStatus || "Unknown"}<br />Offices ${(item.officeConfiguration || []).join(", ")}</div></div>`).join("");
  $("erf-prompts").innerHTML = (reproducibility.promptSnapshots || []).map(item => `<div class="api-call"><b>${item.promptPackage}</b><span>${item.promptVersion}</span><div>Hash ${item.promptHash}<br />Validation ${item.validationStatus}</div></div>`).join("");
  $("erf-strategies").innerHTML = (reproducibility.strategySnapshots || []).map(item => `<div class="api-call"><b>${item.strategyPackage}</b><span>${item.strategyVersion}</span><div>${item.strategyMetadata?.strategy || "Strategy"}<br />Regime ${item.applicableMarketRegime}</div></div>`).join("");
  $("erf-configuration").innerHTML = (reproducibility.configurationSnapshots || []).map(item => `<div class="api-call"><b>${item.configurationVersion}</b><span>${item.environmentProfile}</span><div>Enterprise ${item.enterpriseVersion}<br />Registry ${item.registryHash}</div></div>`).join("");
  $("erf-providers").innerHTML = (reproducibility.providerSnapshots || []).map(item => `<div class="api-call"><b>${item.provider}</b><span>${item.providerVersion}</span><div>Source ${item.source}<br />Replay independent ${item.replayDoesNotDependOnCurrentProviders ? "YES" : "NO"}</div></div>`).join("");
  $("erf-portfolio").innerHTML = (reproducibility.portfolioSnapshots || []).map(item => `<div class="api-call"><b>Portfolio Snapshot</b><span>${money(item.cash || 0)}</span><div>Buying Power ${money(item.buyingPower || 0)}<br />Exposure ${item.currentExposure || 0}<br />Positions ${(item.positions || []).length}</div></div>`).join("");
  $("erf-replay-statistics").innerHTML = Object.entries(reproducibility.replayStatistics || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${Array.isArray(value) ? value.join(", ") : value}</b></div>`).join("");
  $("erf-coverage").innerHTML = Object.entries(reproducibility.historicalCoverage || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
  $("erf-provenance").innerHTML = (reproducibility.provenanceGraph || []).map(item => `<div class="api-call"><b>${item.snapshotId}</b><span>${item.provenanceNodes} nodes</span><div>Workflow ${item.workflowId}<br />Truth ${item.performanceTruthId}<br />Attribution ${item.attributionReportId || "Pending"}</div></div>`).join("") || `<div class="alert-empty">Provenance Graph awaiting enterprise snapshots</div>`;
  $("erf-diagnostics").innerHTML = `
    ${Object.entries(reproducibility.lawVII || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${typeof value === "boolean" ? (value ? "YES" : "NO") : value}</b></div>`).join("")}
    ${Object.entries(reproducibility.internalDiagnostics || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("")}
  `;
}

function renderEnterpriseOperationalGuardrails() {
  const guardrails = state.enterpriseOperationalGuardrails;
  if (!guardrails || !$("eog-summary")) return;
  $("eog-summary").innerHTML = [
    ["Engineering Order", guardrails.engineeringOrder],
    ["Mode", guardrails.constitutionalMode],
    ["Readiness", guardrails.enterpriseReadinessScore],
    ["State", guardrails.readinessState],
    ["Confidence", `${Math.round(Number(guardrails.readinessConfidence || 0) * 100)}%`],
    ["Paper Authorized", guardrails.tradingAuthorization?.paperTradingAuthorized ? "YES" : "NO"],
  ].map(([name, value]) => `<div><span>${name}</span><b>${value}</b></div>`).join("");
  $("eog-registry").innerHTML = (guardrails.guardrailRegistry || []).map(item => `<div class="api-call"><b>${item.guardrail}</b><span>${item.status} / ${item.score}</span><div>${item.evidence}<br />Threshold ${item.threshold}<br />Decision ${item.decision} / Response ${item.automaticResponse}</div></div>`).join("");
  $("eog-thresholds").innerHTML = Object.entries(guardrails.thresholdConfiguration || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
  $("eog-authorization").innerHTML = (guardrails.authorizationHistory || []).map(item => `<div class="api-call"><b>${item.authorizationId}</b><span>${item.decision}</span><div>${item.reason}<br />${item.timestamp}<br />Commander ${item.commanderNotification}</div></div>`).join("") || `<div class="alert-empty">Authorization History awaiting workflow requests</div>`;
  $("eog-emergency").innerHTML = (guardrails.emergencyHalts || []).length
    ? guardrails.emergencyHalts.map(item => `<div class="api-call"><b>${item.eventId}</b><span>${item.status}</span><div>${item.reason}</div></div>`).join("")
    : `<div class="alert-empty">No Emergency Halts</div>`;
  $("eog-safe-mode").innerHTML = (guardrails.safeModeEvents || []).length
    ? guardrails.safeModeEvents.map(item => `<div class="api-call"><b>${item.eventId}</b><span>${item.status}</span><div>${item.reason}</div></div>`).join("")
    : `<div class="api-call"><b>Safe Mode</b><span>Available</span><div>Stops new workflows ${guardrails.safeMode?.stopsNewWorkflows ? "YES" : "NO"}<br />Preserves enterprise state ${guardrails.safeMode?.preservesEnterpriseState ? "YES" : "NO"}<br />Continues monitoring ${guardrails.safeMode?.continuesMonitoring ? "YES" : "NO"}</div></div>`;
  $("eog-recovery").innerHTML = (guardrails.recoveryEvents || []).length
    ? guardrails.recoveryEvents.map(item => `<div class="api-call"><b>${item.eventId}</b><span>${item.status}</span><div>${item.reason}</div></div>`).join("")
    : Object.entries(guardrails.recoveryAuthorization || {}).map(([key, value]) => `<div class="api-call"><b>${label(key)}</b><span>Recovery</span><div>${value}</div></div>`).join("");
  $("eog-overrides").innerHTML = (guardrails.commanderOverrides || []).length
    ? guardrails.commanderOverrides.map(item => `<div class="api-call"><b>${item.overrideId}</b><span>${item.status}</span><div>${item.reason}</div></div>`).join("")
    : `<div class="api-call"><b>Commander Override Policy</b><span>Configured</span><div>Non-constitutional overrides ${guardrails.commanderOverridePolicy?.nonConstitutionalGuardrailsMayBeOverridden ? "YES" : "NO"}<br />Absolute protections ${(guardrails.commanderOverridePolicy?.absoluteProtections || []).join(", ")}</div></div>`;
  $("eog-health").innerHTML = Object.entries(guardrails.healthThresholds || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
  $("eog-quality").innerHTML = Object.entries(guardrails.qualityThresholds || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
  $("eog-budget").innerHTML = Object.entries(guardrails.budgetThresholds || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
  $("eog-dependencies").innerHTML = (guardrails.dependencyStatus || []).map(item => `<div class="api-call"><b>${item.dependency}</b><span>${item.status}</span><div>Score ${item.score}<br />Response ${item.automaticResponse}</div></div>`).join("");
  $("eog-timeline").innerHTML = (guardrails.operationalTimeline || []).map(item => `<div class="api-call"><b>${item.event}</b><span>${item.status}</span><div>${item.timestamp}<br />Readiness ${item.score}</div></div>`).join("");
  $("eog-audit").innerHTML = (guardrails.guardrailAuditHistory || []).map(item => `<div class="api-call"><b>${item.auditId}</b><span>${item.guardrail} / ${item.status}</span><div>${item.evidence}<br />Decision ${item.decision}<br />Hash ${item.hash}</div></div>`).join("") || `<div class="alert-empty">Guardrail Audit History awaiting authorization events</div>`;
  $("eog-diagnostics").innerHTML = `
    ${Object.entries(guardrails.lawVII || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${typeof value === "boolean" ? (value ? "YES" : "NO") : value}</b></div>`).join("")}
    ${Object.entries(guardrails.internalDiagnostics || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("")}
  `;
}

function renderEnterpriseExperimentScheduler() {
  const scheduler = state.enterpriseExperimentScheduler;
  if (!scheduler || !$("ees-summary")) return;
  $("ees-summary").innerHTML = [
    ["Engineering Order", scheduler.engineeringOrder],
    ["Mode", scheduler.constitutionalMode],
    ["Backlog", (scheduler.researchBacklog || []).length],
    ["Queue", (scheduler.experimentQueue || []).length],
    ["Today", (scheduler.schedulingCalendar?.today || []).length],
    ["Curiosity", scheduler.researchDashboard?.enterpriseCuriosityIndex || 0],
  ].map(([name, value]) => `<div><span>${name}</span><b>${value}</b></div>`).join("");
  $("ees-backlog").innerHTML = (scheduler.researchBacklog || []).map(item => `<div class="api-call"><b>${item.experimentId}</b><span>${item.category} / ${item.priority}</span><div>${item.title}<br />Hypothesis ${item.hypothesis}<br />Success ${(item.successCriteria || []).join(", ")}</div></div>`).join("");
  $("ees-queue").innerHTML = (scheduler.experimentQueue || []).map(item => `<div class="api-call"><b>${item.queueId}</b><span>${item.status}</span><div>${item.title}<br />Priority ${item.priorityScore}<br />${item.laboratoryStatus}</div></div>`).join("");
  $("ees-priority").innerHTML = (scheduler.priorityCalculations || []).slice(0, 12).map(item => `<div class="api-call"><b>${item.experimentId}</b><span>${item.priorityScore}</span><div>Benefit ${item.expectedEnterpriseBenefit} / Information ${item.estimatedInformationGain}<br />Cost ${item.estimatedCreditCost} / Knowledge per credit ${item.knowledgePerCredit}</div></div>`).join("");
  $("ees-information").innerHTML = (scheduler.informationGainEstimates || []).slice(0, 12).map(item => `<div><span>${item.experimentId}</span><b>${item.knowledgePerCredit}</b></div>`).join("");
  $("ees-dependencies").innerHTML = (scheduler.dependencyGraph || []).map(item => `<div class="api-call"><b>${item.experimentId}</b><span>${item.dependenciesSatisfied ? "Satisfied" : "Blocked"}</span><div>${(item.dependencies || []).join("<br />") || "No dependencies"}</div></div>`).join("");
  $("ees-calendar").innerHTML = Object.entries(scheduler.schedulingCalendar || {}).map(([windowName, rows]) => `<div class="api-call"><b>${label(windowName)}</b><span>${(rows || []).length}</span><div>${(rows || []).map(item => `${item.experimentId}: ${item.title}`).join("<br />") || "No scheduled research"}</div></div>`).join("");
  $("ees-capacity").innerHTML = Object.entries(scheduler.laboratoryCapacity || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
  $("ees-budget").innerHTML = Object.entries(scheduler.budgetAllocation || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
  $("ees-yield").innerHTML = Object.entries(scheduler.knowledgeYieldMetrics || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
  $("ees-velocity").innerHTML = Object.entries(scheduler.researchVelocity || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
  $("ees-commander").innerHTML = (scheduler.commanderPriorities || []).map(item => `<div class="api-call"><b>${item.experimentId}</b><span>${item.commanderPriority}</span><div>${item.title}<br />Priority Score ${item.priorityScore}</div></div>`).join("");
  $("ees-history").innerHTML = (scheduler.experimentHistory || []).length
    ? scheduler.experimentHistory.map(item => `<div class="api-call"><b>${item.experimentId}</b><span>${item.state}</span><div>${item.originalWorkflowId}<br />${item.knowledgeProduced}</div></div>`).join("")
    : `<div class="alert-empty">Experiment History awaiting completed laboratory experiments</div>`;
  $("ees-diagnostics").innerHTML = `
    ${Object.entries(scheduler.lawVII || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${typeof value === "boolean" ? (value ? "YES" : "NO") : value}</b></div>`).join("")}
    ${Object.entries(scheduler.lawVIIIFrugality || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("")}
    ${Object.entries(scheduler.internalDiagnostics || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("")}
  `;
}

function renderPromptEvolutionEngine() {
  const promptEvolution = state.promptEvolutionEngine;
  if (!promptEvolution || !$("pee-metrics")) return;
  const repository = promptEvolution.promptRepository || [];
  const candidates = promptEvolution.promptImprovementCandidates || [];
  $("pee-metrics").innerHTML = Object.entries(promptEvolution.performanceDashboard || {}).map(([key, value]) => `<div>${label(key)}<b>${value}</b></div>`).join("");
  $("pee-repository").innerHTML = repository.length
    ? repository.map(item => `
      <div class="api-call"><b>${item.promptId}</b><span>${item.associatedOffice} / ${item.status} / v${item.versionNumber}</span><div>${item.promptName}<br />${item.purpose}<br />Confidence ${Math.round((item.confidence || 0) * 100)}% / Current Production ${item.currentProductionVersion}</div></div>
    `).join("")
    : `<div class="alert-empty">Prompt Repository awaiting contract templates</div>`;
  $("pee-candidates").innerHTML = candidates.length
    ? candidates.map(item => `
      <div class="api-call"><b>${item.improvementId}</b><span>${item.relatedPrompt} / ${item.currentVersion} -> ${item.candidateVersion}</span><div>${item.summary}<br />${item.expectedBenefit}<br />${item.laboratoryStatus} / ${item.commanderStatus} / ${item.productionStatus}</div></div>
    `).join("")
    : `<div class="alert-empty">No prompt improvement candidate has cleared evidence intake</div>`;
  $("pee-lineage").innerHTML = (promptEvolution.promptLineage || []).map(item => `<div class="api-call"><b>${item.promptId}</b><span>${item.origin}</span><div>Parent ${item.parentPrompt || "None"} / Children ${(item.childPrompts || []).join(", ") || "None"} / Production ${item.activeProductionVersion}</div></div>`).join("");
  $("pee-metadata").innerHTML = (promptEvolution.promptMetadata || []).map(item => `<div class="api-call"><b>${item.promptName}</b><span>${item.office} / ${item.currentStatus}</span><div>Purpose ${item.purpose}<br />Performance ${item.performanceScore} / Confidence ${Math.round((item.averageConfidence || 0) * 100)}%<br />Recommendations ${(item.relatedRecommendations || []).join(", ") || "Baseline"}</div></div>`).join("");
  $("pee-comparisons").innerHTML = (promptEvolution.comparisonEngine || []).length
    ? promptEvolution.comparisonEngine.map(item => `<div class="api-call"><b>${item.comparisonId}</b><span>${item.currentVersion} vs ${item.candidateVersion}</span><div>${item.measures.join(", ")}<br />${item.status}</div></div>`).join("")
    : `<div class="alert-empty">Comparison Engine awaiting candidate prompts</div>`;
  $("pee-lab").innerHTML = (promptEvolution.laboratoryValidationQueue || []).length
    ? promptEvolution.laboratoryValidationQueue.map(item => `<div class="api-call"><b>${item.improvementId}</b><span>${item.candidateVersion}</span><div>${item.validationPipeline.join(" -> ")}<br />${item.laboratoryStatus} / ${item.productionStatus}</div></div>`).join("")
    : `<div class="alert-empty">Laboratory Results awaiting prompt replay</div>`;
  $("pee-history").innerHTML = `
    <div class="api-call"><b>Promotion History</b><span>${(promptEvolution.promotionHistory || []).length}</span><div>${(promptEvolution.promotionHistory || []).join("<br />") || "No production promotion without Commander approval."}</div></div>
    <div class="api-call"><b>Retirement History</b><span>${(promptEvolution.retirementHistory || []).length}</span><div>${(promptEvolution.retirementHistory || []).join("<br />") || "No retired prompts."}</div></div>
    <div class="api-call"><b>Approval History</b><span>${(promptEvolution.approvalHistory || []).length}</span><div>${(promptEvolution.approvalHistory || []).join("<br />") || "Commander approval required for future promotion."}</div></div>
  `;
  $("pee-diff").innerHTML = (promptEvolution.versionDifferenceViewer || []).length
    ? promptEvolution.versionDifferenceViewer.map(item => `<div class="api-call"><b>${item.improvementId}</b><span>${item.fromVersion} -> ${item.toVersion}</span><div>${item.diffSummary}<br />Raw prompt text hidden ${item.rawPromptTextHidden ? "YES" : "NO"} / Production mutation ${item.productionMutation ? "YES" : "NO"}</div></div>`).join("")
    : `<div class="alert-empty">Version Difference Viewer awaiting candidates</div>`;
  $("pee-dependency").innerHTML = (promptEvolution.promptDependencyGraph || []).map(item => `<div class="api-call"><b>${item.promptId}</b><span>${item.office}</span><div>Depends on ${item.dependsOn.join(", ")}<br />Used by ${item.usedBy.join(", ")}</div></div>`).join("");
  $("pee-diagnostics").innerHTML = Object.entries(promptEvolution.internalDiagnostics || {}).map(([key, value]) => `<div>${label(key)}<b>${value}</b></div>`).join("");
}

function renderPromptPackageManager() {
  const manager = state.promptPackageManager;
  if (!manager || !$("ppm-summary")) return;
  $("ppm-summary").innerHTML = [
    ["Engineering Order", manager.engineeringOrder],
    ["Mode", manager.constitutionalMode],
    ["Registry Packages", (manager.packageRegistry || []).length],
    ["Installed", (manager.installedPackages || []).length],
    ["Active", (manager.activePackages || []).length],
    ["Pipeline", (manager.installationPipeline || []).length],
  ].map(([name, value]) => `<div><span>${name}</span><b>${value}</b></div>`).join("");
  $("ppm-installed").innerHTML = (manager.installedPackages || []).map(item => `
    <div class="api-call"><b>${item.packageId}</b><span>${item.deploymentStatus} / ${item.approvalStatus}</span><div>${item.packageName}<br />Prompt ${item.repositoryReference} v${item.promptVersion}<br />Checksum ${item.checksum}</div></div>
  `).join("") || `<div class="alert-empty">No installed packages</div>`;
  $("ppm-active").innerHTML = (manager.activePackages || []).map(item => `
    <div class="api-call"><b>${item.owningOffice}</b><span>${item.packageId}</span><div>${item.purpose}<br />Health ${item.packageHealth} / Version ${item.packageVersion}</div></div>
  `).join("") || `<div class="alert-empty">No active packages</div>`;
  $("ppm-offices").innerHTML = (manager.officePackageAssignment || []).map(item => `
    <div class="api-call"><b>${item.office}</b><span>${item.consumptionMode}</span><div>${item.activePackageId}<br />Package v${item.activePackageVersion} / Prompt v${item.promptVersion}<br />Environment ${item.environment}</div></div>
  `).join("");
  $("ppm-versions").innerHTML = (manager.versionGraph || []).map(item => `<div class="api-call"><b>${item.packageId}</b><span>v${item.version}</span><div>Related ${(item.relatedVersions || []).join(", ") || "None"}<br />Immutable History ${item.immutableHistory ? "YES" : "NO"}</div></div>`).join("");
  $("ppm-dependencies").innerHTML = (manager.dependencyGraph || []).map(item => `<div class="api-call"><b>${item.packageId}</b><span>Dependencies</span><div>${(item.dependencies || []).join("<br />")}</div></div>`).join("");
  $("ppm-compatibility").innerHTML = (manager.compatibilityMatrix || []).map(item => `<div class="api-call"><b>${item.packageId}</b><span>${item.compatible ? "Compatible" : "Blocked"}</span><div>${(item.checks || []).map(check => `${check.target}: ${check.status}`).join("<br />")}</div></div>`).join("");
  $("ppm-install-history").innerHTML = (manager.installationHistory || []).map(item => `<div class="api-call"><b>${item.eventId}</b><span>${item.status}</span><div>${item.packageId}<br />${item.timestamp}</div></div>`).join("");
  $("ppm-activation-history").innerHTML = (manager.activationHistory || []).map(item => `<div class="api-call"><b>${item.eventId}</b><span>${item.approvalStatus}</span><div>${item.packageId}<br />${item.timestamp}</div></div>`).join("");
  $("ppm-rollback").innerHTML = `
    <div class="api-call"><b>Rollback Manager</b><span>${manager.rollbackManager?.rollbackSupported ? "Supported" : "Unavailable"}</span><div>Commander Approval ${manager.rollbackManager?.requiresCommanderApproval ? "Required" : "Not Required"}<br />Automatic Rollback ${manager.rollbackManager?.automaticRollback ? "YES" : "NO"}</div></div>
    ${(manager.rollbackManager?.restorablePackages || []).map(item => `<div class="api-call"><b>${item.office}</b><span>${item.previousVersion}</span><div>${item.packageId}</div></div>`).join("")}
  `;
  $("ppm-integrity").innerHTML = (manager.integrityVerification || []).map(item => `<div class="api-call"><b>${item.packageId}</b><span>Verified</span><div>Checksum ${item.checksum}<br />Prompt ${item.promptHash}<br />Install ${item.installationHash}</div></div>`).join("");
  $("ppm-health").innerHTML = (manager.healthDashboard || []).map(item => `<div class="api-call"><b>${item.packageId}</b><span>${item.packageHealthScore}</span><div>Performance ${item.performance}<br />Decision Quality ${item.decisionQuality}<br />Lab ${item.laboratoryPerformance}</div></div>`).join("");
  $("ppm-lab").innerHTML = (manager.laboratoryResults || []).map(item => `<div class="api-call"><b>${item.packageId}</b><span>${item.compatibilityValidation}</span><div>Replays ${item.replayCount} / Counterfactual ${item.counterfactualReports}<br />Review ${item.commanderReview}</div></div>`).join("");
  $("ppm-timeline").innerHTML = (manager.deploymentTimeline || []).map(item => `<div class="api-call"><b>${item.packageId}</b><span>${item.event}</span><div>${item.office}<br />${item.timestamp}</div></div>`).join("");
  $("ppm-diagnostics").innerHTML = `
    ${Object.entries(manager.lawVII || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${typeof value === "boolean" ? (value ? "YES" : "NO") : value}</b></div>`).join("")}
    ${Object.entries(manager.internalDiagnostics || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("")}
  `;
}

function renderStrategyPackageManager() {
  const manager = state.strategyPackageManager;
  if (!manager || !$("spm-summary")) return;
  $("spm-summary").innerHTML = [
    ["Engineering Order", manager.engineeringOrder],
    ["Mode", manager.constitutionalMode],
    ["Registry Packages", (manager.strategyPackageRegistry || []).length],
    ["Installed", (manager.installedPackages || []).length],
    ["Active", (manager.activePackages || []).length],
    ["Pipeline", (manager.installationPipeline || []).length],
  ].map(([name, value]) => `<div><span>${name}</span><b>${value}</b></div>`).join("");
  $("spm-installed").innerHTML = (manager.installedPackages || []).map(item => `
    <div class="api-call"><b>${item.packageId}</b><span>${item.deploymentStatus} / ${item.approvalStatus}</span><div>${item.strategyName} v${item.strategyVersion}<br />${item.strategyFamily} / ${item.currentPortfolioUsage}<br />Checksum ${item.checksum}</div></div>
  `).join("") || `<div class="alert-empty">No installed strategy packages</div>`;
  $("spm-active").innerHTML = (manager.activePackages || []).map(item => `
    <div class="api-call"><b>${item.strategyName}</b><span>${item.packageId}</span><div>${item.investmentThesis}<br />Health ${item.packageHealth} / Package v${item.packageVersion}</div></div>
  `).join("") || `<div class="alert-empty">No active strategy packages</div>`;
  $("spm-assignments").innerHTML = `
    <div class="api-call"><b>Analyst</b><span>${manager.analystStrategyAssignment?.consumptionMode || "Pending"}</span><div>${manager.analystStrategyAssignment?.activeStrategyPackageId || "No active package"}<br />${manager.analystStrategyAssignment?.activeStrategyName || ""}</div></div>
    ${(manager.strategyAssignment || []).map(item => `<div class="api-call"><b>${item.assignment}</b><span>${item.strategyName}</span><div>${item.strategyPackageId}<br />Eligible ${item.eligibleForAnalystUse ? "YES" : "NO"} / ${item.environment}</div></div>`).join("")}
  `;
  $("spm-versions").innerHTML = (manager.versionGraph || []).map(item => `<div class="api-call"><b>${item.packageId}</b><span>v${item.strategyVersion}</span><div>Related ${(item.relatedVersions || []).join(", ") || "None"}<br />Immutable Lineage ${item.immutableLineage ? "YES" : "NO"}</div></div>`).join("");
  $("spm-dependencies").innerHTML = (manager.dependencyGraph || []).map(item => `<div class="api-call"><b>${item.packageId}</b><span>Dependencies</span><div>${(item.dependencies || []).join("<br />")}</div></div>`).join("");
  $("spm-compatibility").innerHTML = (manager.compatibilityMatrix || []).map(item => `<div class="api-call"><b>${item.packageId}</b><span>${item.compatible ? "Compatible" : "Blocked"}</span><div>${(item.checks || []).map(check => `${check.target}: ${check.status}`).join("<br />")}</div></div>`).join("");
  $("spm-install-history").innerHTML = (manager.installationHistory || []).map(item => `<div class="api-call"><b>${item.eventId}</b><span>${item.status}</span><div>${item.packageId}<br />${item.timestamp}</div></div>`).join("");
  $("spm-activation-history").innerHTML = (manager.activationHistory || []).map(item => `<div class="api-call"><b>${item.eventId}</b><span>${item.approvalStatus}</span><div>${item.packageId}<br />${item.timestamp}</div></div>`).join("");
  $("spm-rollback").innerHTML = `
    <div class="api-call"><b>Rollback Manager</b><span>${manager.rollbackManager?.rollbackSupported ? "Supported" : "Unavailable"}</span><div>Commander Approval ${manager.rollbackManager?.requiresCommanderApproval ? "Required" : "Not Required"}<br />Automatic Rollback ${manager.rollbackManager?.automaticRollback ? "YES" : "NO"}</div></div>
    ${(manager.rollbackManager?.restorablePackages || []).map(item => `<div class="api-call"><b>${item.strategyName}</b><span>${item.previousVersion}</span><div>${item.packageId}<br />Compatibility ${item.previousCompatibilityState}</div></div>`).join("")}
  `;
  $("spm-integrity").innerHTML = (manager.integrityDashboard || []).map(item => `<div class="api-call"><b>${item.packageId}</b><span>Verified</span><div>Checksum ${item.checksum}<br />Strategy ${item.strategyHash}<br />Deploy ${item.deploymentHash}</div></div>`).join("");
  $("spm-health").innerHTML = (manager.healthDashboard || []).map(item => `<div class="api-call"><b>${item.packageId}</b><span>${item.healthScore}</span><div>Return ${item.return} / Sharpe ${item.sharpeRatio}<br />Win ${item.winRate}% / Drawdown ${item.drawdown}<br />Decision Quality ${item.decisionQuality}</div></div>`).join("");
  $("spm-lab").innerHTML = (manager.laboratoryResults || []).map(item => `<div class="api-call"><b>${item.packageId}</b><span>${item.replayValidation}</span><div>Counterfactual ${item.counterfactualValidation}<br />Performance Comparisons ${item.performanceComparison}<br />Review ${item.commanderReview}</div></div>`).join("");
  $("spm-replay").innerHTML = Object.entries(manager.replayStatistics || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
  $("spm-counterfactual").innerHTML = (manager.counterfactualReports || []).length
    ? manager.counterfactualReports.map(item => `<div class="api-call"><b>${item.performanceComparisonId || "Counterfactual"}</b><span>${item.alpha || 0}</span><div>Outcome ${item.experimentOutcome || 0} / Risk ${item.risk || 0}</div></div>`).join("")
    : `<div class="alert-empty">Counterfactual Reports awaiting strategy experiments</div>`;
  $("spm-regimes").innerHTML = (manager.marketRegimeAssignment || []).map(item => `<div class="api-call"><b>${item.packageId}</b><span>${item.suitability}</span><div>Current ${item.currentMarketRegime}<br />Supports ${(item.supportedMarketRegimes || []).join(", ")}</div></div>`).join("");
  $("spm-timeline").innerHTML = (manager.deploymentTimeline || []).map(item => `<div class="api-call"><b>${item.packageId}</b><span>${item.event}</span><div>${item.strategy}<br />${item.timestamp}</div></div>`).join("");
  $("spm-diagnostics").innerHTML = `
    ${Object.entries(manager.lawVII || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${typeof value === "boolean" ? (value ? "YES" : "NO") : value}</b></div>`).join("")}
    ${Object.entries(manager.internalDiagnostics || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("")}
  `;
}

function renderEnterpriseConfigurationRegistry() {
  const registry = state.enterpriseConfigurationRegistry;
  if (!registry || !$("ecr-summary")) return;
  $("ecr-summary").innerHTML = [
    ["Engineering Order", registry.engineeringOrder],
    ["Mode", registry.constitutionalMode],
    ["Version", registry.enterpriseConfigurationVersion],
    ["Environment", registry.currentEnvironment],
    ["Entries", (registry.configurationRegistry || []).length],
    ["Categories", (registry.categories || []).length],
    ["Registry Hash", registry.registryHash],
  ].map(([name, value]) => `<div><span>${name}</span><b>${value}</b></div>`).join("");
  $("ecr-history").innerHTML = (registry.configurationHistory || []).slice(0, 24).map(item => `<div class="api-call"><b>${item.configurationId}</b><span>${item.currentVersion}</span><div>Versions ${(item.versions || []).join(", ")} / Immutable ${item.immutable ? "YES" : "NO"}</div></div>`).join("");
  $("ecr-versions").innerHTML = (registry.versionGraph || []).slice(0, 24).map(item => `<div class="api-call"><b>${item.configurationId}</b><span>${item.category}</span><div>Version ${item.version}<br />Production ${item.production ? "YES" : "NO"}</div></div>`).join("");
  $("ecr-dependencies").innerHTML = (registry.dependencyGraph || []).slice(0, 24).map(item => `<div class="api-call"><b>${item.configurationId}</b><span>Dependencies</span><div>${(item.dependencies || []).join("<br />") || "None"}<br />Circular ${item.circularDependency ? "YES" : "NO"}</div></div>`).join("");
  $("ecr-environments").innerHTML = (registry.environmentManager?.profiles || []).map(item => `<div class="api-call"><b>${item.environment}</b><span>${item.status}</span><div>Inherits ${item.inheritsFrom || "None"}</div></div>`).join("");
  $("ecr-validation").innerHTML = Object.entries(registry.validationDashboard || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
  $("ecr-promotion").innerHTML = (registry.promotionQueue || []).length
    ? registry.promotionQueue.map(item => `<div class="api-call"><b>${item.configurationId}</b><span>${item.state}</span><div>${item.category}<br />${item.commanderApproval}</div></div>`).join("")
    : `<div class="alert-empty">Promotion Queue empty; Commander approval required for future changes.</div>`;
  $("ecr-rollback").innerHTML = `
    <div class="api-call"><b>Rollback Manager</b><span>${registry.rollbackManager?.rollbackSupported ? "Supported" : "Unavailable"}</span><div>Version ${registry.rollbackManager?.activeVersion}<br />Environment ${registry.rollbackManager?.activeEnvironment}<br />Commander Approval ${registry.rollbackManager?.requiresCommanderApproval ? "Required" : "Not Required"}</div></div>
    ${(registry.rollbackManager?.restorableConfigurations || []).slice(0, 10).map(item => `<div class="api-call"><b>${item.configurationId}</b><span>${item.version}</span><div>${item.environment}</div></div>`).join("")}
  `;
  $("ecr-diff").innerHTML = (registry.configurationDiffViewer || []).map(item => `<div class="api-call"><b>${item.configurationId}</b><span>${item.changed ? "Changed" : "Default"}</span><div>Default ${item.defaultValue}<br />Current ${item.currentValue}</div></div>`).join("");
  $("ecr-search").innerHTML = (registry.configurationSearch || []).slice(0, 24).map(item => `<div class="api-call"><b>${item.name}</b><span>${item.category} / ${item.state}</span><div>${item.configurationId}<br />Environment ${item.environment} / Version ${item.version}</div></div>`).join("");
  $("ecr-health").innerHTML = Object.entries(registry.configurationHealth || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
  $("ecr-audit").innerHTML = (registry.auditHistory || []).map(item => `<div class="api-call"><b>${item.auditReference}</b><span>${item.state}</span><div>${item.configurationId}<br />${item.category} / ${item.commanderApproval}</div></div>`).join("");
  $("ecr-diagnostics").innerHTML = `
    ${Object.entries(registry.lawVII || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${typeof value === "boolean" ? (value ? "YES" : "NO") : value}</b></div>`).join("")}
    ${Object.entries(registry.internalDiagnostics || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("")}
  `;
}

function renderEnterpriseHealthMonitor() {
  const monitor = state.enterpriseHealthMonitor;
  if (!monitor || !$("ehm-summary")) return;
  $("ehm-summary").innerHTML = [
    ["Engineering Order", monitor.engineeringOrder],
    ["Mode", monitor.constitutionalMode],
    ["Health Score", monitor.enterpriseHealthScore],
    ["Status", monitor.status],
    ["Trend", monitor.trend],
    ["Confidence", `${Math.round(Number(monitor.confidence || 0) * 100)}%`],
    ["Current Alerts", (monitor.currentAlerts || []).length],
  ].map(([name, value]) => `<div><span>${name}</span><b>${value}</b></div>`).join("");
  $("ehm-components").innerHTML = (monitor.componentHealth || []).map(item => `
    <div class="api-call"><b>${item.component}</b><span>${item.state} / ${item.healthScore}</span><div>${(item.evidence || []).join("<br />")}</div></div>
  `).join("");
  $("ehm-dependencies").innerHTML = (monitor.dependencyGraph || []).map(item => `
    <div class="api-call"><b>${item.dependencyChain}</b><span>${item.status}</span><div>Health ${item.healthScore}</div></div>
  `).join("");
  $("ehm-alerts").innerHTML = (monitor.alertHistory || []).length
    ? monitor.alertHistory.map(item => `<div class="api-call"><b>${item.component}</b><span>${item.severity} / ${item.resolutionStatus}</span><div>${item.description}<br />${(item.evidence || []).join("<br />")}<br />${item.recommendedAction}</div></div>`).join("")
    : `<div class="alert-empty">No Enterprise Health Monitor alerts</div>`;
  $("ehm-calculations").innerHTML = Object.entries(monitor.healthCalculations || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
  $("ehm-telemetry").innerHTML = Object.entries(monitor.telemetryViewer || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
  $("ehm-timeline").innerHTML = (monitor.healthTimeline || []).map(item => `<div class="api-call"><b>${item.timestamp}</b><span>${item.state}</span><div>Score ${item.enterpriseHealthScore}<br />Alerts ${item.alertCount}</div></div>`).join("");
  $("ehm-forecasts").innerHTML = (monitor.forecastModels || []).map(item => `<div class="api-call"><b>${item.forecast}</b><span>${item.risk}</span><div>${item.basis}</div></div>`).join("");
  $("ehm-runtime").innerHTML = Object.entries(monitor.runtimeStatistics || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
  $("ehm-infrastructure").innerHTML = Object.entries(monitor.infrastructureMetrics || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
  $("ehm-validation").innerHTML = (monitor.validationFailures || []).length
    ? monitor.validationFailures.map(item => `<div class="api-call"><b>${item.component}</b><span>${item.state}</span><div>Health ${item.healthScore}</div></div>`).join("")
    : `<div class="alert-empty">No validation failures</div>`;
  $("ehm-provider").innerHTML = Object.entries(monitor.providerDiagnostics || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
  $("ehm-database").innerHTML = Object.entries(monitor.databaseDiagnostics || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
  $("ehm-rules").innerHTML = (monitor.internalHealthRules || []).map(rule => `<div class="api-call"><b>Health Rule</b><span>Active</span><div>${rule}</div></div>`).join("");
  $("ehm-config").innerHTML = Object.entries(monitor.healthConfiguration || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${Array.isArray(value) ? value.join(", ") : value}</b></div>`).join("");
  $("ehm-diagnostics").innerHTML = `
    ${Object.entries(monitor.lawVII || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${typeof value === "boolean" ? (value ? "YES" : "NO") : value}</b></div>`).join("")}
    ${Object.entries(monitor.internalDiagnostics || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("")}
  `;
}

function renderEnterpriseFailureRecoveryFramework() {
  const recovery = state.enterpriseFailureRecoveryFramework;
  if (!recovery || !$("efr-summary")) return;
  $("efr-summary").innerHTML = [
    ["Engineering Order", recovery.engineeringOrder],
    ["Mode", recovery.constitutionalMode],
    ["Safe State", recovery.safeEnterpriseState?.status],
    ["Active Failures", recovery.recoveryDashboard?.activeFailures],
    ["Validation", recovery.recoveryDashboard?.validationStatus],
    ["Recovery Action", recovery.recoveryDashboard?.activeRecoveryAction],
    ["Commander Action", recovery.commanderRecoverySummary?.requiredCommanderAction],
  ].map(([name, value]) => `<div><span>${name}</span><b>${value}</b></div>`).join("");
  $("efr-failures").innerHTML = (recovery.failureHistory || []).length
    ? recovery.failureHistory.map(item => `<div class="api-call"><b>${item.failureId}</b><span>${item.component} / ${item.severity}</span><div>${item.failureType}<br />${item.exceptionDetails}<br />Plan ${item.recoveryPlan}</div></div>`).join("")
    : `<div class="alert-empty">No failures recorded</div>`;
  $("efr-recoveries").innerHTML = (recovery.recoveryHistory || []).length
    ? recovery.recoveryHistory.map(item => `<div class="api-call"><b>${item.failure}</b><span>${item.classification}</span><div>${(item.recoveryActions || []).join("<br />")}<br />${item.finalStatus}</div></div>`).join("")
    : `<div class="alert-empty">No recoveries recorded</div>`;
  $("efr-timeline").innerHTML = (recovery.failureTimeline || []).length
    ? recovery.failureTimeline.map(item => `<div class="api-call"><b>${item.timestamp}</b><span>${item.event}</span><div>${item.component}<br />${item.status}</div></div>`).join("")
    : `<div class="alert-empty">Failure Timeline clear</div>`;
  $("efr-dashboard").innerHTML = Object.entries(recovery.recoveryDashboard || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
  $("efr-validation").innerHTML = Object.entries(recovery.recoveryValidation || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
  $("efr-checkpoints").innerHTML = (recovery.checkpointBrowser || []).map(item => `<div class="api-call"><b>${item.checkpoint}</b><span>${item.status}</span><div>${item.timestamp}<br />Reference ${item.reference}</div></div>`).join("");
  $("efr-rules").innerHTML = (recovery.recoveryRules || []).map(rule => `<div class="api-call"><b>Recovery Rule</b><span>Active</span><div>${rule}</div></div>`).join("");
  $("efr-statistics").innerHTML = Object.entries(recovery.recoveryStatistics || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
  $("efr-forecasts").innerHTML = (recovery.recoveryForecasts || []).map(item => `<div class="api-call"><b>${item.forecast}</b><span>${item.risk}</span><div>${item.basis}</div></div>`).join("");
  $("efr-chaos").innerHTML = (recovery.chaosTestingControls || []).map(item => `<div class="api-call"><b>${item.simulation}</b><span>${item.mode}</span><div>Production Risk ${item.productionRisk}<br />Commander Approval ${item.commanderApprovalRequired ? "Required" : "Not Required"}</div></div>`).join("");
  $("efr-classification").innerHTML = `
    <div><span>Known Classifications</span><b>${(recovery.failureClassification?.knownClassifications || []).length}</b></div>
    <div><span>Active Classifications</span><b>${(recovery.failureClassification?.activeClassifications || []).join(", ") || "None"}</b></div>
    <div><span>Unknown Failures</span><b>${recovery.failureClassification?.unknownFailures || 0}</b></div>
  `;
  $("efr-diagnostics").innerHTML = `
    ${Object.entries(recovery.recoveryDiagnostics || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${Array.isArray(value) ? value.join(", ") || "None" : value}</b></div>`).join("")}
    ${Object.entries(recovery.internalDiagnostics || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("")}
  `;
  $("efr-dependencies").innerHTML = (recovery.dependencyFailures || []).length
    ? recovery.dependencyFailures.map(item => `<div class="api-call"><b>${item.dependencyChain}</b><span>${item.status}</span><div>Health ${item.healthScore}</div></div>`).join("")
    : `<div class="alert-empty">No dependency failures</div>`;
  $("efr-infrastructure").innerHTML = Object.entries(recovery.infrastructureDiagnostics || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
  $("efr-boundaries").innerHTML = (recovery.transactionBoundaries || []).map(item => `<div class="api-call"><b>${item.operation}</b><span>${item.boundary}</span><div>Partial Success ${item.partialSuccessAllowed}</div></div>`).join("");
  $("efr-quarantine").innerHTML = Object.entries(recovery.quarantine || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("");
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

function renderMarketContextIntegrationEngine() {
  const marketContext = state.marketContextIntegrationEngine;
  if (!marketContext || !$("mcie-summary")) return;
  const latest = marketContext.latestMarketContext || {};
  const layers = marketContext.normalizedMarketLayers || {};
  $("mcie-summary").innerHTML = [
    ["Engineering Order", marketContext.engineeringOrder],
    ["Mode", marketContext.constitutionalMode],
    ["Latest Snapshot", latest.snapshotId || "None"],
    ["Market Session", latest.marketSession || "Standing By"],
    ["Market Regime", latest.marketRegime || "UNKNOWN"],
    ["Overall Trend", latest.overallTrend || "UNKNOWN"],
    ["Volatility", latest.volatilityState || "UNKNOWN"],
    ["Confidence", `${Math.round(Number(latest.confidence || 0) * 100)}%`],
  ].map(([name, value]) => `<div><span>${name}</span><b>${value}</b></div>`).join("");
  $("mcie-repository").innerHTML = (marketContext.marketContextRepository || []).map(item => `
    <div class="api-call"><b>${item.snapshotId}</b><span>${item.marketSession} / ${item.marketRegime}</span><div>Trend ${item.overallTrend} / Volatility ${item.volatilityState} / Liquidity ${item.liquidityState}<br />Symbols ${(item.relatedSymbols || []).join(", ")} / Sectors ${(item.relatedSectors || []).join(", ")}<br />Evidence ${(item.supportingEvidence || []).join("; ")}</div></div>
  `).join("") || `<div class="alert-empty">Market Context Repository awaiting snapshots</div>`;
  $("mcie-layers").innerHTML = Object.entries(layers).map(([name, value]) => `
    <div class="api-call"><b>${label(name)}</b><span>${value?.quality?.validationStatus || "VALID"}</span><div>${Object.entries(value || {}).filter(([key]) => key !== "quality").slice(0, 8).map(([key, field]) => `${label(key)}: ${Array.isArray(field) ? field.join(", ") : typeof field === "object" ? JSON.stringify(field) : field}`).join("<br />")}</div></div>
  `).join("");
  $("mcie-regime").innerHTML = Object.entries(layers.marketRegimeClassification || {}).map(([key, value]) => `<div>${label(key)}<b>${value}</b></div>`).join("");
  $("mcie-sector").innerHTML = Object.entries(layers.sectorLeadership || {}).filter(([key]) => key !== "quality").map(([key, value]) => `<div>${label(key)}<b>${Array.isArray(value) ? value.join(", ") : value}</b></div>`).join("");
  $("mcie-portfolio").innerHTML = Object.entries(layers.portfolioContext || {}).filter(([key]) => key !== "quality").map(([key, value]) => `<div>${label(key)}<b>${Array.isArray(value) ? value.length : value}</b></div>`).join("");
  $("mcie-cache").innerHTML = Object.entries(marketContext.cacheStatistics || {}).map(([key, value]) => `<div>${label(key)}<b>${value}</b></div>`).join("");
  $("mcie-api").innerHTML = Object.entries(marketContext.apiConsumption || {}).map(([key, value]) => `<div>${label(key)}<b>${value}</b></div>`).join("");
  $("mcie-freshness").innerHTML = Object.entries(marketContext.dataFreshness || {}).map(([key, value]) => `<div>${label(key)}<b>${value}</b></div>`).join("");
  $("mcie-source-health").innerHTML = Object.entries(marketContext.sourceHealth || {}).map(([name, value]) => `<div class="api-call"><b>${label(name)}</b><span>${value.validationStatus}</span><div>Source ${value.source}<br />Confidence ${Math.round(Number(value.confidence || 0) * 100)}% / Freshness ${value.freshness} / Completeness ${Math.round(Number(value.completeness || 0) * 100)}%</div></div>`).join("");
  $("mcie-normalization").innerHTML = (marketContext.normalizationRules || []).map(rule => `<div class="api-call"><b>Normalization Rule</b><span>Required</span><div>${rule}</div></div>`).join("");
  $("mcie-diagnostics").innerHTML = Object.entries(marketContext.internalDiagnostics || {}).map(([key, value]) => `<div>${label(key)}<b>${value}</b></div>`).join("");
}

function renderMarketDataProviderAbstractionLayer() {
  const provider = state.marketDataProviderAbstractionLayer;
  if (!provider || !$("mdpa-summary")) return;
  $("mdpa-summary").innerHTML = [
    ["Engineering Order", provider.engineeringOrder],
    ["Mode", provider.constitutionalMode],
    ["Primary Provider", provider.commanderVisibility?.currentPrimaryProvider || "None"],
    ["Fallback Provider", provider.commanderVisibility?.activeFallbackProvider || "None"],
    ["Provider Health", provider.commanderVisibility?.providerHealth || "Unknown"],
    ["Provider Cost Today", money(provider.commanderVisibility?.providerCostToday || 0, 4)],
    ["Rate Limit", provider.commanderVisibility?.rateLimitStatus || "Unknown"],
    ["Cache Hit Rate", `${Math.round(Number(provider.commanderVisibility?.cacheHitRate || 0) * 100)}%`],
  ].map(([name, value]) => `<div><span>${name}</span><b>${value}</b></div>`).join("");
  $("mdpa-registry").innerHTML = (provider.providerRegistry || []).map(item => `
    <div class="api-call"><b>${item.providerId}</b><span>${item.providerName} / ${item.providerType} / ${item.healthStatus}</span><div>Enabled ${item.enabled ? "YES" : "NO"} / Auth ${item.authenticationStatus} / Commander ${item.commanderApprovalStatus}<br />Default ${item.defaultPriority} / Fallback ${item.fallbackPriority}</div></div>
  `).join("");
  $("mdpa-config").innerHTML = Object.entries(provider.providerConfiguration || {}).map(([key, value]) => `<div>${label(key)}<b>${Array.isArray(value) ? value.join(", ") : typeof value === "object" ? Object.keys(value).join(", ") : value}</b></div>`).join("");
  $("mdpa-capabilities").innerHTML = (provider.capabilityMatrix || []).map(item => `<div class="api-call"><b>${item.providerId}</b><span>Capability Matrix</span><div>${Object.entries(item).filter(([key]) => key !== "providerId").map(([key, value]) => `${label(key)}: ${value}`).join("<br />")}</div></div>`).join("");
  $("mdpa-health").innerHTML = (provider.providerHealthDashboard || []).map(item => `<div>${item.providerId}<b>${item.healthStatus} / ${item.authenticationStatus}</b></div>`).join("");
  $("mdpa-calls").innerHTML = (provider.callHistory || []).map(item => `<div class="api-call"><b>${item.auditId}</b><span>${item.provider} / ${item.endpoint}</span><div>Cost ${money(item.actualCost, 4)} / Credit ${item.creditGovernorApproval} / Cache ${item.cacheHitOrMiss}<br />Workflow ${item.workflowId || "None"} / Decision ${item.decisionObjectId || "None"}</div></div>`).join("");
  $("mdpa-costs").innerHTML = (provider.costHistory || []).map(item => `<div>${item.provider} ${item.endpoint}<b>${money(item.actualCostUsd, 4)}</b></div>`).join("");
  $("mdpa-rates").innerHTML = (provider.rateLimitStatus || []).map(item => `<div>Remaining Requests<b>${item.remainingRequests} / ${item.cooldownStatus}</b></div>`).join("");
  $("mdpa-cache").innerHTML = Object.entries(provider.cacheStatistics || {}).map(([key, value]) => `<div>${label(key)}<b>${value}</b></div>`).join("");
  $("mdpa-raw").innerHTML = (provider.rawPayloadViewer || []).map(item => `<div class="api-call"><b>${item.rawPayloadReference}</b><span>${item.storageMode}</span><div>Raw payload archived by reference for audit and replay.</div></div>`).join("");
  $("mdpa-normalization").innerHTML = Object.entries(provider.normalizationDiagnostics || {}).map(([key, value]) => `<div>${label(key)}<b>${value}</b></div>`).join("");
  $("mdpa-failover").innerHTML = (provider.failoverEvents || []).map(item => `<div class="api-call"><b>${item.eventId}</b><span>${item.primaryProvider} -> ${item.fallbackProvider}</span><div>${item.reason}<br />Executed ${item.executed ? "YES" : "NO"} / Audited ${item.audited ? "YES" : "NO"}</div></div>`).join("");
  $("mdpa-replay").innerHTML = Object.entries(provider.replayModeTools || {}).map(([key, value]) => `<div>${label(key)}<b>${value}</b></div>`).join("");
  $("mdpa-controls").innerHTML = `
    <div class="api-call"><b>Mock Provider Controls</b><span>${provider.mockProviderControls?.enabled ? "Enabled" : "Disabled"}</span><div>${(provider.mockProviderControls?.patterns || []).join(", ")}</div></div>
    <div class="api-call"><b>Synthetic Provider Controls</b><span>${provider.syntheticProviderControls?.enabled ? "Enabled" : "Disabled"}</span><div>${(provider.syntheticProviderControls?.patterns || []).join(", ")}</div></div>
  `;
  $("mdpa-auth").innerHTML = Object.entries(provider.authenticationStatus || {}).map(([key, value]) => `<div>${key}<b>${value}</b></div>`).join("");
  $("mdpa-diagnostics").innerHTML = Object.entries(provider.internalDiagnostics || {}).map(([key, value]) => `<div>${label(key)}<b>${value}</b></div>`).join("");
}

function renderDailyEnterpriseLearningPipeline() {
  const pipeline = state.dailyEnterpriseLearningPipeline;
  if (!pipeline || !$("dlp-records")) return;
  const record = pipeline.activeDailyLearningRecord || {};
  $("dlp-records").innerHTML = (pipeline.dailyLearningRecords || []).map(item => `
    <div class="api-call"><b>${item.learningSessionId}</b><span>${item.tradingDate}</span><div>Workflows ${item.workflowCount} / Decisions ${item.decisionObjectCount} / Truth ${item.performanceTruthCount}<br />Recommendations ${item.recommendationsGenerated} / Prompt Candidates ${item.promptCandidates} / Capability Change ${item.enterpriseCapabilityChange}<br />${item.commanderSummary}</div></div>
  `).join("");
  $("dlp-timeline").innerHTML = (pipeline.learningTimeline || []).map(item => `<div class="api-call"><b>${item.stage}</b><span>${item.status}</span><div>Replayable ${item.replayable ? "YES" : "NO"}</div></div>`).join("");
  $("dlp-backlog").innerHTML = (pipeline.improvementBacklog || []).length
    ? pipeline.improvementBacklog.map(item => `<div class="api-call"><b>#${item.rank} ${item.category}</b><span>${item.priority} / ${item.source}</span><div>${item.title}<br />${item.status}</div></div>`).join("")
    : `<div class="alert-empty">Improvement Backlog empty</div>`;
  $("dlp-recommendations").innerHTML = (pipeline.recommendationQueue || []).length
    ? pipeline.recommendationQueue.map(item => `<div class="api-call"><b>${item.recommendationId}</b><span>${item.source}</span><div>${item.title}<br />${item.laboratoryStatus} / ${item.commanderStatus} / ${item.productionStatus}</div></div>`).join("")
    : `<div class="alert-empty">Recommendation Queue waiting for evidence</div>`;
  $("dlp-validation").innerHTML = (pipeline.validationQueue || []).length
    ? pipeline.validationQueue.map(item => `<div class="api-call"><b>${item.validationId}</b><span>${item.source}</span><div>${item.title}<br />${item.validationStatus} / ${item.productionStatus}</div></div>`).join("")
    : `<div class="alert-empty">Validation Queue empty</div>`;
  $("dlp-promotion").innerHTML = (pipeline.promotionQueue || []).length
    ? pipeline.promotionQueue.map(item => `<div class="api-call"><b>${item.promotionId}</b><span>${item.candidateType}</span><div>${item.candidateId}<br />${item.commanderStatus} / ${item.productionStatus} / Auto Deploy ${item.automaticDeployment ? "YES" : "NO"}</div></div>`).join("")
    : `<div class="alert-empty">Promotion Queue empty; Commander approval required before production.</div>`;
  $("dlp-capability").innerHTML = `
    <div><span>Capability Score</span><b>${pipeline.enterpriseCapabilityIndex?.score || 0}</b></div>
    <div><span>Trend</span><b>${pipeline.enterpriseCapabilityIndex?.trend || "BASELINE"}</b></div>
    ${Object.entries(pipeline.enterpriseCapabilityIndex?.dimensions || {}).map(([key, value]) => `<div><span>${label(key)}</span><b>${value}</b></div>`).join("")}
  `;
  $("dlp-knowledge").innerHTML = Object.entries(pipeline.knowledgeGrowthMetrics || {}).map(([key, value]) => `<div>${label(key)}<b>${value}</b></div>`).join("");
  const briefing = pipeline.commanderBriefing || {};
  $("dlp-briefing").innerHTML = `
    <div class="api-call"><b>${briefing.briefingId || "Commander Briefing"}</b><span>Prepared</span><div>${briefing.enterpriseSummary || ""}<br />${briefing.tradingSummary || ""}<br />${briefing.learningSummary || ""}</div></div>
    <div class="api-call"><b>Action Items</b><span>Commander</span><div>${(briefing.commanderActionItems || []).join("<br />")}</div></div>
  `;
  $("dlp-academy").innerHTML = Object.entries(pipeline.academyHandoff || {}).map(([key, value]) => `<div class="api-call"><b>${label(key)}</b><span>Academy</span><div>${Array.isArray(value) ? value.join("<br />") : typeof value === "object" ? JSON.stringify(value) : value}</div></div>`).join("");
  $("dlp-memory").innerHTML = Object.entries(pipeline.longTermEnterpriseMemory || {}).map(([key, value]) => `<div>${label(key)}<b>${Array.isArray(value) ? value.length : typeof value === "object" ? Object.keys(value).length : value}</b></div>`).join("");
  $("dlp-orchestrator").innerHTML = Object.entries(pipeline.learningOrchestrator || {}).map(([key, value]) => `<div>${label(key)}<b>${value}</b></div>`).join("");
  $("dlp-diagnostics").innerHTML = Object.entries(pipeline.pipelineDiagnostics || {}).map(([key, value]) => `<div>${label(key)}<b>${value}</b></div>`).join("");
  $("dlp-statistics").innerHTML = Object.entries(pipeline.internalStatistics || {}).map(([key, value]) => `<div>${label(key)}<b>${value}</b></div>`).join("");
  $("dlp-logs").innerHTML = (pipeline.performanceLogs || []).map(log => `<div class="api-call"><b>Performance Log</b><span>Deterministic</span><div>${log}</div></div>`).join("");
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

function renderEnterpriseLearningEngine() {
  const learning = state.enterpriseLearningEngine;
  if (!learning || !$("ele-metrics")) return;
  const observations = learning.observations || [];
  const recommendations = learning.recommendations || [];
  const backlog = learning.improvementBacklog || [];
  const gaps = learning.knowledgeGaps || [];
  $("ele-metrics").innerHTML = Object.entries(learning.metrics || {}).map(([key, value]) => `<div>${label(key)}<b>${value}</b></div>`).join("");
  $("ele-observations").innerHTML = observations.length
    ? observations.slice(-8).reverse().map(item => `
      <div class="api-call"><b>${item.observationId}</b><span>${item.workflowId} / ${item.decisionObjectId}</span><div>${item.category.join(", ")}<br />Observed ${item.observedOutcome} / Expected ${item.expectedOutcome} / Delta ${item.difference}<br />${item.suggestedImprovement}</div></div>
    `).join("")
    : `<div class="alert-empty">Observation Database standing by for completed workflows</div>`;
  $("ele-recommendations").innerHTML = recommendations.length
    ? recommendations.map(item => `
      <div class="api-call"><b>${item.recommendationId}</b><span>${item.category} / ${item.priority}</span><div>${item.title}<br />Evidence ${item.evidenceStrength} / Confidence ${Math.round((item.confidence || 0) * 100)}%<br />${item.laboratoryStatus} / ${item.commanderApprovalStatus} / ${item.productionStatus}</div></div>
    `).join("")
    : `<div class="alert-empty">Recommendation Database awaiting sufficient evidence</div>`;
  $("ele-backlog").innerHTML = backlog.length
    ? backlog.map(item => `<div class="api-call"><b>#${item.rank} ${item.recommendationId}</b><span>${item.priority}</span><div>${item.title}<br />${item.laboratoryStatus} / ${item.commanderApprovalStatus} / ${item.productionStatus}</div></div>`).join("")
    : `<div class="alert-empty">Improvement Backlog empty</div>`;
  $("ele-gaps").innerHTML = gaps.length
    ? gaps.map(item => `<div class="api-call"><b>${item.gapId}</b><span>${item.priority}</span><div>${item.title}<br />${item.summary}<br />${item.acquisitionStatus}</div></div>`).join("")
    : `<div class="alert-empty">Knowledge Gap Detection clear</div>`;
  $("ele-thresholds").innerHTML = Object.entries(learning.recommendationThresholds || {}).map(([key, value]) => `<div>${label(key)}<b>${value}</b></div>`).join("");
  $("ele-rules").innerHTML = (learning.learningRules || []).map(item => `<div class="api-call"><b>Learning Rule</b><span>Advisory Only</span><div>${item}</div></div>`).join("");
  $("ele-diagnostics").innerHTML = Object.entries(learning.internalDiagnostics || {}).map(([key, value]) => `<div>${label(key)}<b>${value}</b></div>`).join("");
}

function renderHistorianRecommendationEngine() {
  const historian = state.historianRecommendationEngine;
  if (!historian || !$("hre-metrics")) return;
  const patterns = historian.historicalPatternDatabase || [];
  const recommendations = historian.recommendationDatabase || [];
  const lessons = historian.institutionalLessonLibrary || [];
  const gaps = historian.knowledgeGapReports || [];
  $("hre-metrics").innerHTML = Object.entries(historian.recommendationStatistics || {}).map(([key, value]) => `<div>${label(key)}<b>${value}</b></div>`).join("");
  $("hre-patterns").innerHTML = patterns.length
    ? patterns.map(item => `
      <div class="api-call"><b>${item.patternId}</b><span>${item.category} / ${item.evidenceStrength}</span><div>${item.summary}<br />Frequency ${item.historicalFrequency} / Success ${item.historicalSuccessRate}% / Confidence ${Math.round((item.confidenceScore || 0) * 100)}%<br />Workflows ${(item.supportingWorkflows || []).join(", ") || "Awaiting repeated evidence"}</div></div>
    `).join("")
    : `<div class="alert-empty">Historical Pattern Database standing by</div>`;
  $("hre-recommendations").innerHTML = recommendations.length
    ? recommendations.map(item => `
      <div class="api-call"><b>${item.recommendationId}</b><span>${(item.category || []).join(", ")} / ${item.priority}</span><div>${item.summary}<br />${item.detailedExplanation}<br />${item.laboratoryStatus} / ${item.commanderStatus} / ${item.productionStatus}</div></div>
    `).join("")
    : `<div class="alert-empty">Recommendation Database waiting for accumulated historical evidence</div>`;
  $("hre-lessons").innerHTML = lessons.length
    ? lessons.map(item => `<div class="api-call"><b>${item.lessonId}</b><span>${Math.round((item.confidence || 0) * 100)}% confidence</span><div>${item.lessonTitle}<br />${item.description}<br />Value ${item.enterpriseValue}</div></div>`).join("")
    : `<div class="alert-empty">Lesson Archive awaiting historical evidence</div>`;
  $("hre-gaps").innerHTML = gaps.length
    ? gaps.map(item => `<div class="api-call"><b>${item.gapId}</b><span>${item.priority}</span><div>${item.title}<br />${item.summary}<br />${item.academyPriority}</div></div>`).join("")
    : `<div class="alert-empty">Knowledge Gap Reports clear</div>`;
  $("hre-thresholds").innerHTML = Object.entries(historian.recommendationThresholds || {}).map(([key, value]) => `<div>${label(key)}<b>${value}</b></div>`).join("");
  $("hre-algorithms").innerHTML = (historian.patternDetectionAlgorithms || []).map(item => `<div class="api-call"><b>Pattern Detection Algorithm</b><span>Deterministic</span><div>${item}</div></div>`).join("");
  $("hre-lifecycle").innerHTML = (historian.recommendationLifecycle || []).map((item, index) => `<div class="api-call"><b>${index + 1}. ${item}</b><span>Constitutional Pipeline</span><div>No recommendation bypasses laboratory validation or Commander review.</div></div>`).join("");
  $("hre-diagnostics").innerHTML = Object.entries(historian.internalDiagnostics || {}).map(([key, value]) => `<div>${label(key)}<b>${value}</b></div>`).join("");
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

function renderEnterpriseMissionPlanner() {
  const planner = state.enterpriseMissionPlanner;
  if (!planner || !$("emp-status")) return;
  const metrics = planner.metrics || {};
  $("emp-status").innerHTML = Object.entries({
    planner: planner.status || "unknown",
    triggers: metrics.triggersReceived || 0,
    newPlans: metrics.newPlansCreated || 0,
    noAction: metrics.noActionDecisions || 0,
    deltaPlans: metrics.deltaPlansCreated || 0,
    merged: metrics.plansMerged || 0,
    submitted: (planner.submittedMissionPlans || []).length,
    avgOffices: metrics.averageOfficesPerPlan || 0,
    avgCost: `$${Number(metrics.estimatedCostPerPlan || 0).toFixed(4)}`,
    aiCalls: planner.lawCD?.routineAiInvocations || 0,
  }).map(([name, value]) => `<div><span>${label(name)}</span><b>${value}</b></div>`).join("");

  $("emp-trigger-queue").innerHTML = (planner.triggerQueue || []).slice(-8).reverse().map(item => `
    <div class="office-state">
      <b>${item.trigger_id}</b>
      <strong>${item.trigger_type}</strong>
      <span>${item.subject_id || item.ticker || item.position_id || "-"}</span>
      <span>${item.urgency || "routine"}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No planning triggers</b><strong>Quiet</strong><span>Planner has no intake records.</span></div>`;

  $("emp-draft-plans").innerHTML = (planner.draftMissionPlans || []).slice(-8).reverse().map(item => `
    <div class="office-state">
      <b>${item.mission_plan_id} / ${item.mission_type}</b>
      <strong>${item.status}</strong>
      <span>${item.priority_class} / ${item.template_id}</span>
      <span>${item.resource_envelope?.api_call_ceiling || 0}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No draft plans</b><strong>Clear</strong><span>Planner has not created executable work.</span></div>`;

  $("emp-workforce").innerHTML = (planner.minimumWorkforceView || []).slice(-6).reverse().map(item => `
    <div class="office-state">
      <b>${item.mission_plan_id}</b>
      <strong>${(item.included_offices || []).length} in</strong>
      <span>Excluded ${(item.excluded_offices || []).length}</span>
      <span>Services ${(item.deterministic_service_replacements || []).length}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No workforce decisions</b><strong>Quiet</strong><span>Awaiting mission plans.</span></div>`;

  $("emp-dependencies").innerHTML = (planner.dependencyGraphs || []).slice(-6).reverse().map(item => `
    <div class="office-state">
      <b>${item.mission_plan_id}</b>
      <strong>${(item.nodes || []).join(" -> ") || "local"}</strong>
      <span>Edges ${(item.edges || []).length}</span>
      <span>Plan</span>
    </div>
  `).join("") || `<div class="office-state"><b>No dependency graphs</b><strong>Quiet</strong><span>No execution plan is drafted.</span></div>`;

  const latestEnvelope = (planner.resourceEnvelopes || []).slice(-1)[0] || {};
  $("emp-resources").innerHTML = Object.entries({
    plan: latestEnvelope.mission_plan_id || "none",
    runtime: latestEnvelope.runtime_ceiling_seconds || 0,
    apiCalls: latestEnvelope.api_call_ceiling || 0,
    tokens: latestEnvelope.token_ceiling || 0,
    paidData: latestEnvelope.paid_data_call_ceiling || 0,
    estimate: `$${Number(latestEnvelope.estimated_cost_usd || 0).toFixed(4)}`,
  }).map(([name, value]) => `<div><span>${label(name)}</span><b>${value}</b></div>`).join("");

  $("emp-reuse-delta").innerHTML = (planner.reuseAndDelta || []).slice(-6).reverse().map(item => `
    <div class="office-state">
      <b>${item.mission_plan_id}</b>
      <strong>${item.delta?.delta_mission ? "DELTA" : "FULL"}</strong>
      <span>${item.reuse?.decision || "MISSION_REQUIRED"}</span>
      <span>${item.delta?.changed_fields?.length || 0}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No reuse decisions</b><strong>Quiet</strong><span>No mission has required planning.</span></div>`;
}

function renderEnterpriseCostGovernor() {
  const governor = state.enterpriseCostGovernor;
  if (!governor || !$("ecg-status")) return;
  const metrics = governor.metrics || {};
  $("ecg-status").innerHTML = Object.entries({
    governor: governor.status || "unknown",
    spendToday: `$${Number(metrics.spendToday || 0).toFixed(4)}`,
    utilization: `${(Number(metrics.budgetUtilization || 0) * 100).toFixed(1)}%`,
    reservations: metrics.activeReservations || 0,
    rejected: metrics.rejectedReservationCount || 0,
    unsettled: `$${Number(metrics.unsettledAmount || 0).toFixed(4)}`,
    reserve: `$${Number(metrics.safetyReserveRemaining || 0).toFixed(4)}`,
    breakers: (governor.circuitBreakers || []).length,
    gateway: governor.gatewayIntegration?.mandatory ? "MANDATORY" : "OPEN",
    aiCalls: governor.lawCE?.directProviderBypassAllowed ? "BYPASS" : "GATED",
  }).map(([name, value]) => `<div><span>${label(name)}</span><b>${value}</b></div>`).join("");

  const allocation = governor.budgetAllocation || {};
  $("ecg-budget").innerHTML = Object.entries({
    allocated: money(allocation.allocated, 4),
    reserved: money(allocation.reserved, 4),
    incurred: money(allocation.incurred, 4),
    settled: money(allocation.settled, 4),
    released: money(allocation.released, 4),
    available: money(allocation.available, 4),
  }).map(([name, value]) => `<div><span>${label(name)}</span><b>${value}</b></div>`).join("");

  $("ecg-reserves").innerHTML = (governor.protectedReserves || []).map(item => `
    <div class="office-state">
      <b>${item.category}</b>
      <strong>${item.state}</strong>
      <span>${money(item.available_amount, 4)} / ${money(item.allocated_amount, 4)}</span>
      <span>${money(item.reserved_amount, 4)}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No protected reserves</b><strong>Fault</strong><span>Policy has no reserve accounts.</span></div>`;

  $("ecg-reservations").innerHTML = (governor.missionReservations || []).slice(-8).reverse().map(item => `
    <div class="office-state">
      <b>${item.reservation_id} / ${item.mission_plan_id}</b>
      <strong>${item.state}</strong>
      <span>${item.decision} / ${item.budget_category}</span>
      <span>${money(item.approved_amount, 4)}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No reservations</b><strong>Clear</strong><span>No mission has reserved computational capital.</span></div>`;

  $("ecg-offices").innerHTML = (governor.officeCostTable || []).map(item => `
    <div class="office-state">
      <b>${item.office}</b>
      <strong>${item.state}</strong>
      <span>${money(item.costToday, 4)} / ceiling ${money(item.ceiling, 2)}</span>
      <span>${item.apiCalls}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No office usage</b><strong>Quiet</strong><span>No attributed cost has been recorded.</span></div>`;

  $("ecg-providers").innerHTML = (governor.providerModelUsage || []).map(item => `
    <div class="office-state">
      <b>${item.provider} / ${item.model}</b>
      <strong>${item.calls}</strong>
      <span>${item.inputTokens || 0} in / ${item.outputTokens || 0} out</span>
      <span>${money(item.calculatedCost, 4)}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No provider usage</b><strong>Quiet</strong><span>No gateway usage has settled.</span></div>`;

  $("ecg-authorizations").innerHTML = (governor.authorizationStream || []).slice(-5).reverse().map(item => `
    <div class="office-state">
      <b>${item.authorization_id}</b>
      <strong>${item.allowed ? "ALLOW" : "BLOCK"}</strong>
      <span>${item.request?.office_id || "-"} / ${item.request?.model || "-"}</span>
      <span>${item.decision}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No authorization records</b><strong>Quiet</strong><span>Gateway has not requested EO-CE authorization.</span></div>`;

  const forecast = governor.forecast || {};
  $("ecg-forecast").innerHTML = Object.entries({
    day: money(forecast.endOfDayForecast, 4),
    week: money(forecast.endOfWeekForecast, 4),
    month: money(forecast.endOfMonthForecast, 4),
    capacity: forecast.remainingMissionCapacity || 0,
    exhaustion: forecast.estimatedExhaustionTime || "unknown",
    confidence: `${Math.round(Number(forecast.forecastConfidence || 0) * 100)}%`,
  }).map(([name, value]) => `<div><span>${label(name)}</span><b>${value}</b></div>`).join("");
}

function renderInformationFreshnessEngine() {
  const engine = state.informationFreshnessEngine;
  if (!engine || !$("ifr-status")) return;
  const h = engine.headerIndicators || {};
  $("ifr-status").innerHTML = Object.entries({
    records: h.registeredInformationRecords || 0,
    fresh: h.freshRecords || 0,
    limited: h.limitedUseRecords || 0,
    validation: h.validationRequiredRecords || 0,
    partial: h.partiallyStaleRecords || 0,
    stale: h.staleRecords || 0,
    superseded: h.supersededRecords || 0,
    contradicted: h.contradictedRecords || 0,
    due: h.recordsDueForReevaluation || 0,
    avoided: h.refreshMissionsAvoided || 0,
  }).map(([name, value]) => `<div><span>${label(name)}</span><b>${value}</b></div>`).join("");

  $("ifr-inventory").innerHTML = (engine.freshnessInventory || []).slice(-10).reverse().map(item => `
    <div class="office-state">
      <b>${item.information_record_id} / ${item.information_type}</b>
      <strong>${item.currentStatus || "unknown"}</strong>
      <span>${item.subject_id || "-"} / ${item.source_system || "-"}</span>
      <span>${item.recommendedAction || "defer"}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No records</b><strong>Quiet</strong><span>No information metadata is registered.</span></div>`;

  $("ifr-at-risk").innerHTML = (engine.staleAndAtRiskInformation || []).slice(-8).reverse().map(item => `
    <div class="office-state">
      <b>${item.recordId}</b>
      <strong>${item.status}</strong>
      <span>${item.reason || "review"}</span>
      <span>${item.urgency || "prompt"}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No at-risk records</b><strong>Clear</strong><span>Current decisions have no stale critical scope.</span></div>`;

  $("ifr-dependencies").innerHTML = (engine.dependencyMap || []).slice(-8).reverse().map(item => `
    <div class="office-state">
      <b>${item.dependent_record_id}</b>
      <strong>${item.dependencyStatus || "unknown"}</strong>
      <span>${item.dependency_record_id} / ${item.dependency_type}</span>
      <span>${(item.affected_sections || []).join(", ") || "record"}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No dependency links</b><strong>Quiet</strong><span>No product dependency graph is registered.</span></div>`;

  $("ifr-contradictions").innerHTML = (engine.supersessionAndContradictions || []).slice(-8).reverse().map(item => `
    <div class="office-state">
      <b>${item.priorRecord || item.record_a_id || item.recordAId || "record"}</b>
      <strong>${item.resolutionStatus || item.materiality || "material"}</strong>
      <span>${item.newRecord || item.record_b_id || item.recordBId || "-"}</span>
      <span>${item.recommendedAction || "resolve_contradiction"}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No supersession or contradictions</b><strong>Clear</strong><span>Current records have no unresolved conflicts.</span></div>`;

  $("ifr-policies").innerHTML = (engine.freshnessPolicies || []).slice(0, 12).map(item => `
    <div class="office-state">
      <b>${item.policy_id} / ${item.information_type}</b>
      <strong>${item.decision_use_class || "default"}</strong>
      <span>max ${item.maximum_age_seconds ?? "none"}s / min ${item.minimum_source_authority}</span>
      <span>v${item.version}</span>
    </div>
  `).join("");

  const reuse = engine.reuseAndRefresh || {};
  $("ifr-reuse").innerHTML = Object.entries({
    exactReuse: (reuse.exactReuseCandidates || []).length,
    validationOnly: (reuse.validationOnlyCandidates || []).length,
    partialRefresh: (reuse.partialRefreshCandidates || []).length,
    fullRefresh: (reuse.fullRefreshCandidates || []).length,
    blocked: (reuse.blockedRecords || []).length,
    workAvoided: reuse.estimatedWorkAvoided || 0,
    retrievalAvoided: money(reuse.estimatedRetrievalAvoided || 0, 4),
  }).map(([name, value]) => `<div><span>${label(name)}</span><b>${value}</b></div>`).join("");

  $("ifr-queue").innerHTML = (engine.reevaluationQueue || []).slice(-6).reverse().map(item => `
    <div class="office-state">
      <b>${item.recordId}</b>
      <strong>${item.priority}</strong>
      <span>${item.dueTime || "on request"}</span>
      <span>${item.status || "unknown"}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No due reevaluations</b><strong>Clear</strong><span>Scheduled index has no overdue records.</span></div>`;
}

function renderEnterpriseMemoryCache() {
  const cache = state.enterpriseMemoryCache;
  if (!cache || !$("emc-status")) return;
  const h = cache.headerIndicators || {};
  $("emc-status").innerHTML = Object.entries({
    records: h.cacheRecords || 0,
    validated: h.validatedRecords || 0,
    candidates: h.candidateRecords || 0,
    historical: h.historicalRecords || 0,
    invalidated: h.invalidatedRecords || 0,
    superseded: h.supersededRecords || 0,
    contradicted: h.contradictedRecords || 0,
    quarantined: h.quarantinedRecords || 0,
    archived: h.archivedRecords || 0,
    hits: h.cacheHits || 0,
    misses: h.cacheMisses || 0,
    workAvoided: h.workAvoided || 0,
    costAvoided: money(h.costAvoided || 0, 4),
  }).map(([name, value]) => `<div><span>${label(name)}</span><b>${value}</b></div>`).join("");

  $("emc-inventory").innerHTML = (cache.memoryInventory || []).slice(-10).reverse().map(item => `
    <div class="office-state">
      <b>${item.cache_record_id} / ${item.product_subtype}</b>
      <strong>${item.status}</strong>
      <span>${item.subject_id || "-"} / ${item.environment}</span>
      <span>${item.currentFreshnessStatus || "unknown"}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No memory records</b><strong>Quiet</strong><span>No products admitted to enterprise memory.</span></div>`;

  $("emc-admissions").innerHTML = (cache.admissionQueue || []).slice(-8).reverse().map(item => `
    <div class="office-state">
      <b>${item.admission_decision_id}</b>
      <strong>${item.admitted ? "ADMIT" : "REJECT"}</strong>
      <span>${(item.reason_codes || []).join(", ")}</span>
      <span>${item.assigned_tier || "none"}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No admission decisions</b><strong>Quiet</strong><span>Memory admission has not run.</span></div>`;

  $("emc-retrievals").innerHTML = (cache.retrievalResults || []).slice(-6).reverse().map(item => `
    <div class="office-state">
      <b>${item.retrieval_result_id}</b>
      <strong>${(item.selected_cache_record_ids || []).length} selected</strong>
      <span>Exact ${(item.exact_reuse_record_ids || []).length} / partial ${(item.partial_reuse_record_ids || []).length}</span>
      <span>${Math.round(Number(item.overall_coverage_percent || 0) * 100)}%</span>
    </div>
  `).join("") || `<div class="office-state"><b>No retrievals</b><strong>Quiet</strong><span>No cache query has been executed.</span></div>`;

  $("emc-reuse").innerHTML = (cache.reuseEvaluations || []).slice(-8).reverse().map(item => `
    <div class="office-state">
      <b>${item.cache_record_id}</b>
      <strong>${item.decision}</strong>
      <span>Freshness ${item.freshness_decision_id}</span>
      <span>${Math.round(Number(item.scope_coverage_percent || 0) * 100)}%</span>
    </div>
  `).join("") || `<div class="office-state"><b>No reuse evaluations</b><strong>Quiet</strong><span>EO-CF has not evaluated cache reuse yet.</span></div>`;

  $("emc-invalidations").innerHTML = (cache.invalidationRecords || []).slice(-5).reverse().map(item => `
    <div class="office-state">
      <b>${item.cache_record_id}</b>
      <strong>${item.new_status}</strong>
      <span>${item.reason}</span>
      <span>${item.invalidation_type}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No invalidations</b><strong>Clear</strong><span>Memory records have not been invalidated.</span></div>`;

  $("emc-access").innerHTML = (cache.accessAudit || []).slice(-5).reverse().map(item => `
    <div class="office-state">
      <b>${item.cache_record_id}</b>
      <strong>${item.permitted ? "PERMIT" : "DENY"}</strong>
      <span>${item.requester_id}</span>
      <span>${item.reuse_decision || "none"}</span>
    </div>
  `).join("");

  $("emc-contradictions").innerHTML = (cache.contradictionRecords || []).slice(-5).reverse().map(item => `
    <div class="office-state">
      <b>${item.cache_record_id}</b>
      <strong>${item.new_status}</strong>
      <span>${item.reason}</span>
      <span>${item.contradiction_scope || "record"}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No contradictions</b><strong>Clear</strong><span>No contradictory memory evidence is registered.</span></div>`;

  $("emc-quarantine").innerHTML = (cache.quarantineRecords || []).slice(-5).reverse().map(item => `
    <div class="office-state">
      <b>${item.cacheRecordId}</b>
      <strong>${item.tier}</strong>
      <span>${(item.reasonCodes || []).join(", ") || "quarantine"}</span>
      <span>${item.reviewRequired ? "review required" : "clear"}</span>
    </div>
  `).join("");

  $("emc-archive").innerHTML = (cache.archivalRecords || []).slice(-5).reverse().map(item => `
    <div class="office-state">
      <b>${item.cacheRecordId}</b>
      <strong>${item.archiveId}</strong>
      <span>${item.reason}</span>
      <span>${item.archivedAt}</span>
    </div>
  `).join("");

  $("emc-indexes").innerHTML = Object.entries(cache.indexes || {}).map(([name, value]) => `<div><span>${label(name)}</span><b>${Array.isArray(value) ? value.length : value}</b></div>`).join("");
  $("emc-retention").innerHTML = Object.entries(cache.retentionPolicy || {}).slice(0, 6).map(([name, value]) => `<div><span>${label(name)}</span><b>${value}</b></div>`).join("");
  $("emc-repository").innerHTML = `<div><span>Repository Methods</span><b>${(cache.repositoryMethods || []).length}</b></div><div><span>Persistence</span><b>${(cache.persistence || {}).mode || "unknown"}</b></div>`;
  $("emc-eoch").innerHTML = Object.entries(cache.eoCHFeed || {}).map(([name, value]) => `<div><span>${label(name)}</span><b>${Array.isArray(value) ? value.length : value}</b></div>`).join("");
}

function renderWorkflowDeltaEngine() {
  const engine = state.workflowDeltaEngine;
  if (!engine || !$("wch-status")) return;
  const summary = engine.summary || {};
  $("wch-status").innerHTML = Object.entries({
    baselines: summary.baselines || 0,
    requests: summary.requests || 0,
    packages: summary.packages || 0,
    pending: summary.pendingRequests || 0,
    full: summary.fullReassessments || 0,
    partial: summary.partialRevisions || 0,
    reused: summary.reusedProducts || 0,
    officesAvoided: summary.officesAvoided || 0,
    costAvoided: money(summary.estimatedCostAvoided || 0, 4),
  }).map(([name, value]) => `<div><span>${label(name)}</span><b>${value}</b></div>`).join("");

  $("wch-requests").innerHTML = (engine.deltaRequestQueue || []).slice(-8).reverse().map(item => `
    <div class="office-state">
      <b>${item.delta_request_id}</b>
      <strong>${item.request_type}</strong>
      <span>${item.subject_id || "-"} / ${item.environment}</span>
      <span>${item.baseline_id}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No delta requests</b><strong>Quiet</strong><span>No workflow delta request has been analyzed.</span></div>`;

  const change = engine.changeSummary || {};
  $("wch-summary").innerHTML = Object.entries({
    package: change.packageId || "none",
    materiality: change.highestMateriality || "none",
    fullReassessment: change.fullReassessmentRequired ? "YES" : "NO",
    scope: (change.minimumRevisionScope || []).length,
    sequence: (change.recommendedSequence || []).length,
  }).map(([name, value]) => `<div><span>${label(name)}</span><b>${value}</b></div>`).join("");

  $("wch-fields").innerHTML = ((engine.fieldAndSectionDelta || {}).fields || []).slice(-8).reverse().map(item => `
    <div class="office-state">
      <b>${item.field_path}</b>
      <strong>${item.change_type}</strong>
      <span>${item.materiality} / ${item.comparison_method}</span>
      <span>${item.explanation}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No field delta</b><strong>Quiet</strong><span>No current package field changes.</span></div>`;

  $("wch-sections").innerHTML = ((engine.fieldAndSectionDelta || {}).sections || []).slice(-8).reverse().map(item => `
    <div class="office-state">
      <b>${item.section_name}</b>
      <strong>${item.revision_requirement}</strong>
      <span>${item.materiality}</span>
      <span>${item.explanation}</span>
    </div>
  `).join("");

  $("wch-products").innerHTML = (engine.productImpactMatrix || []).slice(-8).reverse().map(item => `
    <div class="office-state">
      <b>${item.cache_record_id || item.product_record_id}</b>
      <strong>${item.revision_requirement}</strong>
      <span>Affected ${(item.affected_fields || []).length} / reusable ${(item.reusable_fields || []).length}</span>
      <span>${item.reason}</span>
    </div>
  `).join("");

  $("wch-offices").innerHTML = (engine.officeImpactMatrix || []).map(item => `
    <div class="office-state">
      <b>${item.office_id}</b>
      <strong>${item.impact_decision}</strong>
      <span>${(item.required_scope || []).slice(0, 3).join(", ") || item.excluded_reason}</span>
      <span>${item.estimated_runtime_seconds || 0}s / ${item.estimated_api_calls || 0} calls</span>
    </div>
  `).join("");

  $("wch-dependencies").innerHTML = (engine.dependencyImpactMap || []).slice(-8).reverse().map(item => `
    <div class="office-state">
      <b>${item.changed_input}</b>
      <strong>${item.materiality}</strong>
      <span>${(item.affected_calculations || []).join(", ")}</span>
      <span>${item.propagation_boundary}</span>
    </div>
  `).join("");

  $("wch-workflow").innerHTML = (engine.workflowGraphComparison || []).map(item => `
    <div class="office-state">
      <b>${item.node_id}</b>
      <strong>${item.change_type}</strong>
      <span>Prior ${item.prior_required ? "Y" : "N"} / Current ${item.current_required ? "Y" : "N"}</span>
      <span>${item.reason}</span>
    </div>
  `).join("");

  $("wch-reuse").innerHTML = Object.entries(engine.reuseAndWorkReduction || {}).map(([name, value]) => `<div><span>${label(name)}</span><b>${value}</b></div>`).join("");
  const feed = engine.missionPlannerFeed || {};
  $("wch-mission-feed").innerHTML = feed.deltaPackageReady ? `
    <div class="office-state">
      <b>${feed.targetEngine}</b>
      <strong>${feed.submitted ? "SUBMITTED" : "READY"}</strong>
      <span>${feed.reason}</span>
      <span>${(feed.changedFields || []).slice(0, 4).join(", ")}</span>
    </div>
  ` : `<div class="office-state"><b>No EO-CD feed</b><strong>Quiet</strong><span>No delta package has been produced.</span></div>`;
}

function renderEnterprisePriorityEngine() {
  const engine = state.enterprisePriorityEngine;
  if (!engine || !$("epj-status")) return;
  const summary = engine.summary || {};
  $("epj-status").innerHTML = Object.entries({
    status: engine.status || "unknown",
    candidates: summary.candidateCount || 0,
    ranked: summary.rankedCount || 0,
    runNow: summary.runNowRecommendations || 0,
    deferred: summary.deferredMissions || 0,
    blocked: summary.blockedMissions || 0,
    preemptions: summary.preemptionRecommendations || 0,
    inheritance: summary.inheritanceEvents || 0,
    starvation: summary.starvationWarnings || 0,
    topClass: summary.topClass || "none",
  }).map(([name, value]) => `<div><span>${label(name)}</span><b>${value}</b></div>`).join("");

  $("epj-ranked-queue").innerHTML = (engine.rankedMissionQueue || []).slice(0, 12).map(item => `
    <div class="office-state">
      <b>#${item.rank} ${item.missionId || item.missionPlanId || item.candidateId}</b>
      <strong>${item.disposition}</strong>
      <span>${item.priorityClass} / score ${Number(item.score || 0).toFixed(2)}</span>
      <span>${item.reason || "Ranked by deterministic policy."}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No ranked missions</b><strong>Quiet</strong><span>Run priority evaluation after missions, events, or plans exist.</span></div>`;

  $("epj-score-breakdown").innerHTML = (engine.scoreBreakdown || []).slice(0, 6).map(item => {
    const components = item.components || {};
    return `
      <div class="office-state">
        <b>${item.mission || item.decisionId}</b>
        <strong>${Number(item.normalizedScore || 0).toFixed(2)}</strong>
        <span>Base ${Number(components.class_base_score || 0).toFixed(1)} / safety ${Number((components.emergency_score || 0) + (components.position_safety_score || 0) + (components.broker_integrity_score || 0) + (components.risk_score || 0)).toFixed(1)}</span>
        <span>Age ${Number((components.mission_age_score || 0) + (components.starvation_score || 0)).toFixed(1)} / resource ${Number((components.budget_availability_score || 0) + (components.office_availability_score || 0) + (components.token_availability_score || 0)).toFixed(1)}</span>
      </div>
    `;
  }).join("") || `<div class="office-state"><b>No score breakdown</b><strong>Quiet</strong><span>No current priority decisions.</span></div>`;

  const safety = engine.safetyPrecedence || {};
  $("epj-safety").innerHTML = Object.entries({
    protected: safety.protectedMissionCount || 0,
    highestProtectedRank: safety.highestProtectedRank || 0,
    discretionaryAboveSafety: safety.discretionaryAboveSafety ? "FAULT" : "NO",
    scoreOverride: safety.numericScoreCanOverrideSafety ? "FAULT" : "BLOCKED",
    doctrineClasses: (safety.doctrine || []).length,
  }).map(([name, value]) => `<div><span>${label(name)}</span><b>${value}</b></div>`).join("");

  $("epj-inheritance").innerHTML = (engine.priorityInheritance || []).map(item => `
    <div class="office-state">
      <b>${item.mission || item.decisionId}</b>
      <strong>${item.effectiveClass}</strong>
      <span>Inherited from ${item.inheritedFrom || "dependency"}</span>
      <span>${item.reason}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No priority inheritance</b><strong>Clear</strong><span>No lower-class dependency is currently elevated.</span></div>`;

  $("epj-preemption").innerHTML = (engine.preemptionAssessments || []).slice(0, 8).map(item => `
    <div class="office-state">
      <b>${item.mission || item.decisionId}</b>
      <strong>${item.recommendation}</strong>
      <span>${item.preemptionClass}</span>
      <span>${item.safe ? "Safe assessment" : "Rejected by safety rule"}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No preemption assessments</b><strong>Quiet</strong><span>No ranked work requires preemption review.</span></div>`;

  $("epj-aging").innerHTML = (engine.starvationAndAging || []).slice(0, 8).map(item => `
    <div class="office-state">
      <b>${item.mission || item.decisionId}</b>
      <strong>${item.deferrals} deferrals</strong>
      <span>Aging ${Number(item.agingScore || 0).toFixed(2)} / starvation ${Number(item.starvationScore || 0).toFixed(2)}</span>
      <span>${item.safetyLimitsAging ? "Safety class protected" : "Fairness applies when safe"}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No aging state</b><strong>Quiet</strong><span>No mission has accrued queue age.</span></div>`;

  $("epj-resources").innerHTML = (engine.resourceConstraints || []).slice(0, 8).map(item => `
    <div class="office-state">
      <b>${item.mission || item.decisionId}</b>
      <strong>${item.reductionRecommendation || "scope ok"}</strong>
      <span>Budget ${Number(item.budgetScore || 0).toFixed(1)} / Office ${Number(item.officeScore || 0).toFixed(1)} / Token ${Number(item.tokenScore || 0).toFixed(1)}</span>
      <span>Freshness ${Number(item.freshnessScore || 0).toFixed(1)}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No resource constraints</b><strong>Quiet</strong><span>No ranked mission has resource pressure.</span></div>`;

  $("epj-deferred").innerHTML = (engine.suspendedAndDeferred || []).map(item => `
    <div class="office-state">
      <b>${item.missionId || item.missionPlanId || item.candidateId}</b>
      <strong>${item.disposition}</strong>
      <span>${(item.blocked || []).join(", ") || item.priorityClass}</span>
      <span>${item.reason}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No suspended or deferred work</b><strong>Clear</strong><span>Current ranking has no deferred items.</span></div>`;

  const feed = engine.schedulerFeed || {};
  $("epj-scheduler-feed").innerHTML = `
    <div><span>Target Engine</span><b>${feed.targetEngine || "EO-CA Enterprise Operations Scheduler"}</b></div>
    <div><span>Recommendations Only</span><b>${feed.recommendationsOnly ? "YES" : "YES"}</b></div>
    <div><span>Run Now</span><b>${(feed.runNow || []).length || 0}</b></div>
    <div><span>Queue Next</span><b>${(feed.queueNext || []).length || 0}</b></div>
    <div><span>Authority Transferred</span><b>${feed.authorityTransferred ? "FAULT" : "NO"}</b></div>
  `;
}

function renderPositionMonitoringNetwork() {
  const network = state.positionMonitoringNetwork;
  if (!network || !$("pmn-status")) return;
  const summary = network.summary || {};
  $("pmn-status").innerHTML = Object.entries({
    status: network.status || "unknown",
    activeWatchers: summary.activeWatchers || 0,
    degraded: summary.degradedWatchers || 0,
    triggered: summary.triggeredWatchers || 0,
    events: summary.eventsEmitted || 0,
    latest: summary.latestEvents || 0,
    positions: summary.activePositionsMonitored || 0,
    aiCalls: network.lawCK?.routineAiInvocations || 0,
  }).map(([name, value]) => `<div><span>${label(name)}</span><b>${value}</b></div>`).join("");

  $("pmn-watchers").innerHTML = (network.watcherRoster || []).slice(0, 16).map(item => `
    <div class="office-state">
      <b>${item.symbol || item.position_id} / ${item.watcher_type}</b>
      <strong>${item.status}</strong>
      <span>Value ${Number(item.last_value || 0).toFixed(4)} / threshold ${Number(item.threshold || 0).toFixed(4)}</span>
      <span>${item.explanation}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No watchers</b><strong>Quiet</strong><span>No open Position Objects require monitoring.</span></div>`;

  $("pmn-events").innerHTML = (network.latestMonitoringEvents || network.monitoringEvents || []).slice(-10).reverse().map(item => `
    <div class="office-state">
      <b>${item.monitoring_event_id} / ${item.event_type}</b>
      <strong>${item.severity}</strong>
      <span>${item.symbol} / ${item.position_id}</span>
      <span>${item.urgency} / ${item.materiality}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No monitoring events</b><strong>Clear</strong><span>Watchers have not emitted material position events.</span></div>`;

  const coverage = network.watcherCoverage || {};
  $("pmn-coverage").innerHTML = `
    <div><span>Positions With Watchers</span><b>${coverage.positionsWithWatchers || 0}</b></div>
    <div><span>Watcher Types</span><b>${(coverage.expectedWatcherTypes || []).length}</b></div>
    <div><span>Feeds EO-CC</span><b>${network.lawCK?.feedsEOCC ? "YES" : "NO"}</b></div>
    <div><span>Events Only</span><b>${network.lawCK?.producesEventsOnly ? "YES" : "NO"}</b></div>
    <div><span>Mutates Positions</span><b>${network.lawCK?.mutatesPositions ? "FAULT" : "NO"}</b></div>
  `;

  $("pmn-feed").innerHTML = (network.eventDetectionFeed || []).slice(-8).reverse().map(item => `
    <div class="office-state">
      <b>${item.source_event_id}</b>
      <strong>${item.event_type}</strong>
      <span>${item.severity} / ${item.urgency}</span>
      <span>${item.summary}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No EO-CC feed</b><strong>Quiet</strong><span>No high-priority monitoring event is ready for Event Detection.</span></div>`;
}

function renderEnterpriseCommunicationsBus() {
  const bus = state.enterpriseCommunicationsBus;
  if (!bus || !$("ecl-status")) return;
  const summary = bus.summary || {};
  $("ecl-status").innerHTML = Object.entries({
    health: bus.health || "UNKNOWN",
    published: summary.messagesPublished || 0,
    perMinute: summary.messagesPublishedPerMinute || 0,
    deliverySuccess: `${Number(summary.deliverySuccessRate || 0).toFixed(2)}%`,
    outbox: summary.currentOutboxDepth || 0,
    retries: summary.retryBacklog || 0,
    deadLetters: summary.deadLetterCount || 0,
    quarantine: summary.quarantineCount || 0,
    activeSubscribers: summary.activeSubscribers || 0,
    unavailableSubscribers: summary.unavailableSubscribers || 0,
    liveLatencyMs: summary.liveLaneLatencyMs || 0,
    paperLatencyMs: summary.paperLaneLatencyMs || 0,
    sequenceGaps: summary.sequenceGapWarnings || 0,
    aiCalls: bus.lawCL?.routineAiInvocations || 0,
  }).map(([name, value]) => `<div><span>${label(name)}</span><b>${value}</b></div>`).join("");

  $("ecl-stream").innerHTML = (bus.messageStream || []).slice(0, 12).map(item => `
    <div class="office-state">
      <b>${item.message_id}</b>
      <strong>${item.message_kind} / ${item.message_type}</strong>
      <span>${item.source_service_id} -> ${item.target_service_id || item.target_topic || item.routing_key}</span>
      <span>${item.correlation_id} / ${item.paper_live_mode} / retry ${item.retry_count || 0}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No messages</b><strong>Quiet</strong><span>No EO-CL messages have been published.</span></div>`;

  $("ecl-trace").innerHTML = (bus.correlationIndex || []).slice(0, 10).map(item => `
    <div class="office-state">
      <b>${item.correlationId}</b>
      <strong>${item.messageCount} messages</strong>
      <span>Traceable causation chain available through EO-CL.</span>
    </div>
  `).join("") || `<div class="office-state"><b>No correlation trace</b><strong>Quiet</strong><span>No message correlation chain has formed.</span></div>`;

  $("ecl-dead").innerHTML = (bus.deadLetters || []).slice(0, 8).map(item => `
    <div class="office-state">
      <b>${item.dead_letter_id}</b>
      <strong>${item.reason_code}</strong>
      <span>${item.message_id} / ${item.subscription_id}</span>
      <span>Attempts ${item.attempts} / Replay ${item.replay_eligible ? "eligible" : "blocked"}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No dead letters</b><strong>Clear</strong><span>No terminal delivery failures are awaiting review.</span></div>`;

  $("ecl-quarantine").innerHTML = (bus.quarantine || []).slice(0, 8).map(item => `
    <div class="office-state">
      <b>${item.quarantine_id}</b>
      <strong>${item.reason_code}</strong>
      <span>${item.source_service_id} / ${item.schema_name} / ${item.paper_live_mode}</span>
      <span>${item.commander_review_state}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No quarantine</b><strong>Clear</strong><span>No authority-sensitive or security-held messages.</span></div>`;

  $("ecl-subscribers").innerHTML = (bus.subscriberHealth || []).map(item => `
    <div class="office-state">
      <b>${item.subscriber}</b>
      <strong>${item.availability}</strong>
      <span>${(item.supportedMessageTypes || []).join(", ")}</span>
      <span>Queue ${item.queueDepth} / Error ${item.errorRate}% / ${item.sideEffectClassification}</span>
    </div>
  `).join("");

  $("ecl-schema").innerHTML = (bus.schemaRegistry || []).slice(0, 12).map(item => `
    <div class="office-state">
      <b>${item.message_type}</b>
      <strong>${item.current_version}</strong>
      <span>${item.owning_authority} / ${item.compatibility_mode}</span>
      <span>${item.deprecated ? "Deprecated" : "Active"}</span>
    </div>
  `).join("");

  $("ecl-law").innerHTML = Object.entries(bus.lawCL || {}).map(([name, value]) => `
    <div><span>${label(name)}</span><b>${value === true ? "YES" : value === false ? "NO" : value}</b></div>
  `).join("");

  $("ecl-audit").innerHTML = (bus.auditTrail || []).slice(0, 10).map(item => `
    <div class="office-state">
      <b>${item.audit_id}</b>
      <strong>${item.action}</strong>
      <span>${item.message_id || item.publisher_id} / ${item.reason_code}</span>
      <span>${item.prior_state || "-"} -> ${item.new_state || "-"}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No audit trail</b><strong>Quiet</strong><span>EO-CL audit is awaiting message activity.</span></div>`;
}

function renderEnterpriseEfficiencyAnalytics() {
  const analytics = state.enterpriseEfficiencyAnalytics;
  if (!analytics || !$("ecn-status")) return;
  const summary = analytics.latestSnapshot?.enterprise_efficiency_summary || {};
  $("ecn-status").innerHTML = Object.entries({
    status: analytics.status || "unknown",
    missionThroughput: summary.missionThroughput ?? "n/a",
    workflowThroughput: summary.workflowThroughput ?? "n/a",
    queueLatency: summary.averageQueueLatency ?? "insufficient",
    apiCost: summary.dailyApiCost ?? "n/a",
    deterministicShare: summary.deterministicWorkShare ?? "n/a",
    usefulUtilization: summary.usefulOfficeUtilization ?? "insufficient",
    cacheReuse: summary.cacheReuseRate ?? "insufficient",
    deltaWork: summary.deltaWorkRate ?? "insufficient",
    monitoringCoverage: summary.monitoringCoverage ?? "insufficient",
    messageDelivery: summary.messageDeliverySuccess ?? "n/a",
    commanderBacklog: summary.commanderReviewBacklog ?? 0,
    dataQuality: summary.dataQualityStatus || "unknown",
    aiCalls: analytics.lawCN?.routineAiInvocations || 0,
  }).map(([name, value]) => `<div><span>${label(name)}</span><b>${value}</b></div>`).join("");

  $("ecn-scorecard").innerHTML = (analytics.scorecard || []).map(item => `
    <div class="office-state">
      <b>${item.metric}</b>
      <strong>${item.status}</strong>
      <span>${item.currentValue ?? "insufficient"} ${item.units || ""} / target ${item.target ?? "n/a"}</span>
      <span>${item.trend} / ${item.dataQuality} / ${item.mode}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No scorecard</b><strong>Awaiting</strong><span>Refresh EO-CN to persist analytics.</span></div>`;

  $("ecn-offices").innerHTML = (analytics.officeEfficiency || []).slice(0, 10).map(item => `
    <div class="office-state">
      <b>${item.office || "Office"}</b>
      <strong>${item.dataQuality || "tracked"}</strong>
      <span>Wake sessions ${item.wakeSessions ?? 0} / missions ${item.completedMissions ?? 0}</span>
      <span>Useful utilization ${item.usefulUtilization ?? "insufficient"}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No office records</b><strong>Insufficient</strong><span>Office wakefulness records are not yet complete.</span></div>`;

  $("ecn-missions").innerHTML = (analytics.missionEfficiency || []).slice(0, 10).map(item => `
    <div class="office-state">
      <b>${item.mission || "Mission"}</b>
      <strong>${item.outcome || "tracked"}</strong>
      <span>${item.type || "mission"} / queue ${item.queueTime ?? "n/a"} / active ${item.activeTime ?? "n/a"}</span>
      <span>Cost ${item.cost ?? 0} / offices ${item.officesUsed ?? 0}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No missions</b><strong>Quiet</strong><span>No scheduler mission records in the analytics window.</span></div>`;

  $("ecn-workflows").innerHTML = (analytics.workflowEfficiency || []).slice(0, 10).map(item => `
    <div class="office-state">
      <b>${item.workflow || "Workflow"}</b>
      <strong>${item.completionState || "tracked"}</strong>
      <span>Duration ${item.duration ?? 0} / cost ${item.cost ?? 0}</span>
      <span>Handoff latency ${item.handoffLatency ?? "insufficient"}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No workflows</b><strong>Quiet</strong><span>No workflow records in the analytics window.</span></div>`;

  const cost = analytics.costEfficiency || {};
  $("ecn-cost").innerHTML = Object.entries({
    dailyApiCost: cost.dailyApiCost ?? "n/a",
    cacheSavings: cost.cacheSavings ?? 0,
    budgetVariance: cost.budgetVariance || "unknown",
    costTrend: cost.costTrend || "current",
  }).map(([name, value]) => `<div><span>${label(name)}</span><b>${value}</b></div>`).join("");

  $("ecn-reuse").innerHTML = Object.entries(analytics.reuseAndDelta || {}).map(([name, value]) => `<div><span>${label(name)}</span><b>${value ?? "insufficient"}</b></div>`).join("");
  $("ecn-communications").innerHTML = Object.entries(analytics.communicationsEfficiency || {}).map(([name, value]) => `<div><span>${label(name)}</span><b>${typeof value === "object" ? JSON.stringify(value) : value}</b></div>`).join("");
  $("ecn-recovery").innerHTML = Object.entries(analytics.recoveryEfficiency || {}).map(([name, value]) => `<div><span>${label(name)}</span><b>${value ?? "insufficient"}</b></div>`).join("");

  $("ecn-findings").innerHTML = (analytics.findings || []).slice(0, 10).map(item => `
    <div class="office-state">
      <b>${item.finding_id}</b>
      <strong>${item.severity} / ${item.finding_type}</strong>
      <span>${item.title}</span>
      <span>${item.causal_status} / ${item.recommended_review}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No findings</b><strong>Clear</strong><span>No efficiency finding requires review.</span></div>`;

  $("ecn-lineage").innerHTML = (analytics.metricLineage || []).slice(0, 10).map(item => `
    <div class="office-state">
      <b>${item.metricValueId}</b>
      <strong>${item.formulaVersion}</strong>
      <span>${item.formula}</span>
      <span>${(item.sourceRecords || []).join(", ")}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No lineage</b><strong>Awaiting</strong><span>Metric lineage appears after calculation.</span></div>`;

  $("ecn-law").innerHTML = Object.entries(analytics.lawCN || {}).map(([name, value]) => `
    <div><span>${label(name)}</span><b>${value === true ? "YES" : value === false ? "NO" : value}</b></div>
  `).join("");
}

function renderEnterpriseDoctrinePolicyManager() {
  const manager = state.enterpriseDoctrinePolicyManager;
  if (!manager || !$("eco-status")) return;
  const metrics = manager.policyMetrics || {};
  $("eco-status").innerHTML = Object.entries({
    health: manager.health?.overallState || manager.status || "UNKNOWN",
    activePolicies: metrics.activePolicies || 0,
    activeDoctrine: manager.activeDoctrineVersion || "unknown",
    pendingApprovals: metrics.pendingApprovals || 0,
    scheduledActivations: metrics.scheduledActivations || 0,
    driftCount: metrics.driftCount || 0,
    emergencyRestrictions: metrics.emergencyRestrictions || 0,
    incompleteDistribution: metrics.incompleteDistributionCount || 0,
    lawVII: manager.lawCO?.lawVIIConstitutional ? "CONSTITUTIONAL" : "FAULT",
    aiCalls: manager.lawCO?.invokesAiForRoutinePolicyValidation ? "FAULT" : 0,
  }).map(([name, value]) => `<div><span>${label(name)}</span><b>${value}</b></div>`).join("");

  $("eco-active-matrix").innerHTML = (manager.activePolicyMatrix || []).slice(0, 18).map(item => `
    <div class="office-state">
      <b>${item.policyDomain} / ${item.policyName}</b>
      <strong>${item.health} / ${item.activeVersion}</strong>
      <span>${item.scope} / ${item.mode} / ${item.subscriberStatus}</span>
      <span>Drift ${item.driftStatus} / hash ${String(item.policyHash || "").slice(0, 12)}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No active policies</b><strong>Blocked</strong><span>EO-CO has no active policy projection.</span></div>`;

  $("eco-doctrine").innerHTML = (manager.doctrineLibrary || []).map(item => `
    <div class="office-state">
      <b>${item.title}</b>
      <strong>${item.doctrine_type} / ${item.version}</strong>
      <span>${item.authority_level} / ${item.status}</span>
      <span>${item.statement}</span>
    </div>
  `).join("");

  $("eco-approvals").innerHTML = (manager.pendingApprovals || []).map(item => `
    <div class="office-state">
      <b>${item.policy} / ${item.version}</b>
      <strong>${item.domain} / ${item.riskClass}</strong>
      <span>Approvals ${item.completedApprovals}/${(item.requiredApprovals || []).length}</span>
      <span>${item.compatibilityStatus} / ${item.simulationStatus}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No pending approvals</b><strong>Clear</strong><span>Policy queue is currently reconciled.</span></div>`;

  $("eco-activation").innerHTML = (manager.activationPlans || []).slice(-10).reverse().map(item => `
    <div class="office-state">
      <b>${item.activation_plan_id}</b>
      <strong>${item.activation_strategy}</strong>
      <span>${item.policy_version_id}</span>
      <span>${(item.target_subscribers || []).join(", ")} / rollback ${item.rollback_target || "defined by policy"}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No activation plans</b><strong>Quiet</strong><span>Approved policies are not currently staging.</span></div>`;

  $("eco-drift").innerHTML = (manager.driftDetections || []).slice(-10).reverse().map(item => `
    <div class="office-state">
      <b>${item.subscriber_id}</b>
      <strong>${item.severity} / ${item.drift_classification}</strong>
      <span>${item.policy_version_id}</span>
      <span>${item.reconciliation_status} / ${item.likely_cause}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No drift</b><strong>Clear</strong><span>Subscribers match their active policy hashes.</span></div>`;

  $("eco-series-c").innerHTML = (manager.seriesCIntegrationMatrix || []).map(item => `
    <div class="office-state">
      <b>${item.subsystem}</b>
      <strong>${item.policyDomain}</strong>
      <span>${item.activePolicyVersion} / ${item.subscriberAcknowledgement}</span>
      <span>${item.priorLocalProvider} -> ${item.eoCoSchema} / drift ${item.driftStatus}</span>
    </div>
  `).join("");

  $("eco-metrics").innerHTML = Object.entries(metrics).slice(0, 18).map(([name, value]) => `
    <div><span>${label(name)}</span><b>${value}</b></div>
  `).join("");

  $("eco-law").innerHTML = Object.entries(manager.lawCO || {}).map(([name, value]) => `
    <div><span>${label(name)}</span><b>${value === true ? "YES" : value === false ? "NO" : value}</b></div>
  `).join("");
}

function renderEventDetectionEngine() {
  const engine = state.eventDetectionEngine;
  if (!engine || !$("ede-status")) return;
  $("ede-status").innerHTML = Object.entries({
    engine: engine.engineState || "unknown",
    detectors: engine.activeDetectors || 0,
    degraded: engine.degradedDetectors || 0,
    failed: engine.failedDetectors || 0,
    candidates: engine.eventsDetectedToday || 0,
    validated: engine.validatedEventsToday || 0,
    suppressed: engine.suppressedEventsToday || 0,
    critical: engine.activeCriticalEvents || 0,
    missions: engine.missionTriggersSubmitted || 0,
    apiCost: `$${Number(engine.externalDataApiCost || 0).toFixed(4)}`,
  }).map(([name, value]) => `<div><span>${label(name)}</span><b>${value}</b></div>`).join("");

  $("ede-active-events").innerHTML = (engine.activeEvents || []).slice(-10).reverse().map(item => `
    <div class="office-state">
      <b>${item.event_id} / ${item.event_type}</b>
      <strong>${item.severity}</strong>
      <span>${item.domain} / ${item.materiality}</span>
      <span>${item.status}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No active events</b><strong>Quiet</strong><span>Validated event ledger is clear.</span></div>`;

  $("ede-detectors").innerHTML = (engine.detectorHealth || []).map(item => `
    <div class="office-state">
      <b>${item.name}</b>
      <strong>${item.state}</strong>
      <span>${item.domain} / ${item.candidate_count || 0} candidates</span>
      <span>${item.validated_count || 0}</span>
    </div>
  `).join("");

  $("ede-flow").innerHTML = Object.entries(engine.eventFlow || {}).map(([name, value]) => `<div><span>${label(name)}</span><b>${value}</b></div>`).join("");

  $("ede-suppression").innerHTML = (engine.suppressionAndDeduplication || []).slice(-8).reverse().map(item => `
    <div class="office-state">
      <b>${item.reason}</b>
      <strong>${item.detector_id}</strong>
      <span>${item.subject_id}</span>
      <span>${item.duplicate_count || 0}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No suppressed events</b><strong>Clear</strong><span>Noise controls have not suppressed work yet.</span></div>`;

  $("ede-groups").innerHTML = (engine.eventGroups || []).map(item => `
    <div class="office-state">
      <b>${item.group_title}</b>
      <strong>${item.aggregate_severity}</strong>
      <span>${item.aggregate_materiality} / ${(item.constituent_event_ids || []).length} events</span>
      <span>${item.status}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No event groups</b><strong>Quiet</strong><span>Correlation has not grouped events.</span></div>`;

  $("ede-rules").innerHTML = (engine.rules || []).map(item => `
    <div class="office-state">
      <b>${item.rule_id}</b>
      <strong>${item.enabled ? "ON" : "OFF"}</strong>
      <span>${item.domain} / ${item.event_type}</span>
      <span>${item.trigger_threshold}</span>
    </div>
  `).join("");
}

function renderScheduler() {
  if (!state.scheduler) return;
  renderEnterpriseOperationsScheduler();
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

function renderEnterpriseOperationsScheduler() {
  const eos = state.enterpriseOperationsScheduler || state.scheduler?.enterpriseOperationsScheduler;
  if (!eos || !$("eos-status")) return;
  $("eos-mode").value = eos.currentOperatingMode || "Observation Only";
  $("eos-status").innerHTML = Object.entries({
    enabled: eos.enabled ? "Enabled" : "Disabled",
    health: eos.status || "Unknown",
    marketSession: eos.currentMarketSession || "Unknown",
    nextMission: eos.nextMission?.mission_name || "None",
    activeMissions: eos.activeMissionCount || 0,
    timezone: eos.timezone || "America/Cancun",
  }).map(([name, value]) => `<div>${label(name)}<b>${value}</b></div>`).join("");
  $("eos-template").innerHTML = (eos.missionTemplates || []).map(template => `<option value="${template.template_id}">${template.mission_name}</option>`).join("");
  $("eos-cost-monitor").innerHTML = Object.entries({
    dailyBudget: eos.missionCostMonitor?.dailyBudgetUsd || 0,
    missionCeiling: eos.missionCostMonitor?.missionCostCeilingUsd || 0,
    actualCost: eos.missionCostMonitor?.actualCostUsd || 0,
    apiCalls: eos.missionCostMonitor?.apiCalls || 0,
    costAvoided: eos.missionCostMonitor?.estimatedCostAvoidedUsd || 0,
    budgetExhausted: eos.missionCostMonitor?.budgetExhausted ? "YES" : "NO",
  }).map(([name, value]) => `<div>${label(name)}<b>${value}</b></div>`).join("");
  const timeline = eos.missionTimeline || {};
  const rows = [...(timeline.active || []), ...(timeline.upcoming || []), ...(timeline.recentlyCompleted || []), ...(timeline.failed || [])].slice(0, 12);
  $("eos-missions").innerHTML = rows.length ? rows.map(mission => `
    <div class="office-state">
      <b>${mission.mission_id} / ${mission.mission_name}</b>
      <strong>${mission.status}</strong>
      <span>${mission.priority}</span>
      <span>${(mission.required_offices || []).join(", ")}</span>
    </div>
  `).join("") : `<div class="office-state"><b>No missions queued</b><strong>Sleeping</strong><span>EOS awaits Commander authorization or scheduled obligation.</span></div>`;
  $("eos-suppressed").innerHTML = (eos.suppressedWork || []).slice(-8).reverse().map(item => `
    <div class="office-state">
      <b>${item.category}</b>
      <strong>${item.mission_id}</strong>
      <span>${item.reason}</span>
      <span>Saved $${item.estimated_api_cost_avoided || 0}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No suppressed work</b><strong>Clear</strong><span>Duplicate and unnecessary work has not been detected.</span></div>`;
  renderOfficeDutyOfficers(eos.officeDutyOfficers || state.officeDutyOfficers || {});
}

function renderOfficeDutyOfficers(odo) {
  if (!odo || !$("odo-roster")) return;
  const roster = odo.enterpriseDutyRoster || [];
  $("odo-target").innerHTML = roster.map(item => `<option value="${item.office_id}">${item.office_name}</option>`).join("");
  const selected = roster.find(item => item.office_id === $("odo-target").value) || roster[0];
  const types = selected?.capability_profile?.supported_request_types || ["risk_review"];
  $("odo-request-type").innerHTML = types.map(type => `<option value="${type}">${label(type)}</option>`).join("");
  $("odo-roster").innerHTML = roster.slice(0, 10).map(item => `
    <div class="office-state">
      <b>${item.office_name}</b>
      <strong>${item.current_status}</strong>
      <span>Queue ${item.queue_depth} / Cost $${item.office_wake_cost_estimate}</span>
      <span>Cooldown ${item.cooldown_until || "Clear"}</span>
    </div>
  `).join("");
  $("odo-pending").innerHTML = (odo.pendingRequests || []).slice(0, 8).map(item => `
    <div class="office-state">
      <b>${item.request_id} / ${item.target_office_id}</b>
      <strong>${item.status}</strong>
      <span>${item.priority} / ${item.request_type}</span>
      <span>${item.task_description}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No pending duty requests</b><strong>Clear</strong><span>Sleeping offices are protected.</span></div>`;
  $("odo-wake-recommendations").innerHTML = (odo.wakeRecommendations || []).slice(-8).reverse().map(item => `
    <div class="office-state">
      <b>${item.office_id} / ${item.disposition}</b>
      <strong>${item.wake_justification_score}</strong>
      <span>${item.reason_code}</span>
      <span>Cost $${item.estimated_activation_cost} / Value ${item.expected_operational_value}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No wake recommendations</b><strong>Quiet</strong><span>Duty Officers have not found work that justifies waking a parent office.</span></div>`;
  $("odo-suppressed").innerHTML = (odo.suppressedWork || []).slice(-8).reverse().map(item => `
    <div class="office-state">
      <b>${item.office_id} / ${item.disposition}</b>
      <strong>${item.reason_code}</strong>
      <span>${item.explanation}</span>
      <span>Saved approx $${item.estimated_activation_cost}</span>
    </div>
  `).join("") || `<div class="office-state"><b>No ODO suppressions</b><strong>Clear</strong><span>No duplicate, cached, routed, or deferred requests yet.</span></div>`;
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

function eosControl(action, extra = {}) {
  return api("/api/eos/control", { action, ...extra });
}

function submitDutyOfficerTask() {
  const eos = state.enterpriseOperationsScheduler || state.scheduler?.enterpriseOperationsScheduler || {};
  const mission = (eos.missionRecords || [])[0] || {};
  return api("/api/odo/task", {
    sourceOfficeId: "Commander",
    targetOfficeId: $("odo-target").value,
    missionId: mission.mission_id || "EOS-MANUAL-ODO",
    workflowId: "ODO-WF-COMMANDER",
    executionTokenId: mission.execution_token_id || "ODO-COMMANDER-TOKEN",
    requestType: $("odo-request-type").value,
    taskDescription: $("odo-task").value || "Commander duty officer review",
    priority: "Normal",
    criticality: "Normal",
    estimatedValue: 60,
    estimatedCost: 0.01,
  });
}

function registerFreshnessSample() {
  const now = new Date().toISOString();
  return api("/api/information-freshness/register", {
    information_record_id: $("ifr-record-id").value || `IFR-COMMANDER-${Date.now()}`,
    domain: "analytical_product",
    information_type: "analyst_report",
    subject_type: "ticker",
    subject_id: "ARGOS-SAMPLE",
    ticker: "SPY",
    source_system: "Commander",
    source_record_id: `CMD-SAMPLE-${Date.now()}`,
    source_authority_class: "validated_internal",
    observed_at: now,
    validated_at: now,
    confidence: 0.91,
    validation_state: "VALID",
    payload_reference: "commander_registered_sample",
    field_manifest: ["summary", "valuation", "risk"],
    section_manifest: ["company", "valuation", "risk"],
  });
}

function evaluateFreshnessRecord() {
  return api("/api/information-freshness/evaluate", {
    recordId: $("ifr-record-id").value || "IFR-MARKET-PROVIDER",
    context: {
      decisionUseClass: "tactical_analysis",
      marketState: "open",
      environment: state.environment || "paper",
    },
  });
}

function invalidateFreshnessRecord() {
  return api("/api/information-freshness/invalidate", {
    recordId: $("ifr-record-id").value || "IFR-MARKET-PROVIDER",
    reason: "manual_invalidation",
    affectedSections: ["valuation", "risk"],
    explanation: "Commander requested freshness invalidation.",
  });
}

function admitMemorySample() {
  const now = new Date().toISOString();
  const subject = $("emc-subject").value || "ARGOS-SAMPLE";
  return api("/api/enterprise-memory/admit", {
    cacheRecordId: `EMC-COMMANDER-${Date.now()}`,
    productReference: "commander_sample_memory",
    productType: "office_report",
    productSubtype: "analyst_report",
    environment: state.environment || "development",
    producingOfficeId: "Commander",
    producingServiceId: "ControlPanel",
    subjectType: "ticker",
    subjectId: subject,
    title: "Commander Memory Sample",
    summary: "Validated sample product admitted through Enterprise Memory Bridge.",
    payloadReference: "commander_sample_memory",
    payloadFormat: "json_reference",
    payloadSizeBytes: 256,
    schemaName: "CommanderMemorySample",
    schemaVersion: "1.0",
    confidence: 0.92,
    validationState: "VALID",
    sourceAuthorityClass: "validated_internal",
    fieldManifest: ["summary", "evidence", "risk"],
    sectionManifest: ["overview", "evidence", "risk"],
    decisionUseClasses: ["strategic_analysis", "commander_briefing"],
    contentHash: `sample-${subject}-${now}`,
    createdAt: now,
  });
}

function queryEnterpriseMemory() {
  return api("/api/enterprise-memory/query", {
    requesterType: "commander",
    requesterId: "Commander",
    decisionUseClass: "strategic_analysis",
    environment: state.environment || "development",
    subjectType: "ticker",
    subjectId: $("emc-subject").value || "ARGOS",
    requestedProductTypes: ["office_report", "mission_product", "portfolio_product"],
    requestedFields: ["summary", "evidence", "risk"],
    requestedSections: ["overview", "evidence", "risk"],
    allowLimitedUse: true,
    maximumResults: 8,
  });
}

function invalidateEnterpriseMemory() {
  const recordId = $("emc-subject").value || "EMC-COMMANDER-BRIEFING";
  return api("/api/enterprise-memory/invalidate", {
    recordId,
    reason: "Commander requested memory invalidation.",
    affectedSections: ["risk"],
    fullInvalidation: false,
  });
}

function createWorkflowDeltaBaseline() {
  const subject = $("wch-subject").value || "SPY";
  return api("/api/workflow-delta/baseline", {
    baselineId: `CH-BL-${subject}`,
    missionId: "CMD-DELTA-BASELINE",
    workflowId: "WF-DELTA-BASELINE",
    subjectType: "ticker",
    subjectId: subject,
    ticker: subject,
    environment: state.environment || "development",
    cacheRecordIds: ["EMC-COMMANDER-BRIEFING"],
    informationRecordIds: ["IFR-COMMANDER-BRIEFING"],
    evidenceRecordIds: ["EVD-BASELINE-001"],
    inputManifest: { market: { price: 100, spread: 0.02 }, company: { guidance: "stable" } },
    outputManifest: { analyst: { valuation: 100, thesis: "hold" }, risk: { score: 0.42 } },
    assumptionManifest: { thesis: { core_assumption: "business unchanged" } },
    policyManifest: { risk: { version: "1.0", max_exposure: 0.1 } },
    dependencyManifest: { valuation: ["market.price", "company.guidance"], risk: ["policy.risk.version", "market.price"] },
    workflowManifest: { nodes: ["Librarian", "Analyst", "Risk"] },
    schemaVersions: { analyst_report: "1.0" },
    validationState: "VALID",
  });
}

function analyzeWorkflowDelta() {
  const subject = $("wch-subject").value || "SPY";
  return api("/api/workflow-delta/analyze", {
    deltaRequestId: `CH-REQ-${Date.now()}`,
    requestType: "manual_comparison",
    baselineId: `CH-BL-${subject}`,
    subjectType: "ticker",
    subjectId: subject,
    missionType: "earnings_reassessment",
    decisionUseClass: "strategic_analysis",
    environment: state.environment || "development",
    currentInformationRecordIds: ["IFR-COMMANDER-BRIEFING"],
    currentCacheRecordIds: ["EMC-COMMANDER-BRIEFING"],
    currentEvidenceRecordIds: ["EVD-BASELINE-001", "EVD-GUIDANCE-NEW"],
    requestedProducts: ["office_report", "mission_product"],
    requestedFields: ["market.price", "analyst.valuation", "risk.score"],
    requestedSections: ["valuation", "risk"],
    currentState: {
      inputManifest: { market: { price: 102.5, spread: 0.03 }, company: { guidance: "raised" } },
      outputManifest: { analyst: { valuation: 104, thesis: "hold" }, risk: { score: 0.48 } },
      assumptionManifest: { thesis: { core_assumption: "business unchanged" } },
      policyManifest: { risk: { version: "1.0", max_exposure: 0.1 } },
      dependencyManifest: { valuation: ["market.price", "company.guidance"], risk: ["policy.risk.version", "market.price"] },
      workflowManifest: { nodes: ["Librarian", "Analyst", "Risk"] },
    },
  });
}

function latestWorkflowDeltaPackageId() {
  const packages = state.workflowDeltaEngine?.deltaPackages || [];
  return packages[packages.length - 1]?.delta_package_id || "CH-PKG-000001";
}

function exportWorkflowDeltaPackage() {
  return api("/api/workflow-delta/export", {
    packageId: latestWorkflowDeltaPackageId(),
    format: "markdown",
  });
}

function replayWorkflowDeltaPackage() {
  return api("/api/workflow-delta/replay", {
    packageId: latestWorkflowDeltaPackageId(),
  });
}

function requestWorkflowDeltaReview() {
  return api("/api/workflow-delta/review", {
    packageId: latestWorkflowDeltaPackageId(),
    action: "request_validation_review",
    reason: "Commander requested delta package review from the Bridge.",
  });
}

function evaluateEnterprisePriority() {
  return api("/api/enterprise-priority/evaluate", {});
}

function replayEnterprisePriority() {
  return api("/api/enterprise-priority/replay", {});
}

function scanPositionMonitoringNetwork() {
  return api("/api/position-monitoring/scan", {});
}

function replayPositionMonitoringNetwork() {
  return api("/api/position-monitoring/replay", {});
}

function publishCommunicationsSample() {
  return api("/api/communications-bus/publish", {
    summary: "Commander requested EO-CL transport verification.",
    severity: "INFO",
    messageType: "SYSTEM_NOTIFICATION",
    targetTopic: "commander.system",
  });
}

function replayLatestCommunication() {
  const message = (state.enterpriseCommunicationsBus?.messageStream || [])[0];
  return api("/api/communications-bus/replay", {
    messageId: message?.message_id || "",
    analytical: true,
  });
}

function traceLatestCommunication() {
  const message = (state.enterpriseCommunicationsBus?.messageStream || [])[0];
  return api("/api/communications-bus/trace", {
    correlationId: message?.correlation_id || "",
  });
}

function retryLatestDeadLetter() {
  const dead = (state.enterpriseCommunicationsBus?.deadLetters || [])[0];
  return api("/api/communications-bus/retry", {
    deadLetterId: dead?.dead_letter_id || "",
    authorization: { commanderAuthorized: false },
  });
}

function refreshEfficiencyAnalytics() {
  return api("/api/efficiency-analytics/refresh", {
    windowStart: "current_operating_day",
    windowEnd: "latest_state_snapshot",
    mode: "COMBINED",
  });
}

function recalculateLatestEfficiencyMetric() {
  const metric = (state.enterpriseEfficiencyAnalytics?.metricValues || [])[0];
  return api("/api/efficiency-analytics/recalculate", {
    metricValueId: metric?.metric_value_id || "",
  });
}

function inspectLatestEfficiencyLineage() {
  const metric = (state.enterpriseEfficiencyAnalytics?.metricValues || [])[0];
  return api("/api/efficiency-analytics/lineage", {
    metricValueId: metric?.metric_value_id || "",
  });
}

function compareEfficiencySnapshot() {
  const analytics = state.enterpriseEfficiencyAnalytics || {};
  return api("/api/efficiency-analytics/compare", {
    left: analytics,
    right: analytics,
  });
}

function acknowledgeLatestEfficiencyFinding() {
  const finding = (state.enterpriseEfficiencyAnalytics?.findings || [])[0];
  return api("/api/efficiency-analytics/acknowledge", {
    findingId: finding?.finding_id || "",
    reason: "Commander acknowledged efficiency finding from bridge.",
  });
}

function latestDoctrinePolicyVersion(statuses = []) {
  const versions = state.enterpriseDoctrinePolicyManager?.policyVersions || [];
  const allowed = statuses.length ? statuses : ["AWAITING_APPROVAL", "APPROVED", "SCHEDULED", "STAGING", "ACTIVE"];
  return [...versions].reverse().find(item => allowed.includes(item.status)) || versions[versions.length - 1] || {};
}

function latestDoctrineActivationPlan() {
  const plans = state.enterpriseDoctrinePolicyManager?.activationPlans || [];
  return plans[plans.length - 1] || {};
}

function submitDoctrinePolicyDraft() {
  return api("/api/doctrine-policy/submit", {
    policyDomain: "PRIORITY",
    policyId: "CO-POL-PRIORITY",
    schemaId: "CO-SCHEMA-PRIORITY",
    semanticVersion: `1.0.${Date.now()}`,
    summary: "Commander sample priority policy draft.",
    changeSummary: "Demonstrates EO-CO deterministic draft submission without activation.",
    rationale: "Bridge verification.",
    configuration: {
      enabled: true,
      modeApplicability: "BOTH",
      acknowledgementRequired: true,
      priorityThreshold: 75,
      selfWakeAllowed: false,
      workflowTokenParallelOwners: 1,
      paperLiveSharedState: false,
      brokerReconciliationRequired: true,
      aiExpenditureUnbounded: false,
      immutableLedgerRewriteAllowed: false,
    },
    idempotencyKey: `eco-submit-${Date.now()}`,
  });
}

function approveLatestDoctrinePolicy() {
  const version = latestDoctrinePolicyVersion(["AWAITING_APPROVAL"]);
  return api("/api/doctrine-policy/approve", {
    policyVersionId: version.policy_version_id || "",
    approver: "Commander",
    authority: "Commander",
    reason: "Commander approved after EO-CO deterministic validation.",
  });
}

function stageLatestDoctrinePolicy() {
  const version = latestDoctrinePolicyVersion(["APPROVED"]);
  return api("/api/doctrine-policy/schedule", {
    policyVersionId: version.policy_version_id || "",
    activationStrategy: "STAGED",
    targetSubscribers: ["Enterprise Priority Engine"],
    acknowledgementRequirements: ["ACTIVE"],
  });
}

function activateLatestDoctrinePolicy() {
  const plan = latestDoctrineActivationPlan();
  return api("/api/doctrine-policy/activate", {
    activationPlanId: plan.activation_plan_id || "",
  });
}

function issueRestrictiveDoctrineDirective() {
  return api("/api/doctrine-policy/directive", {
    policyDomain: "ENTERPRISE_MODE",
    issuer: "Commander",
    urgency: "high",
    rationale: "Commander requested temporary restrictive policy visibility check.",
    expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
    requestedChange: {
      newLiveOrdersEnabled: false,
      paperOnlyMode: true,
    },
  });
}

function recordDoctrinePolicyDrift() {
  const matrix = state.enterpriseDoctrinePolicyManager?.activePolicyMatrix || [];
  const cost = matrix.find(item => item.policyDomain === "COST_GOVERNANCE") || matrix[0] || {};
  return api("/api/doctrine-policy/drift", {
    subscriberId: "Enterprise Cost Governor",
    policyVersionId: cost.policyVersionId || cost.policy_version_id || "",
    actualValues: {
      enabled: true,
      modeApplicability: "BOTH",
      acknowledgementRequired: true,
      budgetCeilingUsd: 999,
      selfWakeAllowed: false,
    },
  });
}

function replayDoctrinePolicy() {
  const version = latestDoctrinePolicyVersion(["ACTIVE"]);
  return api("/api/doctrine-policy/replay", {
    policyVersionId: version.policy_version_id || "",
  });
}

function analyzeDoctrinePolicyImpact() {
  const version = latestDoctrinePolicyVersion(["ACTIVE"]);
  return api("/api/doctrine-policy/impact", {
    policyVersionId: version.policy_version_id || "",
  });
}

async function requestCommanderBriefing(briefingType) {
  await api("/api/cnac/briefing", { briefingType });
  $("commander-strategic-dashboard")?.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function init() {
  $("refresh-btn").addEventListener("click", () => api("/api/state"));
  $("system-health-report").addEventListener("click", () => requestCommanderBriefing("morning_readiness"));
  $("bridge-start-paper").addEventListener("click", () => api("/api/paper/start", {}));
  $("bridge-halt").addEventListener("click", () => api("/api/paper/halt", {}));
  $("bridge-pause").addEventListener("click", () => api("/api/bridge/pause", {}));
  $("bridge-step").addEventListener("click", () => api("/api/bridge/step", {}));
  $("bridge-replay").addEventListener("click", startLatestBridgeReplay);
  $("bridge-lab").addEventListener("click", openBridgeLab);
  $("bridge-commander-report").addEventListener("click", () => requestCommanderBriefing("Daily Enterprise Report"));
  $("cdw-journal-save").addEventListener("click", () => {
    recordCommanderJournalEntry().then(() => { $("cdw-journal-entry").value = ""; });
  });
  $("bridge-office-hud").addEventListener("click", (event) => {
    const button = event.target.closest("[data-bridge-view]");
    if (button) navigateBridge(button.dataset.bridgeView);
  });
  $("csd-navigation").addEventListener("click", (event) => {
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
  $("risk-office-nav").addEventListener("click", (event) => {
    const button = event.target.closest("[data-bridge-view]");
    if (button) navigateBridge(button.dataset.bridgeView);
  });
  $("risk-return-executive").addEventListener("click", () => navigateBridge("executive_bridge"));
  $("risk-open-executive").addEventListener("click", () => navigateBridge("executive_bridge"));
  $("risk-pause").addEventListener("click", () => api("/api/bridge/pause", {}));
  $("risk-resume").addEventListener("click", () => api("/api/bridge/resume", {}));
  $("risk-replay").addEventListener("click", startLatestBridgeReplay);
  $("risk-open-lab").addEventListener("click", openBridgeLab);
  $("risk-open-engineering").addEventListener("click", () => toggleEngineeringMode(true));
  $("risk-subcommand-bridge").addEventListener("click", (event) => {
    if (event.target.closest(".risk-replay-inline")) startLatestBridgeReplay();
  });
  $("trader-office-nav").addEventListener("click", (event) => {
    const button = event.target.closest("[data-bridge-view]");
    if (button) navigateBridge(button.dataset.bridgeView);
  });
  $("trader-return-executive").addEventListener("click", () => navigateBridge("executive_bridge"));
  $("trader-open-executive").addEventListener("click", () => navigateBridge("executive_bridge"));
  $("trader-pause").addEventListener("click", () => api("/api/bridge/pause", {}));
  $("trader-resume").addEventListener("click", () => api("/api/bridge/resume", {}));
  $("trader-cancel-pending").addEventListener("click", () => api("/api/trader/cancel-pending-orders", {}));
  $("trader-replay").addEventListener("click", startLatestBridgeReplay);
  $("trader-open-lab").addEventListener("click", openBridgeLab);
  $("trader-open-engineering").addEventListener("click", () => toggleEngineeringMode(true));
  $("trader-subcommand-bridge").addEventListener("click", (event) => {
    if (event.target.closest(".trader-replay-inline")) startLatestBridgeReplay();
  });
  $("historian-office-nav").addEventListener("click", (event) => {
    const button = event.target.closest("[data-bridge-view]");
    if (button) navigateBridge(button.dataset.bridgeView);
  });
  $("historian-return-executive").addEventListener("click", () => navigateBridge("executive_bridge"));
  $("historian-open-executive").addEventListener("click", () => navigateBridge("executive_bridge"));
  $("historian-replay-workflow").addEventListener("click", startLatestBridgeReplay);
  $("historian-open-lab").addEventListener("click", openBridgeLab);
  $("historian-generate-report").addEventListener("click", () => api("/api/historian/generate-learning-report", {}));
  $("historian-compare-prompts").addEventListener("click", () => api("/api/historian/compare-prompt-versions", {}));
  $("historian-compare-strategies").addEventListener("click", () => api("/api/historian/compare-strategies", {}));
  $("historian-open-engineering").addEventListener("click", () => toggleEngineeringMode(true));
  $("historian-subcommand-bridge").addEventListener("click", (event) => {
    if (event.target.closest(".historian-replay-inline")) startLatestBridgeReplay();
  });
  $("librarian-office-nav").addEventListener("click", (event) => {
    const button = event.target.closest("[data-bridge-view]");
    if (button) navigateBridge(button.dataset.bridgeView);
  });
  $("librarian-return-executive").addEventListener("click", () => navigateBridge("executive_bridge"));
  $("librarian-open-executive").addEventListener("click", () => navigateBridge("executive_bridge"));
  $("librarian-open-historian").addEventListener("click", () => navigateBridge("historian_bridge"));
  $("librarian-replay").addEventListener("click", startLatestBridgeReplay);
  $("librarian-open-lab").addEventListener("click", openBridgeLab);
  $("librarian-open-engineering").addEventListener("click", () => toggleEngineeringMode(true));
  $("librarian-search-button").addEventListener("click", () => {
    activeLibrarianQuery = $("librarian-search-input").value.trim();
    renderLibrarianBridge();
  });
  $("librarian-search-input").addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      activeLibrarianQuery = $("librarian-search-input").value.trim();
      renderLibrarianBridge();
    }
  });
  $("librarian-subcommand-bridge").addEventListener("click", (event) => {
    const queryNode = event.target.closest("[data-librarian-query]");
    if (queryNode) {
      activeLibrarianQuery = queryNode.dataset.librarianQuery || "";
      renderLibrarianBridge();
    }
  });
  $("academy-office-nav").addEventListener("click", (event) => {
    const button = event.target.closest("[data-bridge-view]");
    if (button) navigateBridge(button.dataset.bridgeView);
  });
  $("academy-return-executive").addEventListener("click", () => navigateBridge("executive_bridge"));
  $("sic-office-nav").addEventListener("click", (event) => {
    const button = event.target.closest("[data-bridge-view]");
    if (button) navigateBridge(button.dataset.bridgeView);
  });
  $("sic-return-command").addEventListener("click", () => navigateBridge("command_bridge"));
  $("sic-open-engineering").addEventListener("click", () => toggleEngineeringMode(true));
  $("sic-offices").addEventListener("click", (event) => {
    const target = event.target.closest("[data-bridge-view]");
    if (target) navigateBridge(target.dataset.bridgeView);
  });
  $("boio-return-sic").addEventListener("click", () => navigateBridge("strategic_intelligence_bridge"));
  $("boio-open-engineering").addEventListener("click", () => toggleEngineeringMode(true));
  $("dio-return-sic").addEventListener("click", () => navigateBridge("strategic_intelligence_bridge"));
  $("dio-open-engineering").addEventListener("click", () => toggleEngineeringMode(true));
  $("dclio-return-sic").addEventListener("click", () => navigateBridge("strategic_intelligence_bridge"));
  $("dclio-open-engineering").addEventListener("click", () => toggleEngineeringMode(true));
  $("soo-return-sic").addEventListener("click", () => navigateBridge("strategic_intelligence_bridge"));
  $("soo-open-engineering").addEventListener("click", () => toggleEngineeringMode(true));
  $("msio-return-sic").addEventListener("click", () => navigateBridge("strategic_intelligence_bridge"));
  $("msio-open-engineering").addEventListener("click", () => toggleEngineeringMode(true));
  $("crio-return-sic").addEventListener("click", () => navigateBridge("strategic_intelligence_bridge"));
  $("crio-open-engineering").addEventListener("click", () => toggleEngineeringMode(true));
  $("sso-return-sic").addEventListener("click", () => navigateBridge("strategic_intelligence_bridge"));
  $("sso-open-engineering").addEventListener("click", () => toggleEngineeringMode(true));
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
  $("eos-enable").addEventListener("click", () => eosControl("enable"));
  $("eos-disable").addEventListener("click", () => eosControl("disable"));
  $("eos-set-mode").addEventListener("click", () => eosControl("set_mode", { mode: $("eos-mode").value }));
  $("eos-run-mission").addEventListener("click", () => eosControl("run_mission_now", { templateId: $("eos-template").value }));
  $("eos-cancel-mission").addEventListener("click", () => eosControl("cancel", { missionId: $("eos-cancel-id").value }));
  $("emp-create-request").addEventListener("click", () => api("/api/mission-planner/commander-request", { objective: $("emp-commander-request").value || "Generate a bounded Commander briefing", missionType: "commander_briefing", submitToScheduler: false }));
  $("emp-replay").addEventListener("click", () => api("/api/mission-planner/replay", { triggers: [] }));
  $("ecg-reserve").addEventListener("click", () => api("/api/cost-governor/reserve", { missionPlanId: $("ecg-plan-id").value }));
  $("ifr-evaluate").addEventListener("click", evaluateFreshnessRecord);
  $("ifr-register").addEventListener("click", registerFreshnessSample);
  $("ifr-invalidate").addEventListener("click", invalidateFreshnessRecord);
  $("emc-query").addEventListener("click", queryEnterpriseMemory);
  $("emc-admit").addEventListener("click", admitMemorySample);
  $("emc-invalidate").addEventListener("click", invalidateEnterpriseMemory);
  $("wch-baseline").addEventListener("click", createWorkflowDeltaBaseline);
  $("wch-analyze").addEventListener("click", analyzeWorkflowDelta);
  $("wch-export").addEventListener("click", exportWorkflowDeltaPackage);
  $("wch-replay").addEventListener("click", replayWorkflowDeltaPackage);
  $("wch-review").addEventListener("click", requestWorkflowDeltaReview);
  $("epj-evaluate").addEventListener("click", evaluateEnterprisePriority);
  $("epj-replay").addEventListener("click", replayEnterprisePriority);
  $("pmn-scan").addEventListener("click", scanPositionMonitoringNetwork);
  $("pmn-replay").addEventListener("click", replayPositionMonitoringNetwork);
  $("ecl-publish").addEventListener("click", publishCommunicationsSample);
  $("ecl-replay").addEventListener("click", replayLatestCommunication);
  $("ecl-trace-latest").addEventListener("click", traceLatestCommunication);
  $("ecl-retry").addEventListener("click", retryLatestDeadLetter);
  $("ecn-refresh").addEventListener("click", refreshEfficiencyAnalytics);
  $("ecn-recalculate").addEventListener("click", recalculateLatestEfficiencyMetric);
  $("ecn-lineage-latest").addEventListener("click", inspectLatestEfficiencyLineage);
  $("ecn-compare").addEventListener("click", compareEfficiencySnapshot);
  $("ecn-acknowledge").addEventListener("click", acknowledgeLatestEfficiencyFinding);
  $("eco-submit-safe").addEventListener("click", submitDoctrinePolicyDraft);
  $("eco-approve-latest").addEventListener("click", approveLatestDoctrinePolicy);
  $("eco-stage-latest").addEventListener("click", stageLatestDoctrinePolicy);
  $("eco-activate-latest").addEventListener("click", activateLatestDoctrinePolicy);
  $("eco-restrictive-directive").addEventListener("click", issueRestrictiveDoctrineDirective);
  $("eco-drift-sample").addEventListener("click", recordDoctrinePolicyDrift);
  $("eco-replay").addEventListener("click", replayDoctrinePolicy);
  $("eco-impact").addEventListener("click", analyzeDoctrinePolicyImpact);
  $("ede-observe").addEventListener("click", () => api("/api/event-detection/observe", {}));
  $("ede-replay").addEventListener("click", () => api("/api/event-detection/replay", { observations: [] }));
  $("odo-target").addEventListener("change", renderScheduler);
  $("odo-submit").addEventListener("click", submitDutyOfficerTask);
  await api("/api/state");
  setInterval(() => api("/api/state"), 5000);
}

init().catch((error) => {
  if (error.message === "ARGOS_CONTROL_PANEL_REQUIRES_LOCAL_SERVER" || window.location.protocol === "file:") {
    renderFileProtocolNotice();
    return;
  }
  document.body.innerHTML = `<pre>${error.stack}</pre>`;
});

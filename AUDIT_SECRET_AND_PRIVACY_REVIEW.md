# AUDIT Secret and Privacy Review

No actual `.env` file, private key, broker credential file, or local credential store is tracked. `.env.example` is the sanitized template. Secret-like terms are reported without printing values.

| File examined | May contain sensitive information | Treatment | Reason | Sanitized template created |
|---|---:|---|---|---:|
| `.env.example` | yes | included | Sanitized environment template with placeholder credential fields only. | yes |
| `.gitignore` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `0. Project Management/README.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `1. Foundation/README.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `2. Executive Group/README.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `3. Seeker Group/README.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `4. Analyst Group/README.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `5. Risk Office/README.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `6. Trader Group/README.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `7. Historian Group/README.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `8. Librarian Group/README.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `9. Academy/README.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/EO-CA_Enterprise_Operations_Scheduler.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/EO-CB_Office_Duty_Officer.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/EO-CC_Event_Detection_Engine.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/EO-CD_Enterprise_Mission_Planner.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/EO-CE_Enterprise_Cost_Governor.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/EO-CF_Information_Freshness_Engine.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/EO-CG_Enterprise_Memory_Cache.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/EO-CH_Workflow_Delta_Engine.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/EO-CJ_Enterprise_Priority_Engine.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/EO-CK_Position_Monitoring_Network.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/EO-CL_Enterprise_Communications_Bus.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/EO-CN_Enterprise_Efficiency_Analytics.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-001_Authority_Boundary_Audit.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-001_Dependency_Graph_Report.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/OR-001_Engineering_Order_Traceability_Matrix.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/OR-001_LAW_VII_Compliance_Report.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-001_Operational_Readiness_Checklist.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-001_Persistence_Coverage_Report.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-001_Placeholder_Synthetic_Logic_Report.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-001_Prioritized_Remediation_Roadmap.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-001_Repository_Architecture_Report.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-001_Runtime_Integration_Report.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-002_Completion_Report.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-002_EO-Y_Mutation_Root_Cause.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/OR-002_Remaining_Provisional_Surfaces.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-002_Synthetic_Truth_Inventory.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-002_Test_Report.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-002_Truth_Domain_and_Provenance_Model.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-003_Broker_Architecture.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-003_Completion_Report.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-003_Execution_Quality.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-003_Fill_Model.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-003_Order_Lifecycle.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-003_Remaining_Gaps.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-003_Test_Report.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-004_Completion_Report.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-004_Exit_Authority_Model.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-004_Legacy_Test_Classification.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-004_Monitoring_and_Reassessment_Model.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/OR-004_Persistence_and_Recovery_Requirements.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-004_Position_Lifecycle_Architecture.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-004_Position_Reconciliation_Specification.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-004_Position_and_Trade_Identity_Model.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-004_Synthetic_Truth_Remediation_Report.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-004_Test_Report.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-005_Canonical_Runtime_Architecture.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-005_Legacy_Runtime_Path_Inventory.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-005_Part_1_Implementation_Report.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-005_Part_1_Test_Report.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-005_Read_Only_Runtime_Surface_Audit.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-005_Runtime_Authority_Model.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-005_Scheduler_Mission_and_Duty_Model.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-005_Series_C_Component_Inventory.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/OR-005_Strategic_Intelligence_to_Seeker_Integration.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/OR-005_Workflow_Token_Integration_Audit.md` | yes | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/OR-006_Checkpoint_Restore_Model.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-006_Completion_Report.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-006_Corruption_Detection_Model.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-006_End_to_End_Restart_Test_Report.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-006_Enterprise_Persistence_Architecture.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-006_Entity_Identity_Model.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-006_Long_Duration_Runtime_Report.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/OR-006_Part_1_Implementation_Report.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-006_Part_1_Test_Report.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-006_Persistence_Failure_Model.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/OR-006_Persistence_Inventory.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-006_Reconciliation_Model.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-006_Recovery_Architecture.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-006_Recovery_Test_Report.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/OR-006_Restore_Sequence.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-006_Runtime_Checkpoint_Model.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-006_Runtime_Recovery_Audit.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/OR-006_Schema_Versioning_Model.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/OR-006_State_Ownership_Model.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-006_Transaction_Boundary_Model.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/OR-007_Authority_Certification.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-007_Certification_Matrix.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-007_Completion_Report.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/OR-007_Cost_Certification.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/OR-007_Determinism_Certification.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/OR-007_Enterprise_Boundary_Audit.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-007_Enterprise_Certification_Framework.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-007_Enterprise_Certification_Report.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-007_Enterprise_Certification_Scorecard.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-007_Enterprise_Integrity_Report.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/OR-007_Failure_Certification.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/OR-007_Final_Operational_Readiness_Assessment.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-007_Final_Synthetic_Truth_Audit.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/OR-007_LAW_VII_Certification.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-007_Long_Duration_Runtime_Report.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/OR-007_Long_Duration_Test_Framework.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-007_Operational_Integrity_Report.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-007_Operational_Readiness_Matrix.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-007_Part_1_Implementation_Report.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/OR-007_Part_1_Test_Report.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/OR-007_Persistence_Certification.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-007_Replay_Certification.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-007_Resource_Utilization_Report.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/OR-007_Security_Boundary_Report.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-007_Stress_Test_Report.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/OR-007_Synthetic_Truth_Final_Audit.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/README.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/academy_framework.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/academy_fusion_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/academy_operational_readiness.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/alternative_data_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/analyst_department_framework.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/analyst_operational_readiness.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/analyst_technical_analysis_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/analytical_fusion_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/argos_control_panel_dashboard.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/audit_traceability_framework.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/behavioral_analysis_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/broker_integration_office.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/bubble_detection_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/canonical_data_contract_framework.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/case_study_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/chief_of_staff.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/command_console.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/commander_decision_engine.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/commander_notification_alert_center.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/configuration_environment_framework.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/cross_discipline_review_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/cryptocurrency_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/curriculum_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/database_persistence_foundation.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/decision_evaluation_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/derivatives_analysis_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/deterministic_communication_courier_framework.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/doctrine_management_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/enterprise_activity_bus.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/enterprise_command_center.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/enterprise_credit_governor.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/event_intelligence_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/evidence_evaluation_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/execution_quality_office.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/executive_dashboard.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/executive_group_framework.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/executive_operational_readiness.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/executive_workflow.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/finance_tutor_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/foundation_operational_readiness.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/foundation_testing_framework.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/fundamental_analysis_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/fundamental_research_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/fusion_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/historian_fusion_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/historian_group_framework.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/historian_operational_readiness.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/human_override_kill_switch.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/hypothesis_validation_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/identity_framework.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/infrastructure_ai_resource_management.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/institutional_knowledge_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/instruction_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/interactive_organization_explorer.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/knowledge_assessment_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/knowledge_graph_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/learning_integration_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/librarian_fusion_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/librarian_group_framework.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/librarian_operational_readiness.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/liquidity_risk_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/live_portfolio_performance_console.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/macroeconomic_analysis_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/macroeconomic_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/model_calibration_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/news_sentiment_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/office_operating_modes_scheduling.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/options_flow_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/order_management_office.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/performance_measurement_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/portfolio_risk_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/position_management_office.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/position_risk_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/prompt_evaluation_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/prompt_specification_repository.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/recovery_planning_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/risk_fusion_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/risk_interaction_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/risk_office_framework.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/risk_operational_readiness.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/seeker_department_framework.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/seeker_operational_readiness.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/specification_repository_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/statistical_analysis_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/tail_risk_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/technical_analysis_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Documentation/trade_execution_office.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/trade_monitoring_office.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/trader_fusion_office.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/trader_group_framework.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/trader_operational_readiness.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/treasury_trading_control_panel.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Documentation/volatility_risk_office.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Launch_ARGOS_Control_Panel.cmd` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `PROJECT_HANDOFF.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `README.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Scripts/README.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Scripts/launch_argos_control_panel.ps1` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Scripts/start_argos_control_panel.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Scripts/verify_repository_structure.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/README.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Tests/test_academy_framework.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_academy_fusion_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_academy_readiness.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Tests/test_alternative_data_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_analyst_department_framework.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_analyst_readiness.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Tests/test_analyst_technical_analysis_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_analytical_fusion_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_argos_control_panel_dashboard.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_audit_framework.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Tests/test_behavioral_analysis_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_broker_integration_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_bubble_detection_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_case_study_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_chief_of_staff.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_command_console.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Tests/test_commander_decision_engine.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_commander_notification_alert_center.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Tests/test_communication_framework.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Tests/test_configuration_framework.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_contract_framework.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Tests/test_cross_discipline_review_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_cryptocurrency_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_curriculum_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_decision_evaluation_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_derivatives_analysis_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_doctrine_management_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_enterprise_activity_bus.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_enterprise_command_center.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Tests/test_enterprise_credit_governor.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_event_intelligence_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_evidence_evaluation_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_execution_quality_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_executive_dashboard.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_executive_framework.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_executive_readiness.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Tests/test_executive_workflow.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_finance_tutor_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_foundation_readiness.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Tests/test_foundation_testing_framework.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Tests/test_fundamental_analysis_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_fundamental_research_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_fusion_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_historian_fusion_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_historian_group_framework.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_historian_readiness.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Tests/test_human_override.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Tests/test_hypothesis_validation_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_identity_framework.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Tests/test_infrastructure_resource_management.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_institutional_knowledge_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_instruction_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_interactive_organization_explorer.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Tests/test_knowledge_assessment_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_knowledge_graph_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_learning_integration_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_librarian_fusion_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_librarian_group_framework.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_librarian_readiness.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Tests/test_liquidity_risk_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_live_portfolio_performance_console.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_macroeconomic_analysis_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_macroeconomic_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_model_calibration_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_news_sentiment_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_office_operating_modes_scheduler.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Tests/test_options_flow_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_or003_paper_brokerage.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_or004_position_lifecycle.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_or005_canonical_runtime.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_or006_enterprise_persistence.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_or007_enterprise_certification.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Tests/test_order_management_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_performance_measurement_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_persistence_framework.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_portfolio_risk_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_position_management_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_position_risk_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_prompt_evaluation_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_prompt_specification_repository.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Tests/test_recovery_planning_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_repository_structure.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Tests/test_risk_fusion_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_risk_interaction_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_risk_office_framework.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_risk_readiness.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Tests/test_seeker_department_framework.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_seeker_readiness.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `Tests/test_specification_repository_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_statistical_analysis_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_tail_risk_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_technical_analysis_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_trade_execution_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_trade_monitoring_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_trader_fusion_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_trader_group_framework.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_trader_readiness.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_treasury_trading_control_panel.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `Tests/test_volatility_risk_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `outputs/ARGOS_Git_Style_Snapshot_2026-07-08.md` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `outputs/Authorization_to_Proceed_Group_2.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `outputs/Authorization_to_Proceed_Group_3_Seeker.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `outputs/E-ORR_Executive_Operational_Readiness_Report.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `outputs/ECR-001_Executive_Completion_Report.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `outputs/FCR-001_Foundation_Completion_Report.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `outputs/ORR-001_Operational_Readiness_Report.md` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `pyproject.toml` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/__init__.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/academy/__init__.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/academy/case_study.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/academy/curriculum.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/academy/finance_tutor.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/academy/framework.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/academy/fusion.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/academy/instruction.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/academy/knowledge_assessment.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/academy/readiness.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/analyst/__init__.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/analyst/analytical_fusion.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/analyst/behavioral.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/analyst/cross_discipline.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/analyst/department.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/analyst/derivatives.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/analyst/fundamental.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/analyst/macroeconomic.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/analyst/offices.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/analyst/readiness.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/analyst/risk_interaction.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/analyst/statistical.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/analyst/technical.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/control_panel/__init__.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/api_execution_gateway.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/api_runtime_monitor.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/black_swan_simulation_engine.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/blue_ocean_intelligence_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/canonical_enterprise_runtime.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/capital_allocation_engine.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/capital_rotation_intelligence_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/closed_position_truth.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/cnac.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/control_panel/cognitive_contract.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/cognitive_pilot.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/command_console.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/commander_briefing_generator.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/control_panel/commander_daily_review_workspace.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/commander_strategic_dashboard.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/correlation_intelligence_engine.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/credit_governor.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/daily_learning_pipeline.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/decision_explainability_engine.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/decision_laboratory.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/decision_object_quality_scoring.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/decision_object_schema.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/decline_intelligence_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/disruption_intelligence_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/eab.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/control_panel/ecc.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/enterprise_benchmark_engine.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/enterprise_certification.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/enterprise_communications_bus.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/enterprise_configuration_registry.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/enterprise_cost_governor.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/enterprise_doctrine_policy_manager.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/enterprise_efficiency_analytics.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/enterprise_experiment_scheduler.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/enterprise_failure_recovery.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/enterprise_grand_strategy_engine.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/enterprise_health_monitor.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/enterprise_learning_engine.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/enterprise_memory_cache.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/enterprise_operational_guardrails.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/enterprise_persistence.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/enterprise_priority_engine.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/enterprise_reality_calibration.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/enterprise_reproducibility_framework.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/enterprise_risk_factor_engine.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/event_detection_engine.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/historian_recommendation_engine.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/information_freshness_engine.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/infrastructure.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/ioe.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/control_panel/lppc.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/market_context_engine.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/market_data_provider.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/market_replay_engine.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/market_structure_intelligence_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/mission_planner.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/monte_carlo_portfolio_engine.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/office_duty_officer.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/performance_truth_engine.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/portfolio_construction_engine.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/position_exit_decision_engine.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/position_lifecycle_manager.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/position_monitoring_network.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/position_registry.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/position_sizing_engine.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/position_surveillance_engine.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/prompt_evolution_engine.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/prompt_package_manager.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/runtime.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/scheduler.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/server.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/short_opportunity_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/strategic_intelligence_command.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/strategic_synthesis_office.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/strategy_package_manager.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/strategy_performance_console.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/stress_testing_engine.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/trade_attribution_engine.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/truth_domain.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/workflow_delta_engine.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/workflow_orchestrator.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/control_panel/workflow_runtime_monitor.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/executive/__init__.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/executive/briefing.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/executive/cdr.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/executive/chief_of_staff.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/executive/commander.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/executive/control_panel.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/executive/dashboard.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/executive/decisions.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/executive/engine.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/executive/mailboxes.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/executive/override.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/executive/readiness.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/executive/workflow.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/foundation/__init__.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/foundation/audit/__init__.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/foundation/audit/events.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/foundation/audit/log.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/foundation/audit/service.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/foundation/audit/trace.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/foundation/communication/__init__.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/foundation/communication/courier.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/foundation/communication/mailboxes.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/foundation/configuration/__init__.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/foundation/configuration/environment.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/foundation/configuration/service.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/foundation/contracts/__init__.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/foundation/contracts/base.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/foundation/identity/__init__.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/foundation/identity/identifiers.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/foundation/identity/registry.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/foundation/persistence/__init__.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/foundation/persistence/backup.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/foundation/persistence/migrations.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/foundation/persistence/records.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/foundation/persistence/repository.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/foundation/persistence/services.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/foundation/prompts/__init__.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/foundation/prompts/dependencies.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/foundation/prompts/prompts.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/foundation/prompts/specifications.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/foundation/readiness/__init__.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/foundation/readiness/reports.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/foundation/readiness/verifier.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/foundation/testing/__init__.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/foundation/testing/registry.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/foundation/testing/reports.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/foundation/testing/runner.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/historian/__init__.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/historian/decision_evaluation.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/historian/evidence_evaluation.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/historian/fusion.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/historian/group.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/historian/hypothesis.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/historian/model_calibration.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/historian/performance.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/historian/prompt_evaluation.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/historian/readiness.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/librarian/__init__.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/librarian/doctrine_management.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/librarian/fusion.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/librarian/group.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/librarian/institutional_knowledge.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/librarian/knowledge_graph.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/librarian/learning_integration.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/librarian/readiness.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/librarian/specification_repository.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/risk/__init__.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/risk/bubble.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/risk/department.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/risk/fusion.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/risk/liquidity.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/risk/offices.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/risk/portfolio.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/risk/position.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/risk/readiness.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/risk/recovery.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/risk/tail.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/risk/volatility.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/seeker/__init__.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/seeker/alternative_data.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/seeker/cryptocurrency.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/seeker/department.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/seeker/event_intelligence.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/seeker/fundamental.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/seeker/fusion.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/seeker/macroeconomic.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/seeker/news_sentiment.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/seeker/offices.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/seeker/options_flow.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/seeker/readiness.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/seeker/technical.py` | no | included | Tracked audit candidate file; no actual credential value printed or detected by filename. | no |
| `src/argos/trader/__init__.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/trader/broker_integration.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/trader/execution_quality.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/trader/fusion.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/trader/group.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/trader/offices.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/trader/order_management.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/trader/paper_brokerage.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/trader/position_management.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/trader/readiness.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/trader/trade_execution.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `src/argos/trader/trade_monitoring.py` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `ui/argos_control_panel/app.js` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `ui/argos_control_panel/index.html` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |
| `ui/argos_control_panel/styles.css` | yes | included | Contains sensitive-domain words such as token/broker/credential as source or documentation labels. | no |

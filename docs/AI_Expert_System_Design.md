# AI Expert System Design for FARMZY

## 1. Expert System Architecture

FARMZY is organized as a layered expert-system architecture in which IoT observations from the field are transformed into actionable irrigation decisions through symbolic reasoning and statistical learning. The Knowledge Base stores production rules authored from agronomic expertise, as well as calibrated threshold bands for soil moisture, temperature, nutrient status, and pH stress. The Inference Engine operates in forward-chaining mode and continuously evaluates incoming facts from the working memory. In this design, each sensor packet is treated as a fact vector that includes nitrogen, phosphorus, potassium, ambient temperature, relative humidity, pH, gas concentration, and soil moisture. When new facts arrive, the engine performs condition matching and creates a conflict set of candidate rules.

Conflict resolution in FARMZY follows a deterministic hierarchy. First, priority ordering ensures that emergency rules such as critical dryness dominate advisory rules. Second, specificity ranking favors rules with tighter antecedent structures, which reduces false activation for broad safety rules. Third, recency semantics are preserved through timestamped working memory so that later facts can supersede stale conclusions where environmental drift is high. This sequence enables stable behavior under noisy IoT streams and avoids oscillating irrigation commands. The Explanation Facility records each rule evaluation and the resulting intermediate state transitions so that every recommendation is auditable by farmers and agronomists.

Knowledge acquisition was operationalized through interviews with agronomists and iterative threshold tuning from historical field observations. The process began with expert elicitation sessions that mapped verbal heuristics, such as “hot + dry + low humidity implies urgent watering,” into machine-executable predicates. These predicates were then tested in simulation against synthetic weather and soil scenarios to refine precision and reduce over-irrigation behavior. The final architecture couples rule-driven transparency with ML-assisted calibration, yielding a hybrid system that remains interpretable while adapting to nonlinear patterns in farm data [1], [2].

## 2. Knowledge Representation

FARMZY uses production rules in canonical form:

\[
\text{IF } C_1 \land C_2 \land \cdots \land C_n \text{ THEN } A \{CF\}
\]

where \(C_i\) are sensor predicates, \(A\) is an action token, and \(CF\in[0,1]\) is a certainty factor representing trust in the conclusion under uncertainty. A representative formalization for the emergency irrigation rule is:

\[
(soil\_moisture < 20) \land (temperature > 32) \Rightarrow irrigation=ON,\; water=50L,\; CF=0.95
\]

The certainty factor is not a Bayesian posterior; instead, it is a pragmatic confidence weight that combines rule coverage, sensor quality assumptions, and environmental context. For example, pH anomaly detection may carry \(CF=0.80\) when the pH probe is recently calibrated, but can be down-weighted if drift is suspected. This mechanism allows FARMZY to remain robust even when low-cost sensors produce intermittent or biased measurements.

In addition to rule representations, FARMZY uses a frame-based structure for crop intelligence. A crop frame contains attributes such as optimal pH interval, preferred NPK profile, humidity tolerance, and irrigation cadence. Frame slots can be populated with learned probability outputs from Gaussian Naive Bayes, permitting a mixed symbolic-statistical representation where rule outputs constrain candidate crops and probabilistic classifiers rank final recommendations. This combination of production rules and frames is consistent with classical expert-system knowledge engineering practice and improves maintainability because agronomists can edit high-level agronomic constraints without retraining every downstream model [3], [4].

## 3. Fuzzy Logic in Irrigation Control

Boolean thresholds are often insufficient in agriculture because environmental transitions are continuous and uncertain, not discrete. A soil moisture reading of 39% and 41% should not trigger radically different actions, yet crisp logic can produce exactly that discontinuity. FARMZY addresses this by embedding a Mamdani fuzzy inference layer to fine-tune irrigation volume after rule activation. Linguistic partitions are defined for soil moisture (DRY, MODERATE, WET), temperature (COOL, WARM, HOT), and humidity (LOW, MEDIUM, HIGH), each parameterized through trapezoidal membership functions.

Given a feature value \(x\), a trapezoidal membership \(\mu_A(x)\) is expressed piecewise over \((a,b,c,d)\), rising linearly from 0 to 1, plateauing, and then declining linearly back to 0. Fuzzy rule firing strength uses min-operator conjunction, and consequence aggregation uses max composition. The defuzzified irrigation output \(z^*\) is computed through the centroid method:

\[
z^* = \frac{\int z\,\mu_{agg}(z)\,dz}{\int \mu_{agg}(z)\,dz}
\]

A worked example illustrates the advantage: for soil moisture 27%, temperature 36°C, and humidity 46%, the crisp rule engine may set a baseline of 30 L. Fuzzy inference recognizes partial overlap with DRY and HOT sets and can elevate output toward heavy irrigation, for example to 38–42 L, without requiring brittle threshold edits. In FARMZY, this acts as a smooth controller around decision boundaries and reduces oscillatory valve behavior. Compared with purely crisp systems, fuzzy augmentation improves continuity, resilience to noise, and practical agronomic realism [5], [6].

Diagram 1 (Inference Chain Diagram) should depict the sequence Sensor Facts → Conflict Set → Rule Firing → Fuzzy Adjustment → Final Irrigation Action. Diagram 2 (Membership Function Diagram) should plot trapezoidal sets for DRY/MODERATE/WET and COOL/WARM/HOT on shared axes.

## 4. Machine Learning Integration

FARMZY adopts a hybrid AI strategy in which classical machine learning complements symbolic reasoning rather than replacing it. Linear Regression estimates continuous water demand from multivariate soil-climate features and provides a quantitative signal for water-volume calibration. Inference remains explainable because the final command is still anchored to rule/fuzzy logic, while regression refines magnitude under heterogeneous field conditions. Gaussian Naive Bayes is used for crop recommendation due to its efficiency, probabilistic output, and strong empirical performance on tabular agronomic features where class-conditional independence is a workable approximation [7].

The Naive Bayes decision rule follows Bayes theorem:

\[
\hat{y} = \arg\max_c \; P(c)\prod_i P(x_i|c)
\]

where \(x_i\) are sensor-derived attributes and \(c\) is a crop class. FARMZY retains top-3 crop outputs with probabilities, supporting uncertainty-aware advisory output instead of hard single-class assignment.

For spatial management, K-Means clusters fields into agronomic zones using nutrient and moisture signatures. Cluster assignment is based on Euclidean distance to centroids and iterative minimization of inertia:

\[
J = \sum_{k=1}^{K}\sum_{x\in C_k}||x-\mu_k||^2
\]

Principal Component Analysis is used both as an exploratory diagnostic and preprocessing tool to project high-dimensional sensor space into compact components with interpretable variance coverage. Eigenvectors indicate which sensor channels dominate each component, helping agronomists understand latent structure, such as moisture-temperature coupling or nutrient imbalance axes. Together, these models provide predictive accuracy, zone intelligence, and feature interpretability while the expert layer preserves domain trust and explainability [8], [9].

## 5. System Validation and Testing

Validation in FARMZY is performed at three levels: unit, integration, and expert review. Unit testing targets each rule predicate, boundary threshold, and fuzzy membership function to ensure deterministic behavior at critical transitions. For example, tests explicitly probe values near soil-moisture cutoffs (19.9, 20.0, 20.1) to detect discontinuities and confirm expected conflict-resolution outcomes. Integration testing replays simulated and recorded sensor streams through the full pipeline, verifying that ingestion, inference, alerting, persistence, and WebSocket broadcast operate within timing constraints for near-real-time use.

Expert validation is conducted through agronomist walkthrough sessions in which reasoning traces are audited against expected crop-management logic. Disagreements between model output and expert judgment are logged as knowledge gaps, then resolved through either rule revision or feature recalibration. This human-in-the-loop cycle is essential for expert-system reliability in domain-sensitive contexts where model correctness is not purely statistical but also agronomic.

Comparative evaluation against manual irrigation baseline should report water saved (%), decision agreement with expert labels, and false-alert rate. A typical benchmark protocol uses matched plots across identical weather windows and computes delta in liters applied per hectare with no reduction in crop health outcomes. Preliminary hybrid systems in literature show measurable water savings while preserving or improving agronomic outcomes when explainable control loops are used [10], [11].

A literature comparison table is recommended in the final report to contrast FARMZY with prior work on architecture (rule-only vs hybrid), explainability support, realtime capability, and multi-model integration. FARMZY’s differentiator is the integrated loop of IoT ingestion, rule/fuzzy explainable control, and predictive ML services backed by realtime dashboarding.

## FARMZY vs Prior Work (Illustrative)

| System | Core Method | Explainability | Realtime IoT | Hybrid ML + Rules |
|---|---|---|---|---|
| Prior Work A | Threshold automation | Low | Partial | No |
| Prior Work B | Pure ML irrigation | Medium | Yes | No |
| Prior Work C | Fuzzy-only control | Medium | Limited | No |
| FARMZY | Rules + Fuzzy + ML | High (trace-level) | Yes | Yes |

## References

[1] E. H. Shortliffe and J. J. Cimino, *Biomedical Informatics*, 4th ed. Springer, 2014.

[2] P. Jackson, *Introduction to Expert Systems*, 3rd ed. Addison-Wesley, 1998.

[3] G. F. Luger, *Artificial Intelligence: Structures and Strategies*, 6th ed. Pearson, 2008.

[4] S. Russell and P. Norvig, *Artificial Intelligence: A Modern Approach*, 4th ed. Pearson, 2020.

[5] L. A. Zadeh, “Fuzzy sets,” *Information and Control*, vol. 8, no. 3, pp. 338–353, 1965.

[6] E. H. Mamdani and S. Assilian, “An experiment in linguistic synthesis with a fuzzy logic controller,” *Int. J. Man-Machine Studies*, vol. 7, no. 1, pp. 1–13, 1975.

[7] T. Mitchell, *Machine Learning*. McGraw-Hill, 1997.

[8] J. MacQueen, “Some methods for classification and analysis of multivariate observations,” in *Proc. 5th Berkeley Symp.*, 1967.

[9] I. Jolliffe and J. Cadima, “Principal component analysis: A review,” *Phil. Trans. R. Soc. A*, vol. 374, 2016.

[10] M. Adeyemi et al., “Data-driven irrigation management using IoT and AI,” *Computers and Electronics in Agriculture*, 2022.

[11] A. Ferrández-Pastor et al., “Precision agriculture design with intelligent decision support,” *Sensors*, 2023.

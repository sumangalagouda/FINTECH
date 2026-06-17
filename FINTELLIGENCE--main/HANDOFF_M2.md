# Handoff Document (M2)

## What is built and tested
- ✅ Graph Intelligence backend engine built with NetworkX.
- ✅ New `CaseGraph` Database schema and model for storing unified case graphs to PostgreSQL.
- ✅ Graph Generation: `build_multi_statement_graph` which aggregates transactions across all statements for a case.
- ✅ Circular Flow Detector: Detects cyclic money trails and scores them by timeframe, amount, and node novelty.
- ✅ Layering Chain Detector: Identifies deep path combinations (>= 3 hops) matching layering patterns.
- ✅ Layering Severity Engine: Multi-factor scoring for layering chains to label as Low/Medium/High/Critical.
- ✅ Trail Reconstruction Engine: Traces suspicious transactions up to 10 hops forward.
- ✅ Cross Statement Analysis: Connects intermediary nodes shared between separate statements in the same case.
- ✅ Relationship Discovery Engine: Uses graph centrality (Degree, Betweenness) to detect hubs, bridges, common sources, and common beneficiaries.
- ✅ JWT Protected Graph API Routes mapping to all the above functions.
- ✅ React Frontend initialized using Vite, complete with:
  - **FundFlowGraph.jsx**: A React Flow network visualization rendering size/color-coded accounts based on risk score and transaction count.
  - **AnimatedTrail.jsx**: A Framer Motion and D3 component designed to step-by-step animate the reconstructed 10-hop money trail.
  - **CaseTimeline.jsx**: A vertical timeline using Ant Design and Framer Motion indicating transaction events with badges and tooltips.
  - **BeneficiaryPanel.jsx**: A detailed slide-in Drawer showing risk metrics, stats, and transaction history.
  - **RiskHeatMap.jsx**: A Recharts Treemap that categorizes accounts dynamically by volume and risk level.

## Data Formats & Schemas
- Backend graph endpoints adhere to standard NetworkX `node_link_data` formats.
- All detectors conform to the "Canonical Detector Output JSON" defined in `SCHEMA.md`.

## Known Limitations
- The `CaseGraph` model JSON is generated entirely on demand or read from DB. Real-time incremental graph building is not yet supported.
- `AnimatedTrail` speed control uses approximate JavaScript intervals; Framer Motion is utilized for the transitions.
- The `detectors` module currently depends on dates; converting backend transaction timestamps to full datetime objects would enable the sub-hour layering logic to work properly.

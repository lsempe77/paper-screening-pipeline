import json
from pathlib import Path
from typing import Any, Dict, Tuple

import streamlit as st

ARTIFACT_ROOT = Path("data/output/fulltext/papers")
ALL_RESULTS_CSV = Path("data/output/fulltext_all").glob("all_results_*.csv")

CRITERIA_KEYS = [
    "criterion_1_lmic",
    "criterion_2_cash",
    "criterion_3_assets",
    "criterion_4_design",
    "criterion_5_year",
    "criterion_6_completed",
]

# Mapping from criteria to extraction citation keys to show evidence quotes (heuristic)
CITATION_KEYS = {
    "criterion_2_cash": [
        ("intervention_components", "component_a_cash_support", "cash_evidence_citation"),
    ],
    "criterion_3_assets": [
        ("intervention_components", "component_b_assets", "assets_evidence_citation"),
    ],
    "criterion_4_design": [
        ("study_characteristics", None, "design_evidence_citation"),
    ],
    "criterion_1_lmic": [
        ("evidence_citations", None, "country_citation"),
    ],
}


def _safe_load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # File might contain raw text if JSON parsing failed upstream
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
            return {"raw_text": text}
        except Exception:
            return {}


def _extract_criterion_block(raw: Dict[str, Any], crit_key: str) -> Tuple[str, str]:
    """Return (assessment, reasoning) for a criterion from a raw interpretation payload.

    This is heuristic because interpretation_raw.json stores the LLM JSON as-is.
    We try common shapes:
      - {crit_key: {assessment: ..., reasoning: ...}}
      - {criteria: {crit_key: {assessment, reasoning}}}
      - flat keys like f"{crit_key}_assessment" / f"{crit_key}_reasoning"
      - otherwise fallback to raw snippet.
    """
    # Common nested form
    node = raw.get(crit_key)
    if isinstance(node, dict):
        a = str(node.get("assessment", "")).upper() or ""
        r = str(node.get("reasoning", ""))
        if a or r:
            return a, r

    criteria = raw.get("criteria")
    if isinstance(criteria, dict):
        node = criteria.get(crit_key)
        if isinstance(node, dict):
            a = str(node.get("assessment", "")).upper() or ""
            r = str(node.get("reasoning", ""))
            if a or r:
                return a, r

    # Flat keys
    a = raw.get(f"{crit_key}_assessment")
    r = raw.get(f"{crit_key}_reasoning")
    if a or r:
        return (str(a).upper() if a else ""), (str(r) if r else "")

    # Fallback to raw text snippet
    raw_text = raw.get("raw_text")
    if raw_text:
        return "", raw_text[:600] + ("..." if len(raw_text) > 600 else "")

    return "", ""


def _collect_citations(extraction_raw: Dict[str, Any], crit_key: str) -> str:
    parts = []
    for path in CITATION_KEYS.get(crit_key, []):
        top, mid, leaf = path
        node = extraction_raw.get(top) if top else extraction_raw
        if mid and isinstance(node, dict):
            node = node.get(mid)
        if isinstance(node, dict):
            val = node.get(leaf)
        else:
            val = None
        if val:
            parts.append(str(val))
    # Also common generic evidence fields
    if crit_key == "criterion_2_cash":
        comp = extraction_raw.get("intervention_components", {}).get("component_a_cash_support", {})
        for k in ("cash_support_type", "cash_frequency", "is_loan_or_credit"):
            if comp.get(k) is not None:
                parts.append(f"{k}: {comp.get(k)}")
    if crit_key == "criterion_3_assets":
        compb = extraction_raw.get("intervention_components", {}).get("component_b_assets", {})
        if compb.get("component_b_present") is not None:
            parts.append(f"component_b_present: {compb.get('component_b_present')}")
        if compb.get("assets_provided"):
            parts.append(f"assets_provided: {compb.get('assets_provided')}")
    return " \n\n".join(parts)


def _render_engine_panel(title: str, raw_interpretation: Dict[str, Any], extraction_raw: Dict[str, Any]):
    st.subheader(title)
    with st.expander("Show raw JSON", expanded=False):
        st.json(raw_interpretation)

    rows = []
    for key in CRITERIA_KEYS:
        a, r = _extract_criterion_block(raw_interpretation, key)
        cites = _collect_citations(extraction_raw, key)
        rows.append((key, a or "(n/a)", r or "(no reasoning available)", cites))

    for crit, a, r, cites in rows:
        st.markdown(f"**{crit}** — Assessment: `{a}`")
        st.write(r)
        if cites:
            with st.expander("Citation evidence", expanded=False):
                st.write(cites)
        st.divider()


def main():
    st.set_page_config(page_title="Full-Text Screening Viewer", page_icon="📄", layout="wide")
    st.title("📄 Full-Text Screening — Paper Viewer")
    st.caption("Enter a paper ID to view criteria, reasoning, and final decision. Data comes from per-paper artifacts in `data/output/fulltext/papers/`. ")

    # Discover available paper IDs for convenience
    try:
        available_ids = sorted([p.name for p in ARTIFACT_ROOT.iterdir() if p.is_dir()])
    except Exception:
        available_ids = []

    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        paper_id = st.text_input("Paper ID (type or pick)", placeholder="e.g., 121304162")
    with col2:
        pick_id = st.selectbox("Or select from available", options=[""] + available_ids, index=0)
    with col3:
        go = st.button("Show", type="primary")

    # If user didn't type, use picked id
    if not paper_id and pick_id:
        paper_id = pick_id

    if not paper_id:
        st.info("Enter a paper ID to begin.")
        return

    pdir = ARTIFACT_ROOT / str(paper_id)
    if go or paper_id:
        if not pdir.exists():
            st.error(f"No artifacts found for paper_id `{paper_id}` at {pdir}.")
            st.stop()

        # Load artifacts
        final_result = _safe_load_json(pdir / "final_result.json")
        stage15 = _safe_load_json(pdir / "stage1_5_verification.json")
        eng1_interp = _safe_load_json(pdir / "engine1_interpretation_raw.json")
        eng2_interp = _safe_load_json(pdir / "engine2_interpretation_raw.json")
        eng1_extr = _safe_load_json(pdir / "engine1_extraction_raw.json")
        eng2_extr = _safe_load_json(pdir / "engine2_extraction_raw.json")

        # Header summary
        st.header(f"Paper {paper_id}")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Final Decision", final_result.get("final_decision", "(unknown)"))
        with c2:
            st.write("Rule Applied")
            st.code(final_result.get("decision_rule_applied", ""), language="text")
        with c3:
            st.write("Agreement Level")
            st.code(final_result.get("engines_agree", ""), language="text")

        st.markdown("### Confidence / Rationale")
        st.write(final_result.get("confidence_explanation", "(no explanation)"))
        st.divider()

        # Stage 1.5
        st.subheader("Stage 1.5 — Program Verification")
        s15_cols = st.columns(3)
        with s15_cols[0]:
            st.write("Assessment")
            st.code(stage15.get("assessment", "(n/a)"))
        with s15_cols[1]:
            st.write("Verified Program Name")
            st.code(stage15.get("verified_program_name", "(n/a)"))
        with s15_cols[2]:
            st.write("Applied")
            st.code(str(stage15.get("verification_applied", "")))
        if stage15.get("reasoning"):
            with st.expander("Stage 1.5 Reasoning", expanded=False):
                st.write(stage15.get("reasoning", ""))
        st.divider()

        # Engines panels
        # Compute disagreement highlighting map
        disagree = {}
        for key in CRITERIA_KEYS:
            a1, _ = _extract_criterion_block(eng1_interp, key)
            a2, _ = _extract_criterion_block(eng2_interp, key)
            if a1 and a2 and a1 != a2:
                disagree[key] = (a1, a2)

        if disagree:
            st.warning("Engine disagreement detected on: " + ", ".join(disagree.keys()))
        else:
            st.info("No disagreements between engines on the listed criteria.")

        e1, e2 = st.columns(2)
        with e1:
            _render_engine_panel("Engine 1 — Interpretation", eng1_interp, eng1_extr)
        with e2:
            _render_engine_panel("Engine 2 — Interpretation", eng2_interp, eng2_extr)

        st.success("Done.")


if __name__ == "__main__":
    main()

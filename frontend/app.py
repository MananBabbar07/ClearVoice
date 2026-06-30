import streamlit as st
import requests

API_URL = "https://manan77709-clearvoice-api.hf.space"

st.set_page_config(
    page_title="ClearVoice",
    page_icon="🔬",
    layout="centered"
)

st.title("🔬 ClearVoice")
st.subheader("Medical Misinformation Checker")
st.markdown("Enter a health claim and we'll verify it against peer-reviewed PubMed studies.")

st.divider()

claim = st.text_area(
    "Enter a health claim",
    placeholder="e.g. Vitamin C cures cancer",
    height=100
)

if st.button("Verify Claim", type="primary"):
    if not claim.strip():
        st.error("Please enter a claim.")
    else:
        with st.spinner("Searching PubMed studies and generating verdict..."):
            try:
                response = requests.post(
                    f"{API_URL}/verify",
                    json={"claim": claim},
                    timeout=90
                )
                data = response.json()

                st.divider()

                verdict = data.get("verdict", "UNKNOWN")
                confidence = data.get("confidence", 0)
                evidence_strength = data.get("evidence_strength", "")

                if verdict == "TRUE":
                    st.success(f"✅ Verdict: {verdict}")
                elif verdict == "FALSE":
                    st.error(f"❌ Verdict: {verdict}")
                elif verdict == "MISLEADING":
                    st.warning(f"⚠️ Verdict: {verdict}")
                else:
                    st.info(f"ℹ️ Verdict: {verdict}")

                col1, col2 = st.columns(2)
                col1.metric("Confidence", f"{confidence * 100:.0f}%")
                col2.metric("Evidence Strength", evidence_strength)

                if data.get("cached"):
                    st.caption("⚡ Result served from cache")

                # Decomposition
                decomposition = data.get("decomposition", {})
                if decomposition.get("is_complex"):
                    st.info(f"🔍 Complex claim detected — analyzed {len(decomposition.get('sub_claims', []))} sub-claims")
                    for i, sc in enumerate(decomposition.get("sub_claims", []), 1):
                        st.caption(f"{i}. {sc}")

                st.divider()

                # Plain English
                plain_english = data.get("plain_english", "")
                if plain_english:
                    st.markdown("### 💬 In Plain English")
                    st.write(plain_english)

                takeaway = data.get("takeaway", "")
                if takeaway:
                    st.info(f"💡 **Takeaway:** {takeaway}")

                st.divider()

                # Technical explanation
                with st.expander("🔬 Technical Explanation"):
                    st.write(data.get("explanation", ""))

                    citations = data.get("citations", [])
                    if citations:
                        st.markdown("**Citations:**")
                        for c in citations:
                            pmid = c.get("pmid", "")
                            title = c.get("title", "")
                            if pmid and pmid.isdigit():
                                st.markdown(f"- **{title}** — [PubMed](https://pubmed.ncbi.nlm.nih.gov/{pmid}/)")
                            else:
                                st.markdown(f"- **{title}**")

                st.divider()

                # Judge agent results
                judge = data.get("judge", {})
                if judge:
                    st.markdown("### 📊 Evidence Quality Analysis")

                    overall_quality = judge.get("overall_quality", "UNKNOWN")
                    quality_explanation = judge.get("quality_explanation", "")

                    if overall_quality == "HIGH":
                        st.success(f"📊 Overall Evidence Quality: {overall_quality}")
                    elif overall_quality == "MEDIUM":
                        st.warning(f"📊 Overall Evidence Quality: {overall_quality}")
                    else:
                        st.error(f"📊 Overall Evidence Quality: {overall_quality}")

                    st.caption(quality_explanation)

                    judge_papers = judge.get("papers", [])
                    papers = data.get("papers", [])

                    if judge_papers:
                        st.markdown("#### Study Breakdown")
                        for jp, p in zip(judge_papers, papers):
                            stance = jp.get("stance", "NEUTRAL")
                            study_type = jp.get("study_type", "Unknown")
                            quality_score = jp.get("quality_score", 0)
                            summary = jp.get("one_line_summary", "")

                            if stance == "SUPPORTS":
                                icon = "🟢"
                            elif stance == "CONTRADICTS":
                                icon = "🔴"
                            else:
                                icon = "⚪"

                            with st.expander(f"{icon} [{stance}] {p['title']} ({p['year']})"):
                                col1, col2, col3 = st.columns(3)
                                col1.metric("Study Type", study_type)
                                col2.metric("Quality Score", f"{quality_score}/5")
                                col3.metric("Similarity", p['similarity'])
                                st.write(f"**Journal:** {p['journal']}")
                                st.write(f"**Summary:** {summary}")
                                st.markdown(f"[View on PubMed](https://pubmed.ncbi.nlm.nih.gov/{p['pmid']}/)")

            except Exception as e:
                st.error(f"Error connecting to API: {e}")
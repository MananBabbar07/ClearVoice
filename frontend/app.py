import streamlit as st
import requests
import json

API_URL = "http://localhost:8000"

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
                    json={"claim": claim}
                )
                data = response.json()

                st.divider()

               
                verdict = data.get("verdict", "UNKNOWN")
                confidence = data.get("confidence", 0)

                if verdict == "TRUE":
                    st.success(f"✅ Verdict: {verdict}")
                elif verdict == "FALSE":
                    st.error(f"❌ Verdict: {verdict}")
                elif verdict == "MISLEADING":
                    st.warning(f"⚠️ Verdict: {verdict}")
                else:
                    st.info(f"ℹ️ Verdict: {verdict}")

                st.metric("Confidence", f"{confidence * 100:.0f}%")

                if data.get("cached"):
                    st.caption("⚡ Result served from cache")

                st.divider()

            
                st.markdown("### Explanation")
                st.write(data.get("explanation", ""))

              
                citations = data.get("citations", [])
                if citations:
                    st.markdown("### Citations")
                    for c in citations:
                        if c.get("pmid") and c["pmid"] != "not available":
                            st.markdown(f"- **{c['title']}** — [PubMed](https://pubmed.ncbi.nlm.nih.gov/{c['pmid']}/)")
                        else:
                            st.markdown(f"- {c.get('title', '')}")

                
                papers = data.get("papers", [])
                if papers:
                    st.markdown("### Similar Studies Found")
                    for p in papers:
                        with st.expander(f"[{p['similarity']}] {p['title']} ({p['year']})"):
                            st.write(f"**Journal:** {p['journal']}")
                            st.write(f"**PMID:** {p['pmid']}")
                            st.markdown(f"[View on PubMed](https://pubmed.ncbi.nlm.nih.gov/{p['pmid']}/)")

            except Exception as e:
                st.error(f"Error connecting to API: {e}")
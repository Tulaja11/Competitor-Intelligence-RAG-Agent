import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="RivalRadar", page_icon="", layout="wide")

# --- Custom CSS ---
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        border: 1px solid #2a2a4a;
    }
    .metric-number {
        font-size: 2rem;
        font-weight: bold;
        color: #00d2ff;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #888;
        margin-top: 4px;
    }
    .intent-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .compare-box {
        background: #0e1117;
        border: 1px solid #2a2a4a;
        border-radius: 10px;
        padding: 16px;
        margin-top: 8px;
    }
</style>
""", unsafe_allow_html=True)


# --- Helper Functions ---
def get_competitors():
    try:
        res = requests.get(f"{API_URL}/competitors", timeout=10)
        if res.status_code == 200:
            return res.json().get("competitors", [])
    except requests.exceptions.ConnectionError:
        pass
    return []


def ask_question(question, competitor):
    try:
        res = requests.post(
            f"{API_URL}/ask",
            json={"question": question, "competitor": competitor},
            timeout=120,
        )
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return None


# --- Sidebar ---
st.sidebar.header("Add Competitor")
new_competitor = st.sidebar.text_input("Company Name")

if st.sidebar.button("Track Competitor", type="primary", use_container_width=True):
    if new_competitor:
        with st.sidebar.status(f"Fetching data for {new_competitor}...", expanded=True):
            try:
                res = requests.post(
                    f"{API_URL}/add-competitor",
                    json={"name": new_competitor},
                    timeout=120,
                )
                if res.status_code == 200:
                    data = res.json()
                    st.sidebar.success(
                        f"{new_competitor} tracked! "
                        f"{data['documents_fetched']} docs, "
                        f"{data['chunks_stored']} chunks."
                    )
                    st.rerun()
                else:
                    st.sidebar.error(f"Error: {res.json().get('detail', 'Unknown')}")
            except requests.exceptions.ConnectionError:
                st.sidebar.error("Backend not running.")
    else:
        st.sidebar.warning("Enter a name first.")

# Tracked list in sidebar
st.sidebar.divider()
st.sidebar.header("Tracked Competitors")
competitors = get_competitors()

if competitors:
    for c in competitors:
        col1, col2 = st.sidebar.columns([3, 1])
        col1.markdown(f"**{c['name']}** · {c['total_chunks']} chunks")
        if col2.button("🔄", key=f"refresh_{c['name']}", help=f"Refresh {c['name']}"):
            with st.sidebar.status(f"Refreshing {c['name']}..."):
                try:
                    requests.post(
                        f"{API_URL}/refresh",
                        json={"name": c["name"]},
                        timeout=120,
                    )
                    st.sidebar.success(f"Refreshed {c['name']}")
                    st.rerun()
                except Exception:
                    st.sidebar.error("Refresh failed.")
else:
    st.sidebar.info("No competitors tracked yet.")

# --- Main Area ---
st.title("RivalRadar")
st.caption("Real-time Competitor Intelligence · Powered by RAG + ML Classification")

if not competitors:
    st.info("Start by adding a competitor in the sidebar.")
    st.stop()

# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["Ask", "Compare", "Dashboard"])

competitor_names = [c["name"] for c in competitors]

# ==================== TAB 1: ASK ====================
with tab1:
    selected = st.selectbox("Select Competitor", competitor_names, key="ask_competitor")

    # Quick insight buttons
    st.markdown("**Quick Insights:**")
    qcol1, qcol2, qcol3 = st.columns(3)

    quick_question = None
    if qcol1.button("Latest Products", use_container_width=True):
        quick_question = "What new products or features have they launched recently?"
    if qcol2.button("Open Roles", use_container_width=True):
        quick_question = "Are they hiring? What roles are open?"
    if qcol3.button("Pricing Info", use_container_width=True):
        quick_question = "What is their pricing and what plans do they offer?"

    st.divider()

    # Chat history per competitor
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = {}

    if selected not in st.session_state.chat_history:
        st.session_state.chat_history[selected] = []

    history = st.session_state.chat_history[selected]

    # Display chat history
    for msg in history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Handle quick question or typed question
    question = quick_question or st.chat_input(f"Ask about {selected}...")

    if question:
        # Show user message
        history.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        # Get answer
        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                data = ask_question(question, selected)
                if data:
                    st.markdown(
                        f"**Intent:** `{data['classified_intent']}` · "
                        f"**Confidence:** `{data['confidence']}`"
                    )
                    st.markdown(data["answer"])

                    if data.get("sources"):
                        st.markdown("---")
                        st.markdown("**Sources:**")
                        for url in data["sources"]:
                            st.markdown(f"- [{url}]({url})")

                    full_response = (
                        f"**Intent:** `{data['classified_intent']}` · "
                        f"**Confidence:** `{data['confidence']}`\n\n"
                        f"{data['answer']}"
                    )
                    history.append({"role": "assistant", "content": full_response})
                else:
                    st.error("Could not get answer. Is the backend running?")


# ==================== TAB 2: COMPARE ====================
with tab2:
    if len(competitor_names) < 2:
        st.warning("Add at least 2 competitors to use comparison.")
    else:
        st.subheader("Side-by-Side Competitor Comparison")

        col1, col2 = st.columns(2)
        comp_a = col1.selectbox("Competitor A", competitor_names, key="comp_a")
        comp_b = col2.selectbox(
            "Competitor B",
            [c for c in competitor_names if c != comp_a],
            key="comp_b",
        )

        compare_question = st.text_input(
            "Ask both competitors the same question:",
            placeholder="e.g. Are they hiring engineers?",
        )

        # Quick compare buttons
        st.markdown("**Quick Compare:**")
        ccol1, ccol2, ccol3 = st.columns(3)
        if ccol1.button("Compare Products", use_container_width=True):
            compare_question = "What new products or features have they launched?"
        if ccol2.button("Compare Hiring", use_container_width=True):
            compare_question = "Are they hiring? What roles are open?"
        if ccol3.button("Compare Pricing", use_container_width=True):
            compare_question = "What is their pricing?"

        if compare_question:
            st.divider()
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"### {comp_a}")
                with st.spinner(f"Asking {comp_a}..."):
                    result_a = ask_question(compare_question, comp_a)
                    if result_a:
                        st.markdown(
                            f"`{result_a['classified_intent']}` · "
                            f"`{result_a['confidence']}`"
                        )
                        st.markdown(result_a["answer"])
                        if result_a.get("sources"):
                            for url in result_a["sources"]:
                                st.caption(f"[{url}]({url})")

            with col2:
                st.markdown(f"### {comp_b}")
                with st.spinner(f"Asking {comp_b}..."):
                    result_b = ask_question(compare_question, comp_b)
                    if result_b:
                        st.markdown(
                            f"`{result_b['classified_intent']}` · "
                            f"`{result_b['confidence']}`"
                        )
                        st.markdown(result_b["answer"])
                        if result_b.get("sources"):
                            for url in result_b["sources"]:
                                st.caption(f"[{url}]({url})")


# ==================== TAB 3: DASHBOARD ====================
with tab3:
    st.subheader("Competitor Overview")

    # Metric cards
    mcol1, mcol2, mcol3 = st.columns(3)
    mcol1.markdown(f"""
        <div class="metric-card">
            <div class="metric-number">{len(competitors)}</div>
            <div class="metric-label">Competitors Tracked</div>
        </div>
    """, unsafe_allow_html=True)

    total_chunks = sum(c["total_chunks"] for c in competitors)
    mcol2.markdown(f"""
        <div class="metric-card">
            <div class="metric-number">{total_chunks}</div>
            <div class="metric-label">Total Chunks Indexed</div>
        </div>
    """, unsafe_allow_html=True)

    mcol3.markdown(f"""
        <div class="metric-card">
            <div class="metric-number">3</div>
            <div class="metric-label">Intent Categories</div>
        </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Per-competitor breakdown
    for c in competitors:
        with st.expander(f" {c['name']}", expanded=True):
            icol1, icol2, icol3 = st.columns(3)
            icol1.metric("Chunks Stored", c["total_chunks"])
            icol2.metric("Last Updated", c["last_updated"].split(" ")[0] if c["last_updated"] else "Never")
            icol3.metric("Status", "Active")
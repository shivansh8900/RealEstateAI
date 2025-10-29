import streamlit as st
import pandas as pd
from backend import PropertyChatbot


# Page configuration
st.set_page_config(
    page_title="NoBrokerage Property Chat",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS with FIXED BACKGROUNDS
st.markdown("""
<style>
    /* Main background */
    .main {
        background-color: #f5f7fa;
    }

    /* Chat messages */
    .stChatMessage {
        background-color: white !important;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        color: #000000 !important;
    }

    /* User message background */
    .stChatMessage[data-testid="user-message"] {
        background-color: #E3F2FD !important;
    }

    /* Assistant message background */
    .stChatMessage[data-testid="assistant-message"] {
        background-color: #F5F5F5 !important;
    }

    /* Property cards */
    .property-card {
        background: white !important;
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: transform 0.2s;
        color: #1a1a1a !important;
        border: 1px solid #e0e0e0;
    }

    .property-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }

    .property-title {
        font-size: 20px;
        font-weight: bold;
        color: #1a1a1a !important;
        margin-bottom: 10px;
    }

    .property-price {
        font-size: 24px;
        font-weight: bold;
        color: #FF6B35 !important;
        margin: 10px 0;
    }

    .property-detail {
        display: inline-block;
        background: #f0f0f0 !important;
        padding: 5px 12px;
        border-radius: 20px;
        margin: 5px 5px 5px 0;
        font-size: 14px;
        color: #333333 !important;
    }

    .status-ready {
        background: #4CAF50 !important;
        color: white !important;
    }

    .status-construction {
        background: #FF9800 !important;
        color: white !important;
    }

    /* Main heading */
    h1 {
        color: #FF6B35 !important;
        text-align: center;
        font-weight: 700 !important;
        margin-bottom: 10px !important;
    }

    .subtitle {
        text-align: center;
        color: #2C3E50 !important;
        margin-bottom: 30px;
        font-size: 18px;
    }

    /* Developer credit */
    .developer-credit {
        text-align: center;
        color: #666 !important;
        font-size: 14px;
        margin-top: 10px;
        padding: 10px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 8px;
        color: white !important;
    }

    /* Fix sidebar background */
    section[data-testid="stSidebar"] {
        background-color: #f8f9fa !important;
    }

    /* Fix expander background */
    .streamlit-expanderHeader {
        background-color: #f0f0f0 !important;
        border-radius: 5px;
    }

    .streamlit-expanderContent {
        background-color: white !important;
        border: 1px solid #e0e0e0;
        border-radius: 5px;
    }

    /* Chat input box */
    .stChatInputContainer {
        background-color: white !important;
        border-top: 1px solid #e0e0e0;
    }

    /* All text colors */
    .stChatMessage p {
        color: #000000 !important;
    }

    p, span, div {
        color: #1a1a1a;
    }

    /* Buttons */
    .stButton button {
        background-color: #FF6B35 !important;
        color: white !important;
        border-radius: 8px;
        padding: 8px 16px;
        border: none;
    }

    .stButton button:hover {
        background-color: #E85D2A !important;
    }

    /* Footer */
    .footer {
        position: fixed;
        bottom: 80px;
        right: 20px;
        background: white;
        padding: 10px 20px;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        font-size: 12px;
        color: #666;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chatbot" not in st.session_state:
    try:
        st.session_state.chatbot = PropertyChatbot(
            'project.csv',
            'ProjectAddress.csv',
            'ProjectConfiguration.csv',
            'ProjectConfigurationVariant.csv'
        )
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.stop()

# Header with developer credit
st.title("🏠 NoBrokerage Property Search")
st.markdown('<p class="subtitle">Find your dream property with AI-powered natural language search</p>',
            unsafe_allow_html=True)
st.markdown(
    '<div class="developer-credit">💻 Developed by <strong>Shivansh Shrivastava</strong> | shrivastavashivansh498@gmail.com</div>',
    unsafe_allow_html=True
)

# Example queries in sidebar
with st.sidebar:
    st.header("💡 Example Queries")
    st.markdown("""
    Try asking:
    - **3BHK flat in Mumbai under 5 Cr**
    - **2BHK in Pune under 15 Cr**
    - **1BHK in Mumbai under 2 Cr**
    - **Properties in Mumbai**
    - **2BHK ready to move**
    """)

    st.divider()

    st.header("📊 Available Data")
    if "chatbot" in st.session_state:
        df = st.session_state.chatbot.df
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Properties", len(df))
        with col2:
            st.metric("Cities", "2")
        st.info("🏙️ Mumbai & Pune")

    st.divider()

    if st.button("🔄 Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()

    # Developer info in sidebar
    st.markdown("---")
    st.markdown("### 👨‍💻 Developer")
    st.markdown("**Shivansh Shrivastava**")
    st.markdown("📧 shrivastavashivansh498@gmail.com")
    st.markdown("🎓 AI Engineer Intern Task")
    st.markdown("🏢 NoBrokerage.com")

def display_properties(df):
    """Display property cards with CLEAN City - Locality format."""
    if df.empty:
        st.info("No properties found matching your criteria.")
        return

    for idx, row in df.iterrows():
        # Format price
        price = row['price_inr']
        if price >= 10000000:
            price_str = f"₹{price/10000000:.2f} Cr"
        else:
            price_str = f"₹{price/100000:.2f} L"

        # Status badge
        status = str(row.get('status', 'N/A'))
        status_class = "status-ready" if "READY" in status else "status-construction"
        status_display = status.replace("_", " ").title()

        # Get property details FROM CSV
        prop_name = str(row.get('name', 'Property'))
        bhk_type = str(row.get('bhk', 'N/A'))
        slug = str(row.get('slug', 'property'))
        
        # FIXED: Use clean City - Locality format
        locality = str(row.get('locality', 'Unknown'))
        city_id = row.get('city', '')
        city_name = "Mumbai" if city_id == "cmf50r5a00000vcj0k1iuocuu" else "Pune" if city_id == "cmf6nu3ru000gvcxspxarll3v" else "Unknown"

        # Property card HTML with CLEAN location
        card_html = f"""
        <div class="property-card">
            <div class="property-title">🏢 {prop_name}</div>
            <div class="property-price">{price_str}</div>
            <div style="margin: 15px 0;">
                <span class="property-detail"><strong>{bhk_type}</strong></span>
                <span class="property-detail {status_class}">{status_display}</span>
                <span class="property-detail">📍 {city_name} - {locality}</span>
            </div>
            <a href="/project/{slug}" style="
                background: #FF6B35;
                color: white;
                padding: 8px 16px;
                border-radius: 8px;
                text-decoration: none;
                display: inline-block;
                margin-top: 10px;
                font-size: 14px;
            ">
                🔗 View Full Details
            </a>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "properties" in message and message["properties"] is not None:
            display_properties(message["properties"])

# Chat input
if prompt := st.chat_input("Ask about properties... (e.g., '3BHK in Mumbai under 5 Cr')"):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    # Process query
    with st.chat_message("assistant"):
        with st.spinner("🔍 Searching properties..."):
            try:
                summary, results, filters = st.session_state.chatbot.process_query(prompt)

                # Display summary
                st.markdown(summary)

                # Display filters used
                with st.expander("🔍 Filters Applied"):
                    st.json(filters)

                # Show count
                if not results.empty:
                    st.success(f"✅ Found {len(results)} matching properties!")

                # Display properties
                display_properties(results)

                # Save assistant response
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": summary,
                    "properties": results
                })

            except Exception as e:
                error_msg = f"❌ Sorry, I encountered an error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "properties": None
                })

# Welcome message
if len(st.session_state.messages) == 0:
    with st.chat_message("assistant"):
        st.markdown("""
        👋 **Welcome to NoBrokerage Property Search!**

        I'm your AI property assistant. I can help you find properties based on:

        🏙️ **Location:** Mumbai, Pune
        🏠 **BHK:** 1BHK, 2BHK, 3BHK, 4BHK
        💰 **Budget:** "under 5 Cr" or "between 1 Cr and 3 Cr"
        🏗️ **Status:** Ready to move or Under construction

        **Try these queries:**
        - `3BHK in Mumbai under 5 Cr`
        - `2BHK in Pune under 15 Cr`
        - `Properties in Mumbai`

        Just type your query below! 👇
        """)

# Footer (floating)
st.markdown(
    '<div class="footer">💻 Built by Shivansh Shrivastava for NoBrokerage.com</div>',
    unsafe_allow_html=True
)

import streamlit as st
import pandas as pd
import requests
import altair as alt

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="RSSI Dashboard",
    page_icon="📡",
    layout="wide"
)

# ---------------- THINGSPEAK CONFIG ----------------
CHANNEL_ID = "3232555"
READ_API_KEY = "O5ISQ8GA969Z01WG"
FIELD_NO = 1

THINGSPEAK_URL = (
    f"https://api.thingspeak.com/channels/{CHANNEL_ID}/fields/{FIELD_NO}.json"
    f"?api_key={READ_API_KEY}&results=20"
)

# ---------------- SESSION ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ---------------- LOGIN UI ----------------
if not st.session_state.logged_in:
    st.title("🔐 Login")

    col1, col2 = st.columns(2)
    with col1:
        email = st.text_input("Email")
    with col2:
        password = st.text_input("Password", type="password")

    if st.button("Login"):
        st.session_state.logged_in = True
        st.success("Login Successful")
        st.rerun()

    st.caption("UI Only • Demo Login")

# ---------------- DASHBOARD ----------------
else:
    st.sidebar.title("⚙️ Menu")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    st.sidebar.success("Connected to ThingSpeak")

    st.title("📡 RSSI Monitoring Dashboard (Live ThingSpeak Data)")

    # ---------------- FETCH THINGSPEAK DATA ----------------
    try:
        response = requests.get(THINGSPEAK_URL, timeout=5)
        data = response.json()

        feeds = data["feeds"]
        rssi_values = []
        timestamps = []

        for feed in feeds:
            if feed.get(f"field{FIELD_NO}") is not None:
                rssi_values.append(int(float(feed[f"field{FIELD_NO}"])))
                timestamps.append(feed["created_at"])

        rssi_data = pd.DataFrame({
            "Time": timestamps,
            "RSSI (dBm)": rssi_values
        })

        # ---------------- RSSI STATUS FUNCTION ----------------
        def rssi_status(rssi):
            if rssi >= -55:
                return "🟢 Strong"
            elif -70 <= rssi < -50:
                return "🟡 Average"
            else:
                return "🔴 Weak"

        # ---------------- ADD STATUS COLUMN ----------------
        rssi_data["Status"] = rssi_data["RSSI (dBm)"].apply(rssi_status)

    except Exception as e:
        st.error("❌ Failed to fetch ThingSpeak data")
        st.stop()

    # ---------------- METRICS ----------------
    latest_rssi = rssi_data["RSSI (dBm)"].iloc[-1]
    latest_status = rssi_status(latest_rssi)

    col1, col2, col3 = st.columns(3)
    col1.metric("📶 Latest RSSI", f"{latest_rssi} dBm")
    col2.metric("📡 Signal Quality", latest_status)
    col3.metric("☁️ Source", "ThingSpeak")

    st.markdown("---")

    # ---------------- LINE GRAPH ----------------
    with st.container(border=True):
        st.subheader("📈 RSSI Signal Trend (Live)")

        line_chart = (
            alt.Chart(rssi_data)
            .mark_line(point=True)
            .encode(
                x=alt.X("Time:T", title="Time"),
                y=alt.Y("RSSI (dBm):Q", title="RSSI (dBm)"),
                tooltip=["Time:T", "RSSI (dBm):Q"]
            )
            .properties(height=350)

        )

        st.altair_chart(line_chart, use_container_width=True)

    # ---------------- BAR GRAPH ----------------
    with st.container(border=True):
        st.subheader("📊 RSSI Rise & Fall (Live Bar Graph)")

        bar_chart = (
            alt.Chart(rssi_data)
            .mark_bar(size=20)
            .encode(
                x=alt.X("Time:T", title="Time", axis=alt.Axis(labelAngle=-45)),
                y=alt.Y("RSSI (dBm):Q", title="RSSI (dBm)"),
                color=alt.Color(
                    "Status:N",
                    scale=alt.Scale(
                        domain=["🟢 Strong", "🟡 Average", "🔴 Weak"],
                        range=["green", "orange", "red"]
                    ),
                    legend=alt.Legend(title="Signal Strength")
                ),
                tooltip=["Time:T", "RSSI (dBm):Q", "Status:N"]
            )
            .properties(height=350)
        )

        st.altair_chart(bar_chart, use_container_width=True)

    # ---------------- TABLE ----------------
    st.subheader("📋 RSSI Logs (Live)")
    st.dataframe(rssi_data.tail(10))

    # ---------------- REFRESH ----------------
    if st.button("🔄 Refresh Data"):
        st.rerun()

    st.caption("Live RSSI Dashboard • ThingSpeak • ESP32 Compatible")

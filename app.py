import streamlit as st
import pandas as pd
import requests
import altair as alt

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="RSSI vs Distance Dashboard",
    page_icon="📡",
    layout="wide"
)

# ---------------- THINGSPEAK CONFIG ----------------
CHANNEL_ID = "3232555"
READ_API_KEY = "O5ISQ8GA969Z01WG"

THINGSPEAK_URL = (
    f"https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds.json"
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

    st.caption("Demo Login • UI Only")

# ---------------- DASHBOARD ----------------
else:
    st.sidebar.title("⚙️ Menu")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    st.sidebar.success("Connected to ThingSpeak")

    st.title("📡 RSSI & Distance Monitoring Dashboard")

    # ---------------- FETCH DATA ----------------
    try:
        response = requests.get(THINGSPEAK_URL, timeout=5)
        data = response.json()

        rssi_values = []
        distance_values = []
        timestamps = []

        for feed in data["feeds"]:
            if feed.get("field1") and feed.get("field2"):
                rssi_values.append(int(float(feed["field1"])))
                distance_values.append(float(feed["field2"]))
                timestamps.append(feed["created_at"])

        df = pd.DataFrame({
            "Time": timestamps,
            "RSSI (dBm)": rssi_values,
            "Distance (cm)": distance_values
        })

    except:
        st.error("❌ Failed to fetch data from ThingSpeak")
        st.stop()

    # ---------------- RSSI STATUS ----------------
    def rssi_status(rssi):
        if rssi >= -55:
            return "🟢 Strong"
        elif -70 <= rssi < -55:
            return "🟡 Average"
        else:
            return "🔴 Weak"

    # ---------------- LINK QUALITY ----------------
    def link_quality(distance, rssi):
        if rssi >= -60 and distance <= 100:
            return "Excellent"
        elif -75 <= rssi < -60 and distance <= 200:
            return "Moderate"
        else:
            return "Poor"

    df["Status"] = df["RSSI (dBm)"].apply(rssi_status)
    df["Link Quality"] = df.apply(
        lambda row: link_quality(row["Distance (cm)"], row["RSSI (dBm)"]),
        axis=1
    )

    # ---------------- METRICS ----------------
    latest_rssi = df["RSSI (dBm)"].iloc[-1]
    latest_dist = df["Distance (cm)"].iloc[-1]

    col1, col2, col3 = st.columns(3)
    col1.metric("📶 RSSI", f"{latest_rssi} dBm")
    col2.metric("📏 Distance", f"{latest_dist} cm")
    col3.metric("📡 Status", rssi_status(latest_rssi))

    st.markdown("---")

    # ---------------- RSSI LINE GRAPH ----------------
    with st.container(border=True):
        st.subheader("📈 RSSI Trend Over Time")

        line_chart = (
            alt.Chart(df)
            .mark_line(point=True)
            .encode(
                x="Time:T",
                y="RSSI (dBm):Q",
                tooltip=["Time:T", "RSSI (dBm):Q"]
            )
            .properties(height=350)
        )

        st.altair_chart(line_chart, use_container_width=True)

    # ---------------- DISTANCE vs RSSI SCATTER ----------------
    with st.container(border=True):
        st.subheader("📐 Distance vs RSSI Comparison")

        scatter = (
            alt.Chart(df)
            .mark_circle(size=120)
            .encode(
                x=alt.X("Distance (cm):Q", title="Distance (cm)"),
                y=alt.Y("RSSI (dBm):Q", title="RSSI (dBm)"),
                color=alt.Color(
                    "Link Quality:N",
                    scale=alt.Scale(
                        domain=["Excellent", "Moderate", "Poor"],
                        range=["green", "orange", "red"]
                    )
                ),
                tooltip=["Distance (cm)", "RSSI (dBm)", "Link Quality"]
            )
            .properties(height=350)
        )

        st.altair_chart(scatter, use_container_width=True)

    # ---------------- BAR GRAPH ----------------
    with st.container(border=True):
        st.subheader("📊 RSSI Strength Levels")

        bar_chart = (
            alt.Chart(df)
            .mark_bar(size=25)
            .encode(
                x=alt.X("Time:T", axis=alt.Axis(labelAngle=-45)),
                y="RSSI (dBm):Q",
                color="Status:N",
                tooltip=["Time:T", "RSSI (dBm):Q", "Status:N"]
            )
            .properties(height=350)
        )

        st.altair_chart(bar_chart, use_container_width=True)

    # ---------------- TABLE ----------------
    st.subheader("📋 Live RSSI & Distance Logs")
    st.dataframe(df.tail(10), use_container_width=True)

    # ---------------- INSIGHT ----------------
    st.info(
        f"📊 Observation: RSSI decreases as distance increases "
        f"(Avg Distance: {df['Distance (cm)'].mean():.1f} cm, "
        f"Avg RSSI: {df['RSSI (dBm)'].mean():.1f} dBm)."
    )

    # ---------------- REFRESH ----------------
    if st.button("🔄 Refresh Data"):
        st.rerun()

    st.caption("ESP32 • Ultrasonic Sensor • ThingSpeak • Streamlit")

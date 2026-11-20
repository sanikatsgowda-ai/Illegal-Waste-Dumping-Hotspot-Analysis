
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(
    page_title="Illegal Waste Dumping | Analytics",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================================
# CUSTOM DESIGN
# ==========================================================

st.markdown("""
<style>

.stApp {
    background: #F4F7F5;
}

[data-testid="stSidebar"] {
    background: #163D32;
}

[data-testid="stSidebar"] * {
    color: white !important;
}

.main-title {
    color: #173D32;
    font-size: 36px;
    font-weight: 800;
    margin-bottom: 0px;
}

.sub-title {
    color: #718078;
    font-size: 16px;
    margin-bottom: 20px;
}

.section-title {
    color: #173D32;
    font-size: 25px;
    font-weight: 750;
}

div[data-testid="stMetric"] {
    background: white;
    padding: 18px;
    border-radius: 14px;
    border: 1px solid #E2EAE5;
    box-shadow: 0 3px 10px rgba(0,0,0,0.04);
}

div[data-testid="stMetricLabel"] {
    color: #66786D;
}

div[data-testid="stMetricValue"] {
    color: #173D32;
}

div[data-testid="stMetricDelta"] {
    color: #2E8B57;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
}

.stTabs [data-baseweb="tab"] {
    background: white;
    border-radius: 8px;
    padding: 10px 18px;
}

.stTabs [aria-selected="true"] {
    background-color: #DDEFE3 !important;
}

div[data-testid="stPlotlyChart"] {
    background: white;
    border-radius: 12px;
    padding: 8px;
}

</style>
""", unsafe_allow_html=True)

# ==========================================================
# LOAD DATA
# ==========================================================

@st.cache_data
def load_data():

    df = pd.read_csv("illegal_dumping_data.csv")

    # Date conversion
    df["created_date"] = pd.to_datetime(
        df["created_date"],
        errors="coerce"
    )

    df["closed_date"] = pd.to_datetime(
        df["closed_date"],
        errors="coerce"
    )

    # Numeric conversion
    df["latitude"] = pd.to_numeric(
        df["latitude"],
        errors="coerce"
    )

    df["longitude"] = pd.to_numeric(
        df["longitude"],
        errors="coerce"
    )

    # Missing value handling
    for col in [
        "borough",
        "complaint_type",
        "descriptor",
        "community_board",
        "status"
    ]:
        if col in df.columns:
            df[col] = df[col].fillna("Unknown").astype(str)

    # Date features
    df["date"] = df["created_date"].dt.date

    df["month"] = df["created_date"].dt.strftime("%b %Y")

    df["month_period"] = df["created_date"].dt.to_period("M")

    df["day_name"] = df["created_date"].dt.day_name()

    df["weekday"] = df["created_date"].dt.dayofweek

    df["hour"] = df["created_date"].dt.hour

    df["week"] = df["created_date"].dt.to_period("W").astype(str)

    # Resolution duration
    df["resolution_hours"] = (
        df["closed_date"] - df["created_date"]
    ).dt.total_seconds() / 3600

    df.loc[
        df["resolution_hours"] < 0,
        "resolution_hours"
    ] = None

    # Resolution status based on closed date
    df["resolution_status"] = df["closed_date"].apply(
        lambda x: "Closed" if pd.notna(x) else "Open"
    )

    return df


try:

    df = load_data()

except FileNotFoundError:

    st.error(
        "CSV file not found! Place "
        "'illegal_dumping_data.csv' in the same folder as app.py."
    )

    st.stop()

except Exception as e:

    st.error(f"Error loading dataset: {e}")

    st.stop()


# ==========================================================
# SIDEBAR
# ==========================================================

st.sidebar.markdown("## 🌿 Waste Analytics")

st.sidebar.markdown(
    "### Dashboard Filters"
)

st.sidebar.markdown("---")

borough_options = sorted(
    df["borough"].dropna().unique()
)

selected_boroughs = st.sidebar.multiselect(
    "Select Borough",
    borough_options,
    default=borough_options
)

category_options = sorted(
    df["complaint_type"].dropna().unique()
)

selected_categories = st.sidebar.multiselect(
    "Complaint Category",
    category_options,
    default=category_options
)

status_options = sorted(
    df["resolution_status"].unique()
)

selected_status = st.sidebar.multiselect(
    "Complaint Resolution Status",
    status_options,
    default=status_options
)

min_date = df["created_date"].min().date()

max_date = df["created_date"].max().date()

selected_dates = st.sidebar.date_input(
    "Complaint Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

st.sidebar.markdown("---")

st.sidebar.caption(
    "Data Source: NYC Open Data – 311 Service Requests"
)

# ==========================================================
# FILTER DATA
# ==========================================================

filtered_df = df[
    df["borough"].isin(selected_boroughs)
    &
    df["complaint_type"].isin(selected_categories)
    &
    df["resolution_status"].isin(selected_status)
].copy()

if len(selected_dates) == 2:

    start_date = selected_dates[0]

    end_date = selected_dates[1]

    filtered_df = filtered_df[
        filtered_df["created_date"].dt.date.between(
            start_date,
            end_date
        )
    ]

if filtered_df.empty:

    st.warning(
        "No records found for the selected filters. "
        "Please change your filters."
    )

    st.stop()

# ==========================================================
# HEADER
# ==========================================================

st.markdown(
    '<div class="main-title">'
    '🌍 Illegal Waste Dumping Hotspot Analysis'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">'
    'Interactive environmental complaint analytics '
    '| Live public dataset'
    '</div>',
    unsafe_allow_html=True
)

st.markdown("---")

# ==========================================================
# KPI METRICS
# ==========================================================

total_complaints = len(filtered_df)

borough_counts = filtered_df["borough"].value_counts()

top_borough = (
    borough_counts.index[0]
    if not borough_counts.empty
    else "N/A"
)

open_count = (
    filtered_df["resolution_status"] == "Open"
).sum()

closed_count = (
    filtered_df["resolution_status"] == "Closed"
).sum()

avg_resolution = filtered_df[
    "resolution_hours"
].dropna().mean()

if pd.isna(avg_resolution):

    avg_resolution = 0

valid_coordinates = filtered_df.dropna(
    subset=["latitude", "longitude"]
)

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total Complaints",
    f"{total_complaints:,}"
)

col2.metric(
    "Top Borough",
    top_borough
)

col3.metric(
    "Open Complaints",
    f"{open_count:,}"
)

col4.metric(
    "Avg. Resolution",
    f"{avg_resolution:.1f} hrs"
)

st.markdown("---")

# ==========================================================
# TABS
# ==========================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Trends",
    "📍 Hotspots",
    "🗑️ Categories",
    "🕒 Time Patterns",
    "⚙️ Resolution"
])


# ==========================================================
# ANALYSIS 1 - TREND ANALYSIS
# ==========================================================

with tab1:

    st.markdown(
        '<div class="section-title">'
        '1. Complaint Trend Analysis'
        '</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Analyze complaint trends over daily, weekly "
        "and monthly periods."
    )

    # Daily trend
    daily_data = (
        filtered_df.groupby("date")
        .size()
        .reset_index(name="complaints")
    )

    fig_daily = px.line(
        daily_data,
        x="date",
        y="complaints",
        markers=True,
        title="Daily Complaint Trend",
        color_discrete_sequence=["#218C58"]
    )

    fig_daily.update_layout(
        template="plotly_white",
        xaxis_title="Date",
        yaxis_title="Number of Complaints",
        hovermode="x unified"
    )

    st.plotly_chart(
        fig_daily,
        use_container_width=True
    )

    # Weekly trend
    weekly_data = (
        filtered_df.groupby("week")
        .size()
        .reset_index(name="complaints")
    )

    fig_weekly = px.bar(
        weekly_data,
        x="week",
        y="complaints",
        color="complaints",
        color_continuous_scale="Greens",
        title="Weekly Complaint Distribution"
    )

    fig_weekly.update_layout(
        template="plotly_white",
        xaxis_title="Week",
        yaxis_title="Complaints"
    )

    st.plotly_chart(
        fig_weekly,
        use_container_width=True
    )

    # Monthly trend
    monthly_data = (
        filtered_df.groupby("month_period")
        .size()
        .reset_index(name="complaints")
    )

    monthly_data["month"] = (
        monthly_data["month_period"].astype(str)
    )

    fig_monthly = px.bar(
        monthly_data,
        x="month",
        y="complaints",
        color="complaints",
        color_continuous_scale="Viridis",
        title="Monthly Complaint Distribution"
    )

    fig_monthly.update_layout(
        template="plotly_white",
        xaxis_title="Month",
        yaxis_title="Complaints"
    )

    st.plotly_chart(
        fig_monthly,
        use_container_width=True
    )

    if not daily_data.empty:

        highest_day = daily_data.loc[
            daily_data["complaints"].idxmax()
        ]

        st.info(
            f"Highest reported day: {highest_day['date']} "
            f"with {highest_day['complaints']} complaints."
        )


# ==========================================================
# ANALYSIS 2 - HOTSPOT ANALYSIS
# ==========================================================

with tab2:

    st.markdown(
        '<div class="section-title">'
        '2. Geographical Hotspot Analysis'
        '</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Identify the boroughs and community boards "
        "with the highest reported dumping complaints."
    )

    # Borough comparison
    borough_data = (
        filtered_df.groupby("borough")
        .size()
        .reset_index(name="complaints")
        .sort_values("complaints", ascending=False)
    )

    fig_borough = px.bar(
        borough_data,
        x="borough",
        y="complaints",
        color="complaints",
        color_continuous_scale="Greens",
        title="Complaint Distribution by Borough"
    )

    fig_borough.update_layout(
        template="plotly_white",
        xaxis_title="Borough",
        yaxis_title="Complaint Count"
    )

    st.plotly_chart(
        fig_borough,
        use_container_width=True
    )

    # Community board hotspots
    board_data = (
        filtered_df.groupby("community_board")
        .size()
        .reset_index(name="complaints")
        .sort_values("complaints", ascending=False)
    )

    board_data = board_data[
        board_data["community_board"] != "Unknown"
    ]

    st.subheader("Top 10 Hotspot Community Boards")

    top_boards = board_data.head(10)

    fig_boards = px.bar(
        top_boards,
        x="complaints",
        y="community_board",
        orientation="h",
        color="complaints",
        color_continuous_scale="Reds",
        title="Top Community Boards by Complaint Count"
    )

    fig_boards.update_layout(
        template="plotly_white",
        yaxis={"categoryorder": "total ascending"},
        xaxis_title="Complaints",
        yaxis_title="Community Board"
    )

    st.plotly_chart(
        fig_boards,
        use_container_width=True
    )

    # ======================================================
    # HOTSPOT MAP
    # ======================================================

    st.subheader("🗺️ Illegal Dumping Hotspot Map")

    map_df = filtered_df.dropna(
        subset=["latitude", "longitude"]
    ).copy()

    # Valid NYC coordinate ranges
    map_df = map_df[
        map_df["latitude"].between(40.4, 41.0)
        &
        map_df["longitude"].between(-74.3, -73.6)
    ]

    st.write(
        f"Valid geographical records: {len(map_df):,}"
    )

    if not map_df.empty:

        map_type = st.radio(
            "Select Map Visualization",
            ["Complaint Points", "Hotspot Density"],
            horizontal=True
        )

        # Sample records to improve performance
        if len(map_df) > 5000:

            plot_map_df = map_df.sample(
                5000,
                random_state=42
            )

        else:

            plot_map_df = map_df.copy()

        if map_type == "Complaint Points":

            fig_map = px.scatter(
                plot_map_df,
                x="longitude",
                y="latitude",
                color="borough",
                hover_name="complaint_type",
                hover_data=[
                    "descriptor",
                    "community_board",
                    "status"
                ],
                title="Dumping Complaint Locations",
                color_discrete_sequence=px.colors.qualitative.Safe
            )

            fig_map.update_traces(
                marker=dict(
                    size=7,
                    opacity=0.65
                )
            )

            fig_map.update_layout(
                template="plotly_white",
                height=650,
                xaxis_title="Longitude",
                yaxis_title="Latitude",
                xaxis=dict(
                    scaleanchor="y",
                    scaleratio=1
                ),
                legend_title="Borough"
            )

        else:

            fig_map = px.density_heatmap(
                plot_map_df,
                x="longitude",
                y="latitude",
                nbinsx=45,
                nbinsy=45,
                color_continuous_scale="Hot",
                title="Dumping Complaint Density",
                marginal_x=None,
                marginal_y=None
            )

            fig_map.update_layout(
                template="plotly_white",
                height=650,
                xaxis_title="Longitude",
                yaxis_title="Latitude",
                xaxis=dict(
                    scaleanchor="y",
                    scaleratio=1
                )
            )

        st.plotly_chart(
            fig_map,
            use_container_width=True
        )

        st.success(
            "Map generated successfully using "
            "geographical complaint coordinates."
        )

    else:

        st.warning(
            "No valid geographical coordinates available "
            "for the selected filters."
        )

    # Hotspot ranking table
    st.subheader("Hotspot Ranking Table")

    st.dataframe(
        board_data.head(20),
        use_container_width=True,
        hide_index=True
    )


# ==========================================================
# ANALYSIS 3 - CATEGORY ANALYSIS
# ==========================================================

with tab3:

    st.markdown(
        '<div class="section-title">'
        '3. Complaint Category Analysis'
        '</div>',
        unsafe_allow_html=True
    )

    category_data = (
        filtered_df.groupby("complaint_type")
        .size()
        .reset_index(name="complaints")
        .sort_values("complaints", ascending=False)
    )

    col1, col2 = st.columns(2)

    with col1:

        fig_pie = px.pie(
            category_data,
            names="complaint_type",
            values="complaints",
            hole=0.45,
            title="Complaint Category Distribution",
            color_discrete_sequence=px.colors.sequential.Greens
        )

        fig_pie.update_layout(
            template="plotly_white"
        )

        st.plotly_chart(
            fig_pie,
            use_container_width=True
        )

    with col2:

        fig_category = px.bar(
            category_data,
            x="complaints",
            y="complaint_type",
            orientation="h",
            color="complaints",
            color_continuous_scale="Greens",
            title="Complaints by Category"
        )

        fig_category.update_layout(
            template="plotly_white",
            yaxis={"categoryorder": "total ascending"}
        )

        st.plotly_chart(
            fig_category,
            use_container_width=True
        )

    # Descriptor analysis
    st.subheader("Top Complaint Descriptors")

    descriptor_data = (
        filtered_df.groupby("descriptor")
        .size()
        .reset_index(name="complaints")
        .sort_values("complaints", ascending=False)
        .head(15)
    )

    fig_descriptor = px.bar(
        descriptor_data,
        x="complaints",
        y="descriptor",
        orientation="h",
        color="complaints",
        color_continuous_scale="Viridis",
        title="Most Common Complaint Descriptions"
    )

    fig_descriptor.update_layout(
        template="plotly_white",
        yaxis={"categoryorder": "total ascending"}
    )

    st.plotly_chart(
        fig_descriptor,
        use_container_width=True
    )

    st.subheader("Category Data")

    st.dataframe(
        category_data,
        use_container_width=True,
        hide_index=True
    )


# ==========================================================
# ANALYSIS 4 - TIME PATTERN ANALYSIS
# ==========================================================

with tab4:

    st.markdown(
        '<div class="section-title">'
        '4. Time Pattern Analysis'
        '</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Understand which days and hours have "
        "the highest complaint reporting activity."
    )

    day_order = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday"
    ]

    col1, col2 = st.columns(2)

    # Day of week
    with col1:

        day_data = (
            filtered_df.groupby("day_name")
            .size()
            .reindex(day_order)
            .reset_index(name="complaints")
        )

        fig_day = px.bar(
            day_data,
            x="day_name",
            y="complaints",
            color="complaints",
            color_continuous_scale="Greens",
            title="Complaints by Day of Week"
        )

        fig_day.update_layout(
            template="plotly_white",
            xaxis_title="Day",
            yaxis_title="Complaint Count"
        )

        st.plotly_chart(
            fig_day,
            use_container_width=True
        )

    # Hour of day
    with col2:

        hour_data = (
            filtered_df.groupby("hour")
            .size()
            .reset_index(name="complaints")
        )

        fig_hour = px.bar(
            hour_data,
            x="hour",
            y="complaints",
            color="complaints",
            color_continuous_scale="Viridis",
            title="Complaints by Hour of Day"
        )

        fig_hour.update_layout(
            template="plotly_white",
            xaxis_title="Hour (0–23)",
            yaxis_title="Complaint Count"
        )

        st.plotly_chart(
            fig_hour,
            use_container_width=True
        )

    # Heatmap
    st.subheader("Day of Week vs Hour Heatmap")

    heatmap_data = filtered_df.pivot_table(
        index="day_name",
        columns="hour",
        values="unique_key",
        aggfunc="count",
        fill_value=0
    )

    heatmap_data = heatmap_data.reindex(day_order)

    fig_heatmap = px.imshow(
        heatmap_data,
        labels={
            "x": "Hour of Day",
            "y": "Day of Week",
            "color": "Complaints"
        },
        color_continuous_scale="Greens",
        title="Complaint Activity Heatmap",
        aspect="auto"
    )

    fig_heatmap.update_layout(
        template="plotly_white"
    )

    st.plotly_chart(
        fig_heatmap,
        use_container_width=True
    )

    # Weekday vs weekend
    filtered_df["day_type"] = filtered_df[
        "weekday"
    ].apply(
        lambda x: "Weekend" if x >= 5 else "Weekday"
    )

    daytype_data = (
        filtered_df.groupby("day_type")
        .size()
        .reset_index(name="complaints")
    )

    fig_daytype = px.pie(
        daytype_data,
        names="day_type",
        values="complaints",
        hole=0.4,
        title="Weekday vs Weekend Complaints"
    )

    st.plotly_chart(
        fig_daytype,
        use_container_width=True
    )


# ==========================================================
# ANALYSIS 5 - RESOLUTION ANALYSIS
# ==========================================================

with tab5:

    st.markdown(
        '<div class="section-title">'
        '5. Complaint Resolution Analysis'
        '</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Analyze complaint resolution status, "
        "resolution duration and unresolved locations."
    )

    status_data = (
        filtered_df.groupby("resolution_status")
        .size()
        .reset_index(name="complaints")
    )

    col1, col2 = st.columns(2)

    # Status chart
    with col1:

        fig_status = px.pie(
            status_data,
            names="resolution_status",
            values="complaints",
            hole=0.45,
            title="Open vs Closed Complaints",
            color_discrete_sequence=["#E76F51", "#2A9D8F"]
        )

        st.plotly_chart(
            fig_status,
            use_container_width=True
        )

    # Resolution duration
    with col2:

        resolved_df = filtered_df[
            filtered_df["resolution_hours"].notna()
        ].copy()

        if not resolved_df.empty:

            fig_resolution = px.histogram(
                resolved_df,
                x="resolution_hours",
                nbins=35,
                title="Resolution Duration Distribution",
                color_discrete_sequence=["#2A9D8F"]
            )

            fig_resolution.update_layout(
                template="plotly_white",
                xaxis_title="Resolution Hours",
                yaxis_title="Number of Complaints"
            )

            st.plotly_chart(
                fig_resolution,
                use_container_width=True
            )

        else:

            st.info(
                "No closed complaints with valid "
                "resolution durations."
            )

    # Borough resolution time
    borough_resolution = (
        filtered_df.groupby("borough")
        ["resolution_hours"]
        .mean()
        .reset_index()
    )

    fig_borough_resolution = px.bar(
        borough_resolution,
        x="borough",
        y="resolution_hours",
        color="resolution_hours",
        color_continuous_scale="Greens",
        title="Average Resolution Time by Borough"
    )

    fig_borough_resolution.update_layout(
        template="plotly_white",
        xaxis_title="Borough",
        yaxis_title="Average Hours"
    )

    st.plotly_chart(
        fig_borough_resolution,
        use_container_width=True
    )

    # Unresolved community boards
    unresolved_df = filtered_df[
        filtered_df["resolution_status"] == "Open"
    ]

    unresolved_boards = (
        unresolved_df.groupby("community_board")
        .size()
        .reset_index(name="unresolved_complaints")
        .sort_values(
            "unresolved_complaints",
            ascending=False
        )
    )

    st.subheader("Top Areas with Unresolved Complaints")

    st.dataframe(
        unresolved_boards.head(15),
        use_container_width=True,
        hide_index=True
    )

    # Resolution summary
    st.subheader("Resolution Summary")

    rcol1, rcol2, rcol3 = st.columns(3)

    rcol1.metric(
        "Closed Complaints",
        f"{closed_count:,}"
    )

    rcol2.metric(
        "Open Complaints",
        f"{open_count:,}"
    )

    rcol3.metric(
        "Average Resolution",
        f"{avg_resolution:.2f} hours"
    )


# ==========================================================
# DATA DOWNLOAD
# ==========================================================

st.markdown("---")

st.markdown(
    '<div class="section-title">'
    '📥 Download Data'
    '</div>',
    unsafe_allow_html=True
)

download_csv = filtered_df.to_csv(
    index=False
).encode("utf-8")

st.download_button(
    label="Download Filtered Dataset",
    data=download_csv,
    file_name="filtered_illegal_dumping_data.csv",
    mime="text/csv"
)

# ==========================================================
# FOOTER
# ==========================================================

st.markdown("---")

st.caption(
    "Illegal Waste Dumping Hotspot Analysis | "
    "NYC Open Data 311 Service Requests | "
    "Python • Pandas • Streamlit • Plotly"
)

st.caption(
    "Note: Complaint records represent reported incidents "
    "and do not necessarily represent all actual dumping incidents."
)

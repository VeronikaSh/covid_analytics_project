#######################
# Import libraries
import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px

######################
# Page configuration #
######################
st.set_page_config(
    page_title="Global COVID statistics",
    page_icon="🦠",
    layout="wide",
    initial_sidebar_state="expanded",
)

alt.themes.enable("dark")


#############
# Load data #
#############
df_reshaped = pd.read_csv("data/cleaned_covid_data.csv")
df_reshaped["year"] = pd.to_datetime(df_reshaped["date"]).dt.year
#######################
# Sidebar
with st.sidebar:
    st.title("COVID statistics")

    year_list = list(df_reshaped.year.unique())[::-1]
    continents = list(df_reshaped.continent.unique())

    start_year = st.selectbox("Select start year", year_list)
    end_year = st.selectbox(
        "Select end year", [year for year in year_list if year >= start_year]
    )

    df_filtered = df_reshaped[
        (df_reshaped.year >= start_year) & (df_reshaped.year <= end_year)
    ]

    continent_selection = st.multiselect("Select continent", continents)
    if continent_selection == []:
        continent_selection = ["All"]

    if "All" not in continent_selection:
        df_filtered = df_filtered[df_filtered.continent.isin(continent_selection)]

    countries = list(df_filtered.location.unique())
    countries_selection = st.multiselect("Select countries", countries)

    if countries_selection == []:
        countries_selection = ["All"]

    if "All" not in countries_selection:
        df_filtered = df_filtered[df_filtered.location.isin(countries_selection)]

    st.title("Map view")
    select_map_view = st.selectbox(
        "Select map view", ["Total cases", "Total deaths", "Share of vaccinated people"]
    )

    mapping_options = {
        "Total cases": "total_cases",
        "Total deaths": "total_deaths",
        "Share of vaccinated people": "people_vaccinated",
    }

###########
# Helpers #
###########


def format_number(num):
    if num < 1000000:
        if not num % 1000:
            return f"{num // 1000} K"
        else:
            return f"{round(num / 1000, 1)} K"

    if not num % 1000000:
        return f"{num // 1000000} M"
    return f"{round(num / 1000000, 1)} M"


def total_cases_at_start_and_end(df):
    df["date"] = pd.to_datetime(df["date"])
    earliest_entries_per_country = df.loc[df.groupby("location")["date"].idxmin()]
    latest_entries_per_country = df.loc[df.groupby("location")["date"].idxmax()]
    return earliest_entries_per_country, latest_entries_per_country


#########
# Plots #
#########
import pandas as pd
import altair as alt
import plotly.express as px


# Map
def make_choropleth(input_df, input_id, input_column, continent="All"):
    continent_scope = {
        "Asia": "asia",
        "Africa": "africa",
        "Europe": "europe",
        "North America": "north america",
        "South America": "south america",
    }

    map_scope = continent_scope.get(continent, "world")

    choropleth = px.choropleth(
        input_df,
        locations=input_df[input_id],
        color=input_df[input_column],
        locationmode="ISO-3",
        color_continuous_scale="Reds",
        range_color=(0, max(input_df[input_column])),
        scope=map_scope,  # Use the determined scope
        labels={"total cases": "Cumulative_cases"},
    )

    choropleth.update_layout(
        template="plotly_white",
        plot_bgcolor="rgba(0, 0, 0, 0)",
        paper_bgcolor="rgba(0, 0, 0, 0)",
        margin=dict(l=0, r=0, t=0, b=0),
        height=350,
        geo=dict(
            showframe=False, showcoastlines=False, projection_type="equirectangular"
        ),
        font=dict(family="Arial, sans-serif", size=12, color="White"),
    )

    choropleth.update_geos(
        visible=True, resolution=110, showcountries=True, countrycolor="RebeccaPurple"
    )

    choropleth.update_layout(coloraxis_showscale=True)

    return choropleth


# Donut chart
def make_donut(input_response, input_text, color_scale):
    if color_scale == "green":
        chart_color = ["#2ECC71", "#196F3D"]
    else:
        chart_color = ["#c61a09", "#ffc9bb"]

    source = pd.DataFrame(
        {"Topic": ["", input_text], "% value": [100 - input_response, input_response]}
    )
    source_bg = pd.DataFrame({"Topic": ["", input_text], "% value": [100, 0]})

    plot = (
        alt.Chart(source)
        .mark_arc(innerRadius=45, cornerRadius=25)
        .encode(
            theta="% value",
            color=alt.Color(
                "Topic:N",
                scale=alt.Scale(
                    domain=[input_text, ""],
                    range=chart_color,
                ),
                legend=None,
            ),
        )
        .properties(width=130, height=130)
    )

    text = plot.mark_text(
        align="center",
        color="#29b5e8",
        font="Lato",
        fontSize=32,
        fontWeight=700,
        fontStyle="italic",
    ).encode(text=alt.value(f"{input_response} %"))
    plot_bg = (
        alt.Chart(source_bg)
        .mark_arc(innerRadius=45, cornerRadius=20)
        .encode(
            theta="% value",
            color=alt.Color(
                "Topic:N",
                scale=alt.Scale(
                    domain=[input_text, ""],
                    range=chart_color,
                ),
                legend=None,
            ),
        )
        .properties(width=130, height=130)
    )
    return plot_bg + plot + text


# Heatmap
def make_heatmap(
    input_df, input_y, input_x, input_color, input_color_theme, scale_name
):
    heatmap = (
        alt.Chart(input_df)
        .mark_rect()
        .encode(
            y=alt.Y(
                f"{input_y}:O",
                axis=alt.Axis(
                    title="Country",
                    titleFontSize=18,
                    titlePadding=15,
                    titleFontWeight=900,
                    labelAngle=0,
                ),
            ),
            x=alt.X(
                f"{input_x}:O",
                axis=alt.Axis(
                    title="Month-Year",
                    titleFontSize=18,
                    titlePadding=15,
                    titleFontWeight=900,
                    labelAngle=45,  # Added for better visibility of dates
                ),
            ),
            color=alt.Color(
                f"max({input_color}):Q",
                legend=alt.Legend(title=scale_name),
                scale=alt.Scale(scheme=input_color_theme),
            ),
            stroke=alt.value("black"),
            strokeWidth=alt.value(0.25),
        )
        .properties(width=900)
        .configure_axis(labelFontSize=12, titleFontSize=12)
    )
    return heatmap


########################
# Dashboard Main Panel #
########################
col = st.columns((1.5, 4.5, 2), gap="medium")

with col[0]:
    st.markdown(f"#### Totals \n ###### (by end of {end_year})")

    earliest_entries_per_country, latest_entries_per_country = (
        total_cases_at_start_and_end(df_filtered)
    )

    total_cases_current = int(latest_entries_per_country["total_cases"].sum())
    delta_total_cases = int(
        total_cases_current - earliest_entries_per_country["total_cases"].sum()
    )
    latest_entries_per_country["share_vaccinated"] = (
        latest_entries_per_country["people_vaccinated"]
        / latest_entries_per_country["population"]
    ) * 100

    st.metric(
        label=f"Total cases",
        value=format_number(total_cases_current),
        delta=format_number(delta_total_cases),
    )

    total_deaths_current = int(latest_entries_per_country["total_deaths"].sum())
    delta_total_deaths = int(
        total_deaths_current - earliest_entries_per_country["total_deaths"].sum()
    )
    st.metric(
        label=f"Total deaths",
        value=format_number(total_deaths_current),
        delta=format_number(delta_total_deaths),
    )

    st.markdown("#### Rates")
    st.markdown(
        "<p style='font-size: 14px;'>Share of vacinated population</p>",
        unsafe_allow_html=True,
    )
    total_vaccinations_end_period = int(
        latest_entries_per_country["people_vaccinated"].sum()
    )
    total_population_end_period = int(latest_entries_per_country["population"].sum())

    share_of_vaccinated_population = round(
        (total_vaccinations_end_period / total_population_end_period) * 100
    )

    donut_chart_vaccinations = make_donut(
        share_of_vaccinated_population, "Share of vaccinated population", "green"
    )

    st.altair_chart(donut_chart_vaccinations)

    st.markdown("<p style='font-size: 14px;'>Death rate</p>", unsafe_allow_html=True)

    deaths_end_period = int(latest_entries_per_country["total_deaths"].sum())
    cases_end_period = int(latest_entries_per_country["total_cases"].sum())
    death_rate = round((deaths_end_period / cases_end_period) * 100, 1)

    donut_chart_death_rate = make_donut(death_rate, "Death rate", "red")

    st.altair_chart(donut_chart_death_rate)

    with col[1]:
        continent = "All"
        if len(continent_selection) == 1 and continent_selection[0] != "All":
            continent = continent_selection[0]

        st.markdown(f"#### # {select_map_view} by country")
        cases_per_country_map = make_choropleth(
            latest_entries_per_country,
            "iso_code",
            mapping_options.get(select_map_view),
            continent,
        )

        st.plotly_chart(cases_per_country_map, use_container_width=True)

        # Group by country and month_year, summing the total_cases and taking the max of population
        grouped = (
            df_filtered.groupby(["location", "Month_year"])
            .agg(
                {
                    "total_cases": "max",
                    "total_deaths": "max",
                    "people_vaccinated": "max",
                    "population": "max",
                }
            )
            .reset_index()
        )

        # Calculate the share of total_cases to population
        grouped["respective_share"] = (
            grouped[mapping_options.get(select_map_view)] / grouped["population"]
        ) * 100

        if select_map_view == "Total cases":
            title = "Share of total cases"
        elif select_map_view == "Total deaths":
            title = "Share of total deaths"
        elif select_map_view == "Share of vaccinated people":
            title = "Share of vaccinated people"

        st.markdown(f"#### {title} by country per month")

        heatmap = make_heatmap(
            grouped,
            "location",
            "Month_year",
            "respective_share",
            "reds",
            "%",
        )
        st.altair_chart(heatmap, use_container_width=True)

    with col[2]:
        st.markdown(f"#### Top 10 countries by {select_map_view.lower()}")

        df_sorted = latest_entries_per_country.sort_values(
            by=mapping_options.get(select_map_view), ascending=False
        )

        df_sorted["totals"] = df_sorted[mapping_options.get(select_map_view)].apply(
            format_number
        )

        st.dataframe(
            df_sorted.set_index("location")["totals"][:10],
        )

        with st.expander("About", expanded=True):
            st.write(
                """
                - Data: [Out World in Data](https://ourworldindata.org/covid-vaccinations).
                """
            )

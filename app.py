from email.policy import default
from pathlib import Path
import math

import geopandas
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    layout="wide", page_title="Exploration des loyers encadrés à Paris", page_icon="📈"
)

DATA_PATH = "https://opendata.paris.fr/explore/dataset/logement-encadrement-des-loyers/download/?format=geojson&timezone=Europe/Berlin&lang=fr"

NON_NUMERIC_COLUMNS = ["codeiris", "zonage", "commune", "insee", "gid", "geometry"]


@st.cache
def get_data(file_path: Path) -> geopandas.GeoDataFrame:

    gdf = geopandas.read_file(file_path)

    return gdf


gdf = get_data(DATA_PATH)

st.title("Visualisation des loyers de référence à Paris 🔍")

num_rooms_filters = {
    "1 pièce": 1,
    "2 pièces": 2,
    "3 pièces": 3,
    "4 pièces et plus": 4,
}

construction_year_filters = {
    "Avant 1946": "Avant 1946",
    "Entre 1946 et 1970": "1946-1970",
    "Entre 1971 et 1990": "1971-1990",
    "Après 1990": "Apres 1990",
}


flat_type_filters = {
    "Meublé": "meublé",
    "Non meublé": "non meublé",
}

variable_filters = {
    "Loyer de référence ": "ref",
    "Loyer de référence majoré": "max",
    "Loyer de référence minoré": "min",
}

st.markdown(
    r"""Vous pouvez sélectionner plus d'une valeur par caractéristique, dans ce cas c'est une valeur moyenne qui est affichée."""
)

col1, col2, col3, col4 = st.columns(4)


with col1:
    num_rooms = st.multiselect(
        "Taille du logement",
        options=num_rooms_filters.keys(),
        default="2 pièces",
    )

with col2:
    construction_year = st.multiselect(
        "Année de construction",
        options=construction_year_filters.keys(),
        default="Après 1990",
    )

with col3:
    flat_type = st.multiselect(
        "Type de logement", options=flat_type_filters.keys(), default="Non meublé"
    )

with col4:
    variable = st.radio("Variable", options=variable_filters.keys(), index=1)

num_rooms_df_filter = [num_rooms_filters[e] for e in num_rooms]
construction_year_df_filter = [construction_year_filters[e] for e in construction_year]
flat_type_df_filter = [flat_type_filters[e] for e in flat_type]
selected_variable = variable_filters[variable]

selected_gdf_mean = (
    gdf.loc[
        (gdf.epoque.isin(construction_year_df_filter))
        & (gdf.meuble_txt.isin(flat_type_df_filter))
        & (gdf.piece.isin(num_rooms_df_filter)),
    ]
    .groupby("code_grand_quartier")
    .agg(value=(selected_variable, "mean"), geometry=("geometry", "first"))
)
selected_gdf_mean = geopandas.GeoDataFrame(selected_gdf_mean)

text = f"""Pour votre sélection, le {variable.lower()} est compris entre **{selected_gdf_mean.value.round(2).min()}** €/m² et **{selected_gdf_mean.value.round(2).max()}** €/m²."""
st.markdown(text)

fig = px.choropleth_mapbox(
    selected_gdf_mean,
    geojson=selected_gdf_mean.geometry,
    locations=selected_gdf_mean.index,
    color=selected_gdf_mean.value.round(2),
    center={"lat": 48.86, "lon": 2.33},
    mapbox_style="open-street-map",
    zoom=11,
    height=600,
    width=900,
    opacity=0.5,
    labels={"color": f"{variable} (€/m²)"},
    color_continuous_scale=["#fee6ce", "#fdae6b", "#e6550d"],
    range_color=[
        math.floor(selected_gdf_mean.value.min()),
        math.ceil(selected_gdf_mean.value.max()),
    ],
)

st.plotly_chart(fig, use_container_width=True)

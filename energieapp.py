import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Energie Dashboard", layout="wide")
st.title("🔋 Interactief Energie Dashboard energie")

# Upload meerdere CSV-bestanden
uploaded_files = st.file_uploader("📤 Upload één of meerdere CSV-bestanden", type=["csv"], accept_multiple_files=True)

if uploaded_files:
    dataframes = []
    for file in uploaded_files:
        try:
            df = pd.read_csv(file, encoding='utf-8', sep=None, engine='python')  # Detectie van delimiter
            dataframes.append(df)
        except Exception as e:
            st.error(f"❌ Fout bij inlezen van {file.name}: {str(e)}")

    # Merge alle bestanden
    data = pd.concat(dataframes, ignore_index=True)

    # Voorbewerking
    data.columns = data.columns.str.strip()
    data = data.rename(columns={data.columns[0]: 'Timestamp'})

    # Tijdzone weghalen (alles na '+') in Timestamp voor correcte conversie
    data['Timestamp_clean'] = data['Timestamp'].astype(str).str.split('+').str[0]

    # Converteer naar datetime zonder timezone info
    data['Timestamp'] = pd.to_datetime(data['Timestamp_clean'], errors='coerce')

    # Tijdelijke kolom verwijderen
    data.drop(columns=['Timestamp_clean'], inplace=True)

    # Verwijder rijen zonder geldige Timestamp
    data = data.dropna(subset=['Timestamp'])

    # Tijdcomponenten afleiden
    data['Jaar'] = data['Timestamp'].dt.year
    data['Maand'] = data['Timestamp'].dt.month
    data['Dag'] = data['Timestamp'].dt.day
    data['Uur'] = data['Timestamp'].dt.hour

    tijd_kolommen = ['Timestamp', 'Jaar', 'Maand', 'Dag', 'Uur']
    categorie_kolommen = [col for col in data.columns if col not in tijd_kolommen]

    # Melt naar lange tabel
    data_melted = data.melt(id_vars=tijd_kolommen, value_vars=categorie_kolommen,
                            var_name='Categorie', value_name='Waarde')

    # Verwijder eenheden uit waarden
    data_melted['Waarde'] = data_melted['Waarde'].astype(str).str.extract(r'([\d\.,]+)')[0]
    data_melted['Waarde'] = data_melted['Waarde'].str.replace(',', '.')
    data_melted['Waarde'] = pd.to_numeric(data_melted['Waarde'], errors='coerce')

    # Filters
    st.sidebar.header("🔍 Filters")

    jaren = st.sidebar.multiselect("Selecteer Jaar", sorted(data_melted['Jaar'].dropna().unique()), default=None)
    maanden = st.sidebar.multiselect("Selecteer Maand", sorted(data_melted['Maand'].dropna().unique()), default=None)
    dagen = st.sidebar.multiselect("Selecteer Dag", sorted(data_melted['Dag'].dropna().unique()), default=None)
    uren = st.sidebar.multiselect("Selecteer Uur", sorted(data_melted['Uur'].dropna().unique()), default=None)
    categorieen = st.sidebar.multiselect("Selecteer Categorieën", sorted(data_melted['Categorie'].unique()), default=None)

    gefilterd = data_melted.copy()

    if jaren:
        gefilterd = gefilterd[gefilterd['Jaar'].isin(jaren)]
    if maanden:
        gefilterd = gefilterd[gefilterd['Maand'].isin(maanden)]
    if dagen:
        gefilterd = gefilterd[gefilterd['Dag'].isin(dagen)]
    if uren:
        gefilterd = gefilterd[gefilterd['Uur'].isin(uren)]
    if categorieen:
        gefilterd = gefilterd[gefilterd['Categorie'].isin(categorieen)]

    # Grafiek
    st.subheader("📈 Grafiek")

    if not gefilterd.empty:
        fig = px.line(gefilterd,
                      x="Timestamp",
                      y="Waarde",
                      color="Categorie",
                      title="Waarden per tijdstip",
                      markers=True)
        fig.update_layout(xaxis_title="Tijd", yaxis_title="Waarde")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ Geen data beschikbaar voor deze filtercombinatie.")

    # Gemiddeldes tonen
    st.subheader("📊 Gemiddeldes")
    gemiddelde_per_categorie = gefilterd.groupby('Categorie')['Waarde'].mean().round(2).reset_index()
    st.dataframe(gemiddelde_per_categorie.rename(columns={'Waarde': 'Gemiddelde'}))

    # Preview data
    with st.expander("📄 Bekijk gefilterde gegevens"):
        st.dataframe(gefilterd.head(100))

else:
    st.info("📥 Upload één of meerdere CSV-bestanden om te beginnen.")     
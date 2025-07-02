import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Energie Dashboard", layout="wide")
st.title("🔋 Interactief Energie Dashboard")

# Upload CSV-bestanden
uploaded_files = st.file_uploader("📤 Upload één of meerdere CSV-bestanden", type=["csv"], accept_multiple_files=True)

if uploaded_files:
    dataframes = []
    for file in uploaded_files:
        try:
            df = pd.read_csv(file, encoding='utf-8', sep=None, engine='python')
            dataframes.append(df)
        except Exception as e:
            st.error(f"❌ Fout bij inlezen van {file.name}: {str(e)}")

    # Combineer data
    data = pd.concat(dataframes, ignore_index=True)
    data.columns = data.columns.str.strip()
    data = data.rename(columns={data.columns[0]: 'Timestamp'})

    data['Timestamp_clean'] = data['Timestamp'].astype(str).str.split('+').str[0]
    data['Timestamp'] = pd.to_datetime(data['Timestamp_clean'], errors='coerce')
    data.drop(columns=['Timestamp_clean'], inplace=True)
    data = data.dropna(subset=['Timestamp'])

    # Tijdcomponenten
    data['Jaar'] = data['Timestamp'].dt.year
    data['Maand'] = data['Timestamp'].dt.month
    data['Dag'] = data['Timestamp'].dt.day
    data['Uur'] = data['Timestamp'].dt.hour

    tijd_kolommen = ['Timestamp', 'Jaar', 'Maand', 'Dag', 'Uur']
    waarde_kolommen = [col for col in data.columns if col not in tijd_kolommen]

    data_melted = data.melt(id_vars=tijd_kolommen, value_vars=waarde_kolommen,
                            var_name='Categorie', value_name='Waarde')

    # Waarde opschonen
    data_melted['Waarde'] = data_melted['Waarde'].astype(str).str.extract(r'([\d\.,]+)')[0]
    data_melted['Waarde'] = data_melted['Waarde'].str.replace(',', '.', regex=False)
    data_melted['Waarde'] = pd.to_numeric(data_melted['Waarde'], errors='coerce')

    # 🔍 Filter: Categorie
    st.sidebar.header("📦 Filters")
    categorieen = sorted(data_melted['Categorie'].dropna().unique())
    geselecteerde_categorieen = st.sidebar.multiselect("Selecteer categorieën", categorieen, default=categorieen)

    data_filtered = data_melted[data_melted['Categorie'].isin(geselecteerde_categorieen)]

    # 🔍 Filter: Jaar, Maand, Dag
    beschikbare_jaren = sorted(data_filtered['Jaar'].dropna().unique())
    jaar_selectie = st.selectbox("📅 Selecteer jaar", beschikbare_jaren, index=len(beschikbare_jaren) - 1)

    beschikbare_maanden = sorted(data_filtered[data_filtered['Jaar'] == jaar_selectie]['Maand'].unique())
    maand_selectie = st.selectbox("🗓️ Selecteer maand", beschikbare_maanden)

    beschikbare_dagen = sorted(data_filtered[(data_filtered['Jaar'] == jaar_selectie) & (data_filtered['Maand'] == maand_selectie)]['Dag'].unique())
    dag_selectie = st.selectbox("📆 Selecteer dag", beschikbare_dagen)

    # ======================= GRAFIEK 1: Jaar (per maand) =======================
    st.subheader(f"📊 Jaaroverzicht: totaal per maand ({jaar_selectie})")
    jaar_data = data_filtered[data_filtered['Jaar'] == jaar_selectie]

    maand_aggregatie = jaar_data.groupby(['Maand', 'Categorie'])['Waarde'].sum().reset_index()

    fig_jaar = px.bar(
        maand_aggregatie,
        x='Maand', y='Waarde', color='Categorie', barmode='group',
        labels={'Waarde': 'Totaal', 'Maand': 'Maand'},
        title=f"Maandtotalen voor {jaar_selectie}"
    )
    st.plotly_chart(fig_jaar, use_container_width=True)

    # ======================= GRAFIEK 2: Maand (per dag) =======================
    st.subheader(f"📆 Maandoverzicht: totaal per dag ({jaar_selectie}-{maand_selectie})")
    maand_data = jaar_data[jaar_data['Maand'] == maand_selectie]

    dag_aggregatie = maand_data.groupby(['Dag', 'Categorie'])['Waarde'].sum().reset_index()

    fig_maand = px.bar(
        dag_aggregatie,
        x='Dag', y='Waarde', color='Categorie', barmode='group',
        labels={'Waarde': 'Totaal', 'Dag': 'Dag'},
        title=f"Dagtotalen voor {jaar_selectie}-{maand_selectie}"
    )
    st.plotly_chart(fig_maand, use_container_width=True)

    # ======================= GRAFIEK 3: Dag (per uur) =======================
    st.subheader(f"⏰ Dagoverzicht: totaal per uur ({dag_selectie}-{maand_selectie}-{jaar_selectie})")
    dag_data = maand_data[maand_data['Dag'] == dag_selectie]

    uur_aggregatie = dag_data.groupby(['Uur', 'Categorie'])['Waarde'].sum().reset_index()

    fig_dag = px.bar(
        uur_aggregatie,
        x='Uur', y='Waarde', color='Categorie', barmode='group',
        labels={'Waarde': 'Totaal', 'Uur': 'Uur'},
        title=f"Uurtotalen voor {dag_selectie}-{maand_selectie}-{jaar_selectie}"
    )
    st.plotly_chart(fig_dag, use_container_width=True)

    # Preview
    with st.expander("📄 Bekijk ruwe data"):
        st.dataframe(data_filtered.head(100))

else:
    st.info("📥 Upload één of meerdere CSV-bestanden om te beginnen.")

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Energie Dashboard", layout="wide")
st.title("🔋 Interactief Energie Dashboard")

uploaded_files = st.file_uploader("📤 Upload één of meerdere CSV-bestanden", type=["csv"], accept_multiple_files=True)

if uploaded_files:
    dataframes = []
    for file in uploaded_files:
        try:
            df = pd.read_csv(file, encoding='utf-8', sep=None, engine='python')
            dataframes.append(df)
        except Exception as e:
            st.error(f"❌ Fout bij inlezen van {file.name}: {str(e)}")

    data = pd.concat(dataframes, ignore_index=True)
    data.columns = data.columns.str.strip()
    data = data.rename(columns={data.columns[0]: 'Timestamp'})
    data['Timestamp_clean'] = data['Timestamp'].astype(str).str.split('+').str[0]
    data['Timestamp'] = pd.to_datetime(data['Timestamp_clean'], errors='coerce')
    data.drop(columns=['Timestamp_clean'], inplace=True)
    data = data.dropna(subset=['Timestamp'])
    te_verwijderen_kolommen = [
    "RAK1 1 NUCLEAIR CT15 kWh (kWh)",
    "LK5 1 II P1 CT643 kWh (kWh)",
    "LK5 4 II P1 CT943 kWh (kWh)",
    "LK4 4 I P1 CT543 kWh (kWh)",
    "LK4 2 II P1 CT753 kWh (kWh)",
    "Elektriciteit kW (kW)",
    "WKO TSA 1 Energiemeting pompen 29CP2/3 (kWh)",
    "Afgifteset Inductie units Energiemeting pompen 34CP2/3/4 (kWh)",
    "WKO elektra pompen 33TP1/2/3 Energiemeting pompen 33TP1/2/3 (kWh)",
    "WKO elektra pompen 32TP1/2/3 Energiemeting pompen 32TP1/2/3 (kWh)",
    "LK5 3 I P1 CT453 kWh (kWh)"
    ]
    
    # Verwijder deze kolommen indien aanwezig
    data = data.drop(columns=[col for col in te_verwijderen_kolommen if col in data.columns])


    data['Jaar'] = data['Timestamp'].dt.year
    data['Maand'] = data['Timestamp'].dt.month
    data['Dag'] = data['Timestamp'].dt.day
    data['Uur'] = data['Timestamp'].dt.hour

    tijd_kolommen = ['Timestamp', 'Jaar', 'Maand', 'Dag', 'Uur']
    waarde_kolommen = [col for col in data.columns if col not in tijd_kolommen]

    data_melted = data.melt(id_vars=tijd_kolommen, value_vars=waarde_kolommen,
                            var_name='Categorie', value_name='Waarde')

    data_melted['Waarde'] = data_melted['Waarde'].astype(str).str.extract(r'([\d\.,]+)')[0]
    data_melted['Waarde'] = data_melted['Waarde'].str.replace(',', '.', regex=False)
    data_melted['Waarde'] = pd.to_numeric(data_melted['Waarde'], errors='coerce')

    st.header("📦 Filters")

    # Categorie filter
    categorieen = sorted(data_melted['Categorie'].dropna().unique())
    geselecteerde_categorieen = st.multiselect("Selecteer categorieën", categorieen, default=categorieen)
    data_filtered = data_melted[data_melted['Categorie'].isin(geselecteerde_categorieen)]

    # Jaar filter
    beschikbare_jaren = sorted(data_filtered['Jaar'].dropna().unique())
    jaar_selectie = st.selectbox("📅 Selecteer jaar", beschikbare_jaren, index=len(beschikbare_jaren) - 1)

    # Maand filter
    beschikbare_maanden = sorted(data_filtered[data_filtered['Jaar'] == jaar_selectie]['Maand'].unique())
    maand_selectie = st.selectbox("🗓️ Selecteer maand", beschikbare_maanden)

    # Dag filter
    beschikbare_dagen = sorted(data_filtered[(data_filtered['Jaar'] == jaar_selectie) & (data_filtered['Maand'] == maand_selectie)]['Dag'].unique())
    dag_selectie = st.selectbox("📆 Selecteer dag", beschikbare_dagen)

    # =================== GRAFIEK 1: Jaar met trendlijn ===================
    st.subheader(f"📊 Jaaroverzicht: totaal per maand ({jaar_selectie})")

    jaar_data = data_filtered[data_filtered['Jaar'] == jaar_selectie]
    maand_aggregatie = jaar_data.groupby(['Maand', 'Categorie'])['Waarde'].sum().reset_index()

    vorig_jaar = jaar_selectie - 1
    vorig_jaar_data = data_filtered[data_filtered['Jaar'] == vorig_jaar]
    maand_aggregatie_vorig_jaar = vorig_jaar_data.groupby(['Maand', 'Categorie'])['Waarde'].sum().reset_index()

    fig = go.Figure()

    # Bar per categorie huidig jaar
    for cat in geselecteerde_categorieen:
        df_cat = maand_aggregatie[maand_aggregatie['Categorie'] == cat]
        fig.add_trace(go.Bar(
            x=df_cat['Maand'],
            y=df_cat['Waarde'],
            name=f"{cat} {jaar_selectie}",
            offsetgroup=cat
        ))

    # Lijn per categorie vorig jaar
    for cat in geselecteerde_categorieen:
        df_cat_vorig = maand_aggregatie_vorig_jaar[maand_aggregatie_vorig_jaar['Categorie'] == cat]
        fig.add_trace(go.Scatter(
            x=df_cat_vorig['Maand'],
            y=df_cat_vorig['Waarde'],
            mode='lines+markers',
            name=f"{cat} {vorig_jaar} (trend)",
            line=dict(dash='dash')
        ))

    fig.update_layout(
        barmode='group',
        xaxis_title='Maand',
        yaxis_title='Totaal',
        title=f"Maandtotalen {jaar_selectie} en trendlijn {vorig_jaar}",
        legend_title="Categorie / Jaar"
    )

    st.plotly_chart(fig, use_container_width=True)

    # =================== GRAFIEK 2: Maand (per dag) ===================
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

    # =================== GRAFIEK 3: Dag (per uur) ===================
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

    # Preview ruwe data
    with st.expander("📄 Bekijk ruwe data"):
        st.dataframe(data_filtered.head(100))

else:
    st.info("📥 Upload één of meerdere CSV-bestanden om te beginnen.")

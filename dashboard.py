import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import skew, kurtosis, ttest_ind, pearsonr


# Cargar datos
def load_data(file):
    df = pd.read_excel(file, header=1)
    return df


# Detectar filas con palabras clave en columnas específicas para incidencias separación tornillos intraplaca
palabras_clave = ["INTRAPLACAS", "INTRAPLAQUES", "DESPRÈS", "DESPRENDIDO", "SEPARADO", "SEPARACIÓN", "SEPARADAS",
                  "SOLTADO"]
columnas_revisar = ['COMPLICATIONS INTRAOPERATORY', 'DIAGNOSIS 1', 'OBSERVATIONS 1', 'OBSERVATIOS 2', 'OBSERVATIONS2']


def contiene_palabra_clave(fila):
    return any(any(palabra in str(fila[col]).upper() for palabra in palabras_clave) for col in columnas_revisar)


# Interfaz Streamlit
st.set_page_config(page_title="Pectus Up: Datos y Tendencias", layout="wide")
st.title("Pectus Up: Datos y Tendencias")

uploaded_file = st.file_uploader("Sube el archivo de Excel", type=["xls", "xlsx"])
if uploaded_file:
    df = load_data(uploaded_file)
    st.success("Datos cargados correctamente.")


    #Filtros Globales

    st.sidebar.header("Filtros Globales")

        #Filtro de Países

    country_options = ["Todos"] + list(df["COUNTRY"].unique())
    selected_countries = st.sidebar.multiselect("Países:", country_options, default="Todos")

    if "Todos" not in selected_countries:
        df = df[df["COUNTRY"].isin(selected_countries)]
    elif len(selected_countries) == 0:
        st.write("Ningún país ha sido seleccionado")




        #Filtro de años

    year_options = ["Todos"] + list(df["YEAR"].unique())
    selected_years = st.sidebar.multiselect("Años:", year_options, default="Todos")

    if "Todos" not in selected_years:
        df = df[df["YEAR"].isin(selected_years)]


    # Pestañas para la organización
    tabs = st.tabs(
        ["Resumen General", "Análisis Comercial", "Análisis Técnico", "Incidencias",
         "Exploración Adicional"])


    # Resumen General (Fase 1)
    with tabs[0]:
        st.header("Datos Generales")
        st.write(
            "Sección dedicada al análisis del estado general de los casos registrados en la base de datos. Se incluyen visualizaciones sobre la distribución de los casos según su estado, su evolución a lo largo del tiempo y el uso de diferentes kits en los procedimientos. Este análisis proporciona una visión clara del volumen y tipo de casos manejados, ayudando a entender tendencias y tomar decisiones estratégicas.")

        st.subheader("Estado de los Casos")

        # Definir el mapeo de valores a nombres
        estado_map = {
            1: "1: Caso Abierto",
            2: "2:Caso Aprobado",
            3: "3: Informe Enviado",
            4: "4: Caso Operado",
            5: "5: Caso Retirado"
        }

        # Aplicar el mapeo de estados
        df["STATE NUMBER"] = df["STATE NUMBER"].map(estado_map).fillna(df["STATE NUMBER"])

        # Estado de los casos totales
        status_counts = df["STATE NUMBER"].value_counts()
        fig_pie = px.pie(names=status_counts.index, values=status_counts.values,
                         title="Distribución de Informes Totales por Estado",
                         labels={"names": "STATE NUMBER"})
        st.plotly_chart(fig_pie)

        # Estado de los casos según año

        # Crear DataFrame agrupado correctamente
        sunburst_data = df.groupby(["YEAR", "STATE NUMBER"]).size().reset_index(name="Informes")

        fig_sunburst = px.sunburst(sunburst_data, path=["YEAR", "STATE NUMBER"], values="Informes",
                                   title="Distribución de Informes por Año y Estado")
        # Agregar porcentaje a las etiquetas
        fig_sunburst.update_traces(textinfo="label+percent entry")

        st.plotly_chart(fig_sunburst)

        # 🔹 Evolución de los Informes Totales, Intervensiones y Explantaciones por Año
        st.subheader("Evolución Informes, Intervenciones y Explantaciones por Año")


        # Convertir columnas de fecha
        df["DATE"] = pd.to_datetime(df["DATE"], errors='coerce')
        df["SURGERY DATE"] = pd.to_datetime(df["SURGERY DATE"], errors='coerce')
        df["MONTHTAC"] = df["DATE"].dt.to_period("M").astype(str)

        #Calcular número de casos operados/intervenidos
        df["Intervenciones"] = df["SURGERY DATE"].notna().astype(int)
        df_intervenciones = df[df["Intervenciones"] == 1]


        #Calcular número de casos explantados
        df["Explantaciones"] = df["DATE2"].notna().astype(int)
        df_explantaciones = df[df["Explantaciones"] == 1]


        # Contar casos, intervenciones y explantaciones por año
        yearly_counts = df.groupby("YEAR").size().reset_index(name="Casos")
        yearly_counts_interv = df_intervenciones.groupby("YEAR").size().reset_index(name="Casos")
        yearly_counts_explant = df_explantaciones.groupby("YEAR").size().reset_index(name="Casos")

        # Calcular el total de casos en todos los años
        total_cases = yearly_counts["Casos"].sum()
        total_interv = yearly_counts_interv["Casos"].sum()
        total_explant = yearly_counts_explant["Casos"].sum()


        # Calcular porcentaje respecto al total de TODOS los casos, intervenciones o explantaciones
        yearly_counts["percentage"] = (yearly_counts["Casos"] / total_cases) * 100
        yearly_counts_interv["percentage"] = (yearly_counts_interv["Casos"] / total_interv) * 100
        yearly_counts_explant["percentage"] = (yearly_counts_explant["Casos"] / total_explant) * 100


        #Seleccionar informes, intervenciones o explantaciones para visualizar en la gráfica

        # Crear diccionario con las opciones
        options = {
            "Informes Totales": yearly_counts,
            "Intervenciones": yearly_counts_interv,
            "Explantaciones": yearly_counts_explant
        }

        # Selector en Streamlit
        selected_option = st.selectbox("Seleccione lo que desea visualizar", list(options.keys()))

        # Obtener el DataFrame correspondiente a la opción seleccionada
        selected_variable = options[selected_option]

        # Número de informes, intervenciones y explantaciones
        num_casos = selected_variable["Casos"].sum()
        st.write(f"Número de {selected_option}: **{num_casos}**")



        # Crear gráfico de línea
        fig2 = px.line(selected_variable, x="YEAR", y="Casos", markers=True, title=f"Evolución de {selected_option}")

        ###################### MODIFICAR. Está ajustada la ultima flecha a los datos que hay actualmente en la BBDD para que no pise la linea

        # Añadir anotaciones en los puntos (número de casos y porcentaje)
        for i, row in selected_variable.iterrows():
            if i == len(selected_variable) - 1 and (selected_option == "Informes Totales" or selected_option == "Intervenciones"):
                fig2.add_annotation(
                    x=row["YEAR"], y=row["Casos"],  # Punto final (donde apunta la flecha)
                    ax=row["YEAR"] + 0.1, ay=row["Casos"] + 25,  #  Mueve el inicio de la flecha +1 en x es un año máss +1 en y es un caso más
                    xref="x", yref="y",  # 🔹 Se asegura que las coordenadas sean relativas a los ejes del gráfico
                    axref="x", ayref="y",  # 🔹 Se asegura que la flecha respete los ejes
                    text=f"{int(row['Casos'])} ({row['percentage']:.1f}%)",
                    showarrow=True, arrowhead=2, yshift=10, font=dict(color="#8A2BE2")
                )
            else:
                fig2.add_annotation(
                    x=row["YEAR"], y=row["Casos"],
                    text=f"{int(row['Casos'])} ({row['percentage']:.1f}%)",
                    showarrow=True, arrowhead=2, yshift=10, font=dict(color="#8A2BE2")
                )
        ###########################

        # Asegurar que solo aparezcan años enteros en el eje X
        fig2.update_layout(
            xaxis_title="Año",
            xaxis=dict(tickmode="linear", dtick=1)  # Evitar decimales en el eje X
        )
        fig2.update_traces(mode="markers+lines", line=dict(color="#32CD32"))

        # Mostrar gráfico en Streamlit
        st.plotly_chart(fig2)


        # Distribución kits utilizados

        st.subheader("Distribución de Kits Utilizados")
        kit_counts = df["KIT"].value_counts()
        fig3 = px.bar(kit_counts, x=kit_counts.index, y=kit_counts.values, title="Uso de Kits")
        fig3.update_traces(
            text=[f"{v} ({v / kit_counts.sum():.1%})" for v in kit_counts.values],
            textposition="outside"
        )
        fig3.update_layout(
            yaxis_title="Frecuencia de Uso"  # Nombre del eje Y
        )
        st.plotly_chart(fig3)

        st.subheader("Relación entre Kit y Estado del Caso")
        kit_status_counts = df.groupby(["KIT", "STATE NUMBER"]).size().unstack().fillna(0)
        fig4 = px.bar(kit_status_counts, barmode="stack", title="Casos por Kit y Estado")
        fig4.update_layout(
            yaxis_title="Frecuencia de Uso"  # Nombre del eje Y
        )

        st.plotly_chart(fig4)

        # Calcular los porcentajes dentro de cada KIT
        kit_status_percent = kit_status_counts.div(kit_status_counts.sum(axis=1), axis=0) * 100

        # Crear un DataFrame con los datos en formato más claro
        kit_status_summary = pd.DataFrame()

        for kit in kit_status_counts.index:
            for estado in kit_status_counts.columns:
                total_casos = kit_status_counts.loc[kit, estado]
                porcentaje = kit_status_percent.loc[kit, estado]
                kit_status_summary.loc[f"Estado {estado}", f"Kit {kit}"] = f"{int(total_casos)} ({porcentaje:.1f}%)"

        # Mostrar la tabla en Streamlit
        st.dataframe(kit_status_summary)

        st.subheader("Uso de Medidas de Tornillos y Placas Elevadoras")

        if "b (screw length)" in df.columns and "a (elevator plate)" in df.columns:

            # LIMPIAR Y CONVERTIR LOS DATOS A NÚMEROS
            df["b (screw length)"] = pd.to_numeric(df["b (screw length)"], errors="coerce")
            df["a (elevator plate)"] = df["a (elevator plate)"].astype(str).str.strip()  # Elimina espacios ocultos
            df["a (elevator plate)"] = pd.to_numeric(df["a (elevator plate)"], errors="coerce")
            df["a (elevator plate)"] = df["a (elevator plate)"].astype(float)  # Asegura que no sean categorías
            df["YEAR"] = pd.to_numeric(df["YEAR"], errors="coerce")  # Asegurar que 'year' sea numérico

            # Contar valores y ordenar correctamente
            screw_counts = df["b (screw length)"].value_counts().sort_index()
            plate_counts = df["a (elevator plate)"].value_counts().sort_index()

            # Convertir Series a DataFrame antes de graficar
            screw_counts_df = screw_counts.reset_index()
            screw_counts_df.columns = ["Medida de Tornillo (mm)", "Frecuencia"]

            plate_counts_df = plate_counts.reset_index()
            plate_counts_df.columns = ["Medida de Placa Elevadora (mm)", "Frecuencia"]

            # Graficar tornillos
            fig5 = px.bar(screw_counts_df, x="Medida de Tornillo (mm)", y="Frecuencia",
                          title="Frecuencia de Medidas de Tornillos")

            # Graficar placas elevadoras
            fig6 = px.bar(plate_counts_df, x="Medida de Placa Elevadora (mm)", y="Frecuencia",
                          title="Frecuencia de Medidas de Placas Elevadoras")


            # Forzar el eje X a tratar los valores como categorías para que no redondee las medidas de las placas y nombrar eje x e y
            fig6.update_layout(xaxis_type="category",
                               xaxis_title="Medida de Placa Elevadora (mm)",  # Nombre del eje X
                               yaxis_title="Frecuencia de Uso"  # Nombre del eje Y
                               )

            fig5.update_layout(
                xaxis_title="Medida de Tornillo (mm)",  # Nombre del eje X
                yaxis_title="Frecuencia de Uso"  # Nombre del eje Y
            )

            fig5.update_traces(marker_color="#FF7F0E")
            fig6.update_traces(marker_color="#1F77B4")

            # Agregar número de casos y porcentaje en el gráfico de tornillos
            total_screws = screw_counts.sum()
            fig5.update_traces(
                text=[f"{int(v)} ({v / total_screws:.1%})" for v in screw_counts.values],
                textposition="outside"
            )

            # Agregar número de casos y porcentaje en el gráfico de placas
            total_plates = plate_counts.sum()
            fig6.update_traces(
                text=[f"{int(v)} ({v / total_plates:.1%})" for v in plate_counts.values],
                textposition="outside"
            )

            # Mostrar los gráficos en Streamlit
            st.plotly_chart(fig5)
            st.plotly_chart(fig6)

            # SELECCIÓN DE MEDIDAS Y GRÁFICO DE EVOLUCIÓN POR AÑO
            st.subheader("Evolución del uso de medidas específicas por año")

            # Opciones únicas de tornillos y placas
            screw_options = sorted(df["b (screw length)"].dropna().unique())
            plate_options = sorted(df["a (elevator plate)"].dropna().unique())

            # Selección de medida específica
            selected_screw = st.selectbox("Selecciona una medida de tornillo", screw_options)

            # Filtrar el DataFrame por las medida seleccionada de tornillo
            df_screw = df[df["b (screw length)"] == selected_screw]

            # Contar número de casos por año para cada medida de tornillo
            screw_yearly_counts = df_screw.groupby("YEAR").size().reset_index(name="count_screw")

            # Calcular total de casos por año
            total_cases_per_year = df.groupby("YEAR").size().reset_index(name="total_cases")

            # Merge de datos para agregar el total de casos por año
            screw_yearly_counts = screw_yearly_counts.merge(total_cases_per_year, on="YEAR", how="left")

            # Calcular porcentaje de uso por año
            screw_yearly_counts["percentage"] = (screw_yearly_counts["count_screw"] / screw_yearly_counts[
                "total_cases"]) * 100

            # 🔹 GRAFICO EVOLUCIÓN DE TORNILLOS
            fig_screw = px.line(screw_yearly_counts, x="YEAR", y="count_screw",
                                markers=True,
                                labels={"count_screw": "Número de Casos", "YEAR": "Año"},
                                title=f"Evolución del uso de tornillos de {selected_screw} mm")

            # Añadir anotaciones en los puntos (número de casos y porcentaje)
            for i, row in screw_yearly_counts.iterrows():
                fig_screw.add_annotation(
                    x=row["YEAR"], y=row["count_screw"],
                    text=f"{int(row['count_screw'])} ({row['percentage']:.1f}%)",
                    showarrow=True, arrowhead=2, yshift=10, font=dict(color="#1F77B4")
                )

            # Personalización de trazos
            fig_screw.update_traces(mode="markers+lines", line=dict(color="#FF7F0E"))

            # Configurar el eje X para que solo muestre años enteros
            fig_screw.update_layout(xaxis=dict(tickmode="linear", dtick=1))

            # Mostrar gráfico de tornillos en Streamlit
            st.plotly_chart(fig_screw)

            # 🔹 GRAFICO EVOLUCIÓN DE PLACAS

            # Selección de medida específica
            selected_plate = st.selectbox("Selecciona una medida de placa", plate_options)

            # Filtrar el DataFrame por las medida seleccionada de placa
            df_plate = df[df["a (elevator plate)"] == selected_plate]

            # Contar número de casos por año para cada medida de placa
            plate_yearly_counts = df_plate.groupby("YEAR").size().reset_index(name="count_plate")

            # Merge de datos para agregar el total de casos por año
            plate_yearly_counts = plate_yearly_counts.merge(total_cases_per_year, on="YEAR", how="left")

            # Calcular porcentaje de uso por año
            plate_yearly_counts["percentage"] = (plate_yearly_counts["count_plate"] / plate_yearly_counts[
                "total_cases"]) * 100

            fig_plate = px.line(plate_yearly_counts, x="YEAR", y="count_plate",
                                markers=True,
                                labels={"count_plate": "Número de Casos", "YEAR": "Año"},
                                title=f"Evolución del uso de placas de {selected_plate} mm")

            # Añadir anotaciones en los puntos (número de casos y porcentaje)
            for i, row in plate_yearly_counts.iterrows():
                fig_plate.add_annotation(
                    x=row["YEAR"], y=row["count_plate"],
                    text=f"{int(row['count_plate'])} ({row['percentage']:.1f}%)",
                    showarrow=True, arrowhead=2, yshift=10, font=dict(color="#FF7F0E")
                )

            # Personalización de trazos
            fig_plate.update_traces(mode="markers+lines", line=dict(color="#1F77B4"))

            # Configurar el eje X para que solo muestre años enteros
            fig_plate.update_layout(xaxis=dict(tickmode="linear", dtick=1))

            # Mostrar gráfico de placas en Streamlit
            st.plotly_chart(fig_plate)

            # CALCULAR DATOS CONOCIDOS Y DESCONOCIDOS

            # 🔹 CALCULAR EL TOTAL DE CASOS POR AÑO **ANTES** DE FILTRAR POR MEDIDA
            total_cases_per_year = df.groupby("YEAR").size().reset_index(name="total_cases")

            # Asegurar que `total_cases_per_year` tenga TODOS los años posibles
            all_years = sorted(df["YEAR"].dropna().unique())
            total_cases_per_year = pd.DataFrame({"YEAR": all_years}).merge(total_cases_per_year, on="YEAR",
                                                                           how="left").fillna(0)

            # Convertir `total_cases_per_year` en diccionario para mapear valores
            total_cases_dict = total_cases_per_year.set_index("YEAR")["total_cases"].to_dict()

            # 🔹 CALCULAR DATOS CONOCIDOS Y DESCONOCIDOS PARA TORNILLOS
            screw_yearly_counts = df.groupby("YEAR")["b (screw length)"].count().reset_index(name="known_cases")
            screw_yearly_counts = pd.DataFrame({"YEAR": all_years}).merge(screw_yearly_counts, on="YEAR",
                                                                          how="left").fillna(0)

            # Obtener total de casos y calcular desconocidos
            screw_yearly_counts["total_cases"] = screw_yearly_counts["YEAR"].map(total_cases_dict)
            screw_yearly_counts["unknown_cases"] = screw_yearly_counts["total_cases"] - screw_yearly_counts[
                "known_cases"]
            screw_yearly_counts["unknown_cases"] = screw_yearly_counts["unknown_cases"].apply(
                lambda x: max(x, 0))  # Evitar negativos

            # Calcular porcentaje
            screw_yearly_counts["known_percentage"] = (screw_yearly_counts["known_cases"] / screw_yearly_counts[
                "total_cases"]) * 100
            screw_yearly_counts["unknown_percentage"] = 100 - screw_yearly_counts["known_percentage"]

            # 🔹 CALCULAR DATOS CONOCIDOS Y DESCONOCIDOS PARA PLACAS
            plate_yearly_counts = df.groupby("YEAR")["a (elevator plate)"].count().reset_index(name="known_cases")
            plate_yearly_counts = pd.DataFrame({"YEAR": all_years}).merge(plate_yearly_counts, on="YEAR",
                                                                          how="left").fillna(0)

            # Obtener total de casos y calcular desconocidos
            plate_yearly_counts["total_cases"] = plate_yearly_counts["YEAR"].map(total_cases_dict)
            plate_yearly_counts["unknown_cases"] = plate_yearly_counts["total_cases"] - plate_yearly_counts[
                "known_cases"]
            plate_yearly_counts["unknown_cases"] = plate_yearly_counts["unknown_cases"].apply(
                lambda x: max(x, 0))  # Evitar negativos

            # Calcular porcentaje
            plate_yearly_counts["known_percentage"] = (plate_yearly_counts["known_cases"] / plate_yearly_counts[
                "total_cases"]) * 100
            plate_yearly_counts["unknown_percentage"] = 100 - plate_yearly_counts["known_percentage"]

            # 🔹 GRAFICO BARRAS APILADAS - TORNILLOS
            fig_screw_bar = px.bar(
                screw_yearly_counts, x="YEAR", y=["known_percentage", "unknown_percentage"],
                labels={"value": "Porcentaje", "YEAR": "Año", "variable": "Datos"},
                title="Porcentaje de datos desconocidos en tornillos",
                color_discrete_map={"known_percentage": "#FF7F0E", "unknown_percentage": "gray"}
            )

            # Cambiar nombres de la leyenda
            fig_screw_bar.for_each_trace(
                lambda t: t.update(name="Datos Conocidos" if t.name == "known_percentage" else "Datos Desconocidos"))

            # Agregar etiquetas en las barras
            fig_screw_bar.update_traces(texttemplate="%{y:.1f}%", textposition="inside")

            st.plotly_chart(fig_screw_bar)

            # 🔹 GRAFICO BARRAS APILADAS - PLACAS
            fig_plate_bar = px.bar(
                plate_yearly_counts, x="YEAR", y=["known_percentage", "unknown_percentage"],
                labels={"value": "Porcentaje", "YEAR": "Año", "variable": "Datos"},
                title="Porcentaje de datos desconocidos en placas",
                color_discrete_map={"known_percentage": "#1F77B4", "unknown_percentage": "gray"}
            )

            # Cambiar nombres de la leyenda
            fig_plate_bar.for_each_trace(
                lambda t: t.update(name="Datos Conocidos" if t.name == "known_percentage" else "Datos Desconocidos"))

            # Agregar etiquetas en las barras
            fig_plate_bar.update_traces(texttemplate="%{y:.1f}%", textposition="inside")

            st.plotly_chart(fig_plate_bar)

    # Sección 2
    with tabs[1]:
        st.header("Análisis Comercial")
        st.write(
            "Sección dedidacada al análisis de tendencias de intervenciones por país, conversión de informes y tiempos de conversión.")



        # Evolución anual de los informes por país
        st.subheader("Evolución Anual del Número de Informes e Intervenciones por País")
        yearly_cases = df.groupby(["YEAR", "COUNTRY"]).size().reset_index(name="Número de Informes")
        fig1 = px.line(yearly_cases, x="YEAR", y="Número de Informes", color="COUNTRY",
                       title="Evolución de Informes por País", markers=True)

        fig1.update_layout(
            xaxis_title="Año",  #Nombre eje X
            xaxis=dict(tickmode="linear", dtick=1)  # Evitar decimales en el eje X
        )
        st.plotly_chart(fig1, use_container_width=True)



        # Evolución anual de las intervenciones por país

        yearly_surgery_cases = df_intervenciones.groupby(["YEAR", "COUNTRY"]).size().reset_index(name="Número de Intervenciones")
        fig1 = px.line(yearly_surgery_cases, x="YEAR", y="Número de Intervenciones", color="COUNTRY",
                       title="Evolución de Intervenciones por País", markers=True)

        fig1.update_layout(
            xaxis_title="Año",  # Nombre eje X
            xaxis=dict(tickmode="linear", dtick=1)  # Evitar decimales en el eje X
        )

        st.plotly_chart(fig1, use_container_width=True)


        # Comparación entre países
        st.subheader("Comparación de Número de Informes Totales vs Intervenciones entre Países. Tasa de Conversión")


        # Determinar título con los años seleccionados
        if "Todos" in selected_years or not selected_years:
            titulo_grafica = "Comparación de Casos por País (Todos los Años)"
        else:
            titulo_grafica = f"Comparación de Casos por País ({', '.join(map(str, selected_years))})"

        informes_generados = df.groupby("COUNTRY").size().reset_index(name="Informes Generados")
        intervenciones = df[df["Intervenciones"] == 1].groupby("COUNTRY")["Intervenciones"].count().reset_index()
        comparacion = pd.merge(informes_generados, intervenciones, on="COUNTRY", how="left").fillna(0)

        st.write(intervenciones)

        fig2 = px.bar(comparacion, x="COUNTRY", y=["Informes Generados", "Intervenciones"], barmode='group',
                      title=titulo_grafica)
        st.plotly_chart(fig2, use_container_width=True)

        # Tasa de conversión de informes a intervenciones
        informes_generados = df.shape[0]
        informes_convertidos = df["SURGERY DATE"].notna().sum()
        tasa_conversion = (informes_convertidos / informes_generados) * 100 if informes_generados > 0 else 0

        # Determinar título con los años seleccionados
        if "Todos" in selected_years or not selected_years:
            titulo_grafica2 = "Tasa de Conversión General (Todos los Años)"
        else:
            titulo_grafica2 = f"tasa de Conversión General ({', '.join(map(str, selected_years))})"

        st.metric(titulo_grafica2, f"{tasa_conversion:.2f}%")

        # Determinar título con los años seleccionados
        if "Todos" in selected_years or not selected_years:
            titulo_grafica3 = "Tasa de Conversión por País (Todos los Años)"
        else:
            titulo_grafica3 = f"tasa de Conversión por País ({', '.join(map(str, selected_years))})"


        # Calcular la tasa de conversión por país
        conversion_por_pais = df.groupby("COUNTRY")["SURGERY DATE"].count() / df.groupby("COUNTRY").size()
        # Resetear índice y renombrar columnas
        conversion_por_pais = conversion_por_pais.reset_index()
        conversion_por_pais.columns = ["País", "Tasa de Conversión"]
        # Filtrar países con tasa de conversión > 0
        conversion_por_pais = conversion_por_pais[conversion_por_pais["Tasa de Conversión"] > 0]
        # Crear gráfico de barras
        fig3 = px.bar(
            conversion_por_pais,
            x="País",
            y="Tasa de Conversión",
            title=titulo_grafica3,
            color="Tasa de Conversión",
            color_continuous_scale="Viridis"
        )
        # Mostrar
        st.plotly_chart(fig3, use_container_width=True)



        # Determinar título con los años seleccionados
        if "Todos" in selected_years or not selected_years:
            titulo_grafica4 = "Mapa de Calor de Intervenciones por País (Todos los Años)"
        else:
            titulo_grafica4 = f"Mapa de Calor de Intervenciones por País ({', '.join(map(str, selected_years))})"


        # Generar la matriz de datos para el heatmap
        matrix = df.pivot_table(values='Intervenciones', index='MONTHTAC', columns='COUNTRY', aggfunc='sum',
                                fill_value=0)
        # Filtrar países que tienen todas sus intervenciones = 0
        matrix = matrix.loc[:, (matrix != 0).any(axis=0)]  # Elimina columnas donde todos los valores son 0
        # Crear el mapa de calor con un tamaño más grande
        fig6 = px.imshow(
            matrix,
            labels={'x': 'País', 'y': 'Mes', 'color': 'Intervenciones'},
            title=titulo_grafica4,
            color_continuous_scale='YlOrRd'  # Colores más visibles
        )
        # Ajustar el tamaño del gráfico
        fig6.update_layout(
            width=1000,  # Aumenta el ancho en píxeles
            height=900,  # Aumenta la altura en píxeles
            margin=dict(l=10, r=10, t=50, b=50)  # Reduce márgenes
        )
        # Mostrar con ancho completo
        st.plotly_chart(fig6, use_container_width=True)



        # Tiempo de efectividad
        st.subheader("Distribución del Tiempo de Efectividad")

        # Distribución del tiempo entre la recepción del TAC y la intervención

        # Filtrar registros donde ambas fechas existen
        df_filtered = df.dropna(subset=["DATE", "SURGERY DATE"]).copy()

        # Calcular la diferencia en días
        df_filtered["Tiempo TAC a Intervención"] = (df_filtered["SURGERY DATE"] - df_filtered["DATE"]).dt.days

        df_sin_negativos = df_filtered[df_filtered[
                                           "Tiempo TAC a Intervención"] > 0]  # Filtramos informes con días negativos ya que son informes realizados después de la cirugía

        fig4 = px.histogram(df_sin_negativos, x="Tiempo TAC a Intervención",
                            title="Tiempo desde la Recepción del TAC hasta la Intervención",
                            color_discrete_sequence=["#636EFA"])

        fig4.update_traces(xbins=dict(size=15))  # 🔹 Cada barra representa 1 día

        st.plotly_chart(fig4, use_container_width=True)

        # Mostrar registros con días negativos
        dias_negativos = df_filtered[df_filtered["Tiempo TAC a Intervención"] < 0]
        if not dias_negativos.empty:
            st.subheader("Registros de Informes TAC Postquirúrgicos (Fecha Intervención - Fecha TAC < 0)")
            st.write(f"{dias_negativos.shape[0]} registros")
            st.dataframe(
                dias_negativos[["DATE", "SURGERY DATE", "Tiempo TAC a Intervención", "COUNTRY", "STATE NUMBER"]])

        # Tiempor TAC - Intervención por países

        # Verificar si hay datos para graficar
        if not df_sin_negativos.empty:

            fig5 = px.box(df_sin_negativos, x='COUNTRY', y='Tiempo TAC a Intervención',
                          title="Tiempo entre Recepción del TAC y la Intervención Por Países")
            st.plotly_chart(fig5)
        else:
            st.warning("No hay datos suficientes para calcular el tiempo entre TAC e intervención.")

    with tabs[2]:
        st.header("Análisis Técnico")
        st.write(
            "En esta sección se incluyen estudios sobre índice de Haller, asimetría, rotación esternal y correlaciones técnicas.")

        st.markdown("<br>", unsafe_allow_html=True)

        # Definir las columnas requeridas para el análisis técnico
        columnas_requeridas = [
            "INDICE€", "INDICE(D)", "d(Potencial Lifting Distance)MIN",
            "g (Haller Index)", "f (Assymetry Index)", "h (Correction Index)", "a (Sternal angle)", "Sternum Density",
            "Sternum Cortical Density (superior)", "Sternum Cortical Density (inferior)"
        ]

        # Verificar que todas las columnas requeridas estén en el DataFrame
        if not all(col in df.columns for col in columnas_requeridas):
            st.error(f"🚨 El archivo debe contener las columnas requeridas para el análisis: {columnas_requeridas}")
        else:
            # Renombrar columnas clave para facilitar el análisis
            df.rename(columns={
                "INDICE€": "Índice E",
                "INDICE(D)": "Índice D",
                "d(Potencial Lifting Distance)MIN": "Elevación Potencial",
                "g (Haller Index)": "Índice de Haller",
                "f (Assymetry Index)": "Índice de Asimetría",
                "a (Sternal angle)": "Rotación Esternal",
                "h (Correction Index)": "Índice de Corrección",
                "b(sternal Thickness)MIN": "Anchura del Esternón (mínima)",
                "MAX": "Anchura del Esternón (máxima)",
                "Sternum Density": "Densidad Esternal",
                "Sternum Cortical Density (superior)": "Densidad Cortical Esternal (superior)",
                "Sternum Cortical Density (inferior)": "Densidad Cortical Esternal (inferior)",
                "AGE": "Edad"
            }, inplace=True)

            # Distribución de variables anatómicas clave
            st.subheader("Distribución de Variables Anatómicas")
            variables_anatomicas = ["Índice de Haller", "Índice de Asimetría", "Índice de Corrección",
                         "Rotación Esternal", "Elevación Potencial", "Anchura del Esternón (mínima)", "Anchura del Esternón (máxima)", "Densidad Esternal", "Densidad Cortical Esternal (superior)",
                         "Densidad Cortical Esternal (inferior)"]
            selected_var = st.selectbox("Selecciona una variable para visualizar la distribución:", variables_anatomicas)

            fig_hist = px.histogram(df, x=selected_var, nbins=20, marginal="box",
                                    title=f"Distribución de {selected_var}")
            st.plotly_chart(fig_hist, use_container_width=True)

            # 📊 Estadísticas clave
            media = df[selected_var].mean()
            desviacion = df[selected_var].std()
            var_min = df[selected_var].min()
            var_max = df[selected_var].max()
            asimetria = skew(df[selected_var].dropna())
            curtosis_val = kurtosis(df[selected_var].dropna())

            # Mostrar estadísticas
            col1, col2, col3 = st.columns(3)
            col1.metric(f"📏 Media {selected_var}", f"{media:.2f}")
            col2.metric("📉 Desviación Estándar", f"{desviacion:.2f}")
            col3.metric("📈 Asimetría", f"{asimetria:.2f}")

            col4, col5, col6 = st.columns(3)
            col4.metric(f"🔼 Máximo {selected_var}", f"{var_max:.2f}")
            col5.metric(f"🔽 Mínimo {selected_var}", f"{var_min:.2f}")
            col6.metric("🔄 Curtosis", f"{curtosis_val:.2f}")
            st.write(
                f"·**Desviación Estándar**: mide cuánto varían los datos respecto a la media. Es decir, indica si los valores están muy dispersos o concentrados cerca del promedio. (**(cercana a 0)** → Datos muy agrupados alrededor de la media, poca variabilidad de {selected_var}., , **Alta** →  Datos muy dispersos respecto a la media, mayor variabilidad en {selected_var}")
            st.write(
                "·**Asimetría**: mide cuán simétrica es la distribución de los datos respecto a la media. ( ·**0** → Distribución simétrica, como la normal,    ·**Negativo (< 0)** → Sesgo a la izquierda (cola más larga a la izquierda, la distribución tiene más valores menores a la media),   ·**Positivo (> 0)** → Sesgo a la derecha (cola más larga a la derecha, la distribución tiene más valores mayores a la media)).")
            st.write(
                f"·**Curtosis**: mide si los datos tienen colas más o menos pesadas en comparación con una distribución normal. (**0 o cercano a 0** → Mesocúrtica (Distribución normal, colas estándar)., **Negativo (< 0)** → Platicúrtica (Colas ligeras, distribución más plana, datos más dispersos, sin valores extremos), **Positivo (> 0)** → Leptocúrtica (Colas pesadas, picos más pronunciados, es decir, muchos valores extremos, lo que sugiere casos atípicos (outliers))). ")

            st.markdown("<br>", unsafe_allow_html=True)

            # Evaluación de correlaciones
            st.subheader("Correlación entre Variables del TAC")


                # Análisis de impacto en la efectividad del implante

                # Calcular métricas de efectividad
            df["Índice E"] = df["Índice E"] - df["Índice D"]
            df["Efectividad"] = df["Índice E"] - df["Elevación Potencial"]

            st.markdown("<br>", unsafe_allow_html=True)

            st.markdown("#### **Efectividad**")

            st.markdown("""<br><br>
**DEFINICIÓN DE EFECTIVIDAD**
<br>

La **efectividad** del implante se define como:

<br>

***Efectividad = Indice de Corrección (cm) - Elevación Potencial***  

<br>

Donde:

**Índice de Corrección (cm)**: Representa la distancia a la que corresponde el valor porcentual del Índice de Corrección, el cual indica cuánto debería de elevarse el esternón para alcanzar la corrección esperada. Se calcula como la diferencia entre el Índice E y el Índice D, es decir:

<br>

***Índice de Corrección (cm) = Índice E - Índice D***  

<br>

**Elevación Potencial**: Representa la distancia teórica mínima que el implante puede elevar el esternón según el análisis de la anatomía del paciente a través del TAC.

<br><br>

**INTERPRETACIÓN**:

Un **valor de efectividad más bajo indica una mayor corrección lograda**, es decir, que la anatomía del paciente permite corregir adecuadamente el grado de hundimiento del esternón.  
Si la efectividad es alta (cercana a 0 o positiva), significa que la elevación esperada no alcanzó la distancia calculada a través del índice de corrección, lo que sugiere menor éxito en la intervención.

<br><br><br>
            """, unsafe_allow_html=True)



                   # Mapa de Calor con todas las Variables Anatómicas


            st.markdown("#### **Mapa de Calor: Correlaciones entre Variables Anatómicas, Medidas Placas/Tornillos, Edad y Efectividad**")


            variables_interes = ['Índice de Asimetría', 'Índice de Haller', 'Índice de Corrección', 'Rotación Esternal',
                         'Densidad Esternal','Densidad Cortical Esternal (superior)', 'Densidad Cortical Esternal (inferior)',
                         'b (screw length)', 'a (elevator plate)', 'Anchura del Esternón (mínima)',
                         'Anchura del Esternón (máxima)','Elevación Potencial', 'Edad', 'Efectividad']
            df_correlacion = df[variables_interes].apply(pd.to_numeric, errors='coerce')
            correlaciones_anatomicas = df_correlacion.corr()

            if not correlaciones_anatomicas.empty:
                fig, ax = plt.subplots(figsize=(12, 8))
                sns.heatmap(correlaciones_anatomicas, annot=True, cmap='coolwarm', fmt='.2f', ax=ax)
                plt.title('Mapa de Calor: Relación entre Variables de Interés')
                st.pyplot(fig)
                st.write(
                    "**INTERPRETACIÓN:** "
                    "Este mapa de calor muestra las correlaciones entre diferentes variables anatómicas, medidas de tornillos y placas, edad y efectividad. ")
                st.write(
                    "Los valores cercanos a **1 o -1** indican una relación fuerte entre dos variables. Un valor positivo sugiere que ambas aumentan juntas, mientras que un valor negativo indica que cuando una sube, la otra baja. Valores cercanos a 0 indican poca o ninguna relación. Esto permite identificar patrones anatómicos que podrían estar asociados a incidencias.")
                # Mostrar información sobre la escala de correlación de Taylor (1990)
                st.markdown("""
                **📊 Interpretación de la correlación de Pearson según Taylor (1990)**

                Esta escala se utiliza en **medicina y diagnóstico por imágenes**, donde las correlaciones suelen ser más bajas debido a la variabilidad natural de los datos clínicos.

                | **Valor de r**  | **Interpretación** |
                |---------------|----------------|
                | **0.00 - 0.19**  | 🔵 Muy débil |
                | **0.20 - 0.39**  | 🟢 Débil |
                | **0.40 - 0.59**  | 🟡 Moderada |
                | **0.60 - 0.79**  | 🟠 Fuerte |
                | **0.80 - 1.00**  | 🔴 Muy fuerte |

                📖 **Fuente:**  
                Taylor, R. (1990). *Interpretation of the correlation coefficient: A basic review.*  
                📄 *Journal of Diagnostic Medical Sonography, 6(1), 35-39.*  
                🔗 [DOI: 10.1177/875647939000600106](https://doi.org/10.1177/875647939000600106)
                """, unsafe_allow_html=True)

            else:
                st.warning(
                    "No hay suficientes datos numéricos para generar el mapa de calor de correlaciones anatómicas.")


                   # Visualización de correlaciones de interés

            st.markdown("#### Visualización de correlaciones de interés")

            correlation_pairs = [("Índice de Haller", "Elevación Potencial"),
                                 ("Índice de Asimetría", "Rotación Esternal"),
                                 ("Densidad Esternal", "Edad"),
                                 ("Efectividad", "Índice de Haller"),
                                 ("Efectividad", "Rotación Esternal")]

            selected_pair = st.selectbox("Selecciona dos variables para evaluar su correlación:", correlation_pairs)

            selected_x = selected_pair[0].strip()
            selected_y = selected_pair[1].strip()

            df_corr = df_correlacion[[selected_x, selected_y]].dropna()


            if len(df_filtered) > 1:
                correlation, p_value = pearsonr(df_corr[selected_x], df_corr[selected_y])

                # 🔹 Interpretación según Taylor (1990)
                if abs(correlation) >= 0.80:
                    interpretation = "🟢 **Muy fuerte**"
                elif abs(correlation) >= 0.60:
                    interpretation = "🟢 **Fuerte**"
                elif abs(correlation) >= 0.40:
                    interpretation = "🔵 **Moderada**"
                elif abs(correlation) >= 0.20:
                    interpretation = "🟡 **Débil**"
                else:
                    interpretation = "🔴 **Muy débil**"


                # Crear gráfico de dispersión
                fig_scatter = px.scatter(
                    df_corr, x=selected_x, y=selected_y, trendline="ols",
                    title=f"Correlación entre {selected_x} y {selected_y}"
                )
                st.plotly_chart(fig_scatter, use_container_width=True)


                # Mensaje con la interpretación de la correlación
                if abs(correlation) >= 0.80:
                    st.success(
                        f"✅ **Muy fuerte:** La correlación entre **{selected_x}** y **{selected_y}** es de **{correlation:.2f}**. "
                        "Existe una asociación muy alta entre estas variables, lo que indica que una puede predecir la otra con gran precisión.")

                elif abs(correlation) >= 0.60:
                    st.success(
                        f"✅ **Fuerte:** La correlación entre **{selected_x}** y **{selected_y}** es de **{correlation:.2f}**. "
                        "Las variables están fuertemente relacionadas, aunque pueden existir otros factores que influyan en la variabilidad.")

                elif abs(correlation) >= 0.40:
                    st.info(
                        f"🔵 **Moderada:** La correlación entre **{selected_x}** y **{selected_y}** es de **{correlation:.2f}**. "
                        "Existe una relación clara entre las variables, pero también pueden intervenir otros factores.")

                elif abs(correlation) >= 0.20:
                    st.warning(
                        f"🟡 **Débil:** La correlación entre **{selected_x}** y **{selected_y}** es de **{correlation:.2f}**. "
                        "Hay una relación leve, pero no lo suficientemente fuerte como para ser un predictor fiable.")

                else:
                    st.error(
                        f"❌ **Muy débil:** La correlación entre **{selected_x}** y **{selected_y}** es de **{correlation:.2f}**. "
                        "No hay evidencia de una relación significativa entre las variables.")

            else:
                st.error("❌ No hay suficientes datos para calcular la correlación.")



    with tabs[3]:
        st.header("Análisis de Incidencias")
        st.write(
            "En esta sección se analizan las incidencias relacionadas con la sujeción de los tornillos intraplacas y otros problemas detectados.")

        df['Fila Roja'] = df.apply(contiene_palabra_clave, axis=1)

        # Streamlit UI

        st.subheader("Incidencias Intraoperatorias")

        # Filtro para mostrar solo incidencias intraoperatorias
        df_incidencias_intraoperatorias = df[
            ((df['COMPLICATIONS INTRAOPERATORY'].notna()) & (df['COMPLICATIONS INTRAOPERATORY'] != 'NO INCIDENCIAS')) |
            (df['RESULT'] == 'NO OK')
            ]

        st.write(f"**Número de incidencias intraoperatorias detectadas**: {len(df_incidencias_intraoperatorias)}")
        st.dataframe(df_incidencias_intraoperatorias)



        # Frecuencia de Incidencias Intraoperatorias
        st.write("#### 📊 Frecuencia de Incidencias Intraoperatorias")

        # Contar incidencias
        frecuencia_incidencias = df_incidencias_intraoperatorias[
            'COMPLICATIONS INTRAOPERATORY'].value_counts().reset_index()
        frecuencia_incidencias.columns = ['Tipo de Incidencia', 'Frecuencia']

        # Verificar si hay datos
        if not frecuencia_incidencias.empty:
            # Crear gráfico interactivo con Plotly
            fig = px.bar(
                frecuencia_incidencias,
                x='Tipo de Incidencia',
                y='Frecuencia',
                title="Distribución de Incidencias Intraoperatorias",
                labels={'Frecuencia': 'Número de Casos'},
                color='Frecuencia',
                color_continuous_scale='Blues',
                text_auto=True
            )

            # Mejorar interactividad
            fig.update_layout(
                xaxis=dict(tickangle=45),  # Rotar etiquetas del eje X
                yaxis_title="Frecuencia",
                xaxis_title="Tipo de Incidencia",
                template="plotly_white",  # Tema limpio y profesional
            )

            # Mostrar en Streamlit
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ No hay incidencias suficientes para analizar.")

        # Filtro de incidencias en el follow-up
        st.subheader("Incidencias Follow-Up")
        df_incidencias_follow_up = df[
            ((df['DIAGNOSIS 1'].notna()) & (df['DIAGNOSIS 1'] != 'OK') & ~df['DIAGNOSIS 1'].str.contains('NO SINTOMAS',
                                                                                                         na=False,
                                                                                                         case=False)) |
            ((df['DIAGNOSIS 2'].notna()) & (df['DIAGNOSIS 2'] != 'OK') & ~df['DIAGNOSIS 2'].str.contains('NO SINTOMAS',
                                                                                                         na=False,
                                                                                                         case=False)) |
            ((df['OBSERVATIONS 1'].notna()) & ~df['OBSERVATIONS 1'].str.contains('content', na=False, case=False) & ~df[
                'OBSERVATIONS 1'].str.contains('molt bè', na=False, case=False)) |
            ((df['OBSERVATIOS 2'].notna()) & ~df['OBSERVATIOS 2'].str.contains('Retirada de la placa', na=False,
                                                                               case=False) & ~df[
                'OBSERVATIOS 2'].str.contains('no ha presentado mas sintomas', na=False, case=False))]

        st.write(f"**Número de incidencias durante el follow-up**: {len(df_incidencias_follow_up)}")
        st.dataframe(df_incidencias_follow_up)

        # Filtro de incidencias en la explantación
        st.subheader("Incidencias Explantación")
        df_incidencias_explantacion = df[
            ((df['OBSERVATIONS2'].notna()) & ~df['OBSERVATIONS2'].str.contains('successful', na=False, case=False)) |
            df['COMPLICATIONS'].notna() |
            ((df['REMOVAL REASON'].notna()) & ~df['REMOVAL REASON'].str.contains('time for removal has been completed',
                                                                                 na=False, case=False))
            ]
        st.write(f"**Número de incidencias durante la explantación**: {len(df_incidencias_explantacion)}")
        st.dataframe(df_incidencias_explantacion)

        st.subheader("Incidencias Totales")

        # Concatenar los DataFrames y eliminar duplicados
        df_incidencias = pd.concat(
            [df_incidencias_intraoperatorias, df_incidencias_follow_up, df_incidencias_explantacion]).drop_duplicates()

        # Contar el número total de incidencias
        total_incidencias = len(df_incidencias)

        # Contar incidencias en cada momento
        incidencias_por_momento = {
            "Intraoperatorias": len(df_incidencias_intraoperatorias),
            "Follow-up": len(df_incidencias_follow_up),
            "Explantación": len(df_incidencias_explantacion),
        }

        # Convertir a DataFrame
        df_incidencias_momento = pd.DataFrame(list(incidencias_por_momento.items()), columns=["Momento", "Cantidad"])

        # Calcular porcentaje
        df_incidencias_momento["Porcentaje"] = (df_incidencias_momento["Cantidad"] / total_incidencias) * 100


        st.write(f"**Total de incidencias únicas:** {total_incidencias}")
        st.dataframe(df_incidencias_momento)

        # Gráfico pastel mostrando porcentaje de incidencias según cuando han sucedido
        st.subheader("Porcentaje de Incidencias por Momento")

        # Definir una paleta de colores según el momento de la incidencia
        color_map = {
            "Intraoperatorio": "#FF5733",  # Rojo intenso
            "Follow-up": "#FFC300",  # Amarillo
            "Explantación": "#C70039"  # Rojo oscuro
        }

        # Crear gráfico de pastel interactivo con Plotly
        fig = px.pie(df_incidencias_momento,
                     names="Momento",
                     values="Cantidad",
                     title="Distribución de Incidencias",
                     color="Momento",  # Asigna colores personalizados
                     color_discrete_map=color_map,
                     hole=0.3  # Hace que el gráfico sea tipo "donut"
                     )

        # Personalizar etiquetas y formato
        fig.update_traces(textinfo='percent+label',
                          pull=[0.05] * len(df_incidencias_momento))  # Separa ligeramente los segmentos

        # Mostrar en Streamlit
        st.plotly_chart(fig)

        # Análisis de pacientes con incidencias en rojo
        st.subheader("🟥 Pacientes con Incidencias en Rojo vs. Base de Datos Completa")
        st.write("Pacientes con incidencias marcadas en rojo en el Excel:")
        st.dataframe(df[df['Fila Roja']])

        df_rojo = df[df['Fila Roja']]
        df_normal = df[~df['Fila Roja']]

        # Convertir a numérico, forzando errores a NaN
        df_rojo[variables_interes] = df_rojo[variables_interes].apply(pd.to_numeric, errors='coerce')
        df_normal[variables_interes] = df_normal[variables_interes].apply(pd.to_numeric, errors='coerce')

        # Calcular medias
        medias_rojo = df_rojo[variables_interes].mean()
        medias_total = df_normal[variables_interes].mean()

        # Prueba estadística (t-test)
        p_values = [ttest_ind(df_rojo[var].dropna(), df_normal[var].dropna(), equal_var=False).pvalue for var in
                    variables_interes]

        # Construcción del DataFrame comparativo
        df_comparacion = pd.DataFrame({"Variable": variables_interes,
                                       "Media Incidencias en Rojo": medias_rojo,
                                       "Media General": medias_total,
                                       "P-valor": p_values})


        # Resaltar diferencias significativas
        def highlight_significant(val):
            return 'background-color: red; color: white' if val < 0.05 else ''


        # Resaltar diferencias significativas
        def highlight_significant(val):
            if val < 0.05:
                return 'background-color: darkred; color: white'
            elif val < 0.45:
                return 'background-color: #B7410E; color: white'
            elif val < 0.65:
                return 'background-color: orange; color: black'
            elif val > 0.85:
                return 'background-color: green; color: black'
            return ''

        st.write("📊 Comparación de medidas entre incidencias en rojo y la base de datos completa:")
        st.dataframe(df_comparacion.style.applymap(highlight_significant, subset=['P-valor']))

        # Gráfico de diferencias
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_comparacion["Variable"], y=df_comparacion["Media Incidencias en Rojo"],
                             name="Media Incidencias en Rojo", marker_color='red'))
        fig.add_trace(go.Bar(x=df_comparacion["Variable"], y=df_comparacion["Media General"],
                             name="Media General", marker_color='blue'))
        fig.update_layout(title="Comparación de Medias entre Pacientes con Incidencias en Rojo y el Resto",
                          xaxis_title="Variable", yaxis_title="Valor Medio", barmode='group')
        st.plotly_chart(fig)

        st.success("✅ Análisis completado. Explora las visualizaciones interactivas y obtén insights en tiempo real.")

    with tabs[4]:
        st.header("Exploración Adicional")
        st.write("Sección abierta para explorar nuevos patrones y análisis adicionales avanzados.")
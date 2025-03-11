import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import skew, kurtosis, ttest_ind


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

        # Número de casos totales
        num_filas = df.shape[0]
        st.write(f"Número de casos totales: **{num_filas}**")

        df["YEAR"] = pd.to_datetime(df["DATE"], errors='coerce').dt.year

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
                         title="Distribución de Casos Totales por Estado",
                         labels={"names": "STATE NUMBER"})
        st.plotly_chart(fig_pie)

        # Estado de los casos según año

        # Crear DataFrame agrupado correctamente
        sunburst_data = df.groupby(["YEAR", "STATE NUMBER"]).size().reset_index(name="Casos")

        fig_sunburst = px.sunburst(sunburst_data, path=["YEAR", "STATE NUMBER"], values="Casos",
                                   title="Distribución de Casos por Año y Estado")
        # Agregar porcentaje a las etiquetas
        fig_sunburst.update_traces(textinfo="label+percent entry")

        st.plotly_chart(fig_sunburst)

        # 🔹 Evolución de los casos totales
        st.subheader("Evolución de los Casos por Año")

        # Asegurar que la columna DATE existe y convertirla a formato de año
        if "DATE" in df.columns:
            df["YEAR"] = pd.to_datetime(df["DATE"], errors="coerce").dt.year
        else:
            st.error("La columna 'DATE' no se encuentra en el DataFrame.")

        # Contar casos por año
        yearly_counts = df.groupby("YEAR").size().reset_index(name="Casos")

        # Calcular el total de casos en todos los años
        total_cases = yearly_counts["Casos"].sum()

        # Calcular porcentaje respecto al total de TODOS los casos
        yearly_counts["percentage"] = (yearly_counts["Casos"] / total_cases) * 100  # ✅ CORREGIDO

        # Crear gráfico de línea
        fig2 = px.line(yearly_counts, x="YEAR", y="Casos", markers=True, title="Evolución de Casos por Año")

        ###################### MODIFICAR. Está ajustada la ultima flecha a los datos que hay actualmente en la BBDD para que no pise la linea

        # Añadir anotaciones en los puntos (número de casos y porcentaje)
        for i, row in yearly_counts.iterrows():
            if i == len(yearly_counts) - 1:  # Si es la última anotación
                fig2.add_annotation(
                    x=row["YEAR"], y=row["Casos"],  # Punto final (donde apunta la flecha)
                    ax=row["YEAR"] + 0.1, ay=row["Casos"] + 25,  # 🔹 Mueve el inicio 1 año a la derecha
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
            xaxis=dict(tickmode="linear", dtick=1)  # ✅ Evita decimales en el eje X
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

            # Gráficos de tornillos y placas
            fig5 = px.bar(screw_counts, x=screw_counts.index, y=screw_counts.values,
                          title="Frecuencia de Medidas de Tornillos")

            fig6 = px.bar(plate_counts, x=plate_counts.index, y=plate_counts.values,
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
            "Sección dedidacada al análisis de tendencias de intervenciones por país, efectividad de informes y tiempos de efectividad.")

        # Convertir columnas de fecha
        df["DATE"] = pd.to_datetime(df["DATE"], errors='coerce')
        df["SURGERY DATE"] = pd.to_datetime(df["SURGERY DATE"], errors='coerce')
        df["MONTHTAC"] = df["DATE"].dt.to_period("M").astype(str)

        # Filtrar Países
        st.sidebar.header("Filtros")
        country_options = ["Todos"] + list(df["COUNTRY"].unique())
        selected_countries = st.sidebar.multiselect("Selecciona países", country_options, default="Todos")

        if "Todos" not in selected_countries:
            df = df[df["COUNTRY"].isin(selected_countries)]

        # Evolución anual de los informes por país
        st.subheader("Evolución Anual del Número de Informes por País")
        yearly_cases = df.groupby(["YEAR", "COUNTRY"]).size().reset_index(name="Número de Informes")
        fig1 = px.line(yearly_cases, x="YEAR", y="Número de Informes", color="COUNTRY",
                       title="Evolución de Informes por País", markers=True)

        fig1.update_layout(
            xaxis_title="Año"  # Nombre del eje Y
        )
        st.plotly_chart(fig1, use_container_width=True)

        # Comparación entre países
        st.subheader("Comparación de Número de Informes e Intervenciones entre Países. Tasa de Conversión")

        # Selector de años
        años_disponibles = sorted(df["YEAR"].dropna().unique())
        años_disponibles.insert(0, "Todos")  # Agregar opción "Todos"

        año_seleccionado = st.multiselect("Selecciona el año", options=años_disponibles, default="Todos")

        # Filtrar por años seleccionados
        df_filtrado = df if "Todos" in año_seleccionado or not año_seleccionado else df[
            df["YEAR"].isin(año_seleccionado)]

        # Determinar título con los años seleccionados
        if "Todos" in año_seleccionado or not año_seleccionado:
            titulo_grafica = "Comparación de Casos por País (Todos los Años)"
        else:
            titulo_grafica = f"Comparación de Casos por País ({', '.join(map(str, año_seleccionado))})"

        informes_generados = df_filtrado.groupby("COUNTRY").size().reset_index(name="Informes Generados")
        df_filtrado["Intervenciones"] = df_filtrado["SURGERY DATE"].notna().astype(int)
        intervenciones = df_filtrado[df_filtrado["Intervenciones"] == 1].groupby("COUNTRY")[
            "Intervenciones"].count().reset_index()
        comparacion = pd.merge(informes_generados, intervenciones, on="COUNTRY", how="left").fillna(0)

        fig2 = px.bar(comparacion, x="COUNTRY", y=["Informes Generados", "Intervenciones"], barmode='group',
                      title=titulo_grafica)
        st.plotly_chart(fig2, use_container_width=True)

        # Tasa de conversión de informes a intervenciones
        st.subheader("Tasa de Conversión de Informes a Intervenciones")
        informes_generados = df_filtrado.shape[0]
        informes_convertidos = df_filtrado["SURGERY DATE"].notna().sum()
        tasa_conversion = (informes_convertidos / informes_generados) * 100 if informes_generados > 0 else 0

        # Determinar título con los años seleccionados
        if "Todos" in año_seleccionado or not año_seleccionado:
            titulo_grafica2 = "Tasa de Conversión General (Todos los Años)"
        else:
            titulo_grafica2 = f"tasa de Conversión General ({', '.join(map(str, año_seleccionado))})"

        st.metric(titulo_grafica2, f"{tasa_conversion:.2f}%")

        # Determinar título con los años seleccionados
        if "Todos" in año_seleccionado or not año_seleccionado:
            titulo_grafica3 = "Tasa de Conversión por País (Todos los Años)"
        else:
            titulo_grafica3 = f"tasa de Conversión por País ({', '.join(map(str, año_seleccionado))})"

        # Comparación de efectividad por país
        conversion_por_pais = df_filtrado.groupby("COUNTRY")["SURGERY DATE"].count() / df_filtrado.groupby(
            "COUNTRY").size()
        conversion_por_pais = conversion_por_pais.reset_index()
        conversion_por_pais.columns = ["País", "Tasa de Conversión"]
        fig3 = px.bar(conversion_por_pais, x="País", y="Tasa de Conversión", title=titulo_grafica3,
                      color="Tasa de Conversión", color_continuous_scale="Viridis")
        st.plotly_chart(fig3, use_container_width=True)

        # Determinar título con los años seleccionados
        if "Todos" in año_seleccionado or not año_seleccionado:
            titulo_grafica4 = "Mapa de Calor de Intervenciones por País (Todos los Años)"
        else:
            titulo_grafica4 = f"Mapa de Calor de Intervenciones por País ({', '.join(map(str, año_seleccionado))})"

        # Mapa de calor
        matrix = df.pivot_table(values='Intervenciones', index='MONTHTAC', columns='COUNTRY', aggfunc='sum',
                                fill_value=0)
        fig6 = px.imshow(matrix, labels={'x': 'País', 'y': 'Mes', 'color': 'Intervenciones'},
                         title=titulo_grafica4)
        st.plotly_chart(fig6)

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
                "Sternum Cortical Density (inferior)": "Densidad Cortical Esternal (inferior)"
            }, inplace=True)

            # Distribución de variables anatómicas clave
            st.subheader("Distribución de Variables Anatómicas")
            variables = ["Índice de Haller", "Índice de Asimetría", "Índice E",
                         "Rotación Esternal", "Densidad Esternal", "Densidad Cortical Esternal (superior)",
                         "Densidad Cortical Esternal (inferior)"]
            selected_var = st.selectbox("Selecciona una variable para visualizar la distribución:", variables)

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
            st.write(df[df["Densidad Cortical Esternal (superior)"] > 3000])
            correlation_pairs = [("Índice de Haller", "Elevación Potencial"),
                                 ("Índice de Asimetría", "Rotación Esternal"),
                                 ("Rotación Esternal", "Efectividad")]
            selected_pair = st.selectbox("Selecciona dos variables para evaluar su correlación:", correlation_pairs)

            fig_scatter = px.scatter(df, x=selected_pair[0], y=selected_pair[1], trendline="ols",
                                     title=f"Correlación entre {selected_pair[0]} y {selected_pair[1]}")
            st.plotly_chart(fig_scatter, use_container_width=True)

            # Análisis de impacto en la efectividad del implante

            # Calcular métricas de efectividad
            df["Índice E"] = df["Índice E"] - df["Índice D"]
            df["Efectividad"] = df["Índice E"] - df["Elevación Potencial"]

            st.markdown("<br>", unsafe_allow_html=True)

            st.subheader("Impacto de Parámetros Anatómicos en la Efectividad del Implante")

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

Un valor de efectividad más bajo indica una mayor corrección lograda, es decir, que la anatomía del paciente permite corregir mejor la deformidad del esternón.  
Si la efectividad es alta (cercana a 0 o positiva), significa que la elevación esperada no alcanzó la distancia calculada a través del índice de Haller, lo que sugiere menor éxito en la intervención.

<br><br><br>
            """, unsafe_allow_html=True)

            impacto_var = st.selectbox("Selecciona una variable para analizar su impacto en la efectividad:",
                                       ["Índice de Haller", "Índice de Asimetría", "Rotación Esternal"])

            fig_impact = px.scatter(df, x=impacto_var, y="Efectividad", trendline="ols",
                                    title=f"Impacto de {impacto_var} en la Efectividad del Implante")
            st.plotly_chart(fig_impact, use_container_width=True)

            # Mapa de Calor con todas las Variables Anatómicas

            st.write(
                "**Mapa de Calor: Correlaciones entre Variables Anatómicas, Medidas Placas/Tornillos y Efectividad**")
            variables = ['Índice de Asimetría', 'Índice de Haller', 'Índice de Corrección', 'Índice E',
                         'Densidad Esternal',
                         'Densidad Cortical Esternal (superior)', 'Densidad Cortical Esternal (inferior)',
                         'b (screw length)', 'a (elevator plate)', 'Anchura del Esternón (mínima)',
                         'Anchura del Esternón (máxima)', 'Efectividad']
            df_anatomico = df[variables].apply(pd.to_numeric, errors='coerce')
            correlaciones_anatomicas = df_anatomico.corr()

            if not correlaciones_anatomicas.empty:
                fig, ax = plt.subplots(figsize=(12, 8))
                sns.heatmap(correlaciones_anatomicas, annot=True, cmap='coolwarm', fmt='.2f', ax=ax)
                plt.title('Mapa de Calor: Relación entre Variables Anatómicas')
                st.pyplot(fig)
                st.write(
                    "**Interpretación:** Este mapa de calor muestra las correlaciones entre diferentes variables anatómicas, medidas de tornillos y placas y efectividad. ")
                st.write(
                    "Los valores cercanos a **1 o -1** indican una relación fuerte entre dos variables. Un valor positivo sugiere que ambas aumentan juntas, mientras que un valor negativo indica que cuando una sube, la otra baja. Valores cercanos a 0 indican poca o ninguna relación. Esto permite identificar patrones anatómicos que podrían estar asociados a incidencias.")
            else:
                st.warning(
                    "No hay suficientes datos numéricos para generar el mapa de calor de correlaciones anatómicas.")

    with tabs[3]:
        st.header("Incidencias")
        st.write(
            "En esta sección se analizan las incidencias relacionadas con la sujeción de los tornillos intraplacas y otros problemas detectados.")

        df['Fila Roja'] = df.apply(contiene_palabra_clave, axis=1)

        # Streamlit UI
        st.title("Análisis de Incidencias en la Sujeción de Tornillos")

        st.subheader("Incidencias Intraoperatorias")

        # Filtro para mostrar solo incidencias intraoperatorias
        df_incidencias_intraoperatorias = df[
            ((df['COMPLICATIONS INTRAOPERATORY'].notna()) & (df['COMPLICATIONS INTRAOPERATORY'] != 'NO INCIDENCIAS')) |
            (df['RESULT'] == 'NO OK')
            ]

        st.write(f"**Número de incidencias intraoperatorias detectadas**: {len(df_incidencias_intraoperatorias)}")
        st.dataframe(df_incidencias_intraoperatorias)

        # Frecuencia de Incidencias
        st.write("**Frecuencia de Incidencias Intraoperatorias**")
        frecuencia_incidencias = df_incidencias_intraoperatorias['COMPLICATIONS INTRAOPERATORY'].value_counts()
        if not frecuencia_incidencias.empty:
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.countplot(data=df_incidencias_intraoperatorias, x='COMPLICATIONS INTRAOPERATORY',
                          order=frecuencia_incidencias.index,
                          ax=ax)
            plt.xticks(rotation=45)
            plt.xlabel('Tipo de Incidencia')
            plt.ylabel('Frecuencia')
            plt.title('Distribución de Incidencias')
            st.pyplot(fig)
        else:
            st.warning("No hay incidencias suficientes para analizar.")

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

        # Mostrar en Streamlit
        st.header("Análisis de Incidencias en Distintos Momentos")
        st.write(f"**Total de incidencias únicas:** {total_incidencias}")
        st.dataframe(df_incidencias_momento)

        # Crear gráfico de pastel
        st.subheader("Porcentaje de Incidencias por Momento")
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.pie(df_incidencias_momento["Cantidad"], labels=df_incidencias_momento["Momento"], autopct='%1.1f%%',
               colors=["#ff9999", "#66b3ff", "#99ff99"])
        ax.set_title("Distribución de Incidencias")
        st.pyplot(fig)

        # Análisis de correlaciones con medidas anatómicas
        st.subheader("Correlaciones con Factores Anatómicos de los Registros con Indicencias")
        variables_medidas = ['b (screw length)', 'a (elevator plate)', 'Anchura del Esternón (mínima)',
                             'Anchura del Esternón (máxima)',
                             'Índice de Haller', 'Índice de Asimetría', 'Índice E',
                             'Rotación Esternal', 'Densidad Esternal', 'Densidad Cortical Esternal (superior)',
                             'Densidad Cortical Esternal (inferior)']

        df_incidencias[variables_medidas] = df_incidencias[variables_medidas].apply(
            pd.to_numeric, errors='coerce')
        correlaciones = df_incidencias[variables_medidas].corr()

        if not correlaciones.empty:
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.heatmap(correlaciones, annot=True, cmap='coolwarm', fmt='.2f', ax=ax)
            plt.title('Mapa de Calor: Correlaciones entre Incidencias y Medidas Anatómicas/del Implante')
            st.pyplot(fig)
        else:
            st.warning("No hay datos suficientes para calcular correlaciones.")




        # Test Estadístico (t-test)
        grupo_con_incidencia = df[df['RESULT'] == 'NO OK'][
            variables_medidas]
        grupo_sin_incidencia = df_[df['RESULT'] == 'OK'][
            variables_medidas]

        t_stat, p_value = ttest_ind(grupo_con_incidencia, grupo_sin_incidencia, equal_var=False)

        st.subheader("Resultados del Test t")
        st.write(f"**Valor p:** {p_value:.4f}")

        if p_value < 0.05:
            st.success(
                "La diferencia entre los grupos es estadísticamente significativa (p < 0.05), lo que sugiere que esta variable podría estar relacionada con las incidencias.")
        else:
            st.warning(
                "No se encontró una diferencia significativa entre los grupos (p > 0.05), lo que sugiere que esta variable no tiene un impacto claro en las incidencias.")

        # Análisis de pacientes con incidencias en rojo
        st.subheader("Análisis de Pacientes con Incidencias en Rojo")
        if not df[df['Fila Roja']].empty:
            st.write("Pacientes con incidencias marcadas en rojo en el Excel:")
            st.dataframe(df[df['Fila Roja']])
        else:
            st.warning("No se encontraron pacientes con filas en rojo en el Excel.")

        st.success("Análisis completado. Explora los gráficos y datos interactivos.")

    with tabs[4]:
        st.header("Exploración Adicional")
        st.write("Sección abierta para nuevas correlaciones, patrones y análisis adicionales.")
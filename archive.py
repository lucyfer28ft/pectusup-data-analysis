# Análisis de impacto de variables anatómicas en incidencias ( no está bien programado habría que darle vuelta y no sé si tiene sentido en verdad, no lo veo relevante por ahora)

variable_seleccionada = st.multiselect("Elige una variable anatómica:", options=variables_medidas)

st.subheader(f"Relación entre {variable_seleccionada} e Incidencias")
plt.figure(figsize=(8, 6))
sns.boxplot(x=df_incidencias["RESULT"],
            y=df_incidencias[variable_seleccionada])
plt.xlabel("Hubo incidencia (NO OK / OK)")
plt.ylabel(variable_seleccionada)
plt.title(f"Relación entre {variable_seleccionada} e Incidencias")
st.pyplot(plt)










# Test Estadístico (t-test) ( No tiene sentido, darle vuelta si tal pero no tan relevante para dedicarle el tiempo por ahora)
grupo_con_incidencia = df[df['RESULT'] == 'NO OK'][
    variables_medidas]
grupo_sin_incidencia = df[df['RESULT'] == 'OK'][
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













# Análisis de correlaciones con medidas anatómicas (No sé si tiene sentido, darle vuelta)
st.subheader("Correlaciones con Factores Anatómicos de los Registros con Indicencias")
variables_interes = ['b (screw length)', 'a (elevator plate)', 'Anchura del Esternón (mínima)',
                     'Anchura del Esternón (máxima)',
                     'Índice de Haller', 'Índice de Asimetría', 'Índice de Corrección',
                     'Rotación Esternal', 'Densidad Esternal', 'Densidad Cortical Esternal (superior)',
                     'Densidad Cortical Esternal (inferior)', ]

df_incidencias[variables_interes] = df_incidencias[variables_interes].apply(
    pd.to_numeric, errors='coerce')
correlaciones = df_incidencias[variables_interes].corr()

if not correlaciones.empty:
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(correlaciones, annot=True, cmap='coolwarm', fmt='.2f', ax=ax)
    plt.title('Mapa de Calor: Correlaciones entre Incidencias y Medidas Anatómicas/del Implante')
    st.pyplot(fig)
else:
    st.warning("No hay datos suficientes para calcular correlaciones.")

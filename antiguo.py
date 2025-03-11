# Análisis de impacto de variables anatómicas en incidencias

variable_seleccionada = st.multiselect("Elige una variable anatómica:", options=variables_medidas)

st.subheader(f"Relación entre {variable_seleccionada} e Incidencias")
plt.figure(figsize=(8, 6))
sns.boxplot(x=df_incidencias["RESULT"],
            y=df_incidencias[variable_seleccionada])
plt.xlabel("Hubo incidencia (NO OK / OK)")
plt.ylabel(variable_seleccionada)
plt.title(f"Relación entre {variable_seleccionada} e Incidencias")
st.pyplot(plt)

# Test Estadístico (t-test)
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

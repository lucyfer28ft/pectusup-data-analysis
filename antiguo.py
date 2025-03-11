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
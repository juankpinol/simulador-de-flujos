import streamlit as st
import pandas as pd

st.set_page_config(page_title="Proyector de Flujos", layout="wide")

st.title("Proyector de flujos con plazos y tasas variables")

st.markdown(
    """
    Esta herramienta permite proyectar un flujo mensual de ahorro/inversión:

    - monto mensual
    - plazo en meses
    - tasa anual esperada
    - aporte inicial
    """
)

with st.expander("Ver desarrollo de las fórmulas matemáticas"):
    st.markdown("### 1. Tasa Anual Neta (Aplicación del Costo)")
    st.markdown(
        """
        En este modelo, el **Costo de Administración** anual se descuenta directamente de la expectativa de rentabilidad 
        antes de realizar cualquier proyección. De esta manera, el simulador opera con una rentabilidad "limpia".
        """
    )
    st.latex(r"Tasa_{anual\_neta} = Tasa_{anual\_esperada} - Costo_{administracion}")
    
    st.markdown("---")
    st.markdown("### 2. Conversión a Tasa Mensual")
    st.markdown(
        """
        Para que la tasa mensual aplicada durante 12 meses (interés compuesto) genere el mismo 
        rendimiento que aplicar la tasa anual neta una sola vez, se igualan los factores:
        """
    )
    st.latex(r"(1 + Tasa_{mensual})^{12} = 1 + Tasa_{anual\_neta}")
    st.markdown("Despejando (aplicando raíz doceava y restando 1), llegamos a la fórmula de la tasa mensual:")
    st.latex(r"Tasa_{mensual} = (1 + Tasa_{anual\_neta})^{\frac{1}{12}} - 1")
    
    st.markdown("---")
    st.markdown("### 3. Cálculo del Saldo (Proyección iterativa)")
    st.markdown(
        """
        El simulador proyecta el crecimiento del capital mes a mes. Para cada mes:
        1. Se parte de un **Saldo Inicial** (en el primer mes es el aporte inicial o $0$).
        2. Ese saldo genera intereses durante ese mes.
        3. A eso se le suma el nuevo **Aporte Mensual** inyectado.
        
        La ecuación completa para calcular el final del mes es:
        """
    )
    st.latex(r"Saldo_{final} = Saldo_{inicial} + (Saldo_{inicial} \times Tasa_{mensual}) + Aporte_{mensual}")
    st.markdown("Factorizando el término común ($Saldo_{inicial}$), obtenemos la fórmula que itera el código:")
    st.latex(r"Saldo_{final} = Saldo_{inicial} \times (1 + Tasa_{mensual}) + Aporte_{mensual}")
    st.info(
        "💡 **Nota:** El Saldo Final de un mes se convierte en el Saldo Inicial del mes siguiente. "
        "Este ciclo repetitivo es lo que permite calcular el poderoso efecto del interés compuesto a lo largo de los años."
    )

# -------------------------
# FORMATEO
# -------------------------

def formato_pesos(valor):
    return f"${int(round(valor, 0)):,}".replace(",", ".")

def limpiar_pesos(texto):
    return float(texto.replace("$", "").replace(".", "").replace(",", ""))

def normalizar_input(texto):
    try:
        numero = limpiar_pesos(texto)
        return formato_pesos(numero), numero
    except:
        return texto, None

# -------------------------
# MODELO
# -------------------------

def proyectar_flujo(
    aporte_mensual: float,
    plazo_meses: int,
    tasa_anual: float,
    aporte_inicial: float = 0.0,
) -> pd.DataFrame:

    meses = plazo_meses
    tasa_mensual = (1 + tasa_anual) ** (1 / 12) - 1

    registros = []
    saldo = aporte_inicial

    for mes in range(1, meses + 1):
        anio = (mes - 1) // 12 + 1

        saldo_inicial = saldo
        rentabilidad = saldo_inicial * tasa_mensual
        saldo = saldo_inicial + rentabilidad + aporte_mensual

        registros.append(
            {
                "Mes": mes,
                "Año": anio,
                "Aporte mensual_num": aporte_mensual,
                "Saldo inicial_num": saldo_inicial,
                "Rentabilidad del mes_num": rentabilidad,
                "Saldo final_num": saldo,
            }
        )

    return pd.DataFrame(registros)

# -------------------------
# SIDEBAR INPUTS PRO
# -------------------------

with st.sidebar:
    st.header("Parámetros")

    # Aporte inicial
    aporte_inicial_str = st.text_input("Aporte inicial ($)", value="$0")
    aporte_inicial_str, aporte_inicial = normalizar_input(aporte_inicial_str)

    # Aporte mensual (🔥 FORMATO AUTOMÁTICO)
    aporte_mensual_str = st.text_input("Aporte mensual ($)", value="$1.000.000")
    aporte_mensual_str, aporte_mensual = normalizar_input(aporte_mensual_str)

    if aporte_mensual is None or aporte_inicial is None:
        st.error("Formato inválido. Usa formato tipo $1.000.000")
        st.stop()

    plazo_meses = st.number_input(
        "Plazo (meses)", 
        min_value=1, 
        max_value=1200, 
        value=48, 
        step=1
    )

    tasa_anual_pct = st.slider(
        "Tasa anual esperada (%)",
        min_value=0.0,
        max_value=20.0,
        value=5.0,
        step=0.1,
    )

    costo_admin_anual_pct = st.number_input(
        "Costo de administración anual (%)",
        min_value=0.0,
        max_value=5.0,
        value=0.51,
        step=0.01,
        format="%.2f"
    )

# -------------------------
# CÁLCULO
# -------------------------

tasa_anual = tasa_anual_pct / 100
costo_admin_anual = costo_admin_anual_pct / 100
tasa_anual_neta = tasa_anual - costo_admin_anual

df = proyectar_flujo(
    aporte_mensual=aporte_mensual,
    plazo_meses=plazo_meses,
    tasa_anual=tasa_anual_neta,
    aporte_inicial=aporte_inicial,
)

saldo_final = df["Saldo final_num"].iloc[-1]
aporte_total = df["Aporte mensual_num"].sum() + aporte_inicial
rentabilidad_total = saldo_final - aporte_total

# -------------------------
# RESULTADOS
# -------------------------

col1, col2, col3 = st.columns(3)

col1.metric("Saldo final proyectado", formato_pesos(saldo_final))
col2.metric("Aportes acumulados", formato_pesos(aporte_total))
col3.metric("Ganancia estimada", formato_pesos(rentabilidad_total))

# -------------------------
# GRÁFICO
# -------------------------

st.subheader("Evolución del saldo")
st.line_chart(df.set_index("Mes")["Saldo final_num"])

# -------------------------
# TABLA
# -------------------------

st.subheader("Detalle mensual")

df_mostrar = df.copy()

df_mostrar["Aporte mensual"] = df_mostrar["Aporte mensual_num"].apply(formato_pesos)
df_mostrar["Saldo inicial"] = df_mostrar["Saldo inicial_num"].apply(formato_pesos)
df_mostrar["Rentabilidad del mes"] = df_mostrar["Rentabilidad del mes_num"].apply(formato_pesos)
df_mostrar["Saldo final"] = df_mostrar["Saldo final_num"].apply(formato_pesos)

df_mostrar = df_mostrar[
    [
        "Mes",
        "Año",
        "Aporte mensual",
        "Saldo inicial",
        "Rentabilidad del mes",
        "Saldo final",
    ]
]

st.table(df_mostrar)

# -------------------------
# RESUMEN ANUAL
# -------------------------

st.subheader("Resumen anual")

resumen_anual = (
    df.groupby("Año", as_index=False)
    .agg(
        {
            "Aporte mensual_num": "sum",
            "Rentabilidad del mes_num": "sum",
            "Saldo final_num": "last",
        }
    )
    .rename(
        columns={
            "Aporte mensual_num": "Aporte anual",
            "Rentabilidad del mes_num": "Rentabilidad anual",
            "Saldo final_num": "Saldo final",
        }
    )
)

resumen_anual["Aporte anual"] = resumen_anual["Aporte anual"].apply(formato_pesos)
resumen_anual["Rentabilidad anual"] = resumen_anual["Rentabilidad anual"].apply(formato_pesos)
resumen_anual["Saldo final"] = resumen_anual["Saldo final"].apply(formato_pesos)

st.table(resumen_anual)

# -------------------------
# FOOTER
# -------------------------

st.markdown("---")
st.caption(
    "Modelo de capitalización mensual con tasa anual neta (tasa esperada menos costo de administración). "
    "Proyección referencial, no constituye promesa de rentabilidad."
)
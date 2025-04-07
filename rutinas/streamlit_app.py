import streamlit as st
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import io
import gen_pub

def generar_pdf(rutina):
    """
    Genera un PDF con la rutina de entrenamiento estructurada.
    Si no hay datos estructurados para días o ejercicios, se muestra
    todo el contenido en el campo de "plan_alimentacion".
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()

    # Título
    story.append(Paragraph(rutina.get("titulo", "Rutina de Entrenamiento"), styles["Title"]))
    story.append(Spacer(1, 12))

    # Sección de Días de Entrenamiento y Ejercicios (solo si existen)
    dias = rutina.get("dias_entrenamiento", {})
    if dias:
        story.append(Paragraph("Días de Entrenamiento y Ejercicios:", styles["Heading2"]))
        story.append(Spacer(1, 6))
        datos_tabla = [["Día", "Ejercicio"]]
        for dia, ejercicios in dias.items():
            for ejercicio in ejercicios:
                datos_tabla.append([dia, ejercicio])
        tabla = Table(datos_tabla, colWidths=[150, 300])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(tabla)
        story.append(Spacer(1, 12))

    # Sección de Ejercicios Detallados (solo si existen)
    ejercicios_list = rutina.get("ejercicios", [])
    if ejercicios_list:
        story.append(Paragraph("Ejercicios Detallados:", styles["Heading2"]))
        story.append(Spacer(1, 6))
        for ejercicio in ejercicios_list:
            # Se espera que cada ejercicio sea un diccionario con keys: nombre, series y repeticiones
            texto = f"{ejercicio.get('nombre', 'Ejercicio')}: {ejercicio.get('series', '')} series de {ejercicio.get('repeticiones', '')} repeticiones"
            story.append(Paragraph(texto, styles["Normal"]))
            story.append(Spacer(1, 6))

    # Sección de Plan de Alimentación o Texto completo (si no hay datos estructurados)
    plan = rutina.get("plan_alimentacion", "")
    if plan:
        story.append(Spacer(1, 12))
        story.append(Paragraph("Plan de Alimentación:", styles["Heading2"]))
        story.append(Spacer(1, 6))
        for linea in plan.split('\n'):
            story.append(Paragraph(linea, styles["Normal"]))
            story.append(Spacer(1, 6))

    doc.build(story)
    buffer.seek(0)
    return buffer

def main():
    # Inject CSS with Markdown
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    st.title("Recomendador de Rutinas de Gimnasio")

    # API key
    # api_key = st.secrets.get("API_KEY")
    api_key = "AIzaSyCrnhpYqo4Y94lY5E6rS4ZLuh_QJoxbC_U"
    if not api_key:
        st.error("La API key no está configurada. Configura la API_KEY en secrets.toml.")
        return

    # Inputs del usuario
    edad = st.number_input("Edad", min_value=10, max_value=100, value=25)
    estatura = st.number_input("Estatura en cm", min_value=100, max_value=300, value=170)
    sexo = st.selectbox("Sexo", ["Masculino", "Femenino"])
    dias_entrenamiento = st.slider("Días de entrenamiento por semana", min_value=1, max_value=7, value=3)
    tipo_alimentacion = st.selectbox("Tipo de alimentación", ["Omnívoro", "Vegetariano", "Vegano"])
    objetivo = st.selectbox("Objetivo", ["Construir músculo", "Perder peso", "Marcar musculatura"])
    gimnasio = st.checkbox("¿Tienes acceso a un gimnasio?")
    experiencia = st.selectbox("Experiencia", ["Principiante", "Intermedio", "Avanzado"])
    condicion = st.text_input("¿Tienes alguna condición médica?")

    rutina = None

    if st.button("Generar Rutina"):
        try:
            # Llamada a la función que genera la rutina
            rutina = gen_pub.generate(edad, estatura, sexo, dias_entrenamiento, tipo_alimentacion, objetivo, gimnasio, experiencia, condicion, api_key)

            # Mostrar la respuesta generada por la IA en la interfaz de Streamlit
            st.write("Rutina generada:", rutina)

            # Si se detecta un error en la respuesta, se muestra el error
            if isinstance(rutina, dict) and "error" in rutina:
                st.error(rutina["error"])
            else:
                # Guardar la rutina en el estado de la sesión
                st.session_state.rutina = rutina
                st.write("Rutina guardada en el estado:", rutina)
        except Exception as e:
            st.error(f"Ocurrió un error: {e}")

    # Mostrar información de depuración sobre la estructura de la rutina
    if st.session_state.get("rutina"):
        st.write("Rutina en el estado de la sesión:", st.session_state.get("rutina"))
    else:
        st.write("No hay rutina guardada en el estado.")

    if st.button("Imprimir Rutina"):
        try:
            rutina = st.session_state.get("rutina", None)
            st.write("Rutina en la sesión al imprimir:", rutina)  # Verifica si está disponible

            if rutina:
                # Si la rutina es un string, la convertimos en una estructura mínima
                if isinstance(rutina, str):
                    rutina_pdf = {
                        "titulo": "Rutina de Gimnasio",
                        "dias_entrenamiento": {},  # No hay datos estructurados de días
                        "ejercicios": [],           # No hay lista de ejercicios separados
                        "plan_alimentacion": rutina  # Todo el texto se muestra aquí
                    }
                # Si es un diccionario, usamos sus claves
                elif isinstance(rutina, dict):
                    rutina_pdf = {
                        "titulo": rutina.get("titulo", "Rutina de Gimnasio"),
                        "dias_entrenamiento": rutina.get("dias_entrenamiento", {}),
                        "ejercicios": rutina.get("ejercicios", []),
                        "plan_alimentacion": rutina.get("plan_alimentacion", "")
                    }

                pdf_buffer = generar_pdf(rutina_pdf)

                st.download_button(
                    label="Descargar Rutina en PDF",
                    data=pdf_buffer,
                    file_name="rutina.pdf",
                    mime="application/pdf",
                )
            else:
                st.warning("Genera una rutina primero o revisa que la rutina esté correctamente estructurada.")
        except Exception as e:
            st.error(f"Ocurrió un error al generar el PDF: {e}")

if __name__ == "__main__":
    main()

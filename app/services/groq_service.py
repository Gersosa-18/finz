# app/services/groq_service.py

import os
from groq import Groq
from typing import Dict
from dotenv import load_dotenv

load_dotenv()

class GroqService:

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY no está configurada")
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"

    def generar_resumen_semanal(self, datos: Dict) -> str:
        """Genera un resumen semanal profesional basado en los datos de mercado."""
        
        prompt = f"""
        Sos un analista financiero profesional escribiendo un newsletter semanal para inversores. 

        Datos de la semana ({datos['fecha_generacion']}):

        ÍNDICES:
        {self._formatear_indices(datos['indices'])}

        SECTORES:
        {self._formatear_sectores(datos['sectores'])}

        Escribí un resumen profesional pero natural, con este flujo:

        1. Abrí con 2-3 oraciones sobre cómo fue la semana en general (tono, tendencia, contexto)

        2. Mencioná los índices principales brevemente (cuál lideró y por qué es relevante)

        3. Hablá de los sectores:
        - Destacá los 3 mejores (con ticker, nombre y % - explicá brevemente por qué brillaron)
        - Mencioná los 3 más débiles (con ticker, nombre y % - contexto de por qué quedaron atrás)

        4. Cerrá con 3-4 insights clave para la próxima semana

        ESTILO:
        - Profesional pero accesible (como un newsletter de Stratechery o Morning Brew)
        - Sin bullets ni listas numeradas forzadas - fluye naturalmente
        - Párrafos cortos (2-3 oraciones máximo)
        - NO uses markdown (**, ##)
        - CRÍTICO: Exactamente entre 225-300 palabras. Ni una más, ni una menos.
        - Desarrollá cada sección sin apuro
        - Sé conciso pero impactante
        """

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Sos un analista financiero senior especializado en mercados de USA."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=8000
            )

            return completion.choices[0].message.content
        
        except Exception as e:
            print(e)
            return "Error generando resumen semanal."
    
    def _formatear_indices(self, indices: list) -> str:
        lineas = []
        for idx in indices:
            lineas.append(f"{idx['ticker']}: {idx['cambio_porcentual']:+.2f}%")
        return "\n".join(lineas)
    
    def _formatear_sectores(self, sectores: list) -> str:
        lineas = []
        for scts in sectores:
            lineas.append(f"{scts['ticker']}: {scts['cambio_porcentual']:+.2f}%")
        return "\n".join(lineas)
    
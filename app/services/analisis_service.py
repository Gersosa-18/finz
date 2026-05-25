import os
import yfinance as yf
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

MODELO_VISION = "meta-llama/llama-4-scout-17b-16e-instruct"
MODELO_TEXTO  = "llama-3.3-70b-versatile"


class AnalisisService:

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY no configurada")
        self.client = Groq(api_key=api_key)

    def analizar(self, ticker: str, timeframe: str, imagen_base64: str, media_type: str = "image/png", observacion="") -> dict:
        """
        Orquesta los tres agentes en secuencia:
        1. Técnico -> Lee el chart (visión)
        2. Fundamental -> Lee datos de yfinance
        3. Moderador -> Sintetiza ambos y emite veredicto
        """
        fundamentales = self._obtener_fundamentales(ticker)
        analisis_tecnico = self._agente_tecnico(imagen_base64, media_type, ticker, timeframe)
        analisis_fundamental = self._agente_fundamental(fundamentales, ticker, timeframe)
        resultado_moderador = self._agente_moderador(analisis_tecnico, analisis_fundamental, ticker, timeframe, observacion)

        return {
            "ticker": ticker,
            "timeframe": timeframe,
            "agente_tecnico": analisis_tecnico,
            "agente_fundamental": analisis_fundamental,
            "moderador": resultado_moderador["analisis"],
            "veredicto": resultado_moderador["veredicto"]
        }
    
    def _obtener_fundamentales(self, ticker: str) -> dict:
        try:
            info = yf.Ticker(ticker).info
            return {
                "nombre": info.get("longName"),
                "sector": info.get("sector"),
                "industria": info.get("industry"),
                "precio_actual": info.get("currentPrice") or info.get("regularMarketPrice"),
                "pe_ratio": info.get("trailingPE"),
                "market_cap": info.get("marketCap"),
                "revenue": info.get("totalRevenue"),
                "margen_bruto": info.get("grossMargins"),
                "max_52w": info.get("fiftyTwoWeekHigh"),
                "min_52w": info.get("fiftyTwoWeekLow"),
                "media_50d": info.get("fiftyDayAverage"),
                "media_200d": info.get("twoHundredDayAverage"),
                "volumen_promedio": info.get("averageVolume"),
                "beta": info.get("beta"),

            }
        except Exception as e:
            return {"error": f"No se pudieron obtener fundamentales_ {e}"}
        
    def _agente_tecnico(self, imagen_base64: str, media_type: str, ticker: str, timeframe: str) -> str:
        completion = self.client.chat.completions.create(
            model=MODELO_VISION,
                        messages=[
                {
                    "role": "system",
                    "content": (
                        f"Sos un trader técnico experto. Analizás SOLO lo que ves en el chart, "
                        f"sin considerar fundamentales. Ticker: {ticker} | Timeframe: {timeframe}. "
                        "Respondé en español, directo. Máximo 100 palabras.\n"
                        "Estructura:\n"
                        "TENDENCIA: (alcista/bajista/lateral)\n"
                        "NIVELES CLAVE: (soportes y resistencias visibles)\n"
                        "PATRÓN: (patrón técnico si hay alguno)\n"
                        "SEÑAL: (COMPRAR / ESPERAR / NO_ENTRAR) + justificación breve"
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{media_type};base64,{imagen_base64}"},
                        },
                        {
                            "type": "text",
                            "text": f"Analizá este chart de {ticker} para timeframe {timeframe}.",
                        },
                    ],
                },
            ],
            max_tokens=250,
            temperature=0.3,
        )
        return completion.choices[0].message.content
    
    def _agente_fundamental(self, fundamentales: dict, ticker: str, timeframe: str) -> str:
        datos_str = "\n".join(
            f"{k}: {v}" for k, v in fundamentales.items() if v is not None
        )
        completion = self.client.chat.completions.create(
            model=MODELO_TEXTO,
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"Sos un analista fundamental experto. Analizás SOLO métricas financieras, "
                        f"sin ver el chart. Ticker: {ticker} | Timeframe: {timeframe}. "
                        "Respondé en español, directo. Máximo 150 palabras.\n"
                        "Estructura:\n"
                        "VALUACIÓN: (cara/barata/justa según P/E y sector)\n"
                        "SALUD: (situación financiera del negocio)\n"
                        "CONTEXTO: (posición en el sector)\n"
                        "SEÑAL: (COMPRAR / ESPERAR / NO_ENTRAR) + justificación breve"
                    ),
                },
                {
                    "role": "user",
                    "content": f"Analizá {ticker} con estos datos:\n{datos_str}",
                },
            ],
            max_tokens=250,
            temperature=0.3,
        )
        return completion.choices[0].message.content

    def _agente_moderador(self, tecnico: str, fundamental: str, ticker: str, timeframe: str, observacion: str = "") -> dict:
        completion = self.client.chat.completions.create(
            model=MODELO_TEXTO,
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"Sos un moderador de análisis financiero. Recibís dos análisis independientes "
                        f"y tu trabajo es sintetizarlos. Ticker: {ticker} | Timeframe: {timeframe}. "
                        "Respondé en español. Máximo 150 palabras.\n"
                        "Estructura:\n"
                        "CONVERGENCIA/DIVERGENCIA: (¿coinciden o se contradicen?)\n"
                        f"PESO: (para {timeframe}, ¿qué importa más: técnico o fundamental? ¿por qué?)\n"
                        "VEREDICTO: (exactamente una de estas: COMPRAR / ESPERAR / NO_ENTRAR)\n"
                        "RAZÓN: (1-2 oraciones finales)"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Análisis Técnico:\n{tecnico}\n\n"
                        f"Análisis Fundamental:\n{fundamental}\n\n"
                        f"Moderá ambos análisis para {ticker} en timeframe {timeframe}."
                        + (f"\n\nObservación del usuario: {observacion}" if observacion.strip() else "")
                    ),
                },
            ],
            max_tokens=400,
            temperature=0.2,
        )
 
        respuesta = completion.choices[0].message.content
        veredicto = "ESPERAR"
        if "NO_ENTRAR" in respuesta or "NO ENTRAR" in respuesta:
            veredicto = "NO_ENTRAR"
        elif "VEREDICTO: COMPRAR" in respuesta or "VEREDICTO:** COMPRAR" in respuesta:
            veredicto = "COMPRAR"
        return {"analisis": respuesta, "veredicto": veredicto}

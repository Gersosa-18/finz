# finz/app/utils/analisis_sentimiento.py
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from deep_translator import GoogleTranslator

# Carga única de modelo y tokenizer
tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
modelo = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")

def analizar_sentimiento(texto: str) -> str:
    if not texto or not texto.strip():
        return 'neutral'
   
    try:
        # Traducir al inglés solo si el texto no parece estar en inglés
        texto = GoogleTranslator(source='auto', target='en').translate(texto)
    except Exception as e:
        print(f"⚠️ Error al traducir el texto: {e}")
        return 'neutral'
   
    try:
        tokens = tokenizer(texto, return_tensors="pt", truncation=True)
        with torch.no_grad():
            outputs = modelo(**tokens)
            
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)[0]
        max_prob = probs.max().item()

        # Si la confianza es baja, devolver neutral
        if max_prob < 0.55:  # Menos del 55% de confianza
            return 'neutral'
            
        idx = probs.argmax().item()
        etiqueta = modelo.config.id2label[idx]
        mapeo = {'negative': 'negativo', 'neutral': 'neutral', 'positive': 'positivo'}
        return mapeo.get(etiqueta, 'neutral')
    except Exception as e:
        print(f"❌ Error al analizar el sentimiento: {e}")
        return 'neutral'
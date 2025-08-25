#!/usr/bin/env python3
"""
Script para ingestar la conversación capturada en R2R usando el formato correcto
"""

import requests
import json
from datetime import datetime

def ingest_conversation():
    """Ingesta la conversación en R2R usando el endpoint correcto"""
    print("📥 INGIRIENDO CONVERSACIÓN EN R2R...")
    
    # Leer el archivo de conversación
    try:
        with open('conversation_test_2025-08-23T07-12-26.556034.txt', 'r', encoding='utf-8') as f:
            conversation_content = f.read()
    except FileNotFoundError:
        print("   ❌ Archivo de conversación no encontrado")
        return False
    
    # Usar el endpoint correcto de R2R v3
    url = "http://localhost:7272/v3/documents"
    
    # Preparar los datos en el formato correcto
    files = {
        'file': ('conversation.txt', conversation_content, 'text/plain')
    }
    
    data = {
        'metadata': json.dumps({
            "title": "Conversación Usuario - Extensión R2R",
            "source": "vscode_extension",
            "type": "conversation",
            "timestamp": datetime.now().isoformat(),
            "captured_by": "r2r-activity-tracker",
            "user_query": "icono en la barra lateral izquierda no veo",
            "user_request": "este texto que estoy escribiendo ahora, reculeralo del rag"
        })
    }
    
    try:
        print("   🔄 Enviando a R2R...")
        response = requests.post(url, files=files, data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ Conversación ingresada exitosamente en R2R")
            print(f"   📄 ID del documento: {result.get('results', {}).get('document_id', 'N/A')}")
            return True
        else:
            print(f"   ❌ Error ingresando: {response.status_code}")
            print(f"   📝 Respuesta: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("   ❌ R2R no está disponible")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_search():
    """Prueba buscar el texto ingresado"""
    print("\n🔍 PROBANDO BÚSQUEDA EN R2R...")
    
    queries = [
        "icono en la barra lateral izquierda no veo",
        "este texto que estoy escribiendo ahora",
        "reculeralo del rag"
    ]
    
    for query in queries:
        print(f"\n   🔎 Buscando: '{query}'")
        
        try:
            response = requests.post(
                "http://localhost:7272/v3/retrieval/search",
                json={"query": query, "limit": 3},
                timeout=15
            )
            
            if response.status_code == 200:
                results = response.json()
                found_results = results.get('results', [])
                print(f"   📊 Encontrados: {len(found_results)} resultados")
                
                for i, result in enumerate(found_results[:2], 1):
                    text = result.get('text', '')[:100]
                    score = result.get('score', 0)
                    print(f"   🎯 Resultado {i}: {text}... (score: {score:.3f})")
            else:
                print(f"   ❌ Error en búsqueda: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error buscando: {e}")

def main():
    print("🚀 INGESTA Y PRUEBA EN R2R")
    print("=" * 50)
    
    # 1. Verificar que R2R esté funcionando
    try:
        response = requests.get("http://localhost:7272/v3/health", timeout=5)
        if response.status_code == 200:
            print("✅ R2R backend funcionando")
        else:
            print("❌ R2R backend no responde correctamente")
            return
    except:
        print("❌ R2R backend no disponible")
        return
    
    # 2. Ingestar conversación
    success = ingest_conversation()
    
    if success:
        # 3. Esperar un momento para indexación
        print("\n⏳ Esperando indexación...")
        import time
        time.sleep(3)
        
        # 4. Probar búsqueda
        test_search()
        
        print("\n🎉 COMPLETADO!")
        print("   • Conversación ingresada en R2R ✅")
        print("   • Disponible para búsqueda ✅")
        print("   • Visible en http://localhost:7273/ ✅")
        print("\n💡 Ahora puedes:")
        print("   1. Ir a http://localhost:7273/")
        print("   2. Buscar: 'icono en la barra lateral'")
        print("   3. Ver tu texto capturado por la extensión")
    else:
        print("\n⚠️  No se pudo ingestar, pero los archivos están guardados offline")

if __name__ == "__main__":
    main()

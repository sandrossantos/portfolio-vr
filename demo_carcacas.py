#!/usr/bin/env python3
"""
Script de demonstração (sem GUI) para mostrar funcionalidades principais
"""

import sys
import os
import sqlite3
import base64
import time
import threading
from datetime import datetime

# Simular algumas variáveis globais
DB_PATH = "demo_carcacas.db"
NEXT_SEQUENCE_OVERRIDE = None
NEXT_SEQ_LOCK = threading.Lock()
MAX_RETRY_ATTEMPTS = 2
RETRY_DELAY = 0.5

def inicializar_banco():
    """Inicializa banco de dados"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS carcacas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sequencia INTEGER NOT NULL UNIQUE,
            imagem TEXT NOT NULL,
            classificacao TEXT,
            confidence REAL,
            tracker_id INTEGER,
            timestamp TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def get_proxima_sequencia():
    """Obtém próxima sequência (thread-safe)"""
    global NEXT_SEQUENCE_OVERRIDE
    
    with NEXT_SEQ_LOCK:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(sequencia) FROM carcacas")
        result = cursor.fetchone()
        conn.close()
        
        db_max = result[0] if result[0] is not None else 0
        db_next = db_max + 1
        
        if NEXT_SEQUENCE_OVERRIDE is not None:
            seq = max(db_next, NEXT_SEQUENCE_OVERRIDE)
            NEXT_SEQUENCE_OVERRIDE = seq + 1
        else:
            seq = db_next
        
        return seq

def set_next_sequence(n):
    """Define override de sequência"""
    global NEXT_SEQUENCE_OVERRIDE
    with NEXT_SEQ_LOCK:
        NEXT_SEQUENCE_OVERRIDE = int(n)

def salvar_imagem(imagem_base64, classificacao, tracker_id=None, confidence=None):
    """Salva imagem no banco"""
    # Validação
    if not imagem_base64 or len(imagem_base64) < 100:
        print(f"  ✗ ERRO: Imagem inválida")
        return False
    
    # Retry logic
    for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
        try:
            sequencia = get_proxima_sequencia()
            
            conn = sqlite3.connect(DB_PATH, timeout=10.0)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO carcacas (sequencia, imagem, classificacao, confidence, tracker_id, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (sequencia, imagem_base64, classificacao, confidence, tracker_id, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            print(f"  ✓ Salvo: Sequência {sequencia}, Tracker ID: {tracker_id}, Confidence: {confidence:.2f}")
            return True
            
        except Exception as e:
            print(f"  ✗ Tentativa {attempt} falhou: {e}")
            if attempt < MAX_RETRY_ATTEMPTS:
                time.sleep(RETRY_DELAY)
    
    return False

def listar_registros():
    """Lista registros salvos"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT sequencia, classificacao, confidence, tracker_id, timestamp FROM carcacas ORDER BY sequencia")
    rows = cursor.fetchall()
    conn.close()
    return rows

def main():
    """Demonstração principal"""
    print("="*70)
    print("DEMONSTRAÇÃO - SISTEMA DE CLASSIFICAÇÃO DE CARCAÇAS")
    print("="*70)
    
    # Limpar banco anterior
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    # Inicializar
    print("\n1. Inicializando banco de dados...")
    inicializar_banco()
    print("   ✓ Banco inicializado")
    
    # Demonstrar salvamento básico
    print("\n2. Salvando imagens com sequência automática (max+1)...")
    imagem_teste = base64.b64encode(b"x" * 200).decode('utf-8')
    
    salvar_imagem(imagem_teste, "Carcaça Tipo A", tracker_id=101, confidence=0.85)
    salvar_imagem(imagem_teste, "Carcaça Tipo B", tracker_id=102, confidence=0.92)
    salvar_imagem(imagem_teste, "Carcaça Tipo A", tracker_id=103, confidence=0.78)
    
    # Listar
    print("\n3. Registros no banco:")
    registros = listar_registros()
    for seq, classif, conf, tid, timestamp in registros:
        print(f"   Seq: {seq:3d} | Classe: {classif:15s} | Conf: {conf:.2f} | ID: {tid:3d} | {timestamp}")
    
    # Demonstrar override de sequência
    print("\n4. Definindo sequência inicial para 100...")
    set_next_sequence(100)
    print("   ✓ Override definido")
    
    salvar_imagem(imagem_teste, "Carcaça Tipo C", tracker_id=104, confidence=0.88)
    salvar_imagem(imagem_teste, "Carcaça Tipo A", tracker_id=105, confidence=0.95)
    
    # Listar novamente
    print("\n5. Registros após override:")
    registros = listar_registros()
    for seq, classif, conf, tid, timestamp in registros:
        print(f"   Seq: {seq:3d} | Classe: {classif:15s} | Conf: {conf:.2f} | ID: {tid:3d} | {timestamp}")
    
    # Demonstrar que override menor que max não afeta
    print("\n6. Tentando override menor que max (50)...")
    set_next_sequence(50)
    print("   ✓ Override definido para 50")
    print("   ℹ  Mas como max do banco é 101, próxima sequência será 102")
    
    salvar_imagem(imagem_teste, "Carcaça Tipo B", tracker_id=106, confidence=0.81)
    
    # Listar final
    print("\n7. Registros finais:")
    registros = listar_registros()
    for seq, classif, conf, tid, timestamp in registros:
        print(f"   Seq: {seq:3d} | Classe: {classif:15s} | Conf: {conf:.2f} | ID: {tid:3d} | {timestamp}")
    
    # Estatísticas
    print(f"\n8. Estatísticas:")
    print(f"   Total de registros: {len(registros)}")
    print(f"   Sequências usadas: {[r[0] for r in registros]}")
    
    # Demonstrar validação
    print("\n9. Testando validação de imagem vazia...")
    salvar_imagem("", "Teste", tracker_id=999, confidence=0.5)
    
    # Demonstrar filtro de confiança
    print("\n10. Simulando filtro de confiança (threshold=0.80)...")
    deteccoes = [
        (107, 0.65, "Tipo A"),
        (108, 0.85, "Tipo B"),
        (109, 0.95, "Tipo C"),
    ]
    
    CONF_THRESHOLD = 0.80
    for tid, conf, classe in deteccoes:
        if conf >= CONF_THRESHOLD:
            print(f"   ✓ ID {tid} passou filtro (conf={conf:.2f})")
            salvar_imagem(imagem_teste, classe, tracker_id=tid, confidence=conf)
        else:
            print(f"   ✗ ID {tid} rejeitado (conf={conf:.2f} < {CONF_THRESHOLD:.2f})")
    
    # Resultado final
    print("\n" + "="*70)
    print("DEMONSTRAÇÃO CONCLUÍDA COM SUCESSO!")
    print("="*70)
    print(f"\nBanco de dados: {DB_PATH}")
    print(f"Total de registros salvos: {len(listar_registros())}")
    print("\nFuncionalidades demonstradas:")
    print("  ✓ Sequência automática (max+1)")
    print("  ✓ Override de sequência inicial")
    print("  ✓ Override menor que max usa max+1")
    print("  ✓ Validação de imagem")
    print("  ✓ Filtro de confiança")
    print("  ✓ Retry logic (não demonstrado erro, mas implementado)")
    print("  ✓ Thread-safe com locks")
    print("  ✓ Salvamento com confidence e tracker_id")
    
    # Limpar
    print("\nPara inspecionar o banco:")
    print(f"  sqlite3 {DB_PATH}")
    print("  SELECT * FROM carcacas;")

if __name__ == "__main__":
    main()

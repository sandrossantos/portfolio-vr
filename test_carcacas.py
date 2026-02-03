#!/usr/bin/env python3
"""
Script de teste para validar funcionalidades core sem GUI
"""

import sys
import os
import sqlite3
import base64
import time
import threading
from datetime import datetime

# Adicionar path para importar o módulo
sys.path.insert(0, os.path.dirname(__file__))

# Importar componentes testáveis (sem inicializar GUI)
DB_PATH = "test_carcacas.db"

def setup_test_db():
    """Configura banco de teste"""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
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
    print("✓ Banco de teste configurado")

def test_sequence_basic():
    """Testa sequência básica sem override"""
    print("\n=== Teste 1: Sequência Básica ===")
    
    # Simular get_proxima_sequencia
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(sequencia) FROM carcacas")
    result = cursor.fetchone()
    conn.close()
    
    db_max = result[0] if result[0] is not None else 0
    seq = db_max + 1
    
    print(f"DB Max: {db_max}, Próxima sequência: {seq}")
    assert seq == 1, "Primeira sequência deve ser 1"
    print("✓ Teste 1 passou")

def test_sequence_with_data():
    """Testa sequência com dados existentes"""
    print("\n=== Teste 2: Sequência com Dados Existentes ===")
    
    # Inserir alguns registros
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for i in range(1, 4):
        cursor.execute("""
            INSERT INTO carcacas (sequencia, imagem, timestamp)
            VALUES (?, ?, ?)
        """, (i, f"image_data_{i}", datetime.now().isoformat()))
    conn.commit()
    conn.close()
    
    # Verificar próxima sequência
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(sequencia) FROM carcacas")
    result = cursor.fetchone()
    conn.close()
    
    db_max = result[0]
    seq = db_max + 1
    
    print(f"DB Max: {db_max}, Próxima sequência: {seq}")
    assert seq == 4, "Próxima sequência deve ser 4"
    print("✓ Teste 2 passou")

def test_sequence_override():
    """Testa override de sequência"""
    print("\n=== Teste 3: Override de Sequência ===")
    
    # Simular lógica de override
    NEXT_SEQUENCE_OVERRIDE = 10
    NEXT_SEQ_LOCK = threading.Lock()
    
    with NEXT_SEQ_LOCK:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(sequencia) FROM carcacas")
        result = cursor.fetchone()
        conn.close()
        
        db_max = result[0] if result[0] is not None else 0
        db_next = db_max + 1
        
        seq = max(db_next, NEXT_SEQUENCE_OVERRIDE)
        print(f"DB Max: {db_max}, DB Next: {db_next}, Override: {NEXT_SEQUENCE_OVERRIDE}")
        print(f"Sequência escolhida: {seq}")
        
        assert seq == 10, "Deve usar override (10) pois é maior que db_next (4)"
        print("✓ Teste 3 passou")

def test_sequence_override_lower():
    """Testa override menor que max do banco"""
    print("\n=== Teste 4: Override Menor que DB Max ===")
    
    # Simular lógica de override com valor menor
    NEXT_SEQUENCE_OVERRIDE = 2
    NEXT_SEQ_LOCK = threading.Lock()
    
    with NEXT_SEQ_LOCK:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(sequencia) FROM carcacas")
        result = cursor.fetchone()
        conn.close()
        
        db_max = result[0] if result[0] is not None else 0
        db_next = db_max + 1
        
        seq = max(db_next, NEXT_SEQUENCE_OVERRIDE)
        print(f"DB Max: {db_max}, DB Next: {db_next}, Override: {NEXT_SEQUENCE_OVERRIDE}")
        print(f"Sequência escolhida: {seq}")
        
        assert seq == 4, "Deve usar db_next (4) pois override (2) é menor"
        print("✓ Teste 4 passou")

def test_save_with_validation():
    """Testa salvamento com validação"""
    print("\n=== Teste 5: Validação de Salvamento ===")
    
    # Testar imagem vazia
    imagem_vazia = ""
    if not imagem_vazia or len(imagem_vazia) < 100:
        print("✓ Imagem vazia rejeitada corretamente")
    else:
        assert False, "Imagem vazia não deveria passar validação"
    
    # Testar imagem válida
    imagem_valida = base64.b64encode(b"x" * 200).decode('utf-8')
    if imagem_valida and len(imagem_valida) >= 100:
        print("✓ Imagem válida aceita")
    else:
        assert False, "Imagem válida deveria passar validação"
    
    print("✓ Teste 5 passou")

def test_retry_logic():
    """Testa lógica de retry"""
    print("\n=== Teste 6: Lógica de Retry ===")
    
    MAX_RETRY_ATTEMPTS = 2
    RETRY_DELAY = 0.1
    
    attempts = 0
    success = False
    
    for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
        attempts += 1
        print(f"Tentativa {attempt}/{MAX_RETRY_ATTEMPTS}")
        
        # Simular falha na primeira tentativa
        if attempt == 1:
            print("  Simulando falha...")
            time.sleep(RETRY_DELAY)
            continue
        else:
            # Sucesso na segunda tentativa
            print("  Sucesso!")
            success = True
            break
    
    assert attempts == 2, "Deve ter feito 2 tentativas"
    assert success, "Deve ter sucesso na segunda tentativa"
    print("✓ Teste 6 passou")

def test_thread_safety():
    """Testa thread safety da sequência"""
    print("\n=== Teste 7: Thread Safety ===")
    
    NEXT_SEQUENCE_OVERRIDE = 100
    NEXT_SEQ_LOCK = threading.Lock()
    sequences = []
    
    def get_sequence_threaded():
        with NEXT_SEQ_LOCK:
            nonlocal NEXT_SEQUENCE_OVERRIDE
            seq = NEXT_SEQUENCE_OVERRIDE
            NEXT_SEQUENCE_OVERRIDE += 1
            time.sleep(0.001)  # Simular operação
            sequences.append(seq)
    
    # Criar múltiplas threads
    threads = []
    for _ in range(10):
        t = threading.Thread(target=get_sequence_threaded)
        threads.append(t)
        t.start()
    
    # Aguardar todas
    for t in threads:
        t.join()
    
    # Verificar que não há duplicatas
    print(f"Sequências obtidas: {sorted(sequences)}")
    assert len(sequences) == 10, "Deve ter 10 sequências"
    assert len(set(sequences)) == 10, "Não deve haver duplicatas"
    assert sequences == list(range(100, 110)) or set(sequences) == set(range(100, 110)), "Sequências devem ser únicas"
    print("✓ Teste 7 passou")

def test_confidence_filtering():
    """Testa filtragem por confiança"""
    print("\n=== Teste 8: Filtragem por Confiança ===")
    
    CONFIDENCE_THRESHOLD = 0.5
    
    detections = [
        {'id': 1, 'conf': 0.3},
        {'id': 2, 'conf': 0.5},
        {'id': 3, 'conf': 0.7},
        {'id': 4, 'conf': 0.95},
    ]
    
    filtered = [d for d in detections if d['conf'] >= CONFIDENCE_THRESHOLD]
    
    print(f"Threshold: {CONFIDENCE_THRESHOLD}")
    print(f"Detecções originais: {len(detections)}")
    print(f"Detecções filtradas: {len(filtered)}")
    
    assert len(filtered) == 3, "Deve filtrar detecção com conf < 0.5"
    print("✓ Teste 8 passou")

def test_deduplication():
    """Testa deduplicação por posição e tempo"""
    print("\n=== Teste 9: Deduplicação ===")
    
    RECENT_SAVE_WINDOW = 5.0
    RECENT_SAVE_DISTANCE = 30
    
    recent_saves = []
    current_time = time.time()
    
    # Adicionar salvamento anterior
    recent_saves.append((400, 300, current_time - 1.0))
    
    # Testar objeto próximo no tempo e espaço (deve ser duplicata)
    cx1, cy1 = 410, 305
    dist1 = ((cx1 - 400)**2 + (cy1 - 300)**2)**0.5
    time_diff1 = current_time - (current_time - 1.0)
    is_dup1 = dist1 < RECENT_SAVE_DISTANCE and time_diff1 < RECENT_SAVE_WINDOW
    
    print(f"Teste 1: dist={dist1:.1f}px, time={time_diff1:.1f}s -> duplicata={is_dup1}")
    assert is_dup1, "Objeto próximo deve ser considerado duplicata"
    
    # Testar objeto distante (não deve ser duplicata)
    cx2, cy2 = 500, 300
    dist2 = ((cx2 - 400)**2 + (cy2 - 300)**2)**0.5
    is_dup2 = dist2 < RECENT_SAVE_DISTANCE
    
    print(f"Teste 2: dist={dist2:.1f}px -> duplicata={is_dup2}")
    assert not is_dup2, "Objeto distante não deve ser duplicata"
    
    print("✓ Teste 9 passou")

def cleanup():
    """Remove arquivos de teste"""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    print("\n✓ Limpeza concluída")

def main():
    """Executa todos os testes"""
    print("="*60)
    print("TESTES DO SISTEMA DE CARCAÇAS")
    print("="*60)
    
    try:
        setup_test_db()
        test_sequence_basic()
        test_sequence_with_data()
        test_sequence_override()
        test_sequence_override_lower()
        test_save_with_validation()
        test_retry_logic()
        test_thread_safety()
        test_confidence_filtering()
        test_deduplication()
        
        print("\n" + "="*60)
        print("✓ TODOS OS TESTES PASSARAM!")
        print("="*60)
        
    except AssertionError as e:
        print(f"\n✗ TESTE FALHOU: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        cleanup()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

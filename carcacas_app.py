#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Carcaças Detection App - Streamlit Application
Full implementation with responsive layout, history panel, DB save with retries,
sequence override, deduplication, ROI support, confidence display, and tracker ID handling.
"""

import streamlit as st
import cv2
import numpy as np
from datetime import datetime
import sqlite3
import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd

# ============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================================
st.set_page_config(
    page_title="Detecção de Carcaças",
    page_icon="🥩",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================================
# ESTILOS CSS - REDUÇÃO DE ESPAÇAMENTO À ESQUERDA E LAYOUT RESPONSIVO
# ============================================================================
st.markdown("""
<style>
    /* Reduzir padding geral */
    .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        padding-top: 1rem !important;
        max-width: 100% !important;
    }
    
    /* Reduzir margem do main container */
    .main > div {
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }
    
    /* Estilo para destaque da sequência atual */
    .current-sequence-highlight {
        background: linear-gradient(90deg, #FF6B6B 0%, #FF8E53 100%);
        color: white !important;
        padding: 15px 20px;
        border-radius: 10px;
        font-size: 24px;
        font-weight: bold;
        text-align: center;
        box-shadow: 0 4px 15px rgba(255, 107, 107, 0.4);
        margin: 10px 0;
        border: 3px solid #FFD93D;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% {
            transform: scale(1);
            box-shadow: 0 4px 15px rgba(255, 107, 107, 0.4);
        }
        50% {
            transform: scale(1.02);
            box-shadow: 0 6px 20px rgba(255, 107, 107, 0.6);
        }
    }
    
    /* Histórico à direita */
    .history-panel {
        background-color: #f8f9fa;
        border-left: 3px solid #FF6B6B;
        padding: 15px;
        border-radius: 8px;
        max-height: 600px;
        overflow-y: auto;
    }
    
    .history-item {
        background: white;
        padding: 10px;
        margin-bottom: 10px;
        border-radius: 5px;
        border-left: 4px solid #4CAF50;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    .history-item-recent {
        border-left: 4px solid #FF6B6B;
        background: #fff5f5;
    }
    
    /* Confiança e métricas */
    .confidence-badge {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 15px;
        font-weight: bold;
        font-size: 14px;
    }
    
    .confidence-high {
        background-color: #4CAF50;
        color: white;
    }
    
    .confidence-medium {
        background-color: #FFC107;
        color: black;
    }
    
    .confidence-low {
        background-color: #F44336;
        color: white;
    }
    
    /* ROI visualization */
    .roi-info {
        background: #e3f2fd;
        padding: 8px;
        border-radius: 5px;
        margin: 5px 0;
        font-size: 12px;
        border-left: 3px solid #2196F3;
    }
    
    /* Tracker ID badge */
    .tracker-badge {
        background: #9C27B0;
        color: white;
        padding: 3px 8px;
        border-radius: 10px;
        font-size: 12px;
        font-weight: bold;
        display: inline-block;
        margin: 2px;
    }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .current-sequence-highlight {
            font-size: 18px;
            padding: 10px 15px;
        }
        
        .history-panel {
            max-height: 400px;
        }
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# BANCO DE DADOS - COM RETRIES E TRATAMENTO ROBUSTO
# ============================================================================

class DatabaseManager:
    """Gerenciador de banco de dados com retry automático e deduplicação"""
    
    def __init__(self, db_path: str = "carcacas_detections.db", max_retries: int = 5):
        self.db_path = db_path
        self.max_retries = max_retries
        self.retry_delay = 0.1  # 100ms
        self.init_database()
    
    def init_database(self):
        """Inicializa o banco de dados com todas as tabelas necessárias"""
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                conn = sqlite3.connect(self.db_path, timeout=10.0)
                cursor = conn.cursor()
                
                # Tabela principal de detecções
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS detections (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        sequence_number INTEGER NOT NULL,
                        tracker_id INTEGER,
                        confidence REAL NOT NULL,
                        class_name TEXT NOT NULL,
                        bbox_x1 INTEGER,
                        bbox_y1 INTEGER,
                        bbox_x2 INTEGER,
                        bbox_y2 INTEGER,
                        roi_x INTEGER,
                        roi_y INTEGER,
                        roi_width INTEGER,
                        roi_height INTEGER,
                        frame_number INTEGER,
                        dedup_hash TEXT,
                        UNIQUE(sequence_number, tracker_id, dedup_hash)
                    )
                """)
                
                # Tabela de histórico de sequências
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sequence_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sequence_number INTEGER UNIQUE NOT NULL,
                        timestamp TEXT NOT NULL,
                        total_detections INTEGER DEFAULT 0,
                        average_confidence REAL DEFAULT 0.0,
                        status TEXT DEFAULT 'completed'
                    )
                """)
                
                # Índices para performance
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_sequence 
                    ON detections(sequence_number)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_timestamp 
                    ON detections(timestamp)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_tracker 
                    ON detections(tracker_id)
                """)
                
                conn.commit()
                conn.close()
                return
                
            except sqlite3.OperationalError as e:
                retry_count += 1
                if retry_count >= self.max_retries:
                    st.error(f"❌ Falha ao inicializar banco de dados após {self.max_retries} tentativas: {e}")
                    raise
                time.sleep(self.retry_delay * retry_count)  # Exponential backoff
    
    def save_detection(self, detection_data: Dict) -> bool:
        """
        Salva uma detecção com retry automático e deduplicação
        
        Args:
            detection_data: Dicionário com dados da detecção
            
        Returns:
            bool: True se salvou com sucesso, False caso contrário
        """
        retry_count = 0
        
        # Gerar hash para deduplicação
        dedup_hash = self._generate_dedup_hash(detection_data)
        detection_data['dedup_hash'] = dedup_hash
        
        while retry_count < self.max_retries:
            try:
                conn = sqlite3.connect(self.db_path, timeout=10.0)
                cursor = conn.cursor()
                
                # Tentar inserir (ignora duplicatas)
                cursor.execute("""
                    INSERT OR IGNORE INTO detections 
                    (timestamp, sequence_number, tracker_id, confidence, class_name,
                     bbox_x1, bbox_y1, bbox_x2, bbox_y2, 
                     roi_x, roi_y, roi_width, roi_height,
                     frame_number, dedup_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    detection_data.get('timestamp'),
                    detection_data.get('sequence_number'),
                    detection_data.get('tracker_id'),
                    detection_data.get('confidence'),
                    detection_data.get('class_name'),
                    detection_data.get('bbox_x1'),
                    detection_data.get('bbox_y1'),
                    detection_data.get('bbox_x2'),
                    detection_data.get('bbox_y2'),
                    detection_data.get('roi_x'),
                    detection_data.get('roi_y'),
                    detection_data.get('roi_width'),
                    detection_data.get('roi_height'),
                    detection_data.get('frame_number'),
                    dedup_hash
                ))
                
                # Atualizar histórico de sequência
                self._update_sequence_history(cursor, detection_data.get('sequence_number'))
                
                conn.commit()
                conn.close()
                return True
                
            except sqlite3.IntegrityError:
                # Duplicata detectada - isso é esperado
                return False
                
            except sqlite3.OperationalError as e:
                retry_count += 1
                if retry_count >= self.max_retries:
                    st.error(f"❌ Falha ao salvar detecção após {self.max_retries} tentativas: {e}")
                    return False
                time.sleep(self.retry_delay * retry_count)
            
            except Exception as e:
                st.error(f"❌ Erro inesperado ao salvar detecção: {e}")
                return False
        
        return False
    
    def _generate_dedup_hash(self, detection_data: Dict) -> str:
        """Gera hash único para deduplicação baseado nos dados principais"""
        key_parts = [
            str(detection_data.get('sequence_number', '')),
            str(detection_data.get('tracker_id', '')),
            str(detection_data.get('bbox_x1', '')),
            str(detection_data.get('bbox_y1', '')),
            str(detection_data.get('bbox_x2', '')),
            str(detection_data.get('bbox_y2', ''))
        ]
        return '_'.join(key_parts)
    
    def _update_sequence_history(self, cursor, sequence_number: int):
        """Atualiza o histórico da sequência"""
        # Calcular estatísticas
        cursor.execute("""
            SELECT COUNT(*), AVG(confidence)
            FROM detections
            WHERE sequence_number = ?
        """, (sequence_number,))
        
        count, avg_conf = cursor.fetchone()
        avg_conf = avg_conf or 0.0
        
        # Inserir ou atualizar histórico
        cursor.execute("""
            INSERT OR REPLACE INTO sequence_history
            (sequence_number, timestamp, total_detections, average_confidence, status)
            VALUES (?, ?, ?, ?, 'completed')
        """, (
            sequence_number,
            datetime.now().isoformat(),
            count,
            avg_conf
        ))
    
    def get_sequence_history(self, limit: int = 10) -> List[Dict]:
        """
        Recupera histórico de sequências (mais recentes primeiro)
        
        Args:
            limit: Número máximo de registros
            
        Returns:
            Lista de dicionários com dados das sequências
        """
        try:
            conn = sqlite3.connect(self.db_path, timeout=5.0)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT sequence_number, timestamp, total_detections, 
                       average_confidence, status
                FROM sequence_history
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'sequence_number': row[0],
                    'timestamp': row[1],
                    'total_detections': row[2],
                    'average_confidence': row[3],
                    'status': row[4]
                }
                for row in rows
            ]
            
        except Exception as e:
            st.error(f"❌ Erro ao recuperar histórico: {e}")
            return []
    
    def get_detections_by_sequence(self, sequence_number: int) -> List[Dict]:
        """Recupera todas as detecções de uma sequência específica"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=5.0)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM detections
                WHERE sequence_number = ?
                ORDER BY timestamp DESC
            """, (sequence_number,))
            
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            conn.close()
            
            return [dict(zip(columns, row)) for row in rows]
            
        except Exception as e:
            st.error(f"❌ Erro ao recuperar detecções: {e}")
            return []

# ============================================================================
# INICIALIZAÇÃO DO ESTADO DA SESSÃO
# ============================================================================

def init_session_state():
    """Inicializa variáveis de estado da sessão"""
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    
    if 'current_sequence' not in st.session_state:
        st.session_state.current_sequence = 1
    
    if 'detections_count' not in st.session_state:
        st.session_state.detections_count = 0
    
    if 'current_frame' not in st.session_state:
        st.session_state.current_frame = None
    
    if 'roi_coords' not in st.session_state:
        st.session_state.roi_coords = None
    
    if 'processing_active' not in st.session_state:
        st.session_state.processing_active = False

# ============================================================================
# FUNÇÕES DE PROCESSAMENTO DE IMAGEM
# ============================================================================

def draw_detection_bbox(image: np.ndarray, bbox: Tuple[int, int, int, int], 
                        confidence: float, tracker_id: Optional[int] = None,
                        class_name: str = "carcaça") -> np.ndarray:
    """
    Desenha bounding box com informações de confiança e tracker ID
    
    Args:
        image: Imagem numpy array
        bbox: Tupla (x1, y1, x2, y2)
        confidence: Valor de confiança (0-1)
        tracker_id: ID do tracker (opcional)
        class_name: Nome da classe detectada
        
    Returns:
        Imagem com as anotações desenhadas
    """
    x1, y1, x2, y2 = bbox
    
    # Cor baseada na confiança
    if confidence >= 0.7:
        color = (0, 255, 0)  # Verde
    elif confidence >= 0.5:
        color = (255, 165, 0)  # Laranja
    else:
        color = (255, 0, 0)  # Vermelho
    
    # Desenhar bounding box
    cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
    
    # Preparar label
    label_parts = [f"{class_name}"]
    if tracker_id is not None:
        label_parts.append(f"ID:{tracker_id}")
    label_parts.append(f"{confidence:.2%}")
    
    label = " | ".join(label_parts)
    
    # Desenhar label com fundo
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.6
    thickness = 2
    
    (label_width, label_height), baseline = cv2.getTextSize(
        label, font, font_scale, thickness
    )
    
    # Fundo do label
    cv2.rectangle(
        image,
        (x1, y1 - label_height - 10),
        (x1 + label_width + 10, y1),
        color,
        -1
    )
    
    # Texto do label
    cv2.putText(
        image,
        label,
        (x1 + 5, y1 - 5),
        font,
        font_scale,
        (255, 255, 255),
        thickness
    )
    
    return image

def draw_roi(image: np.ndarray, roi_coords: Tuple[int, int, int, int]) -> np.ndarray:
    """
    Desenha ROI (Region of Interest) na imagem
    
    Args:
        image: Imagem numpy array
        roi_coords: Tupla (x, y, width, height)
        
    Returns:
        Imagem com ROI desenhada
    """
    x, y, w, h = roi_coords
    
    # Desenhar retângulo da ROI
    cv2.rectangle(image, (x, y), (x + w, y + h), (255, 255, 0), 3)
    
    # Label ROI
    cv2.putText(
        image,
        "ROI",
        (x + 5, y + 25),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 0),
        2
    )
    
    return image

def simulate_detection() -> List[Dict]:
    """
    Simula detecções para demonstração
    Em produção, isso seria substituído por um modelo real de detecção
    
    Returns:
        Lista de dicionários com detecções simuladas
    """
    # Simular 1-3 detecções
    num_detections = np.random.randint(1, 4)
    detections = []
    
    for i in range(num_detections):
        detection = {
            'tracker_id': np.random.randint(1, 100),
            'confidence': np.random.uniform(0.5, 0.99),
            'class_name': 'carcaça',
            'bbox': (
                np.random.randint(50, 300),
                np.random.randint(50, 300),
                np.random.randint(400, 600),
                np.random.randint(400, 600)
            )
        }
        detections.append(detection)
    
    return detections

# ============================================================================
# INTERFACE PRINCIPAL
# ============================================================================

def render_current_sequence_highlight():
    """Renderiza o destaque da sequência atual (Próxima seq atual)"""
    st.markdown(
        f"""
        <div class="current-sequence-highlight">
            🎯 Próxima seq atual: #{st.session_state.current_sequence}
        </div>
        """,
        unsafe_allow_html=True
    )

def render_confidence_badge(confidence: float) -> str:
    """Retorna HTML para badge de confiança"""
    if confidence >= 0.7:
        css_class = "confidence-high"
    elif confidence >= 0.5:
        css_class = "confidence-medium"
    else:
        css_class = "confidence-low"
    
    return f'<span class="confidence-badge {css_class}">{confidence:.1%}</span>'

def render_history_panel():
    """Renderiza o painel de histórico à direita (mais recentes no topo)"""
    st.markdown("### 📊 Histórico")
    
    history = st.session_state.db_manager.get_sequence_history(limit=20)
    
    if not history:
        st.info("Nenhum histórico disponível ainda.")
        return
    
    # Container com scroll
    st.markdown('<div class="history-panel">', unsafe_allow_html=True)
    
    for idx, seq_data in enumerate(history):
        # Destaque para mais recente
        item_class = "history-item-recent" if idx == 0 else "history-item"
        
        timestamp_str = seq_data['timestamp'][:19].replace('T', ' ')
        
        st.markdown(f"""
        <div class="{item_class}">
            <strong>Seq #{seq_data['sequence_number']}</strong><br>
            <small>🕐 {timestamp_str}</small><br>
            📦 Detecções: {seq_data['total_detections']}<br>
            {render_confidence_badge(seq_data['average_confidence'])} Média
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def main():
    """Função principal da aplicação"""
    
    # Inicializar estado
    init_session_state()
    
    # Título principal
    st.title("🥩 Sistema de Detecção de Carcaças")
    
    # Renderizar destaque da sequência atual
    render_current_sequence_highlight()
    
    # Layout em colunas: área principal e histórico
    col_main, col_history = st.columns([2, 1])
    
    # ========================================================================
    # COLUNA PRINCIPAL - Controles e Visualização
    # ========================================================================
    with col_main:
        st.markdown("### 🎬 Controles")
        
        # Linha de controles
        ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns(4)
        
        with ctrl_col1:
            # Override de sequência
            new_sequence = st.number_input(
                "Override Sequência",
                min_value=1,
                value=st.session_state.current_sequence,
                step=1,
                help="Sobrescrever número da sequência atual"
            )
            if new_sequence != st.session_state.current_sequence:
                st.session_state.current_sequence = new_sequence
                st.success(f"✅ Sequência alterada para #{new_sequence}")
        
        with ctrl_col2:
            if st.button("▶️ Processar Frame", use_container_width=True):
                st.session_state.processing_active = True
        
        with ctrl_col3:
            if st.button("⏭️ Próxima Sequência", use_container_width=True):
                st.session_state.current_sequence += 1
                st.rerun()
        
        with ctrl_col4:
            if st.button("🔄 Reset", use_container_width=True):
                st.session_state.current_sequence = 1
                st.session_state.detections_count = 0
                st.rerun()
        
        # ====================================================================
        # CONFIGURAÇÃO DE ROI
        # ====================================================================
        st.markdown("### 🎯 Configuração de ROI")
        
        roi_col1, roi_col2, roi_col3, roi_col4 = st.columns(4)
        
        with roi_col1:
            roi_x = st.number_input("ROI X", min_value=0, value=50, step=10)
        with roi_col2:
            roi_y = st.number_input("ROI Y", min_value=0, value=50, step=10)
        with roi_col3:
            roi_width = st.number_input("ROI Largura", min_value=10, value=500, step=10)
        with roi_col4:
            roi_height = st.number_input("ROI Altura", min_value=10, value=400, step=10)
        
        st.session_state.roi_coords = (roi_x, roi_y, roi_width, roi_height)
        
        # ====================================================================
        # PROCESSAMENTO E VISUALIZAÇÃO
        # ====================================================================
        if st.session_state.processing_active:
            st.markdown("### 🖼️ Frame Atual")
            
            # Criar imagem de exemplo (em produção seria do stream de vídeo)
            frame = np.zeros((600, 800, 3), dtype=np.uint8)
            frame[:] = (40, 40, 40)  # Fundo cinza escuro
            
            # Desenhar ROI
            if st.session_state.roi_coords:
                frame = draw_roi(frame, st.session_state.roi_coords)
            
            # Simular detecções
            detections = simulate_detection()
            
            # Processar cada detecção
            for detection in detections:
                # Desenhar bbox
                frame = draw_detection_bbox(
                    frame,
                    detection['bbox'],
                    detection['confidence'],
                    detection['tracker_id'],
                    detection['class_name']
                )
                
                # Salvar no banco de dados
                detection_data = {
                    'timestamp': datetime.now().isoformat(),
                    'sequence_number': st.session_state.current_sequence,
                    'tracker_id': detection['tracker_id'],
                    'confidence': detection['confidence'],
                    'class_name': detection['class_name'],
                    'bbox_x1': detection['bbox'][0],
                    'bbox_y1': detection['bbox'][1],
                    'bbox_x2': detection['bbox'][2],
                    'bbox_y2': detection['bbox'][3],
                    'roi_x': roi_x,
                    'roi_y': roi_y,
                    'roi_width': roi_width,
                    'roi_height': roi_height,
                    'frame_number': st.session_state.detections_count
                }
                
                if st.session_state.db_manager.save_detection(detection_data):
                    st.session_state.detections_count += 1
            
            # Exibir frame
            st.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), use_container_width=True)
            
            # Informações das detecções
            st.markdown("### 📋 Detecções Atuais")
            
            if detections:
                for idx, det in enumerate(detections, 1):
                    det_col1, det_col2, det_col3 = st.columns(3)
                    
                    with det_col1:
                        st.markdown(
                            f'<span class="tracker-badge">Tracker #{det["tracker_id"]}</span>',
                            unsafe_allow_html=True
                        )
                    
                    with det_col2:
                        st.markdown(render_confidence_badge(det['confidence']), unsafe_allow_html=True)
                    
                    with det_col3:
                        st.markdown(f"**{det['class_name']}**")
                    
                    # ROI info
                    st.markdown(f"""
                    <div class="roi-info">
                        📍 BBox: [{det['bbox'][0]}, {det['bbox'][1]}] → [{det['bbox'][2]}, {det['bbox'][3]}]<br>
                        🎯 ROI: x={roi_x}, y={roi_y}, w={roi_width}, h={roi_height}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Nenhuma detecção neste frame.")
            
            # Parar processamento após um frame
            st.session_state.processing_active = False
        
        # ====================================================================
        # ESTATÍSTICAS
        # ====================================================================
        st.markdown("### 📈 Estatísticas")
        
        stat_col1, stat_col2, stat_col3 = st.columns(3)
        
        with stat_col1:
            st.metric("Sequência Atual", f"#{st.session_state.current_sequence}")
        
        with stat_col2:
            st.metric("Total de Detecções", st.session_state.detections_count)
        
        with stat_col3:
            history = st.session_state.db_manager.get_sequence_history(limit=1)
            if history:
                avg_conf = history[0]['average_confidence']
                st.metric("Confiança Média", f"{avg_conf:.1%}")
            else:
                st.metric("Confiança Média", "N/A")
    
    # ========================================================================
    # COLUNA DE HISTÓRICO - Painel à direita
    # ========================================================================
    with col_history:
        render_history_panel()
    
    # ========================================================================
    # SEÇÃO DE DADOS BRUTOS (Expansível)
    # ========================================================================
    with st.expander("🔍 Ver Dados Brutos da Sequência Atual"):
        current_detections = st.session_state.db_manager.get_detections_by_sequence(
            st.session_state.current_sequence
        )
        
        if current_detections:
            df = pd.DataFrame(current_detections)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Nenhuma detecção registrada para esta sequência ainda.")

# ============================================================================
# PONTO DE ENTRADA
# ============================================================================

if __name__ == "__main__":
    main()

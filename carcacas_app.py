#!/usr/bin/env python3
"""
Aplicação de Classificação de Carcaças com Detecção de Cruzamento
Implementa gravação robusta no banco de dados e sequência ajustável manualmente.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
import threading
import sqlite3
import base64
import time
import traceback
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

# ==================== CONFIGURAÇÃO GLOBAL ====================

# Thread-safe sequence override
NEXT_SEQUENCE_OVERRIDE = None
NEXT_SEQ_LOCK = threading.Lock()

# Configurações de detecção
CONFIDENCE_THRESHOLD = 0.5
CROSSING_LINE_Y = 300  # Linha de cruzamento (pixels)
MAX_DISTANCE_ASSOCIATION = 50  # Distância máxima para associação de objetos (pixels)
RECENT_SAVE_WINDOW = 5.0  # Janela de tempo para deduplicação (segundos)
RECENT_SAVE_DISTANCE = 30  # Distância para considerar objeto como duplicado (pixels)

# Configurações de banco de dados
DB_PATH = "carcacas.db"
MAX_RETRY_ATTEMPTS = 2
RETRY_DELAY = 0.5  # segundos

# Executor para operações assíncronas
executor = ThreadPoolExecutor(max_workers=4)


# ==================== FUNÇÕES DE BANCO DE DADOS ====================

def inicializar_banco():
    """Inicializa o banco de dados SQLite se não existir."""
    try:
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
        print(f"[DB] Banco de dados inicializado: {DB_PATH}")
    except Exception as e:
        print(f"[DB ERROR] Falha ao inicializar banco: {e}")
        traceback.print_exc()


def get_proxima_sequencia():
    """
    Obtém a próxima sequência disponível.
    Considera NEXT_SEQUENCE_OVERRIDE se definido, caso contrário usa max+1 do banco.
    Thread-safe usando NEXT_SEQ_LOCK.
    """
    global NEXT_SEQUENCE_OVERRIDE
    
    with NEXT_SEQ_LOCK:
        try:
            # Obter max atual do banco
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(sequencia) FROM carcacas")
            result = cursor.fetchone()
            conn.close()
            
            db_max = result[0] if result[0] is not None else 0
            db_next = db_max + 1
            
            # Determinar sequência a usar
            if NEXT_SEQUENCE_OVERRIDE is not None:
                # Usar o maior entre db_next e NEXT_SEQUENCE_OVERRIDE
                seq = max(db_next, NEXT_SEQUENCE_OVERRIDE)
                # Incrementar override para próxima vez
                NEXT_SEQUENCE_OVERRIDE = seq + 1
            else:
                seq = db_next
            
            # Validação
            if seq <= 0:
                seq = 1
                
            print(f"[SEQUENCE] Próxima sequência: {seq} (DB max: {db_max}, Override: {NEXT_SEQUENCE_OVERRIDE})")
            return seq
            
        except Exception as e:
            print(f"[SEQUENCE ERROR] Erro ao obter sequência: {e}")
            traceback.print_exc()
            # Fallback para timestamp
            return int(time.time())


def set_next_sequence(n):
    """
    Define o próximo valor de sequência a ser usado.
    Thread-safe.
    """
    global NEXT_SEQUENCE_OVERRIDE
    
    with NEXT_SEQ_LOCK:
        try:
            n = int(n)
            if n < 1:
                raise ValueError("Sequência deve ser maior que 0")
            NEXT_SEQUENCE_OVERRIDE = n
            print(f"[SEQUENCE] Override definido para: {n}")
            return True, f"Sequência inicial definida para {n}"
        except ValueError as e:
            msg = f"Valor inválido: {e}"
            print(f"[SEQUENCE ERROR] {msg}")
            return False, msg


def salvar_imagem_banco(imagem_base64, classificacao, app, tracker_id=None, confidence=None):
    """
    Salva imagem no banco de dados com retry e notificação robusta.
    Executa validações e tenta reconectar em caso de erro.
    """
    print(f"[SAVE] Iniciando salvamento - Classificação: {classificacao}, Tracker ID: {tracker_id}, Confidence: {confidence}")
    
    # Validação da imagem
    if not imagem_base64 or len(imagem_base64) < 100:
        error_msg = "Imagem vazia ou muito pequena"
        print(f"[SAVE ERROR] {error_msg}")
        app.root.after(0, lambda: app.notify_save_result(False, error_msg, tracker_id))
        return
    
    # Tentativas de salvamento com retry
    for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
        try:
            print(f"[SAVE] Tentativa {attempt}/{MAX_RETRY_ATTEMPTS}")
            
            # Obter próxima sequência
            sequencia = get_proxima_sequencia()
            
            # Conectar e inserir
            conn = sqlite3.connect(DB_PATH, timeout=10.0)
            cursor = conn.cursor()
            
            timestamp = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO carcacas (sequencia, imagem, classificacao, confidence, tracker_id, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (sequencia, imagem_base64, classificacao, confidence, tracker_id, timestamp))
            
            conn.commit()
            conn.close()
            
            # Sucesso
            success_msg = f"Sequência {sequencia} salva com sucesso"
            print(f"[SAVE SUCCESS] {success_msg}")
            app.root.after(0, lambda s=sequencia, c=confidence, t=tracker_id: 
                          app.notify_save_result(True, f"Sequência {s}", t, confidence=c))
            return
            
        except sqlite3.IntegrityError as e:
            # Erro de unicidade - não tentar novamente
            error_msg = f"Erro de integridade (sequência duplicada?): {e}"
            print(f"[SAVE ERROR] {error_msg}")
            traceback.print_exc()
            app.root.after(0, lambda: app.notify_save_result(False, error_msg, tracker_id))
            return
            
        except Exception as e:
            error_msg = f"Erro na tentativa {attempt}: {e}"
            print(f"[SAVE ERROR] {error_msg}")
            traceback.print_exc()
            
            if attempt < MAX_RETRY_ATTEMPTS:
                print(f"[SAVE] Aguardando {RETRY_DELAY}s antes de retry...")
                time.sleep(RETRY_DELAY)
            else:
                # Última tentativa falhou
                final_error = f"Falha após {MAX_RETRY_ATTEMPTS} tentativas: {e}"
                print(f"[SAVE ERROR] {final_error}")
                app.root.after(0, lambda: app.notify_save_result(False, final_error, tracker_id))


# ==================== CLASSE PRINCIPAL ====================

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Classificação de Carcaças")
        self.root.geometry("1200x800")
        
        # Estado da aplicação
        self.running = False
        self.cap = None
        
        # Rastreamento de objetos
        self.objects_passed = set()  # IDs que já cruzaram a linha
        self.recent_saves = []  # [(cx, cy, timestamp), ...] para deduplicação
        self.last_positions = {}  # {id: {'cx': int, 'cy': int, 'last_seen': datetime}}
        self.next_temp_id = -1  # IDs temporários para objetos sem tracker
        
        # Configurações ajustáveis
        self.confidence_threshold = tk.DoubleVar(value=CONFIDENCE_THRESHOLD)
        self.current_sequence_var = tk.StringVar(value="Aguardando...")
        
        # Construir interface
        self.build_ui()
        
        # Inicializar banco
        inicializar_banco()
        
    def build_ui(self):
        """Constrói a interface gráfica."""
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Painel esquerdo (controles)
        left_panel = ttk.Frame(main_frame, width=250)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)
        
        # Título
        ttk.Label(left_panel, text="Controles", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Botões de controle
        self.start_button = ttk.Button(left_panel, text="Iniciar Captura", command=self.start_capture)
        self.start_button.pack(fill=tk.X, pady=5)
        
        self.stop_button = ttk.Button(left_panel, text="Parar Captura", command=self.stop_capture, state=tk.DISABLED)
        self.stop_button.pack(fill=tk.X, pady=5)
        
        ttk.Separator(left_panel, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Controle de confiança
        ttk.Label(left_panel, text="Limiar de Confiança:").pack(anchor=tk.W, pady=(10, 0))
        confidence_frame = ttk.Frame(left_panel)
        confidence_frame.pack(fill=tk.X, pady=5)
        
        self.confidence_slider = ttk.Scale(
            confidence_frame,
            from_=0.0,
            to=1.0,
            orient=tk.HORIZONTAL,
            variable=self.confidence_threshold,
            command=self.update_confidence_label
        )
        self.confidence_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.confidence_label = ttk.Label(confidence_frame, text=f"{CONFIDENCE_THRESHOLD:.2f}")
        self.confidence_label.pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Separator(left_panel, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Controle de sequência
        ttk.Label(left_panel, text="Sequência Inicial:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(10, 5))
        
        seq_frame = ttk.Frame(left_panel)
        seq_frame.pack(fill=tk.X, pady=5)
        
        self.sequence_entry = ttk.Entry(seq_frame, width=10)
        self.sequence_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(seq_frame, text="Definir", command=self.set_sequence).pack(side=tk.LEFT)
        
        # Display da sequência atual
        ttk.Label(left_panel, text="Próxima Sequência:").pack(anchor=tk.W, pady=(15, 0))
        ttk.Label(left_panel, textvariable=self.current_sequence_var, 
                 font=("Arial", 12, "bold"), foreground="blue").pack(anchor=tk.W, pady=(0, 5))
        
        ttk.Separator(left_panel, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Estatísticas
        ttk.Label(left_panel, text="Estatísticas:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(10, 5))
        self.stats_label = ttk.Label(left_panel, text="Objetos salvos: 0", anchor=tk.W)
        self.stats_label.pack(fill=tk.X)
        
        # Painel direito (vídeo e log)
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Canvas para vídeo
        self.canvas = tk.Canvas(right_panel, bg="black", width=800, height=600)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Log de eventos
        log_frame = ttk.LabelFrame(right_panel, text="Log de Eventos", height=150)
        log_frame.pack(fill=tk.X, pady=(10, 0))
        log_frame.pack_propagate(False)
        
        self.log_text = tk.Text(log_frame, height=8, state=tk.DISABLED, wrap=tk.WORD)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
    
    def update_confidence_label(self, value):
        """Atualiza o label do slider de confiança."""
        self.confidence_label.config(text=f"{float(value):.2f}")
    
    def set_sequence(self):
        """Define a sequência inicial manualmente."""
        try:
            value = self.sequence_entry.get().strip()
            if not value:
                messagebox.showwarning("Aviso", "Digite um valor numérico")
                return
            
            success, message = set_next_sequence(value)
            if success:
                self.log_message(f"✓ {message}", "success")
                self.update_sequence_display()
                messagebox.showinfo("Sucesso", message)
            else:
                self.log_message(f"✗ {message}", "error")
                messagebox.showerror("Erro", message)
                
        except Exception as e:
            error_msg = f"Erro ao definir sequência: {e}"
            self.log_message(f"✗ {error_msg}", "error")
            messagebox.showerror("Erro", error_msg)
    
    def update_sequence_display(self):
        """Atualiza o display da próxima sequência."""
        with NEXT_SEQ_LOCK:
            if NEXT_SEQUENCE_OVERRIDE is not None:
                self.current_sequence_var.set(f"{NEXT_SEQUENCE_OVERRIDE}")
            else:
                self.current_sequence_var.set("Auto (Max+1)")
    
    def log_message(self, message, level="info"):
        """Adiciona mensagem ao log com timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        self.log_text.config(state=tk.NORMAL)
        
        # Definir cores por nível
        if level == "error":
            tag = "error"
            self.log_text.tag_config(tag, foreground="red")
        elif level == "success":
            tag = "success"
            self.log_text.tag_config(tag, foreground="green")
        elif level == "warning":
            tag = "warning"
            self.log_text.tag_config(tag, foreground="orange")
        else:
            tag = "info"
            self.log_text.tag_config(tag, foreground="black")
        
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def notify_save_result(self, success, message, tracker_id=None, confidence=None):
        """Notifica resultado do salvamento (chamado via root.after)."""
        if success:
            conf_text = f" (conf: {confidence:.2f})" if confidence is not None else ""
            tid_text = f" [ID: {tracker_id}]" if tracker_id is not None else ""
            full_message = f"✓ Salvo: {message}{tid_text}{conf_text}"
            self.log_message(full_message, "success")
            
            # Atualizar estatísticas
            current = len(self.objects_passed)
            self.stats_label.config(text=f"Objetos salvos: {current}")
            
            # Atualizar display de sequência
            self.update_sequence_display()
        else:
            tid_text = f" [ID: {tracker_id}]" if tracker_id is not None else ""
            full_message = f"✗ Erro ao salvar{tid_text}: {message}"
            self.log_message(full_message, "error")
    
    def start_capture(self):
        """Inicia a captura de vídeo simulada."""
        self.running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        self.log_message("Captura iniciada", "info")
        
        # Iniciar thread de processamento
        self.capture_thread = threading.Thread(target=self.process_video, daemon=True)
        self.capture_thread.start()
    
    def stop_capture(self):
        """Para a captura de vídeo."""
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
        self.log_message("Captura parada", "warning")
    
    def process_video(self):
        """
        Loop principal de processamento de vídeo.
        NOTA: Esta é uma simulação. Em produção, integraria com YOLO/tracker real.
        """
        # Criar vídeo de teste (simulação)
        frame_count = 0
        
        while self.running:
            try:
                # Criar frame simulado
                frame = self.create_simulated_frame(frame_count)
                
                # Simular detecções
                detections = self.simulate_detections(frame_count)
                
                # Processar detecções
                self.process_detections(frame, detections)
                
                # Exibir frame
                self.display_frame(frame)
                
                frame_count += 1
                time.sleep(0.033)  # ~30 FPS
                
            except Exception as e:
                print(f"[VIDEO ERROR] Erro no loop de vídeo: {e}")
                traceback.print_exc()
                time.sleep(1)
    
    def create_simulated_frame(self, frame_count):
        """Cria um frame simulado para demonstração."""
        frame = 255 * np.ones((600, 800, 3), dtype=np.uint8)
        
        # Desenhar linha de cruzamento
        cv2.line(frame, (0, CROSSING_LINE_Y), (800, CROSSING_LINE_Y), (0, 255, 0), 2)
        cv2.putText(frame, "LINHA DE CRUZAMENTO", (10, CROSSING_LINE_Y - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Adicionar informações
        info_text = f"Frame: {frame_count} | Threshold: {self.confidence_threshold.get():.2f}"
        cv2.putText(frame, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        
        return frame
    
    def simulate_detections(self, frame_count):
        """
        Simula detecções de objetos para demonstração.
        Em produção, isso viria do YOLO/tracker.
        """
        detections = []
        
        # Simular objeto cruzando a cada 100 frames
        if frame_count % 100 == 50:
            # Objeto antes da linha
            detections.append({
                'tracker_id': 1,
                'bbox': (350, CROSSING_LINE_Y - 60, 450, CROSSING_LINE_Y - 10),
                'confidence': 0.85,
                'class': 'carcaca_tipo_A'
            })
        elif frame_count % 100 == 51:
            # Objeto cruzando a linha
            detections.append({
                'tracker_id': 1,
                'bbox': (350, CROSSING_LINE_Y - 30, 450, CROSSING_LINE_Y + 20),
                'confidence': 0.87,
                'class': 'carcaca_tipo_A'
            })
        elif frame_count % 100 == 52:
            # Objeto após a linha
            detections.append({
                'tracker_id': 1,
                'bbox': (350, CROSSING_LINE_Y + 10, 450, CROSSING_LINE_Y + 60),
                'confidence': 0.83,
                'class': 'carcaca_tipo_A'
            })
        
        return detections
    
    def process_detections(self, frame, detections):
        """
        Processa detecções e verifica cruzamento de linha.
        Implementa lógica de associação e deduplicação.
        """
        current_time = datetime.now()
        confidence_threshold = self.confidence_threshold.get()
        
        for det in detections:
            tracker_id = det.get('tracker_id')
            bbox = det['bbox']
            confidence = det['confidence']
            obj_class = det['class']
            
            # Filtro de confiança
            if confidence < confidence_threshold:
                continue
            
            # Calcular centro
            x1, y1, x2, y2 = bbox
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            
            # Desenhar bbox no frame
            color = (0, 255, 0) if tracker_id in self.objects_passed else (255, 0, 0)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, f"ID:{tracker_id} {confidence:.2f}", (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # Associação de objetos sem ID válido
            if tracker_id is None or tracker_id < 0:
                tracker_id = self.associate_object(cx, cy, current_time)
            
            # Atualizar last_positions
            self.last_positions[tracker_id] = {
                'cx': cx,
                'cy': cy,
                'last_seen': current_time
            }
            
            # Verificar cruzamento
            if self.check_crossing(tracker_id, cy):
                # Verificar deduplicação
                if not self.is_duplicate_save(cx, cy, current_time):
                    print(f"[CROSSING] Objeto {tracker_id} cruzou a linha! Submetendo para salvamento...")
                    
                    # Marcar como já processado
                    self.objects_passed.add(tracker_id)
                    self.recent_saves.append((cx, cy, current_time.timestamp()))
                    
                    # Submeter salvamento assíncrono
                    self.submit_save_task(frame, obj_class, tracker_id, confidence)
    
    def associate_object(self, cx, cy, current_time):
        """
        Associa detecção sem ID a um objeto existente por proximidade.
        Retorna ID existente ou cria novo ID temporário.
        """
        # Tentar encontrar objeto próximo visto recentemente
        for obj_id, pos in list(self.last_positions.items()):
            last_seen = pos['last_seen']
            time_diff = (current_time - last_seen).total_seconds()
            
            if time_diff < 1.0:  # Visto há menos de 1 segundo
                dist = ((cx - pos['cx'])**2 + (cy - pos['cy'])**2)**0.5
                if dist <= MAX_DISTANCE_ASSOCIATION:
                    return obj_id
        
        # Criar novo ID temporário
        new_id = self.next_temp_id
        self.next_temp_id -= 1
        return new_id
    
    def check_crossing(self, tracker_id, cy):
        """Verifica se objeto cruzou a linha e ainda não foi salvo."""
        if tracker_id in self.objects_passed:
            return False
        
        # Verificar se cruzou a linha (com pequena margem)
        return abs(cy - CROSSING_LINE_Y) < 20
    
    def is_duplicate_save(self, cx, cy, current_time):
        """Verifica se salvamento seria duplicado baseado em posição e tempo."""
        current_ts = current_time.timestamp()
        
        # Limpar salvamentos antigos
        self.recent_saves = [(x, y, t) for x, y, t in self.recent_saves
                            if current_ts - t < RECENT_SAVE_WINDOW]
        
        # Verificar duplicatas
        for saved_cx, saved_cy, saved_ts in self.recent_saves:
            dist = ((cx - saved_cx)**2 + (cy - saved_cy)**2)**0.5
            time_diff = current_ts - saved_ts
            
            if dist < RECENT_SAVE_DISTANCE and time_diff < RECENT_SAVE_WINDOW:
                return True
        
        return False
    
    def submit_save_task(self, frame, classification, tracker_id, confidence):
        """Submete tarefa de salvamento ao executor."""
        print(f"[TASK] Submetendo tarefa de salvamento - ID: {tracker_id}, Confidence: {confidence}")
        
        # Converter frame para base64
        try:
            # Extrair ROI simulada (em produção seria a bbox do objeto)
            h, w = frame.shape[:2]
            roi = frame[max(0, CROSSING_LINE_Y-50):min(h, CROSSING_LINE_Y+50), :]
            
            _, buffer = cv2.imencode('.jpg', roi)
            imagem_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Submeter ao executor
            executor.submit(salvar_imagem_banco, imagem_base64, classification, 
                          self, tracker_id, confidence)
            
        except Exception as e:
            error_msg = f"Erro ao preparar imagem: {e}"
            print(f"[TASK ERROR] {error_msg}")
            traceback.print_exc()
            self.root.after(0, lambda: self.notify_save_result(False, error_msg, tracker_id))
    
    def display_frame(self, frame):
        """Exibe frame no canvas."""
        try:
            # Converter BGR para RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Converter para PhotoImage
            image = Image.fromarray(frame_rgb)
            
            # Redimensionar se necessário
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            if canvas_width > 1 and canvas_height > 1:
                image = image.resize((canvas_width, canvas_height), Image.LANCZOS)
            
            photo = ImageTk.PhotoImage(image)
            
            # Atualizar canvas
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=photo)
            self.canvas.image = photo  # Manter referência
            
        except Exception as e:
            print(f"[DISPLAY ERROR] Erro ao exibir frame: {e}")


# ==================== PONTO DE ENTRADA ====================

def main():
    """Ponto de entrada da aplicação."""
    # Imports necessários para simulação
    global np, cv2
    try:
        import numpy as np
        import cv2
    except ImportError as e:
        print(f"ERRO: Bibliotecas necessárias não encontradas: {e}")
        print("Instale: pip install numpy opencv-python Pillow")
        return
    
    # Criar janela principal
    root = tk.Tk()
    app = App(root)
    
    # Iniciar aplicação
    print("="*60)
    print("Sistema de Classificação de Carcaças - Iniciado")
    print("="*60)
    print(f"Banco de dados: {DB_PATH}")
    print(f"Limiar de confiança inicial: {CONFIDENCE_THRESHOLD}")
    print(f"Linha de cruzamento: Y={CROSSING_LINE_Y}")
    print("="*60)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\n[APP] Encerrando aplicação...")
    finally:
        executor.shutdown(wait=False)
        print("[APP] Aplicação encerrada")


if __name__ == "__main__":
    main()

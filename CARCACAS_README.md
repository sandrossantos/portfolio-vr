# Sistema de Classificação de Carcaças

Aplicação de visão computacional para detecção e classificação de carcaças com gravação robusta em banco de dados e controle de sequência ajustável.

## Funcionalidades Implementadas

### 1. Gravação Robusta no Banco de Dados
- ✅ Validação de imagem antes de inserir (verifica se não está vazia)
- ✅ Sistema de retry com até 2 tentativas em caso de erro de conexão
- ✅ Logging completo com traceback de erros
- ✅ Notificações GUI em tempo real (sucesso/falha) via `app.root.after`
- ✅ Tratamento de erros de integridade (sequência duplicada)
- ✅ Timeout configurável para operações de banco

### 2. Sequência Atual Ajustável
- ✅ Variável global `NEXT_SEQUENCE_OVERRIDE` com proteção thread-safe (`NEXT_SEQ_LOCK`)
- ✅ Função `set_next_sequence(n)` para definir sequência atual
- ✅ Lógica em `get_proxima_sequencia()`:
  - Consulta `MAX(sequencia)` do banco
  - Se `NEXT_SEQUENCE_OVERRIDE` definido, usa `max(db_max+1, NEXT_SEQUENCE_OVERRIDE)`
  - Incrementa automaticamente para próxima sequência disponível
  - Thread-safe com lock
- ✅ UI com Entry e botão "Definir Sequência"
- ✅ Display da próxima sequência atual no painel esquerdo

### 3. Garantia de Gravação Única
- ✅ Sistema `objects_passed` para rastrear IDs que já cruzaram
- ✅ Sistema `recent_saves` para deduplicação por posição e tempo
- ✅ Associação de objetos sem ID por proximidade espacial e temporal
- ✅ IDs temporários para objetos sem tracker
- ✅ Gravação apenas no momento de cruzamento da linha

### 4. Passagem de Confidence
- ✅ Parâmetro `confidence` em `salvar_imagem_banco()`
- ✅ Confidence salvo no banco de dados
- ✅ Confidence exibido nas notificações e logs
- ✅ Slider UI para ajustar threshold de confiança

### 5. Logging e Debug Aprimorados
- ✅ Mensagens quando tarefa é submetida ao executor
- ✅ Mensagens quando salvamento inicia
- ✅ Mensagens de sucesso/falha detalhadas
- ✅ Validação de sequência > 0
- ✅ Timestamp em todas as mensagens de log

## Requisitos

```bash
pip install -r requirements.txt
```

Dependências:
- Python 3.7+
- numpy
- opencv-python
- Pillow
- tkinter (incluído na maioria das distribuições Python)

## Estrutura do Banco de Dados

```sql
CREATE TABLE carcacas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sequencia INTEGER NOT NULL UNIQUE,
    imagem TEXT NOT NULL,           -- Base64 encoded
    classificacao TEXT,
    confidence REAL,
    tracker_id INTEGER,
    timestamp TEXT NOT NULL
);
```

## Uso

### Iniciar a Aplicação

```bash
python carcacas_app.py
```

### Interface

**Painel Esquerdo:**
- Botões Iniciar/Parar Captura
- Slider de Limiar de Confiança (0.0 - 1.0)
- Campo para definir Sequência Atual
- Display da próxima sequência atual
- Estatísticas de objetos salvos

**Painel Direito:**
- Visualização de vídeo com linha de cruzamento
- Log de eventos em tempo real

### Definir Sequência Atual

1. Digite o número desejado no campo "Sequência Atual"
2. Clique em "Definir Sequência"
3. A próxima gravação usará exatamente essa sequência (ou maior se o banco já tiver sequências maiores)
4. Sequências subsequentes serão incrementadas automaticamente a partir desse valor

### Ajustar Confiança

Use o slider "Limiar de Confiança" para filtrar detecções:
- 0.0 = aceita todas as detecções
- 1.0 = aceita apenas detecções com 100% de confiança
- Padrão: 0.5 (50%)

## Configurações Ajustáveis (no código)

```python
# Banco de dados
DB_PATH = "carcacas.db"
MAX_RETRY_ATTEMPTS = 2
RETRY_DELAY = 0.5  # segundos

# Detecção
CONFIDENCE_THRESHOLD = 0.5
CROSSING_LINE_Y = 300  # pixels
MAX_DISTANCE_ASSOCIATION = 50  # pixels
RECENT_SAVE_WINDOW = 5.0  # segundos
RECENT_SAVE_DISTANCE = 30  # pixels
```

## Integração com YOLO/Tracker Real

A implementação atual usa detecções simuladas para demonstração. Para integrar com YOLO/tracker real:

1. **Substitua `process_video()` para capturar de câmera/vídeo real:**
   ```python
   self.cap = cv2.VideoCapture(0)  # ou caminho do vídeo
   ret, frame = self.cap.read()
   ```

2. **Substitua `simulate_detections()` com detecção YOLO:**
   ```python
   from ultralytics import YOLO
   
   model = YOLO('yolov8n.pt')
   results = model.track(frame, persist=True, conf=0.3)
   
   for r in results:
       boxes = r.boxes
       for i, box in enumerate(boxes):
           tracker_id = int(box.id[i]) if box.id is not None else None
           bbox = box.xyxy[i].cpu().numpy().astype(int)
           confidence = float(box.conf[i])
           class_id = int(box.cls[i])
           # ... processar
   ```

## Thread Safety

- `NEXT_SEQ_LOCK`: Protege acesso a `NEXT_SEQUENCE_OVERRIDE`
- `get_proxima_sequencia()`: Thread-safe
- `set_next_sequence()`: Thread-safe
- `ThreadPoolExecutor`: Salva imagens em background sem bloquear UI
- `app.root.after()`: Garante atualizações GUI na thread principal

## Tratamento de Erros

### Erros de Banco de Dados
- Retry automático com delay
- Notificação GUI em caso de falha
- Traceback completo no console
- Erros de integridade não fazem retry

### Erros de Validação
- Imagem vazia/pequena não é salva
- Sequência inválida (<1) rejeitada
- Mensagens claras ao usuário

## Testes Recomendados

1. **Thread Safety**: Execute múltiplas gravações simultâneas
2. **Sequência Override**: 
   - Defina sequência menor que max do banco → deve usar db_max+1
   - Defina sequência maior que max do banco → deve usar o valor definido
3. **Retry**: Simule erro de banco (fechar arquivo durante gravação)
4. **Deduplicação**: Verifique que mesmo objeto não é salvo múltiplas vezes
5. **Confidence**: Ajuste threshold e verifique filtragem

## Notas e Suposições

1. **Campo `imagem`**: Aceita texto Base64 (tipo TEXT no SQLite)
2. **Sequência única**: Constraint UNIQUE garante não duplicação
3. **IDs temporários**: Usam valores negativos para não conflitar
4. **Linha de cruzamento**: Posição Y fixa (configurável)
5. **Simulação**: Código atual simula detecções; pronto para integração real

## Logs de Debug

Ao executar, você verá no console:
- `[DB]` - Operações de banco de dados
- `[SEQUENCE]` - Operações de sequência
- `[SAVE]` - Tentativas de salvamento
- `[SAVE SUCCESS]` - Salvamentos bem-sucedidos
- `[SAVE ERROR]` - Erros de salvamento
- `[CROSSING]` - Detecções de cruzamento
- `[TASK]` - Submissão de tarefas assíncronas

## Segurança

- SQL parameterizado (proteção contra injection)
- Timeout em conexões de banco
- Validação de entrada do usuário
- Tratamento de exceções em todas as operações críticas

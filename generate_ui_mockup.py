#!/usr/bin/env python3
"""
Gera uma representação visual da UI (mock screenshot)
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import numpy as np

# Criar figura
fig = plt.figure(figsize=(14, 9))
fig.patch.set_facecolor('#f0f0f0')

# Título
fig.suptitle('Sistema de Classificação de Carcaças - Interface Gráfica', 
             fontsize=16, fontweight='bold', y=0.98)

# Criar dois painéis principais
ax_left = plt.subplot2grid((10, 10), (0, 0), colspan=3, rowspan=8)
ax_right = plt.subplot2grid((10, 10), (0, 3), colspan=7, rowspan=7)
ax_log = plt.subplot2grid((10, 10), (7, 3), colspan=7, rowspan=3)

# ===== PAINEL ESQUERDO (Controles) =====
ax_left.set_xlim(0, 10)
ax_left.set_ylim(0, 100)
ax_left.axis('off')
ax_left.set_title('Painel de Controles', fontweight='bold', pad=20)

y_pos = 95

# Título
ax_left.text(5, y_pos, 'Controles', ha='center', fontsize=14, fontweight='bold')
y_pos -= 8

# Botões
button1 = FancyBboxPatch((1, y_pos-4), 8, 3.5, boxstyle="round,pad=0.1", 
                         facecolor='#4CAF50', edgecolor='black', linewidth=1)
ax_left.add_patch(button1)
ax_left.text(5, y_pos-2, 'Iniciar Captura', ha='center', va='center', 
             fontsize=10, fontweight='bold', color='white')
y_pos -= 6

button2 = FancyBboxPatch((1, y_pos-4), 8, 3.5, boxstyle="round,pad=0.1", 
                         facecolor='#ddd', edgecolor='black', linewidth=1)
ax_left.add_patch(button2)
ax_left.text(5, y_pos-2, 'Parar Captura', ha='center', va='center', 
             fontsize=10, color='#666')
y_pos -= 10

# Separador
ax_left.plot([1, 9], [y_pos, y_pos], 'k-', linewidth=1)
y_pos -= 5

# Slider de confiança
ax_left.text(5, y_pos, 'Limiar de Confiança:', ha='center', fontsize=9, fontweight='bold')
y_pos -= 4
slider_bg = FancyBboxPatch((1, y_pos-2), 8, 2, facecolor='#e0e0e0', 
                           edgecolor='black', linewidth=1)
ax_left.add_patch(slider_bg)
slider_fill = FancyBboxPatch((1, y_pos-2), 4, 2, facecolor='#2196F3', 
                             edgecolor='none')
ax_left.add_patch(slider_fill)
ax_left.text(9.5, y_pos-1, '0.50', ha='left', va='center', fontsize=9)
y_pos -= 6

# Separador
ax_left.plot([1, 9], [y_pos, y_pos], 'k-', linewidth=1)
y_pos -= 5

# Sequência atual
ax_left.text(5, y_pos, 'Sequência Atual:', ha='center', fontsize=9, fontweight='bold')
y_pos -= 4
entry_bg = FancyBboxPatch((1, y_pos-2), 4, 2.5, facecolor='white', 
                          edgecolor='black', linewidth=1)
ax_left.add_patch(entry_bg)
ax_left.text(3, y_pos-0.5, '100', ha='center', va='center', fontsize=9)

button3 = FancyBboxPatch((5.5, y_pos-2), 3.5, 2.5, boxstyle="round,pad=0.05", 
                         facecolor='#2196F3', edgecolor='black', linewidth=1)
ax_left.add_patch(button3)
ax_left.text(7.25, y_pos-0.5, 'Definir Sequência', ha='center', va='center', 
             fontsize=8, color='white', fontweight='bold')
y_pos -= 6

# Display de sequência
ax_left.text(1, y_pos, 'Próxima seq atual:', ha='left', fontsize=8)
y_pos -= 3
ax_left.text(1, y_pos, '101', ha='left', fontsize=11, fontweight='bold', color='blue')
y_pos -= 6

# Separador
ax_left.plot([1, 9], [y_pos, y_pos], 'k-', linewidth=1)
y_pos -= 5

# Estatísticas
ax_left.text(5, y_pos, 'Estatísticas:', ha='center', fontsize=9, fontweight='bold')
y_pos -= 3
ax_left.text(1, y_pos, 'Objetos salvos: 8', ha='left', fontsize=8)

# ===== PAINEL DIREITO (Vídeo) =====
ax_right.set_xlim(0, 100)
ax_right.set_ylim(0, 75)
ax_right.axis('off')
ax_right.set_title('Visualização de Vídeo', fontweight='bold', pad=20)

# Fundo do vídeo
video_bg = patches.Rectangle((0, 0), 100, 75, facecolor='#1a1a1a', edgecolor='black', linewidth=2)
ax_right.add_patch(video_bg)

# Linha de cruzamento
crossing_y = 37.5
ax_right.plot([0, 100], [crossing_y, crossing_y], 'g-', linewidth=3)
ax_right.text(2, crossing_y+2, 'LINHA DE CRUZAMENTO', fontsize=9, color='lime', fontweight='bold')

# Simular objetos detectados
# Objeto 1 (já passou)
obj1 = patches.Rectangle((30, 45), 12, 18, linewidth=2, edgecolor='lime', facecolor='none')
ax_right.add_patch(obj1)
ax_right.text(31, 64, 'ID:105 0.95', fontsize=7, color='lime', fontweight='bold')

# Objeto 2 (cruzando)
obj2 = patches.Rectangle((55, 32), 12, 18, linewidth=2, edgecolor='yellow', facecolor='none')
ax_right.add_patch(obj2)
ax_right.text(56, 51, 'ID:109 0.88', fontsize=7, color='yellow', fontweight='bold')

# Objeto 3 (antes da linha)
obj3 = patches.Rectangle((75, 15), 12, 18, linewidth=2, edgecolor='red', facecolor='none')
ax_right.add_patch(obj3)
ax_right.text(76, 34, 'ID:110 0.82', fontsize=7, color='red', fontweight='bold')

# Info do frame
ax_right.text(2, 72, 'Frame: 3542 | Threshold: 0.50', fontsize=8, color='white',
             bbox=dict(boxstyle='round', facecolor='black', alpha=0.7))

# ===== PAINEL DE LOG =====
ax_log.set_xlim(0, 100)
ax_log.set_ylim(0, 30)
ax_log.axis('off')
ax_log.set_title('Log de Eventos', fontweight='bold', loc='left', pad=10)

# Fundo do log
log_bg = patches.Rectangle((0, 0), 100, 30, facecolor='white', edgecolor='black', linewidth=1)
ax_log.add_patch(log_bg)

# Mensagens de log
log_messages = [
    ('[20:20:37] ✓ Salvo: Sequência 103 [ID: 108] (conf: 0.85)', 'green'),
    ('[20:20:37] ✓ Salvo: Sequência 104 [ID: 109] (conf: 0.95)', 'green'),
    ('[20:20:38] Captura em andamento...', 'black'),
    ('[20:20:39] Objeto 110 detectado com confiança 0.82', 'blue'),
    ('[20:20:40] ✓ Sequência atual definida para 100', 'green'),
]

y_log = 26
for msg, color in log_messages:
    ax_log.text(1, y_log, msg, fontsize=7, color=color, family='monospace')
    y_log -= 5

# Ajustar layout
plt.tight_layout(rect=[0, 0, 1, 0.96])

# Salvar imagem
output_path = 'ui_screenshot.png'
plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='#f0f0f0')
print(f"✓ Screenshot da UI salvo em: {output_path}")
plt.close()

# Criar também diagrama de arquitetura
fig2, ax = plt.subplots(figsize=(12, 8))
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis('off')
fig2.suptitle('Arquitetura do Sistema', fontsize=16, fontweight='bold')

# Camadas
layers = [
    {'name': 'Interface GUI (Tkinter)', 'y': 85, 'color': '#4CAF50'},
    {'name': 'Controle de Sequência (Thread-Safe)', 'y': 70, 'color': '#2196F3'},
    {'name': 'Lógica de Detecção e Cruzamento', 'y': 55, 'color': '#FF9800'},
    {'name': 'Salvamento Assíncrono (ThreadPool)', 'y': 40, 'color': '#9C27B0'},
    {'name': 'Banco de Dados (SQLite)', 'y': 25, 'color': '#F44336'},
]

for layer in layers:
    box = FancyBboxPatch((10, layer['y']-5), 80, 8, boxstyle="round,pad=0.3",
                         facecolor=layer['color'], edgecolor='black', linewidth=2, alpha=0.8)
    ax.add_patch(box)
    ax.text(50, layer['y'], layer['name'], ha='center', va='center',
           fontsize=11, fontweight='bold', color='white')

# Setas de fluxo
arrow_props = dict(arrowstyle='->', lw=2, color='black')
ax.annotate('', xy=(50, 77), xytext=(50, 83), arrowprops=arrow_props)
ax.annotate('', xy=(50, 62), xytext=(50, 68), arrowprops=arrow_props)
ax.annotate('', xy=(50, 47), xytext=(50, 53), arrowprops=arrow_props)
ax.annotate('', xy=(50, 32), xytext=(50, 38), arrowprops=arrow_props)

# Features à esquerda
features_left = [
    '• Slider de Confiança',
    '• Botões Start/Stop',
    '• Entry de Sequência',
    '• Display Sequência Atual',
]
y_feat = 15
ax.text(5, y_feat, 'Features UI:', fontsize=10, fontweight='bold')
y_feat -= 2
for feat in features_left:
    ax.text(5, y_feat, feat, fontsize=8)
    y_feat -= 2

# Features à direita
features_right = [
    '• NEXT_SEQ_LOCK (thread-safe)',
    '• Retry com delay',
    '• Validação de imagem',
    '• Notificação GUI via after()',
    '• Deduplicação espacial/temporal',
    '• IDs temporários para objetos',
]
y_feat = 15
ax.text(70, y_feat, 'Features Core:', fontsize=10, fontweight='bold')
y_feat -= 2
for feat in features_right:
    ax.text(70, y_feat, feat, fontsize=8)
    y_feat -= 2

plt.tight_layout(rect=[0, 0, 1, 0.95])
output_path2 = 'architecture_diagram.png'
plt.savefig(output_path2, dpi=150, bbox_inches='tight', facecolor='white')
print(f"✓ Diagrama de arquitetura salvo em: {output_path2}")
plt.close()

print("\n✓ Imagens geradas com sucesso!")

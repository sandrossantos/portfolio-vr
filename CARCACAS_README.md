# Carcaças Detection App

Sistema de detecção de carcaças com interface Streamlit, incluindo histórico, ROI, rastreamento e armazenamento robusto em banco de dados.

## Características

### Interface do Usuário
- ✅ **Layout Responsivo**: Espaçamento reduzido à esquerda para melhor aproveitamento da tela
- ✅ **Destaque da Sequência Atual**: "Próxima seq atual" visível com animação e destaque
- ✅ **Painel de Histórico**: Localizado à direita, mostrando sequências mais recentes no topo
- ✅ **Override de Sequência**: Permite sobrescrever o número da sequência atual

### Funcionalidades de Detecção
- ✅ **Suporte a ROI**: Configuração de Region of Interest (x, y, largura, altura)
- ✅ **Display de Confiança**: Badges coloridos indicando níveis de confiança (alta/média/baixa)
- ✅ **Tracker ID**: Exibição e rastreamento de IDs únicos para cada detecção
- ✅ **Bounding Boxes**: Visualização com cores baseadas em confiança

### Banco de Dados
- ✅ **Salvamento Robusto**: Sistema com retry automático (até 5 tentativas)
- ✅ **Deduplicação**: Previne inserção de detecções duplicadas
- ✅ **Histórico de Sequências**: Rastreamento completo com estatísticas
- ✅ **Índices de Performance**: Queries otimizadas

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/sandrossantos/portfolio-vr.git
cd portfolio-vr
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Uso

Execute a aplicação com Streamlit:

```bash
streamlit run carcacas_app.py
```

A aplicação estará disponível em: `http://localhost:8501`

## Controles

### Área Principal
- **Override Sequência**: Campo numérico para alterar manualmente a sequência atual
- **▶️ Processar Frame**: Processa um frame e realiza detecções
- **⏭️ Próxima Sequência**: Avança para a próxima sequência
- **🔄 Reset**: Reinicia contadores e volta para sequência 1

### Configuração de ROI
Configure a região de interesse ajustando:
- **ROI X**: Posição horizontal inicial
- **ROI Y**: Posição vertical inicial
- **ROI Largura**: Largura da região
- **ROI Altura**: Altura da região

### Painel de Histórico
Localizado à direita, mostra:
- Número da sequência
- Timestamp
- Total de detecções
- Confiança média (com badge colorido)
- Item mais recente destacado

## Estrutura do Banco de Dados

### Tabela: detections
Armazena todas as detecções individuais com:
- ID único
- Timestamp
- Número da sequência
- Tracker ID
- Confiança
- Classe detectada
- Coordenadas do bounding box (x1, y1, x2, y2)
- Coordenadas e dimensões do ROI
- Número do frame
- Hash de deduplicação

### Tabela: sequence_history
Mantém histórico de sequências com:
- Número da sequência
- Timestamp
- Total de detecções
- Confiança média
- Status (completed/processing)

## Características Técnicas

### Retry com Backoff Exponencial
O sistema tenta salvar dados até 5 vezes com delay crescente (100ms, 200ms, 400ms, etc.)

### Deduplicação
Hash único baseado em:
- Número da sequência
- Tracker ID
- Coordenadas do bounding box

### Performance
- Índices em colunas críticas (sequence_number, timestamp, tracker_id)
- Timeout de 10 segundos para operações de escrita
- Timeout de 5 segundos para operações de leitura

## Desenvolvimento

### Modo de Simulação
A aplicação atual inclui um simulador de detecções para demonstração. Em produção, substitua a função `simulate_detection()` por:
- Integração com modelo YOLO/TensorFlow
- Stream de câmera ao vivo
- Processamento de vídeos

### Extensões Possíveis
- Integração com modelos de Deep Learning
- Exportação de relatórios
- Alertas em tempo real
- Dashboard de analytics
- API REST para integração

## Screenshots

A interface inclui:
1. Destaque animado da sequência atual no topo
2. Área principal com controles e visualização do frame
3. Painel de histórico à direita com scroll
4. Configuração de ROI
5. Display de detecções com badges de confiança e tracker IDs

## Licença

Este projeto faz parte do portfólio de Sandro Silva dos Santos.

## Contato

- WhatsApp: 91 99239-8394
- Email: sandro.silva@example.com

# Sistema de Gestão de Carcaças 2.0

## Descrição

Sistema de banco de dados para gestão de processos de abate e controle de qualidade de carcaças. Desenvolvido para gerenciar escalas de abate, lotes, registros de qualidade e relatórios operacionais.

## Estrutura do Banco de Dados

### Schema: `carcacas2_0`

O banco de dados contém as seguintes tabelas principais:

#### Tabelas de Cadastro Base
- **animal_tipo**: Tipos de animais processados
- **causa_condenacao**: Causas para condenação de carcaças
- **produto_condenado**: Produtos condenados
- **negociacao**: Tipos de negociação

#### Tabelas de Escala e Lotes
- **escala_abate**: Programação de abates
- **escala_lotes**: Lotes relacionados às escalas
- **lotes**: Informações detalhadas dos lotes (fornecedor, curral, quantidade)

#### Tabelas de Controle de Qualidade
- **dif_limpeza**: Diferenças de peso na limpeza
- **condenacao**: Registros de condenações
- **contusoes**: Registro de contusões nas carcaças
- **vacina**: Controle de vacinas
- **bezerro**: Dados específicos de bezerros

#### Tabelas de Registro
- **peso_carcaca**: Pesos das carcaças
- **foto_carcaca**: Fotos das carcaças processadas
- **fotos_currais**: Fotos dos currais
- **obs**: Observações gerais

## Relatório de DIF (Diferença de Limpeza)

### O que é DIF?

DIF (Diferença de Limpeza) representa a diferença de peso registrada durante o processo de limpeza das carcaças. É um indicador importante para controle de qualidade e análise de perdas no processo.

### Arquivos do Relatório

1. **schema_carcacas2_0.sql**
   - Script completo para criação do banco de dados
   - Inclui todas as tabelas, índices e relacionamentos
   - Pronto para importação no MySQL

2. **relatorio_dif_queries.sql**
   - Coleção de queries SQL para diferentes visões do relatório DIF
   - Inclui 6 tipos de relatórios diferentes:
     - Relatório básico por lote
     - Totais por data
     - Análise por tipo de animal
     - Relatório detalhado com informações do lote
     - Relatório por período
     - Ranking de fornecedores

3. **relatorio_dif.php**
   - Interface web completa para visualização do relatório
   - Filtros por data e tipo de animal
   - Resumo estatístico (total de registros, peso total, peso médio)
   - Tabela detalhada com todos os dados
   - Função de impressão
   - Design responsivo

## Instalação

### 1. Criar o Banco de Dados

```bash
mysql -u root -p < database/schema_carcacas2_0.sql
```

### 2. Configurar o Relatório PHP

Edite o arquivo `database/relatorio_dif.php` e ajuste as configurações de conexão:

```php
$host = 'localhost';      // Host do MySQL
$dbname = 'carcacas2_0';  // Nome do banco
$username = 'root';        // Usuário
$password = '';            // Senha
```

### 3. Acessar o Relatório

Coloque os arquivos em um servidor web com PHP habilitado e acesse:

```
http://localhost/database/relatorio_dif.php
```

## Uso das Queries SQL

Execute as queries diretamente no MySQL Workbench ou cliente MySQL:

```bash
mysql -u root -p carcacas2_0 < database/relatorio_dif_queries.sql
```

## Funcionalidades do Relatório DIF

### Filtros Disponíveis
- **Data Início**: Filtrar a partir de uma data específica
- **Data Fim**: Filtrar até uma data específica
- **Tipo Animal**: Filtrar por BOI, VACA ou BEZ (Bezerro)

### Informações Exibidas
- ID do registro DIF
- Data do abate
- Número do lote
- Peso da diferença (kg)
- Tipo de animal
- Fornecedor
- Curral
- Quantidade de animais
- Número da OC (Ordem de Compra)

### Estatísticas
- Total de registros no período
- Peso total de DIF acumulado
- Peso médio de DIF

## Tecnologias Utilizadas

- **MySQL 8.0+**: Banco de dados relacional
- **PHP 7.4+**: Linguagem de programação server-side
- **PDO**: Interface de acesso ao banco de dados
- **HTML5/CSS3**: Interface web moderna e responsiva
- **JavaScript**: Interatividade e funcionalidades dinâmicas

## Estrutura de Diretórios

```
portfolio-vr/
├── database/
│   ├── schema_carcacas2_0.sql        # Schema completo do banco
│   ├── relatorio_dif_queries.sql     # Queries para relatórios
│   ├── relatorio_dif.php             # Interface web do relatório
│   └── README.md                     # Esta documentação
├── index.html                         # Portfolio VR principal
└── README.md                          # README do projeto
```

## Requisitos do Sistema

- **Servidor Web**: Apache 2.4+ ou Nginx
- **PHP**: 7.4 ou superior
- **MySQL**: 8.0 ou superior
- **Extensões PHP**: PDO, pdo_mysql

## Segurança

⚠️ **Importante**: Antes de colocar em produção:

1. Altere as credenciais padrão do banco de dados
2. Use variáveis de ambiente para credenciais sensíveis
3. Implemente autenticação de usuários
4. Configure SSL/TLS para conexões seguras
5. Sanitize todas as entradas de usuário
6. Implemente proteção contra SQL Injection (já implementada via PDO)

## Suporte

Desenvolvido por: **Sandro Silva dos Santos**

- 📱 WhatsApp: 91 99239-8394
- 📧 Email: sandro.silva@example.com

## Licença

Este projeto faz parte do portfólio profissional e está disponível para demonstração.

---

**Última atualização**: 10 de Fevereiro de 2026

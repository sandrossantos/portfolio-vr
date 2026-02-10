<?php
/**
 * Relatório de Diferença de Limpeza (DIF)
 * Sistema de Gestão de Carcaças - Sandro Silva
 */

// Configurações de conexão com banco de dados
$host = 'localhost';
$dbname = 'carcacas2_0';
$username = 'root';
$password = '';

// Conectar ao banco de dados
try {
    $pdo = new PDO("mysql:host=$host;dbname=$dbname;charset=utf8mb4", $username, $password);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $e) {
    die("Erro na conexão: " . $e->getMessage());
}

// Parâmetros do relatório
$data_inicio = isset($_GET['data_inicio']) ? $_GET['data_inicio'] : date('Y-m-01');
$data_fim = isset($_GET['data_fim']) ? $_GET['data_fim'] : date('Y-m-d');
$animal_tipo = isset($_GET['animal_tipo']) ? $_GET['animal_tipo'] : '';

// Query para buscar dados do relatório
$sql = "
    SELECT 
        dl.id AS dif_id,
        ea.data_abate,
        el.lote AS numero_lote,
        dl.peso AS peso_dif,
        dl.animal_tipo,
        l.fornecedor,
        l.curral,
        l.quantidade_animais,
        l.oc
    FROM 
        dif_limpeza dl
        INNER JOIN escala_lotes el ON dl.escala_lote_id = el.id
        INNER JOIN escala_abate ea ON el.escala_id = ea.id
        LEFT JOIN lotes l ON l.escala_lotes_id = el.id
    WHERE 
        ea.data_abate BETWEEN :data_inicio AND :data_fim
";

if (!empty($animal_tipo)) {
    $sql .= " AND dl.animal_tipo = :animal_tipo";
}

$sql .= " ORDER BY ea.data_abate DESC, el.lote ASC";

$stmt = $pdo->prepare($sql);
$stmt->bindParam(':data_inicio', $data_inicio);
$stmt->bindParam(':data_fim', $data_fim);
if (!empty($animal_tipo)) {
    $stmt->bindParam(':animal_tipo', $animal_tipo);
}
$stmt->execute();
$dados = $stmt->fetchAll(PDO::FETCH_ASSOC);

// Calcular totais
$total_peso = 0;
$total_registros = count($dados);
foreach ($dados as $registro) {
    $total_peso += $registro['peso_dif'];
}
$peso_medio = $total_registros > 0 ? $total_peso / $total_registros : 0;
?>

<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório de DIF - Diferença de Limpeza</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: Arial, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
        }
        
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }
        
        .filters {
            background: #f9f9f9;
            padding: 20px;
            border-radius: 6px;
            margin-bottom: 30px;
            border: 1px solid #e0e0e0;
        }
        
        .filters h3 {
            margin-bottom: 15px;
            color: #444;
            font-size: 18px;
        }
        
        .filter-group {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: flex-end;
        }
        
        .filter-item {
            display: flex;
            flex-direction: column;
        }
        
        .filter-item label {
            margin-bottom: 5px;
            color: #555;
            font-size: 14px;
            font-weight: 600;
        }
        
        .filter-item input,
        .filter-item select {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        
        .btn-filter {
            padding: 9px 20px;
            background: #00a8e8;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: background 0.3s;
        }
        
        .btn-filter:hover {
            background: #0088c2;
        }
        
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .summary-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .summary-card:nth-child(2) {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        
        .summary-card:nth-child(3) {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }
        
        .summary-card h3 {
            font-size: 14px;
            margin-bottom: 10px;
            opacity: 0.9;
        }
        
        .summary-card .value {
            font-size: 28px;
            font-weight: bold;
        }
        
        .summary-card .unit {
            font-size: 12px;
            opacity: 0.8;
        }
        
        .table-container {
            overflow-x: auto;
            margin-top: 20px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }
        
        thead {
            background: #333;
            color: white;
        }
        
        th {
            padding: 12px;
            text-align: left;
            font-weight: 600;
            white-space: nowrap;
        }
        
        tbody tr {
            border-bottom: 1px solid #e0e0e0;
            transition: background 0.2s;
        }
        
        tbody tr:hover {
            background: #f5f5f5;
        }
        
        tbody tr:nth-child(even) {
            background: #fafafa;
        }
        
        tbody tr:nth-child(even):hover {
            background: #f0f0f0;
        }
        
        td {
            padding: 12px;
        }
        
        .no-data {
            text-align: center;
            padding: 40px;
            color: #999;
            font-style: italic;
        }
        
        .print-btn {
            position: fixed;
            bottom: 30px;
            right: 30px;
            padding: 12px 24px;
            background: #28a745;
            color: white;
            border: none;
            border-radius: 50px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            box-shadow: 0 4px 12px rgba(40, 167, 69, 0.4);
            transition: all 0.3s;
        }
        
        .print-btn:hover {
            background: #218838;
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(40, 167, 69, 0.5);
        }
        
        @media print {
            .filters, .print-btn {
                display: none;
            }
            
            body {
                background: white;
                padding: 0;
            }
            
            .container {
                box-shadow: none;
                padding: 0;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Relatório de DIF - Diferença de Limpeza</h1>
        <p class="subtitle">Sistema de Gestão de Carcaças</p>
        
        <div class="filters">
            <h3>Filtros</h3>
            <form method="GET" action="">
                <div class="filter-group">
                    <div class="filter-item">
                        <label for="data_inicio">Data Início:</label>
                        <input type="date" id="data_inicio" name="data_inicio" value="<?php echo htmlspecialchars($data_inicio); ?>">
                    </div>
                    
                    <div class="filter-item">
                        <label for="data_fim">Data Fim:</label>
                        <input type="date" id="data_fim" name="data_fim" value="<?php echo htmlspecialchars($data_fim); ?>">
                    </div>
                    
                    <div class="filter-item">
                        <label for="animal_tipo">Tipo Animal:</label>
                        <select id="animal_tipo" name="animal_tipo">
                            <option value="">Todos</option>
                            <option value="BOI" <?php echo $animal_tipo == 'BOI' ? 'selected' : ''; ?>>Boi</option>
                            <option value="VACA" <?php echo $animal_tipo == 'VACA' ? 'selected' : ''; ?>>Vaca</option>
                            <option value="BEZ" <?php echo $animal_tipo == 'BEZ' ? 'selected' : ''; ?>>Bezerro</option>
                        </select>
                    </div>
                    
                    <button type="submit" class="btn-filter">🔍 Filtrar</button>
                </div>
            </form>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <h3>Total de Registros</h3>
                <div class="value"><?php echo number_format($total_registros, 0, ',', '.'); ?></div>
                <div class="unit">registros</div>
            </div>
            
            <div class="summary-card">
                <h3>Peso Total DIF</h3>
                <div class="value"><?php echo number_format($total_peso, 2, ',', '.'); ?></div>
                <div class="unit">kg</div>
            </div>
            
            <div class="summary-card">
                <h3>Peso Médio DIF</h3>
                <div class="value"><?php echo number_format($peso_medio, 2, ',', '.'); ?></div>
                <div class="unit">kg</div>
            </div>
        </div>
        
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Data Abate</th>
                        <th>Lote</th>
                        <th>Peso DIF (kg)</th>
                        <th>Tipo Animal</th>
                        <th>Fornecedor</th>
                        <th>Curral</th>
                        <th>Qtd Animais</th>
                        <th>OC</th>
                    </tr>
                </thead>
                <tbody>
                    <?php if (count($dados) > 0): ?>
                        <?php foreach ($dados as $row): ?>
                            <tr>
                                <td><?php echo htmlspecialchars($row['dif_id']); ?></td>
                                <td><?php echo date('d/m/Y', strtotime($row['data_abate'])); ?></td>
                                <td><?php echo htmlspecialchars($row['numero_lote']); ?></td>
                                <td><?php echo number_format($row['peso_dif'], 2, ',', '.'); ?></td>
                                <td><?php echo htmlspecialchars($row['animal_tipo']); ?></td>
                                <td><?php echo htmlspecialchars($row['fornecedor']); ?></td>
                                <td><?php echo htmlspecialchars($row['curral']); ?></td>
                                <td><?php echo htmlspecialchars($row['quantidade_animais']); ?></td>
                                <td><?php echo htmlspecialchars($row['oc']); ?></td>
                            </tr>
                        <?php endforeach; ?>
                    <?php else: ?>
                        <tr>
                            <td colspan="9" class="no-data">
                                Nenhum registro encontrado para o período selecionado.
                            </td>
                        </tr>
                    <?php endif; ?>
                </tbody>
            </table>
        </div>
    </div>
    
    <button class="print-btn" onclick="window.print()">🖨️ Imprimir</button>
    
    <script>
        // Auto-submit form on filter change
        document.querySelectorAll('.filters input, .filters select').forEach(element => {
            element.addEventListener('change', function() {
                // Optional: auto-submit on change
                // this.form.submit();
            });
        });
    </script>
</body>
</html>

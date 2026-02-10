-- Relatório de Diferença de Limpeza (DIF)
-- Query para gerar relatório detalhado de diferenças de limpeza
-- Relaciona dados de dif_limpeza com escala de lotes e abate

-- Query 1: Relatório Básico de DIF por Lote
SELECT 
    dl.id AS 'ID DIF',
    dl.escala_lote_id AS 'ID Lote',
    el.lote AS 'Número do Lote',
    dl.peso AS 'Peso DIF (kg)',
    dl.animal_tipo AS 'Tipo Animal',
    ea.data_abate AS 'Data Abate',
    ea.status AS 'Status'
FROM 
    carcacas2_0.dif_limpeza dl
    INNER JOIN carcacas2_0.escala_lotes el ON dl.escala_lote_id = el.id
    INNER JOIN carcacas2_0.escala_abate ea ON el.escala_id = ea.id
ORDER BY 
    ea.data_abate DESC, el.lote ASC;


-- Query 2: Relatório de DIF com Totais por Data
SELECT 
    ea.data_abate AS 'Data Abate',
    COUNT(dl.id) AS 'Qtd Registros',
    SUM(dl.peso) AS 'Peso Total DIF (kg)',
    AVG(dl.peso) AS 'Peso Médio DIF (kg)',
    MIN(dl.peso) AS 'Peso Mínimo (kg)',
    MAX(dl.peso) AS 'Peso Máximo (kg)'
FROM 
    carcacas2_0.dif_limpeza dl
    INNER JOIN carcacas2_0.escala_lotes el ON dl.escala_lote_id = el.id
    INNER JOIN carcacas2_0.escala_abate ea ON el.escala_id = ea.id
GROUP BY 
    ea.data_abate
ORDER BY 
    ea.data_abate DESC;


-- Query 3: Relatório de DIF por Tipo de Animal
SELECT 
    dl.animal_tipo AS 'Tipo Animal',
    COUNT(dl.id) AS 'Qtd Registros',
    SUM(dl.peso) AS 'Peso Total DIF (kg)',
    AVG(dl.peso) AS 'Peso Médio DIF (kg)'
FROM 
    carcacas2_0.dif_limpeza dl
WHERE 
    dl.animal_tipo IS NOT NULL
GROUP BY 
    dl.animal_tipo
ORDER BY 
    SUM(dl.peso) DESC;


-- Query 4: Relatório Detalhado com Informações do Lote
SELECT 
    ea.data_abate AS 'Data Abate',
    el.lote AS 'Lote',
    l.fornecedor AS 'Fornecedor',
    l.curral AS 'Curral',
    l.quantidade_animais AS 'Qtd Animais',
    dl.peso AS 'Peso DIF (kg)',
    dl.animal_tipo AS 'Tipo Animal',
    l.oc AS 'OC'
FROM 
    carcacas2_0.dif_limpeza dl
    INNER JOIN carcacas2_0.escala_lotes el ON dl.escala_lote_id = el.id
    INNER JOIN carcacas2_0.escala_abate ea ON el.escala_id = ea.id
    LEFT JOIN carcacas2_0.lotes l ON l.escala_lotes_id = el.id
ORDER BY 
    ea.data_abate DESC, el.lote ASC;


-- Query 5: Relatório de DIF por Período (exemplo últimos 30 dias)
SELECT 
    ea.data_abate AS 'Data Abate',
    el.lote AS 'Lote',
    dl.peso AS 'Peso DIF (kg)',
    dl.animal_tipo AS 'Tipo Animal',
    l.fornecedor AS 'Fornecedor'
FROM 
    carcacas2_0.dif_limpeza dl
    INNER JOIN carcacas2_0.escala_lotes el ON dl.escala_lote_id = el.id
    INNER JOIN carcacas2_0.escala_abate ea ON el.escala_id = ea.id
    LEFT JOIN carcacas2_0.lotes l ON l.escala_lotes_id = el.id
WHERE 
    ea.data_abate >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
ORDER BY 
    ea.data_abate DESC;


-- Query 6: Relatório de DIF com Ranking de Fornecedores
SELECT 
    l.fornecedor AS 'Fornecedor',
    COUNT(DISTINCT ea.data_abate) AS 'Dias de Abate',
    COUNT(dl.id) AS 'Qtd Registros DIF',
    SUM(dl.peso) AS 'Peso Total DIF (kg)',
    AVG(dl.peso) AS 'Peso Médio DIF (kg)'
FROM 
    carcacas2_0.dif_limpeza dl
    INNER JOIN carcacas2_0.escala_lotes el ON dl.escala_lote_id = el.id
    INNER JOIN carcacas2_0.escala_abate ea ON el.escala_id = ea.id
    LEFT JOIN carcacas2_0.lotes l ON l.escala_lotes_id = el.id
WHERE 
    l.fornecedor IS NOT NULL
GROUP BY 
    l.fornecedor
ORDER BY 
    SUM(dl.peso) DESC;

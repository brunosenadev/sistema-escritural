-- ═══════════════════════════════════════════════════════════════════════
-- CORREÇÃO COMPLEMENTAR — rodar após migracao_banco.sql
-- ═══════════════════════════════════════════════════════════════════════

-- ── PARTE 1: LIKE (artefatos de encoding + variantes de case) ──────────

-- 341 · ITAÚ (qualquer variação com '341' + 'ita')
UPDATE pendentes              SET banco='341 - Banco Itaú' WHERE banco LIKE '341%ita%' AND TRIM(banco)!='341 - Banco Itaú';
UPDATE homologados_cobranca   SET banco='341 - Banco Itaú' WHERE banco LIKE '341%ita%' AND TRIM(banco)!='341 - Banco Itaú';
UPDATE homologados_pagamentos SET banco='341 - Banco Itaú' WHERE banco LIKE '341%ita%' AND TRIM(banco)!='341 - Banco Itaú';
UPDATE homologados_extrato    SET banco='341 - Banco Itaú' WHERE banco LIKE '341%ita%' AND TRIM(banco)!='341 - Banco Itaú';
UPDATE homologados_ext_bancario SET banco='341 - Banco Itaú' WHERE banco LIKE '341%ita%' AND TRIM(banco)!='341 - Banco Itaú';
UPDATE cancelados             SET banco='341 - Banco Itaú' WHERE banco LIKE '341%ita%' AND TRIM(banco)!='341 - Banco Itaú';
UPDATE escritural             SET banco='341 - Banco Itaú' WHERE banco LIKE '341%ita%' AND TRIM(banco)!='341 - Banco Itaú';

-- 0341 prefix também é Itaú
UPDATE pendentes              SET banco='341 - Banco Itaú' WHERE banco LIKE '0341%ita%';
UPDATE homologados_cobranca   SET banco='341 - Banco Itaú' WHERE banco LIKE '0341%ita%';
UPDATE homologados_pagamentos SET banco='341 - Banco Itaú' WHERE banco LIKE '0341%ita%';
UPDATE homologados_extrato    SET banco='341 - Banco Itaú' WHERE banco LIKE '0341%ita%';
UPDATE homologados_ext_bancario SET banco='341 - Banco Itaú' WHERE banco LIKE '0341%ita%';
UPDATE cancelados             SET banco='341 - Banco Itaú' WHERE banco LIKE '0341%ita%';
UPDATE escritural             SET banco='341 - Banco Itaú' WHERE banco LIKE '0341%ita%';

-- ITAÚ sem código ('Banco ItaÃº â 341', ITÃU, etc.)
UPDATE pendentes              SET banco='341 - Banco Itaú' WHERE banco LIKE 'Banco It%341' OR banco LIKE 'Banco It% 341';
UPDATE homologados_cobranca   SET banco='341 - Banco Itaú' WHERE banco LIKE 'Banco It%341' OR banco LIKE 'Banco It% 341';
UPDATE homologados_pagamentos SET banco='341 - Banco Itaú' WHERE banco LIKE 'Banco It%341' OR banco LIKE 'Banco It% 341';
UPDATE homologados_extrato    SET banco='341 - Banco Itaú' WHERE banco LIKE 'Banco It%341' OR banco LIKE 'Banco It% 341';
UPDATE homologados_ext_bancario SET banco='341 - Banco Itaú' WHERE banco LIKE 'Banco It%341' OR banco LIKE 'Banco It% 341';
UPDATE cancelados             SET banco='341 - Banco Itaú' WHERE banco LIKE 'Banco It%341' OR banco LIKE 'Banco It% 341';
UPDATE escritural             SET banco='341 - Banco Itaú' WHERE banco LIKE 'Banco It%341' OR banco LIKE 'Banco It% 341';

-- 237 · BRADESCO (variantes com/sem 'Banco', encoding â = -)
UPDATE pendentes              SET banco='237 - Banco Bradesco' WHERE banco LIKE '237%rad%' AND TRIM(banco)!='237 - Banco Bradesco';
UPDATE homologados_cobranca   SET banco='237 - Banco Bradesco' WHERE banco LIKE '237%rad%' AND TRIM(banco)!='237 - Banco Bradesco';
UPDATE homologados_pagamentos SET banco='237 - Banco Bradesco' WHERE banco LIKE '237%rad%' AND TRIM(banco)!='237 - Banco Bradesco';
UPDATE homologados_extrato    SET banco='237 - Banco Bradesco' WHERE banco LIKE '237%rad%' AND TRIM(banco)!='237 - Banco Bradesco';
UPDATE homologados_ext_bancario SET banco='237 - Banco Bradesco' WHERE banco LIKE '237%rad%' AND TRIM(banco)!='237 - Banco Bradesco';
UPDATE cancelados             SET banco='237 - Banco Bradesco' WHERE banco LIKE '237%rad%' AND TRIM(banco)!='237 - Banco Bradesco';
UPDATE escritural             SET banco='237 - Banco Bradesco' WHERE banco LIKE '237%rad%' AND TRIM(banco)!='237 - Banco Bradesco';

-- 033 · SANTANDER (variantes sem "Banco")
UPDATE pendentes              SET banco='033 - Banco Santander' WHERE banco LIKE '033%ant%' AND TRIM(banco)!='033 - Banco Santander';
UPDATE homologados_cobranca   SET banco='033 - Banco Santander' WHERE banco LIKE '033%ant%' AND TRIM(banco)!='033 - Banco Santander';
UPDATE homologados_pagamentos SET banco='033 - Banco Santander' WHERE banco LIKE '033%ant%' AND TRIM(banco)!='033 - Banco Santander';
UPDATE homologados_extrato    SET banco='033 - Banco Santander' WHERE banco LIKE '033%ant%' AND TRIM(banco)!='033 - Banco Santander';
UPDATE homologados_ext_bancario SET banco='033 - Banco Santander' WHERE banco LIKE '033%ant%' AND TRIM(banco)!='033 - Banco Santander';
UPDATE cancelados             SET banco='033 - Banco Santander' WHERE banco LIKE '033%ant%' AND TRIM(banco)!='033 - Banco Santander';
UPDATE escritural             SET banco='033 - Banco Santander' WHERE banco LIKE '033%ant%' AND TRIM(banco)!='033 - Banco Santander';

-- 001 · BANCO DO BRASIL (variantes de case + ponto final)
UPDATE pendentes              SET banco='001 - Banco do Brasil' WHERE banco LIKE '001%rasil%' AND TRIM(banco)!='001 - Banco do Brasil';
UPDATE homologados_cobranca   SET banco='001 - Banco do Brasil' WHERE banco LIKE '001%rasil%' AND TRIM(banco)!='001 - Banco do Brasil';
UPDATE homologados_pagamentos SET banco='001 - Banco do Brasil' WHERE banco LIKE '001%rasil%' AND TRIM(banco)!='001 - Banco do Brasil';
UPDATE homologados_extrato    SET banco='001 - Banco do Brasil' WHERE banco LIKE '001%rasil%' AND TRIM(banco)!='001 - Banco do Brasil';
UPDATE homologados_ext_bancario SET banco='001 - Banco do Brasil' WHERE banco LIKE '001%rasil%' AND TRIM(banco)!='001 - Banco do Brasil';
UPDATE cancelados             SET banco='001 - Banco do Brasil' WHERE banco LIKE '001%rasil%' AND TRIM(banco)!='001 - Banco do Brasil';
UPDATE escritural             SET banco='001 - Banco do Brasil' WHERE banco LIKE '001%rasil%' AND TRIM(banco)!='001 - Banco do Brasil';

-- BB encoding + / Itaú combo
UPDATE pendentes              SET banco='001 - Banco do Brasil' WHERE banco LIKE 'Banco do Brasil%341';
UPDATE homologados_cobranca   SET banco='001 - Banco do Brasil' WHERE banco LIKE 'Banco do Brasil%341';
UPDATE homologados_pagamentos SET banco='001 - Banco do Brasil' WHERE banco LIKE 'Banco do Brasil%341';
UPDATE homologados_extrato    SET banco='001 - Banco do Brasil' WHERE banco LIKE 'Banco do Brasil%341';
UPDATE homologados_ext_bancario SET banco='001 - Banco do Brasil' WHERE banco LIKE 'Banco do Brasil%341';
UPDATE cancelados             SET banco='001 - Banco do Brasil' WHERE banco LIKE 'Banco do Brasil%341';
UPDATE escritural             SET banco='001 - Banco do Brasil' WHERE banco LIKE 'Banco do Brasil%341';

-- 756 · SICOOB (artefatos de encoding â = -)
UPDATE pendentes              SET banco='756 - Sicoob' WHERE (banco LIKE '756%BANCOOB%' OR banco LIKE '756%Cooperat%' OR banco LIKE '756%CrÃ%') AND TRIM(banco)!='756 - Sicoob';
UPDATE homologados_cobranca   SET banco='756 - Sicoob' WHERE (banco LIKE '756%BANCOOB%' OR banco LIKE '756%Cooperat%' OR banco LIKE '756%CrÃ%') AND TRIM(banco)!='756 - Sicoob';
UPDATE homologados_pagamentos SET banco='756 - Sicoob' WHERE (banco LIKE '756%BANCOOB%' OR banco LIKE '756%Cooperat%' OR banco LIKE '756%CrÃ%') AND TRIM(banco)!='756 - Sicoob';
UPDATE homologados_extrato    SET banco='756 - Sicoob' WHERE (banco LIKE '756%BANCOOB%' OR banco LIKE '756%Cooperat%' OR banco LIKE '756%CrÃ%') AND TRIM(banco)!='756 - Sicoob';
UPDATE homologados_ext_bancario SET banco='756 - Sicoob' WHERE (banco LIKE '756%BANCOOB%' OR banco LIKE '756%Cooperat%' OR banco LIKE '756%CrÃ%') AND TRIM(banco)!='756 - Sicoob';
UPDATE cancelados             SET banco='756 - Sicoob' WHERE (banco LIKE '756%BANCOOB%' OR banco LIKE '756%Cooperat%' OR banco LIKE '756%CrÃ%') AND TRIM(banco)!='756 - Sicoob';
UPDATE escritural             SET banco='756 - Sicoob' WHERE (banco LIKE '756%BANCOOB%' OR banco LIKE '756%Cooperat%' OR banco LIKE '756%CrÃ%') AND TRIM(banco)!='756 - Sicoob';

-- 085 · VIACREDI (case variants)
UPDATE pendentes              SET banco='085 - Viacredi' WHERE banco LIKE '085%via%' AND TRIM(banco)!='085 - Viacredi';
UPDATE homologados_cobranca   SET banco='085 - Viacredi' WHERE banco LIKE '085%via%' AND TRIM(banco)!='085 - Viacredi';
UPDATE homologados_pagamentos SET banco='085 - Viacredi' WHERE banco LIKE '085%via%' AND TRIM(banco)!='085 - Viacredi';
UPDATE homologados_extrato    SET banco='085 - Viacredi' WHERE banco LIKE '085%via%' AND TRIM(banco)!='085 - Viacredi';
UPDATE homologados_ext_bancario SET banco='085 - Viacredi' WHERE banco LIKE '085%via%' AND TRIM(banco)!='085 - Viacredi';
UPDATE cancelados             SET banco='085 - Viacredi' WHERE banco LIKE '085%via%' AND TRIM(banco)!='085 - Viacredi';
UPDATE escritural             SET banco='085 - Viacredi' WHERE banco LIKE '085%via%' AND TRIM(banco)!='085 - Viacredi';

-- ── PARTE 2: mapeamento exato para entradas específicas do resultado ───

CREATE TABLE IF NOT EXISTS _fix (v TEXT, c TEXT);
INSERT INTO _fix VALUES
-- Banco standalone sem código
('274','274 - BMP'),
-- Itaú variantes não pegadas
('ITÃU','341 - Banco Itaú'),
('341-  ITAÃ','341 - Banco Itaú'),
('341 - Banco Itau S.A.','341 - Banco Itaú'),
('2279','341 - Banco Itaú'),
-- Bradesco FIDC patrocinados
('BRADESCO/AILOS','237 - Banco Bradesco'),
('BRADESCO(PROTESTO)','237 - Banco Bradesco'),
('BRADESCO(LIBRA)','237 - Banco Bradesco'),
('BRADESCO(FIDC)','237 - Banco Bradesco'),
('BRADESCO(FACTORY)','237 - Banco Bradesco'),
('BRADESCO - FIDC CREDITISE','237 - Banco Bradesco'),
('BRADESCO - FIDC','237 - Banco Bradesco'),
('BRADESCO (FDIC)','237 - Banco Bradesco'),
('BB - SEC','001 - Banco do Brasil'),
-- FIDC PRIME variantes
('PRIME','FIDC PRIME'),
('237- PRIME FIDC','FIDC PRIME'),
('237 - PRIME FIDC','FIDC PRIME'),
('FDIC (PRIME)','FIDC PRIME'),
-- FIDC RNX variantes
('237 - FIDC RNX','FIDC RNX'),
-- FIDC CREDVALE variantes
('FIDC (CREDVALE)','FIDC CREDVALE'),
('FIDC/CREDVALE','FIDC CREDVALE'),
('FIDIC/ CREDVALE','FIDC CREDVALE'),
('903 - CREDVALE','FIDC CREDVALE'),
-- Codigos errados de banco
('041 - BANCO ITAU','341 - Banco Itaú'),
('756 - ITAU','341 - Banco Itaú'),
('014 - FIDC WALL','FIDC WALL'),
-- Códigos 9xx/8xx/4xx (FIDCs)
('911-BankFundo (BRADESCO)','FIDC'),
('909 - VERTIGO','FIDC'),
('908 - SULBRASIL','FIDC'),
('906 - RED','FIDC'),
('905 - METROPOLITANA','FIDC'),
('904 - DELMONTE','FIDC'),
('902 - BMA','FIDC'),
('900 - ATHENA','FIDC'),
('457 - UY3','FIDC'),
('457-UY3','FIDC'),
('460-UNAVANTI','FIDC'),
('753 - NBC','FIDC'),
('1016 - Redfactor','FIDC'),
('998 - JB CAPITAL SECURITIZADORA S/A','FIDC'),
('997 - REAL','FIDC'),
('997 - INVISTA','FIDC'),
('995 - BELSINOS FIDC','FIDC'),
('994 - BTM SECURITIZADORA DE CREDITOS S/A','FIDC'),
('993 - ALPHA SECURITIZADORA S.A','FIDC'),
('992 - FATORI FINANCAS','FIDC'),
('991 - Tratto Securitizadora S/A','FIDC'),
('990 - NACIONAL INVEST - PERSONALITE','FIDC'),
('989 - RED','FIDC'),
('985 - BANPAR','FIDC'),
('983 - J A SANCHES BISCUOLA ASSESSORIA','FIDC'),
('237 - RDF FIDC','FIDC'),
-- FIDCs pelo nome
('TRUST','FIDC'),('INVISTA','FIDC'),('APOGE','FIDC'),
('VALOREM','FIDC'),('DELMONTE','FIDC'),('CAPITAL','FIDC'),
('BARCELONA','FIDC'),('AVANTE','FIDC'),('HOPE','FIDC'),
('HEIVI','FIDC'),('BANFITA','FIDC'),('ZZA','FIDC'),
('TEMPLI','FIDC'),('SOMA','FIDC'),('SIFRA','FIDC'),
('PLATA','FIDC'),('MATRIZ FIDC','FIDC'),
('FIDC MULTIPLIKE','FIDC'),('FIDC LAKE','FIDC'),
('FIDC B INVEST','FIDC'),('FIDC ATLANTA','FIDC'),
('FIDC ATHENA','FIDC'),('FIDC (BARCELONA)','FIDC'),
('FIDC (ATLANTA)','FIDC'),('FIDC (001-BANCO DO BRASIL)','FIDC'),
('DSX FIDC','FIDC'),('ATHENA','FIDC'),
('C6 BANK TV1 - FIDC','FIDC'),('C6 BANK NETFACTOR','FIDC'),
('PHD FIDC','FIDC'),
('FIDC SUPERNOVA','FIDC'),('FIDC SIFRA','FIDC'),('FIDC PHD','FIDC'),
('FIDC OXSS','FIDC'),('FIDC NP','FIDC'),('FIDC LOTUS','FIDC'),
('FIDC KINERET','FIDC'),('FIDC GARSON -BRADESCO','FIDC'),
('FIDC BMA','FIDC'),('FIDC - SOFISA','FIDC'),('FIDC - MERCHANT','FIDC'),
('FIDC (SIFRA)','FIDC'),('FIDC (PROSPECTA)','FIDC'),
('FIDC (PERSONALITE)','FIDC'),('FIDC (MSUL)','FIDC'),
('FIDC (BRADESCO)','FIDC'),('FIDC (756-SICOOB)','FIDC'),
('FIDC (341-ITAU)','FIDC'),('FIDC  FOSTER 996 (BRADESCO)','FIDC'),
('FIDC VALOREM','FIDC'),('FIDICS','FIDC'),('FIDIC','FIDC'),
('FIDC/TAIPA','FIDC'),('FIDC/RED','FIDC'),('FIDC/LC','FIDC'),
('FIDC/JGM','FIDC'),('FIDC/FMD','FIDC'),('FIDC/DESCONTANET','FIDC'),
('BMA FIDC','FIDC'),('BMA','FIDC'),('BMA - QI TECH','FIDC'),
('MULTIPLIKE FIDC','FIDC'),
('MULTIPLICA','Multiplike'),
('ACREDITAR FIDC SANTAND.','FIDC'),('ACREDITAR FIDC ITAU','FIDC'),
('ALBATROZ - BRADESCO','FIDC'),('ALBATROZ','FIDC'),('AJAXJUD','FIDC'),
('ASSET','FIDC'),('ATF FIDC','FIDC'),('ATF CREDIT','FIDC'),
('ASIA FIDC','FIDC'),('Asia','FIDC'),('APPALOOSA','FIDC'),
('ALPHATRADE','FIDC'),('ALPHA SEC','FIDC'),('BELSINOS FIDC','FIDC'),
('BANPAR','FIDC'),('BANMINAS','FIDC'),
('BRR - MULTI RECEBIVEIS','FIDC'),('BRR - DAYCOVAL','FIDC'),
('C&J','FIDC'),('CAPITAL RS NP','FIDC'),('CAPITAL FIDC','FIDC'),
('CESCE','FIDC'),('CIELO','FIDC'),('CONCILIE','FIDC'),
('DCASH FIDC','FIDC'),('EFETIVA/TECNOTIM','FIDC'),
('FATORI FINANCAS','FIDC'),('FATORI','FIDC'),('FHT','FIDC'),
('FACTORY','FIDC'),('FUNDI','FIDC'),
('GARSON','FIDC'),('GOL','FIDC'),('GOL SECURITIZADORA','FIDC'),
('GRIFFIN CAP.','FIDC'),('HAMPTON','FIDC'),('HM FIDC','FIDC'),
('ICRED','FIDC'),('INDUSEC','FIDC'),('INOVA','FIDC'),('IOSAN','FIDC'),
('KREDITARE','FIDC'),('LARCA CAPITAL','FIDC'),
('LAW','FIDC'),('LAWSEC','FIDC'),('LECCA - 994','FIDC'),
('LEOSEC','FIDC'),('LIBRA FIDC','FIDC'),('LIBRA II NP FIDC','FIDC'),
('LOTUS','FIDC'),('META','FIDC'),('MLBANK','FIDC'),
('NOVA CAPITAL','FIDC'),('ONE7 FIDC','FIDC'),
('ONE7 SECURITIZADORA','FIDC'),('OPHIR FIDC','FIDC'),
('PAGBRASIL','FIDC'),('PERSONALITE','FIDC'),
('REAL','FIDC'),('REAL TIME','FIDC'),('REDFACTOR','FIDC'),
('SB CREDITO FIDC','FIDC'),('SECURITIZADORA','FIDC'),
('SECURITIZADORA FIDEM','FIDC'),('SECURITIZADORA SIFRA','FIDC'),
('SEJA FIDC','FIDC'),('SILVER STONE','FIDC'),('SMR BANK','FIDC'),
('SOLUS','FIDC'),('SOS','FIDC'),('STAR','FIDC'),
('SUNNA','FIDC'),('SUPERNOVA','FIDC'),
('UNAVANTI','FIDC'),('UNIÃO','FIDC'),('UNIQUE','FIDC'),
('XP INVEST.','FIDC'),
('BRASIL SEC','FIDC'),('BRASFOR','FIDC'),
('BARCELONA SEC','FIDC'),
('PHD','274 - BMP'),
('MSUL','FIDC'),
('2279','FIDC'),('114','FIDC'),
-- Bancos específicos não normalizados
('PAGBANK','Pagbank'),
('PAGARME','Pagarme'),
('ORIGINAL','Banco Original'),
-- Pessoas / junk (encoding)
('FlÃ¡vio',''),
('DesirÃ©e Kubischewski',''),
('ANDRÃ IGARASHI CARDOSO DE JESUS',''),
('Aprova',''),
('VYCTOR HUGO QUEIROZ PINTO',''),
('MUNDO INFANTIL STORE COMERCIO DE ROUPAS EIRELLI MIS','');

UPDATE pendentes              SET banco=(SELECT c FROM _fix WHERE v=TRIM(pendentes.banco) LIMIT 1) WHERE TRIM(banco) IN (SELECT v FROM _fix);
UPDATE homologados_cobranca   SET banco=(SELECT c FROM _fix WHERE v=TRIM(homologados_cobranca.banco) LIMIT 1) WHERE TRIM(banco) IN (SELECT v FROM _fix);
UPDATE homologados_pagamentos SET banco=(SELECT c FROM _fix WHERE v=TRIM(homologados_pagamentos.banco) LIMIT 1) WHERE TRIM(banco) IN (SELECT v FROM _fix);
UPDATE homologados_extrato    SET banco=(SELECT c FROM _fix WHERE v=TRIM(homologados_extrato.banco) LIMIT 1) WHERE TRIM(banco) IN (SELECT v FROM _fix);
UPDATE homologados_ext_bancario SET banco=(SELECT c FROM _fix WHERE v=TRIM(homologados_ext_bancario.banco) LIMIT 1) WHERE TRIM(banco) IN (SELECT v FROM _fix);
UPDATE cancelados             SET banco=(SELECT c FROM _fix WHERE v=TRIM(cancelados.banco) LIMIT 1) WHERE TRIM(banco) IN (SELECT v FROM _fix);
UPDATE escritural             SET banco=(SELECT c FROM _fix WHERE v=TRIM(escritural.banco) LIMIT 1) WHERE TRIM(banco) IN (SELECT v FROM _fix);
DROP TABLE IF EXISTS _fix;

-- ── PARTE 3: catch-all para códigos numéricos restantes (FIDCs) ────────
-- Qualquer '9XX - NOME' ou '9XX-NOME' não reconhecido → FIDC

UPDATE pendentes SET banco='FIDC'
WHERE (banco GLOB '[0-9][0-9][0-9] - *' OR banco GLOB '[0-9][0-9][0-9]-*' OR banco GLOB '[0-9][0-9][0-9][0-9] - *')
  AND banco NOT IN (SELECT codigo||' - '||nome FROM bancos_cadastro WHERE codigo!='' AND codigo!='FIDC' AND codigo!='---')
  AND banco NOT IN (SELECT nome FROM bancos_cadastro);

UPDATE homologados_cobranca SET banco='FIDC'
WHERE (banco GLOB '[0-9][0-9][0-9] - *' OR banco GLOB '[0-9][0-9][0-9]-*' OR banco GLOB '[0-9][0-9][0-9][0-9] - *')
  AND banco NOT IN (SELECT codigo||' - '||nome FROM bancos_cadastro WHERE codigo!='' AND codigo!='FIDC' AND codigo!='---')
  AND banco NOT IN (SELECT nome FROM bancos_cadastro);

UPDATE homologados_pagamentos SET banco='FIDC'
WHERE (banco GLOB '[0-9][0-9][0-9] - *' OR banco GLOB '[0-9][0-9][0-9]-*' OR banco GLOB '[0-9][0-9][0-9][0-9] - *')
  AND banco NOT IN (SELECT codigo||' - '||nome FROM bancos_cadastro WHERE codigo!='' AND codigo!='FIDC' AND codigo!='---')
  AND banco NOT IN (SELECT nome FROM bancos_cadastro);

UPDATE homologados_extrato SET banco='FIDC'
WHERE (banco GLOB '[0-9][0-9][0-9] - *' OR banco GLOB '[0-9][0-9][0-9]-*' OR banco GLOB '[0-9][0-9][0-9][0-9] - *')
  AND banco NOT IN (SELECT codigo||' - '||nome FROM bancos_cadastro WHERE codigo!='' AND codigo!='FIDC' AND codigo!='---')
  AND banco NOT IN (SELECT nome FROM bancos_cadastro);

UPDATE homologados_ext_bancario SET banco='FIDC'
WHERE (banco GLOB '[0-9][0-9][0-9] - *' OR banco GLOB '[0-9][0-9][0-9]-*' OR banco GLOB '[0-9][0-9][0-9][0-9] - *')
  AND banco NOT IN (SELECT codigo||' - '||nome FROM bancos_cadastro WHERE codigo!='' AND codigo!='FIDC' AND codigo!='---')
  AND banco NOT IN (SELECT nome FROM bancos_cadastro);

UPDATE cancelados SET banco='FIDC'
WHERE (banco GLOB '[0-9][0-9][0-9] - *' OR banco GLOB '[0-9][0-9][0-9]-*' OR banco GLOB '[0-9][0-9][0-9][0-9] - *')
  AND banco NOT IN (SELECT codigo||' - '||nome FROM bancos_cadastro WHERE codigo!='' AND codigo!='FIDC' AND codigo!='---')
  AND banco NOT IN (SELECT nome FROM bancos_cadastro);

UPDATE escritural SET banco='FIDC'
WHERE (banco GLOB '[0-9][0-9][0-9] - *' OR banco GLOB '[0-9][0-9][0-9]-*' OR banco GLOB '[0-9][0-9][0-9][0-9] - *')
  AND banco NOT IN (SELECT codigo||' - '||nome FROM bancos_cadastro WHERE codigo!='' AND codigo!='FIDC' AND codigo!='---')
  AND banco NOT IN (SELECT nome FROM bancos_cadastro);

-- ── VERIFICAÇÃO FINAL ──────────────────────────────────────────────────
SELECT banco, COUNT(*) as total FROM (
  SELECT banco FROM pendentes
  UNION ALL SELECT banco FROM homologados_cobranca
  UNION ALL SELECT banco FROM homologados_pagamentos
  UNION ALL SELECT banco FROM homologados_extrato
  UNION ALL SELECT banco FROM homologados_ext_bancario
  UNION ALL SELECT banco FROM cancelados
  UNION ALL SELECT banco FROM escritural
)
WHERE banco IS NOT NULL AND banco != ''
  AND banco NOT IN (SELECT codigo||' - '||nome FROM bancos_cadastro WHERE codigo!='' AND codigo!='FIDC' AND codigo!='---')
  AND banco NOT IN (SELECT nome FROM bancos_cadastro)
GROUP BY banco
ORDER BY total DESC

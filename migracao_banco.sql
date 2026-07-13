-- ═════════════════════════════════════════════════════════════════════════
-- MIGRAÇÃO: Normalização do campo banco — 2026-07-07
-- Cole este script inteiro no Editor SQL do Sisplan e execute.
-- ═════════════════════════════════════════════════════════════════════════

-- ─────────────────────────────────────────────────────────────────────────
-- PASSO 1 · Tabela temporária de mapeamento
--   Chave: string exata como está no banco de dados
--   Valor: nome canônico (igual ao texto que o <select> vai gravar)
-- ─────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS _banco_mapa (v TEXT, c TEXT);

-- ── BANCO DO BRASIL ──────────────────────────────────────────────────────
INSERT INTO _banco_mapa VALUES
('BB','001 - Banco do Brasil'),
('001','001 - Banco do Brasil'),
('001-BB','001 - Banco do Brasil'),
('001 - BB','001 - Banco do Brasil'),
('001 -BB','001 - Banco do Brasil'),
('001- BB','001 - Banco do Brasil'),
('001 - BANCO DO BRASIL','001 - Banco do Brasil'),
('001-BANCO DO BRASIL','001 - Banco do Brasil'),
('001 BANCO DO BRASIL','001 - Banco do Brasil'),
('001 - BANCO DO BRASIL.','001 - Banco do Brasil'),
('001-BANCO DO BRASIL SA','001 - Banco do Brasil'),
('001- BANCO DO BRASIL SA','001 - Banco do Brasil'),
('001- BANCO DO BRASIL','001 - Banco do Brasil'),
('001 - BRASIL','001 - Banco do Brasil'),
('001 - Banco do Brasil','001 - Banco do Brasil'),
('001-Banco do Brasil','001 - Banco do Brasil'),
('001 - banco do brasil','001 - Banco do Brasil'),
('001 - Banco do brasil','001 - Banco do Brasil'),
('001- Banco do Brasil','001 - Banco do Brasil'),
('001 - Banco do Brasil SA','001 - Banco do Brasil'),
('BANCO DO BRASIL','001 - Banco do Brasil'),
('Banco do Brasil','001 - Banco do Brasil'),
('BANCO DO BRASIL   001','001 - Banco do Brasil'),
('BANCO DO BRASIL 001-9','001 - Banco do Brasil'),
('Banco do Brasil - 001','001 - Banco do Brasil'),
('Banco do Brasil - 001, Unicred - 136','001 - Banco do Brasil'),
('Banco do Brasil 001 / Itau 341','001 - Banco do Brasil'),
('Banco do Brasil 001','001 - Banco do Brasil');

-- ── ITAÚ ─────────────────────────────────────────────────────────────────
INSERT INTO _banco_mapa VALUES
('ITAU','341 - Banco Itaú'),
('ITAÚ','341 - Banco Itaú'),
('ITAÃ','341 - Banco Itaú'),
('341','341 - Banco Itaú'),
('341 - ITAU','341 - Banco Itaú'),
('341 - ITAÚ','341 - Banco Itaú'),
('341 - ITAÃ','341 - Banco Itaú'),
('341-ITAU','341 - Banco Itaú'),
('341-ITAÚ','341 - Banco Itaú'),
('341 ITAU','341 - Banco Itaú'),
('341 ITAÚ','341 - Banco Itaú'),
('341- ITAU','341 - Banco Itaú'),
('341- ITAÚ','341 - Banco Itaú'),
('341 - BANCO ITAU','341 - Banco Itaú'),
('341 - BANCO ITAÚ','341 - Banco Itaú'),
('341 - BANCO ITAÃ','341 - Banco Itaú'),
('341 - Itau','341 - Banco Itaú'),
('341 itau','341 - Banco Itaú'),
('341 Itau','341 - Banco Itaú'),
('341- itau','341 - Banco Itaú'),
('341- Itau','341 - Banco Itaú'),
('341- Banco ITAU','341 - Banco Itaú'),
('341- BANCO ITAU SA','341 - Banco Itaú'),
('341-BANCO ITAU SA','341 - Banco Itaú'),
('341-BANCO ITAU','341 - Banco Itaú'),
('341--ITAU','341 - Banco Itaú'),
('341-itau','341 - Banco Itaú'),
('ITAU 341','341 - Banco Itaú'),
('ITAU (341)','341 - Banco Itaú'),
('341 BANCO ITAU','341 - Banco Itaú'),
('itau - 341','341 - Banco Itaú'),
('Itau 341','341 - Banco Itaú'),
('0341','341 - Banco Itaú'),
('0341 Banco ItaÃº','341 - Banco Itaú'),
('0341 - Banco ItaÃº','341 - Banco Itaú'),
('034 - Banco ItaÃº','341 - Banco Itaú'),
('184 itau unibanco','341 - Banco Itaú'),
('184 - ITAÚ BBA SA','341 - Banco Itaú'),
('ITAÚ (BOLECODE)','341 - Banco Itaú'),
('Banco ItaÃº â 341','341 - Banco Itaú'),
('341 - Banco ItaÃº','341 - Banco Itaú'),
('341 - ItaÃº','341 - Banco Itaú'),
('341 Banco ItaÃº','341 - Banco Itaú'),
('341-Banco ItaÃº','341 - Banco Itaú'),
('341 - ItaÃº S.A','341 - Banco Itaú'),
('341 -ITAÚ','341 - Banco Itaú'),
('341 -ITAÃ','341 - Banco Itaú'),
('341 - iTAU','341 - Banco Itaú'),
('341 - banco ItaÃº','341 - Banco Itaú'),
('341 - ItaÃº Unibanco','341 - Banco Itaú'),
('341 - ITAÚ UNIBANCO S.A','341 - Banco Itaú'),
('341 ITAÚ UNIBANCO S.A','341 - Banco Itaú'),
('341 -  ItaÃº','341 - Banco Itaú'),
('341 - itaÃº','341 - Banco Itaú'),
('341-ItaÃº','341 - Banco Itaú'),
('341 Banco Itau','341 - Banco Itaú'),
('Banco Itau - 341','341 - Banco Itaú'),
('341 - Itaú S.A','341 - Banco Itaú');

-- ── BRADESCO ──────────────────────────────────────────────────────────────
INSERT INTO _banco_mapa VALUES
('BRADESCO','237 - Banco Bradesco'),
('Bradesco','237 - Banco Bradesco'),
('237','237 - Banco Bradesco'),
('237 - BRADESCO','237 - Banco Bradesco'),
('237-BRADESCO','237 - Banco Bradesco'),
('237- BRADESCO','237 - Banco Bradesco'),
('237 BRADESCO','237 - Banco Bradesco'),
('237 - Bradesco','237 - Banco Bradesco'),
('237-BRADESCO SA','237 - Banco Bradesco'),
('237 - Banco Bradesco','237 - Banco Bradesco'),
('237 Banco Bradesco S.A.','237 - Banco Bradesco'),
('237 BANCO BRADESCO','237 - Banco Bradesco'),
('237 - BANCO BRADESCO','237 - Banco Bradesco'),
('bradesco 237','237 - Banco Bradesco'),
('273-BRADESCO SA','237 - Banco Bradesco'),
('237 -  BRADESCO','237 - Banco Bradesco'),
('237 - Banco Bradesco S.A.','237 - Banco Bradesco'),
('237- Banco Bradesco','237 - Banco Bradesco'),
('237 (WALL FIDC)','237 - Banco Bradesco'),
('BRADESCO (FIDC)','237 - Banco Bradesco'),
('Albatroz 237','237 - Banco Bradesco');

-- ── SANTANDER ─────────────────────────────────────────────────────────────
INSERT INTO _banco_mapa VALUES
('SANTANDER','033 - Banco Santander'),
('Santander','033 - Banco Santander'),
('033','033 - Banco Santander'),
('033 - SANTANDER','033 - Banco Santander'),
('033-SANTANDER','033 - Banco Santander'),
('033 SANTANDER','033 - Banco Santander'),
('033 - banco santander','033 - Banco Santander'),
('033 - Banco Santander','033 - Banco Santander'),
('033 - BANCO SANTANDER','033 - Banco Santander'),
('033- SANTANDER','033 - Banco Santander'),
('033 - SANTANDER S/A','033 - Banco Santander'),
('033 BANCO SANTANDER BRASIL S.A','033 - Banco Santander'),
('33 SANTANDER','033 - Banco Santander'),
('33 - Santander','033 - Banco Santander'),
('33 - SANTANDER','033 - Banco Santander'),
('Santander 033','033 - Banco Santander'),
('033 - Banco Santander S.A.','033 - Banco Santander');

-- ── SICOOB ────────────────────────────────────────────────────────────────
INSERT INTO _banco_mapa VALUES
('SICOOB','756 - Sicoob'),
('Sicoob','756 - Sicoob'),
('sicoob','756 - Sicoob'),
('BANCOOB','756 - Sicoob'),
('756','756 - Sicoob'),
('756 - SICOOB','756 - Sicoob'),
('756-SICOOB','756 - Sicoob'),
('756-0','756 - Sicoob'),
('756- SICOOB','756 - Sicoob'),
('756 sicoob','756 - Sicoob'),
('756 SICOOB','756 - Sicoob'),
('756 - Sicoob','756 - Sicoob'),
('756- Sicoob','756 - Sicoob'),
('Sicoob 756','756 - Sicoob'),
('Sicoob-756','756 - Sicoob'),
('756-Sicoob','756 - Sicoob'),
('756 Sicoob','756 - Sicoob'),
('756 SICCOB','756 - Sicoob'),
('756 - SICCOB','756 - Sicoob'),
('756 - SICOOB SUL','756 - Sicoob'),
('756 - Banco Sicoob','756 - Sicoob'),
('756 - Banco Cooperativo do Brasil S.A','756 - Sicoob'),
('756 - BANCO COOPERATIVO DO BRASIL S.A. (SICOOB)','756 - Sicoob'),
('756 - BANCO COOPERATIVO DO BRASIL S.A','756 - Sicoob'),
('756 - BANCO COOPERATIVO DO BRASIL','756 - Sicoob'),
('756- Sicoob Coopemata','756 - Sicoob'),
('756- sicoob','756 - Sicoob'),
('756-0 SICOOB','756 - Sicoob'),
('756- SICOOB CREDINTER','756 - Sicoob'),
('756 SICOOB ASCICRED','756 - Sicoob'),
('759 - SICOOB','756 - Sicoob'),
('756 - sicoob','756 - Sicoob'),
('756 â BANCOOB','756 - Sicoob'),
('756 Banco Cooperativo Do Brasil S.A','756 - Sicoob'),
('756 - SICOOB ','756 - Sicoob');

-- ── SICREDI ───────────────────────────────────────────────────────────────
INSERT INTO _banco_mapa VALUES
('SICREDI','748 - Sicredi'),
('Sicredi','748 - Sicredi'),
('sicredi','748 - Sicredi'),
('748','748 - Sicredi'),
('748 - SICREDI','748 - Sicredi'),
('748-SICREDI','748 - Sicredi'),
('748 SICREDI','748 - Sicredi'),
('748 sicredi','748 - Sicredi'),
('748 Sicredi','748 - Sicredi'),
('748- SICREDI','748 - Sicredi'),
('748-Sicredi','748 - Sicredi'),
('748 - sicredi','748 - Sicredi'),
('748 - Sicredi','748 - Sicredi'),
('Sicredi - 748','748 - Sicredi'),
('SICREDI 748','748 - Sicredi'),
('0748','748 - Sicredi'),
('748 - BANCO COOPERATIVO SICREDI S.A.','748 - Sicredi'),
('748  SICRED','748 - Sicredi'),
('748 Banco Sicredi','748 - Sicredi'),
('748 - Banco Sicredi','748 - Sicredi'),
('748- Cooperativa Sicredi','748 - Sicredi');

-- ── AILOS ─────────────────────────────────────────────────────────────────
INSERT INTO _banco_mapa VALUES
('AILOS','085 - Ailos'),
('Ailos','085 - Ailos'),
('085','085 - Ailos'),
('085 - AILOS','085 - Ailos'),
('085-AILOS','085 - Ailos'),
('085 -AILOS','085 - Ailos'),
('085 Ailos','085 - Ailos'),
('085 - ailos','085 - Ailos'),
('085 - Ailos','085 - Ailos'),
('085- AILOS','085 - Ailos'),
('085 - COOP CENTRAL AILOS','085 - Ailos'),
('085-Ailos','085 - Ailos'),
('085 - Cooperativa Central de Crédito - Ailos','085 - Ailos');

-- ── VIACREDI ──────────────────────────────────────────────────────────────
INSERT INTO _banco_mapa VALUES
('VIACREDI','085 - Viacredi'),
('Viacredi','085 - Viacredi'),
('VIACRED','085 - Viacredi'),
('085 - VIACREDI','085 - Viacredi'),
('085-VIACREDI','085 - Viacredi'),
('085 viacredi','085 - Viacredi'),
('085 - Viacredi','085 - Viacredi'),
('085 - VIACRED ALTO VALE','085 - Viacredi'),
('085-0 VIACREDI','085 - Viacredi'),
('085-0 - VIACREDI ALTO VALE','085 - Viacredi'),
('085-0 - Ailos/Transpocred','085 - Viacredi'),
('VIACRED ALTO VALE','085 - Viacredi'),
('Homologacao viacredi','085 - Viacredi'),
('Banco: 085-0  - Viacredi','085 - Viacredi'),
('085-0','085 - Viacredi'),
('85 VIACREDI','085 - Viacredi'),
('085- viacred,','085 - Viacredi'),
('VALE CRED','085 - Viacredi');

-- ── TRANSPOCRED ───────────────────────────────────────────────────────────
INSERT INTO _banco_mapa VALUES
('TRANSPOCRED','085 - Transpocred'),
('Transpocred','085 - Transpocred'),
('085 - TRANSPOCRED','085 - Transpocred');

-- ── CEF / CAIXA ───────────────────────────────────────────────────────────
INSERT INTO _banco_mapa VALUES
('CEF','104 - Caixa Econômica Federal'),
('CAIXA','104 - Caixa Econômica Federal'),
('Caixa','104 - Caixa Econômica Federal'),
('104','104 - Caixa Econômica Federal'),
('104 - CEF','104 - Caixa Econômica Federal'),
('104 - Caixa','104 - Caixa Econômica Federal'),
('104-CAIXA ECONÔMICA','104 - Caixa Econômica Federal'),
('104-CAIXA ECONÃMICA','104 - Caixa Econômica Federal'),
('CAIXA ECONOMICA','104 - Caixa Econômica Federal'),
('CAIXA ECONÔMICA','104 - Caixa Econômica Federal'),
('CAIXA ECONÃMICA','104 - Caixa Econômica Federal'),
('104 - CAIXA','104 - Caixa Econômica Federal'),
('CEF-104','104 - Caixa Econômica Federal'),
('104 - Caixa Economica Federal','104 - Caixa Econômica Federal'),
('CAIXA ECONOMICA FEDERAL','104 - Caixa Econômica Federal'),
('003','104 - Caixa Econômica Federal'),
('003 - CAIXA ECONÔMICA FEDERAL','104 - Caixa Econômica Federal'),
('003 - CAIXA ECONÃMICA FEDERAL','104 - Caixa Econômica Federal'),
('104 - Caixa EconÃ´mica / 077 - INTER','104 - Caixa Econômica Federal'),
('104 - Caixa Econômica / 077 - INTER','104 - Caixa Econômica Federal'),
('104 CAIXA ECONÔMICA FEDERAL (CEF)','104 - Caixa Econômica Federal'),
('104 CAIXA ECONÃMICA FEDERAL (CEF)','104 - Caixa Econômica Federal');

-- ── SAFRA ─────────────────────────────────────────────────────────────────
INSERT INTO _banco_mapa VALUES
('SAFRA','422 - Banco Safra'),
('Safra','422 - Banco Safra'),
('422','422 - Banco Safra'),
('422 - SAFRA','422 - Banco Safra'),
('422-SAFRA','422 - Banco Safra'),
('422 -SAFRA','422 - Banco Safra'),
('422 - Safra','422 - Banco Safra'),
('422 - BANCO SAFRA','422 - Banco Safra'),
('422 -  SAFRA','422 - Banco Safra'),
('422- SAFRA','422 - Banco Safra'),
('Safra - 422','422 - Banco Safra'),
('422 - Banco Safra','422 - Banco Safra'),
('SAFRAPAY','422 - Banco Safra');

-- ── UNICRED ───────────────────────────────────────────────────────────────
INSERT INTO _banco_mapa VALUES
('UNICRED','136 - Unicred'),
('Unicred','136 - Unicred'),
('UNICREDI','136 - Unicred'),
('136','136 - Unicred'),
('136 - UNICRED','136 - Unicred'),
('136-UNICRED','136 - Unicred'),
('136 -UNICRED','136 - Unicred'),
('UNICREDI - 136','136 - Unicred'),
('590 - UNICRED','136 - Unicred'),
('136 - Unicred','136 - Unicred');

-- ── CRESOL ────────────────────────────────────────────────────────────────
INSERT INTO _banco_mapa VALUES
('CRESOL','133 - Cresol'),
('Cresol','133 - Cresol'),
('133','133 - Cresol'),
('133 - CRESOL','133 - Cresol'),
('133-CRESOL','133 - Cresol'),
('133- CRESOL','133 - Cresol'),
('133 BANCO CRESOL','133 - Cresol'),
('133 - cresol','133 - Cresol'),
('133 - CRESOL - CRESOL CONFEDERAÇÃO','133 - Cresol'),
('133 - CRESOL - CRESOL CONFEDERAÃÃO','133 - Cresol'),
('CRESOL/BRAD','133 - Cresol'),
('CRESOL - 133','133 - Cresol'),
('133 - Cresol','133 - Cresol');

-- ── DAYCOVAL ──────────────────────────────────────────────────────────────
INSERT INTO _banco_mapa VALUES
('DAYCOVAL','707 - Daycoval'),
('Daycoval','707 - Daycoval'),
('707','707 - Daycoval'),
('707 - DAYCOVAL','707 - Daycoval'),
('707- DAYCOVAL','707 - Daycoval'),
('707 - Banco Daycoval','707 - Daycoval'),
('707 - Daycoval','707 - Daycoval'),
('DAYCOVAL 707-2','707 - Daycoval');

-- ── BANRISUL ──────────────────────────────────────────────────────────────
INSERT INTO _banco_mapa VALUES
('BANRISUL','041 - Banrisul'),
('Banrisul','041 - Banrisul'),
('041 - BANRISUL','041 - Banrisul'),
('041 - Banrisul','041 - Banrisul'),
('041 - Banco do Estado do Rio Grande do Sul','041 - Banrisul'),
('041 - BANCO DO ESTADO DO RIO GRANDE DO SUL','041 - Banrisul'),
('41 - Banrisul','041 - Banrisul'),
('41 - BANRISUL','041 - Banrisul'),
('210 - Banrisul','041 - Banrisul'),
('210 - BANRISUL','041 - Banrisul');

-- ── INTER ─────────────────────────────────────────────────────────────────
INSERT INTO _banco_mapa VALUES
('INTER','077 - Banco Inter'),
('Inter','077 - Banco Inter'),
('BANCO INTER','077 - Banco Inter'),
('077','077 - Banco Inter'),
('077 - INTER','077 - Banco Inter'),
('077-BANCO INTER','077 - Banco Inter'),
('077 - Banco Inter','077 - Banco Inter'),
('INTER 077','077 - Banco Inter'),
('BMA INTER','077 - Banco Inter');

-- ── C6 ────────────────────────────────────────────────────────────────────
INSERT INTO _banco_mapa VALUES
('C6','336 - C6'),
('C6 BANK','336 - C6'),
('336','336 - C6'),
('336 - C6','336 - C6'),
('336-C6 BANK','336 - C6'),
('336 - C6 S.A','336 - C6'),
('Banco C6 336','336 - C6');

-- ── SOFISA ────────────────────────────────────────────────────────────────
INSERT INTO _banco_mapa VALUES
('SOFISA','637 - Sofisa'),
('Sofisa','637 - Sofisa'),
('637 - SOFISA','637 - Sofisa'),
('637 - Sofisa','637 - Sofisa'),
('SOFISA (SANTANDER)','637 - Sofisa');

-- ── BMP / PHD / MONEYPLUS ────────────────────────────────────────────────
INSERT INTO _banco_mapa VALUES
('BMP','274 - BMP'),
('274 - BMP','274 - BMP'),
('274 - PHD','274 - BMP'),
('274 - MONEYPLUS','274 - BMP'),
('274 - Grafeno','274 - BMP'),
('BMP - 274','274 - BMP'),
('MONEY PLUS - 274','274 - BMP'),
('274 - CREDVALE','FIDC CREDVALE');

-- ── VORTX ─────────────────────────────────────────────────────────────────
INSERT INTO _banco_mapa VALUES
('VORTX','310 - Vortx'),
('Vortx','310 - Vortx'),
('310','310 - Vortx'),
('310 - VORTX','310 - Vortx'),
('310 - Vortx','310 - Vortx');

-- ── ASAAS ─────────────────────────────────────────────────────────────────
INSERT INTO _banco_mapa VALUES
('ASAAS','461 - Asaas'),
('Asaas','461 - Asaas'),
('461 - ASAAS','461 - Asaas'),
('461 - Asaas','461 - Asaas'),
('461 Asaas I.P S.A','461 - Asaas');

-- ── BS2 ───────────────────────────────────────────────────────────────────
INSERT INTO _banco_mapa VALUES
('BS2','218 - BS2'),
('218 - BS2','218 - BS2');

-- ── ABC ───────────────────────────────────────────────────────────────────
INSERT INTO _banco_mapa VALUES
('ABC','246 - Banco ABC'),
('BANCO ABC','246 - Banco ABC'),
('ABC BRASIL','246 - Banco ABC'),
('276 - ABC','246 - Banco ABC'),
('246 - ABC','246 - Banco ABC');

-- ── BNB ───────────────────────────────────────────────────────────────────
INSERT INTO _banco_mapa VALUES
('BNB','004 - BNB'),
('004 - BNB','004 - BNB'),
('004 - BANCO DO NORDESTE','004 - BNB');

-- ── BTG PACTUAL ───────────────────────────────────────────────────────────
INSERT INTO _banco_mapa VALUES
('BTG','208 - BTG Pactual'),
('BTG PACTUAL','208 - BTG Pactual'),
('208 - BTG','208 - BTG Pactual');

-- ── BELLUNO ───────────────────────────────────────────────────────────────
INSERT INTO _banco_mapa VALUES
('BELLUNO','Belluno'),
('Belluno','Belluno'),
('901 - BELLUNO','Belluno'),
('990 - BELLUNO','Belluno'),
('BELLUNO FIDC','FIDC BELLUNO');

-- ── CREDVALE FIDC ─────────────────────────────────────────────────────────
INSERT INTO _banco_mapa VALUES
('CREDVALE','FIDC CREDVALE'),
('CREDVALE FIDC','FIDC CREDVALE'),
('CREDIVALE','FIDC CREDVALE'),
('FIDIC/CREDVALE','FIDC CREDVALE'),
('274 - CREDVALE','FIDC CREDVALE');

-- ── FIDC RNX ──────────────────────────────────────────────────────────────
INSERT INTO _banco_mapa VALUES
('RNX FIDC','FIDC RNX'),
('RNX','FIDC RNX'),
('907 - RNX','FIDC RNX'),
('FIDC RNX','FIDC RNX'),
('FIDC (RNX)','FIDC RNX'),
('RNX FIDC (BRADESCO)','FIDC RNX'),
('RNX 444','FIDC RNX'),
('FACTORING(FIDC RNX)','FIDC RNX');

-- ── FIDC OPERA ────────────────────────────────────────────────────────────
INSERT INTO _banco_mapa VALUES
('FIDC/OPERA','FIDC OPERA'),
('OPERA FIDC','FIDC OPERA'),
('FDIC - OPERA','FIDC OPERA'),
('OPERA','FIDC OPERA'),
('Opera','FIDC OPERA'),
('OPERA CAPITAL','FIDC OPERA'),
('237 - OPERA','FIDC OPERA');

-- ── FIDC WALL ─────────────────────────────────────────────────────────────
INSERT INTO _banco_mapa VALUES
('FIDC WALL','FIDC WALL'),
('FIDC WALL (BRADESCO)','FIDC WALL'),
('WALL','FIDC WALL'),
('BRADESCO (WALL)','FIDC WALL'),
('FDIC WALL','FIDC WALL'),
('FDIC (WALL)','FIDC WALL'),
('WALL SEC.','FIDC WALL');

-- ── FIDC PRIME ────────────────────────────────────────────────────────────
INSERT INTO _banco_mapa VALUES
('FIDC PRIME','FIDC PRIME'),
('BRADESCO/FIDC PRIME','FIDC PRIME');

-- ── MULTIPLIKE ────────────────────────────────────────────────────────────
INSERT INTO _banco_mapa VALUES
('MULTIPLIKE','Multiplike'),
('Multiplike','Multiplike');

-- ── FACTORING ─────────────────────────────────────────────────────────────
INSERT INTO _banco_mapa VALUES
('FACTORING','Factoring'),
('factoring','Factoring'),
('factoring - cnab - 400','Factoring');

-- ── FIDC GENÉRICO ─────────────────────────────────────────────────────────
INSERT INTO _banco_mapa VALUES
('FIDC','FIDC');

-- ── NOMES DE PESSOAS → campo vazio ────────────────────────────────────────
INSERT INTO _banco_mapa VALUES
('Marla',''),('MARCOS (TI)',''),('Luiza Pegoraro',''),
('LEONARDO',''),('LETICIA',''),('MARLETE',''),('Marlete',''),
('Roberto Vanzin',''),('Roberto VAnzin',''),('Roberto Vanzini',''),
('GRASIELA ADAM',''),('grasiela adam',''),('GRZIELA ADAM',''),
('Priscila',''),('PRISCILA',''),('PRISCILA FLOSS',''),
('RODRIGO THIESEN',''),('VANDERLEI',''),
('MARILENA MAIA',''),('MARILENA',''),('LILLI THIMOTHEO',''),
('GRASIELA',''),('DRIELY',''),('JEANE',''),('Joana',''),('JOANA',''),
('RODRIGO EDUARDO CUNHA',''),('RIONY SANTOS DE LIMA',''),
('YURI FURTADO',''),('VINICIUS',''),
('Sandro',''),('Rodolfo',''),('RONALDO',''),('ROLENAINE',''),
('RODRIGO',''),('RICARDO',''),('PEDRO MORAUER',''),
('NATIELE',''),('Marcia',''),('MILENA',''),('Milena',''),
('MARILSA KIY',''),('LUIZ CARLOS DEMATE',''),
('Eduardo',''),('EZEQUIEL BORGES',''),
('EUZILANE S. SANTOS LEAL',''),
('Desiree Kubischewski',''),('DesirÃ©e Kubischewski',''),
('Danila',''),('Daiara/Monica',''),('Daiani',''),
('Cristian',''),('Cynthia s theiss',''),
('Catia A. Amorim',''),('Celso Negri',''),
('ADILSON',''),('ALESSANDRA',''),('ALESSANDRA BARCA',''),
('ALFREDO SAUERBRONN SANTANA',''),
('ANDRÈ IGARASHI CARDOSO DE JESUS',''),
('Ana Carolina',''),('ARACIDES',''),
('Estefani (Financeiro)',''),('FABIOLA - FINANCEIRO',''),
('FATIMA',''),('FERNANDO',''),('FERNANDO LUIZ BELLO',''),
('GISELE',''),('Gislaine',''),('IVERTON SCHMITT',''),
('JAIRO',''),('Jonathan Dorow',''),
('JULIETE / SHIRLENE',''),('KARIN THALER',''),
('Luciana Moreira',''),('Marco Aurelio Teixeira Lima',''),
('SR FRANCISCO',''),('Tiago - Externo',''),
('Thiago Caitano Coelho',''),('Tauana/Eduardo',''),
('ANA(COBRANÇA) OU RODRIGO(COMERCIAL)',''),
('Consultou Celso Sisplan',''),('Consultor Celso Sisplan',''),
('CONSULTOR CELSO',''),('FRANCIELE',''),('LEONRADO',''),
('FAIGHUS',''),('Faighus',''),('Fabiana Lima',''),
('dunia damen tannouri de carvalho',''),
('Metal Máquinas Equipamentos LTDA',''),
('ORACON IND E COM DE CONFECÇÕES LTDA',''),
('M SUL',''),('OPHIR',''),
('Kleber André Rosá',''),('Kleber AndrÃ© RosÃ¡',''),
('Z5 DIGITAL',''),('SISPLAN',''),
('--',''),('-',''),('g',''),('1','');

-- ─────────────────────────────────────────────────────────────────────────
-- PASSO 2 · Limpar campos preenchidos com data
-- ─────────────────────────────────────────────────────────────────────────
UPDATE pendentes              SET banco = '' WHERE banco LIKE '20__-__-__%';
UPDATE homologados_cobranca   SET banco = '' WHERE banco LIKE '20__-__-__%';
UPDATE homologados_pagamentos SET banco = '' WHERE banco LIKE '20__-__-__%';
UPDATE homologados_extrato    SET banco = '' WHERE banco LIKE '20__-__-__%';
UPDATE homologados_ext_bancario SET banco = '' WHERE banco LIKE '20__-__-__%';
UPDATE cancelados             SET banco = '' WHERE banco LIKE '20__-__-__%';
UPDATE escritural             SET banco = '' WHERE banco LIKE '20__-__-__%';
UPDATE pendentes              SET banco = '' WHERE banco LIKE '__/__/____';
UPDATE homologados_cobranca   SET banco = '' WHERE banco LIKE '__/__/____';
UPDATE homologados_pagamentos SET banco = '' WHERE banco LIKE '__/__/____';
UPDATE homologados_extrato    SET banco = '' WHERE banco LIKE '__/__/____';
UPDATE homologados_ext_bancario SET banco = '' WHERE banco LIKE '__/__/____';
UPDATE cancelados             SET banco = '' WHERE banco LIKE '__/__/____';
UPDATE escritural             SET banco = '' WHERE banco LIKE '__/__/____';

-- ─────────────────────────────────────────────────────────────────────────
-- PASSO 3 · Aplicar mapeamentos em todas as tabelas
-- ─────────────────────────────────────────────────────────────────────────
UPDATE pendentes SET banco = (
    SELECT c FROM _banco_mapa WHERE v = TRIM(pendentes.banco) LIMIT 1
) WHERE TRIM(banco) IN (SELECT v FROM _banco_mapa);

UPDATE homologados_cobranca SET banco = (
    SELECT c FROM _banco_mapa WHERE v = TRIM(homologados_cobranca.banco) LIMIT 1
) WHERE TRIM(banco) IN (SELECT v FROM _banco_mapa);

UPDATE homologados_pagamentos SET banco = (
    SELECT c FROM _banco_mapa WHERE v = TRIM(homologados_pagamentos.banco) LIMIT 1
) WHERE TRIM(banco) IN (SELECT v FROM _banco_mapa);

UPDATE homologados_extrato SET banco = (
    SELECT c FROM _banco_mapa WHERE v = TRIM(homologados_extrato.banco) LIMIT 1
) WHERE TRIM(banco) IN (SELECT v FROM _banco_mapa);

UPDATE homologados_ext_bancario SET banco = (
    SELECT c FROM _banco_mapa WHERE v = TRIM(homologados_ext_bancario.banco) LIMIT 1
) WHERE TRIM(banco) IN (SELECT v FROM _banco_mapa);

UPDATE cancelados SET banco = (
    SELECT c FROM _banco_mapa WHERE v = TRIM(cancelados.banco) LIMIT 1
) WHERE TRIM(banco) IN (SELECT v FROM _banco_mapa);

UPDATE escritural SET banco = (
    SELECT c FROM _banco_mapa WHERE v = TRIM(escritural.banco) LIMIT 1
) WHERE TRIM(banco) IN (SELECT v FROM _banco_mapa);

-- ─────────────────────────────────────────────────────────────────────────
-- PASSO 4 · Remover tabela temporária
-- ─────────────────────────────────────────────────────────────────────────
DROP TABLE IF EXISTS _banco_mapa;

-- ─────────────────────────────────────────────────────────────────────────
-- PASSO 5 · Inserir bancos novos no cadastro (WHERE NOT EXISTS = idempotente)
-- ─────────────────────────────────────────────────────────────────────────
INSERT INTO bancos_cadastro (codigo,nome,tem_api,ordem) SELECT '085','Viacredi',1,7 WHERE NOT EXISTS (SELECT 1 FROM bancos_cadastro WHERE nome='Viacredi');
INSERT INTO bancos_cadastro (codigo,nome,tem_api,ordem) SELECT '085','Transpocred',0,8 WHERE NOT EXISTS (SELECT 1 FROM bancos_cadastro WHERE nome='Transpocred');
INSERT INTO bancos_cadastro (codigo,nome,tem_api,ordem) SELECT '004','BNB',0,18 WHERE NOT EXISTS (SELECT 1 FROM bancos_cadastro WHERE nome='BNB');
INSERT INTO bancos_cadastro (codigo,nome,tem_api,ordem) SELECT '208','BTG Pactual',0,19 WHERE NOT EXISTS (SELECT 1 FROM bancos_cadastro WHERE nome='BTG Pactual');
INSERT INTO bancos_cadastro (codigo,nome,tem_api,ordem) SELECT '218','BS2',0,20 WHERE NOT EXISTS (SELECT 1 FROM bancos_cadastro WHERE nome='BS2');
INSERT INTO bancos_cadastro (codigo,nome,tem_api,ordem) SELECT '246','Banco ABC',0,21 WHERE NOT EXISTS (SELECT 1 FROM bancos_cadastro WHERE nome='Banco ABC');
INSERT INTO bancos_cadastro (codigo,nome,tem_api,ordem) SELECT '274','BMP',0,22 WHERE NOT EXISTS (SELECT 1 FROM bancos_cadastro WHERE nome='BMP');
INSERT INTO bancos_cadastro (codigo,nome,tem_api,ordem) SELECT '310','Vortx',0,23 WHERE NOT EXISTS (SELECT 1 FROM bancos_cadastro WHERE nome='Vortx');
INSERT INTO bancos_cadastro (codigo,nome,tem_api,ordem) SELECT '336','C6',0,24 WHERE NOT EXISTS (SELECT 1 FROM bancos_cadastro WHERE nome='C6');
INSERT INTO bancos_cadastro (codigo,nome,tem_api,ordem) SELECT '461','Asaas',0,25 WHERE NOT EXISTS (SELECT 1 FROM bancos_cadastro WHERE nome='Asaas');
INSERT INTO bancos_cadastro (codigo,nome,tem_api,ordem) SELECT '637','Sofisa',0,26 WHERE NOT EXISTS (SELECT 1 FROM bancos_cadastro WHERE nome='Sofisa');
INSERT INTO bancos_cadastro (codigo,nome,tem_api,ordem) SELECT '707','Daycoval',0,27 WHERE NOT EXISTS (SELECT 1 FROM bancos_cadastro WHERE nome='Daycoval');
INSERT INTO bancos_cadastro (codigo,nome,tem_api,ordem) SELECT 'FIDC','FIDC RNX',0,50 WHERE NOT EXISTS (SELECT 1 FROM bancos_cadastro WHERE nome='FIDC RNX');
INSERT INTO bancos_cadastro (codigo,nome,tem_api,ordem) SELECT 'FIDC','FIDC OPERA',0,51 WHERE NOT EXISTS (SELECT 1 FROM bancos_cadastro WHERE nome='FIDC OPERA');
INSERT INTO bancos_cadastro (codigo,nome,tem_api,ordem) SELECT 'FIDC','FIDC WALL',0,52 WHERE NOT EXISTS (SELECT 1 FROM bancos_cadastro WHERE nome='FIDC WALL');
INSERT INTO bancos_cadastro (codigo,nome,tem_api,ordem) SELECT 'FIDC','FIDC PRIME',0,53 WHERE NOT EXISTS (SELECT 1 FROM bancos_cadastro WHERE nome='FIDC PRIME');
INSERT INTO bancos_cadastro (codigo,nome,tem_api,ordem) SELECT 'FIDC','FIDC CREDVALE',0,54 WHERE NOT EXISTS (SELECT 1 FROM bancos_cadastro WHERE nome='FIDC CREDVALE');
INSERT INTO bancos_cadastro (codigo,nome,tem_api,ordem) SELECT 'FIDC','FIDC BELLUNO',0,55 WHERE NOT EXISTS (SELECT 1 FROM bancos_cadastro WHERE nome='FIDC BELLUNO');
INSERT INTO bancos_cadastro (codigo,nome,tem_api,ordem) SELECT '---','Belluno',0,56 WHERE NOT EXISTS (SELECT 1 FROM bancos_cadastro WHERE nome='Belluno');
INSERT INTO bancos_cadastro (codigo,nome,tem_api,ordem) SELECT '---','Multiplike',0,57 WHERE NOT EXISTS (SELECT 1 FROM bancos_cadastro WHERE nome='Multiplike');
INSERT INTO bancos_cadastro (codigo,nome,tem_api,ordem) SELECT '---','Factoring',0,58 WHERE NOT EXISTS (SELECT 1 FROM bancos_cadastro WHERE nome='Factoring');
INSERT INTO bancos_cadastro (codigo,nome,tem_api,ordem) SELECT 'FIDC','FIDC',0,59 WHERE NOT EXISTS (SELECT 1 FROM bancos_cadastro WHERE nome='FIDC');

-- ─────────────────────────────────────────────────────────────────────────
-- PASSO 6 · Verificação: mostra o que ainda não foi normalizado
-- (resultado vazio = sucesso total)
-- ─────────────────────────────────────────────────────────────────────────
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
  AND banco NOT IN (SELECT codigo || ' - ' || nome FROM bancos_cadastro WHERE codigo != '' AND codigo != 'FIDC')
  AND banco NOT IN (SELECT nome FROM bancos_cadastro)
GROUP BY banco
ORDER BY total DESC

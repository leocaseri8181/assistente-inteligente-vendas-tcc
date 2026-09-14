# Assistente inteligente para análise de vendas

Protótipo e material de pesquisa do TCC de Leonardo Caseri. O produto importa dados comerciais, valida sua qualidade e prepara indicadores e oportunidades para análise. A priorização por aprendizado de máquina permanece experimental.

Repositório do projeto: https://github.com/leocaseri8181/assistente-inteligente-vendas-tcc

## Estado atual

- Base fictícia Maven obtida de um espelho público com revisão e hashes fixados.
- Auditoria reproduzível e limitações documentadas.
- Esquema SQLite multiempresa e importador idempotente.
- Experimento retrospectivo com separação temporal, baseline, regressão logística e árvore de decisão.
- Primeira API e dashboard local implementados, incluindo envio atômico dos quatro CSVs pela interface.
- Projeto remoto `PROJETO_TCC_VIGENTE` criado no Supabase em São Paulo e seis migrations aplicadas ao PostgreSQL 17, com sete tabelas protegidas por RLS, 24 políticas, papéis por empresa e criação segura da primeira organização no cadastro.
- Autenticação Supabase integrada ao FastAPI e à interface por cookies HttpOnly, com importação restrita a `owner` e `admin`.
- Adaptador PostgreSQL implementado para indicadores, fila e importação transacional dos quatro CSVs; a ativação definitiva depende da criação da primeira conta e da carga real pelo fluxo da aplicação.
- LLM, avaliação com usuários e deploy ainda não foram implementados.

## Texto acadêmico em elaboração

- [Entrega parcial consolidada em Word](tcc_texto/TCC_Leonardo_Caseri_Parcial_ABNT.docx)
- [Resumo e abstract parciais](tcc_texto/RESUMO_PARCIAL.md)
- [Introdução parcial](tcc_texto/INTRODUCAO_PARCIAL.md)
- [Desenvolvimento e avaliação parcial](tcc_texto/DESENVOLVIMENTO_PARCIAL.md)
- [Fundamentação teórica parcial](tcc_texto/FUNDAMENTACAO_TEORICA_PARCIAL.md)
- [Cronograma da entrega parcial](planejamento/CRONOGRAMA_PARCIAL.md)

## Reproduzir

No PowerShell, a partir da pasta do projeto:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
.venv\Scripts\python.exe scripts\download_data.py
.venv\Scripts\python.exe scripts\audit_data.py
.venv\Scripts\python.exe scripts\import_maven.py
.venv\Scripts\python.exe scripts\run_experiment.py
$env:PYTHONPATH = "src"
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe scripts\run_app.py
```

Depois do último comando, abra `http://127.0.0.1:8000`. A documentação interativa da API fica em `http://127.0.0.1:8000/docs`.

Os CSVs brutos e o banco local não são versionados. O manifesto contém origem, revisão, tamanho e SHA-256 de cada arquivo. O download utiliza somente cinco CSVs de uma revisão fixada; não executa código do espelho.

A preparação da persistência de produção está documentada em [Migração para Supabase](planejamento/MIGRACAO_SUPABASE.md). Para executar com autenticação, copie `.env.example` para `.env`, informe a URL e a chave publicável do projeto e use `TCC_DATA_BACKEND=supabase`. Use `sqlite` para a demonstração local reproduzível. A chave secreta de serviço não deve ser usada no navegador nem neste fluxo de login.

## Interpretação

A fonte oficial descreve o conjunto como dados B2B de uma empresa fictícia e declara licença Public Domain. O espelho utilizado não foi comparado byte a byte com um download oficial autenticado. Ele é adequado à demonstração técnica, não à validação de impacto comercial.

O experimento prevê `Won` ou `Lost` no instante registrado como entrada em `Engaging`. Campos posteriores ao resultado são excluídos. O teste final é posterior ao treino. Como os modelos não apresentaram ganho relevante sobre a prevalência no teste temporal inicial, o protótipo não deve anunciar suas pontuações como probabilidades confiáveis para clientes.

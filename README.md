# Zyncash

Aplicação web para controle financeiro diário, pensada para as pessoas que desejam saber de onde o seu dinheiro está saindo e para onde ele está indo. 

## Tecnologias utilizadas

- **Python**
- **Streamlit** — interface web
- **SQLite** — banco de dados local, com tabelas de usuários, lançamentos e sugestões
- **Pandas** — agregações, agrupamentos e filtros por período
- **Matplotlib** — geração dos gráficos
- **ReportLab** — geração dos relatórios em PDF

## Estrutura do projeto

```
zyncash/
├── app.py              # Interface (Streamlit): login, formulário, tabela, menu de opções
├── database.py         # Acesso ao banco de dados (SQLite)
├── analise.py          # Cálculos, agrupamentos e filtros por período (pandas)
├── relatorio_pdf.py    # Geração dos relatórios em PDF (tabela e gráficos)
├── requirements.txt    # Dependências do projeto
├── .streamlit/
│   └── config.toml     # Configuração da interface do Streamlit
└── README.md
```

A separação em módulos foi intencional: `database.py` cuida só de salvar/buscar dados, `analise.py` cuida só dos cálculos, `relatorio_pdf.py` cuida só da geração de PDF, e `app.py` cuida só da interface. Isso facilita testar e expandir cada parte sem afetar as outras.

## Como rodar localmente

```bash
# 1. Clone o repositório
git clone https://github.com/sxbrinz/Zyncash.git
cd Zyncash

# 2. Crie e ative um ambiente virtual
python3 -m venv venv
source venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Execute a aplicação
streamlit run app.py
```

O navegador abrirá automaticamente em `http://localhost:8501`.

## Autora

Sabrina Teixeira — estudante de Ciência da Computação na UFOP
[LinkedIn](https://www.linkedin.com/in/sabrinateixeiradasilva)

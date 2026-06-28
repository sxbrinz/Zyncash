# 💰 Zyncash

Aplicação web para controle financeiro diário, pensada para qualquer pessoa que precise saber, de forma simples, quanto entrou, quanto saiu e quanto sobrou no fim do dia — com uma interface pensada para ser acessível também a usuários menos familiarizados com tecnologia.

## A ideia

Quem trabalha por conta própria (motoboys, freelancers, autônomos em geral) costuma lidar com entradas e saídas de dinheiro o dia inteiro, mas raramente tem um controle claro de quanto realmente sobra no fim do dia, da semana ou do mês. O Zyncash resolve isso com:

- Login simples e direto, com cadastro como ação secundária
- Registro rápido de cada lançamento (entrada ou saída), com categoria e descrição
- Campo de valor com máscara monetária automática (estilo caixa eletrônico)
- Indicador visual discreto (🟢 entrada / 🔴 saída) em vez de linhas coloridas
- Edição e exclusão de lançamentos já cadastrados
- Resumo e gráficos com filtro por dia, semana, mês ou sem filtro, organizados em um menu de opções
- Download de relatórios em PDF (tabela de lançamentos e gráficos, separadamente)
- Caixa de sugestões para os usuários enviarem ideias de melhoria

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

## Próximos passos (ideias de evolução)

- [ ] Domínio próprio (zyncash.com)
- [ ] Envio de sugestões também por e-mail
- [ ] Categorias personalizadas por usuário
- [ ] Alertas quando os gastos do mês superarem um limite definido pelo usuário

## Autora

Sabrina Teixeira da Silva — estudante de Ciência da Computação na UFOP
[LinkedIn](https://www.linkedin.com/in/sabrinateixeiradasilva)

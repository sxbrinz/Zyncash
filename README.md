# Zyncash   

Aplicação web para controle financeiro diário, pensada para quem trabalha e precisa saber, de forma simples, quanto entrou, quanto saiu e quanto sobrou no fim do dia.

## A ideia

Quem trabalha costuma lidar com entradas e saídas de dinheiro o dia inteiro, mas raramente tem um controle claro de quanto realmente sobra no fim do dia, da semana ou do mês. O Zyncash resolve isso com:

- Registro rápido de cada lançamento (entrada ou saída), com categoria e descrição
- Tabela colorida: **verde** para entradas, **vermelho** para saídas
- Resumo automático: total recebido, total gasto e lucro líquido
- Gráficos de saldo por dia, semana e mês
- Gráfico de distribuição de gastos por categoria
- Sistema de login simples, para que cada pessoa veja apenas os próprios dados

## Tecnologias utilizadas

- **Python**
- **Streamlit** — interface web
- **SQLite** — banco de dados local, com tabelas de usuários e lançamentos
- **Pandas** — agregações e agrupamentos por período (análise de dados)
- **Matplotlib** — geração dos gráficos

## Estrutura do projeto

```
Zyncash/
├── app.py            # Interface (Streamlit): login, formulário, tabela e gráficos
├── database.py       # Acesso ao banco de dados (SQLite)
├── analise.py         # Cálculos e agrupamentos (pandas)
├── requirements.txt   # Dependências do projeto
└── README.md
```

A separação em três arquivos foi intencional: `database.py` cuida só de salvar/buscar dados, `analise.py` cuida só dos cálculos, e `app.py` cuida só da interface. Isso facilita testar e expandir cada parte sem afetar as outras.

## Como rodar localmente

```bash
# 1. Clone o repositório
git clone https://github.com/SEU-USUARIO/girodiario.git
cd girodiario

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Execute a aplicação
streamlit run app.py
```

O navegador abrirá automaticamente em `http://localhost:8501`.

## Próximos passos (ideias de evolução)

- [ ] Exportar relatório mensal em PDF
- [ ] Editar lançamentos já cadastrados (atualmenre só é possível excluir)
- [ ] Permitir categorias personalizadas por usuário
- [ ] Alertas quando os gastos do mês superarem um limite definido pelo usuário

## Autora

Sabrina Teixeira da Silva — estudante de Ciência da Computação na UFOP
[LinkedIn](https://www.linkedin.com/in/sabrinateixeiradasilva)

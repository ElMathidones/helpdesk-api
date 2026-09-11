# Help Desk API

API REST para gerenciamento de chamados de suporte técnico, desenvolvida
com FastAPI, PostgreSQL, SQLAlchemy e autenticação JWT.

## Tecnologias

-   Python 3.14
-   FastAPI
-   PostgreSQL
-   SQLAlchemy
-   Alembic
-   Pydantic
-   JWT
-   Argon2
-   Docker
-   Pytest
-   Ruff
-   Black

## Funcionalidades

-   Cadastro de usuários
-   Autenticação com JWT
-   Controle de acesso por perfil
    -   Admin
    -   Technician
    -   Customer
-   Gerenciamento de categorias
-   Criação de chamados
-   Listagem de chamados
-   Consulta de chamado por ID
-   Atribuição de responsável
-   Controle de status do chamado
-   Regras de transição de status
-   Controle de acesso entre clientes
-   Testes automatizados

## Estrutura do projeto

``` text
helpdesk-api/
├── alembic/
├── app/
│   ├── api/
│   │   └── routes/
│   ├── core/
│   ├── db/
│   ├── dependencies/
│   ├── models/
│   ├── repositories/
│   ├── schemas/
│   ├── services/
│   └── main.py
├── tests/
├── .env.example
├── alembic.ini
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
└── requirements-dev.txt
```

## Pré-requisitos

Antes de executar o projeto, tenha instalado:

-   Python 3.14
-   Docker
-   Docker Compose
-   Git

## Configuração do ambiente

Clone o repositório:

``` bash
git clone <URL_DO_REPOSITORIO>
cd helpdesk-api
```

Crie o ambiente virtual:

### Windows PowerShell

``` powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Instale as dependências:

``` powershell
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

## Variáveis de ambiente

Copie o arquivo de exemplo:

``` powershell
Copy-Item .env.example .env
```

Exemplo de configuração:

``` env
APP_NAME=Help Desk API
APP_VERSION=0.1.0
DEBUG=true

DATABASE_URL=postgresql+psycopg://helpdesk:helpdesk@localhost:5432/helpdesk

JWT_SECRET_KEY=change-this-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

> Em ambientes reais, utilize uma chave JWT segura e nunca versione o
> arquivo `.env`.

## Banco de dados

Suba o PostgreSQL com Docker:

``` powershell
docker compose up -d
```

Verifique os containers:

``` powershell
docker compose ps
```

Execute as migrations:

``` powershell
python -m alembic upgrade head
```

## Executando a API

``` powershell
python -m uvicorn app.main:app --reload
```

A aplicação ficará disponível em:

``` text
http://127.0.0.1:8000
```

Swagger:

``` text
http://127.0.0.1:8000/docs
```

OpenAPI:

``` text
http://127.0.0.1:8000/openapi.json
```

## Autenticação

A API utiliza autenticação JWT no padrão Bearer Token.

Fluxo básico:

1.  Crie um usuário em `POST /users`.
2.  Faça login em `POST /auth/login`.
3.  Utilize o token retornado nas rotas protegidas.

No Swagger, utilize o botão **Authorize**.

O campo `username` do formulário de autenticação deve receber o e-mail
do usuário.

## Perfis de acesso

### Customer

-   Pode criar chamados.
-   Pode visualizar seus próprios chamados.
-   Não pode criar categorias.
-   Não pode assumir chamados.
-   Não pode alterar status de chamados.

### Technician

-   Pode visualizar chamados.
-   Pode assumir chamados.
-   Pode alterar status de chamados.

### Admin

-   Possui acesso administrativo.
-   Pode criar categorias.
-   Pode visualizar todos os chamados.
-   Pode assumir chamados.
-   Pode alterar status de chamados.

## Status dos chamados

Os chamados podem utilizar os seguintes status:

``` text
open
under_review
in_progress
resolved
closed
canceled
```

As transições são controladas pela aplicação.

Exemplo de fluxo:

``` text
open
  ↓
in_progress
  ↓
resolved
  ↓
closed
```

Chamados fechados não podem retornar para estados anteriores.

## Testes

Execute:

``` powershell
python -m pytest
```

Também é possível verificar qualidade e formatação:

``` powershell
python -m ruff check .
python -m black --check .
```

Atualmente o projeto possui testes automatizados cobrindo:

-   cadastro de usuários
-   autenticação
-   credenciais inválidas
-   usuários inativos
-   categorias
-   RBAC
-   criação de chamados
-   isolamento entre clientes
-   atribuição de chamados
-   transições de status
-   cenários de erro

## Ambiente de desenvolvimento

Para instalar apenas as dependências necessárias para executar a
aplicação:

``` powershell
python -m pip install -r requirements.txt
```

Para desenvolvimento e testes:

``` powershell
python -m pip install -r requirements-dev.txt
```

## Parando o banco

``` powershell
docker compose down
```

Para também remover os dados locais do PostgreSQL:

``` powershell
docker compose down -v
```

> O comando com `-v` remove o volume do banco e apaga os dados locais.

## Licença

Projeto desenvolvido para fins de estudo e portfólio.

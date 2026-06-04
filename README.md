# ⚙️ SetupMaker

> Plataforma web para montagem e comparação de PCs customizados, desenvolvida com Flask e arquitetura MVC.

---

## 📋 Sobre o Projeto

O **SetupMaker** resolve um problema real: a dificuldade de montar um PC compatível e com o melhor custo-benefício. A plataforma permite que usuários selecionem componentes com verificação automática de compatibilidade, comparem preços em diferentes lojas, estimem desempenho em jogos e compartilhem suas configurações com a comunidade.

---

## 🚀 Funcionalidades

### 🔐 Autenticação e Segurança
- Cadastro com **verificação de e-mail** obrigatória (código de 6 dígitos)
- Login com **autenticação em dois fatores (2FA)** via e-mail
- Alteração de senha com validação de senha forte
- Página de configurações do perfil
- Logout seguro com encerramento de sessão

### 🛡️ Segurança da Aplicação
| Proteção | Implementação |
|----------|---------------|
| **CSRF** | Tokens em todos os formulários via `Flask-WTF` |
| **XSS** | Escape automático pelo template engine `Jinja2` |
| **SQL Injection** | Consultas parametrizadas via `SQLAlchemy` |
| **Senhas** | Hash com `werkzeug.security` (pbkdf2:sha256) |
| **API** | Autenticação via `JWT` (JSON Web Token) |
| **Sessões** | Controle de acesso por rota com `Flask-Login` |

### 🖥️ Montagem de PCs
- Seleção de peças por categoria (CPU, GPU, RAM, Placa-Mãe, SSD, Fonte, Gabinete, Cooler)
- **Verificação automática de compatibilidade** em tempo real:
  - Socket CPU ↔ Placa-Mãe
  - Tipo de RAM (DDR4/DDR5) ↔ Placa-Mãe
  - Consumo total ↔ Wattage da fonte
- Cálculo de **consumo energético** total da build
- **Estimativa de FPS** em jogos populares (Valorant, CS2, GTA V, etc.)
- Salvar, editar e excluir builds
- Compartilhar builds publicamente

### 💰 Comparador de Preços
- Intervalo de preços estimado por peça
- Links diretos para busca nas lojas: **Pichau, KaBuM!, TerabyteShop, Amazon BR, Mercado Livre e AliExpress**
- Sistema para o usuário informar preços encontrados nas lojas
- Comparação automática do menor preço

### ⭐ Avaliações e Comunidade
- Avaliar peças e builds com nota e comentário
- Ranking de melhores builds da comunidade
- Feed de builds públicas

### 🛠️ Painel Administrativo
- Gerenciar usuários
- Cadastrar, editar e excluir produtos
- Gerenciar builds da plataforma

### 🔌 API REST com JWT
- Endpoints protegidos por token JWT
- Documentação disponível em `/api/docs`

---

## 🛠️ Tecnologias Utilizadas

### Backend
- **Python 3.11+**
- **Flask** — framework web
- **Flask-SQLAlchemy** — ORM para banco de dados
- **Flask-Migrate** — migrações de banco
- **Flask-Login** — gerenciamento de sessões
- **Flask-JWT-Extended** — autenticação JWT para API
- **Flask-WTF** — proteção CSRF
- **Flask-Mail** — envio de e-mails (2FA e verificação)
- **Werkzeug** — hash de senhas

### Frontend
- **HTML5 + CSS3**
- **Bootstrap 5**
- **Bootstrap Icons**
- **JavaScript** (vanilla)
- **Google Fonts** (Rajdhani + Inter)

### Banco de Dados
- **SQLite** (desenvolvimento)
- **PostgreSQL** (produção)

---

## 📁 Estrutura do Projeto (MVC)

```
setupmaker/
│
├── app/
│   ├── models/              # Model — banco de dados (SQLAlchemy)
│   │   ├── user.py          # Usuário com 2FA e verificação de e-mail
│   │   ├── produto.py       # Produto e Categoria
│   │   ├── build.py         # Build de PC
│   │   ├── loja.py          # Loja e Preço
│   │   └── avaliacao.py     # Avaliação e Favorito
│   │
│   ├── routes/              # Controller — lógica de negócio
│   │   ├── auth.py          # Registro, login, 2FA, senha
│   │   ├── builds.py        # CRUD de builds + compatibilidade
│   │   ├── produtos.py      # Listagem e detalhe de peças
│   │   ├── avaliacoes.py    # Sistema de avaliações
│   │   ├── admin.py         # Painel administrativo
│   │   └── main.py          # Página inicial e comparador
│   │
│   ├── templates/           # View — interface (Jinja2 + Bootstrap 5)
│   │   ├── base.html        # Layout base com sidebar dinâmica
│   │   ├── auth/            # Login, cadastro, 2FA, configurações
│   │   ├── builds/          # Montador, listagem, detalhe
│   │   ├── produtos/        # Listagem e detalhe de peças
│   │   ├── avaliacoes/      # Avaliações e ranking
│   │   ├── admin/           # Painel administrativo
│   │   └── main/            # Início e comparador
│   │
│   ├── api/
│   │   └── routes.py        # API REST protegida por JWT
│   │
│   ├── services/            # Serviços de negócio
│   │   ├── compatibilidade.py  # Verificação de compatibilidade
│   │   ├── fps_estimator.py    # Estimativa de FPS em jogos
│   │   └── seed.py             # Dados iniciais (80 peças)
│   │
│   ├── utils/
│   │   └── lojas_urls.py    # URLs de busca por loja
│   │
│   └── extensions.py        # Extensões Flask centralizadas
│
├── migrations/              # Migrações do banco de dados
├── config.py                # Configurações por ambiente
├── run.py                   # Ponto de entrada da aplicação
├── requirements.txt         # Dependências do projeto
└── .env                     # Variáveis de ambiente (não commitar!)
```

---

## ⚙️ Como Rodar o Projeto

### Pré-requisitos
- Python 3.11+
- pip

### Passo a passo

**1. Clone o repositório:**
```bash
git clone https://github.com/seu-usuario/setupmaker.git
cd setupmaker
```

**2. Crie e ative o ambiente virtual:**
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python -m venv .venv
source .venv/bin/activate
```

**3. Instale as dependências:**
```bash
pip install -r requirements.txt
```

**4. Configure o arquivo `.env`:**
```bash
# Crie o arquivo .env na raiz do projeto com:
SECRET_KEY=sua-chave-secreta-longa
DATABASE_URL=sqlite:///setupmaker.db
JWT_SECRET_KEY=sua-jwt-secret-longa
MAIL_USERNAME=seu@gmail.com
MAIL_PASSWORD=sua-senha-de-app-gmail
```

> **Como gerar senha de app do Gmail:**
> Acesse [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords), ative verificação em duas etapas e gere uma senha de app para "Outro aplicativo".

**5. Crie o banco de dados:**
```bash
flask db upgrade
```

**6. Popule com dados iniciais:**
```bash
flask seed
```

**7. Rode o servidor:**
```bash
flask run
```

Acesse em: [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 🔌 API REST

A API está disponível em `/api` e requer autenticação JWT (exceto o endpoint de login).

### Autenticação

```bash
# Login — obtém o token JWT
POST /api/auth/login
Content-Type: application/json

{
  "email": "usuario@email.com",
  "password": "suasenha"
}
```

**Resposta:**
```json
{
  "access_token": "eyJ...",
  "usuario": { "id": 1, "username": "usuario", "email": "..." }
}
```

**Usar o token nas requisições:**
```bash
Authorization: Bearer eyJ...
```

### Endpoints Disponíveis

| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| `POST` | `/api/auth/login` | ❌ | Autentica e retorna token JWT |
| `POST` | `/api/auth/refresh` | ✅ | Renova o token JWT |
| `GET`  | `/api/auth/me` | ✅ | Dados do usuário autenticado |
| `GET`  | `/api/produtos` | ✅ | Lista produtos com filtros |
| `GET`  | `/api/produtos/<id>` | ✅ | Detalhe de um produto |
| `GET`  | `/api/produtos/<id>/precos` | ✅ | Preços por loja de um produto |
| `GET`  | `/api/builds` | ✅ | Builds do usuário autenticado |
| `GET`  | `/api/builds/<id>` | ✅ | Detalhe de uma build |
| `GET`  | `/api/builds/publicas` | ✅ | Builds públicas da comunidade |
| `GET`  | `/api/avaliacoes/produtos` | ✅ | Avaliações de produtos |
| `GET`  | `/api/avaliacoes/builds` | ✅ | Avaliações de builds |
| `POST` | `/api/compatibilidade` | ✅ | Verifica compatibilidade de peças |

---

## 🎬 Fluxos Demonstrados no Vídeo

1. **Registro** → cadastro com verificação de e-mail via código 6 dígitos
2. **Login** → autenticação com código 2FA por e-mail
3. **Área protegida** → montador de PC, peças, comparador de preços
4. **Alterar senha** → validação de senha forte (mín. 8 chars, 1 maiúscula, 1 número)
5. **Logout** → encerramento seguro da sessão
6. **Mensagens** → feedback visual de erro e sucesso em todas as ações

---

## 📊 Critérios de Avaliação

| Critério | Implementação |
|----------|---------------|
| **Funcionamento (20pts)** | Sistema completo e funcional com todas as rotas operacionais |
| **Autenticação JWT (20pts)** | Flask-JWT-Extended com 2FA por e-mail e verificação de cadastro |
| **Segurança (20pts)** | CSRF (Flask-WTF), XSS (Jinja2), SQL Injection (SQLAlchemy), hash de senha |
| **Organização MVC (20pts)** | Models, Routes (controllers) e Templates (views) separados e organizados |
| **Documentação (20pts)** | README completo, código comentado e API documentada em `/api/docs` |

---

## 👥 Desenvolvimento

Projeto desenvolvido como trabalho acadêmico para a disciplina de Desenvolvimento Web Seguro.

# 🎰 LottoCV — Otimizador de Apostas para Jogos Sociais de Cabo Verde

Sistema automatizado para análise e recomendação de apostas no Totoloto e Joker de Cabo Verde.

## 📦 Estrutura do Projeto

```
lotto_cv/
├── main.py                    # Ponto de entrada
├── requirements.txt
├── .env.example               # Template de variáveis de ambiente
├── lotto_cv.db                # Base de dados SQLite (gerada automaticamente)
│
├── database/
│   └── models.py              # Tabelas e operações BD
│
├── scraper/
│   ├── scraper.py             # Extração de dados do site
│   ├── decision_engine.py     # Motor de decisão + gerador de números
│   └── notificacoes.py        # Telegram + E-mail
│
└── scheduler/
    └── scheduler.py           # Agendamento automático
```

## 🚀 Instalação e Configuração

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente

```bash
cp .env.example .env
# Edita o .env com os teus tokens e emails
```

### 3. Configurar o Bot do Telegram (para alertas)

1. Abre o Telegram e procura `@BotFather`
2. Envia `/newbot` e segue as instruções
3. Copia o token para `TELEGRAM_BOT_TOKEN` no `.env`
4. Para obter o teu `TELEGRAM_CHAT_ID`:
   - Envia uma mensagem ao teu bot
   - Abre: `https://api.telegram.org/bot<TOKEN>/getUpdates`
   - Copia o `id` do campo `chat`

### 4. Inicializar a base de dados

```bash
python main.py init
```

## 🎮 Utilização

```bash
# Correr o scraping agora (extrai jackpot + histórico)
python main.py scrape

# Ver recomendação de apostas
python main.py recomendar

# Iniciar o agendador automático (corre 24/7)
python main.py scheduler

# Testar notificações Telegram
python scraper/notificacoes.py
```

## ☁️ Deployment na Cloud (Railway.app)

1. Cria conta em [railway.app](https://railway.app) (gratuito)
2. Liga ao teu repositório GitHub
3. Adiciona as variáveis de ambiente no painel do Railway
4. O comando de arranque deve ser: `python main.py scheduler`

## 📊 Lógica de Decisão

| Situação | Ação Recomendada |
|---|---|
| Jackpot ≥ 40.000 contos | Usar 1.000 ECV de uma vez (12 chaves) |
| Jackpot < 40.000 contos | Apostar 200 ECV/semana (Totoloto + Joker) |

## ⚠️ Aviso Importante

> A análise de frequência de números (quentes/frios) é **estatística descritiva** e **não melhora as probabilidades** num sorteio aleatório. O gerador de combinações é uma ferramenta de conveniência, não uma garantia de ganho. Joga com responsabilidade e dentro das tuas possibilidades.

## 🔧 Adaptar o Scraper

Se a estrutura HTML do site mudar, edita os seletores em `scraper/scraper.py`. Para inspecionar o HTML:

```bash
# No browser: F12 → inspecionar elemento com o jackpot
# Ou em Python:
python3 -c "
import requests
from bs4 import BeautifulSoup
r = requests.get('https://www.jogoscruzvermelha.cv/games/totoloto')
soup = BeautifulSoup(r.text, 'html.parser')
print(soup.prettify()[:3000])
"
```

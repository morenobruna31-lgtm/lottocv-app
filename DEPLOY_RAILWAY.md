# 🚀 Deploy LottoCV no Railway — Guia Completo

## O que o Railway faz por ti
- ✅ App online 24/7 sem precisares do computador
- ✅ Base de dados PostgreSQL (dados nunca somem)
- ✅ Scraping automático todos os Sábados às 19:45
- ✅ URL privado protegido com password só tua
- ✅ Gratuito até $5/mês (mais que suficiente)

---

## Passo 1 — Criar conta GitHub
1. Vai a **github.com**
2. Clica "Sign up"
3. Cria a conta (é grátis)

## Passo 2 — Colocar o projeto no GitHub
1. No GitHub, clica no **+** (canto superior direito) → "New repository"
2. Nome: `lottocv`
3. Deixa **Private** (só tu vês)
4. Clica "Create repository"
5. No PowerShell, corre:

```powershell
cd "C:\Users\Lenovo\Downloads\lotto_cv_final\lotto_cv"
git init
git add .
git commit -m "LottoCV inicial"
git branch -M main
git remote add origin https://github.com/SEU_USERNAME/lottocv.git
git push -u origin main
```
(substitui SEU_USERNAME pelo teu username do GitHub)

## Passo 3 — Criar conta Railway
1. Vai a **railway.app**
2. Clica "Login" → "Login with GitHub"
3. Autoriza o Railway

## Passo 4 — Criar o projeto no Railway
1. No Railway, clica **"New Project"**
2. Escolhe **"Deploy from GitHub repo"**
3. Seleciona **lottocv**
4. Railway começa o deploy automaticamente

## Passo 5 — Adicionar PostgreSQL
1. No projeto Railway, clica **"New"** → **"Database"** → **"PostgreSQL"**
2. A variável `DATABASE_URL` é criada automaticamente ✅

## Passo 6 — Adicionar variáveis de ambiente
No Railway → Settings → Variables, adiciona:

| Variável | Valor |
|---|---|
| `ANTHROPIC_API_KEY` | sk-ant-... (a tua chave) |
| `APP_USER` | bruna |
| `APP_PASS` | (escolhe uma password) |
| `JACKPOT_CRITICO` | 40000000 |

## Passo 7 — Obter o teu URL
1. Railway → Settings → Networking → **Generate Domain**
2. O teu URL será algo como: `lottocv-production.up.railway.app`
3. Abre no browser → pede username e password
4. Entra com `bruna` / a tua password ✅

---

## Manutenção
- **Atualizar o código**: faz `git push` e o Railway faz deploy automático
- **Ver logs**: Railway → Deployments → View Logs
- **Base de dados**: nunca perde dados (PostgreSQL permanente)
- **Scraping**: automático aos Sábados, ou clica "Atualizar dados" no dashboard


"""
Script de correcao de encoding — corre na pasta lotto_cv
Substitui emojis por texto simples no dashboard
"""
import re, os

path = "dashboard/index.html"
if not os.path.exists(path):
    print("ERRO: ficheiro nao encontrado")
    exit(1)

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: ensure charset meta is first in head
if '<meta charset="UTF-8">' not in content:
    content = content.replace('<head>', '<head>\n<meta charset="UTF-8">')
    print("Adicionado meta charset")

# Fix 2: Replace problematic emojis with safe HTML entities or text
emoji_fixes = [
    ('🎰', '[TOTOLOTO]'),
    ('🃏', '[JOKER]'),
    ('⏱', '[TIMER]'),
    ('💳', '[ORCAMENTO]'),
    ('🎫', '[APOSTAS]'),
    ('📅', '[DATA]'),
    ('✝️', '[+]'),
    ('🎯', '[ALVO]'),
    ('📊', '[STATS]'),
    ('⏰', '[TEMPO]'),
    ('🔗', '[PARES]'),
    ('❄️', '[FRIO]'),
    ('🔍', '[VER]'),
    ('🙏', '[ORACAO]'),
    ('⟳', '&#8635;'),
    ('↩', '&#8617;'),
    ('⚠️', '[!]'),
    ('🔥', '[QUENTE]'),
    ('🏆', '[6 ACERTOS]'),
    ('🥈', '[5 ACERTOS]'),
    ('🥉', '[4 ACERTOS]'),
    ('📍', '[2-3]'),
    ('🎲', '[DADOS]'),
    ('🎯', '[ALVO]'),
    ('🌸', ''),
    ('✅', '[OK]'),
    ('❌', '[X]'),
    ('💰', '[DINHEIRO]'),
    ('🔔', '[ALERTA]'),
    ('🔕', '[SEM ALERTA]'),
    ('🤖', '[BOT]'),
]

count = 0
for emoji, replacement in emoji_fixes:
    if emoji in content:
        content = content.replace(emoji, replacement)
        count += 1

# Fix 3: Fix accented chars that cause issues
accent_fixes = [
    ('Próximo', 'Proximo'),
    ('Sábados', 'Sabados'),
    ('às', 'as'),
    ('Orçamento', 'Orcamento'),
    ('Frequência', 'Frequencia'),
    ('Frequências', 'Frequencias'),
    ('Evolução', 'Evolucao'),
    ('Últimos', 'Ultimos'),
    ('Estatísticas', 'Estatisticas'),
    ('Avançadas', 'Avancadas'),
    ('Combinações', 'Combinacoes'),
    ('Atrasados', 'Atrasados'),
    ('combinações', 'combinacoes'),
    ('Recomendação', 'Recomendacao'),
    ('Análise', 'Analise'),
    ('Bênção', 'Bencao'),
    ('mês', 'mes'),
    ('Mês', 'Mes'),
    ('Configuração', 'Configuracao'),
    ('próximo', 'proximo'),
    ('sábado', 'sabado'),
    ('sorteios jogados este mês', 'sorteios jogados este mes'),
    ('gastos registados este mês', 'gastos registados este mes'),
    ('Sem dados de near miss ainda. As combinações geradas serão analisadas após cada sorteio.', 
     'Sem dados de near miss ainda. As combinacoes geradas serao analisadas apos cada sorteio.'),
]

for old, new in accent_fixes:
    if old in content:
        content = content.replace(old, new)
        count += 1

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Corrigido! {count} substituicoes feitas.")
print("Faz git add dashboard/index.html && git commit -m 'fix: encoding' && git push")

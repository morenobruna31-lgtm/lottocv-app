"""
Versículos Bíblicos — LottoCV
Versículos de fé, esperança, gratidão e bênção para acompanhar as apostas.
"""

import random

VERSICULOS = [
    {"ref": "Filipenses 4:19", "texto": "O meu Deus suprirá todas as vossas necessidades segundo as suas riquezas em glória em Cristo Jesus."},
    {"ref": "Jeremias 29:11", "texto": "Porque eu sei os planos que tenho para vós, diz o Senhor, planos de paz e não de mal, para vos dar um futuro e uma esperança."},
    {"ref": "Salmos 37:4", "texto": "Tem o teu prazer no Senhor, e ele te dará o que o teu coração deseja."},
    {"ref": "Provérbios 16:3", "texto": "Confia ao Senhor as tuas obras, e os teus projetos serão estabelecidos."},
    {"ref": "Mateus 7:7", "texto": "Pedi e dar-se-vos-á; buscai e encontrareis; batei e abrir-se-vos-á."},
    {"ref": "Salmos 23:1", "texto": "O Senhor é o meu pastor; nada me faltará."},
    {"ref": "Lucas 1:37", "texto": "Porque nada é impossível a Deus."},
    {"ref": "Marcos 11:24", "texto": "Por isso vos digo que tudo o que pedirdes em oração, crede que o recebereis e assim será."},
    {"ref": "Josué 1:9", "texto": "Sê forte e corajoso. Não te atemorizes nem te espantes, porque o Senhor, teu Deus, é contigo por onde quer que andares."},
    {"ref": "Salmos 118:24", "texto": "Este é o dia que o Senhor fez; regozijemo-nos e nele nos alegremos."},
    {"ref": "Romanos 8:28", "texto": "E sabemos que todas as coisas contribuem juntamente para o bem daqueles que amam a Deus."},
    {"ref": "Provérbios 3:5-6", "texto": "Confia no Senhor de todo o teu coração e não te estribes no teu próprio entendimento. Reconhece-o em todos os teus caminhos, e ele endireitará as tuas veredas."},
    {"ref": "Salmos 34:8", "texto": "Provai e vede que o Senhor é bom; bem-aventurado o homem que nele se refugia."},
    {"ref": "Isaías 41:10", "texto": "Não temas, porque eu sou contigo; não te assombres, porque eu sou o teu Deus; eu te fortaleço, e te ajudo, e te sustento com a minha destra fiel."},
    {"ref": "1 Coríntios 2:9", "texto": "O que olhos não viram, nem ouvidos ouviram, nem penetrou o coração do homem, são as coisas que Deus preparou para os que o amam."},
    {"ref": "Salmos 20:4", "texto": "Conceda-te o que o teu coração deseja e realize todos os teus planos."},
    {"ref": "Efésios 3:20", "texto": "Ora, àquele que é poderoso para fazer tudo muito mais abundantemente além do que pedimos ou pensamos, segundo o poder que em nós opera."},
    {"ref": "Deuteronômio 28:12", "texto": "O Senhor te abrirá o seu bom tesouro, os céus, para dar chuva à tua terra no tempo certo e para abençoar toda a obra das tuas mãos."},
    {"ref": "Malaquias 3:10", "texto": "Trazei todos os dízimos à casa do tesouro... e provai-me nisto, diz o Senhor dos Exércitos, se eu não vos abrir as janelas do céu e não derramar sobre vós uma bênção sem medida."},
    {"ref": "Salmos 128:2", "texto": "Porque comerás do trabalho das tuas mãos; feliz serás, e bem te irá."},
]

ORACOES = [
    "🙏 Senhor, nas Tuas mãos entrego esta semana. Que a Tua vontade seja feita, e que eu seja grato por tudo o que recebi.",
    "🙏 Pai Celestial, abençoa este momento. Que estes números sejam guiados pela Tua graça e misericórdia.",
    "🙏 Deus, Tu és a fonte de todas as bênçãos. Aceita a minha fé e a minha esperança neste sorteio.",
    "🙏 Senhor, que a Tua mão esteja sobre mim. Não por sorte, mas pela Tua graça e bondade.",
    "🙏 Pai, sou grato por cada oportunidade. Que este jogo seja uma bênção e não uma aflição.",
]


def versiculos_da_semana(n=3):
    """Devolve N versículos aleatórios para a semana."""
    return random.sample(VERSICULOS, min(n, len(VERSICULOS)))


def oracao_do_dia():
    """Devolve uma oração aleatória."""
    return random.choice(ORACOES)


def bencao_completa():
    """Devolve versículos + oração para mostrar após gerar combinações."""
    versiculos = versiculos_da_semana(3)
    oracao = oracao_do_dia()
    return {
        "versiculos": versiculos,
        "oracao": oracao,
        "mensagem": "✝️ Que Deus abençoe os teus números e guie o teu coração com sabedoria e gratidão."
    }

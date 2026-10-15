import pygame
import math
import heapq

pygame.init()

# Resolução lógica do jogo (mantida para preservar o raycasting e a HUD)
LARGURA = 600
ALTURA = 400
FPS = 60

# A janela pode alternar entre modo janela e tela cheia com F11.
LARGURA_JANELA = 1280
ALTURA_JANELA = 853
modo_tela_cheia = False
display = pygame.display.set_mode((LARGURA_JANELA, ALTURA_JANELA))
tela = pygame.Surface((LARGURA, ALTURA))
pygame.display.set_caption("Raycasting - 2 Fases")


def alternar_tela_cheia():
    """Alterna o display sem alterar a resolução lógica do jogo."""
    global display, modo_tela_cheia
    modo_tela_cheia = not modo_tela_cheia
    if modo_tela_cheia:
        display = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        display = pygame.display.set_mode((LARGURA_JANELA, ALTURA_JANELA))


def obter_area_jogo():
    """Calcula a área de desenho mantendo a proporção original 3:2."""
    largura_display, altura_display = display.get_size()
    escala = min(largura_display / LARGURA, altura_display / ALTURA)
    largura_jogo = max(1, int(LARGURA * escala))
    altura_jogo = max(1, int(ALTURA * escala))
    x = (largura_display - largura_jogo) // 2
    y = (altura_display - altura_jogo) // 2
    return pygame.Rect(x, y, largura_jogo, altura_jogo)


def converter_mouse_para_jogo(posicao):
    """Converte coordenadas do display para a resolução lógica do jogo."""
    mx, my = posicao
    area = obter_area_jogo()
    mx = (mx - area.x) * LARGURA / area.width
    my = (my - area.y) * ALTURA / area.height
    return int(mx), int(my)


def atualizar_display():
    """Amplia a imagem para o display atual sem distorcer o jogo."""
    display.fill((0, 0, 0))
    area = obter_area_jogo()
    quadro_ampliado = pygame.transform.scale(tela, area.size)
    display.blit(quadro_ampliado, area.topleft)
    pygame.display.flip()
relogio = pygame.time.Clock()

T = 5  # tamanho dos blocos do minimapa, reduzido para caber melhor na tela
MINIMAPA_X = 0
MINIMAPA_Y = 0
COLUNAS = 120
L = LARGURA // COLUNAS
FOV = math.pi / 3

mapas = [
    [
        "##############################",
        "#............#...............#",
        "#............#...............#",
        "#............#...............#",
        "#....####....#.......####....#",
        "#....#.......#.......#.......#",
        "#....#.......#.......#.......#",
        "#............#...............#",
        "#......###...................#",
        "#......#.....#...#...........#",
        "#............#...............#",
        "#............#...............#",
        "#....####....#.......####....#",
        "#............#...............#",
        "#............#...............#",
        "#............#...............#",
        "##############################"
    ],
    [
        "##############################",
        "#............#...............#",
        "#............#...............#",
        "#..####......#.......####....#",
        "#..#.........#.......#.......#",
        "#..#.........#.......#.......#",
        "#............#...............#",
        "#.......###..#...............#",
        "#.......#....................#",
        "#............#...............#",
        "#............#...............#",
        "#.....####...#.......####....#",
        "#.....#......#.......#.......#",
        "#............#...............#",
        "#............#...............#",
        "#............#...............#",
        "##############################"
    ]
]


# Expansão dos mapas: 40 colunas x 23 linhas.
# Mantém as áreas originais, portas e botões nas mesmas coordenadas,
# acrescentando corredores, salas laterais e uma ala ao sul.
def ampliar_mapa(mapa_original):
    largura_nova = 40
    altura_nova = 23
    linhas = []
    for indice, linha in enumerate(mapa_original):
        if indice == 0:
            linhas.append("#" * largura_nova)
        elif indice == len(mapa_original) - 1:
            # A antiga borda sul vira um corredor interno da nova ala.
            linhas.append("#" + "." * 12 + "#" + "." * 25 + "#")
        else:
            linhas.append(linha[:-1] + "." * (largura_nova - len(linha)) + "#")

    # Novas linhas continuam a divisória central para não permitir
    # contornar a porta principal por baixo.
    while len(linhas) < altura_nova:
        y_novo = len(linhas)
        linha = ["." for _ in range(largura_nova)]
        linha[0] = "#"
        linha[-1] = "#"
        linha[13] = "#"
        linhas.append("".join(linha))

    # Novas salas e obstáculos na extensão leste e na ala sul.
    grade = [list(linha) for linha in linhas]
    blocos = [
        # Sala leste superior
        (32, 2), (33, 2), (34, 2), (32, 3), (34, 3),
        (32, 4), (33, 4), (34, 4),
        # Cobertura e divisórias de uma sala central
        (30, 8), (31, 8), (32, 8), (33, 8),
        (30, 9), (33, 9), (30, 10), (31, 10), (32, 10), (33, 10),
        # Pequenos pilares na ala leste inferior
        (36, 13), (36, 14), (36, 15),
        # Obstáculos da nova ala sul, sem bloquear o corredor da porta
        (4, 19), (5, 19), (6, 19), (6, 20),
        (18, 18), (19, 18), (20, 18), (20, 19),
        (25, 20), (26, 20), (27, 20),
        (34, 18), (35, 18), (34, 19), (35, 19),
    ]
    for bx, by in blocos:
        # Não altera a borda nem a divisória que protege a porta.
        if 1 <= bx < largura_nova - 1 and 1 <= by < altura_nova - 1:
            if bx != 13:
                grade[by][bx] = "#"

    # Garante bordas fechadas e dimensões idênticas em todas as linhas.
    for yy in range(altura_nova):
        grade[yy][0] = "#"
        grade[yy][-1] = "#"
    grade[0] = ["#"] * largura_nova
    grade[-1] = ["#"] * largura_nova

    return ["".join(linha) for linha in grade]


mapas = [ampliar_mapa(mapa_fase) for mapa_fase in mapas]

portas = [
    (13, 8),
    (13, 8)
]

botoes = [
    (36, 20),
    (36, 20)
]

inimigos_por_fase = [
    [
        [9.5, 4.5],
        [12.5, 2.5],
        [16.5, 3.5],
        [20.5, 5.5],
        [10.5, 10.5],
        [18.5, 10.5],
        [20.5, 12.5],
        [16.5, 13.5],
        [7.5, 13.5],
        [12.5, 14.5]
    ],
    [
        [8.5, 2.5],
        [11.5, 3.5],
        [16.5, 2.5],
        [20.5, 3.5],
        [23.5, 5.5],
        [9.5, 8.5],
        [17.5, 8.5],
        [21.5, 9.5],
        [7.5, 12.5],
        [11.5, 14.5],
        [18.5, 13.5],
        [23.5, 14.5]
    ]
]

fase = 0
mapa = mapas[fase]

MAPA_ALTURA = len(mapa)
MAPA_LARGURA = len(mapa[0])

PORTA_X, PORTA_Y = portas[fase]
BOTAO_X, BOTAO_Y = botoes[fase]

porta_estado = 0
porta_animacao = 0.0
PORTA_TEMPO_ANIMACAO = 15

jogo_vencido = False
mudando_fase = False
tempo_transicao = 0
TEMPO_TRANSICAO = 90

mensagem = ""
tempo_mensagem = 0

x = 3.5
y = 7.5
ang = 0.0

# Inércia leve para deixar a movimentação mais suave.
velocidade_movimento_atual = 0.0
velocidade_angular_atual = 0.0

RAIO_JOGADOR = 0.20
RAIO_INIMIGO = 0.23

VELOCIDADE_NORMAL = 0.08
VELOCIDADE_CORRENDO = 0.15
VELOCIDADE_INIMIGO = 0.020

vida_maxima = 100
vida_jogador = 100

DANO_INIMIGO = 8
DISTANCIA_ATAQUE = 0.75
INTERVALO_ATAQUE = 30

vida_inimigo_maxima = 100

tempo_dano = 0
tempo_cura = 0
TEMPO_CURA = 45
CURA = 35

STAMINA_MAXIMA = 100
stamina = STAMINA_MAXIMA
DRENAGEM_STAMINA = 1.5
RECUPERACAO_STAMINA = 0.8
STAMINA_MINIMA_CORRIDA = 5
cansado = False
tempo_cansado = 0
TEMPO_CANSADO = 90

ARMA_RIFLE = 0
ARMA_PISTOLA = 1
ARMA_MOTOSERRA = 2

arma_atual = ARMA_PISTOLA
# O jogador começa apenas com a pistola; as outras armas são coletadas no cenário.
armas_desbloqueadas = {ARMA_PISTOLA}
menu_armas = False
jogo_pausado = False
tela_pausa = None

rifle_municao_max = 12
rifle_municao = 12
rifle_reserva = 60
RIFLE_TEMPO_RECARREGA = 45
RIFLE_COOLDOWN = 8
rifle_tempo_recarga = 0

pistola_municao_max = 8
pistola_municao = 8
pistola_reserva = 40
PISTOLA_TEMPO_RECARREGA = 35
PISTOLA_COOLDOWN = 14
pistola_tempo_recarga = 0

MOTOSERRA_COOLDOWN = 12

DANO_RIFLE = 100
DANO_PISTOLA = 45
DANO_MOTOSERRA = 65

tiro = 0
cooldown_tiro = 0
RECARREGANDO = False

inimigos = []
vida_inimigos = []
tempo_ataque_inimigos = []
inimigos_com_chave = []
inimigos_drop_arma = []
drops_armas = []  # Itens coletáveis no cenário: [x, y, tipo_da_arma]

# A chave é derrubada por um inimigo específico da primeira fase.
tem_chave = False
posicao_chave = None

caminhos = {}
contador_ia = 0
tempo_animacao = 0

fonte = pygame.font.SysFont("consolas", 22, bold=True)
fonte_pequena = pygame.font.SysFont("consolas", 17, bold=True)
fonte_grande = pygame.font.SysFont("consolas", 32, bold=True)

# Preferências visuais do menu Configurações > Jogabilidade.
menu_configuracoes = False
secao_configuracoes = "inicio"  # inicio, informacoes ou controles
configuracoes_jogabilidade = {
    "minimapa": True,
    "vida": True,
    "stamina": True,
    "arma_municao": True,
    "dicas": True,
    "fase_chave": True,
}

def parede(px, py):
    if px < 0 or py < 0:
        return True

    if px >= MAPA_LARGURA or py >= MAPA_ALTURA:
        return True

    gx = int(px)
    gy = int(py)

    if gx == PORTA_X and gy == PORTA_Y:
        return porta_estado != 2

    return mapa[gy][gx] == "#"

def pode_andar(px, py, raio):
    pontos = [
        (px, py),
        (px - raio, py),
        (px + raio, py),
        (px, py - raio),
        (px, py + raio),
        (px - raio * 0.7, py - raio * 0.7),
        (px + raio * 0.7, py - raio * 0.7),
        (px - raio * 0.7, py + raio * 0.7),
        (px + raio * 0.7, py + raio * 0.7)
    ]

    for px2, py2 in pontos:
        if parede(px2, py2):
            return False

    return True

def mover_com_colisao(obj, dx, dy, raio):
    novo_x = obj[0] + dx

    if pode_andar(novo_x, obj[1], raio):
        obj[0] = novo_x

    novo_y = obj[1] + dy

    if pode_andar(obj[0], novo_y, raio):
        obj[1] = novo_y

def raio_com_porta(angulo):
    c = math.cos(angulo)
    s = math.sin(angulo)
    d = 0.0

    while d < 30:
        px = x + c * d
        py = y + s * d

        if px < 0 or py < 0:
            return d, False

        if px >= MAPA_LARGURA or py >= MAPA_ALTURA:
            return d, False

        gx = int(px)
        gy = int(py)

        if gx == PORTA_X and gy == PORTA_Y:
            if porta_estado != 2:
                return d, True

        if mapa[gy][gx] == "#":
            return d, False

        d += 0.02

    return 30, False

def heuristica(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def vizinhos(no):
    gx, gy = no

    direcoes = [
        (1, 0),
        (-1, 0),
        (0, 1),
        (0, -1)
    ]

    resultado = []

    for dx, dy in direcoes:
        nx = gx + dx
        ny = gy + dy

        if nx < 0 or ny < 0:
            continue

        if nx >= MAPA_LARGURA or ny >= MAPA_ALTURA:
            continue

        if parede(nx + 0.5, ny + 0.5):
            continue

        resultado.append((nx, ny))

    return resultado

def encontrar_caminho(inicio, objetivo):
    inicio = (int(inicio[0]), int(inicio[1]))
    objetivo = (int(objetivo[0]), int(objetivo[1]))

    if parede(objetivo[0] + 0.5, objetivo[1] + 0.5):
        return []

    fila = []
    contador = 0

    heapq.heappush(
        fila,
        (0, contador, inicio)
    )

    veio_de = {}
    custo = {inicio: 0}

    while fila:
        _, _, atual = heapq.heappop(fila)

        if atual == objetivo:
            caminho = []

            while atual != inicio:
                caminho.append(atual)

                if atual not in veio_de:
                    return []

                atual = veio_de[atual]

            caminho.reverse()
            return caminho

        for vizinho in vizinhos(atual):
            novo_custo = custo[atual] + 1

            if vizinho not in custo or novo_custo < custo[vizinho]:
                custo[vizinho] = novo_custo

                prioridade = (
                    novo_custo
                    +
                    heuristica(vizinho, objetivo)
                )

                contador += 1

                heapq.heappush(
                    fila,
                    (
                        prioridade,
                        contador,
                        vizinho
                    )
                )

                veio_de[vizinho] = atual

    return []

def separar_inimigos():
    for i in range(len(inimigos)):
        for j in range(i + 1, len(inimigos)):
            a = inimigos[i]
            b = inimigos[j]

            dx = a[0] - b[0]
            dy = a[1] - b[1]

            distancia = math.hypot(dx, dy)

            if distancia == 0:
                dx = 0.01
                dy = 0.01
                distancia = math.hypot(dx, dy)

            distancia_minima = RAIO_INIMIGO * 2

            if distancia < distancia_minima:
                empurrao = distancia_minima - distancia

                nx = dx / distancia
                ny = dy / distancia

                ax = a[0] + nx * empurrao * 0.5
                ay = a[1] + ny * empurrao * 0.5

                bx = b[0] - nx * empurrao * 0.5
                by = b[1] - ny * empurrao * 0.5

                if pode_andar(ax, ay, RAIO_INIMIGO):
                    a[0] = ax
                    a[1] = ay

                if pode_andar(bx, by, RAIO_INIMIGO):
                    b[0] = bx
                    b[1] = by

def corrigir_inimigo_na_parede(inimigo):
    if pode_andar(
        inimigo[0],
        inimigo[1],
        RAIO_INIMIGO
    ):
        return

    for distancia in [
        0.05,
        0.10,
        0.15,
        0.20,
        0.30,
        0.40,
        0.50,
        0.70,
        1.0
    ]:
        for i in range(32):
            angulo = 2 * math.pi * i / 32

            novo_x = (
                inimigo[0]
                +
                math.cos(angulo) * distancia
            )

            novo_y = (
                inimigo[1]
                +
                math.sin(angulo) * distancia
            )

            if pode_andar(
                novo_x,
                novo_y,
                RAIO_INIMIGO
            ):
                inimigo[0] = novo_x
                inimigo[1] = novo_y
                return

def criar_sprite(pose):
    largura = 24
    altura = 32

    sprite = pygame.Surface(
        (largura, altura),
        pygame.SRCALPHA
    )

    pele = (70, 150, 65)
    pele_clara = (105, 190, 75)
    pele_escura = (35, 85, 40)
    roupa = (55, 55, 70)
    roupa_clara = (85, 85, 105)
    vermelho = (180, 25, 25)
    vermelho_escuro = (90, 10, 10)
    branco = (245, 245, 210)
    preto = (10, 10, 10)
    metal = (100, 105, 115)

    pygame.draw.rect(
        sprite,
        (0, 0, 0, 100),
        (4, 29, 16, 2)
    )

    if pose == 0:
        perna_esq = (6, 22, 5, 8)
        perna_dir = (13, 23, 5, 7)
    elif pose == 1:
        perna_esq = (5, 23, 5, 7)
        perna_dir = (14, 22, 5, 8)
    else:
        perna_esq = (6, 22, 5, 8)
        perna_dir = (13, 22, 5, 8)

    pygame.draw.rect(sprite, roupa, perna_esq)
    pygame.draw.rect(sprite, roupa, perna_dir)

    pygame.draw.rect(sprite, preto, (4, 29, 7, 2))
    pygame.draw.rect(sprite, preto, (13, 29, 7, 2))

    pygame.draw.rect(sprite, pele, (2, 14, 4, 9))
    pygame.draw.rect(sprite, pele, (18, 14, 4, 9))

    pygame.draw.rect(sprite, pele_clara, (2, 21, 4, 3))
    pygame.draw.rect(sprite, pele_clara, (18, 21, 4, 3))

    pygame.draw.rect(sprite, roupa, (6, 13, 12, 11))
    pygame.draw.rect(sprite, roupa_clara, (8, 14, 8, 8))
    pygame.draw.rect(sprite, vermelho, (10, 16, 4, 4))

    pygame.draw.rect(sprite, pele_escura, (9, 10, 6, 4))
    pygame.draw.rect(sprite, pele, (5, 3, 14, 9))

    pygame.draw.rect(sprite, pele_escura, (5, 6, 2, 5))
    pygame.draw.rect(sprite, pele_escura, (17, 6, 2, 5))

    pygame.draw.rect(sprite, preto, (6, 2, 12, 3))
    pygame.draw.rect(sprite, preto, (5, 4, 3, 4))
    pygame.draw.rect(sprite, preto, (16, 4, 3, 4))

    pygame.draw.rect(sprite, branco, (8, 6, 3, 2))
    pygame.draw.rect(sprite, branco, (14, 6, 3, 2))

    pygame.draw.rect(sprite, vermelho, (9, 6, 1, 2))
    pygame.draw.rect(sprite, vermelho, (14, 6, 1, 2))

    pygame.draw.rect(sprite, vermelho_escuro, (9, 9, 6, 2))

    pygame.draw.rect(sprite, metal, (5, 13, 3, 4))
    pygame.draw.rect(sprite, metal, (16, 13, 3, 4))

    return sprite

sprites = [
    criar_sprite(0),
    criar_sprite(1),
    criar_sprite(2)
]

def criar_sprite_chave():
    sprite = pygame.Surface((24, 28), pygame.SRCALPHA)
    dourado = (255, 205, 35)
    claro = (255, 240, 120)
    escuro = (170, 105, 10)
    # Argola da chave
    pygame.draw.circle(sprite, escuro, (8, 8), 7)
    pygame.draw.circle(sprite, dourado, (8, 8), 5)
    pygame.draw.circle(sprite, (30, 30, 35, 255), (8, 8), 2)
    # Haste e dentes
    pygame.draw.rect(sprite, dourado, (7, 12, 4, 13))
    pygame.draw.rect(sprite, claro, (8, 13, 1, 10))
    pygame.draw.rect(sprite, dourado, (10, 19, 6, 3))
    pygame.draw.rect(sprite, escuro, (10, 22, 4, 3))
    return sprite

sprite_chave = criar_sprite_chave()


def criar_sprite_drop_arma(tipo):
    """Cria um ícone simples para a arma que aparece no chão."""
    sprite = pygame.Surface((36, 24), pygame.SRCALPHA)
    if tipo == ARMA_RIFLE:
        cor = (245, 190, 45)
        pygame.draw.rect(sprite, (45, 48, 55), (4, 8, 26, 7), border_radius=2)
        pygame.draw.rect(sprite, cor, (8, 6, 18, 3), border_radius=1)
        pygame.draw.rect(sprite, (95, 65, 35), (9, 14, 7, 7))
        pygame.draw.rect(sprite, cor, (28, 9, 6, 3))
    else:
        cor = (245, 80, 45)
        pygame.draw.rect(sprite, (45, 48, 55), (5, 8, 22, 8), border_radius=2)
        pygame.draw.rect(sprite, cor, (8, 5, 18, 4), border_radius=2)
        pygame.draw.rect(sprite, (180, 180, 185), (27, 10, 7, 3))
        pygame.draw.rect(sprite, (95, 55, 35), (10, 15, 8, 6))
    pygame.draw.rect(sprite, cor, (1, 1, 34, 22), 1, border_radius=3)
    return sprite


sprites_drops_armas = {
    ARMA_RIFLE: criar_sprite_drop_arma(ARMA_RIFLE),
    ARMA_MOTOSERRA: criar_sprite_drop_arma(ARMA_MOTOSERRA),
}


def desenhar_sprite(sprite, sx, altura, distancia_inimigo, distancias):
    proporcao = (
        sprite.get_width()
        /
        sprite.get_height()
    )

    largura = max(
        1,
        int(altura * proporcao)
    )

    altura = max(1, int(altura))

    sprite_grande = pygame.transform.scale(
        sprite,
        (largura, altura)
    )

    pos_x = int(sx - largura / 2)
    pos_y = int(200 + altura / 2)

    for coluna_sprite in range(largura):
        tela_x = pos_x + coluna_sprite

        if tela_x < 0 or tela_x >= LARGURA:
            continue

        coluna_ray = tela_x // L

        if coluna_ray < 0 or coluna_ray >= len(distancias):
            continue

        if distancias[coluna_ray] < distancia_inimigo:
            continue

        area = pygame.Rect(
            coluna_sprite,
            0,
            1,
            altura
        )

        tela.blit(
            sprite_grande,
            (tela_x, pos_y - altura),
            area
        )

def desenhar_rifle():
    if tiro > 0:
        pygame.draw.polygon(
            tela,
            (255, 180, 30),
            [
                (300, 250),
                (286, 276),
                (300, 270),
                (314, 276)
            ]
        )

    pygame.draw.polygon(
        tela,
        (10, 10, 12),
        [
            (250, 400),
            (272, 305),
            (328, 305),
            (350, 400)
        ]
    )

    pygame.draw.polygon(
        tela,
        (38, 40, 47),
        [
            (270, 318),
            (330, 318),
            (340, 400),
            (260, 400)
        ]
    )

    pygame.draw.polygon(
        tela,
        (75, 78, 88),
        [
            (276, 305),
            (324, 305),
            (331, 345),
            (269, 345)
        ]
    )

    pygame.draw.rect(
        tela,
        (105, 110, 120),
        (283, 312, 34, 12)
    )

    pygame.draw.rect(
        tela,
        (145, 148, 155),
        (288, 313, 24, 4)
    )

    pygame.draw.rect(
        tela,
        (18, 20, 24),
        (291, 250, 18, 70)
    )

    pygame.draw.rect(
        tela,
        (65, 68, 76),
        (294, 253, 12, 65)
    )

    pygame.draw.rect(
        tela,
        (125, 128, 135),
        (296, 255, 4, 58)
    )

    pygame.draw.rect(
        tela,
        (12, 13, 16),
        (289, 247, 22, 8)
    )

    pygame.draw.polygon(
        tela,
        (32, 28, 27),
        [
            (278, 348),
            (322, 348),
            (313, 400),
            (287, 400)
        ]
    )

    pygame.draw.polygon(
        tela,
        (55, 46, 43),
        [
            (284, 350),
            (316, 350),
            (309, 400),
            (291, 400)
        ]
    )

def desenhar_pistola():
    if tiro > 0:
        pygame.draw.polygon(
            tela,
            (255, 180, 40),
            [
                (300, 270),
                (289, 295),
                (300, 290),
                (311, 295)
            ]
        )

    pygame.draw.polygon(
        tela,
        (10, 10, 12),
        [
            (265, 400),
            (278, 315),
            (322, 315),
            (340, 400)
        ]
    )

    pygame.draw.rect(
        tela,
        (25, 27, 32),
        (290, 270, 20, 70)
    )

    pygame.draw.rect(
        tela,
        (95, 100, 110),
        (294, 272, 12, 63)
    )

    pygame.draw.polygon(
        tela,
        (65, 68, 76),
        [
            (275, 315),
            (325, 315),
            (318, 350),
            (282, 350)
        ]
    )

    pygame.draw.rect(
        tela,
        (40, 140, 220),
        (282, 322, 36, 5)
    )

    pygame.draw.polygon(
        tela,
        (35, 38, 45),
        [
            (282, 345),
            (318, 345),
            (312, 400),
            (288, 400)
        ]
    )

def desenhar_motoserra():
    vibracao = 0

    if tiro > 0:
        vibracao = 2 if tiro % 2 == 0 else -2

    pygame.draw.polygon(
        tela,
        (20, 20, 22),
        [
            (225 + vibracao, 400),
            (250 + vibracao, 310),
            (350 + vibracao, 310),
            (375 + vibracao, 400)
        ]
    )

    pygame.draw.polygon(
        tela,
        (70, 72, 78),
        [
            (250 + vibracao, 320),
            (350 + vibracao, 320),
            (335 + vibracao, 365),
            (265 + vibracao, 365)
        ]
    )

    pygame.draw.rect(
        tela,
        (185, 35, 25),
        (265 + vibracao, 335, 70, 35)
    )

    pygame.draw.rect(
        tela,
        (235, 55, 30),
        (270 + vibracao, 340, 60, 7)
    )

    pygame.draw.rect(
        tela,
        (25, 25, 27),
        (292 + vibracao, 285, 16, 65)
    )

    pygame.draw.rect(
        tela,
        (95, 98, 105),
        (295 + vibracao, 288, 10, 62)
    )

    pygame.draw.rect(
        tela,
        (35, 35, 38),
        (248 + vibracao, 350, 104, 18)
    )

    for i in range(10):
        xx = 250 + i * 10 + vibracao

        pygame.draw.line(
            tela,
            (190, 190, 185),
            (xx, 351),
            (xx + 7, 367),
            3
        )

    if tiro > 0:
        pygame.draw.circle(
            tela,
            (255, 210, 70),
            (300 + vibracao, 300),
            9
        )

        pygame.draw.circle(
            tela,
            (255, 100, 20),
            (300 + vibracao, 300),
            4
        )

def desenhar_arma():
    if arma_atual == ARMA_RIFLE:
        desenhar_rifle()
    elif arma_atual == ARMA_PISTOLA:
        desenhar_pistola()
    else:
        desenhar_motoserra()

def desenhar_menu_pausa():
    if menu_configuracoes:
        desenhar_menu_configuracoes()
        return

    # Escurece o jogo ao fundo
    camada = pygame.Surface(
        (LARGURA, ALTURA),
        pygame.SRCALPHA
    )
    camada.fill((0, 0, 0, 200))
    tela.blit(camada, (0, 0))

    # Painel principal
    painel = pygame.Rect(100, 35, 400, 330)

    pygame.draw.rect(
        tela, (22, 25, 34), painel,
        border_radius=12
    )
    pygame.draw.rect(
        tela, (100, 115, 140), painel, 3,
        border_radius=12
    )

    titulo = fonte_grande.render(
        "JOGO PAUSADO", True, (255, 210, 60)
    )
    tela.blit(
        titulo,
        titulo.get_rect(center=(300, 68))
    )

    subtitulo = fonte_pequena.render(
        f"FASE {fase + 1}/2",
        True, (180, 190, 210)
    )
    tela.blit(
        subtitulo,
        subtitulo.get_rect(center=(300, 98))
    )

    mouse = converter_mouse_para_jogo(pygame.mouse.get_pos())

    botoes_menu = [
        (pygame.Rect(145, 120, 310, 42), "CONTINUAR", "continuar"),
        (pygame.Rect(145, 170, 310, 42), "CONFIGURACOES", "configuracoes"),
        (pygame.Rect(145, 220, 310, 42), "REINICIAR FASE", "reiniciar"),
        (pygame.Rect(145, 270, 310, 42), "SAIR DO JOGO", "sair")
    ]

    for retangulo, texto, acao in botoes_menu:
        selecionado = retangulo.collidepoint(mouse)

        cor_fundo = (
            (55, 95, 75) if selecionado
            else (38, 43, 55)
        )
        cor_borda = (
            (100, 255, 140) if selecionado
            else (95, 105, 125)
        )
        cor_texto = (
            (255, 235, 130) if selecionado
            else (240, 240, 245)
        )

        pygame.draw.rect(
            tela, cor_fundo, retangulo,
            border_radius=7
        )
        pygame.draw.rect(
            tela, cor_borda, retangulo, 2,
            border_radius=7
        )

        texto_renderizado = fonte.render(
            texto, True, cor_texto
        )
        tela.blit(
            texto_renderizado,
            texto_renderizado.get_rect(
                center=retangulo.center
            )
        )

    ajuda = fonte_pequena.render(
        "ESC - CONTINUAR",
        True, (165, 175, 195)
    )
    tela.blit(
        ajuda,
        ajuda.get_rect(center=(300, 338))
    )

def desenhar_menu_configuracoes():
    """Configurações divididas entre HUD e guia de controles."""
    camada = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    camada.fill((0, 0, 0, 215))
    tela.blit(camada, (0, 0))

    painel = pygame.Rect(65, 18, 470, 364)
    pygame.draw.rect(tela, (22, 25, 34), painel, border_radius=12)
    pygame.draw.rect(tela, (100, 115, 140), painel, 3, border_radius=12)

    mouse = converter_mouse_para_jogo(pygame.mouse.get_pos())
    titulo = fonte_grande.render("CONFIGURACOES", True, (255, 210, 60))
    tela.blit(titulo, titulo.get_rect(center=(300, 48)))

    def desenhar_botao(ret, rotulo):
        hover = ret.collidepoint(mouse)
        pygame.draw.rect(tela, (55, 95, 75) if hover else (38, 43, 55), ret, border_radius=7)
        pygame.draw.rect(tela, (100, 255, 140) if hover else (95, 105, 125), ret, 2, border_radius=7)
        texto = fonte.render(rotulo, True, (245, 245, 245))
        tela.blit(texto, texto.get_rect(center=ret.center))

    if secao_configuracoes == "inicio":
        subtitulo = fonte_pequena.render("ESCOLHA UMA CATEGORIA", True, (180, 190, 210))
        tela.blit(subtitulo, subtitulo.get_rect(center=(300, 85)))
        desenhar_botao(pygame.Rect(105, 112, 390, 68), "INFORMACOES NA TELA")
        desenhar_botao(pygame.Rect(105, 198, 390, 68), "CONTROLES DO JOGO")
        nota = fonte_pequena.render("Personalize a HUD ou consulte os comandos.", True, (175, 185, 200))
        tela.blit(nota, nota.get_rect(center=(300, 292)))
        desenhar_botao(pygame.Rect(180, 328, 240, 34), "VOLTAR")

    elif secao_configuracoes == "informacoes":
        subtitulo = fonte_pequena.render("INFORMACOES NA TELA - LIGAR / OCULTAR", True, (180, 190, 210))
        tela.blit(subtitulo, subtitulo.get_rect(center=(300, 78)))
        opcoes = [
            ("minimapa", "Minimapa"),
            ("vida", "Barra de vida"),
            ("stamina", "Barra de stamina"),
            ("arma_municao", "Arma e municao"),
            ("dicas", "Dicas na tela"),
            ("fase_chave", "Fase e status da chave"),
        ]
        for i, (chave, rotulo) in enumerate(opcoes):
            ret = pygame.Rect(105, 94 + i * 34, 390, 29)
            ativo = configuracoes_jogabilidade[chave]
            hover = ret.collidepoint(mouse)
            pygame.draw.rect(tela, (48, 58, 68) if hover else (35, 40, 51), ret, border_radius=5)
            pygame.draw.rect(tela, (90, 105, 125), ret, 1, border_radius=5)
            tela.blit(fonte_pequena.render(rotulo, True, (240, 240, 245)), (ret.x + 12, ret.y + 5))
            cor = (60, 220, 115) if ativo else (220, 75, 75)
            estado = "LIGADO" if ativo else "OCULTO"
            pygame.draw.rect(tela, cor, (ret.right - 92, ret.y + 3, 82, 23), border_radius=4)
            tela.blit(fonte_pequena.render(estado, True, (10, 15, 18)), fonte_pequena.render(estado, True, (10, 15, 18)).get_rect(center=(ret.right - 51, ret.centery)))
        desenhar_botao(pygame.Rect(180, 316, 240, 34), "VOLTAR")

    else:  # controles
        subtitulo = fonte_pequena.render("GUIA DE CONTROLES", True, (180, 190, 210))
        tela.blit(subtitulo, subtitulo.get_rect(center=(300, 78)))
        controles = [
            ("W / S", "Mover para frente / tras"),
            ("A / D", "Girar para esquerda / direita"),
            ("SHIFT", "Correr enquanto estiver pressionado"),
            ("E", "Interagir com portas, botoes e itens"),
            ("BOTAO ESQ.", "Atirar com a arma equipada"),
            ("RODA MOUSE", "Trocar de arma"),
            ("R", "Recarregar arma"),
            ("F", "Usar cura, quando disponivel"),
            ("M", "Abrir / fechar selecao de armas"),
            ("ESC", "Pausar / voltar ao jogo"),
            ("F11", "Alternar tela cheia"),
        ]
        for i, (tecla, descricao) in enumerate(controles):
            y = 96 + i * 20
            tela.blit(fonte_pequena.render(tecla, True, (255, 210, 90)), (91, y))
            tela.blit(fonte_pequena.render(descricao, True, (235, 238, 245)), (205, y))
        desenhar_botao(pygame.Rect(180, 326, 240, 34), "VOLTAR")


def carregar_fase(numero):
    global fase
    global mapa
    global MAPA_ALTURA
    global MAPA_LARGURA
    global PORTA_X
    global PORTA_Y
    global BOTAO_X
    global BOTAO_Y
    global porta_estado
    global porta_animacao
    global inimigos
    global vida_inimigos
    global tempo_ataque_inimigos
    global inimigos_com_chave
    global inimigos_drop_arma
    global drops_armas
    global tem_chave
    global posicao_chave
    global caminhos
    global contador_ia
    global x
    global y
    global ang
    global mudando_fase
    global tempo_transicao
    global velocidade_movimento_atual
    global velocidade_angular_atual

    velocidade_movimento_atual = 0.0
    velocidade_angular_atual = 0.0

    fase = numero
    if numero == 0:
        tem_chave = False
        posicao_chave = None
    mapa = mapas[fase]

    MAPA_ALTURA = len(mapa)
    MAPA_LARGURA = len(mapa[0])

    PORTA_X, PORTA_Y = portas[fase]
    BOTAO_X, BOTAO_Y = botoes[fase]

    porta_estado = 0
    porta_animacao = 0.0

    inimigos = []
    vida_inimigos = []
    tempo_ataque_inimigos = []
    inimigos_com_chave = []
    inimigos_drop_arma = []
    drops_armas = []

    caminhos = {}
    contador_ia = 0

    if fase == 0:
        x = 3.5
        y = 7.5
        ang = 0.0
    else:
        x = 3.5
        y = 13.5
        ang = 0.0

    for indice_pos, pos in enumerate(inimigos_por_fase[fase]):
        if pode_andar(
            pos[0],
            pos[1],
            RAIO_INIMIGO
        ):
            inimigos.append([
                pos[0],
                pos[1]
            ])

            vida_inimigos.append(
                vida_inimigo_maxima
            )

            tempo_ataque_inimigos.append(0)
            # O primeiro monstro da fase 1 é o portador da chave.
            inimigos_com_chave.append(fase == 0 and indice_pos == 0)
            # Um inimigo da primeira fase derruba o rifle; um da segunda, a motosserra.
            if fase == 0 and indice_pos == 2:
                inimigos_drop_arma.append(ARMA_RIFLE)
            elif fase == 1 and indice_pos == 5:
                inimigos_drop_arma.append(ARMA_MOTOSERRA)
            else:
                inimigos_drop_arma.append(None)

    mudando_fase = False
    tempo_transicao = 0

def alternar_porta():
    global porta_estado
    global mensagem
    global tempo_mensagem

    distancia = math.hypot(
        x - (PORTA_X + 0.5),
        y - (PORTA_Y + 0.5)
    )

    if distancia > 2.0:
        mensagem = "APROXIME-SE DA PORTA"
        tempo_mensagem = 60
        return

    if porta_estado == 0:
        if fase == 0 and not tem_chave:
            mensagem = "A PORTA ESTA TRANCADA! ENCONTRE A CHAVE"
            tempo_mensagem = 100
            return
        porta_estado = 1
        mensagem = "PORTA DESTRANCADA"
        tempo_mensagem = 45
        caminhos.clear()

    elif porta_estado == 2:
        if int(x) == PORTA_X and int(y) == PORTA_Y:
            return

        porta_estado = 3
        caminhos.clear()

def tentar_interagir():
    """Usa a tecla E para interagir com o objeto mais próximo."""
    global tem_chave, posicao_chave, mensagem, tempo_mensagem

    if mudando_fase or jogo_vencido or jogo_pausado or menu_armas:
        return

    # Prioridade 1: pegar a chave quando estiver ao alcance.
    if posicao_chave is not None and fase == 0 and not tem_chave:
        distancia_chave = math.hypot(
            x - posicao_chave[0], y - posicao_chave[1]
        )
        if distancia_chave <= 1.0:
            tem_chave = True
            posicao_chave = None
            mensagem = "VOCE PEGOU A CHAVE!"
            tempo_mensagem = 100
            return

    # Prioridade 2: coletar uma arma derrubada por um inimigo.
    drop_mais_proximo = None
    distancia_drop = float("inf")
    for drop in drops_armas:
        distancia = math.hypot(x - drop[0], y - drop[1])
        if distancia < distancia_drop:
            drop_mais_proximo = drop
            distancia_drop = distancia
    if drop_mais_proximo is not None and distancia_drop <= 1.15:
        tipo_arma = drop_mais_proximo[2]
        if tipo_arma not in armas_desbloqueadas:
            armas_desbloqueadas.add(tipo_arma)
            selecionar_arma(tipo_arma)
            nome_arma = "RIFLE" if tipo_arma == ARMA_RIFLE else "MOTOSERRA"
            mensagem = f"VOCE PEGOU: {nome_arma}!"
            tempo_mensagem = 110
        else:
            mensagem = "VOCE JA POSSUI ESTA ARMA"
            tempo_mensagem = 70
        drops_armas.remove(drop_mais_proximo)
        return

    # Prioridade 3: porta. A função já verifica se o jogador tem a chave.
    distancia_porta = math.hypot(
        x - (PORTA_X + 0.5), y - (PORTA_Y + 0.5)
    )
    if distancia_porta <= 2.0:
        alternar_porta()
        return

    # Prioridade 4: botão de conclusão/avanço de fase.
    distancia_botao = math.hypot(
        x - (BOTAO_X + 0.5), y - (BOTAO_Y + 0.5)
    )
    if distancia_botao <= 1.2:
        tentar_ativar_botao()
        return

    mensagem = "NAO HA NADA PARA INTERAGIR PERTO"
    tempo_mensagem = 60

def atualizar_porta():
    global porta_estado
    global porta_animacao

    velocidade = 1.0 / PORTA_TEMPO_ANIMACAO

    if porta_estado == 1:
        porta_animacao += velocidade

        if porta_animacao >= 1.0:
            porta_animacao = 1.0
            porta_estado = 2
            caminhos.clear()

    elif porta_estado == 3:
        porta_animacao -= velocidade

        if porta_animacao <= 0.0:
            porta_animacao = 0.0
            porta_estado = 0
            caminhos.clear()

def tentar_atirar():
    global tiro
    global cooldown_tiro
    global rifle_municao
    global pistola_municao

    if RECARREGANDO:
        return

    if cooldown_tiro > 0:
        return

    if arma_atual == ARMA_MOTOSERRA:
        tiro = 5
        cooldown_tiro = MOTOSERRA_COOLDOWN
        return

    if arma_atual == ARMA_RIFLE:
        if rifle_municao <= 0:
            return

        rifle_municao -= 1
        cooldown_tiro = RIFLE_COOLDOWN

    else:
        if pistola_municao <= 0:
            return

        pistola_municao -= 1
        cooldown_tiro = PISTOLA_COOLDOWN

    tiro = 6

def iniciar_recarga():
    global RECARREGANDO
    global rifle_tempo_recarga
    global pistola_tempo_recarga

    if RECARREGANDO:
        return

    if arma_atual == ARMA_MOTOSERRA:
        return

    if arma_atual == ARMA_RIFLE:
        if rifle_municao >= rifle_municao_max:
            return

        if rifle_reserva <= 0:
            return

        rifle_tempo_recarga = RIFLE_TEMPO_RECARREGA

    else:
        if pistola_municao >= pistola_municao_max:
            return

        if pistola_reserva <= 0:
            return

        pistola_tempo_recarga = PISTOLA_TEMPO_RECARREGA

    RECARREGANDO = True

def atualizar_recarga():
    global RECARREGANDO
    global rifle_municao
    global rifle_reserva
    global pistola_municao
    global pistola_reserva
    global rifle_tempo_recarga
    global pistola_tempo_recarga

    if not RECARREGANDO:
        return

    if arma_atual == ARMA_RIFLE:
        rifle_tempo_recarga -= 1

        if rifle_tempo_recarga <= 0:
            necessario = rifle_municao_max - rifle_municao

            quantidade = min(
                necessario,
                rifle_reserva
            )

            rifle_municao += quantidade
            rifle_reserva -= quantidade

            RECARREGANDO = False

    else:
        pistola_tempo_recarga -= 1

        if pistola_tempo_recarga <= 0:
            necessario = pistola_municao_max - pistola_municao

            quantidade = min(
                necessario,
                pistola_reserva
            )

            pistola_municao += quantidade
            pistola_reserva -= quantidade

            RECARREGANDO = False

def tentar_curar():
    global vida_jogador
    global tempo_cura

    if tempo_cura > 0:
        return

    if vida_jogador >= vida_maxima:
        return

    vida_jogador = min(
        vida_maxima,
        vida_jogador + CURA
    )

    tempo_cura = TEMPO_CURA

def atualizar_stamina(correndo, andando):
    global stamina
    global cansado
    global tempo_cansado

    if cansado:
        tempo_cansado -= 1
        stamina += RECUPERACAO_STAMINA * 0.5

        if stamina >= STAMINA_MAXIMA:
            stamina = STAMINA_MAXIMA
            cansado = False

        return

    if correndo and andando:
        stamina -= DRENAGEM_STAMINA

        if stamina <= 0:
            stamina = 0
            cansado = True
            tempo_cansado = TEMPO_CANSADO

    else:
        stamina += RECUPERACAO_STAMINA
        stamina = min(
            stamina,
            STAMINA_MAXIMA
        )

def tentar_ativar_botao():
    global mensagem
    global tempo_mensagem
    global mudando_fase
    global tempo_transicao
    global jogo_vencido

    if mudando_fase or jogo_vencido:
        return

    distancia = math.hypot(
        x - (BOTAO_X + 0.5),
        y - (BOTAO_Y + 0.5)
    )

    if distancia > 1.2:
        mensagem = "APROXIME-SE DO BOTAO"
        tempo_mensagem = 60
        return

    if len(inimigos) > 0:
        mensagem = (
            f"ELIMINE TODOS OS INIMIGOS! RESTAM {len(inimigos)}"
        )
        tempo_mensagem = 90
        return

    if fase == 0:
        mudando_fase = True
        tempo_transicao = TEMPO_TRANSICAO
        mensagem = "FASE 1 CONCLUIDA!"
        tempo_mensagem = TEMPO_TRANSICAO
    else:
        jogo_vencido = True

def desenhar_porta_minimapa():
    px = MINIMAPA_X + PORTA_X * T
    py = MINIMAPA_Y + PORTA_Y * T

    if porta_estado != 2:
        pygame.draw.rect(
            tela,
            (170, 90, 25),
            (px, py, T, T)
        )

        pygame.draw.rect(
            tela,
            (255, 210, 60),
            (px, py, T, T),
            1
        )
    else:
        pygame.draw.rect(
            tela,
            (40, 210, 80),
            (px, py, T, T)
        )

def desenhar_botao_minimapa():
    px = MINIMAPA_X + BOTAO_X * T
    py = MINIMAPA_Y + BOTAO_Y * T

    if len(inimigos) == 0:
        cor = (40, 230, 80)
    else:
        cor = (210, 45, 45)

    pygame.draw.rect(
        tela,
        cor,
        (px, py, T, T)
    )

    pygame.draw.rect(
        tela,
        (255, 255, 255),
        (px, py, T, T),
        1
    )

def desenhar_stamina():
    largura = 155
    altura = 13

    pos_x = LARGURA - largura - 12
    pos_y = 45

    pygame.draw.rect(
        tela,
        (15, 15, 18),
        (
            pos_x - 4,
            pos_y - 4,
            largura + 8,
            altura + 8
        )
    )

    pygame.draw.rect(
        tela,
        (70, 70, 75),
        (
            pos_x,
            pos_y,
            largura,
            altura
        ),
        2
    )

    largura_stamina = int(
        largura
        *
        max(0, stamina)
        /
        STAMINA_MAXIMA
    )

    if cansado:
        cor = (220, 70, 50)
    elif stamina > 50:
        cor = (70, 210, 220)
    else:
        cor = (230, 180, 50)

    pygame.draw.rect(
        tela,
        cor,
        (
            pos_x + 2,
            pos_y + 2,
            max(0, largura_stamina - 4),
            altura - 4
        )
    )

    texto = fonte_pequena.render(
        "CANSADO" if cansado else "STAMINA",
        True,
        (255, 255, 255)
    )

    tela.blit(
        texto,
        (pos_x, pos_y + 13)
    )

def desenhar_vida():
    largura = 155
    altura = 15

    pos_x = LARGURA - largura - 12
    pos_y = 12

    pygame.draw.rect(
        tela,
        (15, 15, 18),
        (
            pos_x - 4,
            pos_y - 4,
            largura + 8,
            altura + 28
        )
    )

    pygame.draw.rect(
        tela,
        (70, 70, 75),
        (
            pos_x,
            pos_y,
            largura,
            altura
        ),
        2
    )

    largura_vida = int(
        largura
        *
        max(0, vida_jogador)
        /
        vida_maxima
    )

    if vida_jogador > 60:
        cor = (40, 210, 70)
    elif vida_jogador > 30:
        cor = (240, 190, 40)
    else:
        cor = (220, 45, 40)

    pygame.draw.rect(
        tela,
        cor,
        (
            pos_x + 2,
            pos_y + 2,
            max(0, largura_vida - 4),
            altura - 4
        )
    )

    texto = fonte_pequena.render(
        f"VIDA {vida_jogador}/{vida_maxima}",
        True,
        (255, 255, 255)
    )

    tela.blit(
        texto,
        (pos_x, pos_y + 14)
    )

def selecionar_arma(tipo):
    """Equipa somente armas que o jogador já encontrou."""
    global arma_atual, RECARREGANDO, mensagem, tempo_mensagem
    if tipo not in (ARMA_RIFLE, ARMA_PISTOLA, ARMA_MOTOSERRA):
        return
    if tipo not in armas_desbloqueadas:
        nomes = {ARMA_RIFLE: "RIFLE", ARMA_PISTOLA: "PISTOLA", ARMA_MOTOSERRA: "MOTOSERRA"}
        mensagem = f"{nomes[tipo]} BLOQUEADA: ENCONTRE NO CENARIO"
        tempo_mensagem = 75
        return
    arma_atual = tipo
    RECARREGANDO = False


def trocar_arma_circular(direcao):
    """Alterna apenas entre as armas já desbloqueadas."""
    disponiveis = [a for a in (ARMA_PISTOLA, ARMA_RIFLE, ARMA_MOTOSERRA) if a in armas_desbloqueadas]
    if not disponiveis:
        return
    indice = disponiveis.index(arma_atual) if arma_atual in disponiveis else 0
    selecionar_arma(disponiveis[(indice + direcao) % len(disponiveis)])


def desenhar_indicador_arma():
    """Mostra a arma equipada e a munição, no canto inferior esquerdo."""
    if arma_atual == ARMA_RIFLE:
        nome, tecla, cor, simbolo = "RIFLE", "1", (255, 200, 50), "▰"
        municao, reserva = rifle_municao, rifle_reserva
    elif arma_atual == ARMA_PISTOLA:
        nome, tecla, cor, simbolo = "PISTOLA", "2", (80, 190, 255), "▰"
        municao, reserva = pistola_municao, pistola_reserva
    else:
        nome, tecla, cor, simbolo = "MOTOSERRA", "3", (240, 90, 55), "✦"
        municao, reserva = None, None

    painel_w, painel_h = 215, 66
    painel_x = 10
    painel_y = ALTURA - painel_h - 10

    pygame.draw.rect(
        tela, (15, 18, 24),
        (painel_x, painel_y, painel_w, painel_h),
        border_radius=8
    )
    pygame.draw.rect(
        tela, cor,
        (painel_x, painel_y, painel_w, painel_h),
        2, border_radius=8
    )

    tela.blit(
        fonte_pequena.render(f"{simbolo} {nome} [{tecla}]", True, cor),
        (painel_x + 10, painel_y + 8)
    )

    if municao is not None:
        texto_municao = f"MUNIÇÃO  {municao}/{reserva}"
    else:
        texto_municao = "CORPO A CORPO"

    tela.blit(
        fonte_pequena.render(texto_municao, True, (235, 235, 240)),
        (painel_x + 10, painel_y + 38)
    )


def desenhar_hud():
    # O painel de arma e munição é desenhado por desenhar_indicador_arma().
    # Aqui ficam apenas os avisos de recarga e o número da fase.
    if menu_armas:
        return

    if arma_atual == ARMA_RIFLE:
        municao = rifle_municao
    elif arma_atual == ARMA_PISTOLA:
        municao = pistola_municao
    else:
        municao = None

    if configuracoes_jogabilidade["arma_municao"] and RECARREGANDO:
        texto = fonte.render(
            "RECARREGANDO...",
            True,
            (255, 210, 50)
        )
        tela.blit(texto, texto.get_rect(center=(300, 25)))

    elif configuracoes_jogabilidade["arma_municao"] and arma_atual != ARMA_MOTOSERRA and municao == 0:
        texto = fonte_pequena.render(
            "R = RECARREGAR",
            True,
            (255, 80, 60)
        )
        tela.blit(texto, (230, 15))

    if configuracoes_jogabilidade["fase_chave"]:
        texto_fase = fonte_pequena.render(
            f"FASE {fase + 1}/2",
            True,
            (255, 255, 255)
        )
        tela.blit(texto_fase, (15, 15))

    if configuracoes_jogabilidade["fase_chave"] and fase == 0:
        estado_chave = "CHAVE: SIM" if tem_chave else "CHAVE: NAO"
        cor_chave = (255, 220, 65) if tem_chave else (190, 190, 190)
        tela.blit(
            fonte_pequena.render(estado_chave, True, cor_chave),
            (15, 34)
        )

def desenhar_guias():
    if menu_armas or not configuracoes_jogabilidade["dicas"]:
        return

    fundo = pygame.Surface(
        (220, 125),
        pygame.SRCALPHA
    )

    fundo.fill(
        (5, 7, 10, 190)
    )

    tela.blit(
        fundo,
        (LARGURA - 228, ALTURA - 133)
    )

    comandos = [
        ("E - INTERAGIR", (255, 210, 75)),
        ("F - CURAR", (90, 220, 110)),
        ("SHIFT - CORRER", (80, 210, 230))
    ]

    for i, dados in enumerate(comandos):
        texto, cor = dados

        tela.blit(
            fonte_pequena.render(
                texto,
                True,
                cor
            ),
            (
                LARGURA - 180,
                ALTURA - 115 + i * 20
            )
        )

    drop_perto = next((d for d in drops_armas if math.hypot(x - d[0], y - d[1]) <= 1.15), None)
    if drop_perto is not None:
        nome_drop = "RIFLE" if drop_perto[2] == ARMA_RIFLE else "MOTOSERRA"
        texto = f"E - PEGAR {nome_drop}"
        cor = (255, 200, 70) if drop_perto[2] == ARMA_RIFLE else (255, 100, 70)
    elif posicao_chave is not None and fase == 0 and math.hypot(x - posicao_chave[0], y - posicao_chave[1]) <= 1.0:
        texto = "E - PEGAR CHAVE"
        cor = (255, 220, 65)
    elif math.hypot(x - (PORTA_X + 0.5), y - (PORTA_Y + 0.5)) <= 2.0:
        texto = "E - USAR PORTA"
        cor = (70, 240, 100) if tem_chave or fase != 0 else (230, 70, 60)
    elif math.hypot(x - (BOTAO_X + 0.5), y - (BOTAO_Y + 0.5)) <= 1.2:
        texto = "E - ATIVAR BOTAO" if len(inimigos) == 0 else "MATE OS INIMIGOS"
        cor = (70, 240, 100) if len(inimigos) == 0 else (230, 70, 60)
    else:
        texto = "E - INTERAGIR"
        cor = (190, 195, 205)

    tela.blit(
        fonte_pequena.render(
            texto,
            True,
            cor
        ),
        (
            LARGURA - 180,
            ALTURA - 55
        )
    )

def desenhar_menu_armas():
    if not menu_armas:
        return

    camada = pygame.Surface(
        (LARGURA, ALTURA),
        pygame.SRCALPHA
    )

    camada.fill(
        (0, 0, 0, 170)
    )

    tela.blit(
        camada,
        (0, 0)
    )

    pygame.draw.rect(
        tela,
        (25, 27, 34),
        (80, 45, 440, 310)
    )

    pygame.draw.rect(
        tela,
        (100, 105, 120),
        (80, 45, 440, 310),
        3
    )

    titulo = fonte_grande.render(
        "MENU DE ARMAS",
        True,
        (255, 255, 255)
    )

    tela.blit(
        titulo,
        (185, 60)
    )

    armas = [
        ("1 - RIFLE", "12 balas | 100 dano", ARMA_RIFLE),
        ("2 - PISTOLA", "8 balas | 45 dano", ARMA_PISTOLA),
        ("3 - MOTOSERRA", "Corpo a corpo | 65 dano", ARMA_MOTOSERRA)
    ]

    for i, dados in enumerate(armas):
        nome, info, tipo = dados
        y_menu = 115 + i * 65

        desbloqueada = tipo in armas_desbloqueadas
        if not desbloqueada:
            nome = nome + " [BLOQUEADA]"
            info = "Encontre esta arma no cenario"
        if arma_atual == tipo:
            if tipo == ARMA_RIFLE:
                cor = (255, 200, 50)
            elif tipo == ARMA_PISTOLA:
                cor = (80, 190, 255)
            else:
                cor = (240, 70, 40)
        else:
            cor = (180, 180, 190) if desbloqueada else (105, 105, 115)

        pygame.draw.rect(
            tela,
            cor,
            (110, y_menu, 380, 55),
            2
        )

        tela.blit(
            fonte.render(
                nome,
                True,
                cor
            ),
            (125, y_menu + 7)
        )

        tela.blit(
            fonte_pequena.render(
                info,
                True,
                (190, 190, 200)
            ),
            (125, y_menu + 31)
        )

    tela.blit(
        fonte_pequena.render(
            "Clique para equipar | 1-3 ou scroll troca | M fecha",
            True,
            (160, 160, 170)
        ),
        (115, 330)
    )

def atualizar_inimigos():
    global contador_ia
    global vida_jogador
    global tempo_dano

    contador_ia += 1

    if contador_ia >= 12:
        contador_ia = 0

        objetivo = (
            int(x),
            int(y)
        )

        for indice, inimigo in enumerate(inimigos):
            inicio = (
                int(inimigo[0]),
                int(inimigo[1])
            )

            caminhos[indice] = encontrar_caminho(
                inicio,
                objetivo
            )

    for indice, inimigo in enumerate(inimigos):
        corrigir_inimigo_na_parede(inimigo)

        dx = x - inimigo[0]
        dy = y - inimigo[1]

        distancia = math.hypot(dx, dy)

        if distancia <= DISTANCIA_ATAQUE:
            if tempo_ataque_inimigos[indice] <= 0:
                vida_jogador = max(
                    0,
                    vida_jogador - DANO_INIMIGO
                )

                tempo_ataque_inimigos[indice] = INTERVALO_ATAQUE
                tempo_dano = 10

            continue

        if tempo_ataque_inimigos[indice] > 0:
            tempo_ataque_inimigos[indice] -= 1

        caminho = caminhos.get(
            indice,
            []
        )

        if caminho:
            proximo = caminho[0]

            destino_x = proximo[0] + 0.5
            destino_y = proximo[1] + 0.5

            dx = destino_x - inimigo[0]
            dy = destino_y - inimigo[1]

            distancia_ponto = math.hypot(
                dx,
                dy
            )

            if distancia_ponto > 0.05:
                dx /= distancia_ponto
                dy /= distancia_ponto

                mover_com_colisao(
                    inimigo,
                    dx * VELOCIDADE_INIMIGO,
                    dy * VELOCIDADE_INIMIGO,
                    RAIO_INIMIGO
                )

        elif distancia > 0:
            dx /= distancia
            dy /= distancia

            mover_com_colisao(
                inimigo,
                dx * VELOCIDADE_INIMIGO,
                dy * VELOCIDADE_INIMIGO,
                RAIO_INIMIGO
            )

    separar_inimigos()

    for inimigo in inimigos:
        corrigir_inimigo_na_parede(inimigo)

def desenhar_minimapa():
    """Desenha o mapa em escala compacta no canto superior direito."""
    global MINIMAPA_X, MINIMAPA_Y

    margem = 10
    largura_mapa = MAPA_LARGURA * T
    altura_mapa = MAPA_ALTURA * T
    MINIMAPA_X = LARGURA - largura_mapa - margem
    MINIMAPA_Y = margem

    # Fundo e moldura para separar o minimapa da cena 3D.
    painel = pygame.Rect(
        MINIMAPA_X - 4,
        MINIMAPA_Y - 4,
        largura_mapa + 8,
        altura_mapa + 8
    )
    pygame.draw.rect(tela, (5, 5, 8), painel)
    pygame.draw.rect(tela, (145, 145, 155), painel, 1)

    for my, linha in enumerate(mapa):
        for mx, c in enumerate(linha):
            cor = (78, 82, 90) if c == "#" else (24, 27, 32)
            pygame.draw.rect(
                tela, cor,
                (MINIMAPA_X + mx * T, MINIMAPA_Y + my * T, T, T)
            )

    desenhar_porta_minimapa()
    desenhar_botao_minimapa()

    if posicao_chave is not None and fase == 0:
        chave_mx = MINIMAPA_X + int(posicao_chave[0] * T)
        chave_my = MINIMAPA_Y + int(posicao_chave[1] * T)
        pygame.draw.circle(tela, (255, 210, 35), (chave_mx, chave_my), 3)
        pygame.draw.circle(tela, (255, 245, 150), (chave_mx, chave_my), 1)

    for inimigo in inimigos:
        pygame.draw.circle(
            tela, (220, 45, 45),
            (MINIMAPA_X + int(inimigo[0] * T), MINIMAPA_Y + int(inimigo[1] * T)),
            2
        )

    jogador_x = MINIMAPA_X + int(x * T)
    jogador_y = MINIMAPA_Y + int(y * T)
    pygame.draw.circle(tela, (255, 255, 255), (jogador_x, jogador_y), 3)
    pygame.draw.line(
        tela, (255, 230, 60),
        (jogador_x, jogador_y),
        (MINIMAPA_X + int((x + math.cos(ang)) * T),
         MINIMAPA_Y + int((y + math.sin(ang)) * T)),
        1
    )

def desenhar_transicao():
    tela.fill((5, 5, 10))

    texto = fonte_grande.render(
        "FASE 1 CONCLUIDA!",
        True,
        (70, 255, 100)
    )

    tela.blit(
        texto,
        texto.get_rect(
            center=(300, 150)
        )
    )

    texto2 = fonte.render(
        "Prepare-se para a FASE 2",
        True,
        (230, 230, 230)
    )

    tela.blit(
        texto2,
        texto2.get_rect(
            center=(300, 205)
        )
    )

    progresso = int(
        400 *
        (
            1 -
            tempo_transicao /
            TEMPO_TRANSICAO
        )
    )

    pygame.draw.rect(
        tela,
        (40, 40, 45),
        (100, 250, 400, 12)
    )

    pygame.draw.rect(
        tela,
        (70, 220, 100),
        (100, 250, progresso, 12)
    )

carregar_fase(0)

rodando = True

while rodando:

    for evento in pygame.event.get():

        if evento.type == pygame.KEYDOWN:

            if evento.key == pygame.K_F11:
                alternar_tela_cheia()

            elif evento.key == pygame.K_ESCAPE:
                if jogo_vencido or vida_jogador <= 0:
                    rodando = False
                elif mudando_fase:
                    pass
                elif menu_armas:
                    menu_armas = False
                elif jogo_pausado and menu_configuracoes:
                    if secao_configuracoes != "inicio":
                        secao_configuracoes = "inicio"
                    else:
                        menu_configuracoes = False
                else:
                    jogo_pausado = not jogo_pausado
                    if jogo_pausado:
                        tela_pausa = tela.copy()

            # Enquanto pausado, somente os controles
            # do menu ficam ativos.
            elif jogo_pausado:
                if menu_configuracoes:
                    pass
                elif evento.key == pygame.K_1:
                    jogo_pausado = False

                elif evento.key == pygame.K_2:
                    carregar_fase(fase)
                    jogo_pausado = False

                elif evento.key == pygame.K_3:
                    rodando = False

            elif evento.key == pygame.K_m:
                menu_armas = not menu_armas
                RECARREGANDO = False

            elif (
                evento.key in (pygame.K_1, pygame.K_2, pygame.K_3)
                and not jogo_pausado
                and not mudando_fase
                and not jogo_vencido
                and vida_jogador > 0
            ):
                if evento.key == pygame.K_1:
                    selecionar_arma(ARMA_RIFLE)
                elif evento.key == pygame.K_2:
                    selecionar_arma(ARMA_PISTOLA)
                elif evento.key == pygame.K_3:
                    selecionar_arma(ARMA_MOTOSERRA)

            elif (
                not mudando_fase
                and not jogo_vencido
                and vida_jogador > 0
            ):
                if evento.key == pygame.K_r:
                    iniciar_recarga()

                elif evento.key == pygame.K_f:
                    tentar_curar()

                elif evento.key == pygame.K_e:
                    tentar_interagir()

        # Scroll do mouse troca de arma rapidamente durante a partida.
        if evento.type == pygame.MOUSEWHEEL and not jogo_pausado and not mudando_fase:
            if evento.y > 0:
                trocar_arma_circular(-1)
            elif evento.y < 0:
                trocar_arma_circular(1)

        # Botão esquerdo do mouse dispara durante a partida.
        # Não dispara se o clique for usado em um menu ou na tela de pausa.
        if (
            evento.type == pygame.MOUSEBUTTONDOWN
            and evento.button == 1
            and not menu_armas
            and not jogo_pausado
            and not mudando_fase
            and not jogo_vencido
            and vida_jogador > 0
        ):
            tentar_atirar()

        # Clique em uma opção do menu também equipa a arma.
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1 and menu_armas:
            mx, my = converter_mouse_para_jogo(evento.pos)
            for indice, tipo in enumerate((ARMA_RIFLE, ARMA_PISTOLA, ARMA_MOTOSERRA)):
                if pygame.Rect(110, 115 + indice * 65, 380, 55).collidepoint(mx, my):
                    if tipo in armas_desbloqueadas:
                        selecionar_arma(tipo)
                        menu_armas = False
                    else:
                        selecionar_arma(tipo)  # Mostra aviso de arma bloqueada.
                    break

        if (
            evento.type == pygame.MOUSEBUTTONDOWN
            and evento.button == 1
            and jogo_pausado
        ):
            mx, my = converter_mouse_para_jogo(evento.pos)

            if menu_configuracoes:
                if secao_configuracoes == "inicio":
                    if pygame.Rect(105, 112, 390, 68).collidepoint(mx, my):
                        secao_configuracoes = "informacoes"
                    elif pygame.Rect(105, 198, 390, 68).collidepoint(mx, my):
                        secao_configuracoes = "controles"
                    elif pygame.Rect(180, 328, 240, 34).collidepoint(mx, my):
                        menu_configuracoes = False
                elif secao_configuracoes == "informacoes":
                    chaves_opcoes = ["minimapa", "vida", "stamina", "arma_municao", "dicas", "fase_chave"]
                    for i, chave in enumerate(chaves_opcoes):
                        if pygame.Rect(105, 94 + i * 34, 390, 29).collidepoint(mx, my):
                            configuracoes_jogabilidade[chave] = not configuracoes_jogabilidade[chave]
                            break
                    else:
                        if pygame.Rect(180, 316, 240, 34).collidepoint(mx, my):
                            secao_configuracoes = "inicio"
                elif pygame.Rect(180, 326, 240, 34).collidepoint(mx, my):
                    secao_configuracoes = "inicio"
            else:
                if pygame.Rect(145, 120, 310, 42).collidepoint(mx, my):
                    jogo_pausado = False
                elif pygame.Rect(145, 170, 310, 42).collidepoint(mx, my):
                    menu_configuracoes = True
                    secao_configuracoes = "inicio"
                elif pygame.Rect(145, 220, 310, 42).collidepoint(mx, my):
                    carregar_fase(fase)
                    jogo_pausado = False
                elif pygame.Rect(145, 270, 310, 42).collidepoint(mx, my):
                    rodando = False

    if jogo_pausado:
        if tela_pausa is not None:
            tela.blit(tela_pausa, (0, 0))
        desenhar_menu_pausa()
        atualizar_display()
        relogio.tick(FPS)
        continue

    elif mudando_fase:
        tempo_transicao -= 1

        if tempo_transicao <= 0:
            carregar_fase(1)

    elif not menu_armas and not jogo_vencido and vida_jogador > 0:

        teclas = pygame.key.get_pressed()

        # Rotação com aceleração gradual, em vez de começar/parar bruscamente.
        direcao_rotacao = int(teclas[pygame.K_d]) - int(teclas[pygame.K_a])
        velocidade_angular_alvo = direcao_rotacao * 0.05
        velocidade_angular_atual += (
            velocidade_angular_alvo - velocidade_angular_atual
        ) * 0.35
        ang += velocidade_angular_atual

        passo = int(teclas[pygame.K_w]) - int(teclas[pygame.K_s])
        andando = passo != 0

        correndo = (
            teclas[pygame.K_LSHIFT]
            or teclas[pygame.K_RSHIFT]
        )

        if correndo and stamina > 0 and not cansado:
            velocidade_alvo = VELOCIDADE_CORRENDO
        else:
            velocidade_alvo = VELOCIDADE_NORMAL
            correndo = False

        if passo < 0:
            velocidade_alvo *= -1
        elif passo == 0:
            velocidade_alvo = 0.0

        # Acelera e desacelera suavemente, preservando a colisão com paredes.
        fator_aceleracao = 0.28 if passo != 0 else 0.38
        velocidade_movimento_atual += (
            velocidade_alvo - velocidade_movimento_atual
        ) * fator_aceleracao

        if abs(velocidade_movimento_atual) < 0.002 and passo == 0:
            velocidade_movimento_atual = 0.0
        if direcao_rotacao == 0 and abs(velocidade_angular_atual) < 0.002:
            velocidade_angular_atual = 0.0

        atualizar_stamina(
            correndo and andando,
            andando
        )

        dx = math.cos(ang) * velocidade_movimento_atual
        dy = math.sin(ang) * velocidade_movimento_atual

        jogador_temp = [x, y]

        mover_com_colisao(
            jogador_temp,
            dx,
            dy,
            RAIO_JOGADOR
        )

        x = jogador_temp[0]
        y = jogador_temp[1]

    if cooldown_tiro > 0:
        cooldown_tiro -= 1

    if tiro > 0:
        tiro -= 1

    if tempo_dano > 0:
        tempo_dano -= 1

    if tempo_cura > 0:
        tempo_cura -= 1

    if tempo_mensagem > 0:
        tempo_mensagem -= 1

    atualizar_recarga()
    atualizar_porta()

    if (
        not menu_armas
        and not mudando_fase
        and not jogo_vencido
        and vida_jogador > 0
    ):
        atualizar_inimigos()

    tempo_animacao += 1
    pose = (tempo_animacao // 10) % 3

    if mudando_fase:
        desenhar_transicao()

    elif jogo_vencido:

        tela.fill((5, 25, 10))

        texto = fonte_grande.render(
            "VOCE VENCEU!",
            True,
            (70, 255, 100)
        )

        tela.blit(
            texto,
            texto.get_rect(
                center=(300, 140)
            )
        )

        texto2 = fonte.render(
            "As duas fases foram concluidas.",
            True,
            (220, 255, 220)
        )

        tela.blit(
            texto2,
            texto2.get_rect(
                center=(300, 190)
            )
        )

        texto3 = fonte.render(
            "Todos os inimigos foram eliminados.",
            True,
            (220, 255, 220)
        )

        tela.blit(
            texto3,
            texto3.get_rect(
                center=(300, 225)
            )
        )

        texto4 = fonte_pequena.render(
            "ESC para fechar",
            True,
            (180, 210, 185)
        )

        tela.blit(
            texto4,
            texto4.get_rect(
                center=(300, 270)
            )
        )

    elif vida_jogador <= 0:

        tela.fill((20, 5, 5))

        texto = fonte_grande.render(
            "VOCE MORREU",
            True,
            (230, 50, 50)
        )

        tela.blit(
            texto,
            texto.get_rect(
                center=(300, 180)
            )
        )

        texto2 = fonte.render(
            "ESC para fechar",
            True,
            (230, 230, 230)
        )

        tela.blit(
            texto2,
            texto2.get_rect(
                center=(300, 220)
            )
        )

    else:

        tela.fill((25, 27, 35))

        pygame.draw.rect(
            tela,
            (80, 48, 35),
            (0, 200, 600, 200)
        )

        dist = []

        for i in range(COLUNAS):

            a = (
                ang
                -
                FOV / 2
                +
                FOV * i / COLUNAS
            )

            d, bateu_porta = raio_com_porta(a)

            d_corrigida = d * math.cos(a - ang)

            dist.append(d_corrigida)

            luz = max(
                30,
                230 - d_corrigida * 22
            )

            altura = min(
                400,
                400 / max(
                    d_corrigida,
                    0.1
                )
            )

            if bateu_porta:
                cor = (
                    int(luz * 0.65),
                    int(luz * 0.32),
                    int(luz * 0.12)
                )
            else:
                cor = (
                    int(luz),
                    int(luz * 0.88),
                    int(luz * 0.72)
                )

            pygame.draw.rect(
                tela,
                cor,
                (
                    i * L,
                    200 - altura / 2,
                    L + 1,
                    altura
                )
            )

        # A chave aparece como um item 3D no cenário, respeitando as paredes.
        if posicao_chave is not None and fase == 0:
            dx_chave = posicao_chave[0] - x
            dy_chave = posicao_chave[1] - y
            distancia_chave = math.hypot(dx_chave, dy_chave)
            if distancia_chave > 0.05:
                rel_chave = (math.atan2(dy_chave, dx_chave) - ang + math.pi) % (2 * math.pi) - math.pi
                if abs(rel_chave) <= FOV / 2:
                    sx_chave = 300 + rel_chave / (FOV / 2) * 300
                    col_chave = int(sx_chave / L)
                    if 0 <= col_chave < COLUNAS and dist[col_chave] >= distancia_chave:
                        altura_chave = min(100, max(12, 75 / distancia_chave))
                        desenhar_sprite(sprite_chave, sx_chave, altura_chave, distancia_chave, dist)

        # Armas derrubadas aparecem no mundo 3D e respeitam a oclusao das paredes.
        for drop_x, drop_y, tipo_drop in drops_armas:
            dx_drop = drop_x - x
            dy_drop = drop_y - y
            distancia_drop = math.hypot(dx_drop, dy_drop)
            if distancia_drop <= 0.05:
                continue
            rel_drop = (math.atan2(dy_drop, dx_drop) - ang + math.pi) % (2 * math.pi) - math.pi
            if abs(rel_drop) <= FOV / 2:
                sx_drop = 300 + rel_drop / (FOV / 2) * 300
                col_drop = int(sx_drop / L)
                if 0 <= col_drop < COLUNAS and dist[col_drop] >= distancia_drop:
                    altura_drop = min(80, max(10, 55 / distancia_drop))
                    desenhar_sprite(sprites_drops_armas[tipo_drop], sx_drop, altura_drop, distancia_drop, dist)

        ordem = sorted(
            range(len(inimigos)),
            key=lambda i: -math.dist(
                inimigos[i],
                (x, y)
            )
        )

        inimigo_morto = None

        for indice in ordem:

            if indice >= len(inimigos):
                continue

            inimigo = inimigos[indice]

            dx = inimigo[0] - x
            dy = inimigo[1] - y

            distancia = math.hypot(dx, dy)

            if distancia <= 0:
                continue

            rel = (
                math.atan2(dy, dx)
                - ang
            )

            rel = (
                rel + math.pi
            ) % (
                2 * math.pi
            ) - math.pi

            if abs(rel) > FOV / 2:
                continue

            sx = (
                300
                +
                rel / (FOV / 2)
                * 300
            )

            col = int(sx / L)

            if not 0 <= col < COLUNAS:
                continue

            if dist[col] < distancia:
                continue

            altura = min(
                380,
                400 / max(
                    distancia,
                    0.1
                )
            )

            desenhar_sprite(
                sprites[pose],
                sx,
                altura,
                distancia,
                dist
            )

            vida = vida_inimigos[indice]

            barra_largura = max(
                20,
                int(altura * 0.4)
            )

            barra_x = int(
                sx - barra_largura / 2
            )

            barra_y = int(
                200 - altura - 10
            )

            pygame.draw.rect(
                tela,
                (20, 20, 20),
                (
                    barra_x,
                    barra_y,
                    barra_largura,
                    5
                )
            )

            vida_largura = int(
                barra_largura
                *
                max(0, vida)
                /
                vida_inimigo_maxima
            )

            pygame.draw.rect(
                tela,
                (220, 40, 40),
                (
                    barra_x,
                    barra_y,
                    vida_largura,
                    5
                )
            )

            pode_atacar = False

            if arma_atual == ARMA_MOTOSERRA:

                if distancia < 1.15:
                    if abs(sx - 300) < altura * 0.45:
                        pode_atacar = True

            else:

                if (
                    tiro > 0
                    and abs(sx - 300)
                    < altura * 0.22
                ):
                    pode_atacar = True

            if pode_atacar:

                if arma_atual == ARMA_RIFLE:
                    dano = DANO_RIFLE
                elif arma_atual == ARMA_PISTOLA:
                    dano = DANO_PISTOLA
                else:
                    dano = DANO_MOTOSERRA

                vida_inimigos[indice] -= dano
                tiro = 0

                if vida_inimigos[indice] <= 0:
                    inimigo_morto = indice
                    break

        if inimigo_morto is not None:
            # Alguns inimigos deixam armas no local onde foram derrotados.
            if inimigo_morto < len(inimigos_drop_arma):
                tipo_drop = inimigos_drop_arma[inimigo_morto]
                if tipo_drop is not None and tipo_drop not in armas_desbloqueadas:
                    drops_armas.append([
                        inimigos[inimigo_morto][0],
                        inimigos[inimigo_morto][1],
                        tipo_drop
                    ])
                    nome_drop = "RIFLE" if tipo_drop == ARMA_RIFLE else "MOTOSERRA"
                    mensagem = f"UM INIMIGO DERRUBOU: {nome_drop}! APERTE E PARA PEGAR"
                    tempo_mensagem = 120
            # O monstro portador deixa a chave exatamente onde foi derrotado.
            if inimigo_morto < len(inimigos_com_chave) and inimigos_com_chave[inimigo_morto]:
                if fase == 0 and not tem_chave and posicao_chave is None:
                    posicao_chave = [inimigos[inimigo_morto][0], inimigos[inimigo_morto][1]]
                    mensagem = "UM MONSTRO DERRUBOU UMA CHAVE!"
                    tempo_mensagem = 100
            inimigos.pop(inimigo_morto)
            vida_inimigos.pop(inimigo_morto)
            tempo_ataque_inimigos.pop(inimigo_morto)
            inimigos_com_chave.pop(inimigo_morto)
            if inimigo_morto < len(inimigos_drop_arma):
                inimigos_drop_arma.pop(inimigo_morto)
            caminhos.clear()

        if configuracoes_jogabilidade["minimapa"]:
            desenhar_minimapa()

        pygame.draw.line(
            tela,
            (255, 255, 255),
            (292, 200),
            (308, 200),
            2
        )

        pygame.draw.line(
            tela,
            (255, 255, 255),
            (300, 192),
            (300, 208),
            2
        )

        pygame.draw.circle(
            tela,
            (255, 255, 255),
            (300, 200),
            2
        )

        if not menu_armas:
            desenhar_arma()

        desenhar_hud()
        if configuracoes_jogabilidade["arma_municao"]:
            desenhar_indicador_arma()
        if configuracoes_jogabilidade["vida"]:
            desenhar_vida()
        if configuracoes_jogabilidade["stamina"]:
            desenhar_stamina()
        desenhar_guias()
        desenhar_menu_armas()

        if tempo_mensagem > 0:
            fundo = pygame.Surface(
                (500, 45),
                pygame.SRCALPHA
            )

            fundo.fill(
                (5, 5, 8, 210)
            )

            tela.blit(
                fundo,
                (50, 320)
            )

            texto = fonte.render(
                mensagem,
                True,
                (255, 220, 80)
            )

            tela.blit(
                texto,
                texto.get_rect(
                    center=(300, 342)
                )
            )

    atualizar_display()
    relogio.tick(FPS)

pygame.quit()
import pygame
import math
import heapq

pygame.init()

LARGURA = 600
ALTURA = 400
FPS = 30

tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Raycasting - 2 Fases")
relogio = pygame.time.Clock()

T = 8
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
        "#.............#..............#",
        "#.............#..............#",
        "#..####.......#......####....#",
        "#..#..........#......#.......#",
        "#..#..........#......#.......#",
        "#.............#..............#",
        "#.......###..................#",
        "#.......#......##............#",
        "#..............##............#",
        "#.............#..............#",
        "#.....####....#......####....#",
        "#.....#.......#......#.......#",
        "#.............#..............#",
        "#.............#..............#",
        "#.............#..............#",
        "##############################"
    ]
]

portas = [
    (13, 8),
    (13, 8)
]

botoes = [
    (26, 14),
    (26, 14)
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

arma_atual = ARMA_RIFLE
menu_armas = False

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

caminhos = {}
contador_ia = 0
tempo_animacao = 0

fonte = pygame.font.SysFont("consolas", 20, bold=True)
fonte_pequena = pygame.font.SysFont("consolas", 15, bold=True)
fonte_grande = pygame.font.SysFont("consolas", 28, bold=True)

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
    global caminhos
    global contador_ia
    global x
    global y
    global ang
    global mudando_fase
    global tempo_transicao

    fase = numero
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

    for pos in inimigos_por_fase[fase]:
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

    mudando_fase = False
    tempo_transicao = 0

def alternar_porta():
    global porta_estado

    distancia = math.hypot(
        x - (PORTA_X + 0.5),
        y - (PORTA_Y + 0.5)
    )

    if distancia > 2.0:
        return

    if porta_estado == 0:
        porta_estado = 1
        caminhos.clear()

    elif porta_estado == 2:
        if int(x) == PORTA_X and int(y) == PORTA_Y:
            return

        porta_estado = 3
        caminhos.clear()

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
    px = PORTA_X * T
    py = PORTA_Y * T

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
    px = BOTAO_X * T
    py = BOTAO_Y * T

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
    largura = 130
    altura = 10

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
    largura = 130
    altura = 12

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

def desenhar_hud():
    if menu_armas:
        return

    if arma_atual == ARMA_RIFLE:
        municao = rifle_municao
        reserva = rifle_reserva
        nome = "RIFLE"
        cor = (255, 200, 50)

    elif arma_atual == ARMA_PISTOLA:
        municao = pistola_municao
        reserva = pistola_reserva
        nome = "PISTOLA"
        cor = (80, 190, 255)

    else:
        municao = None
        reserva = None
        nome = "MOTOSERRA"
        cor = (240, 70, 40)

    pygame.draw.rect(
        tela,
        (10, 12, 16),
        (8, 345, 205, 48)
    )

    pygame.draw.rect(
        tela,
        (70, 75, 85),
        (8, 345, 205, 48),
        2
    )

    texto_nome = fonte_pequena.render(
        nome,
        True,
        cor
    )

    tela.blit(
        texto_nome,
        (18, 351)
    )

    if arma_atual == ARMA_MOTOSERRA:
        texto_municao = fonte_pequena.render(
            "SEM MUNICAO",
            True,
            (230, 230, 230)
        )
    else:
        texto_municao = fonte.render(
            f"{municao:02d} / {reserva:02d}",
            True,
            (245, 245, 245)
        )

    tela.blit(
        texto_municao,
        (85, 348)
    )

    if RECARREGANDO:
        texto = fonte.render(
            "RECARREGANDO...",
            True,
            (255, 210, 50)
        )

        tela.blit(
            texto,
            texto.get_rect(
                center=(300, 25)
            )
        )

    elif (
        arma_atual != ARMA_MOTOSERRA
        and municao == 0
    ):
        texto = fonte_pequena.render(
            "R = RECARREGAR",
            True,
            (255, 80, 60)
        )

        tela.blit(
            texto,
            (230, 15)
        )

    texto_fase = fonte_pequena.render(
        f"FASE {fase + 1}/2",
        True,
        (255, 255, 255)
    )

    tela.blit(
        texto_fase,
        (15, 15)
    )

def desenhar_guias():
    if menu_armas:
        return

    fundo = pygame.Surface(
        (180, 115),
        pygame.SRCALPHA
    )

    fundo.fill(
        (5, 7, 10, 190)
    )

    tela.blit(
        fundo,
        (LARGURA - 188, ALTURA - 123)
    )

    comandos = [
        ("F - CURAR", (90, 220, 110)),
        ("G - PORTA", (190, 145, 80)),
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

    if len(inimigos) == 0:
        texto = "E - ATIVAR BOTAO"
        cor = (70, 240, 100)
    else:
        texto = "MATE OS INIMIGOS"
        cor = (230, 70, 60)

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

        if arma_atual == tipo:
            if tipo == ARMA_RIFLE:
                cor = (255, 200, 50)
            elif tipo == ARMA_PISTOLA:
                cor = (80, 190, 255)
            else:
                cor = (240, 70, 40)
        else:
            cor = (180, 180, 190)

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
            "M ou ESC - fechar",
            True,
            (160, 160, 170)
        ),
        (225, 330)
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
    for my, linha in enumerate(mapa):
        for mx, c in enumerate(linha):
            if c == "#":
                pygame.draw.rect(
                    tela,
                    (70, 70, 70),
                    (
                        mx * T,
                        my * T,
                        T,
                        T
                    )
                )
            else:
                pygame.draw.rect(
                    tela,
                    (25, 25, 30),
                    (
                        mx * T,
                        my * T,
                        T,
                        T
                    )
                )

    desenhar_porta_minimapa()
    desenhar_botao_minimapa()

    for inimigo in inimigos:
        pygame.draw.circle(
            tela,
            (220, 30, 30),
            (
                int(inimigo[0] * T),
                int(inimigo[1] * T)
            ),
            3
        )

    pygame.draw.circle(
        tela,
        (255, 255, 255),
        (
            int(x * T),
            int(y * T)
        ),
        5
    )

    pygame.draw.line(
        tela,
        (255, 255, 0),
        (
            int(x * T),
            int(y * T)
        ),
        (
            int(
                (x + math.cos(ang)) * T
            ),
            int(
                (y + math.sin(ang)) * T
            )
        ),
        2
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

        if evento.type == pygame.QUIT:
            rodando = False

        if evento.type == pygame.KEYDOWN:

            if evento.key == pygame.K_ESCAPE:

                if jogo_vencido or vida_jogador <= 0:
                    rodando = False
                else:
                    menu_armas = False

            if evento.key == pygame.K_m:
                menu_armas = not menu_armas
                RECARREGANDO = False

            if menu_armas:

                if evento.key == pygame.K_1:
                    arma_atual = ARMA_RIFLE
                    RECARREGANDO = False

                elif evento.key == pygame.K_2:
                    arma_atual = ARMA_PISTOLA
                    RECARREGANDO = False

                elif evento.key == pygame.K_3:
                    arma_atual = ARMA_MOTOSERRA
                    RECARREGANDO = False

            elif not mudando_fase and not jogo_vencido and vida_jogador > 0:

                if evento.key == pygame.K_SPACE:
                    tentar_atirar()

                elif evento.key == pygame.K_r:
                    iniciar_recarga()

                elif evento.key == pygame.K_f:
                    tentar_curar()

                elif evento.key == pygame.K_g:
                    alternar_porta()

                elif evento.key == pygame.K_e:
                    tentar_ativar_botao()

    if mudando_fase:

        tempo_transicao -= 1

        if tempo_transicao <= 0:
            carregar_fase(1)

    elif not menu_armas and not jogo_vencido and vida_jogador > 0:

        teclas = pygame.key.get_pressed()

        if teclas[pygame.K_RIGHT]:
            ang += 0.05

        if teclas[pygame.K_LEFT]:
            ang -= 0.05

        passo = 0

        if teclas[pygame.K_UP]:
            passo += 1

        if teclas[pygame.K_DOWN]:
            passo -= 1

        andando = passo != 0

        correndo = (
            teclas[pygame.K_LSHIFT]
            or teclas[pygame.K_RSHIFT]
        )

        if correndo and stamina > 0 and not cansado:
            velocidade = VELOCIDADE_CORRENDO
        else:
            velocidade = VELOCIDADE_NORMAL
            correndo = False

        atualizar_stamina(
            correndo,
            andando
        )

        dx = math.cos(ang) * velocidade * passo
        dy = math.sin(ang) * velocidade * passo

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
            inimigos.pop(inimigo_morto)
            vida_inimigos.pop(inimigo_morto)
            tempo_ataque_inimigos.pop(inimigo_morto)
            caminhos.clear()

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
        desenhar_vida()
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

    pygame.display.flip()
    relogio.tick(FPS)

pygame.quit()
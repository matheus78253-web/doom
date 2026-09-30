import pygame
import math
import heapq

pygame.init()

LARGURA = 600
ALTURA = 400

tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Raycasting - IA e Colisão")

relogio = pygame.time.Clock()

mapa = [
    "########################",
    "#.....#................#",
    "#.....#................#",
    "#..#.....##............#",
    "#..#...#...#...........#",
    "#..#...#...............#",
    "#......................#",
    "#.....##...............#",
    "#......................#",
    "#.............#####....#",
    "#................#.....#",
    "#................#.....#",
    "#....#####.......#.....#",
    "#....#...........#.....#",
    "#....#................#",
    "########################"
]

T = 8
MAPA_ALTURA = len(mapa)
MAPA_LARGURA = len(mapa[0])

x = 1.5
y = 4.5
ang = 0.0

FOV = math.pi / 3
COLUNAS = 120
L = LARGURA // COLUNAS
RAIO_JOGADOR = 0.20

inimigos = [
    [9.5, 4.5],
    [12.5, 2.5],
    [16.5, 3.5],
    [20.5, 5.5],
    [8.5, 7.5],
    [14.5, 8.5],
    [18.5, 9.5],
    [21.5, 10.5],
    [16.5, 12.5],
    [7.5, 13.5],
    [12.5, 14.5]
]

RAIO_INIMIGO = 0.23
VELOCIDADE_INIMIGO = 0.035
DISTANCIA_ATAQUE = 0.75

tiro = 0
caminhos = {}
contador_ia = 0

def parede(px, py):
    if px < 0 or py < 0:
        return True
    if px >= MAPA_LARGURA or py >= MAPA_ALTURA:
        return True
    return mapa[int(py)][int(px)] == "#"

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

    for ponto_x, ponto_y in pontos:
        if parede(ponto_x, ponto_y):
            return False

    return True

def mover_com_colisao(obj, dx, dy, raio):
    novo_x = obj[0] + dx

    if pode_andar(novo_x, obj[1], raio):
        obj[0] = novo_x

    novo_y = obj[1] + dy

    if pode_andar(obj[0], novo_y, raio):
        obj[1] = novo_y

def raio(a):
    c = math.cos(a)
    s = math.sin(a)
    d = 0

    while d < 30:
        if parede(x + c * d, y + s * d):
            return d
        d += 0.04

    return 30

def heuristica(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def vizinhos(no):
    x_grid, y_grid = no

    direcoes = [
        (1, 0),
        (-1, 0),
        (0, 1),
        (0, -1)
    ]

    resultado = []

    for dx, dy in direcoes:
        nx = x_grid + dx
        ny = y_grid + dy

        if nx < 0 or ny < 0:
            continue

        if nx >= MAPA_LARGURA or ny >= MAPA_ALTURA:
            continue

        if mapa[ny][nx] == "#":
            continue

        resultado.append((nx, ny))

    return resultado

def encontrar_caminho(inicio, objetivo):
    inicio = (int(inicio[0]), int(inicio[1]))
    objetivo = (int(objetivo[0]), int(objetivo[1]))

    if parede(objetivo[0], objetivo[1]):
        return []

    fila = []
    contador = 0

    heapq.heappush(fila, (0, contador, inicio))

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
                    novo_custo +
                    heuristica(vizinho, objetivo)
                )

                contador += 1

                heapq.heappush(
                    fila,
                    (prioridade, contador, vizinho)
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

            distancia_minima = RAIO_INIMIGO * 2

            if distancia == 0:
                dx = 0.01
                dy = 0.01
                distancia = math.hypot(dx, dy)

            if distancia < distancia_minima:
                empurrao = distancia_minima - distancia

                nx = dx / distancia
                ny = dy / distancia

                novo_ax = a[0] + nx * empurrao * 0.5
                novo_ay = a[1] + ny * empurrao * 0.5
                novo_bx = b[0] - nx * empurrao * 0.5
                novo_by = b[1] - ny * empurrao * 0.5

                if pode_andar(novo_ax, novo_ay, RAIO_INIMIGO):
                    a[0] = novo_ax
                    a[1] = novo_ay

                if pode_andar(novo_bx, novo_by, RAIO_INIMIGO):
                    b[0] = novo_bx
                    b[1] = novo_by

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

    pygame.draw.rect(sprite, (0, 0, 0, 100), (4, 29, 16, 2))

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

    if pose == 0:
        pygame.draw.rect(sprite, pele, (2, 13, 4, 10))
        pygame.draw.rect(sprite, pele, (18, 15, 4, 8))
    elif pose == 1:
        pygame.draw.rect(sprite, pele, (2, 15, 4, 8))
        pygame.draw.rect(sprite, pele, (18, 12, 4, 10))
    else:
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
    pygame.draw.rect(sprite, branco, (10, 9, 1, 1))
    pygame.draw.rect(sprite, branco, (13, 9, 1, 1))

    pygame.draw.rect(sprite, metal, (5, 13, 3, 4))
    pygame.draw.rect(sprite, metal, (16, 13, 3, 4))

    return sprite

sprites = [
    criar_sprite(0),
    criar_sprite(1),
    criar_sprite(2)
]

def desenhar_sprite(sprite, sx, altura):
    proporcao = sprite.get_width() / sprite.get_height()

    largura = max(1, int(altura * proporcao))
    altura = max(1, int(altura))

    sprite_grande = pygame.transform.scale(
        sprite,
        (largura, altura)
    )

    pos_x = int(sx - largura / 2)
    pos_y = int(200 + altura / 2)

    tela.blit(
        sprite_grande,
        (pos_x, pos_y - altura)
    )

rodando = True
tempo_animacao = 0
contador_ia = 0

while rodando:

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False

        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_SPACE:
                tiro = 6

    k = pygame.key.get_pressed()

    ang += (
        k[pygame.K_RIGHT] -
        k[pygame.K_LEFT]
    ) * 0.05

    passo = (
        k[pygame.K_UP] -
        k[pygame.K_DOWN]
    ) * 0.08

    dx = math.cos(ang) * passo
    dy = math.sin(ang) * passo

    jogador_temp = [x, y]

    mover_com_colisao(
        jogador_temp,
        dx,
        dy,
        RAIO_JOGADOR
    )

    x = jogador_temp[0]
    y = jogador_temp[1]

    contador_ia += 1

    if contador_ia >= 12:
        contador_ia = 0
        objetivo = (int(x), int(y))

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
        dx = x - inimigo[0]
        dy = y - inimigo[1]

        distancia = math.hypot(dx, dy)

        if distancia <= DISTANCIA_ATAQUE:
            continue

        caminho = caminhos.get(indice, [])

        if caminho:
            proximo = caminho[0]

            destino_x = proximo[0] + 0.5
            destino_y = proximo[1] + 0.5

            dx = destino_x - inimigo[0]
            dy = destino_y - inimigo[1]

            distancia_ponto = math.hypot(dx, dy)

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

    tempo_animacao += 1
    pose = (tempo_animacao // 10) % 3

    tela.fill((25, 27, 35))

    pygame.draw.rect(
        tela,
        (80, 48, 35),
        (0, 200, 600, 200)
    )

    dist = []

    for i in range(COLUNAS):
        a = (
            ang -
            FOV / 2 +
            FOV * i / COLUNAS
        )

        d = raio(a)

        px = x + math.cos(a) * d
        py = y + math.sin(a) * d

        d *= math.cos(a - ang)

        dist.append(d)

        luz = max(30, 230 - d * 22)

        if abs(px - round(px)) < 0.03:
            luz *= 0.7

        altura = min(
            400,
            400 / max(d, 0.1)
        )

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

    for indice in ordem:
        inimigo = inimigos[indice]

        dx = inimigo[0] - x
        dy = inimigo[1] - y

        distancia = math.hypot(dx, dy)

        if distancia <= 0:
            continue

        rel = math.atan2(dy, dx) - ang
        rel = (
            rel + math.pi
        ) % (2 * math.pi) - math.pi

        if abs(rel) > FOV / 2:
            continue

        sx = 300 + rel / (FOV / 2) * 300

        col = int(sx / L)

        if not 0 <= col < COLUNAS:
            continue

        if dist[col] < distancia:
            continue

        altura = min(
            380,
            400 / max(distancia, 0.1)
        )

        desenhar_sprite(
            sprites[pose],
            sx,
            altura
        )

        if (
            tiro == 6 and
            abs(sx - 300) < altura * 0.22
        ):
            inimigos.pop(indice)
            caminhos.clear()
            tiro = 5
            break

    for my, linha in enumerate(mapa):
        for mx, c in enumerate(linha):
            if c == "#":
                pygame.draw.rect(
                    tela,
                    (70, 70, 70),
                    (mx * T, my * T, T, T)
                )

    for ex, ey in inimigos:
        pygame.draw.circle(
            tela,
            (220, 30, 30),
            (int(ex * T), int(ey * T)),
            3
        )

    pygame.draw.circle(
        tela,
        (255, 255, 255),
        (int(x * T), int(y * T)),
        5
    )

    if tiro > 0:
        pygame.draw.circle(
            tela,
            (255, 100, 0),
            (300, 270),
            34
        )

        pygame.draw.circle(
            tela,
            (255, 220, 0),
            (300, 270),
            18
        )

        tiro -= 1

    arma = [
        (255, 400),
        (280, 320),
        (320, 320),
        (345, 400)
    ]

    pygame.draw.polygon(
        tela,
        (70, 70, 70),
        arma
    )

    pygame.draw.rect(
        tela,
        (35, 35, 35),
        (288, 280, 24, 60)
    )

    pygame.draw.circle(
        tela,
        (255, 255, 255),
        (300, 200),
        3
    )

    pygame.display.flip()
    relogio.tick(30)

pygame.quit()

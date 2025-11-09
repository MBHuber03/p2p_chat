import socket
import struct
import time
import threading
from .utils import (
    MULTICAST_GROUP,
    MULTICAST_PORT,
    HEARTBEAT_TIMEOUT,
    HEARTBEAT_INTERVAL,
)


# ENTRAR NA REDE
def entrar_rede(self):
    # Servidor TCP para receber resposta do coordenador
    # Criar socket
    tcp_server = socket.socket(
        socket.AF_INET, socket.SOCK_STREAM
    )  # Familia do socket, Tipo do socket

    # Permitir que sockets que foram previamente vinculados a um enderecao sejam reutilizados (Utilizar mesmo ip)
    tcp_server.setsockopt(
        socket.SOL_SOCKET, socket.SO_REUSEADDR, 1
    )  # Nivel do socket (nesse caso API), Operacao, valor

    tcp_server.bind(
        (self.meu_ip, self.minha_porta)
    )  # Vincular socket a um endereco e porta

    tcp_server.listen(1)  # Permitir que um servidor aceite coneccoes
    tcp_server.settimeout(5)  # Definir o tempo para bloquear operacoes.

    # Enviar pedido de entrada por multicast
    udp_sock = socket.socket(
        socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
    )  # Familia do socket, Tipo do socket, protocolo

    # Definir a operacao de multicast com TTL (Time-to-live)
    udp_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, struct.pack("b", 1))
    msg = f"ENTRAR|{self.meu_ip}|{self.minha_porta}".encode()
    udp_sock.sendto(
        msg, (MULTICAST_GROUP, MULTICAST_PORT)
    )  # Enviar mensagem para o grupo multicast
    udp_sock.close()  # Fechar socket

    print("[INFO] Pedido de entrada enviado, aguardando resposta do coordenador...")

    try:
        conn, _ = (
            tcp_server.accept()
        )  # Aceitar coneccao, retornando objeto socket e o endereco
        data = conn.recv(1024).decode()  # Receber e armazenar mensagem
        conn.close()
        tcp_server.close()

        # Separar a mensagem para armazenar os valores do id atribuido pelo coordenador e seu coordenador nos campos do objeto no
        resposta = data.split("|")
        self.id = int(resposta[0])
        self.coordenador = int(resposta[1])

        # Atualizar o campo dos nos ativos na rede enviado pelo coordenador
        nos = resposta[2:]
        for n in nos:
            ip, porta, nid = n.split(",")
            self.nos_ativos[int(nid)] = (ip, int(porta))

        print(
            f"[INFO] Entrei na rede com ID {self.id}. Coordenador: {self.coordenador}"
        )
    except (
        socket.timeout
    ):  # Se nao existe nenhum coordenador (primeiro no que entrou na rede)
        # Assumir como coordenador
        print("[INFO] Nenhum coordenador respondeu — serei o coordenador.")
        self.id = 1
        self.coordenador = self.id
        self.nos_ativos[self.id] = (self.meu_ip, self.minha_porta)

        # Threads para o coordenador atribuir id aos novos nos da rede e enviar heartbeat para indicar que esta na rede
        threading.Thread(target=self.multicast_listener, daemon=True).start()
        threading.Thread(target=self.enviar_heartbeat, daemon=True).start()
    finally:
        tcp_server.close()


# MULTICAST LISTENER
def multicast_listener(self):
    # Criar socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

    # Permitir que sockets que foram previamente vinculados a um enderecao sejam reutilizados (Utilizar mesmo ip)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Vincular socket a todas as interfaces do sistema com a porta do grupo multicast
    sock.bind(("", MULTICAST_PORT))

    group = socket.inet_aton(
        MULTICAST_GROUP
    )  # Converte endereco para o formato necessario para operacoes com socket
    mreq = struct.pack(
        "4sL", group, socket.INADDR_ANY
    )  # Converte o endereco do grupo e da interface de rede para um formato necessario setsockopt()

    # Definir que o socket ira receber mensagens destinadas ao grupo multicast
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    print(f"[COORD] Escutando multicast em {MULTICAST_GROUP}:{MULTICAST_PORT}")

    while True:
        data = sock.recv(1024).decode()  # Receber mensagem de entrada na rede
        if not data.startswith("ENTRAR"):
            continue

        # Separar mensagem para atualizar nos ativos da rede e atribuir id ao no
        _, ip_novo, porta_nova = data.split("|")
        porta_nova = int(porta_nova)

        novo_id = self.proximo_id
        self.proximo_id += 1
        self.nos_ativos[novo_id] = (ip_novo, porta_nova)

        print(f"[COORD] Novo nó {ip_novo}:{porta_nova} entrou com ID {novo_id}")

        # Montar resposta com os nos ativos para o novo no da rede
        resposta = f"{novo_id}|{self.id}"
        for nid, (ip_existente, porta_existente) in self.nos_ativos.items():
            resposta += f"|{ip_existente},{porta_existente},{nid}"

        # Enviar a resposta via TCP
        try:
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.connect(
                (ip_novo, porta_nova)
            )  # Conectar ao socket com o ip e porta especificados
            conn.sendall(resposta.encode())
            conn.close()
            print(f"[COORD] Resposta enviada por TCP para {ip_novo}:{porta_nova}")
        except Exception as e:
            print(f"[ERRO] Falha ao enviar resposta TCP: {e}")

        # Notifica os outros nós sobre a entrada do novo nó
        for nid, (nip, nporta) in self.nos_ativos.items():
            if nid not in [self.id, novo_id]:
                try:
                    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    conn.connect((nip, nporta))
                    conn.sendall(f"NOVO_NO|{ip_novo}|{porta_nova}|{novo_id}".encode())
                    conn.close()
                    print(
                        f"[COORD] Resposta enviada por TCP para {ip_novo}:{porta_nova}"
                    )
                except Exception:
                    print(f"[ERRO] Falha ao avisar o nó {nid}")


# TCP LISTENER
def tcp_listener(self):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((self.meu_ip, self.minha_porta))
    server.listen(5)
    while not self.sair:
        try:
            # Aceitar coneccao e receber dados
            conn, _ = server.accept()
            data = conn.recv(1024).decode()

            # Se for uma mensagem, inserir no historico local do no o id, timestamp e o texto
            if data.startswith("MSG|"):
                _, nid, ts, msg = data.split("|", 3)
                self.historico.append((int(nid), int(ts), msg))
                print(f"[{nid}] {msg}")
            # Se for um heartbeat, atualizar o ultimo_heartbeat recebido pelo no
            elif data.startswith("HEARTBEAT"):
                self.ultimo_heartbeat = time.time()
            # Se for um anuncio de saida da rede, remover no dos nos ativos da rede
            elif data.startswith("SAIDA"):
                _, id_saida = data.split("|")
                id_saida = int(id_saida)
                if id_saida in self.nos_ativos:
                    del self.nos_ativos[id_saida]
                    print(f"[INFO] Nó {id_saida} saiu da rede.")
            # Se for uma mensagem de novo no do coordenador, atualizar nos ativos da rede
            elif data.startswith("NOVO_NO|"):
                _, ip_novo, porta_nova, novo_id = data.split("|")
                self.nos_ativos[int(novo_id)] = (ip_novo, int(porta_nova))
                print(
                    f"[INFO] Novo nó adicionado: {ip_novo}:{porta_nova} (ID {novo_id})"
                )

            conn.close()
        except Exception:
            continue


# ENVIAR MENSAGEM
def enviar_mensagem(self, texto):
    # Criar socket tcp para enviar mensagem para todos os nos da rede (mensagem do chat) e adicionar no historico de mensagens local
    self.timestamp += 1
    for nid, (ip, porta) in self.nos_ativos.items():
        if nid == self.id:
            continue
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((ip, porta))
            sock.send(f"MSG|{self.id}|{self.timestamp}|{texto}".encode())
            sock.close()
        except Exception:
            pass
    self.historico.append((self.id, self.timestamp, texto))
    print(f"[EU] {texto}")


# HEARTBEAT
def enviar_heartbeat(self):
    while not self.sair:
        # Criar socket tcp para enviar heartbeat a todos os nos da rede (Somente coordenador executa)
        for nid, (ip, porta) in list(self.nos_ativos.items()):
            if nid == self.id:
                continue
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((ip, porta))
                sock.send(b"HEARTBEAT")
                sock.close()
            except ConnectionRefusedError:
                self.enviar_mensagem(
                    f"[COORD] Falha ao enviar o heartbeat ao nó {nid}. Removendo nó da rede..."
                )

                # Remover no dos nos ativos da rede
                if nid in self.nos_ativos:
                    del self.nos_ativos[nid]

                # Criar socket para avisar outros nos sobre a saída.
                for no_id, (nip, nporta) in self.nos_ativos.items():
                    if no_id != self.id:
                        try:
                            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            sock.connect((nip, nporta))
                            sock.send(f"SAIDA|{nid}".encode())
                            sock.close()
                        except Exception:
                            pass
                # Mensagem no historico local.
                self.historico.append(
                    (self.id, self.timestamp, f"[COORD] Nó {nid} saiu da rede.")
                )
        time.sleep(HEARTBEAT_INTERVAL)


# MONITORAR FALHAS
def monitor_heartbeat(self):
    # Comparar (tempo atual - ultimo heartbeat do no local) com o timeout do heartbeat para detectar se o coordenador falhou
    while not self.sair:
        if self.coordenador != self.id:
            # Se o coordenador falhar, iniciar eleicao
            if time.time() - self.ultimo_heartbeat > HEARTBEAT_TIMEOUT:
                print("[ALERTA] Coordenador falhou! Iniciando eleição...")

                # Criar socket para avisar outros nos sobre a saída.
                for no_id, (nip, nporta) in self.nos_ativos.items():
                    if no_id != self.id:
                        try:
                            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            sock.connect((nip, nporta))
                            sock.send(f"SAIDA|{self.coordenador}".encode())
                            sock.close()
                        except Exception:
                            pass

                self.eleicao()
        time.sleep(1)

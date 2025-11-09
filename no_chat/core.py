import time
from .rede import (
    entrar_rede,
    multicast_listener,
    tcp_listener,
    enviar_mensagem,
    enviar_heartbeat,
    monitor_heartbeat,
)
from .eleicao import eleicao


class NoChat:
    def __init__(self, meu_ip, minha_porta):
        self.meu_ip = meu_ip
        self.id = None
        self.proximo_id = 2
        self.minha_porta = minha_porta
        self.coordenador = None
        self.nos_ativos = {}  # {id: (ip, porta)}
        self.historico = []
        self.timestamp = 0
        self.ultimo_heartbeat = time.time()
        self.sair = False

    # Metodos dos nos na rede.
    # ENTRAR NA REDE
    def entrar_rede(self):
        entrar_rede(self)

    # MULTICAST LISTENER
    def multicast_listener(self):
        multicast_listener(self)

    # TCP LISTENER
    def tcp_listener(self):
        tcp_listener(self)

    # ENVIAR MENSAGEM
    def enviar_mensagem(self, texto):
        enviar_mensagem(self, texto)

    # HEARTBEAT
    def enviar_heartbeat(self):
        enviar_heartbeat(self)

    # MONITORAR FALHAS
    def monitor_heartbeat(self):
        monitor_heartbeat(self)

    # ELEIÇÃO DO COORDENADOR
    def eleicao(self):
        eleicao(self)

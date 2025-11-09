import threading


# ELEIÇÃO
def eleicao(self):
    # No armazena valor do maior id na lista de nos ativos local para determinar o coordenador da rede
    maior_id = max(list(self.nos_ativos.keys()) + [self.id])
    self.coordenador = maior_id
    if self.coordenador == self.id:
        print("[INFO] Assumi o papel de coordenador.")
        # O coordenador eleito comeca a executar suas funcoes de receber mensagens multicast para entrar na rede e de enviar heartbeat para indicar que esta na rede
        threading.Thread(target=self.multicast_listener, daemon=True).start()
        threading.Thread(target=self.enviar_heartbeat, daemon=True).start()
    else:
        print(f"[INFO] Novo coordenador é o ID {self.coordenador}")

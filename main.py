import threading
from no_chat.core import NoChat

# MAIN
if __name__ == "__main__":
    meu_ip = input("Digite seu IP local (ex: 127.0.0.1): ").strip()
    minha_porta = int(input("Digite sua porta: "))

    no = NoChat(meu_ip, minha_porta)
    no.entrar_rede()
    # Thread para receber mensagens tcp (mensagens, atualizacao dos nos ativos, notificacao de saida de nos, ...)
    threading.Thread(target=no.tcp_listener, daemon=True).start()
    # Thread para verificar falha do coordenador
    threading.Thread(target=no.monitor_heartbeat, daemon=True).start()

    # Envio de mensagem.
    while True:
        msg = input()
        if msg.lower() == "sair":
            no.sair = True
            break
        no.enviar_mensagem(msg)

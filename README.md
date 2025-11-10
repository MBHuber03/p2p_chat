# p2p_chat

# Descrição
Sistema de Chat Distribuído com Tolerância a Falhas desenvolvido em Python, onde os nós entram na rede via multicast e trocam mensagens via TCP. O primeiro nó que entra na rede se torna o coordenador, responsável por atribuir id aos novos nós, enviar heartbeat periodicamente para indicar que está na rede e anunciar a saída de nós.
Caso o coordenador falhar ou sair da rede, os nós ativos começam uma eleição do novo coordenador, o nó de maior id.

# Funcionalidades
  - Multicast para entrada de nós na rede;
  - TCP para troca de mensagens, enviar heartbeat e anunciar saída de nós;
  - O coordenador envia heartbeat para indicar que está ativo;
  - Eleição baseada no maior id, caso o coordenador falhar;
  - O sistema se reorganiza após entrada ou saída de nós (atualização da lista local de nós ativos).

# Como executar
  1. Abrir terminal e executar: python3 main.py
  2. Digitar ip e porta.
  3. Enviar mensagens.
  4. Digitar "sair" para sair da rede.

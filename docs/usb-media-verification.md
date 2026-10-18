# Verificação da mídia USB

Em 18/10/2026, a ISO personalizada foi gravada no pendrive solicitado pelo
usuário, identificado no Windows como E antes da operação. A identificação
por dispositivo físico, serial, capacidade, barramento USB e ausência das
flags de disco de boot/sistema foi conferida antes da gravação.

Foram escritos 3616538624 bytes da imagem ISOHybrid, em modo direto, e lidos
novamente os mesmos bytes. A leitura usou I/O sem cache do Windows e o mesmo
SHA-256 foi confirmado para a fonte e para o conteúdo lido do dispositivo:

`a3b86acb7aca372082eb0d62db5b130ab3663510e5e8fb52bd0d1ff95dd4074f`

O gravador encerrou com sucesso. O mecanismo de I/O foi previamente exercitado
em um arquivo sintético, incluindo preservação dos bytes além do limite da
imagem e rejeição de um hash de origem incorreto. Nenhuma camada de IA local
foi executada. A preparação não reiniciou o computador nem instalou o Linux
no disco interno. O boot físico do PC ainda depende da seleção da mídia UEFI.

Serial, caminhos pessoais, conteúdo anterior do pendrive e recibo operacional
completo permanecem locais. Não foi alterado o arquivo ISO nem publicada a
imagem como download externo. Esta conferência cobre os bytes da imagem,
sem constituir teste de toda a capacidade ou de retenção prolongada do USB.

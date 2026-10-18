# Estado do projeto CachyOS Codex

Data: 18/10/2026.

## Entrega

ISO experimental pessoal preparada a partir da ISO oficial preservada.
O live usa Codex root em console e o instalador nativo headless. No destino,
o servi�o root de manuten��o exige login ChatGPT e mant�m limites de execu��o.
As �nicas interven��es humanas previstas s�o conversa com o Codex, OAuth,
senha local oculta e aprova��o do plano concreto de apagar o disco.

- SHA-256 da ISO: a3b86acb7aca372082eb0d62db5b130ab3663510e5e8fb52bd0d1ff95dd4074f.
- Tamanho: 3616538624 bytes.
- SHA-256 do payload: 620ac957ec40860423693f32a82267b607a82ee5d0322de5f414571184b960dd.
- Fonte original: 959f6577f45e25ee9fd8c220fd221b08e4ea79412c7315c0f922dd6d86d5e33c.
- Codex oficial completo 0.163.0, pacote musl fixado em build_inputs.py.
- Instalador nativo: 0.12.4-bb3eccb-20260804.

## Evid�ncias

32 testes unit�rios e compila��o Python passaram. O teste nativo completo
UEFI/KDE/btrfs/GRUB passou em disco virtual descart�vel de 32 GiB. O disco
instalado iniciou sem ISO e confirmou Codex, timer root, permiss�es, senha
sint�tica, root bloqueado e manuten��o sem modelo quando falta autentica��o.
O SquashFS oficial permaneceu id�ntico. Falhas e limites constam em
[docs/verification.md](docs/verification.md).

N�o houve OAuth, infer�ncia local ou remota, medi��o de FPS, reparo aut�nomo,
instala��o f�sica ou grava��o de pendrive. Os testes convencionais usaram CPU.
Root tem permiss�es amplas por autoriza��o humana; prompts n�o s�o sandbox.
Nenhum servi�o ou driver do Windows foi instalado. QEMU e depend�ncias ficaram
no cache da tarefa, sem alterar recursos do sistema.

## Publica��o

Reposit�rio p�blico autorizado: https://github.com/leankant1577/cachyos-codex-lab.
Somente fonte e evid�ncias resumidas s�o destinados � publica��o. A ISO � local.
A apresenta��o factual e o pedido de orienta��o � equipe est�o preparados em
[docs/community-report.md](docs/community-report.md). N�o publicar tokens,
credenciais ou logs privados.

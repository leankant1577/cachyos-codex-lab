# Estado do projeto CachyOS Codex

Data: 18/10/2026.

## Entrega

ISO experimental pessoal preparada a partir da ISO oficial preservada.
O live usa Codex root em console e o instalador nativo headless. No destino,
o serviço root de manutenção exige login ChatGPT e mantém limites de execução.
As únicas intervenções humanas previstas são conversa com o Codex, OAuth,
senha local oculta e aprovação do plano concreto de apagar o disco.

- SHA-256 da ISO: a3b86acb7aca372082eb0d62db5b130ab3663510e5e8fb52bd0d1ff95dd4074f.
- Tamanho: 3616538624 bytes.
- SHA-256 do payload: 620ac957ec40860423693f32a82267b607a82ee5d0322de5f414571184b960dd.
- Fonte original: 959f6577f45e25ee9fd8c220fd221b08e4ea79412c7315c0f922dd6d86d5e33c.
- Codex oficial completo 0.163.0, pacote musl fixado em build_inputs.py.
- Instalador nativo: 0.12.4-bb3eccb-20260804.

## Evidências

32 testes unitários e compilação Python passaram. O teste nativo completo
UEFI/KDE/btrfs/GRUB passou em disco virtual descartável de 32 GiB. O disco
instalado iniciou sem ISO e confirmou Codex, timer root, permissões, senha
sintética, root bloqueado e manutenção sem modelo quando falta autenticação.
O SquashFS oficial permaneceu idêntico. Falhas e limites constam em
[docs/verification.md](docs/verification.md).

Não houve OAuth, inferência local ou remota, medição de FPS, reparo autônomo,
instalação física ou gravação de pendrive. Os testes convencionais usaram CPU.
Root tem permissões amplas por autorização humana; prompts não são sandbox.
Nenhum serviço ou driver do Windows foi instalado. QEMU e dependências ficaram
no cache da tarefa, sem alterar recursos do sistema.

## Publicação

Repositório público autorizado: https://github.com/leankant1577/cachyos-codex-lab.
Somente fonte e evidências resumidas são destinados à publicação. A ISO é local.
A apresentação factual e o pedido de orientação à equipe estão preparados em
[docs/community-report.md](docs/community-report.md). Não publicar tokens,
credenciais ou logs privados.

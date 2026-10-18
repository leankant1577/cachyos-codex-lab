# Verificação da ISO personalizada

Data: 18/10/2026. Construção e testes convencionais locais, sem inferência.

## Artefato

- Arquivo: `cachyos-codex-260809.iso`.
- Tamanho: 3616538624 bytes.
- SHA-256: `a3b86acb7aca372082eb0d62db5b130ab3663510e5e8fb52bd0d1ff95dd4074f`.
- Payload: `620ac957ec40860423693f32a82267b607a82ee5d0322de5f414571184b960dd`.
- Codex oficial Linux musl completo, versão 0.163.0.
- Instalador existente na ISO: `0.12.4-bb3eccb-20260804`.

`verify_iso.py` confirmou o hash da imagem recebida, o checksum do payload
e a preservação byte a byte do SquashFS oficial. Seu SHA-256 é
`b65552654cbffda879d5a78cc9105808155fa79af74417cb4a43d0b0ceea2548`.
O sistema oficial não foi recomprimido. A ISO original permanece intacta.

## Verificações executadas

- `python -m pytest integrations/cachyos-codex/tests -q`: 32 testes passaram.
- `python -m compileall -q integrations/cachyos-codex`: sem erro de compilação.
- A versão do Codex e do instalador foi executada em Linux.
- Extração em um alvo temporário sob umask 077 conferiu executáveis,
  unidades systemd, timer, diretórios públicos 0755 e privados 0700,
  ausência de marcador live e ausência de autenticação embutida.
- A ISO final iniciou sob UEFI, com kernel e initramfs extraídos dela.
  O payload carregou, firstboot foi dispensado pela condição exclusiva do
  live e multi-user.target ficou ativo. O SHA-256 do payload carregado
  coincidiu com o recibo da imagem final.
- O CLI executou como root, validou o plano para CODEX-SMOKE-ONLY e confirmou
  ausência de login. A senha sintética foi coletada na VT local e o controle
  retornou à VT anterior, com modo 0600 e vínculo ao hash do plano.
- Um teste Linux montou a partição do disco virtual somente leitura e
  confirmou que validar-plano recusava esse disco por estar montado.

## Instalação nativa e persistência

A repetição completa UEFI/KDE/btrfs/GRUB concluiu com exit code 0 no instalador
nativo e no controlador. Foram instalados os kernels CachyOS e LTS. A integração
foi copiada para o alvo, a senha sintética aplicada e a senha de root bloqueada.
O plano aprovado foi registrado e as credenciais temporárias foram removidas.

O disco instalado iniciou sozinho, sem mídia ISO anexada. O teste confirmou
Codex 0.163.0, timer habilitado e ativo, permissões públicas e privadas, marcador
de instalação, senha sintética correta, root bloqueado e ausência de OAuth.
O serviço de manutenção foi acionado e terminou com sucesso sem chamar modelo.
O log privado é inicializado pelo entry point depois da montagem de @log.

O boot instalado carregou o kernel LTS 6.18.55-2-cachyos-lts. A interface gráfica
foi mascarada apenas no teste. A última construção acrescentou LICENSE e NOTICE
oficiais do Codex; o payload que chegou ao alvo já continha esses arquivos.
O código executável permaneceu igual entre esse teste e a imagem entregue.

## Falhas encontradas e corrigidas

1. Um checksum com CRLF era aceito pelo GNU e rejeitado pelo BusyBox do
   initramfs. A construção passou a gravar LF e verificar com ambos.
2. systemd-firstboot aguardava entrada antes de concluir sysinit. Uma condição
   exclusiva do live dispensa esse assistente e não é instalada no destino.
3. O controlador privado usava umask 077, herdado pelo instalador nativo.
   Isso criava /etc com modo 0700 e impedia resolução de nomes para alpm.
   A causa foi reproduzida dentro do chroot. O instalador filho agora recebe
   umask 022; o controlador mantém arquivos privados com 077. A extração
   também usa 022 temporariamente e restaura o valor anterior.
4. lsblk sem NAME exigia --tree para retornar children no JSON. As consultas
   de inventário e finalização agora pedem a árvore explicitamente.
5. A finalização revalida o disco e remove timer habilitado, autenticação
   copiada e marcadores recém-criados se uma etapa posterior falhar.

O instalador nativo concluiu em uma candidata anterior; a integração então
bloqueou na identificação da raiz, expondo o problema 4. Um teste de repetição
no mesmo disco foi interrompido pelo sfdisk por dispositivo ocupado, após
uma montagem temporária usada pelo teste. A repetição final usa outro disco
virtual vazio e um boot novo. Nenhuma proteção do sfdisk foi ignorada.

## Parâmetros e limites

QEMU WHPX já disponível no host, quatro vCPUs, 12 GiB de RAM, mídia somente
leitura e disco virtual próprio de 32 GiB. Nenhum disco físico foi anexado.
O kernel da VM recebe noapic para contornar um problema do temporizador
emulado. Esse ajuste não está na ISO. O shell serial e a máscara do agente
live também são exclusivos do teste, evitando login ou inferência. O
NetworkManager foi solicitado explicitamente porque o agente estava mascarado.

O registro híbrido BIOS/UEFI foi preservado por xorriso -boot_image any replay.
O menu UEFI carregou em uma candidata anterior; a validação final usa kernel
e initramfs da imagem sob UEFI. Boot BIOS, kernel LTS no live, interface gráfica
do desktop e hardware real não foram executados nestes testes.

Ainda não houve OAuth, conversa autenticada, avaliação de reparos ou comparação
de desempenho. A Intel Arc B580 e a instalação física não foram homologadas.
Depois dos testes da ISO, o pendrive solicitado foi gravado e o conteúdo
foi confirmado por SHA-256. Consulte usb-media-verification.md. Root tem acesso amplo por solicitação
humana; prompts orientam o escopo, mas não constituem sandbox independente.

A imagem final foi iniciada novamente após a inclusão das licenças. O live
confirmou o payload 620ac957ec40860423693f32a82267b607a82ee5d0322de5f414571184b960dd,
Codex root, multi-user.target ativo, plano válido, rejeição de partição montada,
extração sob umask 077, permissões e unidades. Nenhum instalador foi executado
nessa conferência final.

# Verifica��o da ISO personalizada

Data: 18/10/2026. Constru��o e testes convencionais locais, sem infer�ncia.

## Artefato

- Arquivo: `cachyos-codex-260809.iso`.
- Tamanho: 3616538624 bytes.
- SHA-256: `a3b86acb7aca372082eb0d62db5b130ab3663510e5e8fb52bd0d1ff95dd4074f`.
- Payload: `620ac957ec40860423693f32a82267b607a82ee5d0322de5f414571184b960dd`.
- Codex oficial Linux musl completo, vers�o 0.163.0.
- Instalador existente na ISO: `0.12.4-bb3eccb-20260804`.

`verify_iso.py` confirmou o hash da imagem recebida, o checksum do payload
e a preserva��o byte a byte do SquashFS oficial. Seu SHA-256 �
`b65552654cbffda879d5a78cc9105808155fa79af74417cb4a43d0b0ceea2548`.
O sistema oficial n�o foi recomprimido. A ISO original permanece intacta.

## Verifica��es executadas

- `python -m pytest integrations/cachyos-codex/tests -q`: 32 testes passaram.
- `python -m compileall -q integrations/cachyos-codex`: sem erro de compila��o.
- A vers�o do Codex e do instalador foi executada em Linux.
- Extra��o em um alvo tempor�rio sob umask 077 conferiu execut�veis,
  unidades systemd, timer, diret�rios p�blicos 0755 e privados 0700,
  aus�ncia de marcador live e aus�ncia de autentica��o embutida.
- A ISO final iniciou sob UEFI, com kernel e initramfs extra�dos dela.
  O payload carregou, firstboot foi dispensado pela condi��o exclusiva do
  live e multi-user.target ficou ativo. O SHA-256 do payload carregado
  coincidiu com o recibo da imagem final.
- O CLI executou como root, validou o plano para CODEX-SMOKE-ONLY e confirmou
  aus�ncia de login. A senha sint�tica foi coletada na VT local e o controle
  retornou � VT anterior, com modo 0600 e v�nculo ao hash do plano.
- Um teste Linux montou a parti��o do disco virtual somente leitura e
  confirmou que validar-plano recusava esse disco por estar montado.

## Instala��o nativa e persist�ncia

A repeti��o completa UEFI/KDE/btrfs/GRUB concluiu com exit code 0 no instalador
nativo e no controlador. Foram instalados os kernels CachyOS e LTS. A integra��o
foi copiada para o alvo, a senha sint�tica aplicada e a senha de root bloqueada.
O plano aprovado foi registrado e as credenciais tempor�rias foram removidas.

O disco instalado iniciou sozinho, sem m�dia ISO anexada. O teste confirmou
Codex 0.163.0, timer habilitado e ativo, permiss�es p�blicas e privadas, marcador
de instala��o, senha sint�tica correta, root bloqueado e aus�ncia de OAuth.
O servi�o de manuten��o foi acionado e terminou com sucesso sem chamar modelo.
O log privado � inicializado pelo entry point depois da montagem de @log.

O boot instalado carregou o kernel LTS 6.18.55-2-cachyos-lts. A interface gr�fica
foi mascarada apenas no teste. A �ltima constru��o acrescentou LICENSE e NOTICE
oficiais do Codex; o payload que chegou ao alvo j� continha esses arquivos.
O c�digo execut�vel permaneceu igual entre esse teste e a imagem entregue.

## Falhas encontradas e corrigidas

1. Um checksum com CRLF era aceito pelo GNU e rejeitado pelo BusyBox do
   initramfs. A constru��o passou a gravar LF e verificar com ambos.
2. systemd-firstboot aguardava entrada antes de concluir sysinit. Uma condi��o
   exclusiva do live dispensa esse assistente e n�o � instalada no destino.
3. O controlador privado usava umask 077, herdado pelo instalador nativo.
   Isso criava /etc com modo 0700 e impedia resolu��o de nomes para alpm.
   A causa foi reproduzida dentro do chroot. O instalador filho agora recebe
   umask 022; o controlador mant�m arquivos privados com 077. A extra��o
   tamb�m usa 022 temporariamente e restaura o valor anterior.
4. lsblk sem NAME exigia --tree para retornar children no JSON. As consultas
   de invent�rio e finaliza��o agora pedem a �rvore explicitamente.
5. A finaliza��o revalida o disco e remove timer habilitado, autentica��o
   copiada e marcadores rec�m-criados se uma etapa posterior falhar.

O instalador nativo concluiu em uma candidata anterior; a integra��o ent�o
bloqueou na identifica��o da raiz, expondo o problema 4. Um teste de repeti��o
no mesmo disco foi interrompido pelo sfdisk por dispositivo ocupado, ap�s
uma montagem tempor�ria usada pelo teste. A repeti��o final usa outro disco
virtual vazio e um boot novo. Nenhuma prote��o do sfdisk foi ignorada.

## Par�metros e limites

QEMU WHPX j� dispon�vel no host, quatro vCPUs, 12 GiB de RAM, m�dia somente
leitura e disco virtual pr�prio de 32 GiB. Nenhum disco f�sico foi anexado.
O kernel da VM recebe noapic para contornar um problema do temporizador
emulado. Esse ajuste n�o est� na ISO. O shell serial e a m�scara do agente
live tamb�m s�o exclusivos do teste, evitando login ou infer�ncia. O
NetworkManager foi solicitado explicitamente porque o agente estava mascarado.

O registro h�brido BIOS/UEFI foi preservado por xorriso -boot_image any replay.
O menu UEFI carregou em uma candidata anterior; a valida��o final usa kernel
e initramfs da imagem sob UEFI. Boot BIOS, kernel LTS no live, interface gr�fica
do desktop e hardware real n�o foram executados nestes testes.

Ainda n�o houve OAuth, conversa autenticada, avalia��o de reparos ou compara��o
de desempenho. A Intel Arc B580 e a instala��o f�sica n�o foram homologadas.
Nenhum pendrive foi formatado ou gravado. Root tem acesso amplo por solicita��o
humana; prompts orientam o escopo, mas n�o constituem sandbox independente.

A imagem final foi iniciada novamente ap�s a inclus�o das licen�as. O live
confirmou o payload 620ac957ec40860423693f32a82267b607a82ee5d0322de5f414571184b960dd,
Codex root, multi-user.target ativo, plano v�lido, rejei��o de parti��o montada,
extra��o sob umask 077, permiss�es e unidades. Nenhum instalador foi executado
nessa confer�ncia final.

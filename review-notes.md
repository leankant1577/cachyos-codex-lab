# Revisão da integração

Revisão de código e evidências em 18/10/2026, sem executar modelos.

O fluxo chama somente o instalador nativo em modo headless por JSON. O plano
exige disco inteiro identificado por serial, modelo, tamanho e caminho Linux.
UEFI é obrigatório. Alvos USB, removíveis ou montados são bloqueados, assim
como preservação, dual boot e raiz criptografada neste fluxo experimental.

A revisão independente resultou em revalidação do disco na finalização e
limpeza do timer e do OAuth recém-copiado se houver falha posterior. O teste
nativo revelou duas falhas que testes com mocks não cobriam: umask herdado e
formato real do JSON do lsblk. Ambas foram corrigidas e receberam verificações
unitárias e Linux direcionadas. A suíte atual contém 32 testes.

O timer root usa OAuth ChatGPT salvo, até quatro chamadas por dia UTC e pausa
após três falhas consecutivas no mesmo dia. Sem autenticação, não chama o modelo.
A qualidade das decisões administrativas ainda não foi avaliada. Prompts são
instruções ao agente e não impõem uma barreira de permissões ao root.

Não há promessa de ganho de FPS, reparo automático correto ou aprovação oficial
pelo CachyOS. As evidências e limitações atuais estão em docs/verification.md.

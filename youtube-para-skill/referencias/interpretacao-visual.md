# Interpretação visual dos quadros

Objetivo: transformar o que aparece na tela em ações reproduzíveis, encaixadas na fala.

## Entrada
- `trabalho/<id>.quadros.json`: lista em ordem de tempo `{arquivo, t, motivo, mudanca, fala}`.
- Imagens em `trabalho/<id>.quadros/` (abrir com a ferramenta de leitura de arquivo; o modelo vê a imagem).

## Leitura
1. Lotes de 6 quadros em ordem. Manter na memória só o último quadro do lote anterior (para comparar).
2. Para cada quadro, comparar com o anterior: o que mudou = a ação executada entre os dois.
3. Usar a `fala` do quadro para confirmar intenção e nomes.
4. Ler da imagem: nome do programa/site, caminho de menu, título da janela/aba, rótulo exato do botão/campo, valor digitado, comando no terminal, código no editor, mensagem de resultado, posição do cursor/realce.
5. Quadro sem mudança relevante → ignorar.
6. Texto ilegível → registrar o que se vê e `confianca: "baixa"`; se o quadro vizinho for mais nítido, usar o vizinho.

## Saída: `trabalho/<id>.acoes.json`
```json
[{"t":125,"programa":"nome do software ou site","tela":"Menu > Submenu > Aba","acao":"clicar|digitar|selecionar|marcar|desmarcar|arrastar|abrir|executar|colar|rolar|aguardar","alvo":"rótulo exato como aparece","valor":"texto/comando/código digitado ou opção escolhida","resultado":"o que aparece depois","confianca":"alta|media|baixa"}]
```
Regras:
- Uma ação por objeto; sequência de cliques em menu = uma ação com `tela` = caminho completo.
- `alvo` e `tela` com os rótulos exatamente como na tela (idioma da interface).
- Código ou comando: copiar inteiro em `valor`; se cortado no quadro, juntar com quadros vizinhos.
- Não inventar passo que não aparece nem é narrado.
- Atalho de teclado narrado ou exibido: `acao: "atalho"`, `valor: "Ctrl+Shift+P"`.

## Depois
`python scripts/mesclar.py <id>` → `trabalho/<id>.enriquecido.txt`:
```
[2:00] agora a gente vai configurar o acesso
▶ [2:05] em Configurações > Segurança: clicar "Adicionar chave" → abre janela "Nova chave"
▶ [2:11] em Nova chave: digitar "Nome" = `servidor-01`
[2:15] dá um nome qualquer e salva
```

# Riscos e governança

Marina Clara Constatino Ribeiro · RM 568576 · Grupo 75 · Sprint 1

## Privacidade e LGPD

- O texto analisado é guardado, porque o portal precisa mostrá-lo e exportá-lo. O acesso é só pelo portal, com login e perfis.
- Dados pessoais (CPF, e-mail, telefone, cartão) são mascarados quando possível, principalmente antes de exportar.
- O texto também é enviado ao LLM avaliador do portal, que pode ser um serviço externo. Na demonstração usamos só dados de teste.
- Imagem, PDF e áudio originais não são guardados. Só o texto extraído e os metadados. A voz é dado pessoal.
- Dá para localizar e apagar um evento pelo `trace_id`.

## Licenças

- Cada dataset, modelo e biblioteca tem a licença registrada em `data/FONTES.md`.
- Licença desconhecida ou incompatível: não usamos.
- Dataset traduzido mantém o crédito da fonte original.
- Exemplo sintético é marcado como sintético e revisado por pessoas. Exemplos de red teaming ficam fora do teste.
- Os componentes da API são open source.

## Uso indevido do detector

- Quem quiser testar variações de ataque até passar: rate limit por chave (erro 429) e resposta enxuta, sem mostrar a regra exata.
- Falso senso de segurança: o detector reduz o risco, mas não elimina. Ações críticas precisam de outras camadas.
- Falso positivo: hard negatives no treino, faixa REVIEW e taxa de falso positivo medida em conjunto separado.
- O próprio texto atacar o detector ou o LLM avaliador: o texto é sempre tratado como dado e o LLM responde em formato estruturado.

## Limitações do modelo

- O modelo de partida é mais forte em inglês, então pode errar mais em português, gírias e mistura de idiomas.
- O desempenho pode cair com o tempo se aparecerem ataques novos (deriva). O painel acompanha o score.
- Textos longos pioram o resultado, por isso são divididos em trechos.
- Erros de OCR e de transcrição atrapalham o motor. Vamos medir separadamente.
- O rótulo do LLM pode errar. Vamos conferir uma amostra dos casos em que modelo e LLM concordam.

## Retenção (proposta)

| Dado | Tempo |
|---|---|
| Texto, decisão, score e rótulos | 90 dias na base ativa |
| Arquivos originais de imagem, PDF e áudio | não são guardados |
| Trilha de auditoria (sem o texto) | enquanto o projeto existir |
| Métricas agregadas | sem prazo |
| Logs técnicos da API | 30 dias |

## Auditoria

Cada evento guarda: `trace_id`, data e hora, origem, decisão, score, versão do modelo, latência, avaliação do LLM, rótulo final, origem do rótulo (modelo + LLM ou humano) e quem revisou.

## Indicadores do portal

Acertos, precision, recall, F1, matriz de confusão, quantos REVIEW eram ataque de verdade, concordância entre modelo e LLM, fila de revisão, desempenho por origem e idioma, deriva do score e latência (média, P50 e P95).

## Versões do modelo

Cada versão guarda: nome (v0, v0.1...), data, tipo (regras, TF-IDF, DeBERTa, DeBERTa com LoRA), dataset, limites e métricas no teste. Cada análise guarda a versão que decidiu, e o portal compara as versões lado a lado.

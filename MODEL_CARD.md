# Model Card: PromptShield 2.0 (TF-IDF + Regressão Logística)

## Uso pretendido
Triagem de textos (mensagens, e-mails, trechos de documentos, conteúdo recuperado por RAG) antes de chegarem a um agente de IA, em **português e inglês**. A saída é `ALLOW`, `REVIEW` ou `BLOCK`, pensada para **acionar revisão ou bloqueio**, não como única barreira.

## Fora de escopo
Proteção completa contra prompt injection; idiomas além de PT e EN; imagens e áudio; ataques que dependem de contexto de várias mensagens; uso como prova de que um conteúdo é seguro.

## Modelo
`TfidfVectorizer` (palavras + bigramas, `sublinear_tf`, `min_df=2`, com normalização de acentos, caracteres invisíveis e Base64) seguido de `LogisticRegression` (`class_weight="balanced"`). Limiares escolhidos na validação: revisar ≥ 0,540 e bloquear ≥ 0,669 (valores em `artifacts/metrics.json`).

## Dados
- 2.854 exemplos **sintéticos**, gerados por 64 modelos de frase (PT e EN), **sem revisão humana**.
- Divisão por modelo de frase, sem texto repetido entre treino, validação e teste (verificado por teste automatizado).
- Conjunto externo: 46 frases escritas à mão pelo grupo original (Marina Clara Constatino Ribeiro e Yasmin Leite, FIAP, Grupo 75), nunca usadas no treino.
- Famílias de ataque: ignorar instruções, extrair prompt, vazar dados, jailbreak por papel. Contêm também *hard negatives* (correções legítimas, aulas de segurança, pedidos sensíveis legítimos).

## Resultados (reais, `artifacts/metrics.json`)
| Conjunto | n | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|
| Validação | 490 | 0,992 | 1,000 | 0,996 | 1,000 |
| Teste (moldes novos) | 402 | 0,906 | 1,000 | 0,951 | 0,974 |
| Externo (46 à mão) | 46 | 0,875 | 0,955 | 0,913 | 0,974 |

## Limitações e vieses conhecidos
1. **Dados sintéticos:** os números medem generalização para moldes de frase novos, não ataques reais e criativos. Recall 1,00 no teste não deve ser esperado em produção.
2. **Citar × executar:** todos os 26 falsos positivos do teste vêm de pedidos para explicar ou revisar a gramática de uma frase de ataque entre aspas. O modelo não distingue citar de executar.
3. **Conjunto externo otimista:** moldes de hard negative foram escritos depois de ler essas 46 frases.
4. **Validação saturada** (AUC 1,000): não discrimina bem entre modelos. A logística foi escolhida por desempate (mais simples), e não por superioridade medida frente ao Linear SVM.
5. **Não cobre** paráfrase semântica, homóglifos, outros idiomas e ataques multi-turno.
6. **Tamanho do externo (46)** gera incerteza grande: um único erro muda o F1 em alguns pontos.

## Considerações éticas
Falsos positivos bloqueiam usuários legítimos; por isso existe o estado `REVIEW`. O log registra um hash do texto e não o texto, para não armazenar dados pessoais.

## Comparação com Transformer
**Não realizada.** O código está em `promptshield/transformer_experiment.py`, mas não foi executado (sem GPU e sem acesso ao Hugging Face no ambiente de desenvolvimento).

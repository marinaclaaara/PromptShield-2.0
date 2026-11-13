# Planejamento das próximas etapas

Marina Clara Constatino Ribeiro · RM 568576 · Grupo 75 · Sprint 1

O documento da Intelliway propõe 4 Sprints (CS 1 a CS 4). A divisão é uma sugestão e depende da validação da coordenação.

| Sprint | Foco | Entregas |
|---|---|---|
| CS 1 | Fundações | Problema, ameaça, User Stories, plano do dataset, arquitetura, contrato da API, wireframes, riscos |
| CS 2 | Motor e API v1 | Dataset e baselines medidos, DeBERTa com LoRA, limites pela curva ROC, API v1, OCR |
| CS 3 | Portal e serviço | Login, painel, histórico, revisão humana, avaliador LLM, robô consumidor, áudio |
| CS 4 | Produção | Perfis de acesso, deploy, deriva e retreino, relatório do modelo, demonstração final |

## O que cada disciplina entrega

| Disciplina | CS 1 | CS 2 | CS 3 | CS 4 |
|---|---|---|---|---|
| Processamento de linguagem natural | Pré-processamento e baselines | DeBERTa com LoRA, ROC e limites | Textos longos, ASR, prompt do avaliador | Validação final e relatório do modelo |
| IA generativa | Arquitetura de IA, dados sintéticos, desenho do RAG | Sintéticos revisados, RAG simulado | Avaliador LLM v1 | Avaliar o avaliador, red teaming |
| RPA | JSON de entrada e robô simples | Corpus WEB e base de eventos | Robô ponta a ponta | Monitoramento e demonstração |
| Front end | Wireframes | Front simples ligado à API | Portal MVP | Perfis, ajustes e deploy |
| Visão computacional | Teste de OCR | OCR no motor com imagens de ataque | Baixo contraste e avaliação separada | Análise de erros |
| Governança | Riscos | Versionamento e documentação | KPIs e rotulagem | LGPD, deriva e retreino |

## Kanban (Trello)

Colunas: Backlog, A fazer, Em andamento, Em revisão e Concluído.

Cartões iniciais:
1. Coletar dataset público e conferir licença
2. Traduzir e revisar uma amostra
3. Escrever exemplos próprios
4. Gerar sintéticos e revisar
5. Montar hard negatives
6. Pré-processamento PT-BR
7. Baseline de regras
8. Baseline TF-IDF
9. API mínima com autenticação
10. Pipeline de OCR
11. Fine-tuning DeBERTa com LoRA
12. Portal: login e painel
13. Portal: histórico, revisão e exportação
14. Avaliador LLM
15. Robô consumidor
16. Docker Compose, testes e documentação
17. Vídeo

Link do quadro: https://trello.com/b/4Bju7bmD/promptshield-br

## Responsabilidades

| Área | Responsável |
|---|---|
| Dados e dataset | Marina |
| Motor (baselines e modelo) | Marina |
| API, OCR e áudio | Marina |
| Portal e avaliador LLM | Marina |
| Robô consumidor | Marina |
| Documentação e vídeo | Marina |

## Para a entrega final

- Docker Compose que sobe API, motor e portal
- Testes automatizados da API e do motor
- Script ou notebook que reproduz a avaliação
- Relatório do modelo com limitações
- Demonstração ponta a ponta com o robô consumidor

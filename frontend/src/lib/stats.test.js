import assert from "node:assert/strict";
import test from "node:test";
import { contarDecisoes, formatarPercentual, histogramaRisco, resumir } from "./stats.js";

const h = [
  { decision: "ALLOW", risk_score: 0.05 },
  { decision: "REVIEW", risk_score: 0.6 },
  { decision: "BLOCK", risk_score: 1.0 },
  { decision: "BLOCK", risk_score: 0.8 },
];

test("conta decisões", () => assert.deepEqual(contarDecisoes(h), { ALLOW: 1, REVIEW: 1, BLOCK: 2 }));

test("histograma: score 1.0 cai na última faixa e a soma bate com o total", () => {
  const bins = histogramaRisco(h);
  assert.equal(bins.length, 10);
  assert.equal(bins[9], 1);
  assert.equal(bins.reduce((a, b) => a + b, 0), h.length);
});

test("resumo calcula média e taxa de suspeitos", () => {
  const r = resumir(h);
  assert.equal(r.total, 4);
  assert.ok(Math.abs(r.mediaRisco - 0.6125) < 1e-9);
  assert.equal(r.taxaSuspeitos, 0.75);
});

test("resumo de histórico vazio não divide por zero", () => {
  assert.deepEqual(resumir([]), { total: 0, contagem: { ALLOW: 0, REVIEW: 0, BLOCK: 0 }, mediaRisco: 0, taxaSuspeitos: 0 });
});

test("formata percentual com vírgula", () => assert.equal(formatarPercentual(0.1234), "12,3%"));

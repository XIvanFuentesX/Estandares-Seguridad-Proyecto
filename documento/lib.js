// Utilidades de formato para el documento final (formato obligatorio del curso: carta, Arial 12,
// interlineado 1.0, sangría de primera línea, márgenes 3.5/2.5/3/3 cm, numeración arriba a la derecha).
const fs = require("fs");
const path = require("path");
const {
  Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType, AlignmentType,
  ImageRun, BorderStyle, HeadingLevel, VerticalAlign,
} = require("docx");

const ROOT = path.resolve(__dirname, "..");
const CM = 567; // DXA por centímetro
const PAGE = { width: 12240, height: 15840 };
const MARGIN = { top: 3 * CM, bottom: 3 * CM, left: Math.round(3.5 * CM), right: Math.round(2.5 * CM) };
const CONTENT_W = PAGE.width - MARGIN.left - MARGIN.right; // retrato
const CONTENT_W_LAND = PAGE.height - MARGIN.left - MARGIN.right; // horizontal
const INDENT = 720; // ~5 espacios (1.27 cm)
const FONT = "Arial";

// ---------- CSV ----------
function readCsv(rel) {
  const text = fs.readFileSync(path.join(ROOT, rel), "utf8").replace(/^﻿/, "");
  const rows = [];
  let row = [], field = "", q = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) {
      if (c === '"' && text[i + 1] === '"') { field += '"'; i++; }
      else if (c === '"') q = false;
      else field += c;
    } else if (c === '"') q = true;
    else if (c === ",") { row.push(field); field = ""; }
    else if (c === "\n" || c === "\r") {
      if (c === "\r" && text[i + 1] === "\n") i++;
      row.push(field); field = "";
      if (row.some((v) => v !== "")) rows.push(row);
      row = [];
    } else field += c;
  }
  if (field !== "" || row.length) { row.push(field); rows.push(row); }
  const [head, ...body] = rows;
  return body.map((r) => Object.fromEntries(head.map((h, i) => [h, (r[i] || "").trim()])));
}

// ---------- Texto ----------
// Marcado ligero dentro de cadenas: **negrita**, *cursiva*, [[pendiente]] (resaltado amarillo).
function runs(text, base = {}) {
  const out = [];
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*|\[\[[^\]]+\]\]|`[^`]+`)/g;
  let last = 0, m;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), font: FONT, ...base }));
    const t = m[0];
    if (t.startsWith("**")) out.push(new TextRun({ text: t.slice(2, -2), bold: true, font: FONT, ...base }));
    else if (t.startsWith("`")) out.push(new TextRun({ text: t.slice(1, -1), font: FONT, ...base }));
    else if (t.startsWith("[[")) out.push(new TextRun({ text: t.slice(2, -2), highlight: "yellow", font: FONT, ...base }));
    else out.push(new TextRun({ text: t.slice(1, -1), italics: true, font: FONT, ...base }));
    last = m.index + t.length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), font: FONT, ...base }));
  return out;
}

const p = (text, opts = {}) => new Paragraph({
  children: runs(text),
  alignment: opts.align || AlignmentType.JUSTIFIED,
  indent: opts.noIndent ? undefined : { firstLine: INDENT },
  spacing: { line: 240, after: 120 },
  keepNext: opts.keepNext,
});

const bullet = (text, level = 0) => new Paragraph({
  children: runs(text),
  numbering: { reference: "vinetas", level },
  alignment: AlignmentType.JUSTIFIED,
  spacing: { line: 240, after: 60 },
});

const numbered = (text, ref = "numeros") => new Paragraph({
  children: runs(text),
  numbering: { reference: ref, level: 0 },
  alignment: AlignmentType.JUSTIFIED,
  spacing: { line: 240, after: 60 },
});

const h1 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text, font: FONT })] });
const h2 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun({ text, font: FONT })] });
const h3 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun({ text, font: FONT })] });

// ---------- Tablas y figuras (APA 7: número en negrita, título en cursiva, nota debajo) ----------
let tableNo = 0, figureNo = 0;

function captionLines(kind, n, title) {
  return [
    new Paragraph({ children: [new TextRun({ text: `${kind} ${n}`, bold: true, font: FONT })], spacing: { before: 120, after: 0, line: 240 }, keepNext: true }),
    new Paragraph({ children: [new TextRun({ text: title, italics: true, font: FONT })], spacing: { after: 60, line: 240 }, keepNext: true }),
  ];
}

function note(text) {
  return new Paragraph({
    children: [new TextRun({ text: "Nota. ", italics: true, font: FONT, size: 20 }), ...runs(text, { size: 20 })],
    spacing: { before: 60, after: 200, line: 240 },
    alignment: AlignmentType.JUSTIFIED,
  });
}

const BORDER = { style: BorderStyle.SINGLE, size: 4, color: "8C8C8C" };
const BORDERS = { top: BORDER, bottom: BORDER, left: BORDER, right: BORDER };

function cell(text, width, opts = {}) {
  const lines = String(text ?? "").split("\n");
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    borders: BORDERS,
    verticalAlign: VerticalAlign.CENTER,
    shading: opts.fill ? { fill: opts.fill, type: ShadingType.CLEAR, color: "auto" } : undefined,
    margins: { top: 30, bottom: 30, left: 70, right: 70 },
    children: lines.map((line) => new Paragraph({
      children: runs(line, { size: opts.size || 18, bold: opts.bold, color: opts.color }),
      alignment: opts.align || AlignmentType.LEFT,
      spacing: { line: 240, before: 0, after: 0 },
    })),
  });
}

// widths: proporciones relativas; se escalan al ancho útil.
function table(title, headers, rows, widths, opts = {}) {
  tableNo += 1;
  const total = opts.landscape ? CONTENT_W_LAND : CONTENT_W;
  const sum = widths.reduce((a, b) => a + b, 0);
  const cols = widths.map((w) => Math.floor((w / sum) * total));
  cols[cols.length - 1] += total - cols.reduce((a, b) => a + b, 0);
  const size = opts.size || 18;
  const head = new TableRow({
    tableHeader: true,
    cantSplit: true,
    children: headers.map((h, i) => cell(h, cols[i], { fill: "D9E2F3", bold: true, size })),
  });
  const body = rows.map((r) => new TableRow({
    cantSplit: true,
    children: r.map((v, i) => {
      const fill = opts.fillFn ? opts.fillFn(v, i, r) : undefined;
      return cell(v, cols[i], { size, fill, align: opts.center && opts.center.includes(i) ? AlignmentType.CENTER : undefined });
    }),
  }));
  const out = [...captionLines("Tabla", tableNo, title),
    new Table({ width: { size: total, type: WidthType.DXA }, columnWidths: cols, rows: [head, ...body] })];
  out.push(opts.note ? note(opts.note) : new Paragraph({ children: [], spacing: { after: 120 } }));
  return out;
}

function pngSize(file) {
  const b = fs.readFileSync(file);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
}

function figure(title, rel, noteText, opts = {}) {
  figureNo += 1;
  const file = path.join(ROOT, rel);
  const { w, h } = pngSize(file);
  const maxW = ((opts.landscape ? CONTENT_W_LAND : CONTENT_W) / 1440) * 96; // pulgadas → px a 96 ppp
  const width = Math.round(maxW);
  const height = Math.round((width * h) / w);
  return [
    ...captionLines("Figura", figureNo, title),
    new Paragraph({
      children: [new ImageRun({ type: "png", data: fs.readFileSync(file), transformation: { width, height },
        altText: { title, description: title, name: path.basename(rel) } })],
      alignment: AlignmentType.CENTER, keepNext: true, spacing: { after: 0 },
    }),
    note(noteText),
  ];
}

// Marcador visible para capturas reales que el equipo debe insertar (no se fabrican imágenes).
function capturePlaceholder(title, what) {
  figureNo += 1;
  return [
    ...captionLines("Figura", figureNo, title),
    new Table({
      width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: [CONTENT_W],
      rows: [new TableRow({ children: [new TableCell({
        width: { size: CONTENT_W, type: WidthType.DXA },
        borders: { top: { style: BorderStyle.DASHED, size: 8, color: "B8860B" }, bottom: { style: BorderStyle.DASHED, size: 8, color: "B8860B" },
          left: { style: BorderStyle.DASHED, size: 8, color: "B8860B" }, right: { style: BorderStyle.DASHED, size: 8, color: "B8860B" } },
        shading: { fill: "FFF8DC", type: ShadingType.CLEAR, color: "auto" },
        margins: { top: 300, bottom: 300, left: 200, right: 200 },
        children: [new Paragraph({ alignment: AlignmentType.CENTER, children: runs(`[[INSERTAR CAPTURA REAL]] ${what}`, { size: 20 }) })],
      })] })],
    }),
    note("Captura pendiente de tomar por el equipo sobre el ambiente en ejecución; no debe sustituirse por imágenes de terceros ni editadas."),
  ];
}

module.exports = {
  ROOT, PAGE, MARGIN, CONTENT_W, CONTENT_W_LAND, INDENT, FONT, CM,
  nextTable: () => tableNo + 1,
  readCsv, runs, p, bullet, numbered, h1, h2, h3, table, figure, capturePlaceholder, note, cell,
};

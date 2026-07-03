const fs = await import("node:fs/promises");
const path = await import("node:path");
const { Presentation, PresentationFile } = await import("@oai/artifact-tool");

const W = 1280;
const H = 720;
const OUT = path.resolve("docs/clinical_trial_agent_presentation.pptx");
const SCRATCH = path.resolve("tmp/slides/clinical-trial-agent");
const PREVIEW = path.join(SCRATCH, "preview");
const INSPECT = path.join(SCRATCH, "inspect.json");

const C = {
  bg: "#F7F9FC",
  paper: "#FFFFFF",
  navy: "#102A43",
  blue: "#2F6FED",
  blueSoft: "#E9F0FF",
  teal: "#18A999",
  tealSoft: "#E7F8F4",
  amber: "#F4A340",
  amberSoft: "#FFF3E2",
  slate: "#52667A",
  line: "#D7E1EC",
  pale: "#EEF3F8",
  white: "#FFFFFF",
};

const FONT_TITLE = "Aptos Display";
const FONT_BODY = "Aptos";
const inspect = [];

function shape(slide, geometry, x, y, w, h, fill, line = C.line, lineWidth = 1, radius = null) {
  const config = {
    geometry,
    position: { left: x, top: y, width: w, height: h },
    fill,
    line: { style: "solid", fill: line, width: lineWidth },
  };
  if (radius && geometry === "roundRect") {
    config.adjustmentList = [{ name: "adj", formula: `val ${radius}` }];
  }
  return slide.shapes.add(config);
}

function text(
  slide,
  slideNo,
  value,
  x,
  y,
  w,
  h,
  {
    size = 24,
    color = C.navy,
    bold = false,
    face = FONT_BODY,
    align = "left",
    valign = "top",
    fill = "#00000000",
    line = "#00000000",
    role = "text",
  } = {},
) {
  const box = shape(slide, "rect", x, y, w, h, fill, line, 0);
  box.text = value;
  box.text.fontSize = size;
  box.text.color = color;
  box.text.bold = bold;
  box.text.typeface = face;
  box.text.alignment = align;
  box.text.verticalAlignment = valign;
  box.text.insets = { left: 0, right: 0, top: 0, bottom: 0 };
  box.text.autoFit = "shrinkText";
  inspect.push({
    kind: "textbox",
    slide: slideNo,
    role,
    text: String(value),
    textChars: String(value).length,
    textLines: String(value).split("\n").length,
    bbox: [x, y, w, h],
  });
  return box;
}

function pill(slide, slideNo, label, x, y, w, fill, color, role = "pill") {
  shape(slide, "roundRect", x, y, w, 34, fill, fill, 0, 50000);
  text(slide, slideNo, label, x, y + 1, w, 31, {
    size: 14,
    color,
    bold: true,
    align: "center",
    valign: "middle",
    role,
  });
}

function header(slide, slideNo, section, number) {
  text(slide, slideNo, "AGENTIC AI CAPSTONE", 58, 28, 270, 25, {
    size: 13,
    color: C.blue,
    bold: true,
    role: "capstone label",
  });
  text(slide, slideNo, section.toUpperCase(), 900, 28, 250, 25, {
    size: 13,
    color: C.slate,
    bold: true,
    align: "right",
    role: "section label",
  });
  pill(slide, slideNo, `0${number}`, 1168, 20, 54, C.blue, C.white, "slide number");
  shape(slide, "rect", 58, 63, 1164, 2, C.line, C.line, 0);
}

function title(slide, slideNo, value, subtitle = "") {
  text(slide, slideNo, value, 58, 86, 1110, 62, {
    size: 40,
    color: C.navy,
    bold: true,
    face: FONT_TITLE,
    role: "title",
  });
  if (subtitle) {
    text(slide, slideNo, subtitle, 60, 151, 1090, 44, {
      size: 19,
      color: C.slate,
      role: "subtitle",
    });
  }
}

function bulletCard(slide, slideNo, x, y, w, h, number, heading, body, accent, soft) {
  shape(slide, "roundRect", x, y, w, h, C.paper, C.line, 1, 12000);
  shape(slide, "roundRect", x + 18, y + 18, 42, 42, soft, soft, 0, 50000);
  text(slide, slideNo, String(number), x + 18, y + 18, 42, 40, {
    size: 18,
    color: accent,
    bold: true,
    align: "center",
    valign: "middle",
    role: "capability number",
  });
  text(slide, slideNo, heading, x + 76, y + 17, w - 94, 30, {
    size: 18,
    color: C.navy,
    bold: true,
    role: "capability heading",
  });
  text(slide, slideNo, body, x + 76, y + 51, w - 96, h - 64, {
    size: 15,
    color: C.slate,
    role: "capability body",
  });
}

function footer(slide, slideNo, value) {
  shape(slide, "rect", 58, 682, 1164, 2, C.line, C.line, 0);
  text(slide, slideNo, value, 58, 690, 820, 20, {
    size: 11,
    color: C.slate,
    role: "footer",
  });
}

function slide1(presentation) {
  const s = presentation.slides.add();
  s.background.fill = C.bg;
  header(s, 1, "Problem & Solution", 1);
  title(
    s,
    1,
    "Clinical Trial Protocol & Risk Assistant Agent",
    "From complex study documents to sourced operational decisions.",
  );

  shape(s, "roundRect", 58, 218, 560, 126, C.blueSoft, C.blueSoft, 0, 10000);
  pill(s, 1, "PROBLEM", 80, 237, 102, C.blue, C.white, "problem label");
  text(
    s,
    1,
    "Clinical trial teams must quickly understand protocol requirements, detect operational risks, and turn findings into action.",
    80,
    280,
    510,
    48,
    { size: 19, color: C.navy, role: "problem statement" },
  );

  shape(s, "roundRect", 642, 218, 580, 126, C.tealSoft, C.tealSoft, 0, 10000);
  pill(s, 1, "SOLUTION", 664, 237, 112, C.teal, C.white, "solution label");
  text(
    s,
    1,
    "An agentic assistant combining RAG, tools, memory, MCP, and planning for reliable clinical operations support.",
    664,
    280,
    530,
    48,
    { size: 19, color: C.navy, role: "solution statement" },
  );

  bulletCard(s, 1, 58, 374, 274, 256, 1, "Grounded answers", "Retrieves protocol, SOP, and visit evidence with source labels.", C.blue, C.blueSoft);
  bulletCard(s, 1, 350, 374, 274, 256, 2, "Risk to action", "Explains operational impact and generates owned CRA next steps.", C.teal, C.tealSoft);
  bulletCard(s, 1, 642, 374, 274, 256, 3, "Useful memory", "Stores role, answer style, output format, and study focus in SQLite.", C.amber, C.amberSoft);
  bulletCard(s, 1, 934, 374, 288, 256, 4, "Standard tools", "Exposes the shared tool layer through FastMCP for external agents.", C.blue, C.blueSoft);
  footer(s, 1, "Synthetic study documents • Deterministic mock mode • No medical decisions");

  s.speakerNotes.setText(
    "Open by describing the document-to-action problem in clinical operations. Explain that this is not a generic chatbot: it retrieves evidence, invokes typed tools, remembers user preferences, and produces practical actions. Point out the four capability cards. State that the data is synthetic and that the assistant does not replace investigator or Medical Monitor judgment.",
  );
}

function architectureNode(slide, slideNo, x, y, w, h, step, label, detail, accent, soft) {
  shape(slide, "roundRect", x, y, w, h, C.paper, C.line, 1, 10000);
  shape(slide, "roundRect", x + 14, y + 14, 38, 38, soft, soft, 0, 50000);
  text(slide, slideNo, step, x + 14, y + 14, 38, 36, {
    size: 15,
    color: accent,
    bold: true,
    align: "center",
    valign: "middle",
    role: "architecture step",
  });
  text(slide, slideNo, label, x + 62, y + 13, w - 76, 30, {
    size: 17,
    color: C.navy,
    bold: true,
    role: "architecture node",
  });
  text(slide, slideNo, detail, x + 18, y + 61, w - 36, h - 72, {
    size: 14,
    color: C.slate,
    align: "center",
    role: "architecture detail",
  });
}

function arrow(slide, slideNo, symbol, x, y, w = 34, h = 34) {
  text(slide, slideNo, symbol, x, y, w, h, {
    size: 28,
    color: C.blue,
    bold: true,
    align: "center",
    valign: "middle",
    role: "flow arrow",
  });
}

function slide2(presentation) {
  const s = presentation.slides.add();
  s.background.fill = C.bg;
  header(s, 2, "System Architecture", 2);
  title(s, 2, "One workflow, shared tools, inspectable output", "The planner selects the minimum tool sequence and preserves sources.");

  const topY = 218;
  const botY = 404;
  const w = 250;
  const h = 132;
  const xs = [58, 350, 642, 934];
  architectureNode(s, 2, xs[0], topY, w, h, "1", "User", "Protocol question or operational request", C.blue, C.blueSoft);
  architectureNode(s, 2, xs[1], topY, w, h, "2", "FastAPI API", "Typed endpoints and validation", C.blue, C.blueSoft);
  architectureNode(s, 2, xs[2], topY, w, h, "3", "Agent Planner", "Classifies intent and decides workflow", C.teal, C.tealSoft);
  architectureNode(s, 2, xs[3], topY, w, h, "4", "Memory SQLite", "Stores user role and preferences", C.amber, C.amberSoft);
  arrow(s, 2, "→", 310, 267);
  arrow(s, 2, "→", 602, 267);
  arrow(s, 2, "→", 894, 267);
  arrow(s, 2, "↓", 1042, 357);

  architectureNode(s, 2, xs[3], botY, w, h, "5", "RAG Vector Store", "Retrieves source-labelled study knowledge", C.blue, C.blueSoft);
  architectureNode(s, 2, xs[2], botY, w, h, "6", "Tool Layer", "Search • summary • risk • action plan", C.teal, C.tealSoft);
  architectureNode(s, 2, xs[1], botY, w, h, "7", "MCP Server", "Standardized external tool interface", C.amber, C.amberSoft);
  architectureNode(s, 2, xs[0], botY, w, h, "8", "Final Answer", "Plan • tools • sources • memory", C.blue, C.blueSoft);
  arrow(s, 2, "←", 894, 453);
  arrow(s, 2, "←", 602, 453);
  arrow(s, 2, "←", 310, 453);

  shape(s, "roundRect", 58, 574, 1164, 70, C.navy, C.navy, 0, 9000);
  pill(s, 2, "DOCKER", 78, 592, 94, C.blue, C.white, "docker label");
  text(s, 2, "Packages the FastAPI service, tools, data, memory, and vector index into one reproducible runtime.", 195, 589, 990, 36, {
    size: 18,
    color: C.white,
    valign: "middle",
    role: "docker foundation",
  });
  footer(s, 2, "FastAPI calls shared tools directly; FastMCP exposes the same capabilities externally.");

  s.speakerNotes.setText(
    "Walk through the numbered flow. FastAPI validates the request. The planner chooses a workflow. SQLite supplies user preferences, while RAG supplies study facts. The tool layer performs search, summary, risk detection, and action planning. FastAPI calls these functions directly for demo reliability, and FastMCP exposes the same functions through a standard interface. The final answer reports plan, tools, sources, and memory. Docker packages the complete runtime.",
  );
}

function demoStep(slide, slideNo, x, y, number, label, accent, soft) {
  shape(slide, "roundRect", x, y, 520, 54, C.paper, C.line, 1, 9000);
  shape(slide, "ellipse", x + 12, y + 9, 36, 36, soft, soft, 0);
  text(slide, slideNo, String(number), x + 12, y + 9, 36, 34, {
    size: 15,
    color: accent,
    bold: true,
    align: "center",
    valign: "middle",
    role: "demo step number",
  });
  text(slide, slideNo, label, x + 62, y + 10, 430, 33, {
    size: 17,
    color: C.navy,
    bold: true,
    valign: "middle",
    role: "demo step",
  });
}

function conceptChip(slide, slideNo, x, y, w, label, accent, soft) {
  shape(slide, "roundRect", x, y, w, 58, soft, soft, 0, 12000);
  shape(slide, "ellipse", x + 16, y + 18, 22, 22, accent, accent, 0);
  text(slide, slideNo, "✓", x + 16, y + 16, 22, 24, {
    size: 14,
    color: C.white,
    bold: true,
    align: "center",
    valign: "middle",
    role: "concept check",
  });
  text(slide, slideNo, label, x + 50, y + 13, w - 62, 34, {
    size: 16,
    color: C.navy,
    bold: true,
    valign: "middle",
    role: "course concept",
  });
}

function slide3(presentation) {
  const s = presentation.slides.add();
  s.background.fill = C.bg;
  header(s, 3, "Demo & Course Mapping", 3);
  title(s, 3, "Evidence becomes accountable action", "A six-step demo proves all seven required course concepts.");

  pill(s, 3, "LIVE DEMO", 58, 211, 122, C.blue, C.white, "demo column label");
  pill(s, 3, "COURSE CONCEPTS", 678, 211, 166, C.teal, C.white, "concept column label");

  const steps = [
    "Ingest study documents",
    "Ask the Visit 2 question",
    "Summarize safety monitoring",
    "Detect operational risks",
    "Generate the CRA action plan",
    "Save and reuse memory",
  ];
  for (let i = 0; i < steps.length; i += 1) {
    demoStep(s, 3, 58, 257 + i * 62, i + 1, steps[i], i % 2 === 0 ? C.blue : C.teal, i % 2 === 0 ? C.blueSoft : C.tealSoft);
  }

  const concepts = [
    ["Persona design", C.blue, C.blueSoft],
    ["Tool use", C.teal, C.tealSoft],
    ["MCP", C.amber, C.amberSoft],
    ["Reasoning / planning", C.blue, C.blueSoft],
    ["RAG knowledge", C.teal, C.tealSoft],
    ["Memory", C.amber, C.amberSoft],
    ["Docker deployment", C.blue, C.blueSoft],
  ];
  for (let i = 0; i < concepts.length; i += 1) {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = 678 + col * 272;
    const y = 257 + row * 76;
    conceptChip(s, 3, x, y, 252, concepts[i][0], concepts[i][1], concepts[i][2]);
  }

  shape(s, "roundRect", 678, 575, 524, 54, C.navy, C.navy, 0, 9000);
  text(s, 3, "Mock mode keeps the complete demo reliable without an API key.", 698, 585, 484, 31, {
    size: 16,
    color: C.white,
    bold: true,
    align: "center",
    valign: "middle",
    role: "mock mode callout",
  });
  footer(s, 3, "Educational prototype • Synthetic data • Human verification required");

  s.speakerNotes.setText(
    "Use the left side as the exact demo order: ingest, protocol Q&A, safety summary, risk analysis, CRA plan, and memory reuse. Then map the implementation to the seven course concepts on the right. Explain that persona rules shape behavior; typed tools perform actions; MCP standardizes exposure; the planner sequences tools; RAG stores document knowledge; SQLite stores preferences; and Docker makes the runtime reproducible. Close with the mock-mode reliability statement and the clinical/GxP boundary.",
  );
}

async function saveBlob(blob, filePath) {
  const bytes = new Uint8Array(await blob.arrayBuffer());
  await fs.writeFile(filePath, bytes);
}

async function main() {
  await fs.mkdir(PREVIEW, { recursive: true });
  const p = Presentation.create({ slideSize: { width: W, height: H } });
  p.theme.colorScheme = {
    name: "Clinical Trial Agent",
    themeColors: {
      dk1: C.navy,
      lt1: C.white,
      dk2: C.slate,
      lt2: C.bg,
      accent1: C.blue,
      accent2: C.teal,
      accent3: C.amber,
      accent4: "#6C63FF",
      accent5: "#5D7A96",
      accent6: "#8CB4D8",
      hlink: C.blue,
      folHlink: "#6C63FF",
    },
  };
  slide1(p);
  slide2(p);
  slide3(p);

  for (let i = 0; i < p.slides.count; i += 1) {
    const preview = await p.export({ slide: p.slides.getItem(i), format: "png", scale: 1 });
    await saveBlob(preview, path.join(PREVIEW, `slide-${String(i + 1).padStart(2, "0")}.png`));
  }
  await fs.writeFile(INSPECT, JSON.stringify({ slideCount: p.slides.count, records: inspect }, null, 2));
  const pptx = await PresentationFile.exportPptx(p);
  await pptx.save(OUT);
  console.log(OUT);
}

await main();

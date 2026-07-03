const fs = await import("node:fs/promises");
const { FileBlob, PresentationFile } = await import("@oai/artifact-tool");

const deckPath = "docs/clinical_trial_agent_presentation.pptx";
const deck = await PresentationFile.importPptx(await FileBlob.load(deckPath));
const inspect = JSON.parse(
  await fs.readFile("tmp/slides/clinical-trial-agent/inspect.json", "utf8"),
);

if (deck.slides.count !== 3) {
  throw new Error(`Expected 3 slides, found ${deck.slides.count}`);
}
if (inspect.slideCount !== 3) {
  throw new Error(`Inspect record expected 3 slides, found ${inspect.slideCount}`);
}
const editableText = inspect.records.filter((record) => record.kind === "textbox");
if (editableText.length < 30) {
  throw new Error(`Expected substantial editable text, found ${editableText.length} records`);
}
for (const slideNo of [1, 2, 3]) {
  if (!editableText.some((record) => record.slide === slideNo && record.role === "title")) {
    throw new Error(`Missing editable title on slide ${slideNo}`);
  }
}
console.log(
  JSON.stringify({
    importedSlides: deck.slides.count,
    editableTextRecords: editableText.length,
  }),
);

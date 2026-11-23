/**
 * Table-driven eligibility tests for Search Your Uni.
 * Run from the UniFit folder:
 *   node maintenance/test_admission_rules.mjs
 */
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import vm from "node:vm";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, "..");
const require = createRequire(import.meta.url);
const { checkUniversity } = require(path.join(root, "assets", "js", "admission-rules.js"));

function loadAdmissions() {
  const source = fs.readFileSync(path.join(root, "data", "admissions.js"), "utf8");
  const context = { window: {} };
  vm.runInNewContext(source, context);
  return context.window.unifitAdmissions;
}

function findOne(admissions, predicate, label) {
  const match = admissions.find(predicate);
  if (!match) throw new Error(`Could not find admissions route: ${label}`);
  return match;
}

function steamMarks(overrides = {}) {
  const marks = {
    myan: 80, eng: 80, math: 80, phy: 80, chem: 80, bio: 80,
    ...overrides,
  };
  marks.total = ["myan", "eng", "math", "phy", "chem", "bio"]
    .reduce((sum, key) => sum + (Number(marks[key]) || 0), 0);
  return marks;
}

function assertEqual(actual, expected, message) {
  if (actual !== expected) {
    throw new Error(`${message}\n  expected: ${expected}\n  actual:   ${actual}`);
  }
}

const admissions = loadAdmissions();
let passed = 0;

function test(name, fn) {
  fn();
  passed += 1;
  console.log(`ok - ${name}`);
}

const medicine1 = findOne(admissions, (u) => u.name === "University of Medicine 1, Yangon", "Medicine 1");
const ytu = findOne(admissions, (u) => u.name === "Yangon Technological University", "YTU");
const ucsy = findOne(admissions, (u) => u.name === "University of Computer Studies (Yangon)", "UCSY");
const yadanabonMyanmar = findOne(
  admissions,
  (u) => u.group === "Yadanabon University" && u.name === "မြန်မာစာ",
  "Yadanabon Myanmar",
);

test("Medicine 1 accepts STEAMS-1 total 480", () => {
  assertEqual(checkUniversity(medicine1, steamMarks(), "ygn"), true, "should accept");
});

test("Medicine 1 rejects total below 450", () => {
  const marks = steamMarks({ myan: 70, eng: 70, math: 70, phy: 70, chem: 70, bio: 70 });
  assertEqual(marks.total, 420, "fixture total");
  assertEqual(checkUniversity(medicine1, marks, "ygn"), false, "should reject");
});

test("Medicine 1 rejects wrong subject stream (missing bio)", () => {
  const marks = { myan: 90, eng: 90, math: 90, phy: 90, chem: 90, eco: 90, total: 540 };
  assertEqual(checkUniversity(medicine1, marks, "ygn"), false, "should reject arts/eco stream");
});

test("YTU accepts pcm_eng_combo exactly 300", () => {
  const marks = steamMarks({ eng: 75, math: 75, phy: 75, chem: 75 }); // 300 combo, total 460
  assertEqual(checkUniversity(ytu, marks, "ygn"), true, "should accept");
});

test("YTU rejects pcm_eng_combo 299", () => {
  const marks = steamMarks({ eng: 74, math: 75, phy: 75, chem: 75 }); // 299
  assertEqual(checkUniversity(ytu, marks, "ygn"), false, "should reject");
});

test("UCSY accepts via math_eng_combo even when total is low", () => {
  // totalOrMathEnglish: total 450 OR math+eng 140
  const marks = steamMarks({
    myan: 50, eng: 70, math: 70, phy: 50, chem: 50, bio: 50,
  }); // total 340, math+eng 140
  assertEqual(checkUniversity(ucsy, marks, "ygn"), true, "should accept via combo");
});

test("UCSY rejects when both total and math_eng are below thresholds", () => {
  const marks = steamMarks({
    myan: 50, eng: 60, math: 60, phy: 50, chem: 50, bio: 50,
  }); // total 320, math+eng 120
  assertEqual(checkUniversity(ucsy, marks, "ygn"), false, "should reject");
});

test("Yadanabon Myanmar accepts Mandalay center", () => {
  const marks = steamMarks();
  assertEqual(checkUniversity(yadanabonMyanmar, marks, "mdy"), true, "should accept mdy");
});

test("Yadanabon Myanmar rejects Naypyitaw center", () => {
  const marks = steamMarks();
  assertEqual(checkUniversity(yadanabonMyanmar, marks, "npt"), false, "should reject npt");
});

test("exported admissions payload is non-empty", () => {
  assertEqual(admissions.length > 800, true, `expected 800+ routes, got ${admissions.length}`);
});

const nspuCs = findOne(
  admissions,
  (u) => u.group === "Naypyitaw State Polytechnic University" && /Computer/i.test(u.name),
  "NSPU Computer",
);
const polyBanmaw = findOne(
  admissions,
  (u) => u.group === "Polytechnic University (Banmaw)" && u.name === "Engineering",
  "PU Banmaw Engineering",
);
const phyMathRoute = admissions.find((u) => u.subjectSpecific?.phy_math_or_chem_combo !== undefined);
const pcmBioRoute = admissions.find((u) => u.subjectSpecific?.pcm_bio_combo !== undefined);
const confirmStreamRoute = admissions.find((u) => u.confirmExamStream);

test("NSPU computer accepts totalOrMathEnglish via total 450", () => {
  assertEqual(checkUniversity(nspuCs, steamMarks({ myan: 75, eng: 75, math: 75, phy: 75, chem: 75, bio: 75 }), "npt"), true, "should accept");
});

test("PU Banmaw engineering requires pcm_eng_combo 240", () => {
  const ok = steamMarks({ eng: 60, math: 60, phy: 60, chem: 60 }); // 240
  const low = steamMarks({ eng: 59, math: 60, phy: 60, chem: 60 }); // 239
  assertEqual(checkUniversity(polyBanmaw, ok, "kcn"), true, "should accept 240");
  assertEqual(checkUniversity(polyBanmaw, low, "kcn"), false, "should reject 239");
});

if (phyMathRoute) {
  test("phy_math_or_chem_combo accepts physics+math threshold", () => {
    const need = phyMathRoute.subjectSpecific.phy_math_or_chem_combo;
    const marks = steamMarks({ phy: need - 40, math: 40, chem: 0, eng: 80 });
    assertEqual(checkUniversity(phyMathRoute, marks, "ygn"), true, "should accept");
  });
}

if (pcmBioRoute) {
  test("pcm_bio_combo rejects below threshold", () => {
    const need = pcmBioRoute.subjectSpecific.pcm_bio_combo;
    const marks = steamMarks({ phy: 40, chem: 40, math: 40, bio: 40, eng: 80 });
    assertEqual(marks.phy + marks.chem + marks.math + marks.bio < need, true, "fixture below threshold");
    assertEqual(checkUniversity(pcmBioRoute, marks, "ygn"), false, "should reject");
  });
}

if (confirmStreamRoute) {
  test("confirmExamStream routes still match on marks", () => {
    assertEqual(Boolean(confirmStreamRoute.confirmExamStream), true, "flag present");
    assertEqual(checkUniversity(confirmStreamRoute, steamMarks(), "ygn"), true, "should still be searchable");
  });
}

test("detail urls use canonical slug paths", () => {
  const spaced = admissions.filter((u) => /%20| /.test((u.detailUrl || "").split("#")[0]));
  assertEqual(spaced.length, 0, `unexpected spaced urls: ${spaced.slice(0, 3).map((u) => u.detailUrl)}`);
});

console.log(`\n${passed} tests passed`);

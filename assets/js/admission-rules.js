/**
 * Pure admission eligibility rules shared by Search Your Uni and maintenance tests.
 * Browser: attaches to window.checkUniversity
 * Node: module.exports.checkUniversity
 */
(function (root, factory) {
    if (typeof module === "object" && module.exports) {
        module.exports = factory();
    } else {
        root.checkUniversity = factory().checkUniversity;
    }
}(typeof globalThis !== "undefined" ? globalThis : this, function () {
    function checkUniversity(uni, marks, testCenter) {
        const tc = (testCenter || "").toString().toLowerCase();
        const allowed = uni.allowedCenters ?? "all";

        if (allowed !== "all") {
            if (Array.isArray(allowed)) {
                if (!allowed.map(a => a.toString().toLowerCase()).includes(tc)) return false;
            } else if (allowed.toString().toLowerCase() !== tc) {
                return false;
            }
        }

        const meetsTotal = (marks.total || 0) >= uni.requiredTotal;
        const mathEnglish = (Number(marks.math) || 0) + (Number(marks.eng) || 0);
        const mathEnglishMinimum = uni.subjectSpecific?.math_eng_combo;
        if (uni.totalOrMathEnglish) {
            if (!(meetsTotal || mathEnglish >= mathEnglishMinimum)) return false;
        } else {
            if (Number.isFinite(uni.requiredTotal) && !meetsTotal) return false;
            if (mathEnglishMinimum !== undefined && mathEnglish < mathEnglishMinimum) return false;
        }
        if (uni.subjectSpecific && typeof uni.subjectSpecific === "object") {
            if (uni.subjectSpecific.pcm_eng_combo !== undefined) {
                const phy = Number(marks.phy) || 0;
                const chem = Number(marks.chem) || 0;
                const math = Number(marks.math) || 0;
                const eng = Number(marks.eng) || 0;
                if (phy + chem + math + eng < uni.subjectSpecific.pcm_eng_combo) return false;
            }
            if (uni.subjectSpecific.pcm_bio_combo !== undefined) {
                const subjects = ["phy", "chem", "math", "bio"];
                const sum = subjects.reduce((total, subject) => total + (Number(marks[subject]) || 0), 0);
                if (sum < uni.subjectSpecific.pcm_bio_combo) return false;
            }
            for (const [sub, min] of Object.entries(uni.subjectSpecific)) {
                if (sub === "math_eng_combo" || sub === "pcm_eng_combo" || sub === "pcm_bio_combo") continue;
                if (sub === "phy_math_or_chem_combo") {
                    const physics = Number(marks.phy) || 0;
                    const mathOrChemistry = Math.max(Number(marks.math) || 0, Number(marks.chem) || 0);
                    if (physics + mathOrChemistry < min) return false;
                    continue;
                }
                const val = Number(marks[sub]);
                if (Number.isNaN(val) || val < min) return false;
            }
        }
        if (!uni.requiredSubjects || uni.requiredSubjects.length === 0) return true;

        const first = uni.requiredSubjects[0];
        if (Array.isArray(first)) {
            return uni.requiredSubjects.some(set =>
                Array.isArray(set) &&
                set.every(sub => {
                    const v = marks[sub];
                    return v !== undefined && v !== "" && !Number.isNaN(Number(v));
                })
            );
        }

        return uni.requiredSubjects.every(sub => {
            const v = marks[sub];
            return v !== undefined && v !== "" && !Number.isNaN(Number(v));
        });
    }

    return { checkUniversity };
}));

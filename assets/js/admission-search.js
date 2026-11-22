
        const hamburger = document.getElementById('hamburger');
        const navLinks = document.getElementById('navLinks');

        hamburger.addEventListener('click', () => {
            navLinks.classList.toggle('show');
        });

        const subjectSets = {
            "STEAMS1": [
                { code: "myan", label: "Myanmar" },
                { code: "eng", label: "English" },
                { code: "math", label: "Mathematics" },
                { code: "phy", label: "Physics" },
                { code: "chem", label: "Chemistry" },
                { code: "bio", label: "Biology" }
            ],
            "STEAMS2": [
                { code: "myan", label: "Myanmar" },
                { code: "eng", label: "English" },
                { code: "math", label: "Mathematics" },
                { code: "phy", label: "Physics" },
                { code: "chem", label: "Chemistry" },
                { code: "eco", label: "Economics" }
            ],
            "STAMS1": [
                { code: "myan", label: "Myanmar" },
                { code: "eng", label: "English" },
                { code: "math", label: "Mathematics" },
                { code: "hist", label: "History" },
                { code: "geo", label: "Geography" },
                { code: "eco", label: "Economics" }
            ],
            "STAMS2": [
                { code: "myan", label: "Myanmar" },
                { code: "eng", label: "English" },
                { code: "math", label: "Mathematics" },
                { code: "eco", label: "Economics" },
                { code: "customMyan", label: "စိတ်ကြိုက်မြန်မာစာ" },
                { code: "social", label: "လူမှုရေးသိပ္ပံ" }
            ]
        };

        function generateSubjects() {
            const selectedSet = document.getElementById("subject-set").value;
            const container = document.getElementById("generated-subjects");

            container.innerHTML = "";

            if (!selectedSet) return;

            subjectSets[selectedSet].forEach(sub => {
                container.innerHTML += `
            <div class="subject-box">
                <label>${sub.label}</label>
                <input type="number" id="${sub.code}" placeholder="Mark" min="40" max="100" required>
            </div>
        `;
            });
        }

        function enableEnterJump() {
            const inputs = document.querySelectorAll("#generated-subjects input");

            inputs.forEach((input, index) => {
                input.onkeydown = e => {
                    if (e.key === "Enter") {
                        e.preventDefault();
                        if (inputs[index + 1]) {
                            inputs[index + 1].focus();
                        }
                    }
                };
            });
        }
        document.getElementById("subject-set").addEventListener("change", () => {
            generateSubjects();
            enableEnterJump();
        });
        const universities = window.unifitAdmissions;

        function checkUniversity(uni, marks, testCenter) {
            const tc = (testCenter || "").toString().toLowerCase();
            const allowed = uni.allowedCenters ?? "all";

            if (allowed !== "all") {
                if (Array.isArray(allowed)) {
                    if (!allowed.map(a => a.toString().toLowerCase()).includes(tc)) return false;
                } else {
                    if (allowed.toString().toLowerCase() !== tc) return false;
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
                    const phy = Number(marks["phy"]) || 0;
                    const chem = Number(marks["chem"]) || 0;
                    const math = Number(marks["math"]) || 0;
                    const eng = Number(marks["eng"]) || 0;

                    const sum = phy + chem + math + eng;

                    if (sum < uni.subjectSpecific.pcm_eng_combo) {
                        return false;
                    }
                }
                if (uni.subjectSpecific.pcm_bio_combo !== undefined) {
                    const subjects = ["phy", "chem", "math", "bio"];
                    const sum = subjects.reduce((total, subject) => total + (Number(marks[subject]) || 0), 0);
                    if (sum < uni.subjectSpecific.pcm_bio_combo) return false;
                }
                for (const [sub, min] of Object.entries(uni.subjectSpecific)) {
                    if (sub === "math_eng_combo") continue;
                    if (sub === "pcm_eng_combo") continue;
                    if (sub === "pcm_bio_combo") continue;
                    if (sub === "phy_math_or_chem_combo") {
                        const physics = Number(marks.phy) || 0;
                        const mathOrChemistry = Math.max(Number(marks.math) || 0, Number(marks.chem) || 0);
                        if (physics + mathOrChemistry < min) return false;
                        continue;
                    }
                    const val = Number(marks[sub]);
                    if (isNaN(val) || val < min) return false;
                }
            }
            if (!uni.requiredSubjects || uni.requiredSubjects.length === 0) return true;

            const first = uni.requiredSubjects[0];

            if (Array.isArray(first)) {
                return uni.requiredSubjects.some(set =>
                    Array.isArray(set) &&
                    set.every(sub => {
                        const v = marks[sub];
                        return v !== undefined && v !== "" && !isNaN(Number(v));
                    })
                );
            }

            return uni.requiredSubjects.every(sub => {
                const v = marks[sub];
                return v !== undefined && v !== "" && !isNaN(Number(v));
            });
        }

        function resultCard(uni, className) {
            const card = document.createElement("div");
            card.className = className;
            const name = document.createElement("strong");
            name.textContent = uni.name;
            card.appendChild(name);

            const scoreLabels = {
                eng: "English",
                math_eng_combo: "English + Mathematics",
                pcm_eng_combo: "Physics + Chemistry + Mathematics + English",
                pcm_bio_combo: "Physics + Chemistry + Mathematics + Biology",
                phy_math_or_chem_combo: "Physics + Mathematics or Physics + Chemistry",
            };
            const scores = [];
            if (Number.isFinite(uni.requiredTotal)) scores.push(`${uni.requiredTotal} total`);
            for (const [subject, score] of Object.entries(uni.subjectSpecific || {})) {
                if (scoreLabels[subject]) scores.push(`${score} in ${scoreLabels[subject]}`);
            }
            if (scores.length) {
                const summary = document.createElement("p");
                summary.className = "score-summary";
                summary.textContent = `Minimum: ${scores.join(uni.totalOrMathEnglish ? " or " : " · ")}`;
                card.appendChild(summary);
            }
            if (uni.confirmExamStream) {
                const note = document.createElement("p");
                note.className = "stream-note";
                note.textContent = "Confirm your exam stream with the university.";
                card.appendChild(note);
            }

            const detail = document.createElement("a");
            detail.className = "toggle-btn more-details";
            detail.href = uni.detailUrl;
            detail.target = "_blank";
            detail.rel = "noopener";
            detail.textContent = "More Details";
            card.appendChild(detail);
            return card;
        }

        function searchUniversities() {
            const selectedSet = document.getElementById("subject-set").value;

            if (!selectedSet) {
                alert("Please select a subject set first!");
                return;
            }

            const subjectList = subjectSets[selectedSet];
            const marks = {};

            for (let sub of subjectList) {
                const field = document.getElementById(sub.code);
                const value = field.value.trim();

                if (value === "") {
                    alert("Please fill all subject marks!");
                    field.focus();
                    return;
                }

                const num = Number(value);
                if (isNaN(num) || num < 40 || num > 100) {
                    alert("Please enter marks between 40 and 100!");
                    field.focus();
                    return;
                }

                marks[sub.code] = num;
            }

            marks.total = Object.values(marks).reduce((a, b) => a + b, 0);

            const spinner = document.getElementById("loading-spinner");
            const resultsDiv = document.getElementById("results");
            spinner.style.display = "flex";
            resultsDiv.innerHTML = "";

            setTimeout(() => {
                const testCenter = document.getElementById("division-select").value;
                const eligible = universities.filter(u => checkUniversity(u, marks, testCenter));

                const groups = {};
                eligible.forEach(u => {
                    const key = u.group || u.name;
                    if (!groups[key]) groups[key] = [];
                    groups[key].push(u);
                });

                const uniqueCount = Object.keys(groups).length;

                const h3 = document.createElement("h3");
                h3.textContent = eligible.some(uni => uni.confirmExamStream)
                    ? `Your University Matches: ${uniqueCount}`
                    : `Your Eligible Universities: ${uniqueCount}`;
                resultsDiv.appendChild(h3);

                if (eligible.length === 0) {
                    resultsDiv.innerHTML += "<p>No universities match your marks.</p>";
                    spinner.style.display = "none";
                    return;
                }

                const container = document.createElement("div");
                container.className = "results-container";

                Object.entries(groups).forEach(([groupName, list]) => {
                    if (list[0].group) {
                        const card = document.createElement("div");
                        card.className = "group-card";

                        const body = document.createElement("div");
                        body.className = "group-body";
                        body.style.display = "none";

                        const header = document.createElement("div");
                        header.className = "group-header";
                        header.innerHTML = `
                    <strong>${groupName}</strong>
                    <button class="group-toggle">Show ${list.length} majors</button>
                `;

                        header.querySelector(".group-toggle").onclick = function () {
                            if (body.style.display === "none") {
                                body.style.display = "";
                                this.textContent = `Hide ${list.length} majors`;
                            } else {
                                body.style.display = "none";
                                this.textContent = `Show ${list.length} majors`;
                            }
                        };

                        list.forEach(uni => body.appendChild(resultCard(uni, "uni-sub-card")));

                        card.appendChild(header);
                        card.appendChild(body);
                        container.appendChild(card);

                    } else {
                        container.appendChild(resultCard(list[0], "uni-card"));
                    }
                });

                resultsDiv.appendChild(container);

                document.getElementById("total-score").textContent = marks.total;
                document.getElementById("total-box").style.display = "block";

                spinner.style.display = "none";
            }, 800);
        }


        function clearForm() {
            const inputs = document.querySelectorAll("input");
            inputs.forEach(input => input.value = "");
        }


        const inputs = document.querySelectorAll("input");
        inputs.forEach((input, index) => {
            input.addEventListener("keydown", function (event) {
                if (event.key === "Enter") {
                    event.preventDefault();
                    const nextInput = inputs[index + 1];
                    if (nextInput) {
                        nextInput.focus();
                    }
                }
            });
        });

        const btn = document.getElementById("backToTop");
        window.onscroll = function () {
            if (document.body.scrollTop > 200 || document.documentElement.scrollTop > 200) {
                btn.style.display = "block";
            } else {
                btn.style.display = "none";
            }
        };
        btn.onclick = function () {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        };
    

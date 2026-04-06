# Master's Thesis Requirements at PJAIT Warsaw for Data Science

> **PJAIT's master's thesis process is a multi-semester, formally structured undertaking governed by the [university-wide Study Regulations][regulamin-studiow], faculty-level Dean's orders, and the national anti-plagiarism system.**

For a Data Science student in the Computer Science faculty (Wydział Informatyki), the thesis carries **26 ECTS** across three seminar courses, culminates in a two-part diploma exam (practical defense + theoretical oral), and requires both a written document and a working software prototype. No publicly available GenAI-specific policy exists, but Poland's national [anti-plagiarism system (JSA)][jsa-gov] has included AI-detection capabilities since February 2024, and every thesis is checked through it before defense.

The institutional framework combines general PJAIT regulations with CS faculty-specific Dean's orders. Notably, the Warsaw CS faculty does not publish a single standalone "Regulamin Dyplomowania" PDF for Informatyka — requirements are distributed across the [Study Regulations (Chapter 13)][regulamin-studiow], Dean's zarządzenia on SEM courses, the [thesis essentials webpage][niezbednik], and individual supervisor guidance. The closest equivalent is the [WZI (Faculty of Information Management) graduation regulations][regulamin-wzi], which share substantial structural overlap.

---

## 1. Formatting: Times New Roman, 1.5 Spacing, Hard-Bound

The official formatting standard is set by the [Wymogi wydawnicze prac dyplomowych][wymogi-wydawnicze] (Publishing Requirements for Diploma Theses) and the older [Wymogi redakcyjne][wymogi-redakcyjne] document. All master's theses must use **Times New Roman 12pt** for body text, **14pt bold** for chapter headings, **12pt bold** for subheadings, and **10pt** for footnotes. Line spacing is **1.5**, margins are **2.5 cm on all sides**, and text must be fully justified. Pages must be numbered.

The minimum length for a master's thesis is **72,000 characters with spaces** (approximately **40 normalized pages**). In practice, CS theses at PJAIT typically run **60–80 pages**, with the 40-page minimum considered a floor rather than a target. The thesis must be printed and **hard-bound in a subdued color** — navy blue, black, burgundy, or dark green — with the cover stating "praca magisterska."

The required document structure follows a conventional academic format: title page (per [official template][dokumenty-dyplomowe]), abstract (**400–1,500 characters with spaces**), keywords (minimum 3, up to 5), table of contents (auto-generated), list of abbreviations (if needed), introduction, numbered chapters and subchapters (1., 1.1., 1.1.1.), conclusion/summary, list of tables, list of figures, and bibliography.

The default citation style is the **traditional Polish footnote system** — references appear as footnotes at the bottom of each page. Individual supervisors in the CS faculty may accept alternative citation styles more common in technical literature (IEEE, APA), but the institutional default is footnote-based.

The official template is in **Microsoft Word**. Students wishing to use **LaTeX must independently recreate a matching template** — PJAIT provides no official LaTeX version. An [unofficial LaTeX template][latex-template] exists on GitLab. Regardless of authoring tool, the **final submission must be in PDF format**.

---

## 2. Language: Polish by Default, English Requires Dual Title Pages

Theses are written in Polish by default. Writing in a **foreign language (including English) requires consent from both the supervisor and the Dean**, per §33 of the [Study Regulations][regulamin-studiow]. A thesis written in English must additionally include a **second title page in Polish**, a **Polish-language abstract**, and **Polish keywords**. The diploma examination itself may also be conducted in the foreign language under the same approval.

---

## 3. Submission: GAKKO System and a 5-Step Process

PJAIT uses **GAKKO** (gakko.pjwstk.edu.pl) as its central student information and thesis management system — not APD (which is used at public universities). The supervisor enters thesis metadata into GAKKO, and the student fills in supplementary information.

The submission follows a formal process documented on the [thesis essentials page][niezbednik] and in the [diploma documents package][dokumenty-dyplomowe]:

**Step 1 — Initiate.** After the supervisor accepts the thesis, the student prints and binds one copy, burns CDs containing the thesis as a single PDF file (maximum **45 MB**, not zipped), source code, and any compiled application. The student prints and signs the *oświadczenie o samodzielnym pisaniu pracy* (declaration of independent authorship).

**Step 2 — Submit.** Documents go to the Library (bound thesis + 1 CD for plagiarism checking) and the Dean's Office (remaining CDs + signed declarations). The Library uploads the thesis to [JSA][jsa-gov], which guarantees results within **7 working days**. The supervisor must accept the JSA result in GAKKO.

**Step 3 — Clearance (obiegówka).** The student requests creation of a clearance form in GAKKO only after obtaining absolutorium and the supervisor's acceptance of the plagiarism result. The form requires sign-offs from: Library → Accounting → Supervisor → Reviewer → Dean's Office.

**Step 4 — Defense day.** The Committee Chair collects documents from the Dean's Office at least 30 minutes before the scheduled defense.

**Step 5 — Post-defense.** Diploma information appears in GAKKO. An additional English-language diploma copy can be requested within 30 days for **40 PLN**.

The thesis completion deadline is the **last day of classes** in the given semester. Students who fail to submit face removal from the student register per Art. 108 of the Polish Higher Education Act. A person removed may apply for reinstatement **within 2 years**; defense is then possible only in **March or October**, with a one-time fee of **1,500 PLN**.

---

## 4. Defense: Two-Part Exam with Presentation and Oral Questions

The diploma examination (*egzamin dyplomowy*) consists of two distinct parts per the [Study Regulations §35–37][regulamin-studiow] and [Gdańsk CS faculty instructions][gdansk-instrukcja] (which mirror Warsaw procedures). The student **must pass the practical part before proceeding to the theoretical part**.

**Practical part (obrona).** The student delivers a synthetic presentation — methodology, project execution, and results — lasting a **maximum of 15–20 minutes**. The committee then asks questions about the thesis work.

**Theoretical part.** This is an oral examination before the same committee. The student receives **3 questions**: **1 question on the student's specialization** (e.g., Data Science) and **2 general questions drawn from a published set** covering the entire master's study program (*Zestaw zagadnień na egzamin dyplomowy*). The student receives preparation time before answering.

**Committee composition.** The Diploma Examination Committee has a **minimum of 3 members**: the **Chair**, the **Supervisor** (promotor), and the **Reviewer** (recenzent). The Chair must hold at least a doctoral degree. For master's theses, both the supervisor and reviewer must hold **at minimum a doctoral degree (doktor)**.

---

## 5. Grading: A Weighted Formula Favoring Cumulative GPA

The grading system per the [Study Regulations][regulamin-studiow] and [WZI graduation regulations][regulamin-wzi]:

**Thesis grade** equals the **arithmetic mean of the supervisor's and reviewer's independent grades**. If the reviewer assigns a failing grade, the Dean appoints a second reviewer; two failing reviews means the thesis cannot be defended.

**Final diploma result** uses the formula:

$$\text{Final} = \frac{1}{2} \times \text{GPA} + \frac{1}{4} \times \text{thesis grade} + \frac{1}{4} \times \text{exam grade}$$

The diploma grade thresholds: up to 3.39 = dostateczny, 3.40–3.79 = dostateczny plus, 3.80–4.19 = dobry, 4.20–4.49 = dobry plus, **4.50+ = bardzo dobry**. A **diploma with distinction** requires: cumulative GPA ≥ 4.5, thesis grade of **5.0 from both** supervisor and reviewer, exam grade of 5.0, and a formal motion recognizing exceptional merit.

---

## 6. GenAI Policy: No Explicit Rule, but JSA Detects AI Content

**PJAIT has not published a specific rector's ordinance on generative AI usage** in thesis writing — at least not on its public-facing website. What PJAIT does enforce is the **mandatory [JSA check][jsa-gov]** for every thesis. Since **February 2024**, [JSA includes AI-generated text detection][jsa-ai-detection] — it analyzes text regularity and predictability patterns that distinguish machine-generated prose from human writing. The result is a probability score; the **final decision on acceptability rests with the supervisor**.

The [anti-plagiarism regulation][regulamin-antyplagiat] (Uchwała Senatu nr 4, 22.04.2015) establishes a three-stage verification process. Key thresholds are a **similarity coefficient #2 exceeding 30%** or citations constituting 40%+ of the text.

The student must also sign a **declaration of independent authorship** ([oświadczenie studenta][dokumenty-dyplomowe]), which states the work was written independently.

For broader Polish context: [Polish universities are converging][polish-ai-landscape] on a **"supervisor decides" decentralized model** for AI tool usage. The [University of Warsaw guidelines][uw-ai] require AI use to be agreed upon with the supervisor and documented in the methodology chapter. SGH Warsaw School of Economics permits AI as a supporting tool with full transparency. PJAIT appears to operate under this decentralized model by default.

**Practical recommendation**: treat AI tools as assistants, disclose usage to your supervisor proactively — they will see the JSA AI-detection score regardless. The authorship declaration carries legal weight under Polish academic integrity law.

---

## 7. CS and Data Science Theses: Prototype Required, Novelty Expected

A master's thesis in the Computer Science faculty must contain an **element of novelty** (*element nowatorski*). As [Dr. Mariusz Trzaska][trzaska-seminar] (prominent PJAIT CS supervisor) explains: the master's thesis mainly concerns the development of a certain idea, concept, or solution to a problem; the prototype is a "side effect" demonstrating feasibility.

A **working software prototype** is expected and must be delivered on CD alongside the thesis. The recommended thesis structure for CS/Data Science follows five sections: motivation/introduction, state of the art (existing solutions analysis), proposed solution (the most important chapter), implementation/prototype details, and conclusions.

There is **no mandatory requirement for a GitHub or GitLab repository**. The official requirement is to deliver source code on physical **CDs**. Copyright on the code belongs to the student; if published (e.g., on GitHub), it must note it was created as part of PJAIT coursework.

For the **[Data Science specialization][pjait-data-science]** specifically, the program includes courses such as Introduction to Machine Learning (WUM), Advanced Machine Learning (ZUM), Big Data (BGD), and Large Dataset Analysis (ADD). Common thesis topics include machine learning applications, comparative benchmarking studies, data pipeline architectures, and NLP projects.

---

## 8. ECTS Allocation: 26 Credits Across Three Seminar Semesters

The thesis work in the [3-semester CS master's program][pjait-program] is distributed across three seminar courses totaling **26 ECTS**: **SEM1 carries 5 ECTS**, **SEM2 carries 6 ECTS**, and **SEM3 carries 15 ECTS**. The full program totals approximately **94 ECTS**.

Milestone expectations per semester, per [Dr. Trzaska's seminar guidelines][trzaska-seminar] and the Dean's Order of October 18, 2024:

- **SEM1**: Select a supervisor, establish the exact topic and scope, prepare and submit a thesis outline (*konspekt*) per the established template.
- **SEM2**: Demonstrate clear progress — literature review and theoretical framework substantially developed, initial implementation begun.
- **SEM3**: Completed master's thesis (both written text and prototype). Passing SEM3 is conditioned on the supervisor's positive opinion and a positive anti-plagiarism result.

Before defense, the student must have obtained **absolutorium** (completion of all coursework and credit requirements except the thesis seminar). Students who don't pass the seminar on time may need to purchase an **ITN (Indywidualny Tok Nauki)** extension.

---

## 9. Practical Takeaways for a Data Science Thesis

The PJAIT thesis process is more administratively structured than at many Polish universities. **The most critical practical insight is timeline management**: the 7-day JSA turnaround, supervisor review cycles, and obiegówka sign-off chain mean students should submit the thesis to the library **at least 3–4 weeks before the defense date**.

For a Data Science thesis, the strongest approach combines a clear conceptual contribution (novel analytical method, framework, or comparative analysis) with a functional prototype that validates the concept. The thesis should lean heavily on the "proposed solution" chapter — this is where the master's-level novelty lives — rather than spending disproportionate space on implementation details.

Students should obtain the published *Zestaw zagadnień na egzamin dyplomowy* (theoretical exam question set) from their supervisor early and prepare for the oral component alongside thesis writing. Defense sessions at PJAIT are scheduled in batches announced via [Dean's orders][defense-schedule], typically in February–March (winter semester) and June–July / September–October (summer semester).

---

## References

<!-- PJAIT official regulations -->
[regulamin-studiow]: https://pja.edu.pl/wp-content/uploads/2024/08/Regulamin-Studiow-PJATK-2024-2025_BIP.pdf "Regulamin Studiów PJATK 2024/2025 (Study Regulations)"
[regulamin-wzi]: https://pja.edu.pl/wp-content/uploads/2024/07/Regulamin-dyplomowania-WZI_-2023.pdf "Regulamin Dyplomowania — Wydział Zarządzania Informacją PJATK (2023)"
[regulamin-antyplagiat]: https://pja.edu.pl/wp-content/uploads/2023/02/Regulamin_postepowania_antyplagiatowego_5.pdf "Regulamin postępowania antyplagiatowego PJATK (Uchwała Senatu nr 4)"

<!-- PJAIT thesis formatting and templates -->
[wymogi-wydawnicze]: https://pja.edu.pl/wp-content/uploads/2024/06/Wymogi-wydawnicze-prac-dyplomowych.pdf "Wymogi wydawnicze prac dyplomowych — PJATK (2024)"
[wymogi-redakcyjne]: https://pja.edu.pl/wp-content/uploads/2023/06/Wymogi-redakcyjne-prac-dyplomowych-KJ.pdf "Wymogi redakcyjne prac dyplomowych — PJATK"
[dokumenty-dyplomowe]: https://pja.edu.pl/wp-content/uploads/2023/04/Dokumenty-dyplomowe.pdf "Dokumenty dyplomowe — pakiet formularzy PJATK"
[latex-template]: https://gitlab.com/linoskoczek/szablon-pracy-dyplomowej-pjatk "Unofficial PJAIT LaTeX thesis template — GitLab"

<!-- PJAIT thesis process pages -->
[niezbednik]: https://pja.edu.pl/en/niezbednik-pracy-dyplomowej-wzi/ "Essentials for writing a thesis (Niezbędnik pracy dyplomowej) — PJAIT"
[pjait-students]: https://pja.edu.pl/en/dla-studenta/ "For students — PJAIT"
[defense-schedule]: https://pja.edu.pl/wp-content/uploads/2024/04/23.04.2024_Zarzadzenie-Dziekana-WZI-dot.-terminow-obron_LATO_23_24-1.pdf "Zarządzenie Dziekana WZI — terminy obron, semestr letni 2023/24"

<!-- PJAIT CS faculty and Gdańsk branch instructions -->
[gdansk-instrukcja]: https://gdansk.pja.edu.pl/wp-content/uploads/2025/09/Instrukcja-dyplomowania-od-2024_2025.pdf "Instrukcja dyplomowania — Wydział Informatyki PJATK Gdańsk (2024/2025)"

<!-- PJAIT Data Science program -->
[pjait-data-science]: https://pja.edu.pl/informatyka/informatyka-studia-ii-stopnia-stacjonarne-polskojezyczne/specjalizacje-2/informatyka-data-science/ "Informatyka, studia II stopnia — Data Science — PJATK"
[pjait-program]: https://pja.edu.pl/wp-content/uploads/2024/07/Stacjonarne_drugi_stopien_semletni_2024-25_PL.pdf "Plan studiów stacjonarnych II stopnia 2024/25 — PJATK"

<!-- Supervisor guidance -->
[trzaska-seminar]: https://www.mtrzaska.com/seminarium-magisterskie-informacje/ "Seminarium magisterskie — informacje. Dr Mariusz Trzaska, PJATK"
[trzaska-topics]: https://www.mtrzaska.com/tematyka-prac-magisterskich/ "Tematyka prac magisterskich — Dr Mariusz Trzaska, PJATK"

<!-- JSA and AI detection -->
[jsa-gov]: https://www.gov.pl/web/nauka/jsa--promotor-sprawdzi-czy-student-korzystal-z-technologii-chatgpt "JSA — promotor sprawdzi, czy student korzystał z technologii ChatGPT. Ministerstwo Nauki i Szkolnictwa Wyższego"
[jsa-ai-detection]: https://jsa-cp.opi.org.pl/tag/ai/ "AI — Jednolity System Antyplagiatowy (OPI)"

<!-- Polish university AI landscape -->
[polish-ai-landscape]: https://www.bryk.pl/artykul/studenci-moga-korzystac-z-ai-w-pracach-pisemnych-ale-wedlug-zasad "Jak uczelnie regulują korzystanie z AI? — Bryk.pl"
[uw-ai]: https://www.uw.edu.pl/wytyczne-urk-dotyczace-sztucznej-inteligencji-w-procesie-ksztalcenia/ "Wytyczne URK dotyczące sztucznej inteligencji — Uniwersytet Warszawski"

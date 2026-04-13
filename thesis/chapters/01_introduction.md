# Chapter 1 — Introduction

## 1.1 Background and motivation

Na przestrzeni ostatniej dekady sport elektroniczny przekształcił się z niszowej rozrywki w zjawisko o wymiernym znaczeniu komercyjnym, kulturowym i — co istotniejsze z perspektywy badawczej — metodologicznym. Raporty branżowe szacują przychody globalnego rynku esportowego w 2024 roku na poziomie przekraczającym miliard dolarów [Newzoo2024], jednak to nie skala komercyjna uzasadnia uwagę naukową poświęconą tej domenie, lecz specyfika danych, jakie generuje. Gry wieloosobowe, produkujące obszerne zapisy telemetryczne z każdego meczu, stały się atrakcyjnym poligonem doświadczalnym dla metod uczenia maszynowego, statystyki i analizy danych [Vinyals2017, Bialecki2023].

Wśród gatunków gier szczególne miejsce zajmują gry strategiczne czasu rzeczywistego (ang. *real-time strategy*, RTS). Predykcja wyników w grach RTS jest zadaniem istotnie trudniejszym niż w grach turowych, takich jak szachy czy Go, z kilku fundamentalnych powodów. Po pierwsze, gry RTS charakteryzują się niepełną informacją wynikającą z mechaniki mgły wojny (ang. *fog of war*) — każdy gracz obserwuje jedynie fragment mapy w zasięgu swoich jednostek, co oznacza, że stan przeciwnika jest ukryty i musi być wnioskowany na podstawie ograniczonych obserwacji [Ontanon2013]. Po drugie, decyzje podejmowane są w czasie ciągłym, a nie na przemian — obaj gracze działają jednocześnie, co generuje kombinatoryczną przestrzeń akcji szacowaną średnio na około 10^26 legalnych działań w każdym kroku czasowym [Vinyals2019]. Po trzecie, frakcje (rasy w StarCraft II, cywilizacje w Age of Empires II) nie są symetryczne — różnią się mechanikami, drzewkami technologicznymi i optymalną strategią, co wprowadza złożoność interakcji znacznie wykraczającą poza modele gier o pełnej informacji z symetrycznymi zestawami figur, takich jak szachy czy Go [Ontanon2013, Vinyals2019].

Te cechy sprawiają, że gry RTS stanowią szczególnie wartościowy obiekt badawczy z perspektywy nauk o danych. Złożoność przestrzeni stanów i działań powoduje, że proste modele heurystyczne szybko osiągają sufit predykcyjny, a jednocześnie bogate dane telemetryczne — obejmujące historię meczów graczy, wybory frakcji, informacje o mapie, a w przypadku gier z dostępnymi powtórkami również serie czasowe stanu ekonomicznego i militarnego — dostarczają materiału do budowy zaawansowanych klasyfikatorów [Bialecki2023]. Vinyals i in. [Vinyals2017] wskazali explicite, że StarCraft II spełnia kryteria wielkiego wyzwania (ang. *grand challenge*) dla uczenia ze wzmocnieniem właśnie ze względu na współwystępowanie niepełnej informacji, dużej przestrzeni akcji, rozległej przestrzeni stanów i odroczonego przypisywania nagrody. Późniejsze osiągnięcie poziomu arcymistrza przez agenta AlphaStar [Vinyals2019] potwierdziło tę ocenę, ujawniając zarazem, że nawet agent grający na poziomie czołowych zawodników nie eliminuje niepewności wynikającej z ukrytego stanu gry — co oznacza, że zadanie predykcji wyniku meczu na podstawie dostępnych danych pozostaje otwartym problemem badawczym.

Praktyczne zastosowania modeli predykcyjnych w esporcie obejmują kilka wyraźnie zarysowanych obszarów. W transmisji sportowej modele estymujące prawdopodobieństwo zwycięstwa w czasie rzeczywistym wzbogacają przekaz dla widzów, dostarczając narracyjnego kontekstu zbliżonego do nakładek znanych z transmisji szachowych. Hodge i in. [Hodge2021] wykazali, że model oparty na metodzie gradientowego wzmacniania drzew decyzyjnych osiąga trafność rzędu 85% po pięciu minutach rozgrywki w Dota 2, co wskazuje na realną użyteczność takich systemów w warunkach transmisji na żywo. W branży zakładów bukmacherskich modele predykcyjne stanowią fundament systemów wyceny kursów. Trzeci obszar — narzędzia trenerskie — wykorzystuje modele do identyfikacji słabych punktów w strategii gracza na podstawie analizy ważności cech (ang. *feature importance*) w wytrenowanych modelach [Hodge2021]. Wreszcie, w badaniach nad sztuczną inteligencją modele predykcyjne służą jako narzędzie ewaluacyjne: porównanie przewidywań modelu z rzeczywistymi wynikami agentów AI pozwala ocenić, w jakim stopniu agent podejmuje decyzje zbliżone do optymalnych z perspektywy zagregowanych statystyk meczu [Vinyals2019].

Pomimo rosnącej liczby badań nad predykcją wyników w grach esportowych — w tym prac poświęconych grom z gatunku MOBA, takim jak Dota 2 [Hodge2021] i League of Legends, oraz pracom dotyczącym StarCraft II [Baek2022] — można zaobserwować istotną lukę badawczą. Brak jest opublikowanych prac porównujących skuteczność metod predykcji *pomiędzy* różnymi grami RTS, w szczególności w warunkach asymetrycznej dostępności danych. Niniejsza praca podejmuje to zagadnienie, realizując porównawczą analizę metod predykcji wyników meczów 1v1 w StarCraft II i Age of Empires II — dwóch grach reprezentujących ten sam gatunek, ale różniących się zarówno mechaniką rozgrywki, jak i zakresem dostępnych danych telemetrycznych.

## 1.2 Problem statement

<!--
Formal definition: given pre-game context for a 1v1 RTS match, predict P(focal player wins).
Secondary: how does in-game state improve prediction (SC2 only)?
-->

## 1.3 Research questions

<!--
RQ1: Which ML methods achieve highest prediction accuracy?
RQ2: Which feature categories contribute most?
RQ3: Do best methods generalise across SC2 and AoE2?
RQ4: How does accuracy vary with player history length (cold-start)?
Finalise after experiments confirm these are answerable.
-->

## 1.4 Scope and limitations

<!--
1v1 only, professional/ranked, SC2 has in-game state but AoE2 does not,
per-game prediction not per-tournament.
-->

## 1.5 Thesis outline

<!--
Write last — brief description of each chapter.
-->

## References

- [Vinyals2017] Vinyals, O., Ewalds, T., Bartunov, S., Georgiev, P., Vezhnevets, A. S., Yeo, M., Makhzani, A., Kuttler, H., Agapiou, J., Schrittwieser, J., Quan, J., Gaffney, S., Petersen, S., Simonyan, K., Schaul, T., van Hasselt, H., Silver, D., Lillicrap, T., Calderone, K., Keet, P., Brunasso, A., Lawrence, D., Ekermo, A., Repp, J., & Tsing, R. (2017). StarCraft II: A New Challenge for Reinforcement Learning. arXiv preprint arXiv:1708.04782.

- [Vinyals2019] Vinyals, O., Babuschkin, I., Czarnecki, W. M., Mathieu, M., Dudzik, A., Chung, J., Choi, D. H., Powell, R., Ewalds, T., Georgiev, P., Oh, J., Horgan, D., Kroiss, M., Danihelka, I., Huang, A., Sifre, L., Cai, T., Agapiou, J. P., Jaderberg, M., ... Silver, D. (2019). Grandmaster level in StarCraft II using multi-agent reinforcement learning. Nature, 575(7782), 350-354.

- [Ontanon2013] Ontanon, S., Synnaeve, G., Uriarte, A., Richoux, F., Churchill, D., & Preuss, M. (2013). A Survey of Real-Time Strategy Game AI Research and Competition in StarCraft. IEEE Transactions on Computational Intelligence and AI in Games, 5(4), 293-311.

- [Bialecki2023] Bialecki, A., Jakubowski, M., Wozniak, P., Siedlaczek, J., & Tabaszewski, D. (2023). SC2EGSet: StarCraft II Esport Replay and Game-state Dataset. Scientific Data, 10(1), 600.

- [Hodge2021] Hodge, V. J., Devlin, S. M., Sephton, N. J., Block, F. O., Cowling, P. I., & Drachen, A. (2021). Win Prediction in Multi-Player Esports: Live Professional Match Prediction. IEEE Transactions on Games, 13(4), 368-379.

- [Baek2022] Baek, J., & Kim, S. (2022). 3-Dimensional convolutional neural networks for predicting StarCraft II results and extracting key game situations. PLOS ONE, 17(3), e0264550.

- [Newzoo2024] Newzoo. (2024). Global Esports & Live Streaming Market Report 2024. Newzoo BV. [Industry report]

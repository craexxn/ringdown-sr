# Zusatzbewertung der vier Originalserien – Stufe 1

Stand: 05.11.2026. Lesende Anwendung der [Bewertungsfassung 1](supplemental_assessment.md)
auf alle vier vollständigen, verifizierten Originalarchive: **78 ursprüngliche
Auswahlen**. Korpusstatus `complete`; jede Serie wird getrennt freigegeben.
Keine gemeinsame Erfolgsquote über unterschiedliche Bedingungen.

Vertrag und erste Implementierung wurden vor jeder Anwendung als
`fee9418071834b1ea42692cb436ecdd8fb6d4fd3` committed. Die vollständige Anwendung
verwendet `efb2accd4a31ebf4206b40acaf261a3bf04b31ad`, einschließlich der
abschließenden Inventarprüfung bei Veröffentlichung. Die Regeln sind retrospektiv;
daraus entsteht keine rückwirkende Blindvalidierung.

## Primärdaten und Prüfung

| Originalserie | Auswahlen | Archiv-SHA-256 vor und nach Verarbeitung |
| --- | ---: | --- |
| duration-manjaro-004 | 20 | `c2d9e330770746030bab9467b682a6b595cac25aa132dbb4decd1c4b03472289` |
| local-optimizer-manjaro-001 | 20 | `1ab8c0aa91436c4b169c6c6efa8053e04c47ef57d07915f36ac476483276866d` |
| outer-ladder-manjaro-001 | 20 | `ac7e841b79042e216d6aacae2961ffb8395f298bbcc7ecc11f1092c90b3deb40` |
| transfer-manjaro-001 | 18 | `e363fe1be629973a460fc6e2188bf680c21b2c5519d331bc7e257968dcaaa139` |

Ursprüngliche Indizes und Kandidatenhashes, vollständige Manifeste, Quellen-,
Plan- und Datenbindungen sowie historische Verifikationsnachweise wurden
lesend geprüft. Archivprogramme wurden nicht ausgeführt. Keine neue Suche,
kein Fit und keine pauschale native Gesamtaudit-Serie.

Eine separate Prüfung mit exakten rationalen Darstellungen der Float64-Werte
bestätigt alle 78 Noten. Alle Originalkandidaten und Auswahldiagnosen wurden
wertgleich, die vier vollständigen historischen Serienberichte bytegleich
übernommen. Neue Klasse A stimmt in jedem Fall mit dem alten Kurvenmarker
überein. Auch die bereits separat bewerteten 18 Transferfälle bleiben unverändert.
Manifest und Abschlussstatus sind konsistent; kein Sperrmarker ist vorhanden.

## Ursprüngliche Versuchsgruppen

| Serie | Signal / Bedingung | Äußere Iterationen | Nenner | A | B | C | D | Nicht bewertbar |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| duration-manjaro-004 | unrestricted | 200 | 5 | 3 | 0 | 1 | 1 | 0 |
| duration-manjaro-004 | no_nested_trig | 200 | 5 | 2 | 0 | 0 | 3 | 0 |
| duration-manjaro-004 | no_nested_trig | 2000 | 5 | 3 | 0 | 2 | 0 | 0 |
| duration-manjaro-004 | unrestricted | 2000 | 5 | 4 | 0 | 0 | 1 | 0 |
| local-optimizer-manjaro-001 | local_100_2 | 200 | 5 | 1 | 0 | 3 | 1 | 0 |
| local-optimizer-manjaro-001 | local_300_2 | 200 | 5 | 2 | 0 | 2 | 1 | 0 |
| local-optimizer-manjaro-001 | local_300_5 | 200 | 5 | 3 | 0 | 1 | 1 | 0 |
| local-optimizer-manjaro-001 | local_100_5 | 200 | 5 | 2 | 1 | 1 | 1 | 0 |
| outer-ladder-manjaro-001 | local_300_5 | 200 | 5 | 1 | 1 | 0 | 3 | 0 |
| outer-ladder-manjaro-001 | local_300_5 | 500 | 5 | 5 | 0 | 0 | 0 | 0 |
| outer-ladder-manjaro-001 | local_300_5 | 5000 | 5 | 5 | 0 | 0 | 0 | 0 |
| outer-ladder-manjaro-001 | local_300_5 | 2000 | 5 | 5 | 0 | 0 | 0 | 0 |
| transfer-manjaro-001 | anchor | 500 | 3 | 0 | 0 | 1 | 2 | 0 |
| transfer-manjaro-001 | frequency | 500 | 3 | 1 | 0 | 2 | 0 | 0 |
| transfer-manjaro-001 | decay | 500 | 3 | 1 | 1 | 1 | 0 | 0 |
| transfer-manjaro-001 | phase | 500 | 3 | 2 | 0 | 0 | 1 | 0 |
| transfer-manjaro-001 | amplitude | 500 | 3 | 1 | 1 | 1 | 0 | 0 |
| transfer-manjaro-001 | combined | 500 | 3 | 2 | 1 | 0 | 0 | 0 |

Die feinere Skala beschreibt den Abstand zu den bisherigen engen Grenzen.
Sie verbessert keine Formel und beweist weder eine Ringdown-Identität noch
Definitionslückenfreiheit. Historische C-/S-Zählungen bleiben unverändert.

## Ursprüngliche Einzelentscheidungen

Kennzahlen sind die unveränderten gespeicherten Float64-Werte in rücklesbarer
Dezimaldarstellung. Der Auswahlindex ist wie in `result.json` nullbasiert.

### duration-manjaro-004

| Zelle | Seed | Signal / Bedingung | Außen | Index | Klasse | RMS Training | Max Training | RMS Diagnose | Max Diagnose |
| ---: | ---: | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| 1 | 20261103 | unrestricted | 200 | 8 | A | 8.477079458624036e-10 | 4.54644100145174e-10 | 8.73335562729797e-10 | 4.618376237019702e-10 |
| 2 | 20261103 | no_nested_trig | 200 | 8 | A | 4.506539863463393e-11 | 5.164957350700661e-11 | 4.6419150804282696e-11 | 5.2474108391988175e-11 |
| 3 | 20261103 | no_nested_trig | 2000 | 7 | A | 6.0176081230450575e-12 | 3.2235880631503733e-12 | 6.197698389354278e-12 | 3.263694869915009e-12 |
| 4 | 20261103 | unrestricted | 2000 | 7 | A | 1.1126831394503779e-13 | 5.928590951498336e-14 | 1.1466631381783856e-13 | 6.056266599330233e-14 |
| 5 | 20261104 | no_nested_trig | 200 | 9 | A | 3.3002239442109335e-05 | 2.0840192432772242e-05 | 3.371900632041529e-05 | 2.1112841446875692e-05 |
| 6 | 20261104 | unrestricted | 2000 | 9 | A | 2.2679552776674447e-09 | 1.2153418826876816e-09 | 2.3365363834348235e-09 | 1.2242489799696443e-09 |
| 7 | 20261104 | unrestricted | 200 | 10 | A | 6.486527170906325e-08 | 4.541932250440306e-08 | 6.682274540885701e-08 | 4.5754677740993304e-08 |
| 8 | 20261104 | no_nested_trig | 2000 | 5 | A | 1.501831897063402e-12 | 8.112399640936019e-13 | 1.5472690501671654e-12 | 8.179568133925908e-13 |
| 9 | 20261105 | unrestricted | 2000 | 10 | A | 3.1464506120617664e-13 | 1.9156898289907076e-13 | 3.233763907765229e-13 | 1.9245716131877089e-13 |
| 10 | 20261105 | no_nested_trig | 2000 | 9 | C | 0.010697484500411445 | 0.007132339765657705 | 0.010836056013201067 | 0.006667642802827565 |
| 11 | 20261105 | no_nested_trig | 200 | 9 | D | 0.10660471182683676 | 0.07371144823568213 | 0.10826286449552847 | 0.07493811246858353 |
| 12 | 20261105 | unrestricted | 200 | 7 | A | 5.270733601313411e-11 | 2.8251595507455818e-11 | 5.427900570076804e-11 | 2.8596458534480007e-11 |
| 13 | 20261106 | no_nested_trig | 2000 | 8 | A | 6.742064197496719e-12 | 3.653577440587696e-12 | 6.94582010060822e-12 | 3.6718961204941504e-12 |
| 14 | 20261106 | unrestricted | 200 | 11 | D | 0.0800140092531913 | 0.07253537481005146 | 0.08036160703608983 | 0.07147282703846491 |
| 15 | 20261106 | unrestricted | 2000 | 11 | D | 0.010652093082945686 | 0.011778141856649604 | 1.5105510701464138 | 1.9746274902153809 |
| 16 | 20261106 | no_nested_trig | 200 | 11 | D | 0.1024955831548461 | 0.09312827612199881 | 0.10288996146682845 | 0.09139630119037978 |
| 17 | 20261107 | unrestricted | 200 | 10 | C | 0.013420295509020429 | 0.02386946458261563 | 0.012192035812595571 | 0.022169410037569337 |
| 18 | 20261107 | no_nested_trig | 200 | 6 | D | 0.7405373545955104 | 0.6843868969741089 | 0.8467358630387468 | 1.1130320608175182 |
| 19 | 20261107 | no_nested_trig | 2000 | 12 | C | 0.02282133882731483 | 0.02626145822215631 | 0.022544073114688482 | 0.025801361982897175 |
| 20 | 20261107 | unrestricted | 2000 | 6 | A | 2.3339670076482124e-12 | 1.2544965066751956e-12 | 2.404268765469483e-12 | 1.2703726959273354e-12 |

### local-optimizer-manjaro-001

| Zelle | Seed | Signal / Bedingung | Außen | Index | Klasse | RMS Training | Max Training | RMS Diagnose | Max Diagnose |
| ---: | ---: | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| 1 | 20261120 | local_100_2 | 200 | 9 | C | 0.02239909503160775 | 0.024224131931802617 | 0.02223047796240307 | 0.023714444703591075 |
| 2 | 20261120 | local_300_2 | 200 | 6 | A | 1.4170619059679693e-11 | 7.641540178404682e-12 | 1.4594175022297653e-11 | 7.673445212575066e-12 |
| 3 | 20261120 | local_300_5 | 200 | 5 | A | 1.0339824740700961e-12 | 5.515032874825465e-13 | 1.064935777711208e-12 | 5.608846720406291e-13 |
| 4 | 20261120 | local_100_5 | 200 | 10 | C | 0.04127683080551633 | 0.03611773568607404 | 0.04144674362719571 | 0.03455920186096025 |
| 5 | 20261121 | local_300_2 | 200 | 10 | C | 0.04110188990675676 | 0.0338910426423673 | 0.041386997929260774 | 0.03237214560932933 |
| 6 | 20261121 | local_100_5 | 200 | 10 | D | 0.39901239997464066 | 1.0 | 0.28867577997508626 | 0.8693652029148844 |
| 7 | 20261121 | local_100_2 | 200 | 11 | C | 0.04069240665357403 | 0.03292744321259656 | 0.04101107263643132 | 0.03144297665034628 |
| 8 | 20261121 | local_300_5 | 200 | 8 | D | 0.716102246519166 | 0.6356300115746348 | 0.7377453281846998 | 0.6383257746503139 |
| 9 | 20261122 | local_100_5 | 200 | 6 | A | 1.3019467878343727e-11 | 6.5120964176657026e-12 | 1.3407271080227574e-11 | 6.5919769642874826e-12 |
| 10 | 20261122 | local_300_5 | 200 | 7 | A | 4.779180462126874e-09 | 2.5869155706459424e-09 | 4.922790868495013e-09 | 2.601467430363158e-09 |
| 11 | 20261122 | local_300_2 | 200 | 8 | C | 0.0452199992408665 | 0.03147635791921055 | 0.045805986578030373 | 0.029559661048031205 |
| 12 | 20261122 | local_100_2 | 200 | 10 | D | 0.709644414259024 | 0.7374206465320394 | 0.7074125374525245 | 0.7357827379552868 |
| 13 | 20261123 | local_300_5 | 200 | 6 | A | 8.699392949922515e-12 | 4.665934305592145e-12 | 8.962368550495642e-12 | 4.7395420921250235e-12 |
| 14 | 20261123 | local_100_2 | 200 | 11 | C | 0.01045983428040931 | 0.0073489615856845705 | 0.01057589683751237 | 0.0066447479483415705 |
| 15 | 20261123 | local_100_5 | 200 | 11 | B | 0.005606326595566791 | 0.004075369302341647 | 0.005669101906452647 | 0.0038412403794565383 |
| 16 | 20261123 | local_300_2 | 200 | 9 | D | 0.07337528172469256 | 0.06677786636582073 | 0.0736843787602235 | 0.06586523041131476 |
| 17 | 20261124 | local_100_2 | 200 | 4 | A | 9.385005467465738e-12 | 5.034347938526196e-12 | 9.665883469351978e-12 | 5.089706434091568e-12 |
| 18 | 20261124 | local_300_2 | 200 | 6 | A | 1.9660020222682688e-10 | 1.0548129036891396e-10 | 2.0252536850512682e-10 | 1.0705203390425844e-10 |
| 19 | 20261124 | local_300_5 | 200 | 9 | C | 0.04901537296635437 | 0.05733165933158346 | 0.04834230192410854 | 0.05627771993467734 |
| 20 | 20261124 | local_100_5 | 200 | 7 | A | 3.583559789076237e-05 | 2.3614262077219228e-05 | 3.658344617434472e-05 | 2.385994246315851e-05 |

### outer-ladder-manjaro-001

| Zelle | Seed | Signal / Bedingung | Außen | Index | Klasse | RMS Training | Max Training | RMS Diagnose | Max Diagnose |
| ---: | ---: | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| 1 | 20261201 | local_300_5 | 200 | 6 | D | 0.09389197588530608 | 0.097180386256984 | 0.0935615831058368 | 0.09595317670356773 |
| 2 | 20261201 | local_300_5 | 500 | 6 | A | 4.1390190405572185e-12 | 2.2396529075763283e-12 | 4.264165348633605e-12 | 2.254751940711283e-12 |
| 3 | 20261201 | local_300_5 | 5000 | 11 | A | 3.0156845930527834e-13 | 1.6263379531977762e-13 | 3.1049066532638366e-13 | 1.6340834935180126e-13 |
| 4 | 20261201 | local_300_5 | 2000 | 8 | A | 3.107765724645458e-13 | 1.6725509865977983e-13 | 3.200024106672888e-13 | 1.6864287744056128e-13 |
| 5 | 20261202 | local_300_5 | 500 | 7 | A | 5.2295940146793654e-11 | 2.5724700147833346e-11 | 5.387211020557134e-11 | 2.6180224654837048e-11 |
| 6 | 20261202 | local_300_5 | 2000 | 6 | A | 4.736717721417102e-12 | 2.503108831319878e-12 | 4.8777882695456435e-12 | 2.5167506967349595e-12 |
| 7 | 20261202 | local_300_5 | 200 | 9 | D | 0.5773490490311952 | 0.42356898602438653 | 0.5857298022642803 | 0.4271309187244885 |
| 8 | 20261202 | local_300_5 | 5000 | 5 | A | 2.3338894544481948e-12 | 1.2550550876344602e-12 | 2.4034342356515514e-12 | 1.2614403879090963e-12 |
| 9 | 20261203 | local_300_5 | 2000 | 10 | A | 5.46811188928858e-13 | 2.9504176879413535e-13 | 5.631578563679263e-13 | 2.963324030602621e-13 |
| 10 | 20261203 | local_300_5 | 5000 | 9 | A | 5.46811188928858e-13 | 2.9504176879413535e-13 | 5.631578563679263e-13 | 2.963324030602621e-13 |
| 11 | 20261203 | local_300_5 | 500 | 7 | A | 1.5859208620347615e-12 | 8.530121053951234e-13 | 1.6334125531810281e-12 | 8.612277557773535e-13 |
| 12 | 20261203 | local_300_5 | 200 | 12 | B | 0.0066700193726683165 | 0.003976480468663321 | 0.00682094510462332 | 0.004017341347448841 |
| 13 | 20261204 | local_300_5 | 5000 | 5 | A | 1.7499483860646784e-12 | 9.392521482798344e-13 | 1.8021896973015503e-12 | 9.4551493370898e-13 |
| 14 | 20261204 | local_300_5 | 200 | 10 | D | 0.09392664325614924 | 0.10548598389971264 | 0.0929282901070355 | 0.10352632734842115 |
| 15 | 20261204 | local_300_5 | 2000 | 5 | A | 1.7499447576042227e-12 | 9.392521482798344e-13 | 1.8021926011857284e-12 | 9.4551493370898e-13 |
| 16 | 20261204 | local_300_5 | 500 | 6 | A | 7.087257534430903e-11 | 3.576658413884104e-11 | 7.300097018667138e-11 | 3.633021661292674e-11 |
| 17 | 20261205 | local_300_5 | 200 | 6 | A | 3.1550186227231014e-12 | 1.707134433814872e-12 | 3.2503482694916217e-12 | 1.7174039967926547e-12 |
| 18 | 20261205 | local_300_5 | 500 | 6 | A | 2.2572091864788372e-12 | 1.219913059458122e-12 | 2.325072694000954e-12 | 1.228073198689129e-12 |
| 19 | 20261205 | local_300_5 | 5000 | 5 | A | 1.0970282175813636e-12 | 5.840189443162558e-13 | 1.1299589162220071e-12 | 5.954126081064734e-13 |
| 20 | 20261205 | local_300_5 | 2000 | 5 | A | 2.2572091864788372e-12 | 1.219913059458122e-12 | 2.325072694000954e-12 | 1.228073198689129e-12 |

### transfer-manjaro-001

| Zelle | Seed | Signal / Bedingung | Außen | Index | Klasse | RMS Training | Max Training | RMS Diagnose | Max Diagnose |
| ---: | ---: | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| 1 | 20261210 | anchor | 500 | 10 | D | 0.07290999064390653 | 0.06843973835452644 | 0.07303252446279813 | 0.06678998395381874 |
| 2 | 20261210 | frequency | 500 | 11 | C | 0.022421099508147458 | 0.02514371265890669 | 0.021716670756057585 | 0.024630416152414902 |
| 3 | 20261210 | decay | 500 | 11 | C | 0.02745118797988848 | 0.011247039667094616 | 0.028656508124732184 | 0.011322058594596507 |
| 4 | 20261210 | phase | 500 | 9 | A | 1.0608867760654603e-11 | 1.4310400087174246e-11 | 1.0642335606726655e-11 | 1.4303697115655434e-11 |
| 5 | 20261210 | amplitude | 500 | 9 | A | 1.1087020966781015e-12 | 8.153477892853798e-13 | 1.1236345582236383e-12 | 8.08686451137618e-13 |
| 6 | 20261210 | combined | 500 | 11 | A | 2.68833930294515e-11 | 3.912115076413595e-11 | 2.6040966773698423e-11 | 3.881239774102368e-11 |
| 7 | 20261211 | decay | 500 | 7 | A | 5.187188515705113e-12 | 2.810592036883719e-12 | 5.494370185018493e-12 | 2.8464453016852274e-12 |
| 8 | 20261211 | phase | 500 | 8 | A | 1.6520377380601242e-09 | 2.0752367463350296e-09 | 1.6599677168447133e-09 | 2.081919858731851e-09 |
| 9 | 20261211 | amplitude | 500 | 11 | B | 0.006923938873793328 | 0.0064102422765819345 | 0.00713405911606815 | 0.007003432825952505 |
| 10 | 20261211 | combined | 500 | 9 | A | 1.8471427765358967e-11 | 1.710531716270225e-11 | 1.856295732064314e-11 | 1.720545927952344e-11 |
| 11 | 20261211 | anchor | 500 | 9 | C | 0.017440372953693856 | 0.014731383635450578 | 0.017543284702701733 | 0.014095653499650003 |
| 12 | 20261211 | frequency | 500 | 10 | C | 0.0381715628369685 | 0.028783162457256158 | 0.038745060744289364 | 0.033578840086665764 |
| 13 | 20261212 | amplitude | 500 | 13 | C | 0.036942679597517646 | 0.044031978951399875 | 0.03633360771774242 | 0.04288969485106975 |
| 14 | 20261212 | combined | 500 | 14 | B | 0.0028697495115911874 | 0.0031985706801725424 | 0.0028014195478948305 | 0.003114292516252572 |
| 15 | 20261212 | anchor | 500 | 10 | D | 0.10188646952447318 | 0.09746257638959288 | 0.10198506407310036 | 0.09565393912571385 |
| 16 | 20261212 | frequency | 500 | 5 | A | 2.964182997057556e-12 | 1.5949463971764999e-12 | 3.0537646769006453e-12 | 1.6113221867897456e-12 |
| 17 | 20261212 | decay | 500 | 12 | B | 0.0074719144591342875 | 0.0037223612100434345 | 0.00776166745870147 | 0.0034534694771903972 |
| 18 | 20261212 | phase | 500 | 11 | D | 0.07256659184248325 | 0.0685320274099035 | 0.0723221453299417 | 0.06392705217480421 |

## Ausgabebindung und Grenzen

Separates lokales Ausgabeziel: `results/supplemental-assessment-all-001`.
Die Ausgabe liegt außerhalb aller historischen Ergebnisverzeichnisse.

| Artefakt | SHA-256 |
| --- | --- |
| `assessment_checksums.json` | `80b832f4c1fdf867e61a6ce6253664b08fca34cadee020c5c10b2c83ddb1e4b3` |
| `assessment_report.json` | `8f911cb7f3e30307acfa7af4b691dd1ce1862e1070d09d7bde4c80b2bf1a5e5a` |
| `assessment_records.json` | `287ad16ff545286593f1372ad6b6710c5091331d019e3f82f984a842fa1e6f2e` |

Alle 78 geplanten Fälle haben gültige Kurvenkennzahlen und bleiben in ihren
ursprünglichen Nennern (je fünf beziehungsweise drei). Es liegen keine fehlenden
Serien mehr vor. Die vollständigen Originalfronten bleiben in den unveränderten
Archiven erhalten; bewertet wird ausschließlich die damalige Auswahl.

Alle neuen Struktur-, Domain-, Fortsetzungs-, Restterm- und Parameterfelder
bleiben `not_assessed`. Neue PR-67-Originalergebnisse gehören nicht zu diesem Korpus.
Übergabe und weiterer Ablauf stehen im
[bestehenden Arbeitsdokument](representation_implementation_status.md).
**Nächste ausstehende Stufe ist Stufe 2:** exakte Strukturprüfung einschließlich
Originaldefinitionsbereich und stetiger Fortsetzung, erst nach bestätigter
Übernahme von Stufe 1 und Klärung der offenen methodischen Entscheidungen.

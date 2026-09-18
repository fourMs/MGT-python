# Aligning the four fourMs toolboxes with the group's toolbox list

Working note, 18 September 2026, for Alexander. Written from the workbook `Toolboxes To Python Project.xlsx` (Toolboxes, File Formats, Functionality and Usecases sheets) and from the documentation of the toolboxes in it, read the same day. The question was how musicalgestures, micromotion, ambiscape and musiscape can align with the rest of the list. The answer is that they already share the group's substrate, NumPy and pandas, and differ in three places the sheets care about: how a record carries time and events, how functions compose into pipelines, and what a test dataset is. Each of the three has a cheap fix.

## 1. What the list has in common

| Pattern in the list | Who does it | Where the four stand |
|---|---|---|
| One record object holding data, time and events together | Kinetics Toolkit `TimeSeries` (data, time, events, info; `to_dataframe`, `from_dataframe`); MNE `Raw` with annotations; MoCap Toolbox structs and `Mocapdata`; Respy on pandas | micromotion `MotionRecord` holds channels, sampling rate, unit and gaps, but no events and no absolute start time; ambiscape's session holds files on one clock with a datetime stamp in the filename; musicalgestures keeps most state in files |
| Node or pipeline composition with typed inputs and outputs | mopipe (load, preprocess, process, output; strong I/O type definitions); pixasonics (Feature, Mapper, Synth on an App) | musicalgestures chains methods on an object; micromotion and ambiscape are functions and CLI subcommands; nothing is typed as a node |
| Functional style over NumPy arrays | librosa (`load`, `stft`, `feature.*`) | micromotion and ambiscape are already this; musiscape builds on librosa |
| Explicit time handling, relative and absolute | The File Formats sheet has columns for relative time encoding and date-time encoding; Kinetics Toolkit and MNE carry both | Relative only in micromotion; absolute only by filename convention in ambiscape; musicalgestures reads what FFmpeg reports |
| Standard interchange formats | C3D (MoCap Toolbox, Kinetics Toolkit), BIDS (the neuro toolboxes), CSV and TSV everywhere | C3D only as a musicalgestures extra; no BIDS-like layout; TSV from Qualisys and CSV from sensors in micromotion |
| Real-time or streaming | PyEyesWeb (sliding window), pixasonics (SignalFlow) | None of the four is real-time; ambiscape streams long files in constant memory, which is a different thing |
| Reusable components named as such | The sheet's last column; librosa's four calls; mopipe's interfaces | The four have them (filters, readers, renderers) but the README does not list them under that heading |

## 2. What the group says it needs (Usecases sheet)

Python versions of the MIR and MoCap toolboxes; alignment across devices and verification of it; guidelines and a toolbox for FAIR storage; test datasets in different formats and end-to-end tests; contribution guidelines; a central point of communication; compatibility between audio and video tools. Four of these are already answered by the four toolboxes, and the group does not know it: device alignment (micromotion.align), recurrence and entropy (micromotion.dynamics, listed in the sheet only as pyrqa), the data chain with self-checks and DOIs (the Oslo Standstill Database as the worked example), and audio and video meeting at file boundaries with one implementation per measure.

## 3. Seven moves, cheapest first

1. **List the reusable components in each README** under that heading, in the sheet's words: readers, filters, renderers, the session model, the alignment function. Cost: an afternoon. It is the column the group reads first.
2. **Give `MotionRecord` events and a start time.** An `events` table (time, label) and an optional absolute `start_time`, plus `to_dataframe` and `from_dataframe` as Kinetics Toolkit has them. That makes the four answer both time columns of the File Formats sheet and lets a record travel to any pandas-based tool. Cost: one release of micromotion; the other three inherit it.
3. **Move the C3D reader into micromotion** and keep the musicalgestures extra as a pass-through, since micromotion owns motion series. Then the two motion-capture toolboxes in the list and the fourMs one read the same file.
4. **Write adapters, not ports.** `to_ktk` and `from_ktk` for Kinetics Toolkit's TimeSeries, `to_mne` for physiological channels, and a page showing a micromotion function wrapped as a mopipe node. The group's pipeline pattern is mopipe's; a wrapper costs less than a redesign and keeps the single-owner rule.
5. **Offer the synthetic generators as the group's test datasets.** micromotion's docs already draw their figures from synthetic signals whose answer is known, ambiscape has the same, and the deposited datasets carry self-checks. The Usecases sheet asks for exactly this and for end-to-end tests; the four have both.
6. **Publish the contribution template.** CI, tests, changelog, wiki, releases with a Zenodo DOI, `CITATION.cff` and the terminology charter, as the group's guideline. The sheet asks for guidelines and for validity for publication; this is the answer in the form of files.
7. **Say what the four do not do, in the README.** No real-time, no 3D animation, no joint angles or body-segment models, no BIDS. For those, point at PyEyesWeb, Kinetics Toolkit and the neuro toolboxes. A stated boundary reads as design; an unstated one reads as a gap.

## 4. What not to do

Do not turn the four into a node framework or a MoCap Toolbox port. The group's MATLAB users want Python equivalents of kinematics, joint angles and animation, and Kinetics Toolkit already has the geometry; micromotion's contribution is the band-limited measure and the sensor-agnostic record, which nothing else in the list has. Keep the four-toolbox split, since it is the one design decision in the list that answers the group's compatibility problem.

## 5. Vocabulary

The sheets say modality where the charter says data type. Leave the sheet's words alone in the sheet, and use the charter's in the READMEs and adapters; the adapter docstrings can say both once.

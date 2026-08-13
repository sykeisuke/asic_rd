# IRSX-like ASICプロトタイプ仕様書

版: 0.2（学生実習用基準仕様）

日付: 2026-08-13

プロセス基準: GF180MCU（`gf180mcuD`）

状態: 回路構成の基準仕様は凍結済み。MPW事業者に依存する項目は未確定。

言語: **日本語** | [English version](PROTOTYPE_SPECIFICATION.md)

## 1. この仕様書の役割

本書は、最初のテープアウトを目指す学生チームが共有する正式な管理仕様書である。
最高性能を追求することよりも、仕様作成、回路図、シミュレーション、レイアウト、
サインオフ、製造、測定までの一連の設計フローを、再現可能な形で実証することを
優先する。

実習の詳しい手順は[`lecture/README.md`](lecture/README.md)、現在の検証状況は
[`VERIFICATION_MATRIX.md`](VERIFICATION_MATRIX.md)、テープアウトまでの未完了項目は
[`TAPEOUT_BLOCKERS.md`](TAPEOUT_BLOCKERS.md)を参照する。

本書では要求を次のように分類する。

- **必須（Must）**: Tape-out 1に必要。満たせない場合は、仕様変更または明示的な免除承認が必要。
- **目標（Target）**: 設計上の目標。未達でも、原因と測定結果を残せばフロー実証は成立し得る。
- **発展（Stretch）**: 必須項目の完成を危険にしない場合だけ追加する。
- **実証済み（Demonstrated）**: 現在のリポジトリに再現可能なレイアウト前の証拠がある。
- **未確定（TBD）**: MPW、PDK、パッド、パッケージ、物理設計などの外部条件確定が必要。

## 2. Proposalとの関係

Proposalの長期目標は、1チャンネル、multi-GSa/s、約25 psの時間精度、500 MHzの
アナログ帯域、12-bit Wilkinson ADC、FPGA読み出しである。これらは研究計画全体の
目標であり、Tape-out 1の合否条件ではない。

Tape-out 1では、IRSXと同じ基本的な信号経路を、次の小規模仕様で実証する。

```text
アナログ入力 1チャンネル
→ sampling cell 4個
→ 4-to-1 analog MUX
→ 共有ramp + comparator
→ 6-bit counter capture
→ 6-bit register 4個
→ 24-bit同期serial readout
```

速度、分解能、storage depthは意図的に下げるが、sampling、hold、selection、
Wilkinson conversion、digital capture、readoutというIRSX-likeの信号経路は維持する。

## 3. Tape-out 1の成功定義

Tape-out 1では、次の工程を一度最後まで通すことを第一目的とする。

```text
仕様書
→ 回路図
→ レイアウト前シミュレーション
→ レイアウト
→ DRC / LVS
→ PEX / レイアウト後シミュレーション
→ アナログ・デジタル統合
→ pad ring / package / PCB
→ MPW事業者への提出
→ 初回シリコン測定
```

シリコン上で4-cell/6-bit動作を確認できた場合に加え、必要なテストモードを使って
故障箇所を明確に切り分けられた場合も、フロー実証としての成功に含める。12 bit、
1 GSa/s、500 MHzの達成はTape-out 1の必須条件ではない。

## 4. 凍結する回路構成

| 項目 | Tape-out 1の必須仕様 | 現在の基準 | 将来版 |
| --- | --- | --- | --- |
| プロセス | MPW事業者が認定したGF180MCU | `gf180mcuD` Open PDK | 事業者確定後に正確な版を凍結 |
| アナログチャンネル | 1 | 1 | 複数チャンネル |
| 保存段数 | 4 cells | 実証済み | 32-128 cells |
| Sampling switch | Transmission gate | NMOS/PMOS比較を実証済み | 信頼性確認後にbootstrapped switch |
| Hold capacitor | 各cellに1個 | 1 pFのシミュレーション基準 | レイアウト検討後にPDK素子を選択 |
| 読み出しMUX | 4-to-1 analog MUX | 順次読み出しを実証済み | Buffer追加、深いarray |
| ADC方式 | 共有Wilkinson方式 | Ramp/comparatorを実証済み | 並列化、calibration |
| ADC分解能 | 6 bit | 時刻からのcode生成を実証済み | 8-10 bit、その後12-bit研究 |
| Counter capture | 6-bit Gray-safe capture | RTLで実証済み | 高分解能化 |
| 結果保存 | 6-bit wordを4個 | 24-bit payloadを実証済み | 深いmemory |
| 読み出し | 低速同期CMOS serial | 実証済み | Frame付き高速link |
| Ramp | 内部rampと外部debug経路 | 内部rampのレイアウト前基準あり | 傾き可変、calibration対応 |
| Clock | 外部入力でboardから制御可能 | 20 MHz conversion基準 | 高速sampling timing generator |
| Test access | Block単位で切り分け可能 | 構成を定義済み | 最終pad割当は未確定 |

4 cells、6 bit、24-bit payload、clock domainの境界、アナログ・デジタル間interfaceは
教育用およびレイアウト前統合用の基準として凍結する。これらを変更する場合は、
仕様書の版を上げ、全回帰試験を更新する。

## 5. 機能要求

### 5.1 Samplingとhold

`SAMPLE[i]`が有効な間、transmission gateを通して`VIN`を`VHOLD[i]`へ接続する。
Switchを開いた後は、`CHOLD[i]`にsampled voltageを保持する。

必須要求:

- 4個のcellが、異なる入力値を意図した順番で保存する。
- 各cellに明示的なSAMPLE信号と相補switch制御を設ける。
- Acquisition error、edge disturbance、hold droopの測定方法を定義する。
- 選択されていないcellを意図せず上書きしない。

現在の4-cell nominal試験では、約0.5、0.8、1.1、1.4 Vを保存する。これらは回帰試験用の
入力値であり、シリコンの保証入力範囲ではない。

### 5.2 アナログ選択

One-hot制御のtransmission-gate MUXを使い、保持電圧を1個ずつ`MUX_BUS`へ接続する。

必須要求:

- 変換中に有効となる`SEL[i]`は最大1本とする。
- Cell間に、定義されたbus reset期間を設ける。
- Rampを開始する前にMUXのsettlingを完了させる。
- 読み出しによるhold capacitorの電圧変化を測定する。

### 5.3 Wilkinson変換

Rampをresetし、1個のcellを選択して6-bit counterを開始する。`VRAMP`が`MUX_BUS`と
交差したとき、comparatorがcapture eventを生成する。その時点のcountをADC codeとする。

```text
理想code = floor(交差までの時間 / conversion clock周期)
code範囲 = 0 ... 63
```

必須要求:

- 高い保持電圧ほど交差が遅くなり、codeが減少しない。
- Cell順序を失わずに4回の変換を完了する。
- Comparatorの極性とcapture規則を文書化する。
- 交差しない場合のtimeout動作を定義する。

現在のnominal統合試験のsignatureは`16, 20, 27, 35`である。これは回帰試験の期待値であり、
INL/DNLの保証ではない。

### 5.4 Digital captureとreadout

非同期のcomparator eventは、Gray-coded count captureを用いてdigital clock domainへ渡す。
Controllerは次の順番で4 cellを処理する。

```text
IDLE → RESET_RAMP → SELECT → CONVERT → CAPTURE → NEXT → DONE
```

必須要求:

- 4個の6-bit結果をcell順に保持する。
- 明示的な変更がない限り、24-bit payloadを`{cell3, cell2, cell1, cell0}`とする。
- Serialのbit順、使用clock edge、frame開始、data valid timingを文書化する。
- Resetとconversion timeoutにself-checking RTL testを設ける。
- Conversion clock境界付近での非同期captureを検証する。

## 6. 暫定的な電気仕様

MPW事業者が認定した電気的制限は、必ずこの表より優先する。

| 項目 | 必須 | 目標 | 発展 |
| --- | --- | --- | --- |
| アナログ入力 | 評価済みunipolar範囲で安全動作 | 0.4-1.6 V基準を検証 | Input bufferで範囲拡大 |
| Sampling rate | 外部から制御して機能確認可能 | 10-50 MSa/sを評価 | 100 MSa/s以上 |
| 入力帯域 | DCおよび低周波samplingを実証 | 10 MHz以上を測定 | 50 MHz以上 |
| ADC分解能 | 6-bit変換が機能 | 6-bit transferが単調 | 8-bit test mode |
| Conversion clock | 外部CMOS入力 | 20 MHz基準 | Timing確認後50 MHzまで |
| 変換時間 | Controller timeout以内 | 4-cell sequenceを完了 | Dead time短縮 |
| Core power | Analog/digitalを分離測定可能 | I/Oを除き50 mW未満 | Power mode追加 |
| Readout | 低速同期CMOS | FPGAと接続可能 | Frame付きserializer |

PVT、mismatch、PEX、package効果、測定不確かさを含めるまでは、表の数値をシリコン保証値と
して扱わない。

## 7. 必要な回路とテスト構造

### 7.1 アナログ回路

- Transmission-gate sampling cell 4個とhold capacitor。
- Bus resetを持つ4-to-1 analog MUX。
- Ramp generator、reset device、bias回路、ramp monitor。
- Comparatorとoutput buffer。
- 外部ramp注入またはbypass経路。
- 実装に必要なanalog biasと電源decoupling。

### 7.2 デジタル回路

- 6-bit counterとGray-coded asynchronous capture。
- 4-cell conversion controller。
- 6-bit result register 4個。
- 24-bit同期serial readout。
- Reset、test mode、timeout、status logic。

### 7.3 必須の観測手段

最終的なpad数の範囲内で、top levelには次を設ける。

- 少なくとも1個の`VHOLD`を直接またはbuffer経由で観測できる端子。
- 外部ramp入力と、内部rampのbuffered monitor。
- Comparator単体test modeとdigital output観測。
- Conversion clock入力と分周clockまたはstatus monitor。
- Analog crossingに依存しないcounter/digital test mode。
- 全capture codeへの直接またはserial access。
- Analog、digital、I/O電源電流を個別に測定できる接続。
- MOSまたはcapacitorのcharacterization用replicaを少なくとも1個。

テスト用の観測手段は、保存段数、分解能、serializer機能の追加より優先する。

## 8. 検証要求

### 8.1 レイアウト前アナログ検証

シリコンに含める各analog blockには、次を用意する。

- 読みやすいXschem回路図、または管理されたSPICE sourceと階層説明。
- 必要に応じたnominal DC、AC、transient test。
- 自動測定と再現可能な実行command。
- Process、supply、temperature corner test。
- Comparatorおよびmatchingが重要なdeviceのmismatch/Monte Carlo解析。
- Ideal model、transistor-level、統合testの明確な区別。

アナログ回帰試験は次で実行する。

```sh
make analog-regression
```

### 8.2 デジタル・mixed-signal検証

各RTL blockにself-checking simulation、選択したGF180 standard-cell libraryでのsynthesis、
timing analysisを用意する。SPICEで測定したcrossing timeを実際のcapture RTLへ渡し、
conversion clock境界付近も検証する。

```sh
make course-regression
```

### 8.3 物理検証

Tape-out前に、各analog macroとfull-chip topで次の順序を完了する。

```text
回路図シミュレーション
→ レイアウト
→ DRC
→ 抽出
→ LVS
→ PEXシミュレーション
```

LVS PASSは接続一致を示すが、アナログ性能を保証しない。PEX後にsampling error、hold
disturbance、ramp slope/linearity、comparator delay/offset、統合conversion codeを、
レイアウト前と同じ定義で再測定する。

### 8.4 Top-level signoff

- 認定済みpad/ESD libraryとreview済みpad ring。
- Analog/digital power domain、substrate方針、decouplingのreview。
- 必要に応じたfull-chip DRC、LVS、antenna、density/fill、ERC、provider check。
- Digital blockへのanalog macro LEF/GDS統合。
- 固定containerとPDK revisionを使ったclean checkoutからの再現性確認。
- Report、tool version、waiver、最終提出checksumの保存。

## 9. シリコン受入試験

次の項目を実証できた場合、またはtest modeによって故障箇所を明確に切り分けられた場合、
Tape-out 1をcomplete-flow実証として成功とする。

1. Package後のdieを安全にpower-upでき、analog/digital電源電流を測定できる。
2. Reset、control clock、status、serial communicationが動作する。
3. 少なくとも1 cellがDCまたは低周波入力をacquireしてholdできる。
4. 外部ramp経路でcomparator crossingを観測できる。
5. Counter captureがcodeを返し、serial readoutがbitを正しく保持する。
6. 複数入力点のtransfer curveを測定できる。
7. 4個のsampleを正しいcell addressへ対応づけられる。
8. 内部ramp動作を外部ramp基準と比較できる。
9. 測定結果、故障、calibration data、pre-silicon比較を公開する。

## 10. Tape-out 1で対象外とする項目

- Multi-GSa/s動作。
- 25 psの時間精度。
- 500 MHz analog bandwidthの実測保証。
- 8、10、12-bit ADC性能の保証。
- 32、128、512-cell array。
- 複数チャンネル統合。
- DLLでlockしたsampling timing。
- 製品品質のPMT amplifier/shaper。
- LVDSまたは高速serial I/O。
- Radiation qualificationまたは量産信頼性保証。

## 11. 設計凍結ゲート

### Gate A: 外部条件の凍結

- MPW事業者、run、提出日、die area、認定PDK revisionを確定する。
- Supply option、認定I/O cell、package/COB option、pad templateを確認する。
- Provider deliverableとopen-source公開条件を文書化する。

### Gate B: 回路図の凍結

- 凍結済み4-cell/6-bit構成が`make course-regression`に合格する。
- PVTとmismatch計画に合否基準がある。
- Top-level interface、test mode、clock、timeout、payload formatをreviewする。
- Area、power、pad budgetの初期見積りが成立する。

### Gate C: Block layoutの凍結

- Sampling/MUX、ramp、comparator、bias、digital blockがDRC/LVSに合格する。
- 抽出後の重要simulationが合格するか、差異にreview済みwaiverがある。
- Macro abstractとintegration pinを凍結する。

### Gate D: Full-chipの凍結

- Pad ring、power、analog/digital macro、test structure、fill、seal-ring制約を統合する。
- Full-chip signoffに合格する。
- ASIC pinout、package/bond map、PCB、FPGA interfaceが一致する。

### Gate E: Tape-out release

- Provider checklistとclean-clone buildに合格する。
- 最終GDS/OASIS、netlist、report、waiver、checksum、Git tagを保存する。
- Measurement planとboard bring-up時の安全制限を承認する。

## 12. 未確定の外部条件

内部構成は4 cells、6 bitで凍結済みである。残る未確定事項は、外部条件または物理設計に
依存する次の項目である。

1. MPW事業者、run date、slot、提出期限。
2. 認定されるGF180MCU PDK releaseとmetal stack。
3. 認定core/analog/I/O supplyとpad/ESD library。
4. Die area、pad数、pad pitch、seal ring、density/fill要求。
5. Package、chip-on-board、wire-bond carrierの選択。
6. Area、leakage、PEX検討後のcapacitor device/type/value。
7. PVT、mismatch、post-layout比較後のcomparator variant。
8. 外部・内部ramp電圧範囲とmonitor pad実装。
9. Silicon testにおけるsampling clockとconversion clockの正式上限。
10. Evaluation PCB、FPGA board、connector、I/O電圧とprotocol。

## 13. 仕様変更管理

本書はTape-out 1のscopeを管理する。Interface、cell数、ADC width、payload format、pad数、
supply domain、device reliability、または必須要求を変更する場合は、次を行う。

1. Versionと日付を更新する。
2. 変更理由と影響範囲を文書化する。
3. Test、verification matrix、Handbook、関連decision recordを更新する。
4. Merge前に全回帰試験を実行する。

Block内部のparameter調整は、interface、信頼性制限、必須動作を変えない場合に限り、
architecture revisionなしで進めてよい。

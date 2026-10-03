# 波形サンプリングASICプロトタイプ仕様書

版: 0.6-draft（管理基準仕様、2026-09-18 の回路構成改訂をレビュー中）

日付: 2026-09-18

プロセス基準: GF180MCU（`gf180mcuD`）

MPW事業者: **wafer.space GF180MCU Run 3**

提出基準日: clean GDS 2026-12-16 11:59 PM AoE（購入前に事業者へ再確認）

状態: MPW事業者、PDK commit、3.3 V library/supply基準、slot電源構成は凍結済み。**回路構成は 2026-09-18 に改訂**（共同研究先 IC 設計グループとの設計レビュー）: 4-to-1 analog MUX を廃止し、cell ごとに comparator を置いて 4 cell を並列変換する。hold capacitor は描ける最小の MIM（54.5 fF）。bottom-plate sampling とし、ramp は capacitor に印加して comparator は固定基準で判定する。ADC は 8 bit。RTL とそのテスト、最初のトランジスタレベル cell 検討は本改訂に従って更新済み。アナログ回路図・レイアウトは再導出中。
第2 core supply pairを追加した`0.5x1` COB ringは事業者platformのCoB precheckに合格
（2026-08-31）。事業者は書面認定を発行しないため、ESDは設計ルールで対応する。
**2026-10-02 に slot を `1x0.5` へ変更**（他は売り切れ、ADR 0004 addendum）: die 3.932 × 2.531 mm、analog pad 4 本、第 2 core pair は `bidir[45:44]`。購入締切 2026-12-09。

言語: **日本語** | [English version](PROTOTYPE_SPECIFICATION.md)

## 1. この仕様書の役割

本書は、最初のテープアウトを目指す上で共有する正式な管理仕様書である。
最高性能を追求することよりも、仕様作成、回路図、シミュレーション、レイアウト、
サインオフ、製造、測定までの一連の設計フローを、再現可能な形で実証することを
優先する。

実習の詳しい手順は
[`lecture/ASIC_Lab_Handbook_JP.md`](lecture/ASIC_Lab_Handbook_JP.md)、現在の検証状況は
[`VERIFICATION_MATRIX.md`](VERIFICATION_MATRIX.md)、テープアウトまでの未完了項目は
[`TAPEOUT_BLOCKERS.md`](TAPEOUT_BLOCKERS.md)を参照する。
MPW選定根拠と公開済みslot条件は
[`decisions/0004-wafer-space-run3.md`](decisions/0004-wafer-space-run3.md)に記録する。
Technology、library、supplyの凍結値と事業者への確認事項は
[`PDK_PAD_SUPPLY_FREEZE.md`](PDK_PAD_SUPPLY_FREEZE.md)で管理する。

本書では要求を次のように分類する。

- **必須（Must）**: Tape-out 1に必要。満たせない場合は、仕様変更または明示的な免除承認が必要。
- **目標（Target）**: 設計上の目標。未達でも、原因と測定結果を残せばフロー実証は成立し得る。
- **発展（Stretch）**: 必須項目の完成を危険にしない場合だけ追加する。
- **実証済み（Demonstrated）**: 現在のリポジトリに再現可能なレイアウト前の証拠がある。
- **未確定（TBD）**: MPW、PDK、パッド、パッケージ、物理設計などの外部条件確定が必要。

## 2. Proposalとの関係

Proposalで最初に実証するPoCは1チャンネルである。一方、IRSX相当を目指す研究の
長期到達点は、8チャンネル、multi-GSa/s、約25 psの時間精度、500 MHzのアナログ帯域、
12-bit Wilkinson ADC、FPGA読み出しである。これらの長期性能は、Tape-out 1の
合否条件ではない。

Tape-out 1では、IRSXと同じ基本的な信号経路を、次の小規模仕様で実証する。

```text
アナログ入力 1チャンネル
→ bottom-plate sampling cell 4個（各 54.5 fF MIM）
→ 共通 ramp 1本、cell ごとに comparator 1個（固定基準で判定）
→ 共有 8-bit Gray counter、4 並列 capture
→ 8-bit register 4個
→ 32-bit 同期 serial readout
```

速度、分解能、storage depthは意図的に下げるが、sampling、hold、selection、
波形sampling、Wilkinson conversion、digital capture、readoutという信号経路は維持する。

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
→ wafer.space GF180MCU Run 3へのclean GDS提出
→ 初回シリコン測定
```

シリコン上で4-cell/6-bit動作を確認できた場合に加え、必要なテストモードを使って
故障箇所を明確に切り分けられた場合も、フロー実証としての成功に含める。12 bit、
1 GSa/s、500 MHzの達成はTape-out 1の必須条件ではない。

## 4. 3段階の開発計画と回路構成

`[x]`は現在の正式な設計基準、`[ ]`は将来段階を示す。Tape-out 2と3の数値は、前段の
シリコン測定結果を受けて再凍結するため、現時点では研究目標である。

| 開発段階 | 現在選択 | 目的 | Channels | Cells/ch | ADC | Sampling目標 | 主な追加機能 |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| Tape-out 1 | [x] | Complete flowとtest accessの実証（スケール可能な cell 構成で） | 1 | 4 | 8 bit | 25 MSa/s基準 | 外部clock、内部/外部ramp、32-bit serial |
| Tape-out 2 | [ ] | 深いSCAとcalibrationの実証 | 1 | 32-128 | 8-10 bit | 100-500 MSa/s目標 | PVT/mismatch、cell calibration、高速timing |
| Tape-out 3 | [ ] | IRSX相当systemへの拡張 | 8 | cell 面積から決める（下記注） | 12 bit目標 | 1 GSa/s以上を目標 | 8-channel統合、500 MHz帯域、system calibration |

Tape-out 1で凍結する詳細構成は次の通りである。

| 項目 | 現在の基準 | 状態 |
| --- | --- | --- |
| MPW事業者 | wafer.space GF180MCU Run 3 | [x] |
| 提出予定 | Clean GDS 2026-12-16、parts shipment Q2 2027。購入前に再確認 | [x] 公開日程 / [ ] 再確認 |
| Provider template | commit `0de7e394337a1f7f5303ac7a3681bf2481b58176` | [x] |
| プロセス | `gf180mcuD`、PDK/Ciel commit `f6eeac7dad085ffcc829ccfd721f7b4ce39edcf7` | [x] |
| Analog device/supply | 3.3 V device、`AVDD=3.3 V`、`AVSS=0 V` | [x] |
| Digital cell/supply | `gf180mcu_as_sc_mcu7t3v3`、`DVDD_CORE=3.3 V` | [x] |
| Pad library/I/O supply | `gf180mcu_ocd_io`、`IOVDD=3.3 V`。事業者の書面認定は存在せず、platformの自動checkが判定基準 | [x] platform precheck合格 |
| ESD | 選択pad library内の構造のみ（`asig` padはDVDD/DVSSへのHBM diodeのみ、buffer無し）。Gate接続padには局所CDM二次保護（diode周長 > 25 um、直列poly R > 50 ohm）を追加。事業者からの特性データは提供されない | [x] 設計ルール |
| Slot/package | **`1x0.5`**（2026-10-02 改訂、下記 `0.5x1` の記述は旧）default pad ring + COB。`bidir[43:42]`位置を`AVDD`用の第2 core `vdd/vss` pairに変更 | [x] platform CoB precheck合格（2026-08-31） |
| 公開pad budget | 56 signal I/O（うちanalog 6）+ 16 power pads。Run 1のCOB pinoutは公開済み（run固有、Run 3版の改訂に注意） | [x] |
| Sampling switch | Bottom-plate sampling: 固定基準側の switch を先に開き、入力 transmission gate を後に開く（2026-09-18） | [x] |
| Hold capacitor | **54.5 fF MIM**（GF180 で描ける最小の MIM。Via4 規則まで満たす FuseTop は 27.2 µm²、抽出密度 2.007 fF/µm²）。2026-09-18 に MOS（`cap_nmos` はバイアス依存が大、蓄積型 `cap_nmos_03v3_b` は平坦だが活性領域を使う）と MOM（≈0.57 fF/µm²、M1–M4 を footprint 全体で占有）より優先して決定。理由は MIM が M4/M5 で **comparator の上に載り cell 面積を消費しない**こと。v0.5 の 1 pF は廃止した共有バス MUX の帰結だった | [x] |
| 読み出しMUX | **無し**（2026-09-18）。cell ごとに comparator を置き、ramp を全 cell に配って 4 変換を並列実行する（IRSX 型）。v0.5 の MUX ブロックはレガシー参考としてリポジトリに残す | [x] 廃止 |
| ADC方式 | Wilkinson: 共有 ramp と 8-bit Gray counter、cell ごとの comparator。**ramp は保持容量に印加**（comparator 入力ではない）: comparator は先に凍結された極板を見て固定基準で判定するため、同相依存が伝達関数に入らない | [x] |
| 入力電圧窓 | 幅 1.5 V、IRSX 相当の 0.5–2.0 V を作業仮定。3.3 V 電源では窓の**位置**はフロントエンドの基線で決まる自由変数。comparator 変種と同時に凍結 | [ ] target |
| Comparator 入力対 | 固定基準判定（2026-09-18）により「0.5–2.0 V 全域でのオフセット精度」要求は消え、被測定ノードが判定点へ向かって動く間に入力対が動作し続ける耐性だけが残る（5.3 節）。可動判定点を前提に選んだ PMOS 入力と ≈150 µm² / ≈50 µW のサイズは新仕様で再導出する（2.0 V 近傍の固定判定点なら NMOS 対が自然） | [ ] 再導出 |
| Counter capture | 共有 8-bit Gray counter と cell ごとの comparator-edge capture 4 系統、cell ごとの timeout flag | [x] |
| Result storage | 8-bit word 4個、合計 32 bit `{cell3, cell2, cell1, cell0}` | [x] |
| Readout | 低速同期CMOS serial | [x] |
| Ramp | 内部rampと外部debug/bypass経路 | [x] |
| Test access | Block単位で故障を切り分け可能 | [x]、最終pad割当はTBD |

4 cells、6 bit、24-bit payload、clock domainの境界、アナログ・デジタル間interfaceは
教育用およびレイアウト前統合用の基準として凍結する。これらを変更する場合は、
仕様書の版を上げ、全回帰試験を更新する。

## 5. 機能要求

### 5.1 Samplingとhold（bottom-plate sampling）

各 cell は 54.5 fF の `CHOLD[i]` を 2 つのノード `VTOP[i]`（入力側）と `VBOT[i]`（基準側）の間に持ち、switch は 3 個ある。

| 名前 | 種類 | 役割 |
| --- | --- | --- |
| `VIN` | Analog voltage | 4 cell へ共通に配る連続入力 |
| `SAMPLE[i]` / `SAMPLE_B[i]` | 相補 digital control | 入力 transmission gate `VIN` → `VTOP[i]` |
| `HOLD_REF[i]` | Digital control | `VBOT[i]` → `VREF`（固定電位）の switch。**`SAMPLE[i]` より先に開く** |
| `RAMP_CONNECT` | Digital control（全 cell 共通） | 変換中に `VTOP[i]` → `VRAMP` バスへ接続する switch |
| `VREF` | Analog 基準 | 基準極板の固定電位。comparator の判定基準でもある |
| `VRAMP` | Analog voltage | 全 cell 共通の ramp。0 V から開始 |

| 動作phase | `SAMPLE[i]` | `HOLD_REF[i]` | `RAMP_CONNECT` | 状態 |
| --- | --- | --- | --- | --- |
| Track | 1 | 1 | 0 | `VTOP[i]` は `VIN` を追従、`VBOT[i] = VREF` |
| Freeze | 1 | 0 | 0 | 基準側極板を先に開く: 電荷が凍結され、switch は常に `VREF` にあるので電荷注入は**信号非依存** |
| Hold | 0 | 0 | 0 | 入力 gate を開く: その信号依存の電荷注入は `VTOP[i]` に落ちるが、`VTOP[i]` は後で ramp に駆動し直されるため結果に入らない |
| Convert | 0 | 0 | 1 | `VTOP[i]` を `VRAMP` で駆動。`VBOT[i] = VREF − (VIN − VRAMP)·C/(C+Cp)` が `VREF` へ向かって上昇 |

どの極板を見るかが決定的である（トランジスタレベル検討 `make bottom-plate-cell`、2026-09-18）: 凍結した極板を comparator で見る構成では pedestal は −7.8 mV 一定（0.5–2.0 V での広がり 0.09 mV）、直線性 0.008 LSB、**ゲイン誤差 −0.02 %**（入力と ramp が同じ容量分割を通るため寄生容量が相殺）。逆に入力側極板を見る構成（ramp を基準側極板に印加）では 10–23 mV の信号依存 pedestal（2–4 LSB）と +9〜10 % の寄生ゲイン誤差が残り、cell ごとの校正が必要になる。物理的な MIM の上下極板はどちらを使ってもよいが、電気的には**先に開いた switch の側の極板を comparator が見る**こと。

必須要求:

- 4 個の cell が、異なる入力値を意図した順番で保存する。
- `HOLD_REF[i]` → `SAMPLE[i]` の順序（目標 1–3 ns）をチップ内で生成し、シミュレーションで観測できる。
- Acquisition error、pedestal（平均と入力依存性）、hold droop、寄生ゲインの測定方法を定義する。
- 選択されていない cell を意図せず上書きしない。

回帰試験の入力値は 0.5、0.8、1.1、1.4、1.7、2.0 V（作業入力窓）。シリコンの保証入力範囲ではない。

### 5.2 並列変換（v0.5 のアナログ選択を置き換え）

Analog MUX は無い。最後の cell を hold した後、controller は全 `VTOP[i]` を `VRAMP`（0 V に保持）へ接続し、整定を待って ramp を解放し共有 counter を開始する。各 comparator i は `VBOT[i]` が `VREF` に達したとき（`VRAMP ≈ VIN_i` のとき）に判定する。4 変換は同時に進み、1 本の ramp で完了する。

- `RAMP_CONNECT` は全 cell 共通。cell 選択信号は存在しない。
- 接続と ramp 解放の間に定義された整定期間を置く。
- Ramp バスの負荷は接続 cell の合計（Tape-out 1 で 4 × (54.5 fF + Cp)）。ramp generator 仕様にこの負荷と Tape-out 3 でのスケーリングを含める。

### 5.3 Wilkinson変換

```text
理想code = floor((t_cross − t_ramp_start) / conversion clock周期)
code範囲 = 0 ... 255。交差しない cell は 255 を返し timeout[i] = 1
```

- 高い保持電圧ほど交差が遅くなり、code が減少しない。
- 全 comparator は固定基準 `VREF`（名目 2.0 V）で判定する。したがってオフセットは cell ごとの定数（pedestal）であり、入力レベルの関数ではない。変換中、被測定ノードは `VREF − VIN·C/(C+Cp)`（2.0 V sample で約 0.15 V）から `VREF` まで動く。comparator はこの範囲で「動作し続ける」ことが要求され、「精度」は判定点でのみ要求される。
- Comparator の極性と capture 規則を文書化する。
- 交差しない場合の timeout 動作を定義する。

デジタル経路の回帰 signature は並列の `16, 20, 27, 200`（v0.5 の順次 `16, 20, 27, 35` を置き換え）。回帰試験の期待値であり、INL/DNL の保証ではない。

### 5.4 Digital captureとreadout

Controller の順序:

```text
IDLE（acquire）→ CONNECT → CONVERT → [overflow 時 DRAIN] → DONE
```

- 共有 8-bit binary counter を Gray 符号化し、各 cell は自身の comparator 立下がりで Gray word を capture（局所 capture clock）。toggle synchronizer で conversion clock domain へ戻す。
- 4 個の 8-bit 結果を cell 順に保持し、cell ごとの `timeout` flag を添える。
- 明示的な変更がない限り、32-bit payload を `{cell3, cell2, cell1, cell0}` とする。
- Serial の bit 順（LSB first）、使用 clock edge、frame 開始、data valid timing を文書化する。
- Reset、timeout、同時 capture、最終 count での capture に self-checking test を設ける（`make parallel-controller`、`make digital-top`）。

### 5.5 Sampling timingとconversion timing

Testbench では `SAMPLE0..3` の開始を 10、50、90、130 ns とし、40 ns 間隔は 25 MSa/s に相当する（2026-09-18 のレビューでは 50 MSa/s も議論され、Tape-out 1 では基板側で制御するパラメータのまま）。各 cell 内では基準側 switch が入力 gate より 1–3 ns 先に開く。

Conversion clock は独立したパラメータ。20 MHz 基準で `TCOUNT = 50 ns`、4 cell の並列 8-bit 変換は 256 count = 12.8 µs に接続・整定のオーバーヘッドを加えた時間で完了する。Tape-out 1 は短い 4 sample 記録を取得後に変換する構成であり、dead-time-free の連続サンプラではない。

![Tape-out 1のsamplingとconversion timing](lecture/assets/tapeout1_sampling_conversion_timing.png)

*図1（v0.5 版、書き直し予定）: sampling schedule は不変。conversion は 4 回の順次 2.9 µs slot ではなく 1 本の並列 12.8 µs ramp になった。*

## 6. 開発段階ごとの暫定電気仕様

回路構成と電気仕様は同じTape-out段階に対応させる。MPW事業者が認定した電気的制限は、
必ずこの表より優先する。

| 項目 | Tape-out 1 [x] | Tape-out 2 [ ] | Tape-out 3 [ ] |
| --- | --- | --- | --- |
| Channels | 1 | 1 | 8 |
| Cells/channel | 4 | 32-128 | 128以上を候補 |
| Sampling interval | 40 ns基準 | 2-10 ns目標 | 1 ns以下を目標 |
| Sampling rate | 25 MSa/s基準 | 100-500 MSa/s目標 | 1 GSa/s以上を目標 |
| Record window | 最初から最後まで120 ns、4 sample depthとして160 ns相当 | Cell数とrateで決定 | Cell数とrateで決定 |
| Analog input | 0.5-2.0 V 作業窓（IRSX 相当） | 前段測定後に再設定 | Front-endを含め再設定 |
| Analog bandwidth | DC/低周波を必須、10 MHzを測定目標 | 50-200 MHz目標 | 500 MHz目標 |
| ADC | 8-bit Wilkinson、cell ごとの comparator | 8-10 bit Wilkinson | 12-bit Wilkinson目標 |
| Conversion clock | 20 MHz基準、samplingと独立 | 20-100 MHz候補 | Architectureと並列度を再設計 |
| Conversion/readout | 4 cell を並列に 1 本の 12.8 µs ramp で変換 | 深いarrayに対応した並列化を検討 | 8-channel throughputへ対応 |
| Power | Analog/digitalを分離測定、I/O除き50 mW未満を目標 | 測定結果からbudget化 | System power budgetを設定 |
| Calibration | Pedestal/transfer測定 | Cellごとのtime/voltage calibration | 8-channel system calibration |

PVT、mismatch、PEX、package効果、測定不確かさを含めるまでは、表の数値をシリコン保証値と
して扱わない。

## 7. 必要な回路とテスト構造

### 7.1 アナログ回路

- Bottom-plate sampling cell 4 個: 入力 transmission gate、チップ内遅延で先に開く基準側 switch、54.5 fF MIM、ramp 接続 switch。
- Comparator 4 個（固定基準判定）と output buffer。
- 接続 cell を駆動する ramp generator、reset device、bias 回路、ramp monitor。
- `VREF` 生成/decoupling または外部 `VREF` pad。
- 外部ramp注入またはbypass経路。
- 実装に必要なanalog biasと電源decoupling。

### 7.2 デジタル回路

- 共有 8-bit counter と Gray-coded asynchronous capture 4 系統。
- 並列 conversion controller（acquire / connect / convert / drain）。
- 8-bit result register 4 個と cell ごとの timeout flag。
- 32-bit 同期 serial readout。
- Reset、test mode、timeout、status logic。

### 7.3 必須の観測手段

最終的なpad数の範囲内で、top levelには次を設ける。

- 少なくとも1個の`VHOLD`を直接またはbuffer経由で観測できる端子。
- 外部ramp入力と、内部rampのbuffered monitor。
- Comparator単体test modeとdigital output観測。
- Conversion clock入力と分周clockまたはstatus monitor。
- Analog crossingに依存しないcounter/digital test mode。
- 全capture codeへの直接またはserial access。
- VDD側でanalog core（`AVDD`）、digital core、I/O電源電流を個別に測定できる接続。
  default COB breakoutでは全groundが共通のため、ground電流は分離できない。
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

電源投入順序、停止条件、block別測定、4-cell統合測定、ADC/速度/帯域評価の詳細は
[`SILICON_TEST_PROCEDURE_JP.md`](SILICON_TEST_PROCEDURE_JP.md)に従う。

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
- IRSX相当の8チャンネル統合。
- DLLでlockしたsampling timing。
- 製品品質のPMT amplifier/shaper。
- LVDSまたは高速serial I/O。
- Radiation qualificationまたは量産信頼性保証。

## 11. 設計凍結ゲート

### Gate A: 外部条件の凍結

- MPW事業者、run、提出日、die area、PDK revisionを確定する。
- Supply option、I/O cell、package/COB option、pad templateを確認する。事業者は
  書面認定を発行しないため、platform.wafer.spaceの自動precheck/CoB checkが判定基準
  （[`PDK_PAD_SUPPLY_FREEZE.md`](PDK_PAD_SUPPLY_FREEZE.md)参照）。
- Provider deliverableとopen-source公開条件を文書化する。
- 技術項目は2026-08-31に完了。slot購入でgateを閉じる。

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

2026-08-31に解決済み（詳細は[`PDK_PAD_SUPPLY_FREEZE.md`](PDK_PAD_SUPPLY_FREEZE.md)）:
`0.5x1` default pad ring + COB slotを凍結。PDK/template commitは公開templateの
pinと一致。3.3 V libraryとI/O cellはplatform precheckに合格（書面認定は存在しない）。
Analog padのESDは設計ルールで対応。`AVDD`は第2 core supply pairで分離し、
groundは全て共通。PackageはCOB。

1. Run 3 の `1x0.5` slot を購入する（COB 込み $6,500、購入締切 2026-12-09）。購入時と
   提出前にPDK/template pinを再確認する。
2. 入力電圧窓の位置（幅 1.5 V）と comparator 入力対の変種を、広窓掃引データに基づき同時に決定。その後、選択変種の PVT/mismatch/post-layout 確認。
3. スケーリング経路のための小容量テスト構造（50 fF MIM、~15 fF MOM/MOS）。パッド・面積予算が許す場合。
4. 外部・内部ramp電圧範囲とmonitor pad実装。
5. Silicon testにおけるsampling clockとconversion clockの正式上限。
6. Evaluation PCB（事業者COB mezzanineに接続）、FPGA board、connector、
   I/O電圧とprotocol。

## 13. 仕様変更管理

本書はTape-out 1のscopeを管理する。Interface、cell数、ADC width、payload format、pad数、
supply domain、device reliability、または必須要求を変更する場合は、次を行う。

1. Versionと日付を更新する。
2. 変更理由と影響範囲を文書化する。
3. Test、verification matrix、Handbook、関連decision recordを更新する。
4. Merge前に全回帰試験を実行する。

Block内部のparameter調整は、interface、信頼性制限、必須動作を変えない場合に限り、
architecture revisionなしで進めてよい。

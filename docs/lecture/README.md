<img src="assets/image1.png" style="width:6.5in;height:2.74444in" />

*図1　本プロトタイプの信号経路。青はアナログ、緑はデジタル領域。*

Version 1.0 \| 2026-08-11

Repository: github.com/sykeisuke/asic\_rd

# このハンドブックの目的

この教材のゴールは、最高性能のASICを一度で作ることではありません。仕様、回路図、SPICE、RTL、協調検証、配置配線、サインオフ、GDSIIという一連の流れを、誰でも再現できる形で通すことです。学生はGitHubの設計ファイルを読み、同じコマンドで結果を再生成し、次の設計判断を説明できる状態を目指します。

|                                                                                                                                |
|--------------------------------------------------------------------------------------------------------------------------------|
| **最重要原則** 結果のスクリーンショットだけを信用しない。入力ファイル、実行コマンド、生成物、合否基準の4点を常に対応づけます。 |

## 学習成果

-   GF180 PDKを使ったMOS特性と基本アナログ回路を説明できる。

-   サンプル・ホールド、ランプ、コンパレータからWilkinson
    ADCの変換原理を説明できる。

-   SPICEイベントをRTLへ渡す境界と、Gray
    codeを用いたCDC対策を説明できる。

-   RTL-to-GDSフローの各成果物とDRC/LVS/STAの意味を説明できる。

-   prototypeとtape-out-ready
    designの違いを、未解決項目を含めて説明できる。

## 推奨の進め方

| **段階**     | **Lab** | **成果**                             |
|--------------|---------|--------------------------------------|
| 基礎         | 0–2     | 環境、PDK、MOS、sampling             |
| 変換器       | 3–5     | comparator、ramp、1/4-cell Wilkinson |
| デジタル     | 6–8     | controller、co-sim、CDC、serial      |
| 物理実装     | 9       | netlistからGDSII                     |
| 設計レビュー | 10      | 証拠、blocker、次版仕様              |

# 1. 全体設計フロー

<img src="assets/image2.png" style="width:6.5in;height:3.44118in" />

*図2　仕様からGDSIIまで。各矢印が検証可能であることがcomplete
flowの条件。*

## ブロックの役割

| **ブロック**         | **入力 → 出力**           | **このprototypeで確認すること**      |
|----------------------|---------------------------|--------------------------------------|
| Sampling cell        | VIN + SAMPLE → VHOLD      | 4つの異なる電圧を保持できる          |
| Analog MUX           | VHOLD\[3:0\] + SEL → VMUX | 選択セルだけを共有ADCへ接続する      |
| Ramp                 | START → VRAMP             | 単調な電圧-時間変換を作る            |
| Comparator           | VMUX, VRAMP → HIT         | 交差時刻をデジタルイベントへ変換する |
| Gray counter/capture | CLK, HIT → CODE\[5:0\]    | 境界付近でも多bit同時遷移を避ける    |
| Serializer           | CODE x4 → DATA            | 少ないpad数でFPGAへ読み出す          |

|                                                                                                                                           |
|-------------------------------------------------------------------------------------------------------------------------------------------|
| **今回の仕様** 4 storage cells、6-bit変換、共有ramp/comparator、24-bit serial readout。速度・分解能・帯域よりもflowの完結性を優先します。 |

# Lab 0 リポジトリを読む

|                                                                         |
|-------------------------------------------------------------------------|
| **到達目標** 設計ソースと生成物を区別し、再現コマンドを自分で見つける。 |

git clone https://github.com/sykeisuke/asic\_rd.git  
cd asic\_rd  
git status  
make check

## 最初に読む5ファイル

| **ファイル**                     | **読む理由**                           |
|----------------------------------|----------------------------------------|
| README.md                        | 入口、クイックスタート、全体構成       |
| docs/PROTOTYPE\_SPECIFICATION.md | 何を作るか、数値仕様、success criteria |
| docs/TOP\_LEVEL\_INTERFACE.md    | アナログ/デジタル境界とI/O             |
| docs/VERIFICATION\_MATRIX.md     | 要求とtestの対応                       |
| docs/TAPEOUT\_BLOCKERS.md        | prototype後に残る実装リスク            |

## ディレクトリの見方

-   simulations/: Xschem/ngspice用のアナログtestbenchと結果。

-   digital/: synthesizable RTL、testbench、physical design設定。

-   docs/: 仕様、判断記録、検証表。

-   work/ や runs/: 再生成できる中間成果物。設計のsource of
    truthと混同しない。

## 確認問題

-   現在のHEAD commitを記録し、実験ノートに貼る。

-   VERIFICATION\_MATRIXの1行を選び、要求、test、artifact、判定を説明する。

# 2. Mac + Docker開発環境

Macはホストとして十分に使えます。Linux向けEDAツールとGF180
PDKはDockerコンテナ内へ固定し、XschemなどGUIはブラウザVNCから操作します。これにより学生ごとのmacOS差を小さくします。

1.  Docker
    Desktopを起動し、メイン画面でEngineがRunningであることを確認する。

2.  リポジトリで make vnc を実行する。

3.  ブラウザで http://localhost:8080/?password=abc123 を開く。

4.  File Managerから
    /foss/designs/simulations/gf180\_nmos\_dc/nmos\_dc.sch を開く。

cd /Users/ykeisuke/Desktop/mywork/asic\_rd  
make vnc  
\# Browser: http://localhost:8080/?password=abc123

## アカウントは必要か

通常のローカルimage実行にDocker
Hubアカウントは必須ではありません。ただしprivate image、rate
limit回避、組織管理を使う場合はログインが必要です。授業では使用imageのdigestまたはtagを固定します。

## よくあるトラブル

| **症状**                 | **確認**                                             |
|--------------------------|------------------------------------------------------|
| localhost:8080が開かない | docker ps、make vncのログ、port競合                  |
| XschemにPDK symbolがない | PDK\_ROOTとコンテナ内mount                           |
| ファイル変更が見えない   | host pathと/foss/designsの対応                       |
| com.docker.vmnetd警告    | Docker公式最新版、残存helper、macOS Gatekeeperを確認 |

|                                                                                                                                         |
|-----------------------------------------------------------------------------------------------------------------------------------------|
| **安全上の注意** Gatekeeperを恒久的に無効化しない。Docker公式配布物を使い、異常が続く場合は再インストールとhelper cleanupを優先します。 |

# Lab 1 GF180 MOSを測る

|                                                                        |
|------------------------------------------------------------------------|
| **到達目標** NMOSのI–V曲線を再生成し、回路設計に使うbias領域を読める。 |

make nmos-dc

5.  nmos\_dc.schを開き、device名、W/L、body接続、supplyを確認する。

6.  testbenchのVGS/VDS sweep範囲を読む。

7.  make nmos-dcを実行し、CSV/plotの生成時刻を確認する。

8.  同じVGSでVDSを上げたとき、linear領域からsaturation領域へ移る形を説明する。

## 成功判定

□ ngspiceがerrorなしで終了する。

□ simulations/gf180\_nmos\_dc/work/nmos\_id\_vds.csv が更新される。

□ 電流の符号、単位、sweep軸を説明できる。

## 設計者の問い

モデルが動くことと、回路が正しいことは別です。温度、process
corner、電源範囲、device optionがMPW
providerの許容条件に一致しているかを必ず後段で確認します。

|                                                                                                    |
|----------------------------------------------------------------------------------------------------|
| **演習** Wを2倍にしたvariantを作り、同じbiasでIdがどう変化するか予測してからsimulationで確認する。 |

# Lab 2 Sampling cell

|                                                                                       |
|---------------------------------------------------------------------------------------|
| **到達目標** track/hold動作、acquisition、droop、charge injectionを波形から評価する。 |

make sampling-cell  
make four-cell  
make four-cell-mux

## 観測順序

9.  SAMPLE high中にVHOLDがVINへ追従することを確認する。

10. SAMPLE edge直後のstepを測り、charge
    injection/feedthroughを区別する。

11. hold期間の傾きを測り、droop rate \[V/s\]へ換算する。

12. 4-cell testで各cellが異なる時刻の電圧を保持することを確認する。

13. MUX選択を変え、非選択cellの値が破壊されないことを確認する。

| **Cell** | **保持電圧 \[V\]** | **目標 \[V\]** | **誤差 \[mV\]** |
|----------|--------------------|----------------|-----------------|
| 0        | 0.490799           | 0.500          | 9.201           |
| 1        | 0.792128           | 0.800          | 7.872           |
| 2        | 1.094365           | 1.100          | 5.635           |
| 3        | 1.399222           | 1.400          | 0.778           |

|                                                                                                      |
|------------------------------------------------------------------------------------------------------|
| **読み方** この値はprototype testbenchでのnominal結果です。PVT/Monte Carlo後の保証値ではありません。 |

## 失敗時の切り分け

-   全cellが同じ値：sampling pulseの位相またはnode namingを確認。

-   MUX busが浮く：SEL decodeとtransmission gateのcomplementary
    controlを確認。

-   保持値が急減：capacitance、leakage path、simulation timestepを確認。

# Lab 3 Comparatorとramp

|                                                                      |
|----------------------------------------------------------------------|
| **到達目標** 入力電圧を交差時刻へ変換し、ADCの主要誤差源を説明する。 |

make comparator  
make comparator-range  
make comparator-offset  
make ramp-generator

Wilkinson変換では、一定傾斜のrampが保持電圧へ到達した瞬間にcounter値をcaptureします。理想的には
t\_cross = (V\_hold − V\_start) / slope です。したがってramp
slope、offset、delay、noiseがcodeへ直接写ります。

## 測るもの

| **Test**   | **測定量**              | **設計への意味**         |
|------------|-------------------------|--------------------------|
| comparator | logic swing、delay      | デジタル側が認識できるか |
| range      | common-mode/input range | 変換可能なanalog範囲     |
| offset     | input-referred offset   | code bias、校正必要性    |
| ramp       | slope、linearity、reset | LSB幅とconversion time   |

## 6-bitの基準

入力範囲をVFSとすると理想LSBは VFS/64 です。1.6 V範囲なら25
mV/LSBです。prototypeではまずcode
orderingとmonotonicityを確認し、INL/DNLの保証は後続版へ分離します。

|                                                                                          |
|------------------------------------------------------------------------------------------|
| **演習** ramp slopeを±10%変え、同じ入力のcrossing timeとcodeがどれだけ変わるか表にする。 |

# Lab 4 1-cell Wilkinson slice

|                                                                                   |
|-----------------------------------------------------------------------------------|
| **到達目標** sampling、ramp、comparator、counterの因果関係を1つの波形で説明する。 |

make wilkinson-slice  
make transfer

14. sampling phaseでinputをhold capacitorへ保存する。

15. conversion startでramp resetを解除し、counterを開始する。

16. VRAMPがVHOLDへ到達するとcomparator edgeが発生する。

17. edge時のcounterをcaptureし、end-of-conversionまで保持する。

18. input sweepからcode transferを作り、単調性を確認する。

## 合否基準

□ 低い入力ほど早く交差し、小さいcodeになる。

□ inputを増やしてもcodeが逆戻りしない。

□ 0–63の範囲外へ出ない。

□ 飽和点とdead regionを波形上で説明できる。

|                                                                                                                                                         |
|---------------------------------------------------------------------------------------------------------------------------------------------------------|
| **注意** transient波形が自然に見えても、capture条件が1 timestep依存なら脆弱です。max timestepを変えた再実行でcodeが不合理に変化しないことを確認します。 |

# Lab 5 4-cell shared conversion

|                                                                        |
|------------------------------------------------------------------------|
| **到達目標** 4つの保持値を1つのramp/comparatorで順次6-bit code化する。 |

make four-cell-wilkinson

<img src="assets/image3.png" style="width:6.45in;height:3.49059in" />

*図3　4-cell shared Wilkinson conversion。上段は保持値とMUX
bus、下段はrampとcomparator。*

| **Cell** | **MUX電圧 \[V\]** | **交差時刻 \[µs\]** | **6-bit code** |
|----------|-------------------|---------------------|----------------|
| 0        | 0.456612          | 0.831984            | 16             |
| 1        | 0.734986          | 1.040260            | 20             |
| 2        | 1.014740          | 1.399500            | 27             |
| 3        | 1.296100          | 1.771850            | 35             |

codeは保持値の順序に従って16 &lt; 20 &lt; 27 &lt;
35となっています。この段階の成功は、絶対精度よりもsample → select →
compare → captureの順序とデータ対応が崩れていないことです。

|                                                                                                                |
|----------------------------------------------------------------------------------------------------------------|
| **レビュー観点** MUX切替直後のsettling時間を十分取っているか。前cellの残留値が次のcrossingへ影響していないか。 |

# Lab 6 Controller RTL

|                                                                    |
|--------------------------------------------------------------------|
| **到達目標** 4-cell変換のsequencingを合成可能なRTLとして検証する。 |

make counter  
make gray-counter  
make controller  
make digital-top

## 状態遷移を言葉で書く

19. IDLE: startを待ち、各valid flagをclearする。

20. RESET\_RAMP: rampとcounterを既知状態へ戻す。

21. SELECT: 対象cellをMUXへ接続しsettlingを待つ。

22. CONVERT: Gray counterを進め、comparator hitを待つ。

23. CAPTURE: codeを対象registerへ保存する。

24. NEXT/DONE: 4 cell完了後にserializerへ引き渡す。

## RTL testで見るもの

-   reset直後にXが残らない。

-   cell selectがone-hotまたは仕様どおりのbinaryである。

-   captureは各cellにつき一度だけ発生する。

-   timeout時にもstate machineが停止し続けない。

-   doneとdata\_validのpulse/level仕様がtestbenchと一致する。

|                                                                                                                                  |
|----------------------------------------------------------------------------------------------------------------------------------|
| **設計ルール** simulation専用delay、initial依存、real型をsynthesizable coreへ持ち込まない。analogモデルはtestbench側へ置きます。 |

# Lab 7 SPICE-to-RTL協調検証

|                                                                                     |
|-------------------------------------------------------------------------------------|
| **到達目標** アナログ交差時刻をデジタルtestbenchへ渡し、end-to-end codeを照合する。 |

make four-cell-cosim

このプロジェクトの協調検証は、SPICEが生成したcrossing eventを抽出し、RTL
testbenchへ刺激として与える方式です。アナログsimulatorとRTL
simulatorを同時結合する重いAMS環境を使わず、境界条件を明示できます。

## 境界contract

| **項目**            | **固定すべき内容**                    |
|---------------------|---------------------------------------|
| time unit           | 秒、ns、psの変換規則                  |
| edge polarity       | rising/fallingのどちらがhitか         |
| sampling convention | edge直前/直後のcounterをcaptureするか |
| code format         | binary/Gray、bit order、width         |
| invalid case        | 未交差、timeout、saturationの表現     |

## debugの順番

25. SPICE CSVに交差が存在するか。

26. event抽出値の単位が正しいか。

27. testbenchで同時刻にpulseが生成されたか。

28. capture registerのenableが立ったか。

29. expected codeとの±1境界差か、根本的なsequence差か。

# Lab 8 Gray captureとCDC

|                                                                                     |
|-------------------------------------------------------------------------------------|
| **到達目標** comparator edgeがcounter clock境界へ近づく現実的な不確かさを検証する。 |

make phase-sweep

<img src="assets/image4.png" style="width:6.2in;height:2.68667in" />

*図4　cell 2のphase sweep。+500 ps付近でcodeが27から28へ変わる。*

binary
counterは例として011111→100000のように複数bitが同時に変化します。非同期edgeがその途中をcaptureすると存在しないcodeになり得ます。Gray
counterは隣接code間で1
bitだけ変化するため、境界付近の不確かさを原則として隣接codeへ閉じ込めます。

## この結果の解釈

-   +400 psでは27、+600 psでは28。境界で±1
    codeとなることは量子化として自然。

-   +500 psはcell 2のboundary。これはsetup/hold保証を意味しない。

-   siliconではmetastability、clock skew、comparator
    delay分布も評価が必要。

|                                                                                                                                             |
|---------------------------------------------------------------------------------------------------------------------------------------------|
| **判断記録** 設計理由は docs/decisions/0003-gray-comparator-capture.md に残しています。コードだけでなく、なぜその方式を選んだかを読むこと。 |

# 3. 24-bit serial readout

4個の6-bit codeを24-bit
wordへまとめ、FPGAへserial転送します。pad数を抑えられる一方、bit
order、frame境界、clock domain、idle
levelを仕様として固定する必要があります。

make digital-top

| **Field** | **仕様確認**                       |
|-----------|------------------------------------|
| Payload   | code0, code1, code2, code3の連結順 |
| Bit order | MSB-firstまたはLSB-first           |
| Handshake | valid/ready、busy、done            |
| Clock     | ASIC生成かFPGA供給か               |
| Reset     | 途中reset時のline状態              |

## logic analyzerでの受入試験

30. 既知code 16, 20, 27, 35をloadする。

31. serial clockとdataを同時取得する。

32. 24 edge分をdecodeし、元の4 codeへ戻す。

33. frameを連続送信し、境界でbit slipがないことを確認する。

|                                                                                                                                                                                              |
|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **PCBへつながる仕様** I/O voltage、drive strength、level shifting、ground reference、connector pinoutはpad libraryと評価PCBの制約に依存します。prototype RTLの論理仕様だけでは確定しません。 |

# Lab 9 RTL-to-GDS

|                                                                                    |
|------------------------------------------------------------------------------------|
| **到達目標** 合成、floorplan、placement、CTS、routing、signoffの成果物を確認する。 |

make digital-physical

<img src="assets/image5.png" style="width:5.3in;height:5.7399in" />

*図5　GF180 standard-cell flowで生成したデジタルtopの最終レイアウト。*

| **Metric**        | **結果**              |
|-------------------|-----------------------|
| Core/die size     | 215.49 × 233.41 µm    |
| Die area          | 50,297.5 µm²          |
| Utilization       | 39.5%                 |
| Standard cells    | 798（sequential 101） |
| Total wire / vias | 14,792 µm / 2,784     |
| Estimated power   | 6.13 mW               |

成果物は digital/asic\_digital\_top/physical/final\_views/
以下にあります。GDS、DEF、LEF、gate-level
netlist、metricsを相互に対応づけます。

# 4. Signoff結果の読み方

| **Check**         | **今回の結果** | **意味**                            |
|-------------------|----------------|-------------------------------------|
| DRC               | 0 violations   | 実行deck上のlayout ruleに違反なし   |
| Antenna           | 0 violations   | 報告対象のantenna rule違反なし      |
| LVS               | 0 violations   | layoutと参照netlistの接続一致       |
| Setup             | 0 violations   | 解析cornerでsetup requirementを満足 |
| Hold              | 0 violations   | 解析cornerでhold requirementを満足  |
| Worst setup slack | 39.21 ns       | 現在のclock constraintに大きな余裕  |
| Worst hold slack  | 0.336 ns       | 最小hold余裕                        |

|                                                                                                                                                                 |
|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **重要** 0 violationsは『チップ全体がtape-out ready』を意味しません。今回の結果はデジタルブロック、使用したlibrary/view、設定したconstraintの範囲で成立します。 |

## 証拠を確認する

-   metrics.json/csv: 数値結果。

-   asic\_digital\_top.gds: foundryへ渡す形状データ候補。

-   asic\_digital\_top.nl.v: 物理実装後のgate-level netlist。

-   resolved.json: 実際に解決されたflow設定。

-   run log/report: warningとwaiverを含む実行証跡。

## 確認問題

-   clock periodを半分にした場合、setup slackがどう変わるか予測する。

-   hold slackが正でも安心しきれない理由をcorner、OCV、I/O
    constraintから説明する。

# 5. 再現可能なデバッグ

エラーを見たらランダムに設定を変えず、最初に失敗した境界を特定します。下流のエラーは上流の欠損から連鎖していることが多いためです。

## 標準debug loop

34. 再現：同じcommitとcommandで再発させる。

35. 縮小：最小testbenchまたは単一cellへ戻す。

36. 観測：input、internal state、outputを同じtimebaseで保存する。

37. 仮説：1回の実行で検証できる原因を1つ書く。

38. 変更：1要因だけ変える。

39. 回帰：直ったtestと既存testを両方実行する。

40. 記録：原因、変更、証拠をcommitまたはdecision logへ残す。

| **症状**               | **最初に見る場所**                                             |
|------------------------|----------------------------------------------------------------|
| SPICE convergence      | initial condition、ramp discontinuity、timestep、floating node |
| codeが全部0/63         | comparator polarity、reset、range                              |
| cell順が入れ替わる     | MUX select、payload packing                                    |
| ±1が不安定             | capture convention、CDC boundary                               |
| RTL simはPASS、P&R失敗 | clock/reset、unsupported construct、constraints                |
| DRC/LVS不一致          | PDK deck、pin label、bulk/substrate、netlist source            |

# 6. 学生演習

## 演習A：再現レポート

-   make checkからmake four-cell-wilkinsonまで実行する。

-   commit hash、実行環境、command、主要波形、判定を2ページでまとめる。

-   nominal結果と保証値を混同していないか自己レビューする。

## 演習B：ADC設計変更

-   ramp slopeを変更し、conversion timeとcode scaleの変化を予測する。

-   simulationを実行し、予測との差を説明する。

-   VERIFICATION\_MATRIXへ新しいtestを1行追加する。

## 演習C：CDC boundary

-   phase sweep点を増やし、遷移境界を絞り込む。

-   binary capture版とGray capture版のfailure modeを比較する。

-   ±1 codeを許容する判定条件を文章で定義する。

## 演習D：physical experiment

-   clock constraintまたはutilizationを1つだけ変える。

-   area、slack、wire length、runtimeの変化を比較する。

-   改善したmetricと悪化したmetricを両方報告する。

|                                                                                                              |
|--------------------------------------------------------------------------------------------------------------|
| **提出物** README形式の短い実験記録、変更diff、再現command、主要artifactへの相対path。画像だけの提出は不可。 |

# 7. Prototypeからtape-outへ

このリポジトリはcomplete design
flowのdemonstrationとして大きな節目に到達しています。しかしfoundryへ提出するfull
chipには、デジタルGDS以外の設計とprovider固有条件が残っています。

| **残作業**        | **必要な出口条件**                                                  |
|-------------------|---------------------------------------------------------------------|
| MPW/provider確定  | run日程、PDK release、submission checklist、面積、公開条件          |
| Analog layout     | sampling/MUX/ramp/comparatorのlayout、PEX、DRC/LVS                  |
| PVT/Monte Carlo   | corner、温度、電源、mismatchのpass/fail                             |
| Top integration   | analog + digital floorplan、power/ground、clock、substrate strategy |
| Pad/ESD           | provider-qualified I/O library、voltage、ESD、latch-up              |
| Package/PCB       | bond map、package parasitic、evaluation PCB、FPGA interface         |
| Full-chip signoff | top DRC/LVS、antenna、ERC、density、timing、deliverable audit       |

|                                                                                                                                                                                    |
|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **電源上の注意** 現デジタルflowはGF180の gf180mcu\_fd\_sc\_mcu7t5v0 timing viewsを使用しています。最終電源、pad、library選択はMPW providerのqualified option確認後にfreezeします。 |

## Tape-out readiness review

□ PDKとtool versionが固定されている。

□ 全要求にtestとartifactが紐づいている。

□ 全waiverにownerと根拠がある。

□ pad ring、seal ring、density/fillを含むtop GDSがある。

□ package/PCB/test planがchip pinoutと一致する。

# 8. Specification snapshot

| **項目**          | **Prototype v0**                                                   |
|-------------------|--------------------------------------------------------------------|
| Process           | GF180MCU Open PDK baseline                                         |
| Channels          | 1 analog channel                                                   |
| Storage depth     | 4 cells                                                            |
| ADC               | shared Wilkinson, 6 bit                                            |
| Readout           | 24-bit serial payload                                              |
| Control           | synthesizable RTL FSM                                              |
| Primary objective | complete reproducible design flow                                  |
| Not yet claimed   | target bandwidth, precision, radiation tolerance, production yield |

## 用語集

| **用語**      | **意味**                                           |
|---------------|----------------------------------------------------|
| PDK           | processのdevice model、layer、rule deck、library等 |
| MPW           | 複数designでwafer costを共有するshuttle            |
| SCA           | switched-capacitor array。波形をcapacitor列へ保存  |
| Wilkinson ADC | rampの交差時刻をcounterで測るADC                   |
| CDC           | clock domain crossing。非同期信号の受け渡し        |
| DRC           | layout形状がdesign ruleへ適合するか                |
| LVS           | layout接続とschematic/netlistの一致                |
| STA           | ベクトルを使わずpath timingを検証                  |
| PEX           | layout寄生R/Cを抽出して再simulation                |
| GDSII         | mask layoutを表す交換形式                          |

# 9. Command quick reference

| **Command**              | **対象**                      |
|--------------------------|-------------------------------|
| make check               | environment/repository sanity |
| make nmos-dc             | GF180 NMOS DC sweep           |
| make sampling-cell       | single sampling cell          |
| make four-cell           | 4-cell sampling array         |
| make comparator          | comparator transient          |
| make comparator-range    | input range                   |
| make comparator-offset   | offset sensitivity            |
| make ramp-generator      | ramp                          |
| make wilkinson-slice     | single 6-bit conversion       |
| make transfer            | ADC transfer                  |
| make four-cell-mux       | shared analog MUX             |
| make four-cell-wilkinson | 4-cell integrated analog      |
| make gray-counter        | Gray counter RTL              |
| make controller          | conversion controller         |
| make four-cell-cosim     | SPICE-to-RTL co-sim           |
| make phase-sweep         | CDC boundary sweep            |
| make digital-top         | full RTL regression           |
| make digital-physical    | RTL-to-GDS                    |
| make vnc                 | browser desktop               |

# 10. Final review sheet

学生は以下を口頭またはREADMEで説明できれば、このprototypeのcomplete
flowを自走できています。

□ なぜ4-cell/6-bitまで仕様を緩めたのか。

□ sampling errorがADC codeへどう伝播するか。

□ ramp/comparator/counterがどの順番で働くか。

□ なぜGray captureを選んだのか。

□ SPICEとRTLの境界contractは何か。

□ DRC/LVS/STAの0 violationsが何を保証し、何を保証しないか。

□ どのファイルがsourceで、どれがgenerated artifactか。

□ tape-outまでに残るtop-level blockerは何か。

|                                                                                                                                                                                         |
|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **次の設計課題** 最優先はanalog layout + extracted simulationです。sampling cellを最初のlayout対象とし、schematic → layout → DRC → LVS → PEX → transient比較を1ブロックで完結させます。 |

## 主要参照先

-   GitHub: https://github.com/sykeisuke/asic\_rd

-   docs/PROTOTYPE\_SPECIFICATION.md

-   docs/VERIFICATION\_MATRIX.md

-   docs/TAPEOUT\_BLOCKERS.md

-   docs/decisions/0003-gray-comparator-capture.md

このハンドブック自体も設計成果物です。回路、command、結果、判断が変わったら、同じcommitで更新してください。

# Tape-out 1 シリコン試験手順書

版: 0.1
対象: 1-channel、4-cell、6-bit Wilkinson ASIC

## 1. 目的と安全原則

本書は、packageまたはwire-bond carrierに実装したTape-out 1 ASICを、破損させずに段階的に
立ち上げる手順を定める。各段階に合格してから次へ進む。最初から全機能を同時に動かさない。

- ESD対策済みの作業台、wrist strap、接地した測定器を使用する。
- ASICへ信号を加える前に、該当I/O電源を投入する。無給電pinへ電圧を加えない。
- 電源電圧、投入順序、絶対最大定格はMPW事業者のpad/PDK資料を最優先する。
- 各電源をcurrent limit付きで投入する。初期limitは設計電流見積りとboard単体測定から承認する。
- 異常電流、rail電圧異常、発熱、発振、不安定なbondがあれば直ちに停止して電源を切る。
- Oscilloscope probeやsignal generatorのgroundで意図しない短絡を作らない。

## 2. 試験前に用意するもの

- 回路図、PCB layout、ASIC pinout、bond map、pad電圧表。
- Current limit付き多出力DC電源、DMM、oscilloscope、logic analyzer。
- DC/低周波source、pulse/function generator、必要に応じて低jitter clock source。
- FPGA readout firmwareと、使用commit/tagを記録したPC software。
- Pre-siliconのexpected waveform、code、許容範囲。
- Chip ID、board ID、日付、温度、測定器、設定、raw dataを記録するlog。

## 3. Phase 0: 無給電検査

1. Die、bond wire、package、PCBを顕微鏡または高倍率写真で記録する。
2. ASICを載せる前のboardで全regulator出力とclockを確認する。
3. 電源railからgroundへの抵抗を測り、設計値および未実装boardと比較する。
4. 隣接pin、supply、ground間のshortがないことを確認する。
5. Connector、jumper、series resistor、test pointの実装値を確認する。

**合格条件:** 目視異常と予期しないshortがなく、ASIC未接続時の全railが規定範囲にある。

## 4. Phase 1: 段階的power-up

1. 全clock、analog input、digital inputを0 Vまたはhigh impedanceにする。
2. MPW事業者が指定する順序でI/O、digital、analog railをcurrent limit付きで投入する。
3. 各railの電圧と静止電流を個別に記録する。
4. 30秒、2分、10分後に再測定し、温度上昇やdriftを確認する。
5. Resetをassertした状態とreleaseした状態の電流を比較する。

**停止条件:** current limit到達、想定の2倍を超える電流、railの5%以上の低下、局所発熱、時間とともに
増加する電流。停止後は抵抗測定と実装検査へ戻る。

## 5. Phase 2: デジタル単体試験

Analog inputと内部rampを停止したままdigital test modeを使う。

1. Reset、status、divided-clock monitorを確認する。
2. 低速clockから開始し、6-bit counterが0から63まで進むことを確認する。
3. Comparator crossingをtest signalで模擬し、4個のresult registerへ既知codeをcaptureする。
4. 24-bit payloadが`{cell3, cell2, cell1, cell0}`で、bit順とactive edgeが仕様通りか確認する。
5. Clockを段階的に20 MHzまで上げ、各段階で同じtestを繰り返す。

**合格条件:** Reset、counter、capture、cell address、serial readoutが全test vectorで一致する。

## 6. Phase 3: Comparatorと外部ramp

1. Comparator standalone modeを選び、既知DC電圧を比較入力へ加える。
2. 外部rampを低速で掃引し、comparator outputの反転点をoscilloscopeで測る。
3. 複数のDC入力点でcrossing voltage、delay、繰返しばらつきを記録する。
4. Digital counter captureを有効にし、crossing timeとcodeが対応するか確認する。

**合格条件:** Comparator極性が正しく、入力電圧の増加に対してcrossing time/codeが非減少となる。

## 7. Phase 4: Sampling cell単体試験

1. 安全範囲内のDC入力を加え、cell 0だけをtrackしてからholdする。
2. `VHOLD` monitorでacquisition error、clock edge disturbance、hold droopを測る。
3. 入力を0.4-1.6 Vの複数点で変え、同じ測定を行う。
4. Cell 1-3について順に繰り返し、pedestalとgain差を記録する。
5. Hold時間を変え、leakageによるcode変化を測る。

**合格条件:** 少なくとも1 cellが入力順序を保持し、4 cellの差を測定可能なdataとして取得できる。

## 8. Phase 5: 4-cell統合変換

1. まず低周波またはDC入力で、4本の`SAMPLE[i]`を40 ns間隔で駆動する。
2. Sampling完了後、MUXでcell 0-3を順に選択する。
3. 外部rampと20 MHz conversion clockで4個の6-bit codeを取得する。
4. `VIN`、観測可能な`VHOLD`、`MUX_BUS`、`VRAMP`、`COMPARE_OUT`、reset、serial dataを保存する。
5. 入力を変えて、cell addressが入れ替わらずcodeが非減少となることを確認する。
6. 同じ手順を内部rampへ切り替え、外部rampとの差を比較する。

**合格条件:** 4個のsampleが正しいaddressで読み出され、入力に対して一貫したcodeを返す。またはtest
modeにより故障blockをsampling、MUX、ramp、comparator、counter、readoutのいずれかへ切り分けられる。

## 9. Phase 6: ADC、速度、帯域のcharacterization

1. DC入力を細かく掃引し、各cellのcode transition、missing code、monotonicityを測る。
2. 十分な入力点と低noise測定を得た後にDNL/INLを計算する。
3. Sampling間隔を40 nsから段階的に短くし、errorが急増する点を実測上限とする。
4. Sine入力の周波数を上げ、振幅低下、phase、code errorから実用帯域を評価する。
5. Supply電圧と温度を認定範囲内で変え、pedestal、gain、ramp slope、offsetを再測定する。
6. Cellごとのpedestal、gain、time offsetをcalibration tableとして保存する。

Tape-out 1では6-bit、25 MSa/s、10 MHz測定目標の実証を優先する。Tape-out 2/3の性能値を、
最初のdie 1個だけの結果から保証しない。

## 10. 測定記録template

| 項目 | 記録内容 |
| --- | --- |
| Device | Wafer/lot、die ID、package、board ID |
| Revision | ASIC、PCB、FPGA、softwareのGit commit/tag |
| Environment | 日時、温度、湿度、測定器と校正日 |
| Supplies | 設定電圧、実測電圧、current limit、実測電流 |
| Clocks | Sampling pulse幅/間隔、conversion周波数、振幅 |
| Stimulus | 入力種別、振幅、offset、周波数 |
| Result | Pass/Fail、waveform、raw data、解析script |
| Deviation | 仕様との差、停止条件、暫定原因、次の試験 |

Raw dataは編集せず保存し、解析結果、写真、scope設定、scriptと一緒にdevice ID別directoryへ置く。

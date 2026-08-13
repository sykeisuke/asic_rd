# Lab 1: Sampling switchとHold capacitor

## このLabで理解すること

この回路は、連続的に変化する入力電圧`VIN`から、ある時刻の値を
capacitorへ保存します。まず見る信号は`VIN`、`SAMPLE`、`VHOLD`の3つです。

```text
VIN -- transmission gate -- VHOLD
                              |
                            CHOLD
                              |
                             GND
```

`SAMPLE=High`ではtransmission gateがONになり、`VHOLD`は`VIN`を追跡します。
`SAMPLE=Low`ではgateがOFFになり、切断直前の電圧が`CHOLD`へ残ります。

## なぜNMOSとPMOSを並列にするか

NMOSだけのswitchは低い電圧を通しやすい一方、高い電圧ではgate-source電圧が
不足して抵抗が増えます。PMOSは逆の傾向を持ちます。両者を並列にして逆相clockで
駆動すると、入力範囲全体で比較的均一なswitchになります。これがtransmission gateです。

## ファイル

| ファイル | 役割 |
| --- | --- |
| `ideal_sampling_cell.spice` | 理想switch。誤差ゼロに近い基準 |
| `sampling_cell.spice` | GF180 NMOS-only switch |
| `transmission_gate.spice` | GF180 NMOS+PMOS switch |
| `sampling_cell_tg.sch` | Xschemで読む教材用transmission gate回路 |

## 操作手順

Mac Terminalでrepositoryへ移動し、simulationを実行します。

```sh
cd /Users/ykeisuke/Desktop/mywork/asic_rd
make sampling-cell
```

VNC desktopのFile Managerで次を開きます。

```text
/foss/designs/simulations/gf180_sampling_cell/sampling_cell_tg.sch
```

Xschem上部の`Netlist`、`Simulate`を順に押し、緑矢印を`Ctrl + 左クリック`して
RAW結果を読み込みます。上段graphには`VIN`と`VHOLD`、下段には`SAMPLE`と
`SAMPLE_B`が表示されます。

## 波形の読み方

1. `SAMPLE=3.3 V`の区間で`VHOLD`が`VIN`を追跡することを確認する。
2. `SAMPLE`が0 Vへ下がった直後に`VHOLD`が一定になることを確認する。
3. switchを切る直前の`VIN`と`VHOLD`の差をacquisition errorとして読む。
4. clock edge前後の`VHOLD`の変化をedge disturbanceとして読む。現在の0.3 nsの
   測定窓では入力自身の変化も含むため、理想switchの値を基準として差分を見る。
5. hold区間中の`VHOLD`の傾きをdroopとして読む。

## 数値結果

`work/ideal_measurements.txt`、`work/measurements.txt`、
`work/transmission_gate_measurements.txt`を比較します。理想switch、NMOS-only、
transmission gateの順に、実デバイス由来の誤差と改善効果を区別できます。

`clock_feedthrough`という出力名は既存testとの互換性のため残していますが、現在の
測定値は純粋なclock feedthroughだけではありません。理想switchにも約2 mVが現れる
のは、測定窓内で入力波形が動くためです。今後、入力をedge周辺で一定にした専用testを
追加して純粋なclock feedthroughとcharge injectionを分離します。

## 自分で変更する実験

最初は一度に1項目だけ変更します。

1. `CHOLD`を`1p`から`0.5p`へ変更する。追従は速くなるがclock feedthroughが
   相対的に大きくなるか確認する。
2. `CHOLD`を`2p`へ変更する。追従と保持のtrade-offを確認する。
3. NMOSの`W=10u`を`5u`へ変更する。on-resistance増加によるacquisition errorを確認する。
4. PMOSのclockを意図的に100 psずらし、非重複時間または同時導通の影響を見る。

変更前の予想、変更したparameter、測定値、説明を表に残します。

## このLabの合格条件

- TRACKとHOLDを波形上で指し示せる。
- `VIN`、`VHOLD`、`SAMPLE`の因果関係を説明できる。
- acquisition error、clock feedthrough、droopの測定位置を説明できる。
- 理想switchとMOS switchの違いを説明できる。
- transmission gateを使う理由を説明できる。
